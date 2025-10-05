"""
Stratégie de croisement de moyennes mobiles
"""
import backtrader as bt
from strategies.base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    """
    Stratégie basée sur le croisement de moyennes mobiles
    
    Signaux:
    - Achat: Quand la MA rapide croise au-dessus de la MA lente
    - Vente: Quand la MA rapide croise en-dessous de la MA lente
    """
    
    params = (
        ('fast_period', 50),
        ('slow_period', 200),
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Moyennes mobiles
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, 
            period=self.params.fast_period
        )
        
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, 
            period=self.params.slow_period
        )
        
        # Signal de croisement
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        self.log(
            f"MA Rapide: {self.params.fast_period}, "
            f"MA Lente: {self.params.slow_period}"
        )
    
    def next(self):
        """Logique de trading"""
        # Ne pas trader si un ordre est en cours
        if self.order:
            return
        
        # Vérifier si on est en position
        if not self.position:
            # Signal d'achat: MA rapide croise au-dessus
            if self.crossover > 0:
                self.log(f'SIGNAL ACHAT, Prix: {self.datas[0].close[0]:.2f}')
                # Calculer la taille de la position (95% du capital)
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Signal de vente: MA rapide croise en-dessous
            if self.crossover < 0:
                self.log(f'SIGNAL VENTE, Prix: {self.datas[0].close[0]:.2f}')
                self.order = self.sell(size=self.position.size)
