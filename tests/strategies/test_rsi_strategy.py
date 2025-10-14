"""
Tests unitaires et d'intégration pour la stratégie RSIStrategy.
"""

import pytest
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime

from strategies.rsi_strategy import RSIStrategy


# Helper pour exécuter un backtest avec des données spécifiques (DataFrame)
def run_backtest(data, strategy_class, **params):
    """
    Exécute un backtest complet avec une stratégie et des données fournies.
    Retourne l'instance de la stratégie après l'exécution pour analyse.
    """
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(100000.0)

    # Ajout du flux de données
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    # Ajout de la stratégie
    cerebro.addstrategy(strategy_class, **params)

    # Ajout d'un analyseur pour vérifier les trades
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="tradeanalyzer")

    # Exécuter le backtest. cerebro.run() retourne une liste des stratégies exécutées.
    executed_strategies = cerebro.run()

    # Retourner la première (et unique) instance de stratégie
    return executed_strategies[0]


@pytest.fixture
def neutral_data():
    """Fixture pour des données où le RSI reste dans la zone neutre."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=60)
    # Oscillation très stable autour de 150
    prices = 150 + np.sin(np.arange(60) / 10) * 0.5 + np.random.randn(60) * 0.1
    data = {
        "open": prices,
        "high": prices + 0.5,
        "low": prices - 0.5,
        "close": prices,
        "volume": 100000,
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "datetime"
    return df


@pytest.fixture
def buy_signal_data():
    """Fixture pour des données générant un signal d'achat (RSI < 30)."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=60)
    # Chute contrôlée
    prices = 150 - np.logspace(0, 1.5, num=60) + np.random.randn(60) * 0.2
    data = {
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": 100000,
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "datetime"
    return df


@pytest.fixture
def buy_then_sell_data():
    """Fixture pour des données générant un achat puis une vente (RSI > 70)."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=60)
    # Chute puis forte hausse
    drop = 150 - np.logspace(0, 1.5, num=30)
    rally = drop[-1] + np.logspace(0, 2, num=30)
    prices = np.concatenate([drop, rally]) + np.random.randn(60) * 0.3
    data = {
        "open": prices,
        "high": prices + 2,
        "low": prices - 2,
        "close": prices,
        "volume": 100000,
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "datetime"
    return df


class TestRSIStrategy:
    """Groupe de tests pour la RSIStrategy."""

    def test_strategy_initialization(self, neutral_data):
        """Vérifie que la stratégie s'initialise correctement."""
        # Test avec paramètres par défaut
        strategy_default = run_backtest(neutral_data, RSIStrategy)
        assert isinstance(strategy_default.rsi, bt.indicators.RSI)
        assert strategy_default.params.rsi_period == 10
        assert strategy_default.params.rsi_oversold == 35
        assert strategy_default.params.rsi_overbought == 60

        # Test avec paramètres personnalisés
        strategy_custom = run_backtest(
            neutral_data, RSIStrategy, rsi_period=20, rsi_oversold=25, rsi_overbought=75
        )
        assert strategy_custom.params.rsi_period == 20
        assert strategy_custom.params.rsi_oversold == 25
        assert strategy_custom.params.rsi_overbought == 75

    def test_no_signal_in_neutral_zone(self, neutral_data):
        """Vérifie qu'aucun ordre n'est passé quand le RSI est neutre."""
        strategy = run_backtest(
            neutral_data, RSIStrategy, rsi_oversold=20, rsi_overbought=80
        )

        analysis = strategy.analyzers.tradeanalyzer.get_analysis()
        assert analysis.total.total == 0

    def test_buy_signal_when_oversold_and_not_in_position(self, buy_signal_data):
        """Vérifie qu'un ordre d'achat est passé lorsque le RSI est en survente."""
        strategy = run_backtest(
            buy_signal_data, RSIStrategy, rsi_period=10, rsi_oversold=30
        )

        analysis = strategy.analyzers.tradeanalyzer.get_analysis()
        assert analysis.total.total >= 1  # Au moins un trade doit être ouvert
        assert analysis.total.open >= 1  # Un trade doit être ouvert et non fermé

    def test_no_rebuy_when_oversold_and_in_position(self, buy_signal_data):
        """Vérifie qu'on n'achète pas à nouveau si déjà en position."""
        # Les données `buy_signal_data` contiennent plusieurs barres consécutives en zone de survente.
        # La logique "if not self.position" doit empêcher les achats multiples.
        strategy = run_backtest(
            buy_signal_data, RSIStrategy, rsi_period=10, rsi_oversold=30
        )

        analysis = strategy.analyzers.tradeanalyzer.get_analysis()
        # On vérifie qu'un seul trade a été ouvert au total.
        assert analysis.total.total == 1

    def test_sell_signal_when_overbought_and_in_position(self, buy_then_sell_data):
        """Vérifie qu'un ordre de vente est passé en surachat et en position."""
        strategy = run_backtest(
            buy_then_sell_data,
            RSIStrategy,
            rsi_period=10,
            rsi_oversold=30,
            rsi_overbought=70,
        )

        analysis = strategy.analyzers.tradeanalyzer.get_analysis()
        # On doit avoir un seul trade au total, qui a été ouvert puis fermé.
        assert analysis.total.total == 1
        assert analysis.total.closed == 1
