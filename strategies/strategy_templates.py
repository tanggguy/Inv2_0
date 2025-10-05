"""
═══════════════════════════════════════════════════════════════════════════════
    STRATEGY TEMPLATES - 5 Templates Prêts à l'Emploi
═══════════════════════════════════════════════════════════════════════════════

Copiez-collez ces templates et modifiez-les selon vos besoins

Sauvegardez dans: strategies/strategy_templates.py
"""

from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE 1: STRATÉGIE SIMPLE AVEC STOPS
# ═══════════════════════════════════════════════════════════════════════════

class MyFirstStrategy(BaseAdvancedStrategy):
    """
    Template de base - À personnaliser
    
    Modifiez:
    1. Les paramètres (params)
    2. Les indicateurs dans __init__
    3. La logique dans next()
    """
    
    params = (
        # Paramètres de la stratégie
        ('my_parameter', 20),
        
        # Gestion des risques
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.02),           # 2% stop loss
        ('use_take_profit', True),
        ('risk_reward_ratio', 2.5),        # 2.5:1 risque/rendement
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.03),       # 3% trailing
        ('trailing_activation_pct', 0.02), # Active après 2% gain
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # ===== AJOUTEZ VOS INDICATEURS ICI =====
        self.my_indicator = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.my_parameter
        )
        
        # Exemple d'autres indicateurs:
        # self.rsi = bt.indicators.RSI(period=14)
        # self.macd = bt.indicators.MACD()
        # self.bollinger = bt.indicators.BollingerBands()
    
    def next(self):
        # TOUJOURS vérifier les stops en premier
        if self._check_stops():
            return
        
        if self.order:
            return
        
        # ===== LOGIQUE D'ACHAT =====
        if not self.position:
            # Modifiez cette condition selon votre stratégie
            if self.datas[0].close[0] > self.my_indicator[0]:
                self.log(f'SIGNAL ACHAT @ {self.datas[0].close[0]:.2f}')
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        # ===== LOGIQUE DE VENTE =====
        else:
            # Modifiez cette condition pour vos sorties anticipées
            if self.datas[0].close[0] < self.my_indicator[0]:
                self.log(f'SIGNAL VENTE @ {self.datas[0].close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE 2: TRIPLE INDICATEUR
# ═══════════════════════════════════════════════════════════════════════════

class TripleIndicatorStrategy(BaseAdvancedStrategy):
    """
    Stratégie utilisant 3 indicateurs pour confirmation
    - MA pour la tendance
    - RSI pour le timing
    - Volume pour la confirmation
    """
    
    params = (
        # Indicateurs
        ('ma_period', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('volume_factor', 1.5),
        
        # Stops
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.025),
        ('use_take_profit', True),
        ('risk_reward_ratio', 3.0),
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.02),
        ('trailing_activation_pct', 0.03),
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Tendance
        self.ma = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.ma_period
        )
        
        # Momentum
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        # Volume
        self.volume_sma = bt.indicators.SMA(
            self.datas[0].volume,
            period=20
        )
        
        self.log(f"Triple Indicator: MA={self.params.ma_period}, RSI={self.params.rsi_period}")
    
    def next(self):
        if self._check_stops():
            return
        
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        if not self.position:
            # 3 conditions pour acheter:
            # 1. Prix au-dessus de la MA (tendance haussière)
            trend_up = current_price > self.ma[0]
            
            # 2. RSI en survente (timing d'entrée)
            rsi_buy = self.rsi[0] < self.params.rsi_oversold
            
            # 3. Volume élevé (confirmation)
            high_volume = self.datas[0].volume[0] > (self.volume_sma[0] * self.params.volume_factor)
            
            if trend_up and rsi_buy and high_volume:
                self.log(
                    f'SIGNAL ACHAT CONFIRMÉ - Prix: {current_price:.2f}, '
                    f'RSI: {self.rsi[0]:.2f}, Volume: Élevé'
                )
                size = int((self.broker.getcash() * 0.95) / current_price)
                self.order = self.buy(size=size)
        
        else:
            # Sortie anticipée si RSI en surachat
            if self.rsi[0] > self.params.rsi_overbought:
                self.log(f'SORTIE RSI SURACHAT ({self.rsi[0]:.2f})')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE 3: SCALPING AVEC STOPS SERRÉS
# ═══════════════════════════════════════════════════════════════════════════

class ScalpingStrategy(BaseAdvancedStrategy):
    """
    Stratégie de scalping avec stops très serrés
    Pour timeframes courts (5min, 15min)
    """
    
    params = (
        # Indicateurs
        ('ema_fast', 5),
        ('ema_slow', 13),
        ('rsi_period', 7),
        
        # Stops très serrés pour scalping
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.005),          # 0.5% stop
        ('use_take_profit', True),
        ('take_profit_pct', 0.015),        # 1.5% profit (3:1)
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.007),      # 0.7% trailing
        ('trailing_activation_pct', 0.008), # Active à 0.8%
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        self.ema_fast = bt.indicators.EMA(
            self.datas[0].close,
            period=self.params.ema_fast
        )
        
        self.ema_slow = bt.indicators.EMA(
            self.datas[0].close,
            period=self.params.ema_slow
        )
        
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        self.crossover = bt.indicators.CrossOver(self.ema_fast, self.ema_slow)
        
        self.log(f"Scalping: EMA {self.params.ema_fast}/{self.params.ema_slow}, Stop: 0.5%")
    
    def next(self):
        if self._check_stops():
            return
        
        if self.order:
            return
        
        if not self.position:
            # Achat rapide sur crossover + RSI
            if self.crossover > 0 and 40 < self.rsi[0] < 60:
                self.log(f'SCALP ACHAT @ {self.datas[0].close[0]:.2f}')
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Sortie rapide sur crossover inverse
            if self.crossover < 0:
                self.log(f'SCALP VENTE @ {self.datas[0].close[0]:.2f}')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE 4: SWING TRADING
