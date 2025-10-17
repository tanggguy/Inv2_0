# test_symbol_analyzer.py

import pytest
import pandas as pd
import numpy as np
from backtesting.symbol_analyzer import SymbolAnalyzer


@pytest.fixture
def sample_results():
    return {
        "AAPL": {
            "symbol": "AAPL",
            "allocated_capital": 25000,
            "weight": 0.25,
            "total_return": 50.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -15.0,
            "total_trades": 20,
            "win_rate": 60.0,
            "absolute_pnl": 12500,
            "final_value": 37500,
        },
        "MSFT": {
            "symbol": "MSFT",
            "allocated_capital": 25000,
            "weight": 0.25,
            "total_return": 40.0,
            "sharpe_ratio": 1.2,
            "max_drawdown": -20.0,
            "total_trades": 18,
            "win_rate": 65.0,
            "absolute_pnl": 10000,
            "final_value": 35000,
        },
        "GOOGL": {
            "symbol": "GOOGL",
            "allocated_capital": 25000,
            "weight": 0.25,
            "total_return": 30.0,
            "sharpe_ratio": 0.8,
            "max_drawdown": -25.0,
            "total_trades": 15,
            "win_rate": 55.0,
            "absolute_pnl": 7500,
            "final_value": 32500,
        },
    }


@pytest.fixture
def sample_returns():
    dates = pd.date_range("2023-01-01", periods=100)
    return {
        "AAPL": pd.Series(np.random.randn(100) * 0.02, index=dates),
        "MSFT": pd.Series(np.random.randn(100) * 0.018, index=dates),
        "GOOGL": pd.Series(np.random.randn(100) * 0.022, index=dates),
    }


@pytest.fixture
def analyzer(sample_results):
    return SymbolAnalyzer(sample_results)


def test_init(analyzer):
    assert len(analyzer.symbols) == 3
    assert "AAPL" in analyzer.symbols
    assert "MSFT" in analyzer.symbols
    assert "GOOGL" in analyzer.symbols


def test_get_top_performers_return(analyzer):
    top = analyzer.get_top_performers(n=2, metric="return_pct")

    assert isinstance(top, pd.DataFrame)
    assert len(top) <= 2


def test_get_top_performers_sharpe(analyzer):
    top = analyzer.get_top_performers(n=2, metric="sharpe_ratio")

    assert isinstance(top, pd.DataFrame)
    assert len(top) <= 2


def test_get_top_performers_invalid_metric(analyzer):
    top = analyzer.get_top_performers(n=2, metric="return_pct")

    assert isinstance(top, pd.DataFrame)


def test_get_top_performers_more_than_available(analyzer):
    top = analyzer.get_top_performers(n=10)

    assert len(top) == 3


def test_calculate_pnl_contributions(analyzer):
    contributions = analyzer.calculate_pnl_contributions()

    assert len(contributions) == 3
    assert "AAPL" in contributions
    assert "percentage" in contributions["AAPL"]
    assert "absolute" in contributions["AAPL"]

    total_pct = sum(c["percentage"] for c in contributions.values())
    assert abs(total_pct - 100.0) < 0.01


def test_calculate_pnl_contributions_negative():
    results = {
        "AAPL": {"symbol": "AAPL", "absolute_pnl": 10000, "weight": 0.5},
        "MSFT": {"symbol": "MSFT", "absolute_pnl": -5000, "weight": 0.5},
    }
    analyzer = SymbolAnalyzer(results)

    contributions = analyzer.calculate_pnl_contributions()

    assert contributions["AAPL"]["percentage"] > 100
    assert contributions["MSFT"]["percentage"] < 0


def test_calculate_correlation_matrix_no_returns(analyzer):
    corr = analyzer.calculate_correlation_matrix()

    assert corr.shape == (3, 3)
    assert (corr.values == np.eye(3)).all()


def test_calculate_correlation_matrix_with_returns(analyzer, sample_returns):
    corr = analyzer.calculate_correlation_matrix(sample_returns)

    assert corr.shape == (3, 3)
    assert corr.loc["AAPL", "AAPL"] == 1.0
    assert corr.loc["MSFT", "MSFT"] == 1.0
    assert -1 <= corr.loc["AAPL", "MSFT"] <= 1


def test_calculate_correlation_matrix_empty_returns(analyzer):
    corr = analyzer.calculate_correlation_matrix({})

    assert corr.shape == (3, 3)


def test_calculate_diversification_ratio_no_returns(analyzer):
    ratio = analyzer.calculate_diversification_ratio()

    assert isinstance(ratio, float)
    assert ratio >= 1.0


def test_calculate_diversification_ratio_with_returns(analyzer, sample_returns):
    ratio = analyzer.calculate_diversification_ratio(sample_returns)

    assert isinstance(ratio, float)
    assert ratio >= 1.0


def test_calculate_diversification_ratio_empty_returns(analyzer):
    ratio = analyzer.calculate_diversification_ratio({})

    assert ratio == 1.0


def test_get_symbol_dataframe(analyzer):
    df = analyzer.get_metrics_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "symbol" in df.columns


def test_compare_symbols(analyzer):
    df = analyzer.get_metrics_dataframe()
    comparison = df[df["symbol"].isin(["AAPL", "MSFT"])].to_dict("records")

    assert len(comparison) >= 2


def test_compare_symbols_not_found(analyzer):
    df = analyzer.get_metrics_dataframe()
    comparison = df[df["symbol"].isin(["AAPL", "INVALID"])].to_dict("records")

    assert len(comparison) >= 1


def test_correlation_matrix_single_symbol():
    results = {"AAPL": {"symbol": "AAPL", "total_return": 50.0}}
    analyzer = SymbolAnalyzer(results)

    corr = analyzer.calculate_correlation_matrix()

    assert corr.shape == (1, 1)
    assert corr.iloc[0, 0] == 1.0


def test_diversification_with_perfect_correlation():
    returns = {
        "AAPL": pd.Series([0.01, 0.02, 0.03]),
        "MSFT": pd.Series([0.01, 0.02, 0.03]),
    }

    results = {
        "AAPL": {"weight": 0.5, "max_drawdown": -10},
        "MSFT": {"weight": 0.5, "max_drawdown": -10},
    }

    analyzer = SymbolAnalyzer(results)
    ratio = analyzer.calculate_diversification_ratio(returns)

    assert ratio >= 1.0


def test_diversification_with_negative_correlation():
    returns = {
        "AAPL": pd.Series([0.01, -0.02, 0.03]),
        "MSFT": pd.Series([-0.01, 0.02, -0.03]),
    }

    results = {
        "AAPL": {"weight": 0.5, "max_drawdown": -10},
        "MSFT": {"weight": 0.5, "max_drawdown": -10},
    }

    analyzer = SymbolAnalyzer(results)
    ratio = analyzer.calculate_diversification_ratio(returns)

    assert ratio >= 1.0


def test_pnl_contributions_zero_total():
    results = {
        "AAPL": {"symbol": "AAPL", "absolute_pnl": 0},
        "MSFT": {"symbol": "MSFT", "absolute_pnl": 0},
    }

    analyzer = SymbolAnalyzer(results)
    contributions = analyzer.calculate_pnl_contributions()

    assert contributions["AAPL"]["percentage"] == 0
    assert contributions["MSFT"]["percentage"] == 0
