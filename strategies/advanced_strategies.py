"""
═══════════════════════════════════════════════════════════════════════════════
    STRATÉGIES AVANCÉES AVEC STOP LOSS & TRAILING STOP
═══════════════════════════════════════════════════════════════════════════════

Ce fichier contient plusieurs stratégies avancées avec gestion des risques:

1. BaseAdvancedStrategy - Classe de base avec stop loss intégré
2. MACrossoverAdvanced - MA avec stop loss et take profit
3. RSITrailingStop - RSI avec trailing stop
4. BreakoutStrategy - Breakout avec stops multiples
5. MomentumStrategy - Momentum avec ATR stops

Sauvegardez ce fichier dans: strategies/advanced_strategies.py
"""

import backtrader as bt
from strategies.base_strategy import BaseStrategy
from monitoring.logger import setup_logger

logger = setup_logger("advanced_strategies")


# ═══════════════════════════════════════════════════════════════════════════
# CLASSE DE BASE AVANCÉE
# ═══════════════════════════════════════════════════════════════════════════

class BaseAdvancedStrategy(BaseStrategy):
    """
    Classe de base avec gestion avancée des stops
    
    Fonctionnalités:
    - Stop Loss fixe ou dynamique
    - Take Profit
    - Trailing Stop
    - Stop Loss basé sur ATR
    """
    
    params = (
        # Stop Loss
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.02),          # 2% stop loss
        ('stop_loss_atr_mult', 2.0),      # Ou 2x ATR
        ('use_atr_stop', False),          # Utiliser ATR au lieu de %
        
        # Take Profit
        ('use_take_profit', True),
        ('take_profit_pct', 0.05),        # 5% take profit
        ('risk_reward_ratio', 2.5),       # Ou ratio risque/rendement
        
        # Trailing Stop
        ('use_trailing_stop', False),
        ('trailing_stop_pct', 0.03),      # 3% trailing
        ('trailing_activation_pct', 0.02), # Active après 2% de gain
        
        # ATR pour stops dynamiques
        ('atr_period', 14),
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Tracking des stops
        self.stop_order = None
        self.profit_order = None
        self.entry_price = None
        self.stop_price = None
        self.profit_price = None
        self.highest_price = None
        
        # ATR pour stops dynamiques
        if self.params.use_atr_stop:
            self.atr = bt.indicators.ATR(
                self.datas[0],
                period=self.params.atr_period
            )
    
    def notify_order(self, order):
        """Gestion des ordres avec stops"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.entry_price = order.executed.price
                self.highest_price = order.executed.price
                
                self.log(
                    f'ACHAT EXÉCUTÉ @ {order.executed.price:.2f}, '
                    f'Coût: {order.executed.value:.2f}, '
                    f'Commission: {order.executed.comm:.2f}'
                )
                
                # Placer les ordres de sortie
                if self.params.use_stop_loss or self.params.use_take_profit:
                    self._place_exit_orders()
                
            elif order.issell():
                # Calculer le P&L
                if self.entry_price:
                    pnl = order.executed.price - self.entry_price
                    pnl_pct = (pnl / self.entry_price) * 100
                    
                    self.log(
                        f'VENTE EXÉCUTÉE @ {order.executed.price:.2f}, '
                        f'P&L: {pnl:.2f} ({pnl_pct:.2f}%)'
                    )
                
                # Réinitialiser
                self.entry_price = None
                self.highest_price = None
                self.stop_order = None
                self.profit_order = None
            
            self.order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Ordre {order.getstatusname()}', level="WARNING")
            self.order = None
    
    def _place_exit_orders(self):
        """Place les ordres de stop loss et take profit"""
        if not self.entry_price:
            return
        
        # Calculer le stop loss
        if self.params.use_stop_loss:
            if self.params.use_atr_stop:
                # Stop basé sur ATR
                stop_distance = self.atr[0] * self.params.stop_loss_atr_mult
                self.stop_price = self.entry_price - stop_distance
            else:
                # Stop basé sur pourcentage
                self.stop_price = self.entry_price * (1 - self.params.stop_loss_pct)
            
            self.log(f'  → Stop Loss placé @ {self.stop_price:.2f}')
        
        # Calculer le take profit
        if self.params.use_take_profit:
            if self.params.risk_reward_ratio and self.stop_price:
                # Take profit basé sur ratio risque/rendement
                risk = self.entry_price - self.stop_price
                reward = risk * self.params.risk_reward_ratio
                self.profit_price = self.entry_price + reward
            else:
                # Take profit basé sur pourcentage
                self.profit_price = self.entry_price * (1 + self.params.take_profit_pct)
            
            self.log(f'  → Take Profit placé @ {self.profit_price:.2f}')
    
    def _check_stops(self):
        """Vérifie et gère les stops (à appeler dans next())"""
        if not self.position:
            return False
        
        current_price = self.datas[0].close[0]
        if self.highest_price is None or self.entry_price is None:
            # Devrait normalement être initialisé dans notify_order
            # Mais si pas encore fait, initialiser maintenant
            self.entry_price = self.position.price
            self.highest_price = current_price
        # Mettre à jour le plus haut prix pour trailing stop
        if current_price > self.highest_price:
            self.highest_price = current_price
        
        # Vérifier trailing stop
        if self.params.use_trailing_stop:
            # Activer seulement si gain minimum atteint
            gain_pct = (self.highest_price - self.entry_price) / self.entry_price
            
            if gain_pct >= self.params.trailing_activation_pct:
                trailing_stop = self.highest_price * (1 - self.params.trailing_stop_pct)
                
                # Mettre à jour le stop si plus haut
                if trailing_stop > self.stop_price:
                    self.stop_price = trailing_stop
                    self.log(f'  → Trailing Stop ajusté @ {self.stop_price:.2f}')
        
        # Vérifier stop loss
        if self.params.use_stop_loss and current_price <= self.stop_price:
            self.log(f'STOP LOSS DÉCLENCHÉ @ {current_price:.2f}', level="WARNING")
            self.order = self.sell(size=self.position.size)
            return True
        
        # Vérifier take profit
        if self.params.use_take_profit and current_price >= self.profit_price:
            self.log(f'TAKE PROFIT DÉCLENCHÉ @ {current_price:.2f}')
            self.order = self.sell(size=self.position.size)
            return True
        
        return False


# ═══════════════════════════════════════════════════════════════════════════
# STRATÉGIE 1: MA CROSSOVER AVEC STOP LOSS & TAKE PROFIT
# ═══════════════════════════════════════════════════════════════════════════

class MACrossoverAdvanced(BaseAdvancedStrategy):
    """
    Croisement de moyennes mobiles + RSI avec gestion avancée des stops
    
    Configuration recommandée:
    - stop_loss_pct = 0.02 (2%)
    - take_profit_pct = 0.05 (5%)
    - risk_reward_ratio = 2.5
    """
    
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 60),
        ('fast_period', 50),
        ('slow_period', 100),
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.03),
        ('use_take_profit', True),
        ('risk_reward_ratio', 3),
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.025),
        ('trailing_activation_pct', 0.03),
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()

        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        self.fast_ma = bt.indicators.EMA(
            self.datas[0].close,
            period=self.params.fast_period
        )
        
        self.slow_ma = bt.indicators.EMA(
            self.datas[0].close,
            period=self.params.slow_period
        )
        
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        self.log(
            f"MA Crossover Advanced: EMA{self.params.fast_period}/{self.params.slow_period}, "
            f"Stop: {self.params.stop_loss_pct*100}%, "
            f"TP: R/R {self.params.risk_reward_ratio}"
        )
    
    def next(self):
        # Vérifier les stops d'abord
        if self._check_stops():
            return
        
        if self.order:
            return
        
        rsi_value = self.rsi[0]

        if not self.position:
            # Signal d'achat
            if self.crossover > 0 and rsi_value < self.params.rsi_oversold:
                self.log(f'SIGNAL ACHAT, Prix: {self.datas[0].close[0]:.2f}')
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Signal de vente (sortie anticipée)
            if self.crossover < 0:
                self.log(f'SIGNAL VENTE (Crossover inversé)')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# STRATÉGIE 2: RSI AVEC TRAILING STOP
# ═══════════════════════════════════════════════════════════════════════════

class RSITrailingStop(BaseAdvancedStrategy):
    """
    RSI avec trailing stop pour maximiser les profits
    
    Configuration recommandée:
    - rsi_oversold = 30
    - rsi_overbought = 70
    - trailing_stop_pct = 0.03 (3%)
    - trailing_activation_pct = 0.02 (2%)
    """
    
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.03),
        ('use_take_profit', False),  # On préfère le trailing
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.03),
        ('trailing_activation_pct', 0.02),
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        self.log(
            f"RSI Trailing Stop: RSI({self.params.rsi_period}), "
            f"Oversold: {self.params.rsi_oversold}, "
            f"Trailing: {self.params.trailing_stop_pct*100}%"
        )
    
    def next(self):
        # Vérifier les stops
        if self._check_stops():
            return
        
        if self.order:
            return
        
        rsi_value = self.rsi[0]
        
        if not self.position:
            # Achat en zone de survente
            if rsi_value < self.params.rsi_oversold:
                self.log(f'SIGNAL ACHAT (RSI={rsi_value:.2f}), Prix: {self.datas[0].close[0]:.2f}')
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Sortie si RSI en surachat (en plus du trailing)
            if rsi_value > self.params.rsi_overbought:
                self.log(f'SIGNAL VENTE (RSI surachat={rsi_value:.2f})')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# STRATÉGIE 3: BREAKOUT AVEC ATR STOP
# ═══════════════════════════════════════════════════════════════════════════

class BreakoutATRStop(BaseAdvancedStrategy):
    """
    Stratégie de breakout avec stop loss basé sur ATR
    
    Achète quand le prix casse le plus haut de N périodes
    Stop loss dynamique basé sur ATR
    """
    
    params = (
        ('breakout_period', 20),
        ('use_stop_loss', True),
        ('use_atr_stop', True),
        ('stop_loss_atr_mult', 2.0),
        ('atr_period', 14),
        ('use_take_profit', True),
        ('risk_reward_ratio', 3.0),
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.04),
        ('trailing_activation_pct', 0.03),
        ('volume_confirmation', True),
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Plus haut et plus bas sur la période
        self.highest = bt.indicators.Highest(
            self.datas[0].high,
            period=self.params.breakout_period
        )
        
        self.lowest = bt.indicators.Lowest(
            self.datas[0].low,
            period=self.params.breakout_period
        )
        
        # Volume moyen
        if self.params.volume_confirmation:
            self.avg_volume = bt.indicators.SMA(
                self.datas[0].volume,
                period=20
            )
        
        self.log(
            f"Breakout ATR: Période={self.params.breakout_period}, "
            f"ATR Stop={self.params.stop_loss_atr_mult}x, "
            f"R/R={self.params.risk_reward_ratio}"
        )
    
    def next(self):
        # Vérifier les stops
        if self._check_stops():
            return
        
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        if not self.position:
            # Breakout haussier
            if current_price > self.highest[-1]:
                # Vérifier le volume si activé
                if self.params.volume_confirmation:
                    if self.datas[0].volume[0] < self.avg_volume[0] * 1.2:
                        return  # Volume insuffisant
                
                self.log(
                    f'BREAKOUT HAUSSIER @ {current_price:.2f} '
                    f'(Plus haut={self.highest[-1]:.2f})'
                )
                size = int((self.broker.getcash() * 0.95) / current_price)
                self.order = self.buy(size=size)
        
        else:
            # Sortie si breakout baissier (casse le support)
            if current_price < self.lowest[-1]:
                self.log(f'BREAKOUT BAISSIER - Sortie anticipée')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# STRATÉGIE 4: MOMENTUM AVEC STOPS MULTIPLES
# ═══════════════════════════════════════════════════════════════════════════

class MomentumMultipleStops(BaseAdvancedStrategy):
    """
    Stratégie momentum avec système de stops multiples
    
    - Stop loss initial serré
    - Breakeven après X% de gain
    - Trailing stop agressif après Y% de gain
    """
    
    params = (
        ('roc_period', 10),               # Rate of Change
        ('roc_threshold', 2.0),           # 2% momentum minimum
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.015),         # 1.5% stop initial
        ('breakeven_trigger', 0.02),      # Passer à breakeven après 2%
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.025),     # 2.5% trailing
        ('trailing_activation_pct', 0.04), # Activer après 4%
        ('aggressive_trailing_pct', 0.015), # 1.5% trailing après 8%
        ('aggressive_trigger', 0.08),
        ('use_take_profit', True),
        ('take_profit_pct', 0.12),        # 12% take profit
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Rate of Change (Momentum)
        self.roc = bt.indicators.ROC(
            self.datas[0].close,
            period=self.params.roc_period
        )
        
        # RSI pour confirmation
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=14
        )
        
        self.log(
            f"Momentum Multiple Stops: ROC({self.params.roc_period}), "
            f"Stop initial={self.params.stop_loss_pct*100}%, "
            f"Breakeven @ {self.params.breakeven_trigger*100}%"
        )
    
    def next(self):
        # Vérifier les stops avec gestion avancée
        if self.position and self.entry_price:
            current_price = self.datas[0].close[0]
            gain_pct = (current_price - self.entry_price) / self.entry_price
            
            # Déplacer vers breakeven
            if gain_pct >= self.params.breakeven_trigger:
                if self.stop_price < self.entry_price:
                    self.stop_price = self.entry_price
                    self.log(f'  → Stop déplacé au BREAKEVEN @ {self.stop_price:.2f}')
            
            # Trailing agressif après gros gain
            if gain_pct >= self.params.aggressive_trigger:
                if self.highest_price > current_price:
                    aggressive_stop = self.highest_price * (1 - self.params.aggressive_trailing_pct)
                    if aggressive_stop > self.stop_price:
                        self.stop_price = aggressive_stop
                        self.log(f'  → TRAILING AGRESSIF @ {self.stop_price:.2f}')
        
        # Vérifier les stops
        if self._check_stops():
            return
        
        if self.order:
            return
        
        if not self.position:
            # Signal momentum fort + RSI pas en surachat
            if self.roc[0] > self.params.roc_threshold and self.rsi[0] < 70:
                self.log(
                    f'SIGNAL MOMENTUM (ROC={self.roc[0]:.2f}%), '
                    f'Prix: {self.datas[0].close[0]:.2f}'
                )
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)


# ═══════════════════════════════════════════════════════════════════════════
# GUIDE D'UTILISATION
# ═══════════════════════════════════════════════════════════════════════════

"""
UTILISATION:

1. Sauvegarder ce fichier dans: strategies/advanced_strategies.py

2. Tester une stratégie:
   python main.py --strategy MACrossoverAdvanced --symbols AAPL

3. Modifier les paramètres dans config/strategies_config.yaml:

ma_crossover_advanced:
  parameters:
    fast_period: 20
    slow_period: 50
    stop_loss_pct: 0.02
    take_profit_pct: 0.05
    trailing_stop_pct: 0.025

4. Créer votre propre stratégie en héritant de BaseAdvancedStrategy

5. Les méthodes importantes:
   - _place_exit_orders(): Place automatiquement stop/tp
   - _check_stops(): Vérifie et gère tous les stops
   - Appelez _check_stops() au début de next()
"""