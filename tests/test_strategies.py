#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
    TESTEUR & COMPARATEUR DE STRATÉGIES
═══════════════════════════════════════════════════════════════════════════════

Script pour tester et comparer plusieurs stratégies simultanément

Utilisation:
    python scripts/test_strategies.py
    python scripts/test_strategies.py --symbols AAPL MSFT --quick

Sauvegardez dans: scripts/test_strategies.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import pandas as pd
from datetime import datetime
from tabulate import tabulate

from config import settings
from backtesting.backtest_engine import BacktestEngine
from monitoring.logger import setup_logger

logger = setup_logger("strategy_tester")


# Liste des stratégies à tester
AVAILABLE_STRATEGIES = [
    "MovingAverage",
    "RSI",
    "MACrossoverAdvanced",
    "RSITrailingStop",
    "BreakoutATRStop",
    "MomentumMultipleStops",
    "MaSuperStrategie",
]


def test_single_strategy(strategy_name, symbols, start_date, end_date, capital):
    """Teste une seule stratégie"""

    logger.info(f"\n{'='*70}")
    logger.info(f"Test de {strategy_name}")
    logger.info(f"{'='*70}")

    try:
        engine = BacktestEngine(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital,
            verbose=False,
        )

        results = engine.run()

        if results:
            return {
                "strategy": strategy_name,
                "symbols": ", ".join(symbols),
                "final_value": results["final_value"],
                "total_return": results["total_return"],
                "sharpe_ratio": results["sharpe_ratio"],
                "max_drawdown": results["max_drawdown"],
                "total_trades": results["total_trades"],
                "win_rate": results["win_rate"],
                "avg_win": results["avg_win"],
                "avg_loss": results["avg_loss"],
            }
        else:
            logger.error(f"Aucun résultat pour {strategy_name}")
            return None

    except Exception as e:
        logger.error(f"Erreur avec {strategy_name}: {e}")
        return None


def compare_strategies(strategies, symbols, start_date, end_date, capital):
    """Compare plusieurs stratégies"""

    logger.info(f"\n{'═'*70}")
    logger.info("COMPARAISON DE STRATÉGIES")
    logger.info(f"{'═'*70}")
    logger.info(f"Symboles: {', '.join(symbols)}")
    logger.info(f"Période: {start_date} → {end_date}")
    logger.info(f"Capital: ${capital:,.2f}")
    logger.info(f"{'═'*70}\n")

    results = []

    for strategy_name in strategies:
        result = test_single_strategy(
            strategy_name, symbols, start_date, end_date, capital
        )
        if result:
            results.append(result)

    return results


def display_comparison_table(results):
    """Affiche un tableau de comparaison"""

    if not results:
        logger.error("Aucun résultat à afficher")
        return

    # Créer le DataFrame
    df = pd.DataFrame(results)

    # Formater les colonnes
    df["final_value"] = df["final_value"].apply(lambda x: f"${x:,.2f}")
    df["total_return"] = df["total_return"].apply(lambda x: f"{x:.2f}%")
    df["sharpe_ratio"] = df["sharpe_ratio"].apply(lambda x: f"{x:.2f}")
    df["max_drawdown"] = df["max_drawdown"].apply(lambda x: f"{x:.2f}%")
    df["win_rate"] = df["win_rate"].apply(lambda x: f"{x:.2f}%")
    df["avg_win"] = df["avg_win"].apply(lambda x: f"${x:.2f}")
    df["avg_loss"] = df["avg_loss"].apply(lambda x: f"${x:.2f}")

    # Renommer les colonnes pour l'affichage
    df.columns = [
        "Stratégie",
        "Symboles",
        "Capital Final",
        "Rendement",
        "Sharpe",
        "Max DD",
        "Trades",
        "Win Rate",
        "Gain Moy",
        "Perte Moy",
    ]

    # Afficher le tableau
    print("\n" + "=" * 140)
    print("TABLEAU COMPARATIF DES STRATÉGIES")
    print("=" * 140)
    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
    print("=" * 140)


