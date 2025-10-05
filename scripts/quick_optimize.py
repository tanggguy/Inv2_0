#!/usr/bin/env python3
"""
Quick Start - Optimisation facile avec le nouveau système

Utilisez ce script pour lancer rapidement des optimisations
sans écrire de code
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimization.optimization_config import OptimizationConfig, load_preset
from optimization.optimizer import UnifiedOptimizer
from optimization.results_storage import ResultsStorage

# Import des stratégies disponibles
from strategies.masuperstrategie import MaSuperStrategie
from strategies.moving_average import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy

try:
    from strategies.advanced_strategies import (
        MACrossoverAdvanced,
        RSITrailingStop,
        BreakoutATRStop,
        MomentumMultipleStops
    )
    ADVANCED_AVAILABLE = True
except:
    ADVANCED_AVAILABLE = False


def print_banner():
    """Affiche le banner"""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           🚀 QUICK START - OPTIMISATION SIMPLIFIÉE 🚀              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def choose_strategy():
    """Permet de choisir une stratégie"""
    strategies = {
        '1': ('MaSuperStrategie', MaSuperStrategie),
        '2': ('MovingAverage', MovingAverageStrategy),
        '3': ('RSI', RSIStrategy),
    }
    
    if ADVANCED_AVAILABLE:
        strategies.update({
            '4': ('MACrossoverAdvanced', MACrossoverAdvanced),
            '5': ('RSITrailingStop', RSITrailingStop),
            '6': ('BreakoutATRStop', BreakoutATRStop),
            '7': ('MomentumMultipleStops', MomentumMultipleStops),
        })
    
    print("\n📊 CHOISIR UNE STRATÉGIE")
    print("="*70)
    
    for key, (name, _) in strategies.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input(f"\nVotre choix (1-{len(strategies)}) [1]: ").strip() or '1'
        if choice in strategies:
            name, strategy_class = strategies[choice]
            print(f"\n✓ Stratégie sélectionnée: {name}")
            return name, strategy_class
        print("❌ Choix invalide")


def choose_preset(strategy_name: str = None):
    """
    Permet de choisir un preset (adapté à la stratégie si fournie)
    
    Args:
        strategy_name: Nom de la stratégie pour adapter automatiquement
    
    Returns:
        (preset_name, config)
    """
    config_manager = OptimizationConfig()
    presets = config_manager.list_presets()
    
    print("\n⚙️  CHOISIR UNE CONFIGURATION")
    print("="*70)
    
    for i, preset_name in enumerate(presets, 1):
        preset = config_manager.get_preset(preset_name)
        desc = preset.get('description', 'N/A')
        print(f"  {i}. {preset_name:<20} - {desc}")
    
    while True:
        choice = input(f"\nVotre choix (1-{len(presets)}) [2]: ").strip() or '2'
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                preset_name = presets[idx]
                
                # 🔥 MODIFICATION : Adapter à la stratégie si fournie
                if strategy_name:
                    config = config_manager.get_config_for_strategy(
                        strategy_name=strategy_name,
                        preset_name=preset_name
                    )
                    
                    if config.get('_metadata', {}).get('adapted'):
                        print(f"\n✓ Configuration adaptée pour {strategy_name}")
                else:
                    config = config_manager.get_preset(preset_name)
                
                print(f"\n✓ Configuration sélectionnée: {preset_name}")
                return preset_name, config
        except:
            pass
        print("❌ Choix invalide")


def choose_optimization_type():
    """Permet de choisir le type d'optimisation"""
    types = {
        '1': ('grid_search', 'Grid Search', 'Test toutes les combinaisons'),
        '2': ('walk_forward', 'Walk-Forward', 'Validation robuste anti-overfitting'),
    }
    
    print("\n🔬 TYPE D'OPTIMISATION")
    print("="*70)
    
    for key, (_, name, desc) in types.items():
        print(f"  {key}. {name:<20} - {desc}")
    
    while True:
        choice = input("\nVotre choix (1-2) [1]: ").strip() or '1'
        if choice in types:
            opt_type, name, _ = types[choice]
            print(f"\n✓ Type sélectionné: {name}")
            return opt_type
        print("❌ Choix invalide")


