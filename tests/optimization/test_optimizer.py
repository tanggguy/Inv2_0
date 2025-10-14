# test_optimizer.py

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import backtrader as bt
from multiprocessing import cpu_count
import sys
from pathlib import Path


# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# Import du module à tester
from optimization.optimizer import UnifiedOptimizer, optimize


@pytest.fixture
def mock_strategy_class():
    """Fixture pour créer une fausse classe de stratégie."""
    mock_strategy = MagicMock()
    mock_strategy.__name__ = "MockStrategy"
    return mock_strategy


@pytest.fixture
def base_config():
    """Configuration de base pour les tests."""
    return {
        "symbols": ["AAPL", "GOOGL"],
        "period": {"start": "2020-01-01", "end": "2021-01-01"},
        "capital": 100000,
        "param_grid": {"period": [10, 20, 30], "threshold": [0.5, 1.0, 1.5]},
    }


@pytest.fixture
def mock_data_handler(mocker):
    """Mock du DataHandler."""
    mock_handler = mocker.MagicMock()
    mock_df = pd.DataFrame(
        {
            "Open": [100, 101, 102],
            "High": [105, 106, 107],
            "Low": [99, 100, 101],
            "Close": [104, 105, 106],
            "Volume": [1000, 1100, 1200],
        },
        index=pd.date_range("2020-01-01", periods=3),
    )
    mock_handler.fetch_data.return_value = mock_df
    return mock_handler


@pytest.fixture
def mock_results_storage(mocker):
    """Mock du ResultsStorage."""
    return mocker.MagicMock()


@pytest.fixture
def optimizer(mock_strategy_class, base_config, mocker):
    """Fixture pour créer une instance d'UnifiedOptimizer."""
    mocker.patch("optimization.optimizer.DataHandler")
    mocker.patch("optimization.optimizer.ResultsStorage")
    mocker.patch("optimization.optimizer.setup_logger")

    return UnifiedOptimizer(
        strategy_class=mock_strategy_class,
        config=base_config,
        optimization_type="grid_search",
        verbose=True,
        use_parallel=False,
    )


class TestUnifiedOptimizerInit:
    """Tests pour l'initialisation de UnifiedOptimizer."""

    def test_init_with_minimal_config(self, mock_strategy_class, mocker):
        """Test l'initialisation avec une configuration minimale."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        config = {
            "symbols": ["AAPL"],
            "period": {"start": "2020-01-01", "end": "2021-01-01"},
            "capital": 100000,
            "param_grid": {},
        }

        opt = UnifiedOptimizer(strategy_class=mock_strategy_class, config=config)

        assert opt.strategy_class == mock_strategy_class
        assert opt.symbols == ["AAPL"]
        assert opt.start_date == "2020-01-01"
        assert opt.end_date == "2021-01-01"
        assert opt.capital == 100000
        assert opt.optimization_type == "grid_search"
        assert opt.verbose is True
        assert opt.use_parallel is True

    def test_init_with_custom_optimization_type(
        self, mock_strategy_class, base_config, mocker
    ):
        """Test l'initialisation avec un type d'optimisation personnalisé."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        opt = UnifiedOptimizer(
            strategy_class=mock_strategy_class,
            config=base_config,
            optimization_type="walk_forward",
            verbose=False,
            use_parallel=True,
        )

        assert opt.optimization_type == "walk_forward"
        assert opt.verbose is False
        assert opt.use_parallel is True

    def test_init_run_id_generation(self, mock_strategy_class, base_config, mocker):
        """Test que le run_id est généré correctement."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        with patch("optimization.optimizer.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20230101_120000"

            opt = UnifiedOptimizer(
                strategy_class=mock_strategy_class,
                config=base_config,
                use_parallel=False,
            )

            expected_run_id = "MockStrategy_grid_search_sequential_20230101_120000"
            assert opt.run_id == expected_run_id

    def test_init_with_default_symbols(self, mock_strategy_class, mocker):
        """Test l'initialisation avec les symboles par défaut."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        config = {
            "period": {"start": "2020-01-01", "end": "2021-01-01"},
            "param_grid": {},
        }

        opt = UnifiedOptimizer(strategy_class=mock_strategy_class, config=config)

        assert opt.symbols == ["AAPL"]


