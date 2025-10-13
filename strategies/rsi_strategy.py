"""
Stratégie basée sur le RSI (Relative Strength Index)
"""
import backtrader as bt
from strategies.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    Stratégie RSI
    
    Signaux:
    - Achat: RSI < seuil de survente (oversold)
    - Vente: RSI > seuil de surachat (overbought)
    """
    
    params = (
        ('rsi_period', 10),
        ('rsi_oversold', 30),
        ('rsi_overbought', 60),
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # Indicateur RSI
        self.rsi = bt.indicators.RSI(
            self.datas[0].close,
            period=self.params.rsi_period
        )
        
        self.log(
            f"RSI: période={self.params.rsi_period}, "
            f"survente={self.params.rsi_oversold}, "
            f"surachat={self.params.rsi_overbought}"
        )
    
    def next(self):
        """Logique de trading"""
        if self.order:
            return
        
        rsi_value = self.rsi[0]
        
        if not self.position:
            # Signal d'achat: RSI en survente
            if rsi_value < self.params.rsi_oversold:
                self.log(
                    f'SIGNAL ACHAT (RSI={rsi_value:.2f}), '
                    f'Prix: {self.datas[0].close[0]:.2f}'
                )
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)
        
        else:
            # Signal de vente: RSI en surachat
            if rsi_value > self.params.rsi_overbought:
                self.log(
                    f'SIGNAL VENTE (RSI={rsi_value:.2f}), '
                    f'Prix: {self.datas[0].close[0]:.2f}'
                )
                self.order = self.sell(size=self.position.size)
