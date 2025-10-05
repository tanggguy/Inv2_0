#!/usr/bin/env python3
"""
🧪 SCRIPT DE TEST - Parallélisation

Compare les performances entre mode séquentiel et parallèle.

Usage:
    python test_parallel.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from datetime import datetime
from multiprocessing import cpu_count
from optimization.optimizer import UnifiedOptimizer
from optimization.optimization_config import load_preset
from strategies.masuperstrategie import MaSuperStrategie


def print_header(title, char="="):
    """Affiche un header formaté"""
    print("\n" + char*80)
    print(f"  {title}")
    print(char*80 + "\n")


def format_time(seconds):
    """Formate un temps en secondes"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def test_configuration():
    """Affiche la configuration système"""
    print_header("🖥️  CONFIGURATION SYSTÈME")
    
    print(f"CPU Cores: {cpu_count()}")
    print(f"Python: {sys.version.split()[0]}")
    
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        print(f"RAM Totale: {ram_gb:.1f} GB")
        print(f"RAM Disponible: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    except ImportError:
        print("RAM: (installer psutil pour voir)")
    
    print("\n✅ Configuration OK")


def run_test(use_parallel: bool, preset_name: str = 'quick') -> dict:
    """
    Lance un test d'optimisation
    
    Args:
        use_parallel: Utiliser la parallélisation
        preset_name: Nom du preset
    
    Returns:
        Dict avec métriques
    """
    mode = "PARALLÈLE" if use_parallel else "SÉQUENTIEL"
    print_header(f"🧪 TEST {mode}")
    
    # Charger config
    config = load_preset(preset_name)
    
    # Calculer le nombre de combinaisons
    param_grid = config.get('param_grid', {})
    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    
    print(f"Preset: {preset_name}")
    print(f"Stratégie: MaSuperStrategie")
    print(f"Symboles: {', '.join(config.get('symbols', []))}")
    print(f"Période: {config['period']['start']} → {config['period']['end']}")
    print(f"Combinaisons: {total_combos}")
    if use_parallel:
        n_workers = max(1, cpu_count() - 2)
        print(f"Workers: {n_workers}/{cpu_count()} cores")
    print()
    
    # Créer l'optimiseur
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='grid_search',
        use_parallel=use_parallel,
        verbose=False  # Pas de logs détaillés pour le test
    )
    
    # Timer
    start_time = time.time()
    
    # Lancer
    print(f"⏱️  Démarrage...")
    
    try:
        results = optimizer.run()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Métriques
        metrics = {
            'mode': mode,
            'parallel': use_parallel,
            'total_time': total_time,
            'total_combos': total_combos,
            'time_per_combo': total_time / total_combos if total_combos > 0 else 0,
            'best_sharpe': results.get('best', {}).get('sharpe', 0),
            'valid_results': len(results.get('all_results', [])),
            'run_id': results.get('run_id', 'N/A')
        }
        
        # Afficher résultats
        print(f"\n✅ Test terminé !")
        print(f"   Temps total: {format_time(total_time)}")
        print(f"   Temps/combo: {metrics['time_per_combo']*1000:.1f}ms")
        print(f"   Résultats valides: {metrics['valid_results']}/{total_combos}")
        print(f"   Meilleur Sharpe: {metrics['best_sharpe']:.2f}")
        
        return metrics
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_results(seq_metrics, par_metrics):
    """Compare les résultats entre séquentiel et parallèle"""
    print_header("📊 COMPARAISON DES RÉSULTATS")
    
    # Table comparative
    print(f"{'Métrique':<25} {'Séquentiel':<15} {'Parallèle':<15} {'Gain':<10}")
    print("-" * 70)
    
    # Temps total
    seq_time = seq_metrics['total_time']
    par_time = par_metrics['total_time']
    speedup = seq_time / par_time if par_time > 0 else 0
    
    print(f"{'Temps total':<25} {format_time(seq_time):<15} {format_time(par_time):<15} {speedup:.2f}x")
    
    # Temps par combo
    seq_per = seq_metrics['time_per_combo'] * 1000
    par_per = par_metrics['time_per_combo'] * 1000
    print(f"{'Temps/combo (ms)':<25} {seq_per:.1f}ms{'':<9} {par_per:.1f}ms{'':<9} {seq_per/par_per:.2f}x")
    
    # Résultats
    seq_valid = seq_metrics['valid_results']
    par_valid = par_metrics['valid_results']
    print(f"{'Résultats valides':<25} {seq_valid:<15} {par_valid:<15} {'=':<10}")
    
    # Sharpe
    seq_sharpe = seq_metrics['best_sharpe']
    par_sharpe = par_metrics['best_sharpe']
    diff = abs(seq_sharpe - par_sharpe)
    print(f"{'Meilleur Sharpe':<25} {seq_sharpe:.2f}{'':<12} {par_sharpe:.2f}{'':<12} Δ={diff:.3f}")
    
    # Analyse du speedup
    print_header("🚀 ANALYSE DU SPEEDUP")
    
    n_cores = cpu_count()
    n_workers = max(1, n_cores - 2)
    theoretical_speedup = n_workers
    efficiency = (speedup / theoretical_speedup) * 100 if theoretical_speedup > 0 else 0
    
    print(f"Speedup réel:        {speedup:.2f}x")
    print(f"Speedup théorique:   {theoretical_speedup:.2f}x ({n_workers} workers)")
    print(f"Efficacité:          {efficiency:.1f}%")
    
    # Évaluation
    print("\n💡 Évaluation:")
    if speedup >= theoretical_speedup * 0.8:
        print("   🔥 EXCELLENT ! Parallélisation très efficace !")
    elif speedup >= theoretical_speedup * 0.6:
        print("   ✅ BIEN ! Parallélisation efficace.")
    elif speedup >= theoretical_speedup * 0.4:
        print("   ⚠️  BON mais peut être amélioré.")
    else:
        print("   ❌ Faible gain. Vérifier la configuration.")
    
    # Temps économisé
    time_saved = seq_time - par_time
    print(f"\n⏰ Temps économisé: {format_time(time_saved)}")
    
    # Projection sur gros volumes
    print_header("🔮 PROJECTION SUR GROS VOLUMES")
    
    large_combos = [100, 500, 1000, 2000]
    
    print(f"{'Combinaisons':<15} {'Séquentiel':<15} {'Parallèle':<15} {'Économie':<15}")
    print("-" * 65)
    
    for combos in large_combos:
        seq_large = combos * seq_metrics['time_per_combo']
        par_large = combos * par_metrics['time_per_combo']
        saved = seq_large - par_large
        
        print(f"{combos:<15} {format_time(seq_large):<15} {format_time(par_large):<15} {format_time(saved):<15}")
    
    # Recommandations
    print_header("💡 RECOMMANDATIONS")
    
    if speedup > 1.5:
        print("✅ La parallélisation fonctionne bien !")
        print("   → Utilisez use_parallel=True par défaut")
        print(f"   → Gain moyen attendu: {speedup:.1f}x plus rapide")
    else:
        print("⚠️  Le speedup est faible. Causes possibles :")
        print("   - Nombre de combinaisons trop petit (overhead > gain)")
        print("   - Problème de sérialisation des données")
        print("   - CPU limité par autre chose (I/O, mémoire)")
    
    print(f"\n📝 Utilisez parallèle quand : combinaisons > {100 // speedup:.0f}")