class TestPreloadData:
    """Tests pour la méthode _preload_data."""

    def test_preload_data_first_time(self, optimizer, mock_data_handler, mocker):
        """Test le pré-chargement initial des données."""
        mocker.patch.object(optimizer, "data_handler", mock_data_handler)

        cache = optimizer._preload_data()

        assert "AAPL" in cache
        assert "GOOGL" in cache
        assert optimizer._cache_loaded is True
        assert optimizer._data_cache is not None
        assert mock_data_handler.fetch_data.call_count == 2

    def test_preload_data_uses_cache(self, optimizer, mock_data_handler, mocker):
        """Test que le cache est réutilisé."""
        mocker.patch.object(optimizer, "data_handler", mock_data_handler)

        # Premier chargement
        cache1 = optimizer._preload_data()
        call_count_first = mock_data_handler.fetch_data.call_count

        # Deuxième chargement (devrait utiliser le cache)
        cache2 = optimizer._preload_data()
        call_count_second = mock_data_handler.fetch_data.call_count

        assert cache1 == cache2
        assert call_count_first == call_count_second

    def test_preload_data_with_empty_dataframe(self, optimizer, mocker):
        """Test le comportement avec un DataFrame vide."""
        mock_handler = mocker.MagicMock()
        mock_handler.fetch_data.return_value = pd.DataFrame()
        mocker.patch.object(optimizer, "data_handler", mock_handler)

        cache = optimizer._preload_data()

        assert len(cache) == 0

    def test_preload_data_with_exception(self, optimizer, mocker):
        """Test le comportement en cas d'exception."""
        mock_handler = mocker.MagicMock()
        mock_handler.fetch_data.side_effect = Exception("Network error")
        mocker.patch.object(optimizer, "data_handler", mock_handler)

        cache = optimizer._preload_data()

        assert len(cache) == 0


class TestConvertParams:
    """Tests pour la méthode _convert_params."""

    def test_convert_params_with_period(self, optimizer):
        """Test la conversion des paramètres avec 'period'."""
        params = {"fast_period": 10.5, "slow_period": 20.8}
        converted = optimizer._convert_params(params)

        assert converted["fast_period"] == 10
        assert converted["slow_period"] == 20
        assert isinstance(converted["fast_period"], int)

    def test_convert_params_with_window(self, optimizer):
        """Test la conversion avec 'window'."""
        params = {"window": 15.7, "threshold": 0.5}
        converted = optimizer._convert_params(params)

        assert converted["window"] == 15
        assert converted["threshold"] == 0.5

    def test_convert_params_with_length(self, optimizer):
        """Test la conversion avec 'length'."""
        params = {"length": 25.3}
        converted = optimizer._convert_params(params)

        assert converted["length"] == 25

    def test_convert_params_with_days(self, optimizer):
        """Test la conversion avec 'days'."""
        params = {"lookback_days": 30.9}
        converted = optimizer._convert_params(params)

        assert converted["lookback_days"] == 30

    def test_convert_params_no_conversion_needed(self, optimizer):
        """Test avec des paramètres ne nécessitant pas de conversion."""
        params = {"threshold": 0.5, "multiplier": 1.5}
        converted = optimizer._convert_params(params)

        assert converted == params

    def test_convert_params_empty_dict(self, optimizer):
        """Test avec un dictionnaire vide."""
        params = {}
        converted = optimizer._convert_params(params)

        assert converted == {}


