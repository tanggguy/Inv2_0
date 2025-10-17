# test_plotly_charts.py

import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from backtesting.plotly_charts import PlotlyChartsGenerator


@pytest.fixture
def sample_results():
    dates = pd.date_range("2023-01-01", periods=100)
    return {
        "aggregated": {
            "total_return": 45.0,
            "sharpe_ratio": 1.3,
            "max_drawdown": -18.0,
            "pnl_contributions": {
                "AAPL": {"absolute": 12500, "percentage": 55.5},
                "MSFT": {"absolute": 10000, "percentage": 44.5},
            },
        },
        "by_symbol": {
            "AAPL": {"total_return": 50.0, "sharpe_ratio": 1.5, "max_drawdown": -15.0},
            "MSFT": {"total_return": 40.0, "sharpe_ratio": 1.1, "max_drawdown": -20.0},
        },
        "daily_returns": {
            "AAPL": pd.Series(np.random.randn(100) * 0.02, index=dates),
            "MSFT": pd.Series(np.random.randn(100) * 0.018, index=dates),
        },
        "daily_values": {
            "AAPL": pd.Series(
                25000 * (1 + np.random.randn(100) * 0.02).cumprod(), index=dates
            ),
            "MSFT": pd.Series(
                25000 * (1 + np.random.randn(100) * 0.018).cumprod(), index=dates
            ),
        },
    }


@pytest.fixture
def generator(sample_results):
    return PlotlyChartsGenerator(sample_results)


def test_init(generator):
    assert generator.results is not None
    assert generator.aggregated is not None
    assert generator.by_symbol is not None
    assert generator.daily_returns is not None
    assert generator.daily_values is not None


def test_init_empty():
    gen = PlotlyChartsGenerator({})

    assert gen.aggregated == {}
    assert gen.by_symbol == {}
    assert gen.daily_returns == {}
    assert gen.daily_values == {}


def test_generate_equity_curves(generator):
    fig = generator.generate_equity_curves()

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.layout.title.text == "📈 Equity Curves Comparées"


def test_generate_equity_curves_no_data():
    gen = PlotlyChartsGenerator({"daily_values": {}})
    fig = gen.generate_equity_curves()

    assert fig is None


def test_generate_correlation_heatmap(generator):
    fig = generator.generate_correlation_heatmap(generator.daily_returns)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.layout.title.text == "🔗 Matrice de Corrélation des Returns"


def test_generate_correlation_heatmap_no_data(generator):
    fig = generator.generate_correlation_heatmap({})

    assert fig is None


def test_generate_return_vs_drawdown_scatter(generator):
    fig = generator.generate_return_vs_drawdown_scatter()

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.layout.title.text == "📊 Return vs Drawdown (Risk/Reward)"


def test_generate_return_vs_drawdown_scatter_no_data():
    gen = PlotlyChartsGenerator({"by_symbol": {}})
    fig = gen.generate_return_vs_drawdown_scatter()

    assert fig is None


def test_generate_pnl_contributions_bar(generator):
    fig = generator.generate_pnl_contributions_bar()

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.layout.title.text == "💰 Contributions au P&L Total"


def test_generate_pnl_contributions_bar_no_data():
    gen = PlotlyChartsGenerator({"aggregated": {}})
    fig = gen.generate_pnl_contributions_bar()

    assert fig is None


