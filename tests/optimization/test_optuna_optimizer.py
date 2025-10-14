# test_optuna_optimizer.py

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import optuna
from datetime import datetime

from optimization.optuna_optimizer import OptunaOptimizer, create_optuna_optimizer


@pytest.fixture
def mock_objective_func():
    """Fixture pour une fonction objectif mock"""
    return Mock(return_value=0.75)


@pytest.fixture
def simple_param_grid():
    """Fixture pour une grille de paramètres simple"""
    return {"param1": [10, 20, 30], "param2": [0.1, 0.2, 0.3]}


@pytest.fixture
def complex_param_grid():
    """Fixture pour une grille de paramètres complexe"""
    return {
        "int_param": {"type": "int", "low": 10, "high": 100, "step": 5},
        "float_param": {"type": "float", "low": 0.1, "high": 1.0, "step": 0.1},
        "float_log": {"type": "float", "low": 0.001, "high": 1.0, "log": True},
        "categorical": {"type": "categorical", "choices": ["a", "b", "c"]},
    }


@pytest.fixture
def mock_logger():
    """Fixture pour un logger mock"""
    return Mock()


@pytest.fixture
def mock_study():
    """Fixture pour un study Optuna mock"""
    study = Mock()
    study.best_params = {"param1": 20, "param2": 0.2}
    study.best_value = 0.85
    study.trials = [
        Mock(
            state=optuna.trial.TrialState.COMPLETE,
            duration=Mock(total_seconds=Mock(return_value=1.0)),
        )
    ]
    return study