# ═══════════════════════════════════════════════════════════════════════════

class SwingTradingStrategy(BaseAdvancedStrategy):
    """
    Stratégie de swing trading (positions 2-10 jours)
    Stops plus larges pour laisser respirer
    """
    
    params = (
        # Indicateurs
        ('ma_short', 20),
        ('ma_long', 50),
        ('atr_period', 14),
        
        # Stops adaptés au swing
        ('use_stop_loss', True),
        ('use_atr_stop', True),
        ('stop_loss_atr_mult', 2.5),       # 2.5x ATR
        ('use_take_profit', True),
        ('risk_reward_ratio', 3.0),
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.05),       # 5% trailing
        ('trailing_activation_pct', 0.07), # Active à 7%
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        self.ma_short = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.ma_short
        )
        
        self.ma_long = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.ma_long
        )
        
        self.macd = bt.indicators.MACD(self.datas[0].close)
        
        self.crossover = bt.indicators.CrossOver(self.ma_short, self.ma_long)
        
        self.log(f"Swing Trading: MA {self.params.ma_short}/{self.params.ma_long}, ATR Stop")
    
    def next(self):
        if self._check_stops():
            return
        
        if self.order:
            return
        
        if not self.position:
            # Achat sur tendance + MACD
            if self.crossover > 0 and self.macd.macd[0] > self.macd.signal[0]:
                self.log(f'SWING ACHAT @ {self.datas[0].close[0]:.2f}')
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Sortie sur signal inverse
            if self.crossover < 0 or self.macd.macd[0] < self.macd.signal[0]:
                self.log(f'SWING VENTE - Signal inversé')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE 5: MEAN REVERSION (BOLLINGER BANDS)
# ═══════════════════════════════════════════════════════════════════════════

class MeanReversionStrategy(BaseAdvancedStrategy):
    """
    Stratégie de retour à la moyenne avec Bollinger Bands
    Achète quand survendu, vend quand suracheté
    """
    
    params = (
        # Bollinger Bands
        ('bb_period', 20),
        ('bb_std', 2.0),
        
        # RSI pour confirmation
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        
        # Stops
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.03),
        ('use_take_profit', True),
        ('take_profit_pct', 0.04),
        ('use_trailing_stop', False),  # Pas de trailing en mean reversion
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        self.bollinger = bt.indicators.BollingerBands(
            self.datas[0].close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )
        
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        self.log(f"Mean Reversion: BB({self.params.bb_period}, {self.params.bb_std})")
    
    def next(self):
        if self._check_stops():
            return
        
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        if not self.position:
            # Achat quand prix touche bande inférieure + RSI survendu
            touch_lower = current_price <= self.bollinger.lines.bot[0]
            rsi_oversold = self.rsi[0] < self.params.rsi_oversold
            
            if touch_lower and rsi_oversold:
                self.log(
                    f'MEAN REVERSION ACHAT @ {current_price:.2f} '
                    f'(BB Lower: {self.bollinger.lines.bot[0]:.2f}, RSI: {self.rsi[0]:.2f})'
                )
                size = int((self.broker.getcash() * 0.95) / current_price)
                self.order = self.buy(size=size)
        
        else:
            # Vente quand prix atteint bande supérieure ou moyenne
            touch_upper = current_price >= self.bollinger.lines.top[0]
            touch_mid = current_price >= self.bollinger.lines.mid[0]
            rsi_overbought = self.rsi[0] > self.params.rsi_overbought
            
            if touch_upper or (touch_mid and rsi_overbought):
                self.log(f'MEAN REVERSION VENTE @ {current_price:.2f}')
                self.order = self.sell(size=self.position.size)


# ═══════════════════════════════════════════════════════════════════════════
# GUIDE D'UTILISATION
# ═══════════════════════════════════════════════════════════════════════════

"""
COMMENT UTILISER CES TEMPLATES:

1. Choisir un template qui correspond à votre style de trading

2. Copier le code dans un nouveau fichier:
   cp strategies/strategy_templates.py strategies/ma_strategie.py

3. Modifier selon vos besoins:
   - Changer le nom de la classe
   - Ajuster les paramètres
   - Ajouter/modifier les indicateurs
   - Personnaliser la logique d'achat/vente

4. Tester:
   python main.py --strategy MaStrategie --symbols AAPL

EXEMPLES DE PERSONNALISATION:

# Changer les périodes MA
('ma_period', 30)  # Au lieu de 50

# Ajuster les stops
('stop_loss_pct', 0.015)  # 1.5% au lieu de 2%
('risk_reward_ratio', 3.0)  # 3:1 au lieu de 2.5:1

# Ajouter un indicateur
self.adx = bt.indicators.ADX(period=14)

# Modifier la condition d'achat
if trend_up and rsi_buy and high_volume and self.adx[0] > 25:
    # Acheter seulement si ADX > 25 (tendance forte)

CONSEILS:

- Commencez avec MyFirstStrategy (le plus simple)
- Testez chaque modification sur des données historiques
- Gardez une stratégie simple au début
- Documentez vos modifications
- Sauvegardez les versions qui fonctionnent bien
"""