class TestRunSingleBacktest:
    """Tests pour la méthode _run_single_backtest."""

    def test_run_single_backtest_success(self, optimizer, mocker):
        """Test un backtest réussi."""
        # Mock cerebro
        mock_cerebro = mocker.MagicMock()
        mock_cerebro.broker.getvalue.side_effect = [100000, 110000]

        # Mock analyzers
        mock_strat = mocker.MagicMock()
        mock_strat.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.5}
        mock_strat.analyzers.drawdown.get_analysis.return_value = {
            "max": {"drawdown": 10}
        }
        mock_strat.analyzers.trades.get_analysis.return_value = {
            "total": {"total": 20},
            "won": {"total": 15},
        }
        mock_cerebro.run.return_value = [mock_strat]

        mocker.patch("optimization.optimizer.bt.Cerebro", return_value=mock_cerebro)
        mocker.patch("optimization.optimizer.create_data_feed")

        # ✅ FIX: Mock le MetricsValidator pour qu'il retourne les résultats sans les modifier
        mock_validator = mocker.MagicMock()
        mock_validator.validate_and_clean.side_effect = lambda x: x
        mocker.patch(
            "optimization.optimizer.MetricsValidator", return_value=mock_validator
        )

        # Pré-charger les données
        optimizer._data_cache = {"AAPL": pd.DataFrame()}
        optimizer._cache_loaded = True

        params = {"period": 20}
        result = optimizer._run_single_backtest(params)

        assert result is not None
        assert result["period"] == 20
        assert result["sharpe"] == 1.5
        assert result["trades"] == 20
        assert result["win_rate"] == 75.0

    def test_run_single_backtest_with_custom_dates(self, optimizer, mocker):
        """Test un backtest avec des dates personnalisées."""
        mock_cerebro = mocker.MagicMock()
        mock_cerebro.broker.getvalue.side_effect = [100000, 105000]
        mock_strat = mocker.MagicMock()
        mock_strat.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.0}
        mock_strat.analyzers.drawdown.get_analysis.return_value = {
            "max": {"drawdown": 5}
        }
        mock_strat.analyzers.trades.get_analysis.return_value = {
            "total": {"total": 10},
            "won": {"total": 6},
        }
        mock_cerebro.run.return_value = [mock_strat]

        mocker.patch("optimization.optimizer.bt.Cerebro", return_value=mock_cerebro)
        mocker.patch("optimization.optimizer.create_data_feed")

        mock_validator = mocker.MagicMock()
        mock_validator.validate_and_clean.side_effect = lambda x: x
        mocker.patch(
            "optimization.optimizer.MetricsValidator", return_value=mock_validator
        )

        mock_handler = mocker.MagicMock()
        mock_handler.fetch_data.return_value = pd.DataFrame()
        mocker.patch.object(optimizer, "data_handler", mock_handler)

        params = {"period": 15}
        result = optimizer._run_single_backtest(
            params, start_date="2020-06-01", end_date="2020-12-31"
        )

        assert result is not None
        mock_handler.fetch_data.assert_called()

    def test_run_single_backtest_with_exception(self, optimizer, mocker):
        """Test le comportement en cas d'exception."""
        mocker.patch(
            "optimization.optimizer.bt.Cerebro", side_effect=Exception("Backtest error")
        )

        optimizer._data_cache = {"AAPL": pd.DataFrame()}
        optimizer._cache_loaded = True

        params = {"period": 20}
        result = optimizer._run_single_backtest(params)

        assert result is None

    def test_run_single_backtest_no_trades(self, optimizer, mocker):
        """Test avec aucun trade."""
        mock_cerebro = mocker.MagicMock()
        mock_cerebro.broker.getvalue.side_effect = [100000, 100000]
        mock_strat = mocker.MagicMock()
        mock_strat.analyzers.sharpe.get_analysis.return_value = {"sharperatio": None}
        mock_strat.analyzers.drawdown.get_analysis.return_value = {
            "max": {"drawdown": 0}
        }
        mock_strat.analyzers.trades.get_analysis.return_value = {
            "total": {"total": 0},
            "won": {"total": 0},
        }
        mock_cerebro.run.return_value = [mock_strat]

        mocker.patch("optimization.optimizer.bt.Cerebro", return_value=mock_cerebro)
        mocker.patch("optimization.optimizer.create_data_feed")

        mock_validator = mocker.MagicMock()
        mock_validator.validate_and_clean.side_effect = lambda x: x
        mocker.patch(
            "optimization.optimizer.MetricsValidator", return_value=mock_validator
        )

        optimizer._data_cache = {"AAPL": pd.DataFrame()}
        optimizer._cache_loaded = True

        params = {"period": 20}
        result = optimizer._run_single_backtest(params)

        assert result is not None
        assert result["trades"] == 0
        assert result["win_rate"] == 0


