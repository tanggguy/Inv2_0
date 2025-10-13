"""
Tests unitaires pour le module base_strategy (VERSION FINALE)
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import backtrader as bt
from strategies.base_strategy import BaseStrategy


# Crée un fichier de données temporaire pour toute la session de test
@pytest.fixture(scope="session")
def mock_csv_data(tmpdir_factory):
    """Crée un fichier CSV de données de marché pour les tests."""
    csv_content = """Date,Open,High,Low,Close,Volume
2024-01-15,150.0,152.0,149.0,151.0,100000
2024-01-16,151.2,153.5,150.5,152.5,120000
2024-01-17,152.0,154.0,151.5,153.0,110000
"""
    csv_file = tmpdir_factory.mktemp("data").join("mock_data.csv")
    csv_file.write(csv_content)
    return str(csv_file)


def create_initialized_strategy(strategy_class, data_path, **params):
    """
    Helper pour créer une instance de stratégie correctement initialisée dans un Cerebro.
    C'est la méthode correcte pour tester les stratégies backtrader.
    """
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(10000.00)
    data_feed = bt.feeds.GenericCSVData(
        dataname=data_path, dtformat=("%Y-%m-%d"), openinterest=-1
    )
    cerebro.adddata(data_feed)
    cerebro.addstrategy(strategy_class, **params)
    return cerebro.run()[0]


class TestBaseStrategy:
    """Tests pour la classe BaseStrategy"""

    # ═══════════════════════════════════════════════════════════════════
    # TESTS __init__
    # ═══════════════════════════════════════════════════════════════════

    def test_init_default_values(self, mock_csv_data):
        """Test l'initialisation avec valeurs par défaut"""
        strategy = create_initialized_strategy(BaseStrategy, mock_csv_data)
        assert strategy.order is None
        assert strategy.buyprice is None
        assert strategy.buycomm is None
        assert strategy.trade_count == 0
        assert strategy.params.printlog is True

    def test_init_with_custom_params(self, mock_csv_data):
        """Test l'initialisation avec paramètres personnalisés"""
        strategy = create_initialized_strategy(
            BaseStrategy, mock_csv_data, printlog=False
        )
        assert strategy.params.printlog is False

    @patch("strategies.base_strategy.logger")
    def test_init_logger_called(self, mock_logger, mock_csv_data):
        """Test que le logger est appelé lors de l'initialisation"""
        create_initialized_strategy(BaseStrategy, mock_csv_data)
        mock_logger.info.assert_any_call("Initialisation de BaseStrategy")

    # ═══════════════════════════════════════════════════════════════════
    # TESTS log()
    # ═══════════════════════════════════════════════════════════════════

    @patch("strategies.base_strategy.logger")
    def test_log_with_printlog_enabled(self, mock_logger, mock_csv_data):
        """Test log quand printlog est activé"""
        strategy = create_initialized_strategy(
            BaseStrategy, mock_csv_data, printlog=True
        )
        strategy.log("Test message")

        # CORRECTION : On vérifie le DERNIER appel au logger.
        last_call_args = mock_logger.info.call_args[0][0]
        assert "2024-01-17 - Test message" in last_call_args

    @patch("strategies.base_strategy.logger")
    def test_log_with_printlog_disabled(self, mock_logger, mock_csv_data):
        """Test log quand printlog est désactivé"""
        strategy = create_initialized_strategy(
            BaseStrategy, mock_csv_data, printlog=False
        )
        strategy.log("Ne devrait pas apparaître")
        # Seul le log de __init__ doit passer si printlog=False n'est pas appliqué à l'init.
        # Si __init__ respectait printlog, le count serait 0. On garde 1 pour être sûr.
        assert mock_logger.info.call_count == 1

    # ═══════════════════════════════════════════════════════════════════
    # TESTS notify_order()
    # ═══════════════════════════════════════════════════════════════════

    @pytest.fixture
    def mock_order(self):
        """Fixture pour un ordre mocké simple."""
        order = MagicMock()
        (
            order.Submitted,
            order.Accepted,
            order.Completed,
            order.Canceled,
            order.Margin,
            order.Rejected,
        ) = range(6)
        return order

    def test_notify_order_buy_completed(self, mock_csv_data, mock_order):
        """Test notify_order avec achat complété"""
        strategy = create_initialized_strategy(BaseStrategy, mock_csv_data)

        mock_order.status = mock_order.Completed
        mock_order.isbuy.return_value = True
        mock_order.executed.price = 150.50
        mock_order.executed.value = 15050.00
        mock_order.executed.comm = 7.52

        strategy.notify_order(mock_order)

        assert strategy.buyprice == 150.50
        assert strategy.buycomm == 7.52
        assert strategy.trade_count == 1
        assert strategy.order is None

    def test_notify_order_sell_completed(self, mock_csv_data, mock_order):
        """Test notify_order avec vente complétée"""
        strategy = create_initialized_strategy(BaseStrategy, mock_csv_data)

        mock_order.status = mock_order.Completed
        mock_order.isbuy.return_value = False
        mock_order.issell.return_value = True
        mock_order.executed.price = 160.75
        mock_order.executed.value = 16075.00
        mock_order.executed.comm = 8.03

        strategy.notify_order(mock_order)

        assert strategy.trade_count == 1
        assert strategy.order is None

    def test_notify_order_rejected(self, mock_csv_data, mock_order):
        """Test notify_order avec ordre rejeté"""
        strategy = create_initialized_strategy(BaseStrategy, mock_csv_data)
        strategy.order = "un ordre existant"

        mock_order.status = mock_order.Rejected

        strategy.notify_order(mock_order)

        assert strategy.order is None

    # ═══════════════════════════════════════════════════════════════════
    # TESTS notify_trade()
    # ═══════════════════════════════════════════════════════════════════

    @patch("strategies.base_strategy.logger")
    def test_notify_trade_closed_profit(self, mock_logger, mock_csv_data):
        """Test notify_trade avec trade fermé en profit"""
        strategy = create_initialized_strategy(BaseStrategy, mock_csv_data)

        mock_trade = MagicMock()
        mock_trade.isclosed = True
        mock_trade.pnl = 1500.50
        mock_trade.pnlcomm = 1492.98

        strategy.notify_trade(mock_trade)

        mock_logger.info.assert_any_call(
            "2024-01-17 - TRADE FERMÉ, Profit Brut: 1500.50, Profit Net: 1492.98"
        )