def customize_config(config, strategy_name):
    """Permet de personnaliser la config"""
    print("\n🔧 PERSONNALISATION (optionnel)")
    print("="*70)
    
    customize = input("Modifier la configuration ? (o/n) [n]: ").strip().lower()
    
    if customize != 'o':
        return config
    
    config_manager = OptimizationConfig()
    
    # Modifier les symboles
    print(f"\nSymboles actuels: {', '.join(config['symbols'])}")
    new_symbols = input("Nouveaux symboles (séparés par espace) [Enter pour garder]: ").strip()
    if new_symbols:
        config['symbols'] = new_symbols.split()
        print(f"✓ Symboles mis à jour: {', '.join(config['symbols'])}")
    
    # Modifier le capital
    print(f"\nCapital actuel: ${config.get('capital', 100000):,.2f}")
    new_capital = input("Nouveau capital [Enter pour garder]: ").strip()
    if new_capital:
        try:
            config['capital'] = float(new_capital)
            print(f"✓ Capital mis à jour: ${config['capital']:,.2f}")
        except:
            print("⚠️  Valeur invalide, capital inchangé")
    
    # Afficher résumé
    print("\n📋 Configuration finale:")
    print(config_manager.get_config_summary(config))
    
    confirm = input("\nConfirmer ? (o/n) [o]: ").strip().lower() or 'o'
    
    return config if confirm == 'o' else None


def run_optimization(strategy_class, config, opt_type):
    """Lance l'optimisation"""
    print("\n" + "="*70)
    print("🚀 LANCEMENT DE L'OPTIMISATION")
    print("="*70)
    
    # Créer l'optimiseur
    optimizer = UnifiedOptimizer(
        strategy_class=strategy_class,
        config=config,
        optimization_type=opt_type,
        verbose=True
    )
    
    print(f"\nRun ID: {optimizer.run_id}")
    print("\n⏳ Optimisation en cours...")
    print("(Ceci peut prendre quelques minutes)\n")
    
    # Lancer avec callback de progression
    def progress_callback(pct):
        bar_length = 50
        filled = int(bar_length * pct)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f'\r[{bar}] {pct*100:.1f}%', end='', flush=True)
    
    try:
        results = optimizer.run(progress_callback=progress_callback)
        print('\n')  # Nouvelle ligne après la barre de progression
        
        return results
        
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_results(results):
    """Affiche les résultats"""
    if not results or 'best' not in results:
        print("\n❌ Pas de résultats disponibles")
        return
    
    print("\n" + "="*70)
    print("🏆 RÉSULTATS")
    print("="*70)
    
    best = results['best']
    
    # Métriques principales
    print("\n📈 Métriques de Performance:")
    print(f"   Sharpe Ratio:     {best.get('sharpe', 0):>10.2f}")
    print(f"   Rendement Total:  {best.get('return', 0):>10.2f}%")
    print(f"   Max Drawdown:     {best.get('drawdown', 0):>10.2f}%")
    print(f"   Nombre de Trades: {best.get('trades', 0):>10}")
    print(f"   Taux de Réussite: {best.get('win_rate', 0):>10.2f}%")
    
    # Meilleurs paramètres
    print("\n🎯 Meilleurs Paramètres:")
    for key, value in best.items():
        if key not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']:
            print(f"   {key:.<25} {value}")
    
    # Statistiques supplémentaires
    if 'statistics' in results:
        stats = results['statistics']
        print("\n📊 Statistiques Walk-Forward:")
        print(f"   Avg In-Sample Sharpe:  {stats.get('avg_in_sharpe', 0):>10.2f}")
        print(f"   Avg Out-Sample Sharpe: {stats.get('avg_out_sharpe', 0):>10.2f}")
        print(f"   Dégradation Moyenne:   {stats.get('avg_degradation', 0):>10.2f}")
    
    # Évaluation
    sharpe = best.get('sharpe', 0)
    print("\n💡 Évaluation:")
    if sharpe > 2:
        print("   ⭐⭐⭐⭐⭐ EXCELLENTE performance !")
    elif sharpe > 1.5:
        print("   ⭐⭐⭐⭐ TRÈS BONNE performance")
    elif sharpe > 1:
        print("   ⭐⭐⭐ BONNE performance")
    elif sharpe > 0.5:
        print("   ⭐⭐ Performance ACCEPTABLE")
    else:
        print("   ⭐ Performance FAIBLE")
    
    print("\n✅ Résultats sauvegardés automatiquement")
    print(f"   Run ID: {results['run_id']}")