def main():
    """Fonction principale"""
    
    print("\n" + "🧪"*40)
    print("  SCRIPT DE TEST - PARALLÉLISATION")
    print("🧪"*40)
    
    # Configuration système
    test_configuration()
    
    input("\nAppuyez sur Entrée pour démarrer les tests...\n")
    
    # Test 1: Mode SÉQUENTIEL
    print_header("1️⃣  TEST SÉQUENTIEL", "=")
    seq_metrics = run_test(use_parallel=False, preset_name='quick')
    
    if seq_metrics is None:
        print("\n❌ Test séquentiel échoué. Arrêt.")
        return 1
    
    # Petite pause
    print("\n" + "⏳"*40)
    print("  Pause de 3 secondes avant le test parallèle...")
    print("⏳"*40)
    time.sleep(3)
    
    # Test 2: Mode PARALLÈLE
    print_header("2️⃣  TEST PARALLÈLE", "=")
    par_metrics = run_test(use_parallel=True, preset_name='quick')
    
    if par_metrics is None:
        print("\n❌ Test parallèle échoué.")
        print("\n💡 Suggestions :")
        print("   - Vérifier que optimizer_worker.py est présent")
        print("   - Vérifier les imports")
        print("   - Essayer avec moins de workers")
        return 1
    
    # Comparaison
    compare_results(seq_metrics, par_metrics)
    
    # Sauvegarde
    print_header("💾 SAUVEGARDE DES RÉSULTATS")
    
    import json
    
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_cores': cpu_count(),
            'python_version': sys.version.split()[0]
        },
        'sequential': seq_metrics,
        'parallel': par_metrics,
        'comparison': {
            'speedup': seq_metrics['total_time'] / par_metrics['total_time'],
            'time_saved_seconds': seq_metrics['total_time'] - par_metrics['total_time']
        }
    }
    
    results_file = Path(__file__).parent / 'test_parallel_results.json'
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"✅ Résultats sauvegardés dans: {results_file}")
    
    # Conclusion
    print_header("✅ TESTS TERMINÉS")
    
    speedup = test_results['comparison']['speedup']
    
    print(f"🎯 Speedup global: {speedup:.2f}x")
    print(f"⏰ Temps économisé: {format_time(test_results['comparison']['time_saved_seconds'])}")
    
    if speedup >= 4:
        print("\n🔥 EXCELLENT ! Votre système tire pleinement parti de la parallélisation !")
    elif speedup >= 2.5:
        print("\n✅ TRÈS BIEN ! La parallélisation est efficace !")
    elif speedup >= 1.5:
        print("\n👍 BIEN ! Gain significatif avec la parallélisation.")
    else:
        print("\n⚠️  Gain modeste. Consultez le guide pour optimiser.")
    
    print("\n📚 Consultez GUIDE_PARALLELISATION.md pour plus d'infos.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())