class TestOptunaOptimizer:
    """Tests pour la classe OptunaOptimizer"""

    def test_init_with_defaults(self, mock_objective_func, simple_param_grid):
        """Test l'initialisation avec les paramètres par défaut"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_create_study.return_value = Mock()

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            assert optimizer.objective_func == mock_objective_func
            assert optimizer.param_grid == simple_param_grid
            assert optimizer.n_trials == 100
            assert optimizer.timeout is None
            assert optimizer.direction == "maximize"
            assert optimizer.n_jobs == -1
            assert optimizer.show_progress is True
            assert optimizer.best_params is None
            assert optimizer.best_value is None
            assert optimizer.optimization_history == []

    def test_init_with_custom_params(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test l'initialisation avec des paramètres personnalisés"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_create_study.return_value = Mock()

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=50,
                timeout=3600,
                direction="minimize",
                study_name="custom_study",
                storage="sqlite:///custom.db",
                sampler_type="random",
                pruner_type="successive_halving",
                n_jobs=4,
                show_progress=False,
                logger=mock_logger,
            )

            assert optimizer.n_trials == 50
            assert optimizer.timeout == 3600
            assert optimizer.direction == "minimize"
            assert optimizer.study_name == "custom_study"
            assert optimizer.storage == "sqlite:///custom.db"
            assert optimizer.n_jobs == 4
            assert optimizer.show_progress is False
            assert optimizer.logger == mock_logger

    def test_init_creates_storage_directory(
        self, mock_objective_func, simple_param_grid
    ):
        """Test que l'initialisation crée le dossier de stockage"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optimization.optuna_optimizer.Path"
        ) as mock_path_class:

            mock_create_study.return_value = Mock()
            mock_storage_dir = Mock()
            mock_storage_dir.__truediv__ = Mock(
                return_value="results/optuna_studies/optuna.db"
            )
            mock_path_class.return_value = mock_storage_dir

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            mock_storage_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_storage_dir.__truediv__.assert_called_once_with("optuna.db")

    def test_create_sampler_tpe(self):
        """Test la création d'un sampler TPE"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={}, sampler_type="tpe"
            )

            from optuna.samplers import TPESampler

            assert isinstance(optimizer.sampler, TPESampler)

    def test_create_sampler_random(self):
        """Test la création d'un sampler Random"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={}, sampler_type="random"
            )

            from optuna.samplers import RandomSampler

            assert isinstance(optimizer.sampler, RandomSampler)

    def test_create_sampler_unknown_defaults_to_tpe(self, mock_logger):
        """Test qu'un sampler inconnu utilise TPE par défaut"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={},
                sampler_type="unknown",
                logger=mock_logger,
            )

            from optuna.samplers import TPESampler

            assert isinstance(optimizer.sampler, TPESampler)
            mock_logger.warning.assert_called_once()

    def test_create_pruner_median(self):
        """Test la création d'un pruner Median"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={}, pruner_type="median"
            )

            from optuna.pruners import MedianPruner

            assert isinstance(optimizer.pruner, MedianPruner)

    def test_create_pruner_successive_halving(self):
        """Test la création d'un pruner SuccessiveHalving"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={}, pruner_type="successive_halving"
            )

            from optuna.pruners import SuccessiveHalvingPruner

            assert isinstance(optimizer.pruner, SuccessiveHalvingPruner)

    def test_create_pruner_none(self):
        """Test la création d'un pruner None"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={}, pruner_type="none"
            )

            from optuna.pruners import NopPruner

            assert isinstance(optimizer.pruner, NopPruner)

    def test_create_pruner_unknown_defaults_to_median(self, mock_logger):
        """Test qu'un pruner inconnu utilise Median par défaut"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={},
                pruner_type="unknown",
                logger=mock_logger,
            )

            from optuna.pruners import MedianPruner

            assert isinstance(optimizer.pruner, MedianPruner)
            mock_logger.warning.assert_called_once()

    def test_suggest_params_with_list(self):
        """Test la suggestion de paramètres avec des listes"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={"param1": [10, 20, 30]}
            )

            mock_trial = Mock()
            mock_trial.suggest_categorical = Mock(return_value=20)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 20}
            mock_trial.suggest_categorical.assert_called_once_with(
                "param1", [10, 20, 30]
            )

    def test_suggest_params_with_int_range(self):
        """Test la suggestion de paramètres avec un range entier"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={
                    "param1": {"type": "int", "low": 10, "high": 100, "step": 5}
                },
            )

            mock_trial = Mock()
            mock_trial.suggest_int = Mock(return_value=50)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 50}
            mock_trial.suggest_int.assert_called_once_with(
                "param1", 10, 100, step=5, log=False
            )

    def test_suggest_params_with_int_range_log(self):
        """Test la suggestion de paramètres avec un range entier logarithmique"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={
                    "param1": {"type": "int", "low": 1, "high": 1000, "log": True}
                },
            )

            mock_trial = Mock()
            mock_trial.suggest_int = Mock(return_value=100)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 100}
            mock_trial.suggest_int.assert_called_once_with(
                "param1", 1, 1000, step=1, log=True
            )

    def test_suggest_params_with_float_range(self):
        """Test la suggestion de paramètres avec un range flottant"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={"param1": {"type": "float", "low": 0.1, "high": 1.0}},
            )

            mock_trial = Mock()
            mock_trial.suggest_float = Mock(return_value=0.5)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 0.5}
            mock_trial.suggest_float.assert_called_once_with(
                "param1", 0.1, 1.0, log=False
            )

    def test_suggest_params_with_float_range_step(self):
        """Test la suggestion de paramètres avec un range flottant avec step"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={
                    "param1": {"type": "float", "low": 0.1, "high": 1.0, "step": 0.1}
                },
            )

            mock_trial = Mock()
            mock_trial.suggest_float = Mock(return_value=0.5)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 0.5}
            mock_trial.suggest_float.assert_called_once_with(
                "param1", 0.1, 1.0, step=0.1, log=False
            )

    def test_suggest_params_with_float_range_log(self):
        """Test la suggestion de paramètres avec un range flottant logarithmique"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={
                    "param1": {"type": "float", "low": 0.001, "high": 1.0, "log": True}
                },
            )

            mock_trial = Mock()
            mock_trial.suggest_float = Mock(return_value=0.1)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 0.1}
            mock_trial.suggest_float.assert_called_once_with(
                "param1", 0.001, 1.0, log=True
            )

    def test_suggest_params_with_categorical(self):
        """Test la suggestion de paramètres catégoriels"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={
                    "param1": {"type": "categorical", "choices": ["a", "b", "c"]}
                },
            )

            mock_trial = Mock()
            mock_trial.suggest_categorical = Mock(return_value="b")

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": "b"}
            mock_trial.suggest_categorical.assert_called_once_with(
                "param1", ["a", "b", "c"]
            )

    def test_suggest_params_with_unknown_type_defaults_to_float(self, mock_logger):
        """Test qu'un type inconnu utilise float par défaut"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(),
                param_grid={"param1": {"type": "unknown", "low": 0, "high": 1}},
                logger=mock_logger,
            )

            mock_trial = Mock()
            mock_trial.suggest_float = Mock(return_value=0.5)

            params = optimizer._suggest_params(mock_trial)

            assert params == {"param1": 0.5}
            mock_logger.warning.assert_called_once()
            mock_trial.suggest_float.assert_called_once()

    def test_suggest_params_with_invalid_format_raises_error(self):
        """Test qu'un format invalide lève une erreur"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid={"param1": "invalid"}
            )

            mock_trial = Mock()

            with pytest.raises(ValueError, match="Format de paramètre invalide"):
                optimizer._suggest_params(mock_trial)

    def test_suggest_params_with_multiple_params(self, complex_param_grid):
        """Test la suggestion de plusieurs paramètres"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=Mock(), param_grid=complex_param_grid
            )

            mock_trial = Mock()
            mock_trial.suggest_int = Mock(return_value=50)
            mock_trial.suggest_float = Mock(side_effect=[0.5, 0.01])
            mock_trial.suggest_categorical = Mock(return_value="b")

            params = optimizer._suggest_params(mock_trial)

            assert len(params) == 4
            assert "int_param" in params
            assert "float_param" in params
            assert "float_log" in params
            assert "categorical" in params

    def test_detect_step_with_regular_sequence(self):
        """Test la détection du pas avec une séquence régulière"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([10, 20, 30, 40])
            assert step == 10

    def test_detect_step_with_float_sequence(self):
        """Test la détection du pas avec une séquence de flottants"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([0.1, 0.2, 0.3, 0.4])
            assert abs(step - 0.1) < 1e-10

    def test_detect_step_with_irregular_sequence(self):
        """Test la détection du pas avec une séquence irrégulière"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([10, 20, 35, 50])
            assert step is None

    def test_detect_step_with_single_value(self):
        """Test la détection du pas avec une seule valeur"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([10])
            assert step is None

    def test_detect_step_with_empty_list(self):
        """Test la détection du pas avec une liste vide"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([])
            assert step is None

    def test_detect_step_with_very_small_steps(self):
        """Test la détection du pas avec des pas très petits"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            step = optimizer._detect_step([0.0, 1e-15, 2e-15])
            assert step is None

    def test_is_discrete_with_regular_sequence(self):
        """Test la vérification de discrétisation avec une séquence régulière"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            assert optimizer._is_discrete([10, 20, 30, 40]) is True

    def test_is_discrete_with_irregular_sequence(self):
        """Test la vérification de discrétisation avec une séquence irrégulière"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(objective_func=Mock(), param_grid={})

            assert optimizer._is_discrete([10, 20, 35, 50]) is False

    def test_objective_wrapper_success(self, mock_objective_func):
        """Test le wrapper objectif avec succès"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid={"param1": [10, 20]}
            )

            mock_trial = Mock()
            mock_trial.number = 1
            mock_trial.suggest_categorical = Mock(return_value=10)

            score = optimizer._objective_wrapper(mock_trial)

            assert score == 0.75
            mock_objective_func.assert_called_once_with({"param1": 10})
            assert len(optimizer.optimization_history) == 1
            assert optimizer.optimization_history[0]["trial"] == 1

    def test_objective_wrapper_with_exception_maximize(self, mock_logger):
        """Test le wrapper objectif avec exception (maximize)"""
        mock_obj_func = Mock(side_effect=Exception("Test error"))

        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_obj_func,
                param_grid={"param1": [10]},
                direction="maximize",
                logger=mock_logger,
            )

            mock_trial = Mock()
            mock_trial.number = 1
            mock_trial.suggest_categorical = Mock(return_value=10)

            score = optimizer._objective_wrapper(mock_trial)

            assert score == float("-inf")
            mock_logger.error.assert_called_once()

    def test_objective_wrapper_with_exception_minimize(self, mock_logger):
        """Test le wrapper objectif avec exception (minimize)"""
        mock_obj_func = Mock(side_effect=Exception("Test error"))

        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_obj_func,
                param_grid={"param1": [10]},
                direction="minimize",
                logger=mock_logger,
            )

            mock_trial = Mock()
            mock_trial.number = 1
            mock_trial.suggest_categorical = Mock(return_value=10)

            score = optimizer._objective_wrapper(mock_trial)

            assert score == float("inf")

    def test_optimize_success(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test l'optimisation avec succès"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_study = Mock()
            mock_study.best_params = {"param1": 20}
            mock_study.best_value = 0.85
            mock_study.trials = [
                Mock(
                    state=optuna.trial.TrialState.COMPLETE,
                    duration=Mock(total_seconds=Mock(return_value=1.0)),
                ),
                Mock(state=optuna.trial.TrialState.PRUNED),
                Mock(state=optuna.trial.TrialState.FAIL),
            ]
            mock_create_study.return_value = mock_study

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=3,
                logger=mock_logger,
            )

            result = optimizer.optimize()

            assert result["best_params"] == {"param1": 20}
            assert result["best_value"] == 0.85
            assert result["n_trials"] == 3
            assert "study" in result
            assert "optimization_history" in result
            mock_study.optimize.assert_called_once()

    def test_optimize_with_progress_callback(
        self, mock_objective_func, simple_param_grid
    ):
        """Test l'optimisation avec callback de progression"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_study = Mock()
            mock_study.best_params = {"param1": 20}
            mock_study.best_value = 0.85
            mock_study.trials = [Mock(state=optuna.trial.TrialState.COMPLETE)]
            mock_create_study.return_value = mock_study

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=10,
            )

            mock_callback = Mock()
            result = optimizer.optimize(progress_callback=mock_callback)

            assert result["best_params"] == {"param1": 20}
            mock_study.optimize.assert_called_once()

    def test_optimize_with_keyboard_interrupt(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test l'optimisation interrompue par l'utilisateur"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_study = Mock()
            mock_study.optimize.side_effect = KeyboardInterrupt()
            mock_study.best_params = {"param1": 20}
            mock_study.best_value = 0.85
            mock_study.trials = [Mock()]
            mock_create_study.return_value = mock_study

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                logger=mock_logger,
            )

            result = optimizer.optimize()

            assert result["best_params"] == {"param1": 20}
            assert result["interrupted"] is True
            mock_logger.warning.assert_called_once()

    def test_optimize_with_empty_trials_after_interrupt(
        self, mock_objective_func, simple_param_grid
    ):
        """Test l'optimisation interrompue sans trials"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_study = Mock()
            mock_study.optimize.side_effect = KeyboardInterrupt()
            mock_study.trials = []
            mock_create_study.return_value = mock_study

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            result = optimizer.optimize()

            assert result["best_params"] is None
            assert result["best_value"] is None
            assert result["interrupted"] is True

    def test_get_importance_success(self, mock_objective_func, simple_param_grid):
        """Test la récupération de l'importance des paramètres"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optimization.optuna_optimizer.optuna.importance.get_param_importances"
        ) as mock_get_importance:

            mock_study = Mock()
            mock_create_study.return_value = mock_study
            mock_get_importance.return_value = {"param1": 0.7, "param2": 0.3}

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            importance = optimizer.get_importance()

            assert importance == {"param1": 0.7, "param2": 0.3}
            mock_get_importance.assert_called_once_with(mock_study)

    def test_get_importance_with_exception(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test la récupération de l'importance avec exception"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optimization.optuna_optimizer.optuna.importance.get_param_importances"
        ) as mock_get_importance:

            mock_study = Mock()
            mock_create_study.return_value = mock_study
            mock_get_importance.side_effect = Exception("Test error")

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                logger=mock_logger,
            )

            importance = optimizer.get_importance()

            assert importance == {}
            mock_logger.warning.assert_called_once()

    def test_save_visualizations_success(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test la sauvegarde des visualisations"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optuna.visualization.plot_optimization_history"
        ) as mock_plot_history, patch(
            "optuna.visualization.plot_param_importances"
        ) as mock_plot_importance, patch(
            "optuna.visualization.plot_parallel_coordinate"
        ) as mock_plot_parallel, patch(
            "optuna.visualization.plot_slice"
        ) as mock_plot_slice, patch(
            "optimization.optuna_optimizer.Path"
        ) as mock_path_class:

            mock_study = Mock()
            mock_create_study.return_value = mock_study

            mock_fig = Mock()
            mock_plot_history.return_value = mock_fig
            mock_plot_importance.return_value = mock_fig
            mock_plot_parallel.return_value = mock_fig
            mock_plot_slice.return_value = mock_fig

            # Créer deux instances de mock distinctes pour init et save_visualizations
            mock_init_path = Mock()
            mock_init_path.__truediv__ = Mock(
                return_value="results/optuna_studies/optuna.db"
            )

            mock_output_path = Mock()
            mock_output_path.__truediv__ = Mock(return_value="output/file.html")

            # Le premier appel est pour __init__, le second pour save_visualizations
            mock_path_class.side_effect = [mock_init_path, mock_output_path]

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                logger=mock_logger,
            )

            optimizer.save_visualizations(output_dir="custom_dir")

            # Vérifier que mkdir a bien été appelé pour le output_dir
            mock_output_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            assert mock_fig.write_html.call_count == 4
            assert mock_logger.info.call_count == 4

    def test_save_visualizations_with_exception(
        self, mock_objective_func, simple_param_grid, mock_logger
    ):
        """Test la sauvegarde des visualisations avec exception"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optuna.visualization.plot_optimization_history"
        ) as mock_plot_history, patch(
            "optimization.optuna_optimizer.Path"
        ) as mock_path_class:

            mock_study = Mock()
            mock_create_study.return_value = mock_study
            mock_plot_history.side_effect = Exception("Plot error")

            # Mock pour __init__ qui supporte l'opérateur /
            mock_init_path = Mock()
            mock_init_path.__truediv__ = Mock(
                return_value="results/optuna_studies/optuna.db"
            )

            # Mock pour save_visualizations
            mock_output_path = Mock()
            mock_output_path.__truediv__ = Mock(return_value="output/file.html")

            mock_path_class.side_effect = [mock_init_path, mock_output_path]

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                logger=mock_logger,
            )

            optimizer.save_visualizations()

            mock_logger.warning.assert_called()

    def test_save_visualizations_default_directory(
        self, mock_objective_func, simple_param_grid
    ):
        """Test la sauvegarde des visualisations avec le répertoire par défaut"""
        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study, patch(
            "optuna.visualization.plot_optimization_history"
        ) as mock_plot, patch(
            "optuna.visualization.plot_param_importances"
        ) as mock_plot2, patch(
            "optuna.visualization.plot_parallel_coordinate"
        ) as mock_plot3, patch(
            "optuna.visualization.plot_slice"
        ) as mock_plot4, patch(
            "optimization.optuna_optimizer.Path"
        ) as mock_path_class:

            mock_study = Mock()
            mock_create_study.return_value = mock_study

            mock_fig = Mock()
            mock_plot.return_value = mock_fig
            mock_plot2.return_value = mock_fig
            mock_plot3.return_value = mock_fig
            mock_plot4.return_value = mock_fig

            # Mock pour __init__
            mock_init_path = Mock()
            mock_init_path.__truediv__ = Mock(
                return_value="results/optuna_studies/optuna.db"
            )

            # Mock pour save_visualizations
            mock_output_path = Mock()
            mock_output_path.__truediv__ = Mock(return_value="output/file.html")

            mock_path_class.side_effect = [mock_init_path, mock_output_path]

            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            optimizer.save_visualizations()

            # Vérifier que Path a été appelé avec le répertoire par défaut lors du deuxième appel
            assert mock_path_class.call_count == 2
            assert mock_path_class.call_args_list[1] == call("results/optuna_plots")


