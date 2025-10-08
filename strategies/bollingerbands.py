from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt

class MeanReversionStrategy(BaseAdvancedStrategy):
    """
    Stratégie de retour à la moyenne avec Bollinger Bands
    Achète quand survendu, vend quand suracheté + tendance haussiere (ema) + RSI pour confirmation
    """
    
    params = (
        # Moyenne mobile exponentiel  (tendance)
        ('ema_period', 250),
        # Bollinger Bands (volatilité)
        ('bb_period', 55),
        ('bb_std', 1.95),
        
        # RSI pour confirmation (momentum)
        ('rsi_period', 14),
        ('rsi_oversold', 34),
        ('rsi_overbought', 75),
        
        # Stops
        ('use_stop_loss', True),
        ('stop_loss_pct', 0.03),
        ('use_take_profit', True),
        ('take_profit_pct', 0.045),
        ('use_trailing_stop', False),  # Pas de trailing en mean reversion
        
        ('printlog', True),
    )
    
    def __init__(self):
        super().__init__()
        self.ema = bt.indicators.EMA(
            self.datas[0].close,
            period=self.params.ema_period
        )
        
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
            # Achat quand prix touche bande inférieure + RSI survendu + tendance haussière
            tendance_haussiere = current_price > self.ema[0]
            touch_lower = current_price <= self.bollinger.lines.bot[0]
            rsi_oversold = self.rsi[0] < self.params.rsi_oversold
            
            if tendance_haussiere and touch_lower and rsi_oversold:
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