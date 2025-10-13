#!/usr/bin/env python3
"""
Optimisation personnalisée pour MaSuperStrategie
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.optimize_strategy import StrategyOptimizer
from strategies.marsi import MaSuperStrategie

def optimize_my_strategy():
    """Optimise MaSuperStrategie avec configuration avancée"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║          🔬 OPTIMISATION DE MA SUPER STRATÉGIE 🔬                    ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    print("\n📋 CONFIGURATION")
    print("="*70)
    
    # Choix du symbole
    print("\nSymboles disponibles:")
    print("  1. AAPL (Apple)")
    print("  2. MSFT (Microsoft)")
    print("  3. GOOGL (Google)")
    print("  4. TSLA (Tesla)")
    print("  5. SPY (S&P 500 ETF)")
    print("  6. Multi-symboles (AAPL+MSFT)")
    
    choice = input("\nVotre choix (1-6) [1]: ").strip() or '1'
    
    symbols_map = {
        '1': ['AAPL'],
        '2': ['MSFT'],
        '3': ['GOOGL'],
        '4': ['TSLA'],
        '5': ['SPY'],
        '6': ['AAPL', 'MSFT']
    }
    
    symbols = symbols_map.get(choice, ['AAPL'])
    
    # Période
    print("\nPériode d'optimisation:")
    print("  1. Court terme (1 an) - Rapide")
    print("  2. Moyen terme (2 ans) - Recommandé")
    print("  3. Long terme (3 ans) - Robuste")
    print("  4. Très long terme (5 ans) - Très robuste")
    
    period_choice = input("\nVotre choix (1-4) [2]: ").strip() or '2'
    
    periods = {
        '1': ('2023-01-01', '2024-01-01'),
        '2': ('2022-01-01', '2024-01-01'),
        '3': ('2021-01-01', '2024-01-01'),
        '4': ('2019-01-01', '2024-01-01')
    }
    
    start_date, end_date = periods.get(period_choice, ('2022-01-01', '2024-01-01'))
    
    # Type d'optimisation
    print("\nType d'optimisation:")
    print("  1. Rapide (peu de combinaisons)")
    print("  2. Standard (équilibrée)")
    print("  3. Complète (toutes les combinaisons)")
    print("  4. Personnalisée")
    
    opt_choice = input("\nVotre choix (1-4) [2]: ").strip() or '2'
    
    # Grilles de paramètres
    if opt_choice == '1':
        param_grid = {
            'ma_period': [20, 50],
            'rsi_period': [14],
            'stop_loss_pct': [0.02],
        }
    elif opt_choice == '2':
        param_grid = {
            'ma_period': [10, 20, 30, 50],
            'rsi_period': [7, 14, 21],
            'stop_loss_pct': [0.015, 0.02, 0.025],
            'trailing_stop_pct': [0.025, 0.03, 0.035],
        }
    elif opt_choice == '3':
        param_grid = {
            'ma_period': [10, 15, 20, 25, 30, 40, 50],
            'rsi_period': [7, 10, 14, 21, 28],
            'stop_loss_pct': [0.01, 0.015, 0.02, 0.025, 0.03],
            'trailing_stop_pct': [0.02, 0.025, 0.03, 0.035, 0.04],
            'trailing_activation_pct': [0.015, 0.02, 0.025],
        }
    else:  # Personnalisée
        param_grid = {
            'ma_period': [int(x) for x in input("Périodes MA (ex: 10,20,30): ").split(',')],
            'rsi_period': [int(x) for x in input("Périodes RSI (ex: 7,14,21): ").split(',')],
            'stop_loss_pct': [float(x)/100 for x in input("Stop Loss % (ex: 1.5,2,2.5): ").split(',')],
        }
    
    # Afficher le résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE L'OPTIMISATION")
    print("="*70)
    print(f"Symboles: {', '.join(symbols)}")
    print(f"Période: {start_date} → {end_date}")
    print(f"Paramètres à tester: {param_grid}")
    
    from itertools import product
    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    print(f"Total combinaisons: {total_combos}")
    
    # Confirmation
    confirm = input("\n▶ Lancer l'optimisation ? (o/n) [o]: ").strip().lower() or 'o'
    
    if confirm != 'o':
        print("Optimisation annulée")
        return
    
    # Lancer l'optimisation
    optimizer = StrategyOptimizer(
        strategy_class=MaSuperStrategie,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        capital=100000
    )
    
    best_params = optimizer.optimize(param_grid)
    
    if best_params:
        print("\n" + "="*70)
        print("🎯 COMMENT UTILISER CES PARAMÈTRES")
        print("="*70)
        print("\n1. Ouvrir votre stratégie:")
        print("   notepad strategies\\masuperstrategie.py")
        print("\n2. Modifier les params:")
        print("   params = (")
        for key, value in best_params.items():
            if key not in ['sharpe', 'return', 'drawdown', 'trades', 'win_rate']:
                print(f"       ('{key}', {value}),")
        print("   )")
        print("\n3. Sauvegarder et tester:")
        print(f"   python main.py --strategy MaSuperStrategie --symbols {symbols[0]}")


if __name__ == "__main__":
    optimize_my_strategy()