class TestCreateOptunaOptimizer:
    """Tests pour la fonction helper create_optuna_optimizer"""

    def test_create_optuna_optimizer_with_defaults(
        self, mock_objective_func, simple_param_grid
    ):
        """Test la création avec les paramètres par défaut"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = create_optuna_optimizer(
                objective_func=mock_objective_func, param_grid=simple_param_grid
            )

            assert isinstance(optimizer, OptunaOptimizer)
            assert optimizer.objective_func == mock_objective_func
            assert optimizer.param_grid == simple_param_grid
            assert optimizer.n_trials == 100

    def test_create_optuna_optimizer_with_custom_n_trials(
        self, mock_objective_func, simple_param_grid
    ):
        """Test la création avec un nombre de trials personnalisé"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = create_optuna_optimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=50,
            )

            assert optimizer.n_trials == 50

    def test_create_optuna_optimizer_with_kwargs(
        self, mock_objective_func, simple_param_grid
    ):
        """Test la création avec des kwargs additionnels"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = create_optuna_optimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=50,
                direction="minimize",
                timeout=3600,
            )

            assert optimizer.n_trials == 50
            assert optimizer.direction == "minimize"
            assert optimizer.timeout == 3600

    def test_create_optuna_optimizer_empty_param_grid(self, mock_objective_func):
        """Test la création avec une grille de paramètres vide"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = create_optuna_optimizer(
                objective_func=mock_objective_func, param_grid={}
            )

            assert optimizer.param_grid == {}


