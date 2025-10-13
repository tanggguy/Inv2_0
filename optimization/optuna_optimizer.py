#!/usr/bin/env python3
"""
Module d'optimisation Optuna pour le framework de trading
Intégration complète avec UnifiedOptimizer

🎯 Avantages d'Optuna:
- 50-100x plus rapide que GridSearch
- Algorithme intelligent (TPE - Tree-structured Parzen Estimator)
- Pruning automatique des essais non prometteurs
- Visualisations interactives
- Parallélisation native
- Persistence des résultats dans une DB
"""

import optuna
from optuna.pruners import MedianPruner, SuccessiveHalvingPruner
from optuna.samplers import TPESampler, RandomSampler
import logging
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import json
from datetime import datetime

# Désactiver les logs Optuna verbeux
optuna.logging.set_verbosity(optuna.logging.WARNING)


class OptunaOptimizer:
    """
    Optimiseur Optuna intégré dans l'architecture de trading

    Usage:
        optuna_opt = OptunaOptimizer(
            objective_func=run_backtest_func,
            param_grid=param_grid,
            n_trials=100,
            direction='maximize'
        )
        best_params = optuna_opt.optimize()
    """

    def __init__(
        self,
        objective_func: Callable,
        param_grid: Dict[str, List],
        n_trials: int = 100,
        timeout: Optional[int] = None,
        direction: str = "maximize",
        study_name: Optional[str] = None,
        storage: Optional[str] = None,
        sampler_type: str = "tpe",
        pruner_type: str = "median",
        n_jobs: int = -1,
        show_progress: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialise l'optimiseur Optuna

        Args:
            objective_func: Fonction à optimiser (retourne un score)
            param_grid: Dictionnaire des paramètres à optimiser
            n_trials: Nombre d'essais maximum
            timeout: Timeout en secondes (None = pas de limite)
            direction: 'maximize' ou 'minimize'
            study_name: Nom de l'étude (pour persistence)
            storage: URL de stockage (ex: 'sqlite:///optuna.db')
            sampler_type: 'tpe', 'random', 'cmaes'
            pruner_type: 'median', 'successive_halving', 'none'
            n_jobs: Nombre de workers parallèles (-1 = tous les CPUs)
            show_progress: Afficher la barre de progression
            logger: Logger personnalisé
        """
        self.objective_func = objective_func
        self.param_grid = param_grid
        self.n_trials = n_trials
        self.timeout = timeout
        self.direction = direction
        self.n_jobs = n_jobs
        self.show_progress = show_progress
        self.logger = logger

        # Générer un nom d'étude si non fourni
        if study_name is None:
            study_name = f"study_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.study_name = study_name

        # Configurer le storage (persistence)
        if storage is None:
            # Par défaut: SQLite dans le dossier results/optuna_studies
            storage_dir = Path("results/optuna_studies")
            storage_dir.mkdir(parents=True, exist_ok=True)
            storage = f"sqlite:///{storage_dir / 'optuna.db'}"
        self.storage = storage

        # Configurer le sampler
        self.sampler = self._create_sampler(sampler_type)

        # Configurer le pruner
        self.pruner = self._create_pruner(pruner_type)

        # Créer l'étude
        self.study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            direction=direction,
            sampler=self.sampler,
            pruner=self.pruner,
            load_if_exists=True,
        )

        # Métriques
        self.best_params = None
        self.best_value = None
        self.optimization_history = []

    def _create_sampler(self, sampler_type: str):
        """Crée le sampler approprié"""
        samplers = {
            "tpe": TPESampler(seed=42, n_startup_trials=10),
            "random": RandomSampler(seed=42),
            # 'cmaes': CmaEsSampler(seed=42)  # Nécessite cma package
        }

        if sampler_type not in samplers:
            if self.logger:
                self.logger.warning(
                    f"Sampler '{sampler_type}' inconnu, utilisation de 'tpe'"
                )
            sampler_type = "tpe"

        return samplers[sampler_type]

    def _create_pruner(self, pruner_type: str):
        """Crée le pruner approprié"""
        pruners = {
            "median": MedianPruner(
                n_startup_trials=10, n_warmup_steps=5, interval_steps=1
            ),
            "successive_halving": SuccessiveHalvingPruner(),
            "none": optuna.pruners.NopPruner(),
        }

        if pruner_type not in pruners:
            if self.logger:
                self.logger.warning(
                    f"Pruner '{pruner_type}' inconnu, utilisation de 'median'"
                )
            pruner_type = "median"

        return pruners[pruner_type]

    def _suggest_params(self, trial) -> dict:
        """
        Suggère des paramètres pour un trial Optuna

        Gère deux formats:
        1. Liste: [val1, val2, val3]
        2. Range: {type: 'int', low: 10, high: 100, step: 5}

        Args:
            trial: Trial Optuna

        Returns:
            Dict avec les paramètres suggérés
        """
        params = {}

        for param_name, param_values in self.param_grid.items():

            # FORMAT 1: Liste de valeurs discrètes
            if isinstance(param_values, list):
                params[param_name] = trial.suggest_categorical(param_name, param_values)

            # FORMAT 2: Dictionnaire avec type/low/high
            elif isinstance(param_values, dict):
                param_type = param_values.get("type", "float")

                # Paramètres entiers
                if param_type == "int":
                    low = int(param_values["low"])
                    high = int(param_values["high"])
                    step = int(param_values.get("step", 1))
                    log = param_values.get("log", False)

                    params[param_name] = trial.suggest_int(
                        param_name, low, high, step=step, log=log
                    )

                # Paramètres flottants
                elif param_type == "float":
                    low = float(param_values["low"])
                    high = float(param_values["high"])
                    step = param_values.get("step", None)
                    log = param_values.get("log", False)

                    if step is not None:
                        params[param_name] = trial.suggest_float(
                            param_name, low, high, step=float(step), log=log
                        )
                    else:
                        params[param_name] = trial.suggest_float(
                            param_name, low, high, log=log
                        )

                # Paramètres catégoriels
                elif param_type == "categorical":
                    choices = param_values.get("choices", [])
                    params[param_name] = trial.suggest_categorical(param_name, choices)

                else:
                    # Type inconnu, utiliser float par défaut
                    if self.logger:
                        self.logger.warning(
                            f"Type '{param_type}' inconnu pour '{param_name}', "
                            f"utilisation de float par défaut"
                        )
                    low = float(param_values.get("low", 0))
                    high = float(param_values.get("high", 1))
                    params[param_name] = trial.suggest_float(param_name, low, high)

            else:
                # Format invalide
                raise ValueError(
                    f"Format de paramètre invalide pour '{param_name}': {param_values}. "
                    f"Attendu: liste ou dict avec 'type'/'low'/'high'"
                )

        return params

    def _detect_step(self, values: List) -> Optional[float]:
        """Détecte le pas entre les valeurs"""
        if len(values) < 2:
            return None

        try:
            sorted_values = sorted(values)
            steps = [
                sorted_values[i + 1] - sorted_values[i]
                for i in range(len(sorted_values) - 1)
            ]

            # Filtrer les steps très petits (float precision issues)
            steps = [s for s in steps if abs(s) > 1e-10]

            if not steps:
                return None

            # Si tous les pas sont identiques (avec tolérance pour les floats), c'est une séquence régulière
            unique_steps = set(round(s, 10) for s in steps)

            if len(unique_steps) == 1:
                return steps[0]

            return None
        except (TypeError, ValueError):
            return None

    def _is_discrete(self, values: List[float]) -> bool:
        """Vérifie si les valeurs sont discrètes"""
        step = self._detect_step(values)
        return step is not None

    def _objective_wrapper(self, trial: optuna.Trial) -> float:
        """
        Wrapper de la fonction objectif pour Optuna
        """
        # Suggérer les paramètres
        params = self._suggest_params(trial)

        # Exécuter la fonction objectif
        try:
            score = self.objective_func(params)

            # Enregistrer dans l'historique
            self.optimization_history.append(
                {"trial": trial.number, "params": params, "value": score}
            )

            return score

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur trial {trial.number}: {e}")
            # Retourner une valeur très mauvaise
            return float("-inf") if self.direction == "maximize" else float("inf")

    def optimize(
        self, progress_callback: Optional[Callable[[float, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Lance l'optimisation

        Args:
            progress_callback: Fonction callback(progress_pct, eta_seconds)

        Returns:
            Dictionnaire avec best_params, best_value, et study
        """
        if self.logger:
            self.logger.info(f"\n{'='*80}")
            self.logger.info(f"🔬 OPTUNA OPTIMIZATION: {self.study_name}")
            self.logger.info(f"{'='*80}")
            self.logger.info(f"Trials: {self.n_trials}")
            self.logger.info(f"Direction: {self.direction}")
            self.logger.info(f"Sampler: {type(self.sampler).__name__}")
            self.logger.info(f"Pruner: {type(self.pruner).__name__}")
            self.logger.info(f"Parallel jobs: {self.n_jobs}")
            self.logger.info(f"Storage: {self.storage}\n")

        # Callback personnalisé pour la progression
        def _progress_callback(study, trial):
            if progress_callback:
                progress = trial.number / self.n_trials
                # Estimer le temps restant
                if trial.number > 0:
                    avg_duration = sum(
                        t.duration.total_seconds() for t in study.trials if t.duration
                    ) / len([t for t in study.trials if t.duration])
                    remaining_trials = self.n_trials - trial.number
                    eta = avg_duration * remaining_trials
                    progress_callback(progress, int(eta))

        # Lancer l'optimisation
        try:
            self.study.optimize(
                self._objective_wrapper,
                n_trials=self.n_trials,
                timeout=self.timeout,
                n_jobs=self.n_jobs,
                show_progress_bar=self.show_progress,
                callbacks=[_progress_callback] if progress_callback else None,
            )

            # Récupérer les meilleurs résultats
            self.best_params = self.study.best_params
            self.best_value = self.study.best_value

            if self.logger:
                self.logger.info(f"\n{'='*80}")
                self.logger.info("🏆 MEILLEURS RÉSULTATS")
                self.logger.info(f"{'='*80}")
                self.logger.info(f"Best value: {self.best_value:.4f}")
                self.logger.info(f"Best params:")
                for param, value in self.best_params.items():
                    self.logger.info(f"   {param}: {value}")

                # Statistiques
                self.logger.info(f"\n{'='*80}")
                self.logger.info("📊 STATISTIQUES")
                self.logger.info(f"{'='*80}")
                self.logger.info(f"Total trials: {len(self.study.trials)}")
                self.logger.info(
                    f"Completed trials: {len([t for t in self.study.trials if t.state == optuna.trial.TrialState.COMPLETE])}"
                )
                self.logger.info(
                    f"Pruned trials: {len([t for t in self.study.trials if t.state == optuna.trial.TrialState.PRUNED])}"
                )
                self.logger.info(
                    f"Failed trials: {len([t for t in self.study.trials if t.state == optuna.trial.TrialState.FAIL])}"
                )

            return {
                "best_params": self.best_params,
                "best_value": self.best_value,
                "study": self.study,
                "n_trials": len(self.study.trials),
                "optimization_history": self.optimization_history,
            }

        except KeyboardInterrupt:
            if self.logger:
                self.logger.warning("\n⚠️ Optimisation interrompue par l'utilisateur")
            return {
                "best_params": self.study.best_params if self.study.trials else None,
                "best_value": self.study.best_value if self.study.trials else None,
                "study": self.study,
                "interrupted": True,
            }

    def get_importance(self) -> Dict[str, float]:
        """Retourne l'importance des paramètres"""
        try:
            return optuna.importance.get_param_importances(self.study)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Impossible de calculer l'importance: {e}")
            return {}

    def save_visualizations(self, output_dir: str = "results/optuna_plots"):
        """
        Sauvegarde des visualisations Optuna

        Args:
            output_dir: Dossier de sortie
        """
        from optuna.visualization import (
            plot_optimization_history,
            plot_param_importances,
            plot_parallel_coordinate,
            plot_slice,
        )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        plots = {
            "history": plot_optimization_history,
            "importance": plot_param_importances,
            "parallel": plot_parallel_coordinate,
            "slice": plot_slice,
        }

        for name, plot_func in plots.items():
            try:
                fig = plot_func(self.study)
                fig.write_html(str(output_path / f"{self.study_name}_{name}.html"))

                if self.logger:
                    self.logger.info(f"✅ Graphique sauvegardé: {name}.html")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ Impossible de générer {name}: {e}")


# Fonction helper pour intégration facile
def create_optuna_optimizer(
    objective_func: Callable, param_grid: Dict, n_trials: int = 100, **kwargs
) -> OptunaOptimizer:
    """
    Factory function pour créer rapidement un OptunaOptimizer

    Usage:
        optimizer = create_optuna_optimizer(
            objective_func=my_backtest_func,
            param_grid={'period': [10, 20, 30], 'threshold': [0.5, 1.0, 1.5]},
            n_trials=50
        )
        results = optimizer.optimize()
    """
    return OptunaOptimizer(
        objective_func=objective_func,
        param_grid=param_grid,
        n_trials=n_trials,
        **kwargs,
    )
