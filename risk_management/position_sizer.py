"""
Calcul de la taille des positions
"""
import backtrader as bt
from config import settings
from monitoring.logger import setup_logger

logger = setup_logger("position_sizer")


class PercentSizer(bt.Sizer):
    """
    Sizer basé sur un pourcentage du capital
    """
    params = (
        ('percents', 95),  # Utiliser 95% du capital disponible
    )
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            size = int((cash * (self.params.percents / 100)) / data.close[0])
            return size
        
        # Pour la vente, vendre toute la position
        return self.broker.getposition(data).size


class FixedRiskSizer(bt.Sizer):
    """
    Sizer basé sur un risque fixe par trade
    """
    params = (
        ('risk_per_trade', 0.02),  # Risquer 2% du capital
        ('stop_loss_pct', 0.05),   # Stop loss à 5%
    )
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # Calculer la taille basée sur le risque
            portfolio_value = self.broker.getvalue()
            risk_amount = portfolio_value * self.params.risk_per_trade
            
            # Taille = Risque / Stop Loss
            size = int(risk_amount / (data.close[0] * self.params.stop_loss_pct))
            
            # Vérifier qu'on a assez de capital
            max_size = int(cash / data.close[0])
            size = min(size, max_size)
            
            return size
        
        return self.broker.getposition(data).size


class KellySizer(bt.Sizer):
    """
    Sizer basé sur le critère de Kelly
    """
    params = (
        ('win_rate', 0.5),
        ('avg_win', 1.5),
        ('avg_loss', 1.0),
        ('kelly_fraction', 0.5),  # Utiliser la moitié du Kelly
    )
    
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            # Formule de Kelly: f = (p*b - q) / b
            # p = win_rate, q = 1-p, b = avg_win/avg_loss
            p = self.params.win_rate
            q = 1 - p
            b = self.params.avg_win / self.params.avg_loss
            
            kelly = (p * b - q) / b
            kelly = max(0, min(kelly, 1)) * self.params.kelly_fraction
            
            size = int((cash * kelly) / data.close[0])
            return size
        
        return self.broker.getposition(data).size
