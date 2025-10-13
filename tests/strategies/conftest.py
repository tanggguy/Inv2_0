"""
Configuration partagée pour les tests de stratégies

Ce fichier contient des fixtures et helpers réutilisables
pour tous les tests de stratégies de trading.
"""

import pytest
from unittest.mock import MagicMock, Mock
from datetime import date
from strategies.base_strategy import BaseStrategy


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES POUR DATA FEEDS
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_data():
    """
    Mock d'un data feed Backtrader

    Returns:
        MagicMock: Data feed mocké avec OHLCV et datetime
    """
    mock = MagicMock()

    # Date par défaut
    mock.datetime.date.return_value = date(2024, 1, 15)

    # Prix OHLCV typiques
    mock.close = [100.0]
    mock.open = [99.0]
    mock.high = [101.0]
    mock.low = [98.0]
    mock.volume = [1000000]

    # Index pour accès historique
    mock.__getitem__ = lambda self, x: 100.0 if x == 0 else 99.0

    return mock


@pytest.fixture
def mock_data_series():
    """
    Mock d'un data feed avec série de données

    Utile pour tester les indicateurs qui ont besoin d'historique

    Returns:
        MagicMock: Data feed avec série de prix
    """
    mock = MagicMock()

    # Série de dates
    mock.datetime.date.return_value = date(2024, 1, 15)

    # Série de prix (derniers 20 jours)
    prices = [100 + i * 0.5 for i in range(20)]
    mock.close = prices
    mock.open = [p - 0.5 for p in prices]
    mock.high = [p + 1.0 for p in prices]
    mock.low = [p - 1.0 for p in prices]
    mock.volume = [1000000 + i * 10000 for i in range(20)]

    # Accès par index
    def get_item(idx):
        if idx == 0:
            return prices[-1]
        elif idx < 0 and abs(idx) <= len(prices):
            return prices[idx]
        return prices[0]

    mock.__getitem__ = get_item

    return mock


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES POUR BROKER
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_broker():
    """
    Mock du broker Backtrader

    Returns:
        MagicMock: Broker mocké avec capital de 100,000
    """
    broker = MagicMock()
    broker.getvalue.return_value = 100000.0
    broker.getcash.return_value = 100000.0
    return broker


@pytest.fixture
def mock_broker_with_position():
    """
    Mock du broker avec une position ouverte

    Returns:
        MagicMock: Broker avec position en cours
    """
    broker = MagicMock()
    broker.getvalue.return_value = 110000.0  # +10% profit
    broker.getcash.return_value = 60000.0  # 60k en cash, 50k en position

    # Mock de la position
    position = MagicMock()
    position.size = 500  # 500 actions
    position.price = 100.0  # Prix d'achat
    broker.getposition.return_value = position

    return broker


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES POUR ORDRES
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_order():
    """
    Mock d'un ordre Backtrader

    Returns:
        MagicMock: Ordre avec tous les statuts possibles
    """
    order = MagicMock()

    # Statuts possibles
    order.Submitted = 0
    order.Accepted = 1
    order.Completed = 2
    order.Canceled = 3
    order.Margin = 4
    order.Rejected = 5

    # Exécution par défaut
    order.executed.price = 100.0
    order.executed.value = 10000.0
    order.executed.comm = 5.0
    order.executed.size = 100

    # Type d'ordre
    order.isbuy.return_value = True
    order.issell.return_value = False

    return order


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def create_strategy():
    """
    Factory fixture pour créer des stratégies avec mocks Backtrader

    Usage:
        def test_my_strategy(create_strategy):
            strategy = create_strategy(MyStrategy)
            assert strategy is not None

    Returns:
        Callable: Fonction pour créer des stratégies mockées
    """

    def _create(strategy_class=BaseStrategy, **params):
        """
        Crée une instance de stratégie avec mocks Backtrader

        Args:
            strategy_class: Classe de stratégie à instancier
            **params: Paramètres optionnels pour la stratégie

        Returns:
            Instance de stratégie avec mocks appropriés
        """
        # Créer l'instance
        if params:
            strategy = strategy_class(params=params)
        else:
            strategy = strategy_class()

        # Mock des attributs internes Backtrader requis
        strategy._next_stid = 0
        strategy._id = 0
        strategy.env = MagicMock()

        return strategy

    return _create


