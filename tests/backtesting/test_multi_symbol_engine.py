# test_multi_symbol_engine.py
import pytest
from unittest.mock import MagicMock, patch, call
import pandas as pd
from datetime import datetime
import backtrader as bt
from collections import OrderedDict

# Mock the logger at the module level to ensure it's patched during import
mock_logger = MagicMock()
patcher = patch("monitoring.logger.setup_logger", return_value=mock_logger)
patcher.start()

# Import the class to be tested AFTER the patch is active
from backtesting.multi_symbol_engine import MultiSymbolBacktestEngine

# Stop the patcher after the import
patcher.stop()


@pytest.fixture
def mock_dependencies(mocker):
    """Mocks all external dependencies for the engine."""
    # We patch the logger within the engine's module specifically for tests
    mocker.patch("backtesting.multi_symbol_engine.logger", mock_logger)

    # Mock the parent's __init__ only for initialization tests
    mock_parent_init = mocker.patch(
        "backtesting.backtest_engine.BacktestEngine.__init__"
    )
    mock_portfolio_manager = mocker.patch(
        "backtesting.portfolio_manager.PortfolioManager"
    )
    mock_thread_pool = mocker.patch("concurrent.futures.ThreadPoolExecutor")
    mock_cerebro = mocker.patch("backtrader.Cerebro")
    mock_create_data_feed = mocker.patch("data.data_fetcher.create_data_feed")
    mock_datetime = mocker.patch("datetime.datetime")

    return {
        "ParentInit": mock_parent_init,
        "PortfolioManager": mock_portfolio_manager,
        "ThreadPoolExecutor": mock_thread_pool,
        "Cerebro": mock_cerebro,
        "create_data_feed": mock_create_data_feed,
        "datetime": mock_datetime,
        "logger": mock_logger,
    }


