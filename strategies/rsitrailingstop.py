from strategies.advanced_strategies import BaseAdvancedStrategy
import backtrader as bt


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
        ("rsi_period", 10),
        ("rsi_oversold", 35),
        ("rsi_overbought", 60),
        ("use_stop_loss", True),
        ("stop_loss_pct", 0.03),
        ("use_take_profit", False),  # On préfère le trailing
        ("use_trailing_stop", True),
        ("trailing_stop_pct", 0.07),
        ("trailing_activation_pct", 0.02),
        ("printlog", True),
    )

    def __init__(self):
        super().__init__()

        self.rsi = bt.indicators.RSI(self.datas[0].close, period=self.params.rsi_period)

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
                self.log(
                    f"SIGNAL ACHAT (RSI={rsi_value:.2f}), Prix: {self.datas[0].close[0]:.2f}"
                )
                size = int((self.broker.getcash() * 0.95) / self.datas[0].close[0])
                self.order = self.buy(size=size)

        else:
            # Sortie si RSI en surachat (en plus du trailing)
            if rsi_value > self.params.rsi_overbought:
                self.log(f"SIGNAL VENTE (RSI surachat={rsi_value:.2f})")
                self.order = self.sell(size=self.position.size)
