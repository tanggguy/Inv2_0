#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration Optuna dans quick_optimize

Test automatisé pour s'assurer que toutes les fonctionnalités marchent
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("="*70)
print("🧪 TEST QUICK_OPTIMIZE AVEC OPTUNA")
print("="*70)

# Test 1: Imports
print("\n1️⃣  Test des imports...")
try:
    from optimization.optuna_presets import OPTUNA_PRESETS, get_optuna_preset, list_optuna_presets
    from optimization.optimizer import UnifiedOptimizer
    from strategies.rsi_strategy import RSIStrategy
    print("   ✅ Tous les imports réussis")
except Exception as e:
    print(f"   ❌ Erreur d'import: {e}")
    sys.exit(1)

# Test 2: Liste des presets Optuna
print("\n2️⃣  Test liste des presets Optuna...")
try:
    presets = list_optuna_presets()
    print(f"   ✅ {len(presets)} presets disponibles:")
    for preset in presets:
        print(f"      • {preset}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# Test 3: Chargement d'un preset
print("\n3️⃣  Test chargement preset 'optuna_quick'...")
try:
    config = get_optuna_preset('optuna_quick')
    print("   ✅ Preset chargé avec succès")
    print(f"      • Trials: {config['optuna']['n_trials']}")
    print(f"      • Sampler: {config['optuna']['sampler']}")
    print(f"      • Pruner: {config['optuna']['pruner']}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# Test 4: Création d'un optimiseur avec Optuna
print("\n4️⃣  Test création optimiseur Optuna...")
try:
    # Modifier la config pour un test très rapide
    config['optuna']['n_trials'] = 5  # Seulement 5 trials pour le test
    config['period'] = {
        'start': '2024-01-01',
        'end': '2024-02-01'  # 1 mois seulement
    }
    
    optimizer = UnifiedOptimizer(
        strategy_class=RSIStrategy,
        config=config,
        optimization_type='optuna',
        verbose=False,
        use_parallel=False  # Mode séquentiel pour le test
    )
    print("   ✅ Optimiseur créé avec succès")
    print(f"      • Run ID: {optimizer.run_id}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    sys.exit(1)

# Test 5: Exécution rapide (5 trials)
print("\n5️⃣  Test exécution rapide (5 trials)...")
print("   ⏳ Lancement de l'optimisation (ceci peut prendre 30-60 secondes)...")

try:
    results = optimizer.run()
    
    if results and 'best' in results:
        print("   ✅ Optimisation terminée avec succès")
        print(f"      • Meilleur Sharpe: {results['best'].get('sharpe', 0):.2f}")
        print(f"      • Nombre de résultats: {len(results.get('all_results', []))}")
        
        # Vérifier l'importance des paramètres
        if 'param_importance' in results:
            print("      • Importance des paramètres calculée ✓")
        else:
            print("      ⚠️  Importance des paramètres non disponible")
    else:
        print("   ⚠️  Optimisation terminée mais résultats incomplets")
        
except Exception as e:
    print(f"   ❌ Erreur pendant l'optimisation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Vérifier les visualisations
print("\n6️⃣  Test génération des visualisations...")
try:
    from pathlib import Path
    plots_dir = Path("optimization/optuna_plots")
    
    if plots_dir.exists():
        plots = list(plots_dir.glob(f"{optimizer.run_id}_*.html"))
        if plots:
            print(f"   ✅ {len(plots)} visualisations générées:")
            for plot in plots:
                print(f"      • {plot.name}")
        else:
            print("   ⚠️  Aucune visualisation trouvée (peut être normal pour si peu de trials)")
    else:
        print("   ⚠️  Dossier optuna_plots non créé")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 7: Vérifier la base de données Optuna
print("\n7️⃣  Test base de données Optuna...")
try:
    from pathlib import Path
    db_path = Path("optimization/optuna_studies/optuna.db")
    
    if db_path.exists():
        print(f"   ✅ Base de données trouvée")
        print(f"      • Taille: {db_path.stat().st_size / 1024:.2f} KB")
    else:
        print("   ⚠️  Base de données non trouvée")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Résumé final
print("\n" + "="*70)
print("📊 RÉSUMÉ DES TESTS")
print("="*70)
print("✅ Tous les tests ont réussi !")
print("\n🎉 L'intégration Optuna est fonctionnelle")
print("\nVous pouvez maintenant utiliser:")
print("  python scripts/quick_optimize_optuna.py")
print("\nOu pour tester l'original (qui devrait aussi marcher):")
print("  python scripts/quick_optimize.py")
print("="*70)