@pytest.fixture
def engine_instance(mocker):
    """
    Provides a valid instance of MultiSymbolBacktestEngine for testing.
    We avoid mocking super().__init__ here to ensure instance attributes are set.
    """
    # Mock dependencies that are called during initialization
    mocker.patch("backtesting.portfolio_manager.PortfolioManager")
    mocker.patch("backtesting.multi_symbol_engine.logger", mock_logger)

    # Let the parent __init__ run to set attributes correctly
    engine = MultiSymbolBacktestEngine(
        strategy_name="TestStrategy",
        symbols=["AAPL", "GOOG"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
        verbose=False,
    )

    # Attach a mock data_handler, which would normally be set by the parent
    engine.data_handler = MagicMock()
    return engine


class TestMultiSymbolBacktestEngine:
    """Test suite for the MultiSymbolBacktestEngine class."""

    def test_initialization_default_weights(self, mock_dependencies):
        """Test nominal initialization with equal symbol weights."""
        symbols = ["AAPL", "GOOG"]
        capital = 100000
        MultiSymbolBacktestEngine(
            strategy_name="TestStrategy",
            symbols=symbols,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=capital,
            symbol_weights=None,
            max_positions=5,
            verbose=True,
        )

        # Verify parent class is initialized
        mock_dependencies["ParentInit"].assert_called_once_with(
            strategy_name="TestStrategy",
            symbols=symbols,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=capital,
            verbose=True,
        )

        # Verify PortfolioManager is initialized correctly
        mock_dependencies["PortfolioManager"].assert_called_once_with(
            symbols=symbols, total_capital=capital, weights=None, max_positions=5
        )

    def test_initialization_custom_weights(self, mock_dependencies):
        """Test initialization with custom symbol weights."""
        symbols = ["AAPL", "GOOG"]
        capital = 200000
        weights = {"AAPL": 0.7, "GOOG": 0.3}
        MultiSymbolBacktestEngine(
            strategy_name="TestStrategy",
            symbols=symbols,
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=capital,
            symbol_weights=weights,
        )
        mock_dependencies["PortfolioManager"].assert_called_once_with(
            symbols=symbols, total_capital=capital, weights=weights, max_positions=None
        )

    def test_run_successful_flow(self, engine_instance, mocker):
        """Test the main run method's successful execution flow."""
        mocker.patch.object(
            engine_instance, "_run_all_symbol_backtests", return_value={"AAPL": {}}
        )
        mocker.patch.object(
            engine_instance, "_aggregate_results", return_value={"aggregated": "data"}
        )
        mocker.patch.object(engine_instance, "_print_summary")
        engine_instance.portfolio_manager.get_summary.return_value = {
            "info": "portfolio"
        }

        results = engine_instance.run()

        engine_instance._run_all_symbol_backtests.assert_called_once()
        engine_instance._aggregate_results.assert_called_once()
        engine_instance._print_summary.assert_called_once()
        assert results is not None
        assert results["aggregated"] == {"aggregated": "data"}
        assert results["by_symbol"] == {"AAPL": {}}

    def test_run_no_backtest_results(self, engine_instance, mocker):
        """Test run method when no symbol backtests succeed."""
        mocker.patch.object(
            engine_instance, "_run_all_symbol_backtests", return_value={}
        )
        mocker.patch.object(engine_instance, "_aggregate_results")

        results = engine_instance.run()

        engine_instance._run_all_symbol_backtests.assert_called_once()
        engine_instance._aggregate_results.assert_not_called()
        mock_logger.error.assert_called_with("Aucun résultat de backtest disponible")
        assert results is None

    def test_run_all_symbol_backtests_parallel(
        self, engine_instance, mock_dependencies, mocker
    ):
        """Test running backtests in parallel mode."""
        engine_instance.verbose = False
        mock_executor = mock_dependencies[
            "ThreadPoolExecutor"
        ].return_value.__enter__.return_value
        mock_future = MagicMock()
        mock_future.result.return_value = {"result": "success"}
        mock_executor.submit.return_value = mock_future
        mocker.patch(
            "concurrent.futures.as_completed", return_value=[mock_future, mock_future]
        )

        engine_instance._run_all_symbol_backtests()

        assert mock_executor.submit.call_count == 2
        mock_logger.info.assert_any_call("Mode parallèle (max 4 threads)")

    def test_run_all_symbol_backtests_sequential(self, engine_instance, mocker):
        """Test running backtests in sequential (verbose) mode."""
        engine_instance.verbose = True
        mocker.patch.object(
            engine_instance,
            "_run_symbol_backtest",
            side_effect=[{"res": 1}, {"res": 2}],
        )

        results = engine_instance._run_all_symbol_backtests()

        assert engine_instance._run_symbol_backtest.call_count == 2
        assert results == {"AAPL": {"res": 1}, "GOOG": {"res": 2}}
        mock_logger.info.assert_any_call("Mode séquentiel (verbose activé)")

    def test_run_all_symbol_backtests_with_failures(
        self, engine_instance, mock_dependencies, mocker
    ):
        """Test parallel execution when some backtests fail."""
        engine_instance.verbose = False
        mock_executor = mock_dependencies[
            "ThreadPoolExecutor"
        ].return_value.__enter__.return_value

        future_ok = MagicMock()
        future_ok.result.return_value = {"status": "ok"}
        future_fail = MagicMock()
        future_fail.result.side_effect = Exception("Test Error")

        future_to_symbol = {future_ok: "AAPL", future_fail: "GOOG"}
        mocker.patch(
            "concurrent.futures.as_completed", return_value=[future_ok, future_fail]
        )
        mock_executor.submit.side_effect = lambda func, symbol: {
            s: f for f, s in future_to_symbol.items()
        }[symbol]

        results = engine_instance._run_all_symbol_backtests()

        assert "AAPL" in results
        assert "GOOG" not in results
        mock_logger.error.assert_called_with("✗ Erreur GOOG: Test Error")

    def test_run_symbol_backtest_success(
        self, engine_instance, mock_dependencies, mocker
    ):
        """Test a single symbol backtest execution successfully."""
        symbol = "AAPL"
        # Configure mocks to return real numbers to avoid TypeError on formatting
        engine_instance.portfolio_manager.get_allocation.return_value = 50000.0
        engine_instance.portfolio_manager.get_weight.return_value = 0.5

        engine_instance.data_handler.fetch_data.return_value = pd.DataFrame(
            {"close": [100]}
        )
        mocker.patch.object(engine_instance, "_load_strategy", return_value=MagicMock())
        mock_cerebro = mock_dependencies["Cerebro"].return_value
        mock_strategy_instance = MagicMock()
        mock_cerebro.run.return_value = [mock_strategy_instance]
        mocker.patch.object(engine_instance, "_collect_daily_returns_from_analyzer")
        mocker.patch.object(
            engine_instance,
            "_analyze_symbol_results",
            return_value={"final": "results"},
        )

        result = engine_instance._run_symbol_backtest(symbol)

        engine_instance.data_handler.fetch_data.assert_called_once_with(
            symbol, "2023-01-01", "2023-12-31"
        )
        assert result == {"final": "results"}

    @pytest.mark.parametrize("df_return", [None, pd.DataFrame()])
    def test_run_symbol_backtest_no_data(self, engine_instance, df_return):
        """Test symbol backtest when data fetching fails."""
        engine_instance.portfolio_manager.get_allocation.return_value = 50000.0
        engine_instance.portfolio_manager.get_weight.return_value = 0.5
        engine_instance.data_handler.fetch_data.return_value = df_return

        result = engine_instance._run_symbol_backtest("AAPL")

        assert result is None
        mock_logger.warning.assert_called_with("Pas de données pour AAPL")

    def test_run_symbol_backtest_strategy_load_fails(self, engine_instance, mocker):
        """Test symbol backtest when strategy loading fails."""
        engine_instance.portfolio_manager.get_allocation.return_value = 50000.0
        engine_instance.portfolio_manager.get_weight.return_value = 0.5
        engine_instance.data_handler.fetch_data.return_value = pd.DataFrame(
            {"close": [100]}
        )
        mocker.patch.object(engine_instance, "_load_strategy", return_value=None)

        result = engine_instance._run_symbol_backtest("AAPL")

        assert result is None
        mock_logger.error.assert_called_with(
            "Impossible de charger stratégie pour AAPL"
        )

    def test_aggregate_results(self, engine_instance):
        """Test the aggregation of results from all symbols."""
        engine_instance.symbol_results = {
            "AAPL": {
                "initial_value": 50000,
                "final_value": 60000,
                "absolute_pnl": 10000,
                "sharpe_ratio": 1.2,
                "max_drawdown": -10.0,
                "weight": 0.5,
                "total_trades": 10,
                "won_trades": 8,
                "lost_trades": 2,
            },
            "GOOG": {
                "initial_value": 50000,
                "final_value": 45000,
                "absolute_pnl": -5000,
                "sharpe_ratio": -0.5,
                "max_drawdown": -15.0,
                "weight": 0.5,
                "total_trades": 5,
                "won_trades": 1,
                "lost_trades": 4,
            },
        }

        agg = engine_instance._aggregate_results()

        assert agg["portfolio_return"] == pytest.approx(5.0)
        assert agg["portfolio_sharpe"] == pytest.approx(0.35)
        assert agg["portfolio_max_drawdown"] == -15.0

    def test_collect_daily_returns_from_analyzer(self, engine_instance):
        """Test collecting daily returns and values from the analyzer."""
        symbol = "TSLA"
        mock_strategy = MagicMock()
        dates = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
        returns = [0.01, -0.005]
        mock_strategy.analyzers.time_return.get_analysis.return_value = OrderedDict(
            zip(dates, returns)
        )
        engine_instance.portfolio_manager.get_allocation.return_value = 10000

        engine_instance._collect_daily_returns_from_analyzer(mock_strategy, symbol)

        expected_values = pd.Series(
            [10000 * 1.01, 10000 * 1.01 * (1 - 0.005)],
            index=pd.DatetimeIndex(dates),
            name=symbol,  # Add name to match the implementation
        )
        pd.testing.assert_series_equal(
            engine_instance.daily_values[symbol], expected_values
        )
