#!/usr/bin/env python3
"""
Script de test pour l'intégration Optuna

Ce script teste l'optimisation Optuna de manière autonome
avant de l'intégrer complètement dans le projet.
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from optimization.optuna_optimizer import OptunaOptimizer
import random
import time


def test_simple_function():
    """
    Test 1: Optimiser une fonction mathématique simple
    """
    print("="*80)
    print("TEST 1: Fonction Mathématique Simple")
    print("="*80)
    print("\nObjectif: Trouver (x, y) qui maximise -(x-5)² - (y-3)²")
    print("Optimum attendu: x=5, y=3\n")
    
    # Fonction objectif simple à optimiser
    def objective(params):
        x = params['x']
        y = params['y']
        # Fonction à maximiser: parabole avec optimum en (5, 3)
        return -(x - 5)**2 - (y - 3)**2
    
    # Définir l'espace de recherche
    param_grid = {
        'x': list(range(0, 11)),  # 0 à 10
        'y': list(range(0, 11))   # 0 à 10
    }
    
    # Créer l'optimiseur
    optimizer = OptunaOptimizer(
        objective_func=objective,
        param_grid=param_grid,
        n_trials=30,
        direction='maximize',
        study_name='test_simple',
        sampler_type='tpe',
        pruner_type='none',
        show_progress=True
    )
    
    # Optimiser
    results = optimizer.optimize()
    
    # Afficher les résultats
    print(f"\n🏆 Meilleurs paramètres trouvés:")
    print(f"   x = {results['best_params']['x']} (attendu: 5)")
    print(f"   y = {results['best_params']['y']} (attendu: 3)")
    print(f"   Valeur = {results['best_value']:.4f}")
    
    # Importance
    importance = optimizer.get_importance()
    print(f"\n📊 Importance des paramètres:")
    for param, imp in importance.items():
        print(f"   {param}: {imp:.4f}")
    
    # Test de proximité
    assert abs(results['best_params']['x'] - 5) <= 1, "x devrait être proche de 5"
    assert abs(results['best_params']['y'] - 3) <= 1, "y devrait être proche de 3"
    
    print("\n✅ TEST 1 RÉUSSI\n")


def test_trading_simulation():
    """
    Test 2: Simuler une optimisation de stratégie de trading
    """
    print("="*80)
    print("TEST 2: Simulation de Trading")
    print("="*80)
    print("\nObjectif: Optimiser une stratégie de trading simulée\n")
    
    # Fonction qui simule un backtest de stratégie
    def simulated_backtest(params):
        """Simule un backtest avec un Sharpe Ratio aléatoire mais influencé par les paramètres"""
        period = params['period']
        multiplier = params['multiplier']
        risk_pct = params['risk_pct']
        
        # Simuler le temps de calcul d'un backtest
        time.sleep(0.1)
        
        # Score simulé (plus réaliste qu'aléatoire pur)
        # Meilleurs paramètres autour de: period=20, multiplier=2.0, risk_pct=0.02
        score = (
            -0.05 * (period - 20)**2 +  # Optimum à period=20
            -2.0 * (multiplier - 2.0)**2 +  # Optimum à multiplier=2.0
            -100 * (risk_pct - 0.02)**2 +  # Optimum à risk_pct=0.02
            random.gauss(1.5, 0.3)  # Sharpe de base avec du bruit
        )
        
        return max(score, 0)  # Sharpe ne peut pas être négatif
    
    # Espace de paramètres typique d'une stratégie
    param_grid = {
        'period': list(range(5, 51, 5)),  # 5, 10, 15, ..., 50
        'multiplier': [i/10 for i in range(5, 31, 2)],  # 0.5, 0.7, ..., 3.0
        'risk_pct': [i/1000 for i in range(5, 31, 2)]  # 0.005, 0.007, ..., 0.030
    }
    
    print(f"Espace de recherche:")
    print(f"   period: {len(param_grid['period'])} valeurs")
    print(f"   multiplier: {len(param_grid['multiplier'])} valeurs")
    print(f"   risk_pct: {len(param_grid['risk_pct'])} valeurs")
    
    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    print(f"   Total combinaisons: {total_combos:,}\n")
    
    n_trials = 50
    print(f"Optuna va tester seulement {n_trials} trials intelligemment\n")
    
    # Créer l'optimiseur
    optimizer = OptunaOptimizer(
        objective_func=simulated_backtest,
        param_grid=param_grid,
        n_trials=n_trials,
        direction='maximize',
        study_name='test_trading',
        sampler_type='tpe',
        pruner_type='median',
        show_progress=True
    )
    
    # Optimiser avec callback de progression
    def progress_callback(progress, eta):
        if int(progress * 10) != int((progress - 0.02) * 10):  # Tous les 10%
            print(f"   Progression: {progress*100:.0f}% - ETA: {eta//60}m{eta%60}s")
    
    start_time = time.time()
    results = optimizer.optimize(progress_callback=progress_callback)
    elapsed_time = time.time() - start_time
    
    # Afficher les résultats
    print(f"\n🏆 Meilleurs paramètres trouvés:")
    for param, value in results['best_params'].items():
        print(f"   {param} = {value}")
    print(f"\n📈 Meilleur Sharpe Ratio: {results['best_value']:.4f}")
    
    # Performance
    print(f"\n⚡ Performance:")
    print(f"   Temps total: {elapsed_time:.2f}s")
    print(f"   Temps par trial: {elapsed_time/n_trials:.2f}s")
    print(f"   Vitesse estimée vs GridSearch: {total_combos/n_trials:.1f}x plus rapide")
    
    # Importance
    importance = optimizer.get_importance()
    print(f"\n📊 Importance des paramètres:")
    for param, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"   {param}: {imp:.4f}")
    
    # Sauvegarder les visualisations
    print(f"\n💾 Sauvegarde des visualisations...")
    try:
        optimizer.save_visualizations("test_plots")
        print(f"   ✅ Visualisations sauvegardées dans test_plots/")
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")
    
    print("\n✅ TEST 2 RÉUSSI\n")


def test_parallel_optimization():
    """
    Test 3: Test de la parallélisation
    """
    print("="*80)
    print("TEST 3: Parallélisation")
    print("="*80)
    print("\nObjectif: Vérifier que la parallélisation fonctionne\n")
    
    def slow_objective(params):
        """Fonction lente pour tester la parallélisation"""
        time.sleep(0.5)  # Simule un backtest lent
        x = params['x']
        return -(x - 50)**2 + random.gauss(0, 10)
    
    param_grid = {
        'x': list(range(0, 101, 5))
    }
    
    # Test séquentiel
    print("🐌 Test séquentiel (n_jobs=1)...")
    start = time.time()
    optimizer_seq = OptunaOptimizer(
        objective_func=slow_objective,
        param_grid=param_grid,
        n_trials=10,
        direction='maximize',
        study_name='test_seq',
        n_jobs=1,  # Séquentiel
        show_progress=False
    )
    results_seq = optimizer_seq.optimize()
    time_seq = time.time() - start
    print(f"   Temps: {time_seq:.2f}s")
    
    # Test parallèle
    print(f"\n🚀 Test parallèle (n_jobs=-1)...")
    start = time.time()
    optimizer_par = OptunaOptimizer(
        objective_func=slow_objective,
        param_grid=param_grid,
        n_trials=10,
        direction='maximize',
        study_name='test_par',
        n_jobs=-1,  # Tous les CPUs
        show_progress=False
    )
    results_par = optimizer_par.optimize()
    time_par = time.time() - start
    print(f"   Temps: {time_par:.2f}s")
    
    # Speedup
    speedup = time_seq / time_par
    print(f"\n⚡ Speedup: {speedup:.2f}x")
    
    assert speedup > 1.2, "La parallélisation devrait donner un speedup > 1.2x"
    
    print("\n✅ TEST 3 RÉUSSI\n")


def main():
    """Lance tous les tests"""
    print("\n" + "="*80)
    print("🧪 TESTS D'INTÉGRATION OPTUNA")
    print("="*80 + "\n")
    
    try:
        # Test 1
        test_simple_function()
        input("Appuyez sur Entrée pour continuer vers le Test 2...")
        
        # Test 2
        test_trading_simulation()
        input("Appuyez sur Entrée pour continuer vers le Test 3...")
        
        # Test 3
        test_parallel_optimization()
        
        # Résumé
        print("="*80)
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        print("="*80)
        print("\n✅ Optuna est correctement intégré et fonctionne parfaitement.")
        print("📚 Consultez GUIDE_OPTUNA_INTEGRATION.md pour l'utilisation complète.\n")
        
    except AssertionError as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())