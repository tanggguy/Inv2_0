#!/usr/bin/env python3
"""
Script d'optimisation Optuna depuis fichier YAML
================================================

Permet de lancer des optimisations Optuna en chargeant la configuration
depuis un fichier YAML avec support des profils (dev/prod/quick).

Usage:
    python scripts/run_optuna_from_yaml.py config.yaml
    python scripts/run_optuna_from_yaml.py config.yaml --profile prod
    python scripts/run_optuna_from_yaml.py config.yaml --profile dev --verbose

Analyse des résultats:
    optuna-dashboard sqlite:///optimization/optuna_studies/optuna.db
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
import argparse
from typing import Dict, Any, Optional
import importlib
from datetime import datetime

from monitoring.logger import setup_logger
from optimization.optimizer import UnifiedOptimizer

logger = setup_logger("optuna_yaml_runner")


class YAMLOptunaRunner:
    """
    Exécuteur d'optimisation Optuna depuis configuration YAML

    Gère:
    - Chargement de la configuration YAML
    - Système de profils (dev/prod/quick)
    - Import dynamique de la stratégie
    - Validation des paramètres
    - Lancement de l'optimisation
    """

    def __init__(
        self, yaml_path: str, profile: Optional[str] = None, verbose: bool = False
    ):
        """
        Initialise le runner

        Args:
            yaml_path: Chemin vers le fichier YAML
            profile: Profil à utiliser (dev/prod/quick) ou None pour config de base
            verbose: Mode verbose
        """
        self.yaml_path = Path(yaml_path)
        self.profile = profile
        self.verbose = verbose

        if not self.yaml_path.exists():
            raise FileNotFoundError(f"❌ Fichier YAML introuvable: {self.yaml_path}")

        logger.info(f"📄 Chargement de la configuration: {self.yaml_path}")
        if profile:
            logger.info(f"🎯 Profil sélectionné: {profile}")

    def load_config(self) -> Dict[str, Any]:
        """
        Charge et parse le fichier YAML

        Returns:
            Configuration complète
        """
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Valider la structure de base
        self._validate_config(config)

        # Appliquer le profil si spécifié
        if self.profile:
            if "profiles" not in config or self.profile not in config["profiles"]:
                raise ValueError(f"❌ Profil '{self.profile}' introuvable dans le YAML")

            profile_config = config["profiles"][self.profile]
            logger.info(
                f"✅ Application du profil '{self.profile}': {profile_config.get('description', '')}"
            )

            # Fusionner le profil avec la config de base
            config = self._merge_configs(config, profile_config)

        return config

    def _validate_config(self, config: Dict) -> None:
        """
        Valide la structure du fichier YAML

        Args:
            config: Configuration à valider

        Raises:
            ValueError: Si la configuration est invalide
        """
        required_keys = ["strategy", "config", "optuna", "param_grid"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"❌ Clé manquante dans le YAML: '{key}'")

        # Valider la section stratégie
        if "class" not in config["strategy"] or "name" not in config["strategy"]:
            raise ValueError("❌ 'strategy' doit contenir 'class' et 'name'")

        # Valider la section config
        required_config_keys = ["symbols", "period", "capital"]
        for key in required_config_keys:
            if key not in config["config"]:
                raise ValueError(f"❌ Clé manquante dans 'config': '{key}'")

        # Valider period
        if (
            "start" not in config["config"]["period"]
            or "end" not in config["config"]["period"]
        ):
            raise ValueError("❌ 'period' doit contenir 'start' et 'end'")

        # Valider param_grid non vide
        if not config["param_grid"]:
            raise ValueError("❌ 'param_grid' ne peut pas être vide")

        logger.info("✅ Configuration YAML valide")

    def _merge_configs(self, base: Dict, profile: Dict) -> Dict:
        """
        Fusionne la config de base avec un profil

        Les paramètres du profil écrasent ceux de la base.

        Args:
            base: Configuration de base
            profile: Configuration du profil

        Returns:
            Configuration fusionnée
        """
        merged = base.copy()

        # Fusionner optuna
        if "optuna" in profile:
            merged["optuna"].update(profile["optuna"])

        # Fusionner config (symbols, period, capital)
        if "config" in profile:
            for key in ["symbols", "period", "capital"]:
                if key in profile["config"]:
                    merged["config"][key] = profile["config"][key]

        # Fusionner param_grid si présent dans le profil
        if "param_grid" in profile:
            merged["param_grid"].update(profile["param_grid"])

        return merged

    def load_strategy_class(self, class_path: str):
        """
        Charge dynamiquement la classe de stratégie

        Args:
            class_path: Chemin Python de la classe (ex: 'strategies.marsi.MaRSI')

        Returns:
            Classe de stratégie
        """
        logger.info(f"🔍 Import de la stratégie: {class_path}")

        try:
            # Séparer le module et la classe
            module_path, class_name = class_path.rsplit(".", 1)

            # Importer le module
            module = importlib.import_module(module_path)

            # Récupérer la classe
            strategy_class = getattr(module, class_name)

            logger.info(f"✅ Stratégie chargée: {class_name}")
            return strategy_class

        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"❌ Impossible de charger la stratégie '{class_path}': {e}"
            )

    def run(self) -> Dict:
        """
        Lance l'optimisation Optuna

        Returns:
            Résultats de l'optimisation
        """
        # Charger la configuration
        config = self.load_config()

        # Charger la classe de stratégie
        strategy_class = self.load_strategy_class(config["strategy"]["class"])
        strategy_name = config["strategy"]["name"]

        # Préparer la configuration pour UnifiedOptimizer
        optimizer_config = {
            "symbols": config["config"]["symbols"],
            "period": config["config"]["period"],
            "capital": config["config"]["capital"],
            "param_grid": config["param_grid"],
            "optuna": config["optuna"],
        }

        # Afficher un résumé
        self._print_summary(strategy_name, optimizer_config)

        # Créer et lancer l'optimiseur
        logger.info("\n" + "=" * 80)
        logger.info("🚀 LANCEMENT DE L'OPTIMISATION OPTUNA")
        logger.info("=" * 80 + "\n")

        optimizer = UnifiedOptimizer(
            strategy_class=strategy_class,
            config=optimizer_config,
            optimization_type="optuna",
            verbose=self.verbose,
            use_parallel=True,
        )

        results = optimizer.run()

        # Afficher les résultats
        self._print_results(results)

        return results

    def _print_summary(self, strategy_name: str, config: Dict) -> None:
        """
        Affiche un résumé de la configuration avant le lancement

        Args:
            strategy_name: Nom de la stratégie
            config: Configuration complète
        """
        logger.info("\n" + "=" * 80)
        logger.info("📋 RÉSUMÉ DE LA CONFIGURATION")
        logger.info("=" * 80)

        logger.info(f"\n🎯 Stratégie:")
        logger.info(f"   Nom: {strategy_name}")

        logger.info(f"\n📊 Données:")
        logger.info(f"   Symboles: {', '.join(config['symbols'])}")
        logger.info(
            f"   Période: {config['period']['start']} → {config['period']['end']}"
        )
        logger.info(f"   Capital initial: ${config['capital']:,.0f}")

        logger.info(f"\n🔬 Paramètres Optuna:")
        optuna_cfg = config["optuna"]
        logger.info(f"   Trials: {optuna_cfg['n_trials']}")
        logger.info(f"   Sampler: {optuna_cfg['sampler']}")
        logger.info(f"   Pruner: {optuna_cfg['pruner']}")
        logger.info(f"   Timeout: {optuna_cfg['timeout'] or 'Aucun'}")
        logger.info(f"   Parallélisation: {optuna_cfg['n_jobs']} jobs")
        logger.info(f"   Sauvegarde plots: {optuna_cfg['save_plots']}")

        logger.info(f"\n⚙️ Grille de paramètres:")
        for param, values in config["param_grid"].items():
            if isinstance(values, list):
                logger.info(f"   {param}: {values}")
            elif isinstance(values, dict):
                logger.info(f"   {param}: {values}")

        logger.info("\n" + "=" * 80 + "\n")

    def _print_results(self, results: Dict) -> None:
        """
        Affiche les résultats de l'optimisation

        Args:
            results: Résultats retournés par l'optimiseur
        """
        logger.info("\n" + "=" * 80)
        logger.info("🏆 RÉSULTATS DE L'OPTIMISATION")
        logger.info("=" * 80)

        best = results.get("best", {})

        if best:
            logger.info(f"\n📈 Meilleures métriques:")
            logger.info(f"   Sharpe Ratio: {best.get('sharpe', 0):.4f}")
            logger.info(f"   Return: {best.get('return', 0):.2f}%")
            logger.info(f"   Drawdown: {best.get('drawdown', 0):.2f}%")
            logger.info(f"   Win Rate: {best.get('win_rate', 0):.2f}%")
            logger.info(f"   Trades: {best.get('trades', 0)}")

            logger.info(f"\n🎯 Meilleurs paramètres:")
            EXCLUDED_METRICS = {
                "sharpe",
                "return",
                "drawdown",
                "trades",
                "win_rate",
                "initial_value",
                "final_value",
                "total_return",
                "max_drawdown",
                "sharpe_ratio",
                "avg_win",
                "avg_loss",
                "won_trades",
                "lost_trades",
            }

            for key, value in best.items():
                if key not in EXCLUDED_METRICS:
                    logger.info(f"   {key}: {value}")

        # Importance des paramètres
        if "param_importance" in results:
            logger.info(f"\n📊 Importance des paramètres:")
            for param, importance in results["param_importance"].items():
                logger.info(f"   {param}: {importance:.4f}")

        logger.info("\n" + "=" * 80)
        logger.info(f"💾 Résultats sauvegardés dans la base Optuna")
        logger.info(
            f"📊 Visualiser avec: optuna-dashboard sqlite:///optimization/optuna_studies/optuna.db"
        )
        logger.info("=" * 80 + "\n")


def main():
    """Point d'entrée du script"""
    parser = argparse.ArgumentParser(
        description="🔬 Optimisation Optuna depuis fichier YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  # Utiliser la configuration de base
  python scripts/run_optuna_from_yaml.py optimization_configs/my_strategy.yaml
  
  # Utiliser le profil 'quick' pour un test rapide
  python scripts/run_optuna_from_yaml.py optimization_configs/my_strategy.yaml --profile quick
  
  # Utiliser le profil 'prod' pour une optimisation complète
  python scripts/run_optuna_from_yaml.py optimization_configs/my_strategy.yaml --profile prod --verbose
  
  # Visualiser les résultats
  optuna-dashboard sqlite:///optimization/optuna_studies/optuna.db
        """,
    )

    parser.add_argument(
        "yaml_file", type=str, help="Chemin vers le fichier YAML de configuration"
    )

    parser.add_argument(
        "--profile",
        type=str,
        choices=["quick", "dev", "prod"],
        default=None,
        help="Profil à utiliser (quick/dev/prod). Si non spécifié, utilise la config de base.",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Mode verbose avec logs détaillés"
    )

    args = parser.parse_args()

    try:
        # Créer et lancer le runner
        runner = YAMLOptunaRunner(
            yaml_path=args.yaml_file, profile=args.profile, verbose=args.verbose
        )

        results = runner.run()

        logger.info("\n✅ Optimisation terminée avec succès!")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Erreur: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":

    sys.exit(main())
