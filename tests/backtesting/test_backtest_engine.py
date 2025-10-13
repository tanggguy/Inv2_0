"""
Tests unitaires pour le module backtest_engine
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import pandas as pd
import numpy as np
from backtesting.backtest_engine import BacktestEngine


class TestBacktestEngine:
    """Tests pour la classe BacktestEngine"""

    @pytest.fixture
    def sample_params(self):
        """Paramètres par défaut pour les tests"""
        return {
            "strategy_name": "MovingAverage",
            "symbols": ["AAPL", "GOOGL"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000,
            "verbose": False,
        }

    @pytest.fixture
    def sample_dataframe(self):
        """DataFrame de test avec données OHLCV"""
        dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")
        np.random.seed(42)

        data = {
            "Open": np.random.uniform(100, 200, len(dates)),
            "High": np.random.uniform(150, 250, len(dates)),
            "Low": np.random.uniform(50, 150, len(dates)),
            "Close": np.random.uniform(100, 200, len(dates)),
            "Volume": np.random.randint(1000000, 10000000, len(dates)),
        }

        df = pd.DataFrame(data, index=dates)
        df["High"] = df[["High", "Low"]].max(axis=1)
        df["Low"] = df[["High", "Low"]].min(axis=1)

        return df

    @pytest.fixture
    def mock_cerebro(self):
        """Mock de Cerebro"""
        with patch("backtesting.backtest_engine.bt.Cerebro") as mock:
            cerebro_instance = MagicMock()
            cerebro_instance.broker.getvalue.side_effect = [100000, 125000]
            mock.return_value = cerebro_instance
            yield cerebro_instance

    @pytest.fixture
    def mock_strategy_instance(self):
        """Mock d'instance de stratégie avec analyseurs"""
        strategy = MagicMock()
        strategy.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.5}
        strategy.analyzers.drawdown.get_analysis.return_value = {
            "max": {"drawdown": 15.5}
        }
        strategy.analyzers.returns.get_analysis.return_value = {}
        strategy.analyzers.trades.get_analysis.return_value = {
            "total": {"total": 50},
            "won": {"total": 32, "pnl": {"average": 1250.0}},
            "lost": {"total": 18, "pnl": {"average": -850.0}},
        }
        return strategy

    def test_init_basic(self, sample_params):
        """Test l'initialisation basique de BacktestEngine"""
        with patch("backtesting.backtest_engine.bt.Cerebro"):
            engine = BacktestEngine(**sample_params)

        assert engine.strategy_name == "MovingAverage"
        assert engine.symbols == ["AAPL", "GOOGL"]
        assert engine.start_date == "2024-01-01"
        assert engine.end_date == "2024-12-31"
        assert engine.initial_capital == 100000
        assert engine.verbose is False

    def test_init_default_values(self):
        """Test les valeurs par défaut lors de l'initialisation"""
        with patch("backtesting.backtest_engine.bt.Cerebro"):
            engine = BacktestEngine(
                strategy_name="TestStrategy",
                symbols=["AAPL"],
                start_date="2024-01-01",
                end_date="2024-12-31",
            )

        assert engine.initial_capital == 100000
        assert engine.verbose is False

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.settings")
    def test_init_sets_cerebro_cash(
        self, mock_settings, mock_cerebro_class, sample_params
    ):
        """Test que le capital initial est correctement défini dans Cerebro"""
        mock_settings.COMMISSION = 0.001
        cerebro_instance = MagicMock()
        mock_cerebro_class.return_value = cerebro_instance

        engine = BacktestEngine(**sample_params)

        cerebro_instance.broker.setcash.assert_called_once_with(100000)

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.settings")
    def test_init_sets_commission(
        self, mock_settings, mock_cerebro_class, sample_params
    ):
        """Test que la commission est correctement définie"""
        mock_settings.COMMISSION = 0.001
        cerebro_instance = MagicMock()
        mock_cerebro_class.return_value = cerebro_instance

        engine = BacktestEngine(**sample_params)

        cerebro_instance.broker.setcommission.assert_called_once_with(commission=0.001)

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_init_adds_analyzers(self, mock_cerebro_class, sample_params):
        """Test que les analyseurs sont ajoutés à Cerebro"""
        cerebro_instance = MagicMock()
        mock_cerebro_class.return_value = cerebro_instance

        engine = BacktestEngine(**sample_params)

        # Vérifier que addanalyzer a été appelé 4 fois (sharpe, drawdown, returns, trades)
        assert cerebro_instance.addanalyzer.call_count == 4

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.DataHandler")
    def test_init_creates_data_handler(
        self, mock_data_handler, mock_cerebro_class, sample_params
    ):
        """Test que DataHandler est créé lors de l'initialisation"""
        engine = BacktestEngine(**sample_params)

        assert engine.data_handler is not None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.importlib")
    def test_load_strategy_hardcoded_moving_average(
        self, mock_importlib, mock_cerebro, sample_params
    ):
        """Test le chargement d'une stratégie hardcodée (MovingAverage)"""
        mock_module = MagicMock()
        mock_strategy_class = MagicMock()
        mock_module.MovingAverageStrategy = mock_strategy_class
        mock_importlib.import_module.return_value = mock_module

        engine = BacktestEngine(**sample_params)
        strategy_class = engine._load_strategy()

        assert strategy_class == mock_strategy_class
        mock_importlib.import_module.assert_called_with("strategies.moving_average")

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.importlib")
    def test_load_strategy_hardcoded_rsi(
        self, mock_importlib, mock_cerebro, sample_params
    ):
        """Test le chargement de la stratégie RSI"""
        sample_params["strategy_name"] = "RSI"
        mock_module = MagicMock()
        mock_strategy_class = MagicMock()
        mock_module.RSIStrategy = mock_strategy_class
        mock_importlib.import_module.return_value = mock_module

        engine = BacktestEngine(**sample_params)
        strategy_class = engine._load_strategy()

        assert strategy_class == mock_strategy_class
        mock_importlib.import_module.assert_called_with("strategies.rsi_strategy")

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.importlib")
    @patch("backtesting.backtest_engine.Path")
    def test_load_strategy_dynamic(
        self, mock_path, mock_importlib, mock_cerebro, sample_params
    ):
        """Test le chargement dynamique d'une stratégie non hardcodée"""
        sample_params["strategy_name"] = "CustomStrategy"

        # Mock pour simuler un fichier custom_strategy.py
        mock_file = MagicMock()
        mock_file.name = "custom_strategy.py"
        mock_file.stem = "custom_strategy"

        mock_strategies_dir = MagicMock()
        mock_strategies_dir.glob.return_value = [mock_file]
        mock_path.return_value = mock_strategies_dir

        # Mock du module importé
        mock_module = MagicMock()
        mock_strategy_class = MagicMock()
        mock_module.CustomStrategy = mock_strategy_class

        def import_side_effect(module_name):
            if "custom_strategy" in module_name:
                return mock_module
            raise ImportError()

        mock_importlib.import_module.side_effect = import_side_effect

        engine = BacktestEngine(**sample_params)

        with patch("backtesting.backtest_engine.hasattr", return_value=True):
            with patch(
                "backtesting.backtest_engine.getattr", return_value=mock_strategy_class
            ):
                strategy_class = engine._load_strategy()

        assert strategy_class == mock_strategy_class

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.importlib")
    def test_load_strategy_not_found(self, mock_importlib, mock_cerebro, sample_params):
        """Test le chargement d'une stratégie inexistante"""
        sample_params["strategy_name"] = "NonExistentStrategy"
        mock_importlib.import_module.side_effect = ImportError()

        engine = BacktestEngine(**sample_params)

        with patch("backtesting.backtest_engine.Path") as mock_path:
            mock_path.return_value.glob.return_value = []
            strategy_class = engine._load_strategy()

        assert strategy_class is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.importlib")
    def test_load_strategy_import_error(
        self, mock_importlib, mock_cerebro, sample_params
    ):
        """Test la gestion des erreurs d'import"""
        mock_importlib.import_module.side_effect = ImportError("Module not found")

        engine = BacktestEngine(**sample_params)

        with patch("backtesting.backtest_engine.Path") as mock_path:
            mock_path.return_value.glob.return_value = []
            strategy_class = engine._load_strategy()

        assert strategy_class is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_load_data_success(self, mock_cerebro, sample_params, sample_dataframe):
        """Test le chargement réussi des données"""
        cerebro_instance = MagicMock()
        mock_cerebro.return_value = cerebro_instance

        with patch("backtesting.backtest_engine.DataHandler") as mock_dh:
            mock_handler_instance = MagicMock()
            mock_handler_instance.fetch_data.return_value = sample_dataframe
            mock_dh.return_value = mock_handler_instance

            with patch("backtesting.backtest_engine.create_data_feed") as mock_feed:
                mock_data_feed = MagicMock()
                mock_feed.return_value = mock_data_feed

                engine = BacktestEngine(**sample_params)
                engine._load_data()

                # Vérifier que fetch_data a été appelé pour chaque symbole
                assert mock_handler_instance.fetch_data.call_count == len(
                    sample_params["symbols"]
                )
                # Vérifier que adddata a été appelé pour chaque symbole
                assert cerebro_instance.adddata.call_count == len(
                    sample_params["symbols"]
                )

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_load_data_empty_dataframe(self, mock_cerebro, sample_params):
        """Test le chargement de données vides"""
        cerebro_instance = MagicMock()
        mock_cerebro.return_value = cerebro_instance

        with patch("backtesting.backtest_engine.DataHandler") as mock_dh:
            mock_handler_instance = MagicMock()
            mock_handler_instance.fetch_data.return_value = pd.DataFrame()
            mock_dh.return_value = mock_handler_instance

            engine = BacktestEngine(**sample_params)
            engine._load_data()

            # adddata ne devrait pas être appelé si les données sont vides
            cerebro_instance.adddata.assert_not_called()

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_load_data_none_dataframe(self, mock_cerebro, sample_params):
        """Test le chargement quand fetch_data retourne None"""
        cerebro_instance = MagicMock()
        mock_cerebro.return_value = cerebro_instance

        with patch("backtesting.backtest_engine.DataHandler") as mock_dh:
            mock_handler_instance = MagicMock()
            mock_handler_instance.fetch_data.return_value = None
            mock_dh.return_value = mock_handler_instance

            engine = BacktestEngine(**sample_params)
            engine._load_data()

            cerebro_instance.adddata.assert_not_called()

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_analyze_results_success(
        self, mock_cerebro, sample_params, mock_strategy_instance
    ):
        """Test l'analyse des résultats avec succès"""
        engine = BacktestEngine(**sample_params)
        engine.strategy_instance = mock_strategy_instance

        results = engine._analyze_results(100000, 125000)

        assert results is not None
        assert results["initial_value"] == 100000
        assert results["final_value"] == 125000
        assert results["total_return"] == 25.0
        assert results["sharpe_ratio"] == 1.5
        assert results["max_drawdown"] == 15.5
        assert results["total_trades"] == 50
        assert results["won_trades"] == 32
        assert results["lost_trades"] == 18
        assert results["win_rate"] == 64.0

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_analyze_results_zero_trades(self, mock_cerebro, sample_params):
        """Test l'analyse avec zéro trades"""
        strategy = MagicMock()
        strategy.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 0}
        strategy.analyzers.drawdown.get_analysis.return_value = {"max": {"drawdown": 0}}
        strategy.analyzers.returns.get_analysis.return_value = {}
        strategy.analyzers.trades.get_analysis.return_value = {
            "total": {"total": 0},
            "won": {"total": 0, "pnl": {"average": 0}},
            "lost": {"total": 0, "pnl": {"average": 0}},
        }

        engine = BacktestEngine(**sample_params)
        engine.strategy_instance = strategy

        results = engine._analyze_results(100000, 100000)

        assert results["win_rate"] == 0
        assert results["total_trades"] == 0

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_analyze_results_division_by_zero(
        self, mock_cerebro, sample_params, mock_strategy_instance
    ):
        """Test la gestion de la division par zéro"""
        engine = BacktestEngine(**sample_params)
        engine.strategy_instance = mock_strategy_instance

        # Test avec start_value = 0
        results = engine._analyze_results(0, 125000)

        assert results["total_return"] == 0

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_analyze_results_exception_handling(self, mock_cerebro, sample_params):
        """Test la gestion des exceptions lors de l'analyse"""
        strategy = MagicMock()
        strategy.analyzers.sharpe.get_analysis.side_effect = Exception("Test error")

        engine = BacktestEngine(**sample_params)
        engine.strategy_instance = strategy

        results = engine._analyze_results(100000, 125000)

        assert results is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_run_strategy_not_found(self, mock_cerebro, sample_params):
        """Test l'exécution quand la stratégie n'est pas trouvée"""
        cerebro_instance = MagicMock()
        mock_cerebro.return_value = cerebro_instance

        with patch("backtesting.backtest_engine.DataHandler"):
            engine = BacktestEngine(**sample_params)

            with patch.object(engine, "_load_strategy", return_value=None):
                results = engine.run()

        assert results is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_run_execution_error(self, mock_cerebro, sample_params, sample_dataframe):
        """Test la gestion des erreurs pendant l'exécution"""
        cerebro_instance = MagicMock()
        cerebro_instance.broker.getvalue.return_value = (
            100000  # Valeur numérique au lieu de MagicMock
        )
        cerebro_instance.run.side_effect = Exception("Execution error")
        mock_cerebro.return_value = cerebro_instance

        mock_strategy_class = MagicMock()

        with patch("backtesting.backtest_engine.DataHandler") as mock_dh:
            mock_handler_instance = MagicMock()
            mock_handler_instance.fetch_data.return_value = sample_dataframe
            mock_dh.return_value = mock_handler_instance

            with patch("backtesting.backtest_engine.create_data_feed"):
                engine = BacktestEngine(**sample_params)

                with patch.object(
                    engine, "_load_strategy", return_value=mock_strategy_class
                ):
                    results = engine.run()

        assert results is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_run_complete_success(
        self, mock_cerebro, sample_params, sample_dataframe, mock_strategy_instance
    ):
        """Test d'une exécution complète réussie"""
        cerebro_instance = MagicMock()
        cerebro_instance.broker.getvalue.side_effect = [100000, 125000]
        cerebro_instance.run.return_value = [mock_strategy_instance]
        mock_cerebro.return_value = cerebro_instance

        mock_strategy_class = MagicMock()

        with patch("backtesting.backtest_engine.DataHandler") as mock_dh:
            mock_handler_instance = MagicMock()
            mock_handler_instance.fetch_data.return_value = sample_dataframe
            mock_dh.return_value = mock_handler_instance

            with patch("backtesting.backtest_engine.create_data_feed"):
                engine = BacktestEngine(**sample_params)

                with patch.object(
                    engine, "_load_strategy", return_value=mock_strategy_class
                ):
                    results = engine.run()

        assert results is not None
        assert results["initial_value"] == 100000
        assert results["final_value"] == 125000

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_plot_results_success(self, mock_cerebro, sample_params):
        """Test l'affichage des graphiques"""
        cerebro_instance = MagicMock()
        mock_cerebro.return_value = cerebro_instance

        engine = BacktestEngine(**sample_params)
        engine.plot_results()

        cerebro_instance.plot.assert_called_once()

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_plot_results_error(self, mock_cerebro, sample_params):
        """Test la gestion des erreurs lors de l'affichage"""
        cerebro_instance = MagicMock()
        cerebro_instance.plot.side_effect = Exception("Plot error")
        mock_cerebro.return_value = cerebro_instance

        engine = BacktestEngine(**sample_params)
        # Ne devrait pas lever d'exception
        engine.plot_results()

    @patch("backtesting.backtest_engine.bt.Cerebro")
    @patch("backtesting.backtest_engine.PerformanceAnalyzer")
    def test_generate_report_with_results(
        self, mock_analyzer_class, mock_cerebro, sample_params
    ):
        """Test la génération de rapport avec résultats"""
        mock_analyzer = MagicMock()
        mock_analyzer.generate_report.return_value = "/path/to/report.txt"
        mock_analyzer_class.return_value = mock_analyzer

        engine = BacktestEngine(**sample_params)
        engine.results = {"total_return": 25.0}

        report_path = engine.generate_report()

        assert report_path == "/path/to/report.txt"
        mock_analyzer_class.assert_called_once_with(
            engine.results, engine.strategy_name
        )
        mock_analyzer.generate_report.assert_called_once()

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_generate_report_without_results(self, mock_cerebro, sample_params):
        """Test la génération de rapport sans résultats"""
        engine = BacktestEngine(**sample_params)
        engine.results = None

        report_path = engine.generate_report()

        assert report_path is None

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_verbose_mode(self, mock_cerebro, sample_params):
        """Test le mode verbose"""
        sample_params["verbose"] = True

        engine = BacktestEngine(**sample_params)

        assert engine.verbose is True

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_multiple_symbols(self, mock_cerebro, sample_params):
        """Test avec plusieurs symboles"""
        sample_params["symbols"] = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        engine = BacktestEngine(**sample_params)

        assert len(engine.symbols) == 4

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_single_symbol(self, mock_cerebro, sample_params):
        """Test avec un seul symbole"""
        sample_params["symbols"] = ["AAPL"]

        engine = BacktestEngine(**sample_params)

        assert len(engine.symbols) == 1

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_custom_initial_capital(self, mock_cerebro, sample_params):
        """Test avec un capital initial personnalisé"""
        sample_params["initial_capital"] = 500000

        engine = BacktestEngine(**sample_params)

        assert engine.initial_capital == 500000

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_date_parameters(self, mock_cerebro, sample_params):
        """Test des paramètres de date"""
        engine = BacktestEngine(**sample_params)

        assert engine.start_date == "2024-01-01"
        assert engine.end_date == "2024-12-31"

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_results_storage(self, mock_cerebro, sample_params, mock_strategy_instance):
        """Test que les résultats sont stockés correctement"""
        engine = BacktestEngine(**sample_params)
        engine.strategy_instance = mock_strategy_instance

        results = engine._analyze_results(100000, 125000)

        assert engine.results == results

    @patch("backtesting.backtest_engine.bt.Cerebro")
    def test_all_hardcoded_strategies(self, mock_cerebro, sample_params):
        """Test que toutes les stratégies hardcodées peuvent être chargées"""
        hardcoded_strategies = [
            "MovingAverage",
            "RSI",
            "MACrossoverAdvanced",
            "RSITrailingStop",
            "BreakoutATRStop",
            "MomentumMultipleStops",
            "MaSuperStrategie",
            "BollingerBandsStrategy",
            "MeanReversionStrategy",
            "SqueezeMomentumStrategy",
        ]

        with patch("backtesting.backtest_engine.importlib") as mock_importlib:
            mock_module = MagicMock()
            mock_importlib.import_module.return_value = mock_module

            for strategy_name in hardcoded_strategies:
                sample_params["strategy_name"] = strategy_name
                engine = BacktestEngine(**sample_params)

                # Simuler la présence de la classe
                with patch("backtesting.backtest_engine.getattr"):
                    strategy_class = engine._load_strategy()

                # Vérifier que import_module a été appelé
                assert mock_importlib.import_module.called
