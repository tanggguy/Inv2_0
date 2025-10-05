#!/usr/bin/env python3
"""
Script de test pour valider le refactoring de l'optimisation

Teste :
1. Chargement des configs
2. Grid Search
3. Walk-Forward  
4. Stockage des résultats
5. Historique
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimization.optimization_config import OptimizationConfig, load_preset
from optimization.optimizer import UnifiedOptimizer
from optimization.results_storage import ResultsStorage
from strategies.masuperstrategie import MaSuperStrategie


def test_config():
    """Test 1: Configuration"""
    print("\n" + "="*70)
    print("TEST 1: CONFIGURATION")
    print("="*70)
    
    config_manager = OptimizationConfig()
    
    # Liste des presets
    presets = config_manager.list_presets()
    print(f"✓ {len(presets)} presets chargés: {', '.join(presets)}")
    
    # Charger un preset
    quick = config_manager.get_preset('quick')
    print(f"\n✓ Preset 'quick' chargé:")
    print(config_manager.get_config_summary(quick))
    
    # Validation
    is_valid, errors = config_manager.validate_config(quick)
    assert is_valid, f"Config invalide: {errors}"
    print("\n✓ Validation OK")
    
    return quick


def test_grid_search(config):
    """Test 2: Grid Search"""
    print("\n" + "="*70)
    print("TEST 2: GRID SEARCH")
    print("="*70)
    
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='grid_search',
        verbose=True
    )
    
    print(f"\n🔬 Lancement Grid Search...")
    print(f"   Run ID: {optimizer.run_id}")
    
    results = optimizer.run()
    
    print(f"\n✓ Grid Search terminé")
    print(f"   Combinaisons testées: {results['total_combinations']}")
    print(f"   Meilleur Sharpe: {results['best'].get('sharpe', 0):.2f}")
    print(f"   Meilleur Return: {results['best'].get('return', 0):.2f}%")
    
    return results


def test_walk_forward():
    """Test 3: Walk-Forward"""
    print("\n" + "="*70)
    print("TEST 3: WALK-FORWARD")
    print("="*70)
    
    config = load_preset('walk_forward_quick')
    
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='walk_forward',
        verbose=True
    )
    
    print(f"\n🚶 Lancement Walk-Forward...")
    print(f"   Run ID: {optimizer.run_id}")
    
    results = optimizer.run()
    
    print(f"\n✓ Walk-Forward terminé")
    if 'statistics' in results:
        stats = results['statistics']
        print(f"   Avg In-Sample Sharpe: {stats.get('avg_in_sharpe', 0):.2f}")
        print(f"   Avg Out-Sample Sharpe: {stats.get('avg_out_sharpe', 0):.2f}")
        print(f"   Dégradation moyenne: {stats.get('avg_degradation', 0):.2f}")
    
    return results


def test_storage():
    """Test 4: Stockage et historique"""
    print("\n" + "="*70)
    print("TEST 4: STOCKAGE ET HISTORIQUE")
    print("="*70)
    
    storage = ResultsStorage()
    
    # Lister les runs
    runs = storage.list_runs()
    print(f"\n✓ {len(runs)} runs dans l'historique")
    
    if runs:
        # Afficher les 3 derniers
        print("\n📋 Derniers runs:")
        for run in runs[-3:]:
            print(f"   • {run['run_id']}")
            print(f"     {run['strategy']} - Sharpe: {run['best_sharpe']:.2f}")
        
        # Charger un run
        last_run_id = runs[-1]['run_id']
        print(f"\n📂 Chargement du run: {last_run_id}")
        loaded = storage.load_run(last_run_id)
        
        if loaded:
            print(f"   ✓ Run chargé:")
            print(f"     Strategy: {loaded['summary']['strategy']}")
            print(f"     Type: {loaded['summary']['optimization_type']}")
            print(f"     Best Sharpe: {loaded['summary']['best_params'].get('sharpe', 0):.2f}")
        
        # Statistiques globales
        print("\n📊 Statistiques globales:")
        stats = storage.get_statistics()
        print(f"   Total runs: {stats['total_runs']}")
        print(f"   Stratégies testées: {stats['total_strategies']}")
        print(f"   Best Sharpe ever: {stats['best_sharpe']:.2f}")
        print(f"   Best Return ever: {stats['best_return']:.2f}%")
        
        # Comparaison (si au moins 2 runs)
        if len(runs) >= 2:
            print("\n🔍 Comparaison des 2 derniers runs:")
            comparison = storage.compare_runs([runs[-2]['run_id'], runs[-1]['run_id']])
            if comparison is not None:
                print(comparison.to_string(index=False))


def test_custom_config():
    """Test 5: Configuration custom"""
    print("\n" + "="*70)
    print("TEST 5: CONFIGURATION CUSTOM")
    print("="*70)
    
    config_manager = OptimizationConfig()
    
    # Créer une config custom
    custom = config_manager.create_custom(
        symbols=['AAPL'],
        start_date='2023-06-01',
        end_date='2023-12-31',
        param_grid={
            'ma_period': [15, 25],
            'rsi_period': [14]
        },
        capital=50000,
        name="Test Custom",
        description="Config de test personnalisée"
    )
    
    print("\n✓ Config custom créée:")
    print(config_manager.get_config_summary(custom))
    
    # Merge avec preset
    print("\n🔀 Merge avec preset 'quick':")
    merged = config_manager.merge_configs('quick', {
        'symbols': ['MSFT'],
        'capital': 150000
    })
    print(config_manager.get_config_summary(merged))
    
    return custom


def main():
    """Fonction principale de test"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           🧪 TEST DU REFACTORING - OPTIMIZATION MODULE 🧪           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Test 1: Config
        config = test_config()
        
        # Test 2: Grid Search
        grid_results = test_grid_search(config)
        
        # Test 3: Walk-Forward (optionnel - prend plus de temps)
        run_walk_forward = input("\n▶ Lancer Walk-Forward (plus long) ? (o/n) [n]: ").strip().lower()
        if run_walk_forward == 'o':
            wf_results = test_walk_forward()
        
        # Test 4: Storage
        test_storage()
        
        # Test 5: Custom config
        test_custom_config()
        
        # Résumé final
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("="*70)
        
        print("\n📁 Fichiers créés:")
        print("   • config/optimization_presets.json")
        print("   • optimization/config.py")
        print("   • optimization/optimizer.py")
        print("   • optimization/results_storage.py")
        print("   • results/history/optimization_runs.json")
        print("   • results/details/{run_id}/")
        
        print("\n🎯 Prochaines étapes:")
        print("   1. ✓ Refactoring terminé")
        print("   2. → Créer le dashboard Streamlit")
        print("   3. → Migrer les anciens scripts si nécessaire")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)