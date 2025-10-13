#!/usr/bin/env python3
"""
Optimisation avec visualisation des résultats
Crée des graphiques pour analyser l'impact des paramètres
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from scripts.optimize_strategy import StrategyOptimizer
from strategies.marsi import MaSuperStrategie
from config import settings


def create_heatmap(results_df, param1, param2, metric="sharpe"):
    """Crée une heatmap pour 2 paramètres"""

    # Créer une table pivot
    pivot = results_df.pivot_table(
        values=metric, index=param1, columns=param2, aggfunc="mean"
    )

    # Créer la heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn", center=0)
    plt.title(f"Impact de {param1} et {param2} sur {metric.upper()}")
    plt.tight_layout()

    # Sauvegarder
    filename = settings.RESULTS_DIR / f"heatmap_{param1}_{param2}_{metric}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"✓ Heatmap sauvegardée: {filename}")
    plt.close()


def create_param_impact_chart(results_df, param, metric="sharpe"):
    """Crée un graphique de l'impact d'un paramètre"""

    # Grouper par paramètre
    grouped = results_df.groupby(param)[metric].agg(["mean", "std", "min", "max"])

    # Créer le graphique
    fig, ax = plt.subplots(figsize=(12, 6))

    x = grouped.index
    y_mean = grouped["mean"]
    y_std = grouped["std"]

    ax.plot(x, y_mean, "o-", linewidth=2, markersize=8, label="Moyenne")
    ax.fill_between(x, y_mean - y_std, y_mean + y_std, alpha=0.3, label="±1 std")

    ax.set_xlabel(param)
    ax.set_ylabel(metric.upper())
    ax.set_title(f"Impact de {param} sur {metric.upper()}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Sauvegarder
    filename = settings.RESULTS_DIR / f"impact_{param}_{metric}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"✓ Graphique sauvegardé: {filename}")
    plt.close()


def create_3d_surface(results_df, param1, param2, metric="sharpe"):
    """Crée une surface 3D"""
    from mpl_toolkits.mplot3d import Axes3D

    # Préparer les données
    pivot = results_df.pivot_table(values=metric, index=param1, columns=param2)

    X, Y = np.meshgrid(pivot.columns, pivot.index)
    Z = pivot.values

    # Créer le graphique 3D
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8)

    ax.set_xlabel(param2)
    ax.set_ylabel(param1)
    ax.set_zlabel(metric.upper())
    ax.set_title(f"Surface 3D: {param1} vs {param2} → {metric.upper()}")

    fig.colorbar(surf, shrink=0.5)

    # Sauvegarder
    filename = settings.RESULTS_DIR / f"surface3d_{param1}_{param2}_{metric}.png"
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    print(f"✓ Surface 3D sauvegardée: {filename}")
    plt.close()


def optimize_with_visualization():
    """Optimisation complète avec visualisations"""

    print(
        """
╔═══════════════════════════════════════════════════════════════════════╗
║        🎨 OPTIMISATION AVEC VISUALISATION 🎨                         ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    )

    # Configuration
    from strategies.marsi import MaSuperStrategie
    from strategies.moving_average import MovingAverageStrategy

    optimizer = StrategyOptimizer(
        strategy_class=MovingAverageStrategy,
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"],
        start_date="2022-01-01",
        end_date="2024-01-01",
        capital=100000,
    )

    # Définir la grille de paramètres à tester
    param_grid = {
        # 'ma_period': [10, 20, 30, 50],
        # 'rsi_period': [7, 14, 21],
        # 'stop_loss_pct': [0.015, 0.02, 0.025],
        "fast_period": [5 * i for i in range(1, 11)],
        "slow_period": [50 * i for i in range(1, 6)],
    }

    print(f"\n🔬 Lancement de l'optimisation...")
    from itertools import product

    total = 1
    for v in param_grid.values():
        total *= len(v)
    print(f"   Total: {total} combinaisons\n")

    # Optimiser
    best_params = optimizer.optimize(param_grid)

    # Charger les résultats
    results_df = pd.DataFrame(optimizer.results)

    print("\n" + "=" * 70)
    print("📊 GÉNÉRATION DES VISUALISATIONS")
    print("=" * 70 + "\n")

    # 1. Heatmaps pour toutes les paires de paramètres
    param_names = list(param_grid.keys())

    for i, param1 in enumerate(param_names):
        for param2 in param_names[i + 1 :]:
            print(f"Création heatmap: {param1} vs {param2}...")
            create_heatmap(results_df, param1, param2, "sharpe")
            create_heatmap(results_df, param1, param2, "return")

    # 2. Graphiques d'impact individuel
    for param in param_names:
        print(f"Création graphique impact: {param}...")
        create_param_impact_chart(results_df, param, "sharpe")
        create_param_impact_chart(results_df, param, "return")

    # 3. Surface 3D (si numpy disponible)
    try:
        import numpy as np

        if len(param_names) >= 2:
            print(f"Création surface 3D: {param_names[0]} vs {param_names[1]}...")
            create_3d_surface(results_df, param_names[0], param_names[1], "sharpe")
    except ImportError:
        print("⚠️  Numpy non disponible pour la surface 3D")

    # 4. Distribution des métriques
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    results_df["sharpe"].hist(ax=axes[0, 0], bins=20, edgecolor="black")
    axes[0, 0].set_title("Distribution Sharpe Ratio")
    axes[0, 0].set_xlabel("Sharpe Ratio")

    results_df["return"].hist(ax=axes[0, 1], bins=20, edgecolor="black", color="green")
    axes[0, 1].set_title("Distribution Rendement")
    axes[0, 1].set_xlabel("Rendement (%)")

    results_df["drawdown"].hist(ax=axes[1, 0], bins=20, edgecolor="black", color="red")
    axes[1, 0].set_title("Distribution Max Drawdown")
    axes[1, 0].set_xlabel("Max Drawdown (%)")

    results_df["win_rate"].hist(ax=axes[1, 1], bins=20, edgecolor="black", color="blue")
    axes[1, 1].set_title("Distribution Win Rate")
    axes[1, 1].set_xlabel("Win Rate (%)")

    plt.tight_layout()
    dist_file = settings.RESULTS_DIR / "distributions.png"
    plt.savefig(dist_file, dpi=300, bbox_inches="tight")
    print(f"✓ Distributions sauvegardées: {dist_file}")
    plt.close()

    print("\n" + "=" * 70)
    print("✅ VISUALISATIONS TERMINÉES")
    print("=" * 70)
    print(f"\n📁 Consultez le dossier: {settings.RESULTS_DIR}")
    print("\nFichiers créés:")
    for file in sorted(settings.RESULTS_DIR.glob("*.png")):
        print(f"   • {file.name}")

    return best_params


if __name__ == "__main__":
    try:
        import numpy as np

        optimize_with_visualization()
    except ImportError as e:
        print(f"❌ Dépendance manquante: {e}")
        print("\nInstallez:")
        print("  pip install numpy matplotlib seaborn")
