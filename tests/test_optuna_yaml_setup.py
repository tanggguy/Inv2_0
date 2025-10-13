#!/usr/bin/env python3
"""
Script de test pour le système Optuna-YAML

Vérifie que:
- Tous les modules nécessaires sont installés
- La structure de dossiers est correcte
- Un fichier YAML est valide
- L'import de stratégie fonctionne

Usage:
    python scripts/test_optuna_yaml_setup.py
    python scripts/test_optuna_yaml_setup.py optimization_configs/masuperstrategie_optuna.yaml
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from typing import List, Tuple


def test_imports() -> Tuple[bool, List[str]]:
    """
    Teste les imports requis
    
    Returns:
        (success, errors)
    """
    errors = []
    
    try:
        import yaml
    except ImportError:
        errors.append("❌ PyYAML non installé. Installez avec: pip install pyyaml")
    
    try:
        import optuna
    except ImportError:
        errors.append("❌ Optuna non installé. Installez avec: pip install optuna")
    
    try:
        import backtrader
    except ImportError:
        errors.append("❌ Backtrader non installé. Installez avec: pip install backtrader")
    
    try:
        from monitoring.logger import setup_logger
    except ImportError:
        errors.append("❌ Module monitoring.logger introuvable")
    
    try:
        from optimization.optimizer import UnifiedOptimizer
    except ImportError:
        errors.append("❌ Module optimization.optimizer introuvable")
    
    try:
        from optimization.optuna_optimizer import OptunaOptimizer
    except ImportError:
        errors.append("❌ Module optimization.optuna_optimizer introuvable")
    
    return len(errors) == 0, errors


def test_directory_structure() -> Tuple[bool, List[str]]:
    """
    Vérifie la structure de dossiers
    
    Returns:
        (success, errors)
    """
    errors = []
    required_dirs = [
        "scripts",
        "optimization",
        "optimization/optuna_studies",
        "strategies",
        "monitoring"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            errors.append(f"❌ Dossier manquant: {dir_path}")
    
    # Vérifier l'existence du script principal
    if not Path("scripts/run_optuna_from_yaml.py").exists():
        errors.append("❌ Script manquant: scripts/run_optuna_from_yaml.py")
    
    return len(errors) == 0, errors


def test_yaml_file(yaml_path: str) -> Tuple[bool, List[str]]:
    """
    Teste la validité d'un fichier YAML
    
    Args:
        yaml_path: Chemin vers le fichier YAML
    
    Returns:
        (success, errors)
    """
    import yaml
    
    errors = []
    
    if not Path(yaml_path).exists():
        errors.append(f"❌ Fichier introuvable: {yaml_path}")
        return False, errors
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérifier la structure
        required_keys = ['strategy', 'config', 'optuna', 'param_grid']
        for key in required_keys:
            if key not in config:
                errors.append(f"❌ Clé manquante dans le YAML: '{key}'")
        
        # Vérifier strategy
        if 'strategy' in config:
            if 'class' not in config['strategy']:
                errors.append("❌ 'strategy.class' manquant")
            if 'name' not in config['strategy']:
                errors.append("❌ 'strategy.name' manquant")
        
        # Vérifier config
        if 'config' in config:
            if 'symbols' not in config['config']:
                errors.append("❌ 'config.symbols' manquant")
            if 'period' not in config['config']:
                errors.append("❌ 'config.period' manquant")
            elif 'start' not in config['config']['period'] or 'end' not in config['config']['period']:
                errors.append("❌ 'config.period' doit contenir 'start' et 'end'")
            if 'capital' not in config['config']:
                errors.append("❌ 'config.capital' manquant")
        
        # Vérifier param_grid non vide
        if 'param_grid' in config and not config['param_grid']:
            errors.append("❌ 'param_grid' ne peut pas être vide")
        
    except yaml.YAMLError as e:
        errors.append(f"❌ Erreur de parsing YAML: {e}")
    except Exception as e:
        errors.append(f"❌ Erreur inattendue: {e}")
    
    return len(errors) == 0, errors


def test_strategy_import(class_path: str) -> Tuple[bool, List[str]]:
    """
    Teste l'import d'une stratégie
    
    Args:
        class_path: Chemin Python de la classe
    
    Returns:
        (success, errors)
    """
    import importlib
    
    errors = []
    
    try:
        # Séparer le module et la classe
        module_path, class_name = class_path.rsplit('.', 1)
        
        # Importer le module
        module = importlib.import_module(module_path)
        
        # Récupérer la classe
        strategy_class = getattr(module, class_name)
        
        # Vérifier que c'est bien une classe
        if not isinstance(strategy_class, type):
            errors.append(f"❌ '{class_path}' n'est pas une classe")
        
    except ImportError as e:
        errors.append(f"❌ Impossible d'importer '{class_path}': {e}")
    except AttributeError as e:
        errors.append(f"❌ Classe '{class_name}' introuvable dans le module: {e}")
    except Exception as e:
        errors.append(f"❌ Erreur inattendue: {e}")
    
    return len(errors) == 0, errors


def print_section(title: str):
    """Affiche un titre de section"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def main():
    """Point d'entrée du script de test"""
    parser = argparse.ArgumentParser(
        description="🧪 Test du système Optuna-YAML",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'yaml_file',
        nargs='?',
        type=str,
        default=None,
        help='Chemin vers un fichier YAML à tester (optionnel)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "🧪 TEST DU SYSTÈME OPTUNA-YAML ".center(70, "="))
    
    all_success = True
    
    # Test 1: Imports
    print_section("📦 Test des imports Python")
    success, errors = test_imports()
    if success:
        print("✅ Tous les modules requis sont installés")
    else:
        all_success = False
        for error in errors:
            print(error)
    
    # Test 2: Structure de dossiers
    print_section("📁 Test de la structure de dossiers")
    success, errors = test_directory_structure()
    if success:
        print("✅ Structure de dossiers valide")
    else:
        all_success = False
        for error in errors:
            print(error)
    
    # Test 3: Fichier YAML (si fourni)
    if args.yaml_file:
        print_section(f"📄 Test du fichier YAML: {args.yaml_file}")
        
        success, errors = test_yaml_file(args.yaml_file)
        if success:
            print("✅ Fichier YAML valide")
            
            # Test 4: Import de la stratégie
            import yaml
            with open(args.yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'strategy' in config and 'class' in config['strategy']:
                class_path = config['strategy']['class']
                
                print_section(f"🎯 Test de l'import de stratégie: {class_path}")
                success, errors = test_strategy_import(class_path)
                if success:
                    print(f"✅ Stratégie '{class_path}' importée avec succès")
                else:
                    all_success = False
                    for error in errors:
                        print(error)
        else:
            all_success = False
            for error in errors:
                print(error)
    
    # Résumé final
    print("\n" + "="*70)
    if all_success:
        print("✅ TOUS LES TESTS RÉUSSIS ".center(70, " "))
        print("="*70)
        print("\n🎉 Le système est prêt à être utilisé !")
        
        if args.yaml_file:
            print(f"\nVous pouvez lancer l'optimisation avec:")
            print(f"  python scripts/run_optuna_from_yaml.py {args.yaml_file} --profile quick")
        else:
            print("\nPour tester un fichier YAML spécifique:")
            print("  python scripts/test_optuna_yaml_setup.py optimization_configs/masuperstrategie_optuna.yaml")
        
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ ".center(70, " "))
        print("="*70)
        print("\n⚠️ Veuillez corriger les erreurs ci-dessus avant de continuer.")
        return 1


if __name__ == "__main__":
    sys.exit(main())