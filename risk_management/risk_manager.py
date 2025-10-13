"""
Gestionnaire des risques du portefeuille
"""

from config import settings
from monitoring.logger import setup_logger

logger = setup_logger("risk_manager")


class RiskManager:
    """Gère les règles de risque du système"""

    def __init__(self, max_position_size=0.1, max_risk_per_trade=0.02):
        self.max_position_size = max_position_size
        self.max_risk_per_trade = max_risk_per_trade
        self.risk_config = settings.RISK_MANAGEMENT

        logger.info(
            f"RiskManager initialisé: "
            f"max_position={max_position_size*100}%, "
            f"max_risk={max_risk_per_trade*100}%"
        )

    def validate_position_size(self, size, price, portfolio_value):
        """
        Valide qu'une position respecte les limites

        Args:
            size: Taille de la position
            price: Prix de l'actif
            portfolio_value: Valeur totale du portefeuille

        Returns:
            Taille ajustée si nécessaire
        """
        position_value = size * price
        position_pct = position_value / portfolio_value

        if position_pct > self.max_position_size:
            # Ajuster la taille
            max_value = portfolio_value * self.max_position_size
            adjusted_size = int(max_value / price)

            logger.warning(
                f"Position trop grande ({position_pct*100:.1f}%), "
                f"ajustée de {size} à {adjusted_size}"
            )

            return adjusted_size

        return size

    def check_portfolio_risk(self, positions):
        """
        Vérifie le risque total du portefeuille

        Args:
            positions: Dictionnaire des positions {symbol: position_info}

        Returns:
            True si le risque est acceptable
        """
        total_risk = sum(pos.get("risk", 0) for pos in positions.values())
        max_risk = self.risk_config["max_portfolio_risk"]

        if total_risk > max_risk:
            logger.warning(
                f"Risque portfolio trop élevé: {total_risk*100:.1f}% "
                f"(max: {max_risk*100:.1f}%)"
            )
            return False

        return True

    def calculate_stop_loss(self, entry_price, atr=None, method="percentage"):
        """
        Calcule le niveau de stop loss

        Args:
            entry_price: Prix d'entrée
            atr: Average True Range (optionnel)
            method: 'percentage' ou 'atr'

        Returns:
            Prix du stop loss
        """
        if method == "percentage":
            stop_distance = entry_price * 0.05  # 5% par défaut
        elif method == "atr" and atr:
            stop_distance = atr * 2  # 2x ATR
        else:
            stop_distance = entry_price * 0.05

        stop_loss = entry_price - stop_distance
        return stop_loss

    def calculate_take_profit(self, entry_price, stop_loss, risk_reward=2):
        """
        Calcule le niveau de take profit

        Args:
            entry_price: Prix d'entrée
            stop_loss: Prix du stop loss
            risk_reward: Ratio risque/rendement

        Returns:
            Prix du take profit
        """
        risk = entry_price - stop_loss
        reward = risk * risk_reward
        take_profit = entry_price + reward

        return take_profit
