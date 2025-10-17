# test_multi_symbol_exporter.py

import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from backtesting.multi_symbol_exporter import MultiSymbolExporter


@pytest.fixture
def sample_results():
    dates = pd.date_range("2023-01-01", periods=100)
    return {
        "aggregated": {
            "strategy": "RSI",
            "total_return": 45.0,
            "sharpe_ratio": 1.3,
            "max_drawdown": -18.0,
            "total_trades": 50,
            "global_win_rate": 62.0,
            "absolute_pnl": 22500,
            "initial_value": 100000,
            "final_value": 122500,
            "pnl_contributions": {
                "AAPL": {"absolute": 12500, "percentage": 55.5},
                "MSFT": {"absolute": 10000, "percentage": 44.5},
            },
        },
        "by_symbol": {
            "AAPL": {
                "symbol": "AAPL",
                "allocated_capital": 50000,
                "weight": 0.5,
                "total_return": 50.0,
                "sharpe_ratio": 1.5,
                "max_drawdown": -15.0,
                "total_trades": 25,
                "win_rate": 64.0,
                "absolute_pnl": 12500,
                "final_value": 62500,
            },
            "MSFT": {
                "symbol": "MSFT",
                "allocated_capital": 50000,
                "weight": 0.5,
                "total_return": 40.0,
                "sharpe_ratio": 1.1,
                "max_drawdown": -20.0,
                "total_trades": 25,
                "win_rate": 60.0,
                "absolute_pnl": 10000,
                "final_value": 60000,
            },
        },
        "portfolio_info": {
            "total_capital": 100000,
            "allocations": {"AAPL": 50000, "MSFT": 50000},
        },
        "daily_returns": {
            "AAPL": pd.Series(np.random.randn(100) * 0.02, index=dates),
            "MSFT": pd.Series(np.random.randn(100) * 0.018, index=dates),
        },
        "daily_values": {
            "AAPL": pd.Series(np.random.rand(100) * 10000 + 50000, index=dates),
            "MSFT": pd.Series(np.random.rand(100) * 10000 + 50000, index=dates),
        },
    }


@pytest.fixture
def exporter(sample_results, tmp_path):
    return MultiSymbolExporter(sample_results, output_dir=str(tmp_path))


def test_init(exporter, tmp_path):
    assert exporter.results is not None
    assert exporter.output_dir == tmp_path
    assert exporter.aggregated is not None
    assert exporter.by_symbol is not None


def test_output_dir_creation(sample_results, tmp_path):
    output_dir = tmp_path / "test_output"
    exporter = MultiSymbolExporter(sample_results, output_dir=str(output_dir))

    assert output_dir.exists()


def test_export_json(exporter, tmp_path):
    filepath = exporter.export_json()

    assert Path(filepath).exists()

    with open(filepath, "r") as f:
        data = json.load(f)

    assert "metadata" in data or "symbols" in data or "portfolio" in data


def test_export_json_custom_filename(exporter, tmp_path):
    filepath = exporter.export_json("custom.json")

    assert Path(filepath).name == "custom.json"
    assert Path(filepath).exists()


def test_export_csv_symbol_metrics(exporter, tmp_path):
    files = exporter.export_csv_suite()

    assert "symbol_metrics" in files
    filepath = files["symbol_metrics"]
    assert Path(filepath).exists()

    df = pd.read_csv(filepath)
    assert len(df) >= 1


def test_export_csv_capital_allocation(exporter, tmp_path):
    files = exporter.export_csv_suite()

    assert "allocations" in files
    filepath = files["allocations"]
    assert Path(filepath).exists()


def test_export_csv_pnl_contributions(exporter, tmp_path):
    files = exporter.export_csv_suite()

    assert "contributions" in files
    filepath = files["contributions"]
    assert Path(filepath).exists()


def test_export_csv_suite(exporter, tmp_path):
    files = exporter.export_csv_suite()

    assert "symbol_metrics" in files
    assert "allocations" in files
    assert "contributions" in files

    for filepath in files.values():
        assert Path(filepath).exists()


def test_export_html(exporter, tmp_path):
    filepath = exporter.export_html()

    assert Path(filepath).exists()

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    assert "<!DOCTYPE html>" in html
    assert "Multi-Symbol Backtest Report" in html


def test_export_html_custom_filename(exporter, tmp_path):
    filepath = exporter.export_html("custom_report.html")

    assert Path(filepath).name == "custom_report.html"
    assert Path(filepath).exists()


def test_export_all(exporter, tmp_path):
    files = exporter.export_all()

    assert "json" in files
    assert "html" in files


def test_csv_encoding(exporter, tmp_path):
    files = exporter.export_csv_suite()
    filepath = files["symbol_metrics"]

    df = pd.read_csv(filepath, encoding="utf-8")
    assert len(df) >= 0


def test_html_encoding(exporter, tmp_path):
    filepath = exporter.export_html()

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    assert len(content) > 0


def test_multiple_exports(exporter, tmp_path):
    files1 = exporter.export_all()
    files2 = exporter.export_all()

    for key in files1:
        assert Path(files1[key]).exists()
        assert Path(files2[key]).exists()


def test_export_with_special_characters(tmp_path):
    results = {
        "aggregated": {
            "strategy": "RSI-Été-2023",
            "pnl_contributions": {"AAPL": {"absolute": 1000, "percentage": 100}},
        },
        "by_symbol": {
            "AAPL": {
                "symbol": "AAPL",
                "total_return": 50.0,
                "absolute_pnl": 1000,
                "weight": 1.0,
            }
        },
        "portfolio_info": {},
    }

    exporter = MultiSymbolExporter(results, output_dir=str(tmp_path))
    files = exporter.export_all()

    assert all(Path(f).exists() for f in files.values())