def view_history():
    """Affiche l'historique"""
    storage = ResultsStorage()
    runs = storage.list_runs()
    
    if not runs:
        print("\n📋 Aucun run dans l'historique")
        return
    
    print("\n📋 HISTORIQUE DES OPTIMISATIONS")
    print("="*70)
    
    # Afficher les 10 derniers
    for run in runs[-10:]:
        print(f"\n• {run['run_id']}")
        print(f"  Stratégie: {run['strategy']}")
        print(f"  Type: {run['type']}")
        print(f"  Sharpe: {run['best_sharpe']:.2f} | Return: {run['best_return']:.2f}%")
        print(f"  Symboles: {', '.join(run['symbols'])}")
    
    # Stats globales
    print("\n" + "="*70)
    stats = storage.get_statistics()
    print(f"📊 Total runs: {stats['total_runs']}")
    print(f"🏆 Best Sharpe: {stats['best_sharpe']:.2f}")
    print(f"💰 Best Return: {stats['best_return']:.2f}%")


def main():
    """Fonction principale"""
    
    print_banner()
    
    print("\n🎯 QUE VOULEZ-VOUS FAIRE ?")
    print("="*70)
    print("  1. Lancer une nouvelle optimisation")
    print("  2. Voir l'historique des optimisations")
    print("  3. Quitter")
    
    choice = input("\nVotre choix (1-3) [1]: ").strip() or '1'
    
    if choice == '2':
        view_history()
        return 0
    
    if choice == '3':
        print("\n👋 Au revoir !")
        return 0
    
    # Workflow d'optimisation
    try:
        # Étape 1: Choisir la stratégie
        strategy_name, strategy_class = choose_strategy()
        
        # Étape 2: Choisir le preset (avec adaptation automatique)
        # 🔥 MODIFICATION : Passer strategy_name
        preset_name, config = choose_preset(strategy_name=strategy_name)
        
        # Étape 3: Choisir le type d'optimisation
        opt_type = choose_optimization_type()
        
        # Étape 4: Personnaliser (optionnel)
        config = customize_config(config, strategy_name)
        if config is None:
            print("\n❌ Configuration annulée")
            return 1
        
        # 🔥 NOUVELLE VALIDATION
        config_manager = OptimizationConfig()
        is_valid, warnings = config_manager.validate_strategy_params(
            strategy_class,
            config.get('param_grid', {})
        )
        
        if warnings:
            print("\n⚠️  AVERTISSEMENTS:")
            for warning in warnings:
                print(f"  • {warning}")
            
            confirm = input("\nContinuer malgré les avertissements ? (o/n) [n]: ").strip().lower()
            if confirm != 'o':
                print("\n❌ Optimisation annulée")
                return 1
        
        # Étape 5: Confirmation finale
        print("\n" + "="*70)
        print("📋 RÉCAPITULATIF")
        print("="*70)
        print(f"Stratégie: {strategy_name}")
        print(f"Config: {preset_name}")
        print(f"Type: {opt_type}")
        print(f"Symboles: {', '.join(config['symbols'])}")
        print(f"Période: {config['period']['start']} → {config['period']['end']}")
        
        # Afficher les paramètres qui seront optimisés
        param_grid = config.get('param_grid', {})
        print(f"\nParamètres à optimiser:")
        for param, values in param_grid.items():
            print(f"  • {param}: {values}")
        
        from itertools import product
        total_combos = 1
        for values in param_grid.values():
            total_combos *= len(values)
        print(f"Combinaisons: {total_combos}")
        
        confirm = input("\n▶ Lancer l'optimisation ? (o/n) [o]: ").strip().lower() or 'o'
        
        if confirm != 'o':
            print("\n❌ Optimisation annulée")
            return 1
        
        # Étape 6: Lancer l'optimisation
        results = run_optimization(strategy_class, config, opt_type)
        
        # Étape 7: Afficher les résultats
        if results:
            display_results(results)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Optimisation interrompue par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)