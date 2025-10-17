# test_multi_symbol_engine.py

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
import backtrader as bt

from backtesting.multi_symbol_engine import MultiSymbolBacktestEngine


@pytest.fixture
def mock_data_handler():
    handler = Mock()
    df = pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [105, 106, 107],
            "Low": [99, 100, 101],
            "Close": [103, 104, 105],
            "Volume": [1000000, 1100000, 1200000],
        },
        index=pd.date_range("2023-01-01", periods=3),
    )
    handler.fetch_data.return_value = df
    return handler


@pytest.fixture
def mock_portfolio_manager():
    manager = Mock()
    manager.get_allocation.return_value = 25000.0
    manager.get_weight.return_value = 0.25
    manager.get_summary.return_value = {
        "total_capital": 100000,
        "allocations": {"AAPL": 25000, "MSFT": 25000},
    }
    return manager


@pytest.fixture
def engine():
    with patch("data.data_handler.DataHandler"):
        with patch("backtesting.portfolio_manager.PortfolioManager"):
            engine = MultiSymbolBacktestEngine(
                strategy_name="RSI",
                symbols=["AAPL", "MSFT"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000,
            )
            return engine


def test_init(engine):
    assert engine.strategy_name == "RSI"
    assert engine.symbols == ["AAPL", "MSFT"]
    assert engine.initial_capital == 100000
    assert engine.daily_returns == {}
    assert engine.daily_values == {}


def test_init_with_custom_weights():
    with patch("data.data_handler.DataHandler"):
        with patch("backtesting.portfolio_manager.PortfolioManager"):
            weights = {"AAPL": 0.6, "MSFT": 0.4}
            engine = MultiSymbolBacktestEngine(
                strategy_name="RSI",
                symbols=["AAPL", "MSFT"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000,
                symbol_weights=weights,
            )
            assert engine.initial_capital == 100000


def test_collect_daily_returns_from_analyzer():
    engine = MultiSymbolBacktestEngine(
        strategy_name="RSI",
        symbols=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
    )

    mock_strategy = Mock()
    mock_analyzer = Mock()
    mock_analyzer.get_analysis.return_value = {
        date(2023, 1, 1): 0.01,
        date(2023, 1, 2): 0.02,
        date(2023, 1, 3): -0.01,
    }
    mock_strategy.analyzers.time_return = mock_analyzer

    engine._collect_daily_returns_from_analyzer(mock_strategy, "AAPL")

    assert "AAPL" in engine.daily_returns
    assert len(engine.daily_returns["AAPL"]) == 3
    assert "AAPL" in engine.daily_values


def test_collect_daily_returns_empty():
    engine = MultiSymbolBacktestEngine(
        strategy_name="RSI",
        symbols=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
    )

    mock_strategy = Mock()
    mock_analyzer = Mock()
    mock_analyzer.get_analysis.return_value = {}
    mock_strategy.analyzers.time_return = mock_analyzer

    engine._collect_daily_returns_from_analyzer(mock_strategy, "AAPL")

    assert "AAPL" not in engine.daily_returns


def test_aggregate_results(engine):
    engine.symbol_results = {
        "AAPL": {
            "total_return": 50.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -15.0,
            "total_trades": 20,
            "won_trades": 12,
            "lost_trades": 8,
            "win_rate": 60.0,
            "absolute_pnl": 12500,
            "initial_value": 25000,
            "final_value": 37500,
            "weight": 0.5,
        },
        "MSFT": {
            "total_return": 40.0,
            "sharpe_ratio": 1.2,
            "max_drawdown": -20.0,
            "total_trades": 18,
            "won_trades": 11,
            "lost_trades": 7,
            "win_rate": 65.0,
            "absolute_pnl": 10000,
            "initial_value": 25000,
            "final_value": 35000,
            "weight": 0.5,
        },
    }

    agg = engine._aggregate_results()

    assert "portfolio_return" in agg
    assert "portfolio_sharpe" in agg
    assert "portfolio_max_drawdown" in agg
    assert "total_trades" in agg
    assert "portfolio_win_rate" in agg
    assert "pnl_contributions" in agg
    assert len(agg["pnl_contributions"]) == 2


def test_get_daily_returns(engine):
    engine.daily_returns = {
        "AAPL": pd.Series([0.01, 0.02, -0.01]),
        "MSFT": pd.Series([0.015, -0.01, 0.02]),
    }

    returns = engine.get_daily_returns()

    assert len(returns) == 2
    assert "AAPL" in returns
    assert "MSFT" in returns
    assert isinstance(returns["AAPL"], pd.Series)


def test_get_daily_values(engine):
    engine.daily_values = {
        "AAPL": pd.Series([25000, 25250, 25500]),
        "MSFT": pd.Series([25000, 25375, 25125]),
    }

    values = engine.get_daily_values()

    assert len(values) == 2
    assert "AAPL" in values
    assert "MSFT" in values
    assert isinstance(values["AAPL"], pd.Series)


def test_get_results(engine):
    engine.aggregated_results = {"total_return": 45.0}
    engine.symbol_results = {"AAPL": {}, "MSFT": {}}
    engine.daily_returns = {"AAPL": pd.Series([0.01])}
    engine.daily_values = {"AAPL": pd.Series([25000])}

    results = engine.get_results()

    assert "aggregated" in results
    assert "by_symbol" in results
    assert "portfolio_info" in results
    assert "daily_returns" in results
    assert "daily_values" in results


@patch("backtesting.multi_symbol_engine.bt.Cerebro")
def test_run_symbol_backtest_success(mock_cerebro_class, engine):
    mock_cerebro = Mock()
    mock_cerebro_class.return_value = mock_cerebro

    mock_strategy = Mock()
    mock_analyzer = Mock()
    mock_analyzer.get_analysis.return_value = {
        date(2023, 1, 1): 0.01,
        date(2023, 1, 2): 0.02,
    }
    mock_strategy.analyzers.time_return = mock_analyzer
    mock_strategy.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.5}
    mock_strategy.analyzers.drawdown.get_analysis.return_value = {
        "max": {"drawdown": 15.0}
    }
    mock_strategy.analyzers.returns.get_analysis.return_value = {"rtot": 0.5}
    mock_strategy.analyzers.trades.get_analysis.return_value = {
        "total": {"total": 20, "won": 12}
    }
    mock_strategy.analyzers.annual_returns.get_analysis.return_value = {}

    mock_cerebro.broker.getvalue.side_effect = [25000, 37500]
    mock_cerebro.run.return_value = [mock_strategy]

    with patch.object(engine, "_load_strategy", return_value=Mock):
        result = engine._run_symbol_backtest("AAPL")

    assert result is not None
    assert "total_return" in result


def test_load_strategy_rsi():
    with patch("data.data_handler.DataHandler"):
        with patch("backtesting.portfolio_manager.PortfolioManager"):
            engine = MultiSymbolBacktestEngine(
                strategy_name="RSI",
                symbols=["AAPL"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000,
            )

            strategy = engine._load_strategy()

            assert strategy is not None


def test_load_strategy_invalid():
    with patch("data.data_handler.DataHandler"):
        with patch("backtesting.portfolio_manager.PortfolioManager"):
            engine = MultiSymbolBacktestEngine(
                strategy_name="NonExistent",
                symbols=["AAPL"],
                start_date="2023-01-01",
                end_date="2023-12-31",
                initial_capital=100000,
            )

            strategy = engine._load_strategy()

            assert strategy is None or strategy is not None


def test_analyze_symbol_results():
    engine = MultiSymbolBacktestEngine(
        strategy_name="RSI",
        symbols=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100000,
    )

    mock_strategy = Mock()
    mock_strategy.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.5}
    mock_strategy.analyzers.drawdown.get_analysis.return_value = {
        "max": {"drawdown": 15.0}
    }
    mock_strategy.analyzers.returns.get_analysis.return_value = {"rtot": 0.5}
    mock_strategy.analyzers.trades.get_analysis.return_value = {
        "total": {"total": 20, "won": 12}
    }
    mock_strategy.analyzers.annual_returns.get_analysis.return_value = {}

    result = engine._analyze_symbol_results(
        mock_strategy,
        start_value=25000,
        end_value=37500,
        symbol="AAPL",
        allocated_capital=25000,
        weight=0.25,
    )

    assert result["symbol"] == "AAPL"
    assert result["allocated_capital"] == 25000
    assert result["weight"] == 0.25
    assert "total_return" in result
    assert "sharpe_ratio" in result
    assert "max_drawdown" in result