class TestGridSearch:
    """Tests pour les méthodes de grid search."""

    def test_grid_search_sequential(self, optimizer, mocker):
        """Test le grid search séquentiel."""
        mock_backtest_result = {
            "period": 20,
            "sharpe": 1.5,
            "return": 10.0,
            "drawdown": 5.0,
            "trades": 10,
            "win_rate": 60.0,
        }

        mocker.patch.object(
            optimizer, "_run_single_backtest", return_value=mock_backtest_result
        )
        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch.object(
            optimizer, "_analyze_results", return_value={"best": mock_backtest_result}
        )
        mocker.patch.object(optimizer, "_save_results")

        result = optimizer._grid_search()

        assert result is not None
        assert "best" in result

    def test_grid_search_with_progress_callback(self, optimizer, mocker):
        """Test le grid search avec callback de progression."""
        mock_backtest_result = {"period": 20, "sharpe": 1.5, "return": 10.0}

        mocker.patch.object(
            optimizer, "_run_single_backtest", return_value=mock_backtest_result
        )
        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch.object(
            optimizer, "_analyze_results", return_value={"best": mock_backtest_result}
        )
        mocker.patch.object(optimizer, "_save_results")

        progress_callback = mocker.MagicMock()
        result = optimizer._grid_search(progress_callback=progress_callback)

        assert progress_callback.called

    def test_grid_search_parallel(self, optimizer, mocker):
        """Test le grid search parallèle."""
        mock_backtest_result = {
            "period": 20,
            "sharpe": 1.5,
            "return": 10.0,
            "drawdown": 5.0,
            "trades": 10,
            "win_rate": 60.0,
        }

        mocker.patch.object(
            optimizer, "_preload_data", return_value={"AAPL": pd.DataFrame()}
        )
        mocker.patch.object(
            optimizer, "_analyze_results", return_value={"best": mock_backtest_result}
        )
        mocker.patch.object(optimizer, "_save_results")

        # Mock Pool
        mock_pool = mocker.MagicMock()
        mock_pool.__enter__.return_value = mock_pool
        mock_pool.starmap.return_value = [mock_backtest_result] * 9  # 3x3 grid
        mocker.patch("optimization.optimizer.Pool", return_value=mock_pool)
        mocker.patch("optimization.optimizer.cpu_count", return_value=4)

        optimizer.use_parallel = True
        result = optimizer._grid_search_parallel()

        assert result is not None
        assert "best" in result

    def test_grid_search_parallel_with_exception(self, optimizer, mocker):
        """Test le grid search parallèle avec exception (fallback séquentiel)."""
        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch("optimization.optimizer.Pool", side_effect=Exception("Pool error"))
        mocker.patch.object(optimizer, "_grid_search", return_value={"best": {}})

        result = optimizer._grid_search_parallel()

        assert result is not None


class TestWalkForward:
    """Tests pour la méthode walk-forward."""

    def test_generate_walk_forward_periods(self, optimizer):
        """Test la génération des périodes walk-forward."""
        optimizer.start_date = "2020-01-01"
        optimizer.end_date = "2021-01-01"

        periods = optimizer._generate_walk_forward_periods(
            in_sample_months=6, out_sample_months=3
        )

        assert len(periods) > 0
        assert "in_sample" in periods[0]
        assert "out_sample" in periods[0]

    def test_walk_forward_analysis(self, optimizer, mocker):
        """Test l'analyse walk-forward complète."""
        # Mock de l'optimiseur In-Sample
        mock_in_sample_results = {
            "best": {"period": 20, "threshold": 1.0, "sharpe": 2.0, "return": 15.0}
        }

        mock_out_sample_result = {
            "period": 20,
            "threshold": 1.0,
            "sharpe": 1.5,
            "return": 12.0,
            "trades": 10,
        }

        mocker.patch.object(
            optimizer,
            "_generate_walk_forward_periods",
            return_value=[
                {
                    "in_sample": ("2020-01-01", "2020-06-30"),
                    "out_sample": ("2020-07-01", "2020-09-30"),
                }
            ],
        )

        mocker.patch("optimization.optimizer.UnifiedOptimizer")
        mock_in_sample_opt = mocker.MagicMock()
        mock_in_sample_opt.run.return_value = mock_in_sample_results
        mocker.patch(
            "optimization.optimizer.UnifiedOptimizer", return_value=mock_in_sample_opt
        )

        mocker.patch.object(
            optimizer, "_run_single_backtest", return_value=mock_out_sample_result
        )
        mocker.patch.object(
            optimizer, "_analyze_walk_forward_results", return_value={"best": {}}
        )

        optimizer.config["walk_forward"] = {
            "in_sample_months": 6,
            "out_sample_months": 3,
        }

        result = optimizer._walk_forward()

        assert result is not None


