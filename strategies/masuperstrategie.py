"""
MaSuperStrategie - Stratégie personnalisée
Créée avec le Strategy Creator interactif
"""

from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt


class MaSuperStrategie(BaseAdvancedStrategy):
    """
    Description de votre stratégie
    
    TODO:
    - Décrire la logique de trading
    - Ajouter les indicateurs nécessaires
    - Implémenter les conditions d'achat/vente
    - Tester et optimiser
    """
    
    params = (
        # Paramètres de la stratégie (à personnaliser)
        ('ma_period', 10),
        ('rsi_period', 7),
        
        # Gestion des risques
        ('use_stop_loss', True),
        ('use_atr_stop', True),
        ('stop_loss_atr_mult', 2.0),
        ('atr_period', 14),
        ('use_take_profit', True),
        ('take_profit_pct', 0.05),
        ('use_trailing_stop', True),
        ('trailing_stop_pct', 0.035),
        ('trailing_activation_pct', 0.02),
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # ===== AJOUTEZ VOS INDICATEURS ICI =====
        self.ma_fast = bt.indicators.SMA(self.datas[0].close, period=20)
        self.ma_slow = bt.indicators.SMA(self.datas[0].close, period=50)
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        # Exemple: Moyenne mobile
        self.ma = bt.indicators.SMA(
            self.datas[0].close,
            period=self.params.ma_period
        )
        
        # Exemple: RSI
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        # Autres indicateurs disponibles:
        # self.ema = bt.indicators.EMA(period=20)
        # self.macd = bt.indicators.MACD()
        # self.bollinger = bt.indicators.BollingerBands()
        # self.atr = bt.indicators.ATR(period=14)
        # self.stochastic = bt.indicators.Stochastic()
        
        self.log(f"MaSuperStrategie initialisée avec succès")
    
    def next(self):
        # ===== VÉRIFICATION DES STOPS =====
        # TOUJOURS en premier !
        if self._check_stops():
            return
        
        if self.order:
            return
        
        current_price = self.datas[0].close[0]
        
        # ===== LOGIQUE D'ACHAT =====
        # Vérifier si on est en position
        if not self.position:
            # Signal d'achat: MA rapide croise au-dessus
            if self.crossover > 0:
                self.log(f'SIGNAL ACHAT, Prix: {self.datas[0].close[0]:.2f}')
                # Calculer la taille de la position (95% du capital)
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)

        # ===== LOGIQUE DE VENTE =====
        else:
            # Signal de vente: MA rapide croise en-dessous
            if self.crossover < 0:
                self.log(f'SIGNAL VENTE, Prix: {self.datas[0].close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
        
        
        


# ═══════════════════════════════════════════════════════════════════════════
# GUIDE DE PERSONNALISATION
# ═══════════════════════════════════════════════════════════════════════════

"""
PROCHAINES ÉTAPES:

1. Personnaliser les indicateurs:
   - Ajouter/supprimer les indicateurs selon vos besoins
   - Ajuster les périodes

2. Implémenter votre logique de trading:
   - Modifier les conditions d'achat dans "LOGIQUE D'ACHAT"
   - Modifier les conditions de vente dans "LOGIQUE DE VENTE"

3. Tester votre stratégie:
   python main.py --strategy MaSuperStrategie --symbols AAPL

4. Optimiser:
   - Ajuster les paramètres
   - Backtester sur différentes périodes
   - Comparer avec d'autres stratégies

EXEMPLES DE CONDITIONS:

# Croisement de moyennes mobiles
if self.ma_fast[0] > self.ma_slow[0] and self.ma_fast[-1] <= self.ma_slow[-1]:
    # Acheter

# RSI en survente
if self.rsi[0] < 30:
    # Acheter

# Prix sort des bandes de Bollinger
if current_price < self.bollinger.lines.bot[0]:
    # Acheter

# Breakout
if current_price > self.highest_20days[0]:
    # Acheter

# Combinaison multiple
if (trend_up and rsi_oversold and high_volume):
    # Acheter

RESSOURCES:

- Backtrader Indicators: https://www.backtrader.com/docu/indautoref/
- Documentation complète: README.md
- Templates: strategies/strategy_templates.py
"""