def test_generate_rolling_correlation(generator):
    fig = generator.generate_rolling_correlation(
        generator.daily_returns, window=20, symbol1="AAPL", symbol2="MSFT"
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1


def test_generate_rolling_correlation_default_symbols(generator):
    fig = generator.generate_rolling_correlation(generator.daily_returns, window=20)

    assert isinstance(fig, go.Figure)


def test_generate_rolling_correlation_insufficient_data():
    returns = {"AAPL": pd.Series([0.01])}
    gen = PlotlyChartsGenerator({"daily_returns": returns})

    fig = gen.generate_rolling_correlation(returns, window=20)

    assert fig is None


def test_generate_all_rolling_correlations(generator):
    fig = generator.generate_all_rolling_correlations(
        generator.daily_returns, window=20
    )

    assert isinstance(fig, go.Figure)


def test_generate_all_rolling_correlations_insufficient_symbols():
    returns = {"AAPL": pd.Series([0.01])}
    gen = PlotlyChartsGenerator({"daily_returns": returns})

    fig = gen.generate_all_rolling_correlations(returns)

    assert fig is None


def test_generate_cumulative_returns_comparison(generator):
    fig = generator.generate_cumulative_returns_comparison()

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2


def test_generate_cumulative_returns_comparison_no_data():
    gen = PlotlyChartsGenerator({"daily_returns": {}})
    fig = gen.generate_cumulative_returns_comparison()

    assert fig is None


def test_generate_all_charts(generator):
    charts = generator.generate_all_charts()

    assert isinstance(charts, dict)
    assert "equity_curves" in charts
    assert "cumulative_returns" in charts
    assert "correlation_heatmap" in charts
    assert "return_vs_drawdown" in charts
    assert "pnl_contributions" in charts
    assert "rolling_correlations" in charts


def test_generate_all_charts_empty():
    gen = PlotlyChartsGenerator({})
    charts = gen.generate_all_charts()

    assert isinstance(charts, dict)
    assert len(charts) == 0


def test_equity_curves_formatting(generator):
    fig = generator.generate_equity_curves()

    assert fig.layout.xaxis.title.text == "Date"
    assert fig.layout.yaxis.title.text == "Portfolio Value ($)"
    assert fig.layout.height == 500


def test_correlation_heatmap_colorscale(generator):
    fig = generator.generate_correlation_heatmap(generator.daily_returns)

    assert fig.data[0].zmin == -1
    assert fig.data[0].zmax == 1
    assert fig.data[0].zmid == 0


def test_scatter_marker_colors(generator):
    fig = generator.generate_return_vs_drawdown_scatter()

    assert fig.data[0].marker.showscale == True


def test_bar_chart_colors(generator):
    fig = generator.generate_pnl_contributions_bar()

    colors = fig.data[0].marker.color
    assert all(c == "#2ecc71" for c in colors)


def test_rolling_correlation_window_sizes():
    dates = pd.date_range("2023-01-01", periods=200)
    returns = {
        "AAPL": pd.Series(np.random.randn(200) * 0.02, index=dates),
        "MSFT": pd.Series(np.random.randn(200) * 0.018, index=dates),
    }

    results = {"daily_returns": returns}
    gen = PlotlyChartsGenerator(results)

    fig_30 = gen.generate_rolling_correlation(returns, window=30)
    fig_60 = gen.generate_rolling_correlation(returns, window=60)

    assert isinstance(fig_30, go.Figure)
    assert isinstance(fig_60, go.Figure)


def test_charts_with_three_symbols():
    dates = pd.date_range("2023-01-01", periods=100)
    results = {
        "aggregated": {
            "pnl_contributions": {
                "AAPL": {"absolute": 10000, "percentage": 40},
                "MSFT": {"absolute": 8000, "percentage": 32},
                "GOOGL": {"absolute": 7000, "percentage": 28},
            }
        },
        "by_symbol": {
            "AAPL": {"total_return": 50, "max_drawdown": -15, "sharpe_ratio": 1.5},
            "MSFT": {"total_return": 40, "max_drawdown": -20, "sharpe_ratio": 1.2},
            "GOOGL": {"total_return": 35, "max_drawdown": -18, "sharpe_ratio": 1.0},
        },
        "daily_returns": {
            "AAPL": pd.Series(np.random.randn(100) * 0.02, index=dates),
            "MSFT": pd.Series(np.random.randn(100) * 0.018, index=dates),
            "GOOGL": pd.Series(np.random.randn(100) * 0.019, index=dates),
        },
        "daily_values": {
            "AAPL": pd.Series(np.random.rand(100) * 10000 + 20000, index=dates),
            "MSFT": pd.Series(np.random.rand(100) * 10000 + 20000, index=dates),
            "GOOGL": pd.Series(np.random.rand(100) * 10000 + 20000, index=dates),
        },
    }

    gen = PlotlyChartsGenerator(results)

    fig_equity = gen.generate_equity_curves()
    fig_corr = gen.generate_correlation_heatmap(results["daily_returns"])
    fig_rolling = gen.generate_all_rolling_correlations(
        results["daily_returns"], window=20
    )

    assert len(fig_equity.data) == 3
    assert fig_corr.data[0].z.shape == (3, 3)
    assert isinstance(fig_rolling, go.Figure)


def test_empty_contributions():
    results = {
        "aggregated": {"pnl_contributions": {}},
        "by_symbol": {},
        "daily_returns": {},
        "daily_values": {},
    }

    gen = PlotlyChartsGenerator(results)
    fig = gen.generate_pnl_contributions_bar()

    assert fig is None