class TestOptunaOptimization:
    """Tests pour l'optimisation Optuna."""

    def test_optuna_optimization(self, optimizer, mocker):
        """Test l'optimisation Optuna."""
        mock_optuna_results = {
            "best_params": {"period": 20, "threshold": 1.0},
            "best_value": 2.0,
            "n_trials": 100,
            "optimization_history": [
                {"trial": 1, "value": 1.5},
                {"trial": 2, "value": 2.0},
            ],
        }

        mock_backtest_result = {
            "period": 20,
            "threshold": 1.0,
            "sharpe": 2.0,
            "return": 15.0,
            "drawdown": 5.0,
            "trades": 20,
            "win_rate": 70.0,
        }

        mock_optuna_opt = mocker.MagicMock()
        mock_optuna_opt.optimize.return_value = mock_optuna_results
        mock_optuna_opt.optimization_history = mock_optuna_results[
            "optimization_history"
        ]
        mock_optuna_opt.get_importance.return_value = {}
        mock_optuna_opt.save_visualizations = mocker.MagicMock()

        mocker.patch(
            "optimization.optimizer.OptunaOptimizer", return_value=mock_optuna_opt
        )
        mocker.patch.object(
            optimizer, "_run_single_backtest", return_value=mock_backtest_result
        )
        mocker.patch.object(
            optimizer,
            "_analyze_optuna_results",
            return_value={"best": mock_backtest_result},
        )
        mocker.patch.object(optimizer, "_save_results")

        optimizer.config["optuna"] = {"n_trials": 100}

        result = optimizer._optuna_optimization()

        assert result is not None
        assert "best" in result


class TestAnalyzeResults:
    """Tests pour l'analyse des résultats."""

    def test_analyze_results_with_valid_data(self, optimizer):
        """Test l'analyse avec des données valides."""
        optimizer.results = [
            {
                "period": 10,
                "sharpe": 1.5,
                "return": 10.0,
                "drawdown": 5.0,
                "trades": 10,
                "win_rate": 60.0,
            },
            {
                "period": 20,
                "sharpe": 2.0,
                "return": 15.0,
                "drawdown": 3.0,
                "trades": 15,
                "win_rate": 70.0,
            },
            {
                "period": 30,
                "sharpe": 1.2,
                "return": 8.0,
                "drawdown": 7.0,
                "trades": 8,
                "win_rate": 50.0,
            },
        ]

        results = optimizer._analyze_results()

        assert results["best"]["sharpe"] == 2.0
        assert results["best"]["period"] == 20
        assert results["total_combinations"] == 3
        assert "statistics" in results

    def test_analyze_results_empty_results(self, optimizer):
        """Test l'analyse avec des résultats vides."""
        optimizer.results = []

        results = optimizer._analyze_results()

        assert results["best"] == {}
        assert results["all_results"] == []

    def test_analyze_walk_forward_results(self, optimizer):
        """Test l'analyse des résultats walk-forward."""
        walk_forward_results = [
            {
                "period": 1,
                "in_sample": {"start": "2020-01-01", "end": "2020-06-30"},
                "out_sample": {"start": "2020-07-01", "end": "2020-09-30"},
                "best_params": {"period": 20},
                "in_sharpe": 2.0,
                "in_return": 15.0,
                "out_sharpe": 1.5,
                "out_return": 12.0,
                "out_trades": 10,
                "degradation": 0.5,
            }
        ]

        results = optimizer._analyze_walk_forward_results(walk_forward_results)

        assert "best" in results
        assert "statistics" in results
        assert results["statistics"]["avg_in_sharpe"] == 2.0

    def test_analyze_optuna_results(self, optimizer, mocker):
        """Test l'analyse des résultats Optuna."""
        optuna_results = {
            "best_params": {"period": 20, "threshold": 1.0},
            "best_value": 2.0,
            "n_trials": 100,
            "optimization_history": [
                {"trial": 1, "value": 1.5},
                {"trial": 2, "value": 2.0},
            ],
        }

        mock_backtest_result = {
            "sharpe": 2.0,
            "return": 15.0,
            "drawdown": 5.0,
            "trades": 20,
            "win_rate": 70.0,
        }

        mocker.patch.object(
            optimizer, "_run_single_backtest", return_value=mock_backtest_result
        )

        results = optimizer._analyze_optuna_results(optuna_results)

        assert "best" in results
        assert results["best"]["period"] == 20
        assert results["best"]["sharpe"] == 2.0


class TestSaveResults:
    """Tests pour la sauvegarde des résultats."""

    def test_save_results(self, optimizer, mocker):
        """Test la sauvegarde des résultats."""
        mock_storage = mocker.MagicMock()
        optimizer.storage = mock_storage

        results = {"best": {"sharpe": 2.0}}
        optimizer._save_results(results)

        mock_storage.save_run.assert_called_once()


class TestGetBestParams:
    """Tests pour get_best_params."""

    def test_get_best_params_with_results(self, optimizer):
        """Test la récupération des meilleurs paramètres."""
        optimizer.best_result = {
            "period": 20,
            "threshold": 1.0,
            "sharpe": 2.0,
            "return": 15.0,
            "drawdown": 5.0,
            "trades": 20,
            "win_rate": 70.0,
        }

        best_params = optimizer.get_best_params()

        assert best_params == {"period": 20, "threshold": 1.0}

    def test_get_best_params_no_results(self, optimizer):
        """Test sans résultats."""
        optimizer.best_result = None

        best_params = optimizer.get_best_params()

        assert best_params == {}


