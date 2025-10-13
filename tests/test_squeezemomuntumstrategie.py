#!/usr/bin/env python3
"""
Script de test rapide pour Squeeze Momentum Strategy

Usage:
    python test_squeeze_momentum.py
    python test_squeeze_momentum.py --symbols TSLA,NVDA --start 2023-01-01
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import argparse
from datetime import datetime
import backtrader as bt
from strategies.squeezemomentumstrategy import SqueezeMomentumStrategy
from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger

logger = setup_logger("test_squeeze")


def parse_args():
    parser = argparse.ArgumentParser(description="Test Squeeze Momentum Strategy")

    parser.add_argument(
        "--symbols",
        type=str,
        default="TSLA",
        help="Symboles séparés par des virgules (ex: AAPL,MSFT,TSLA)",
    )

    parser.add_argument(
        "--start",
        type=str,
        default="2015-01-01",
        help="Date de début (format: YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date de fin (format: YYYY-MM-DD)",
    )

    parser.add_argument("--cash", type=float, default=100000, help="Capital initial")

    parser.add_argument(
        "--commission",
        type=float,
        default=0.001,
        help="Commission par trade (0.001 = 0.1%%)",
    )

    # Paramètres de la stratégie
    parser.add_argument(
        "--min-volume", type=int, default=1000000, help="Volume moyen minimum requis"
    )

    parser.add_argument(
        "--min-squeeze-days",
        type=int,
        default=3,
        help="Nombre minimum de jours de squeeze",
    )

    parser.add_argument(
        "--target-mult",
        type=float,
        default=2.0,
        help="Multiplicateur pour le target (ex: 2.0 = squeeze height × 2)",
    )

    return parser.parse_args()


def run_backtest(args):
    """Exécute le backtest"""

    print("\n" + "=" * 80)
    print("🚀 SQUEEZE MOMENTUM STRATEGY - BACKTEST")
    print("=" * 80)

    # Créer le moteur Cerebro
    cerebro = bt.Cerebro()

    # Ajouter la stratégie avec paramètres
    cerebro.addstrategy(
        SqueezeMomentumStrategy,
        min_volume_avg=args.min_volume,
        min_squeeze_days=args.min_squeeze_days,
        target_multiplier=args.target_mult,
        printlog=True,
    )

    # Charger les données
    symbols = [s.strip() for s in args.symbols.split(",")]
    data_handler = DataHandler()

    print(f"\n📊 Chargement des données...")
    print(f"   Symboles: {', '.join(symbols)}")
    print(f"   Période: {args.start} → {args.end}")

    loaded_count = 0
    for symbol in symbols:
        try:
            df = data_handler.fetch_data(
                symbol=symbol, start_date=args.start, end_date=args.end, interval="1d"
            )

            if df is not None and len(df) > 0:
                # Utiliser create_data_feed du projet
                data = create_data_feed(df, name=symbol)
                cerebro.adddata(data, name=symbol)
                print(f"   ✅ {symbol}: {len(df)} barres chargées")
                loaded_count += 1
            else:
                print(f"   ❌ {symbol}: Aucune donnée disponible")

        except Exception as e:
            print(f"   ❌ {symbol}: Erreur - {e}")

    # Vérifier qu'au moins une donnée a été chargée
    if loaded_count == 0:
        print(f"\n❌ ERREUR: Aucune donnée n'a pu être chargée!")
        print("   Suggestions:")
        print("   - Vérifiez votre connexion Internet")
        print("   - Vérifiez que les symboles sont corrects")
        print("   - Essayez avec une période plus récente")
        return None, None

    # Configuration du broker
    cerebro.broker.setcash(args.cash)
    cerebro.broker.setcommission(commission=args.commission)

    # Ajouter les analyseurs
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    # Afficher paramètres
    print(f"\n⚙️  Configuration:")
    print(f"   Capital initial:      ${args.cash:,.2f}")
    print(f"   Commission:           {args.commission*100:.2f}%")
    print(f"   Volume minimum:       {args.min_volume:,}")
    print(f"   Jours squeeze min:    {args.min_squeeze_days}")
    print(f"   Target multiplier:    {args.target_mult}×")
    print(f"   Risque par trade:     2.0%")

    # Valeur initiale
    start_value = cerebro.broker.getvalue()
    print(f"\n💰 Valeur initiale du portefeuille: ${start_value:,.2f}")

    # Exécuter le backtest
    print("\n" + "=" * 80)
    print("📈 DÉMARRAGE DU BACKTEST...")
    print("=" * 80 + "\n")

    results = cerebro.run()

    # Vérifier que le backtest a bien retourné des résultats
    if not results or len(results) == 0:
        print("\n❌ ERREUR: Le backtest n'a retourné aucun résultat!")
        print("   Cela peut arriver si:")
        print("   - Aucune donnée n'a été chargée")
        print("   - La stratégie n'a pas pu être initialisée")
        return None, None

    strat = results[0]

    # Valeur finale
    end_value = cerebro.broker.getvalue()
    pnl = end_value - start_value
    pnl_pct = (pnl / start_value) * 100

    # Afficher les résultats
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS DU BACKTEST")
    print("=" * 80)

    print(f"\n💰 Performance Globale:")
    print(f"   Valeur finale:     ${end_value:,.2f}")
    print(f"   P&L:               ${pnl:,.2f} ({pnl_pct:+.2f}%)")

    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe.get_analysis()
    if sharpe.get("sharperatio"):
        print(f"   Sharpe Ratio:      {sharpe['sharperatio']:.3f}")

    # Drawdown
    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f"\n📉 Drawdown:")
    print(f"   Max Drawdown:      {drawdown['max']['drawdown']:.2f}%")
    print(f"   Max Drawdown $:    ${drawdown['max']['moneydown']:,.2f}")

    # Returns
    returns = strat.analyzers.returns.get_analysis()
    if returns.get("rnorm100"):
        print(f"\n📈 Returns:")
        print(f"   Return annualisé:  {returns['rnorm100']:.2f}%")

    # Trades
    trades = strat.analyzers.trades.get_analysis()
    total_trades = trades.get("total", {}).get("total", 0)

    if total_trades > 0:
        won = trades.get("won", {}).get("total", 0)
        lost = trades.get("lost", {}).get("total", 0)
        win_rate = (won / total_trades * 100) if total_trades > 0 else 0

        print(f"\n📊 Statistiques des Trades:")
        print(f"   Total trades:      {total_trades}")
        print(f"   Gagnants:          {won} ({win_rate:.1f}%)")
        print(f"   Perdants:          {lost} ({100-win_rate:.1f}%)")

        if won > 0:
            avg_win = trades["won"]["pnl"]["average"]
            print(f"   Gain moyen:        ${avg_win:,.2f}")

        if lost > 0:
            avg_loss = trades["lost"]["pnl"]["average"]
            print(f"   Perte moyenne:     ${avg_loss:,.2f}")
    else:
        print(f"\n⚠️  Aucun trade exécuté pendant la période")

    print("\n" + "=" * 80)

    # Option: Sauvegarder un graphique
    try:
        print("\n📊 Génération du graphique...")
        cerebro.plot(style="candlestick", barup="green", bardown="red")
    except Exception as e:
        print(f"⚠️  Impossible de générer le graphique: {e}")

    return cerebro, results


def main():
    args = parse_args()

    try:
        cerebro, results = run_backtest(args)

        # Vérifier si le backtest a pu s'exécuter
        if cerebro is None or results is None:
            print("\n❌ Le backtest n'a pas pu être exécuté.\n")
            return 1

        print("\n✅ Backtest terminé avec succès!\n")

    except Exception as e:
        logger.error(f"Erreur lors du backtest: {e}", exc_info=True)
        print(f"\n❌ Erreur: {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