def identify_best_strategy(results):
    """Identifie la meilleure stratégie"""

    if not results:
        return

    # Trouver la meilleure selon différents critères
    best_return = max(results, key=lambda x: x["total_return"])
    best_sharpe = max(results, key=lambda x: x["sharpe_ratio"])
    best_winrate = max(results, key=lambda x: x["win_rate"])
    min_drawdown = min(results, key=lambda x: x["max_drawdown"])

    print("\n" + "=" * 70)
    print("🏆 MEILLEURES STRATÉGIES PAR CRITÈRE")
    print("=" * 70)
    print(
        f"📈 Meilleur Rendement:     {best_return['strategy']:<25} {best_return['total_return']:.2f}%"
    )
    print(
        f"⭐ Meilleur Sharpe Ratio:  {best_sharpe['strategy']:<25} {best_sharpe['sharpe_ratio']:.2f}"
    )
    print(
        f"🎯 Meilleur Win Rate:      {best_winrate['strategy']:<25} {best_winrate['win_rate']:.2f}%"
    )
    print(
        f"🛡️  Plus Faible Drawdown:  {min_drawdown['strategy']:<25} {min_drawdown['max_drawdown']:.2f}%"
    )

    # Score composite (pondéré)
    for result in results:
        score = (
            (result["total_return"] / 100) * 0.3
            + result["sharpe_ratio"] * 0.3
            + (result["win_rate"] / 100) * 0.2
            + (1 - abs(result["max_drawdown"]) / 100) * 0.2
        )
        result["score"] = score

    best_overall = max(results, key=lambda x: x["score"])

    print(f"\n🥇 MEILLEURE STRATÉGIE GLOBALE (Score Composite)")
    print(f"   → {best_overall['strategy']}")
    print(f"   Score: {best_overall['score']:.3f}")
    print("=" * 70)


def generate_report(results, symbols, start_date, end_date):
    """Génère un rapport détaillé"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = settings.RESULTS_DIR / f"comparison_{timestamp}.txt"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT DE COMPARAISON DE STRATÉGIES\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Date du rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Symboles testés: {', '.join(symbols)}\n")
        f.write(f"Période: {start_date} → {end_date}\n\n")

        f.write("=" * 80 + "\n")
        f.write("RÉSULTATS PAR STRATÉGIE\n")
        f.write("=" * 80 + "\n\n")

        for result in results:
            f.write(f"\n{result['strategy']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Capital Final:     ${result['final_value']:>15,.2f}\n")
            f.write(f"Rendement Total:   {result['total_return']:>15.2f}%\n")
            f.write(f"Sharpe Ratio:      {result['sharpe_ratio']:>15.2f}\n")
            f.write(f"Max Drawdown:      {result['max_drawdown']:>15.2f}%\n")
            f.write(f"Nombre de Trades:  {result['total_trades']:>15}\n")
            f.write(f"Taux de Réussite:  {result['win_rate']:>15.2f}%\n")
            f.write(f"Gain Moyen:        ${result['avg_win']:>15.2f}\n")
            f.write(f"Perte Moyenne:     ${result['avg_loss']:>15.2f}\n")

        f.write("\n" + "=" * 80 + "\n")

    logger.info(f"\n✅ Rapport sauvegardé: {report_file}")
    return report_file


def parse_arguments():
    """Parse les arguments"""
    parser = argparse.ArgumentParser(description="Testeur et comparateur de stratégies")

    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        default=AVAILABLE_STRATEGIES,
        help="Liste des stratégies à tester",
    )

    parser.add_argument(
        "--symbols", type=str, nargs="+", default=["AAPL"], help="Liste des symboles"
    )

    parser.add_argument(
        "--start-date", type=str, default="2022-01-01", help="Date de début"
    )

    parser.add_argument(
        "--end-date", type=str, default="2024-12-31", help="Date de fin"
    )

    parser.add_argument("--capital", type=float, default=100000, help="Capital initial")

    parser.add_argument(
        "--quick", action="store_true", help="Test rapide (période courte)"
    )

    parser.add_argument(
        "--save-report", action="store_true", help="Sauvegarder le rapport"
    )

    return parser.parse_args()


def main():
    """Fonction principale"""

    args = parse_arguments()

    # Mode quick: période réduite
    if args.quick:
        args.start_date = "2024-01-01"
        args.end_date = "2024-06-30"
        logger.info("🚀 Mode QUICK activé - période réduite")

    # Afficher le banner
    print(
        """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║           🧪 TESTEUR & COMPARATEUR DE STRATÉGIES 🧪                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    )

    # Comparer les stratégies
    results = compare_strategies(
        strategies=args.strategies,
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        capital=args.capital,
    )

    # Afficher les résultats
    if results:
        display_comparison_table(results)
        identify_best_strategy(results)

        # Sauvegarder le rapport
        if args.save_report:
            generate_report(results, args.symbols, args.start_date, args.end_date)
    else:
        logger.error("Aucun résultat à afficher")
        return 1

    print("\n✅ Comparaison terminée\n")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}", exc_info=True)
        sys.exit(1)