@pytest.fixture
def create_full_strategy(mock_data, mock_broker):
    """
    Factory fixture pour créer des stratégies complètement configurées

    Usage:
        def test_my_strategy(create_full_strategy):
            strategy = create_full_strategy(MyStrategy)
            strategy.next()  # Peut appeler next() car tout est configuré

    Returns:
        Callable: Fonction pour créer des stratégies prêtes à l'emploi
    """

    def _create(strategy_class=BaseStrategy, **params):
        """
        Crée une instance de stratégie complètement configurée

        Args:
            strategy_class: Classe de stratégie à instancier
            **params: Paramètres optionnels pour la stratégie

        Returns:
            Instance de stratégie avec data feed et broker
        """
        # Créer l'instance
        if params:
            strategy = strategy_class(params=params)
        else:
            strategy = strategy_class()

        # Mock des attributs Backtrader
        strategy._next_stid = 0
        strategy._id = 0
        strategy.env = MagicMock()

        # Ajouter data et broker
        strategy.datas = [mock_data]
        strategy.broker = mock_broker

        # Position mock
        strategy.position = MagicMock()
        strategy.position.size = 0  # Pas de position par défaut

        return strategy

    return _create


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES POUR INDICATEURS
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_indicator():
    """
    Mock d'un indicateur Backtrader (SMA, RSI, etc.)

    Returns:
        MagicMock: Indicateur avec valeurs de test
    """
    indicator = MagicMock()

    # Valeur actuelle
    indicator.__getitem__ = lambda self, x: 50.0 if x == 0 else 49.0

    # Lignes (pour BB, MACD, etc.)
    indicator.lines = MagicMock()
    indicator.lines.top = [55.0]
    indicator.lines.mid = [50.0]
    indicator.lines.bot = [45.0]

    return indicator


# ═══════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════


def assert_order_placed(strategy, order_type="buy"):
    """
    Helper pour vérifier qu'un ordre a été placé

    Args:
        strategy: Instance de stratégie à vérifier
        order_type: Type d'ordre ('buy' ou 'sell')
    """
    assert strategy.order is not None, f"Aucun ordre {order_type} placé"


def assert_no_order_placed(strategy):
    """
    Helper pour vérifier qu'aucun ordre n'a été placé

    Args:
        strategy: Instance de stratégie à vérifier
    """
    assert strategy.order is None, "Un ordre a été placé alors qu'il ne devrait pas"


def create_price_data(prices, dates=None):
    """
    Crée un mock de data feed avec des prix personnalisés

    Args:
        prices: Liste des prix de clôture
        dates: Liste optionnelle de dates (génère automatiquement si None)

    Returns:
        MagicMock: Data feed avec les prix fournis
    """
    mock = MagicMock()

    # Dates
    if dates is None:
        from datetime import timedelta

        base_date = date(2024, 1, 1)
        dates = [base_date + timedelta(days=i) for i in range(len(prices))]

    mock.datetime.date.side_effect = dates

    # Prix
    mock.close = prices
    mock.open = [p * 0.99 for p in prices]
    mock.high = [p * 1.01 for p in prices]
    mock.low = [p * 0.98 for p in prices]
    mock.volume = [1000000] * len(prices)

    # Accès par index
    def get_item(idx):
        if idx == 0:
            return prices[-1]
        elif idx < 0 and abs(idx) <= len(prices):
            return prices[idx]
        return prices[0]

    mock.__getitem__ = get_item

    return mock


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION PYTEST
# ═══════════════════════════════════════════════════════════════════════════


def pytest_configure(config):
    """Configuration globale des tests"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