class TestRun:
    """Tests pour la méthode run principale."""

    def test_run_grid_search(self, optimizer, mocker):
        """Test l'exécution du grid search."""
        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch.object(optimizer, "_grid_search", return_value={"best": {}})

        with patch("optimization.optimizer.time.time", side_effect=[0, 10, 20]):
            result = optimizer.run()

        assert result is not None

    def test_run_walk_forward(self, optimizer, mocker):
        """Test l'exécution du walk-forward."""
        optimizer.optimization_type = "walk_forward"

        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch.object(optimizer, "_walk_forward", return_value={"best": {}})

        with patch("optimization.optimizer.time.time", side_effect=[0, 10, 20]):
            result = optimizer.run()

        assert result is not None

    def test_run_optuna(self, optimizer, mocker):
        """Test l'exécution d'Optuna."""
        optimizer.optimization_type = "optuna"

        mocker.patch.object(optimizer, "_preload_data", return_value={})
        mocker.patch.object(
            optimizer, "_optuna_optimization", return_value={"best": {}}
        )

        with patch("optimization.optimizer.time.time", side_effect=[0, 10, 20]):
            result = optimizer.run()

        assert result is not None

    def test_run_invalid_optimization_type(self, optimizer, mocker):
        """Test avec un type d'optimisation invalide."""
        optimizer.optimization_type = "invalid_type"

        mocker.patch.object(optimizer, "_preload_data", return_value={})

        with pytest.raises(ValueError, match="Type d'optimisation non supporté"):
            optimizer.run()


class TestOptimizeHelperFunction:
    """Tests pour la fonction helper optimize."""

    def test_optimize_function(self, mock_strategy_class, mocker):
        """Test la fonction optimize helper."""
        mock_preset_config = {
            "symbols": ["AAPL"],
            "period": {"start": "2020-01-01", "end": "2021-01-01"},
            "capital": 100000,
            "param_grid": {"period": [10, 20]},
        }

        # ✅ FIX: Patcher le bon chemin d'import
        mocker.patch(
            "optimization.optimization_config.load_preset",
            return_value=mock_preset_config,
        )
        mocker.patch("optimization.optimizer.UnifiedOptimizer")

        mock_optimizer = mocker.MagicMock()
        mock_optimizer.run.return_value = {"best": {}}
        mocker.patch(
            "optimization.optimizer.UnifiedOptimizer", return_value=mock_optimizer
        )

        result = optimize(
            strategy_class=mock_strategy_class,
            preset_name="standard",
            optimization_type="grid_search",
            use_parallel=True,
        )

        assert result is not None


class TestEdgeCases:
    """Tests pour les cas limites et edge cases."""

    def test_optimizer_with_empty_param_grid(self, mock_strategy_class, mocker):
        """Test avec une grille de paramètres vide."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        config = {
            "symbols": ["AAPL"],
            "period": {"start": "2020-01-01", "end": "2021-01-01"},
            "capital": 100000,
            "param_grid": {},
        }

        opt = UnifiedOptimizer(strategy_class=mock_strategy_class, config=config)

        assert opt.param_grid == {}

    def test_optimizer_with_single_symbol(self, mock_strategy_class, mocker):
        """Test avec un seul symbole."""
        mocker.patch("optimization.optimizer.DataHandler")
        mocker.patch("optimization.optimizer.ResultsStorage")
        mocker.patch("optimization.optimizer.setup_logger")

        config = {
            "symbols": ["AAPL"],
            "period": {"start": "2020-01-01", "end": "2021-01-01"},
            "capital": 100000,
            "param_grid": {"period": [10]},
        }

        opt = UnifiedOptimizer(strategy_class=mock_strategy_class, config=config)

        assert len(opt.symbols) == 1

    def test_convert_params_with_negative_values(self, optimizer):
        """Test la conversion avec des valeurs négatives."""
        params = {"period": -10.5}
        converted = optimizer._convert_params(params)

        assert converted["period"] == -10

    def test_convert_params_with_zero(self, optimizer):
        """Test la conversion avec zéro."""
        params = {"period": 0.0}
        converted = optimizer._convert_params(params)

        assert converted["period"] == 0