class TestEdgeCases:
    """Tests pour les cas limites"""

    def test_param_grid_with_negative_values(self, mock_objective_func):
        """Test avec des valeurs négatives dans la grille"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            param_grid = {"param1": {"type": "int", "low": -100, "high": -10}}
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=param_grid
            )

            mock_trial = Mock()
            mock_trial.suggest_int = Mock(return_value=-50)

            params = optimizer._suggest_params(mock_trial)
            assert params["param1"] == -50

    def test_param_grid_with_zero_values(self, mock_objective_func):
        """Test avec des valeurs zéro dans la grille"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            param_grid = {"param1": [0, 1, 2]}
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=param_grid
            )

            mock_trial = Mock()
            mock_trial.suggest_categorical = Mock(return_value=0)

            params = optimizer._suggest_params(mock_trial)
            assert params["param1"] == 0

    def test_n_trials_zero(self, mock_objective_func, simple_param_grid):
        """Test avec zéro trials"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                n_trials=0,
            )

            assert optimizer.n_trials == 0

    def test_timeout_zero(self, mock_objective_func, simple_param_grid):
        """Test avec un timeout de zéro"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func,
                param_grid=simple_param_grid,
                timeout=0,
            )

            assert optimizer.timeout == 0

    def test_empty_optimization_history_after_all_failures(self, mock_logger):
        """Test l'historique d'optimisation après échecs complets"""
        mock_obj_func = Mock(side_effect=Exception("Always fail"))

        with patch(
            "optimization.optuna_optimizer.optuna.create_study"
        ) as mock_create_study:
            mock_study = Mock()
            mock_study.trials = []
            mock_create_study.return_value = mock_study

            optimizer = OptunaOptimizer(
                objective_func=mock_obj_func,
                param_grid={"param1": [10]},
                logger=mock_logger,
            )

            # L'historique est vide car aucun trial n'a réussi
            assert len(optimizer.optimization_history) == 0

    def test_very_large_param_grid(self, mock_objective_func):
        """Test avec une très grande grille de paramètres"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            large_grid = {f"param{i}": [1, 2, 3] for i in range(100)}
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid=large_grid
            )

            assert len(optimizer.param_grid) == 100

    def test_single_value_in_list(self, mock_objective_func):
        """Test avec une seule valeur dans une liste"""
        with patch("optimization.optuna_optimizer.optuna.create_study"):
            optimizer = OptunaOptimizer(
                objective_func=mock_objective_func, param_grid={"param1": [42]}
            )

            mock_trial = Mock()
            mock_trial.suggest_categorical = Mock(return_value=42)

            params = optimizer._suggest_params(mock_trial)
            assert params["param1"] == 42
