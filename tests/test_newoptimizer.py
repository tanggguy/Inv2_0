#!/usr/bin/env python3
"""
🧪 SCRIPT DE BENCHMARK - Comparaison des Performances

Compare les performances entre l'ancienne et la nouvelle version de l'optimiseur.

Usage:
    python benchmark_optimizer.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from datetime import datetime
from optimization.optimizer import UnifiedOptimizer
from optimization.optimization_config import load_preset
from strategies.masuperstrategie import MaSuperStrategie


def print_header(title):
    """Affiche un header formaté"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def format_time(seconds):
    """Formate un temps en secondes"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def run_benchmark():
    """Lance le benchmark"""
    
    print_header("🧪 BENCHMARK - OPTIMISEUR OPTIMISÉ")
    
    # Configuration du test
    print("📋 Configuration du test:")
    print("  • Stratégie: MaSuperStrategie")
    print("  • Preset: quick")
    print("  • Type: Grid Search")
    
    # Charger la config
    config = load_preset('quick')
    
    # Afficher les détails
    param_grid = config.get('param_grid', {})
    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    
    print(f"  • Symboles: {', '.join(config.get('symbols', []))}")
    print(f"  • Période: {config['period']['start']} → {config['period']['end']}")
    print(f"  • Paramètres: {param_grid}")
    print(f"  • Combinaisons totales: {total_combos}")
    
    # Préparer les métriques
    metrics = {
        'preload_time': 0,
        'backtest_time': 0,
        'total_time': 0,
        'combinations_tested': 0,
        'best_sharpe': 0,
        'cache_used': False
    }
    
    print_header("🚀 EXÉCUTION DU BENCHMARK")
    
    # Timer global
    global_start = time.time()
    
    # Créer l'optimiseur
    print("📦 Création de l'optimiseur...")
    optimizer = UnifiedOptimizer(
        MaSuperStrategie,
        config,
        optimization_type='grid_search',
        verbose=False  # Pas de logs détaillés pour le benchmark
    )
    
    print(f"✅ Optimiseur créé: {optimizer.run_id}\n")
    
    # Callback de progression
    last_progress = 0
    def progress_callback(pct):
        nonlocal last_progress
        current = int(pct * 100)
        if current >= last_progress + 10:  # Afficher tous les 10%
            print(f"  Progression: {current}%")
            last_progress = current
    
    # Lancer l'optimisation
    print("⏱️  Démarrage de l'optimisation...\n")
    
    try:
        results = optimizer.run(progress_callback=progress_callback)
        
        global_end = time.time()
        
        # Calculer les métriques
        metrics['total_time'] = global_end - global_start
        metrics['combinations_tested'] = results.get('total_combinations', 0)
        metrics['best_sharpe'] = results.get('best', {}).get('sharpe', 0)
        metrics['cache_used'] = optimizer._cache_loaded
        
        # Calculer le temps moyen par combinaison
        time_per_combo = metrics['total_time'] / metrics['combinations_tested'] if metrics['combinations_tested'] > 0 else 0
        
        # Afficher les résultats
        print_header("📊 RÉSULTATS DU BENCHMARK")
        
        print("⏱️  Temps d'exécution:")
        print(f"  • Total: {format_time(metrics['total_time'])}")
        print(f"  • Par combinaison: {time_per_combo:.3f}s")
        
        print("\n📈 Performance:")
        print(f"  • Combinaisons testées: {metrics['combinations_tested']}")
        print(f"  • Meilleur Sharpe: {metrics['best_sharpe']:.2f}")
        print(f"  • Cache utilisé: {'✅ Oui' if metrics['cache_used'] else '❌ Non'}")
        
        print("\n🏆 Meilleurs paramètres:")
        best = results.get('best', {})
        for key, value in best.items():
            if key not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']:
                print(f"  • {key}: {value}")
        
        print("\n💡 Métriques de qualité:")
        print(f"  • Sharpe Ratio: {best.get('sharpe', 0):.2f}")
        print(f"  • Return: {best.get('return', 0):.2f}%")
        print(f"  • Max Drawdown: {best.get('drawdown', 0):.2f}%")
        print(f"  • Nombre de trades: {best.get('trades', 0)}")
        print(f"  • Win rate: {best.get('win_rate', 0):.2f}%")
        
        # Estimation avec l'ancienne version
        print_header("📉 COMPARAISON AVEC ANCIENNE VERSION (ESTIMATION)")
        
        # Estimer le temps de l'ancienne version
        # Hypothèse: 3s de chargement par combinaison + 0.6s de backtest
        old_time_estimate = (metrics['combinations_tested'] * 3.0) + (metrics['combinations_tested'] * 0.6)
        improvement = old_time_estimate / metrics['total_time'] if metrics['total_time'] > 0 else 0
        time_saved = old_time_estimate - metrics['total_time']
        
        print("⚠️  Note: Estimation basée sur temps de chargement de 3s/combo")
        print(f"\n  Ancienne version (estimée): {format_time(old_time_estimate)}")
        print(f"  Nouvelle version (mesurée): {format_time(metrics['total_time'])}")
        print(f"  \n  🚀 Amélioration: {improvement:.1f}x plus rapide !")
        print(f"  ⏰ Temps économisé: {format_time(time_saved)}")
        
        # Calcul du gain par optimisation
        if improvement >= 5:
            emoji = "🔥"
            comment = "EXCELLENT gain !"
        elif improvement >= 3:
            emoji = "🎯"
            comment = "Très bon gain !"
        elif improvement >= 2:
            emoji = "✅"
            comment = "Bon gain !"
        else:
            emoji = "⚠️"
            comment = "Gain modéré"
        
        print(f"\n  {emoji} {comment}")
        
        # Projection sur gros volumes
        print_header("🔮 PROJECTION SUR GROS VOLUMES")
        
        large_combos = 1000
        large_new_time = large_combos * time_per_combo
        large_old_time = large_combos * 3.6
        
        print(f"Pour {large_combos} combinaisons:")
        print(f"  Ancienne version: {format_time(large_old_time)}")
        print(f"  Nouvelle version: {format_time(large_new_time)}")
        print(f"  Économie: {format_time(large_old_time - large_new_time)}")
        
        # Sauvegarde des résultats
        print_header("💾 SAUVEGARDE")
        
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'run_id': optimizer.run_id,
            'config': {
                'strategy': 'MaSuperStrategie',
                'preset': 'quick',
                'symbols': config.get('symbols', []),
                'period': config['period'],
                'param_grid': param_grid
            },
            'metrics': metrics,
            'results': {
                'best_sharpe': best.get('sharpe', 0),
                'best_return': best.get('return', 0),
                'best_params': {k: v for k, v in best.items() 
                              if k not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']}
            },
            'performance': {
                'total_time_seconds': metrics['total_time'],
                'time_per_combo_seconds': time_per_combo,
                'estimated_old_time': old_time_estimate,
                'improvement_factor': improvement
            }
        }
        
        # Sauvegarder dans un fichier
        import json
        benchmark_file = Path(__file__).parent / 'benchmark_results.json'
        with open(benchmark_file, 'w') as f:
            json.dump(benchmark_results, f, indent=2)
        
        print(f"✅ Résultats sauvegardés dans: {benchmark_file}")
        
        print_header("✅ BENCHMARK TERMINÉ")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du benchmark: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale"""
    
    print("\n" + "🎯"*40)
    print("  SCRIPT DE BENCHMARK - OPTIMISEUR")
    print("🎯"*40)
    
    print("\nCe script va mesurer les performances de l'optimiseur optimisé.")
    print("Il comparera également avec une estimation de l'ancienne version.\n")
    
    input("Appuyez sur Entrée pour commencer...")
    
    success = run_benchmark()
    
    if success:
        print("\n✅ Benchmark réussi !")
        print("Les résultats ont été sauvegardés dans benchmark_results.json")
    else:
        print("\n❌ Le benchmark a échoué.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())