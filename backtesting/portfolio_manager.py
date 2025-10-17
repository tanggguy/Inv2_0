"""
Portfolio Manager - Gestion de l'allocation du capital entre symboles

Ce module gère:
- Allocation du capital par symbole (equal-weight ou custom)
- Validation des poids
- Calcul de la taille des positions proportionnelle au capital alloué
- Gestion des contraintes de positions simultanées
"""

from typing import Dict, List, Optional
from monitoring.logger import setup_logger

logger = setup_logger("portfolio_manager")


class PortfolioManager:
    """
    Gestionnaire de portefeuille multi-symbole

    Responsabilités:
    - Allouer le capital entre les symboles
    - Valider les poids (somme = 1.0)
    - Calculer les tailles de positions
    - Gérer les limites de positions simultanées
    """

    def __init__(
        self,
        symbols: List[str],
        total_capital: float,
        weights: Optional[Dict[str, float]] = None,
        max_positions: Optional[int] = None,
    ):
        """
        Initialise le gestionnaire de portefeuille

        Args:
            symbols: Liste des symboles à trader
            total_capital: Capital total disponible
            weights: Dict des poids par symbole {symbol: weight}
                     Si None, utilise equal-weight
            max_positions: Nombre maximum de positions simultanées
                          Si None, pas de limite
        """
        self.symbols = symbols
        self.total_capital = total_capital
        self.max_positions = max_positions
        self.open_positions = {}  # {symbol: {'size': X, 'entry_price': Y}}

        # Gérer les poids
        if weights is None:
            # Equal-weight par défaut
            self.weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
            logger.info(f"Allocation equal-weight: {1.0/len(symbols):.2%} par symbole")
        else:
            self.weights = weights
            logger.info("Allocation custom weights fournis")

        # Valider les poids
        self._validate_weights()

        # Calculer les allocations
        self.allocations = self._calculate_allocations()

        self._log_allocation_summary()

    def _validate_weights(self) -> None:
        """
        Valide que les poids sont corrects

        Vérifie:
        1. Tous les symboles ont un poids
        2. Aucun poids négatif
        3. Somme des poids = 1.0 (tolérance 1%)

        Raises:
            ValueError: Si validation échoue
        """
        # Vérifier que tous les symboles ont un poids
        missing_symbols = set(self.symbols) - set(self.weights.keys())
        if missing_symbols:
            raise ValueError(f"Poids manquants pour les symboles: {missing_symbols}")

        # Vérifier symboles en trop
        extra_symbols = set(self.weights.keys()) - set(self.symbols)
        if extra_symbols:
            logger.warning(f"Poids fournis pour symboles non utilisés: {extra_symbols}")
            # Retirer les symboles en trop
            for symbol in extra_symbols:
                del self.weights[symbol]

        # Vérifier poids négatifs
        negative_weights = {s: w for s, w in self.weights.items() if w < 0}
        if negative_weights:
            raise ValueError(f"Poids négatifs détectés: {negative_weights}")

        # Vérifier somme = 1.0 (tolérance 1%)
        total_weight = sum(self.weights.values())
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(
                f"Somme des poids = {total_weight:.4f}, devrait être 1.0 "
                f"(tolérance ±1%). Poids: {self.weights}"
            )

        # Normaliser si légèrement différent de 1.0
        if total_weight != 1.0:
            logger.info(f"Normalisation des poids: {total_weight:.6f} → 1.0")
            self.weights = {s: w / total_weight for s, w in self.weights.items()}

        logger.info("✓ Validation des poids réussie")

    def _calculate_allocations(self) -> Dict[str, float]:
        """
        Calcule le capital alloué à chaque symbole

        Returns:
            Dict {symbol: allocated_capital}
        """
        allocations = {}
        for symbol in self.symbols:
            allocated = self.total_capital * self.weights[symbol]
            allocations[symbol] = allocated

        return allocations

    def _log_allocation_summary(self) -> None:
        """Affiche un résumé de l'allocation"""
        logger.info("=" * 70)
        logger.info("📊 ALLOCATION DU CAPITAL")
        logger.info("=" * 70)
        logger.info(f"Capital total: ${self.total_capital:,.2f}")
        if self.max_positions:
            logger.info(f"Max positions simultanées: {self.max_positions}")
        logger.info("-" * 70)

        for symbol in sorted(self.symbols):
            weight = self.weights[symbol]
            allocated = self.allocations[symbol]
            logger.info(f"  {symbol:6s}: ${allocated:>12,.2f}  ({weight:>6.2%})")

        logger.info("=" * 70)

    def get_allocation(self, symbol: str) -> float:
        """
        Obtient le capital alloué pour un symbole

        Args:
            symbol: Symbole à rechercher

        Returns:
            Capital alloué en dollars

        Raises:
            ValueError: Si symbole inconnu
        """
        if symbol not in self.allocations:
            raise ValueError(f"Symbole inconnu: {symbol}")

        return self.allocations[symbol]

    def get_weight(self, symbol: str) -> float:
        """
        Obtient le poids d'un symbole

        Args:
            symbol: Symbole à rechercher

        Returns:
            Poids (entre 0 et 1)

        Raises:
            ValueError: Si symbole inconnu
        """
        if symbol not in self.weights:
            raise ValueError(f"Symbole inconnu: {symbol}")

        return self.weights[symbol]

    def calculate_position_size(
        self, symbol: str, price: float, allocation_pct: float = 0.95
    ) -> int:
        """
        Calcule la taille de position pour un symbole

        Position sizing proportionnel au capital alloué.
        Par défaut, utilise 95% du capital alloué pour laisser marge.

        Args:
            symbol: Symbole à trader
            price: Prix actuel du symbole
            allocation_pct: % du capital alloué à utiliser (défaut: 0.95)

        Returns:
            Nombre d'actions à acheter (entier)

        Example:
            Capital alloué AAPL: $40,000
            Prix AAPL: $150
            allocation_pct: 0.95
            → Taille = int(40000 * 0.95 / 150) = 253 actions
        """
        if symbol not in self.allocations:
            raise ValueError(f"Symbole inconnu: {symbol}")

        if price <= 0:
            raise ValueError(f"Prix invalide: {price}")

        if not (0 < allocation_pct <= 1):
            raise ValueError(
                f"allocation_pct doit être entre 0 et 1, reçu: {allocation_pct}"
            )

        allocated_capital = self.allocations[symbol]
        usable_capital = allocated_capital * allocation_pct

        size = int(usable_capital / price)

        logger.debug(
            f"Position size {symbol}: {size} actions "
            f"(capital: ${allocated_capital:,.2f}, "
            f"prix: ${price:.2f})"
        )

        return size

    def can_open_position(self) -> bool:
        """
        Vérifie si une nouvelle position peut être ouverte

        Returns:
            True si on peut ouvrir une position, False sinon
        """
        if self.max_positions is None:
            return True  # Pas de limite

        current_count = len(self.open_positions)
        can_open = current_count < self.max_positions

        if not can_open:
            logger.debug(
                f"Limite de positions atteinte: {current_count}/{self.max_positions}"
            )

        return can_open

    def add_position(self, symbol: str, size: int, entry_price: float) -> None:
        """
        Enregistre une nouvelle position ouverte

        Args:
            symbol: Symbole
            size: Taille de la position (nombre d'actions)
            entry_price: Prix d'entrée
        """
        self.open_positions[symbol] = {"size": size, "entry_price": entry_price}

        logger.debug(
            f"Position ouverte: {symbol} - {size} actions @ ${entry_price:.2f}"
        )

    def close_position(self, symbol: str) -> None:
        """
        Ferme une position

        Args:
            symbol: Symbole à fermer
        """
        if symbol in self.open_positions:
            del self.open_positions[symbol]
            logger.debug(f"Position fermée: {symbol}")
        else:
            logger.warning(f"Tentative de fermeture position inexistante: {symbol}")

    def get_open_positions_count(self) -> int:
        """
        Retourne le nombre de positions actuellement ouvertes

        Returns:
            Nombre de positions ouvertes
        """
        return len(self.open_positions)

    def get_open_positions(self) -> Dict[str, Dict]:
        """
        Retourne les positions ouvertes

        Returns:
            Dict {symbol: {'size': X, 'entry_price': Y}}
        """
        return self.open_positions.copy()

    def is_position_open(self, symbol: str) -> bool:
        """
        Vérifie si une position est ouverte pour un symbole

        Args:
            symbol: Symbole à vérifier

        Returns:
            True si position ouverte, False sinon
        """
        return symbol in self.open_positions

    def get_summary(self) -> Dict:
        """
        Retourne un résumé du portefeuille

        Returns:
            Dict avec informations du portefeuille
        """
        return {
            "symbols": self.symbols,
            "total_capital": self.total_capital,
            "weights": self.weights,
            "allocations": self.allocations,
            "max_positions": self.max_positions,
            "open_positions_count": self.get_open_positions_count(),
            "open_positions": self.open_positions,
        }

    def __repr__(self) -> str:
        """Représentation string"""
        return (
            f"PortfolioManager("
            f"symbols={len(self.symbols)}, "
            f"capital=${self.total_capital:,.0f}, "
            f"max_positions={self.max_positions})"
        )
