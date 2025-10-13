#!/usr/bin/env python3
"""
Diagnostic RSI Strategy - Pourquoi Si Peu de Trades?
====================================================
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt

from data.data_handler import DataHandler
from data.data_fetcher import create_data_feed
from monitoring.logger import setup_logger

logger = setup_logger("rsi_diagnostic")


class RSIDiagnostic(bt.Strategy):
    """Stratégie RSI avec diagnostic détaillé"""

    params = (
        ("rsi_period", 10),
        ("rsi_oversold", 20),
        ("rsi_overbought", 80),
        ("printlog", False),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.datas[0].close, period=self.params.rsi_period)

        # Compteurs
        self.total_days = 0
        self.rsi_ready_days = 0
        self.oversold_days = 0
        self.overbought_days = 0
        self.buy_signals = 0
        self.sell_signals = 0
        self.actual_trades = 0

        # Historique RSI
        self.rsi_history = []

    def next(self):
        self.total_days += 1

        if len(self.rsi) < self.params.rsi_period:
            return

        self.rsi_ready_days += 1
        rsi_val = self.rsi[0]
        self.rsi_history.append(rsi_val)

        # Vérifier les conditions
        if rsi_val < self.params.rsi_oversold:
            self.oversold_days += 1
            if not self.position:
                self.buy_signals += 1
                if self.params.printlog:
                    print(
                        f"{self.datas[0].datetime.date(0)} | 🟢 ACHAT | RSI={rsi_val:.1f} < {self.params.rsi_oversold}"
                    )

        if rsi_val > self.params.rsi_overbought:
            self.overbought_days += 1
            if self.position:
                self.sell_signals += 1
                if self.params.printlog:
                    print(
                        f"{self.datas[0].datetime.date(0)} | 🔴 VENTE | RSI={rsi_val:.1f} > {self.params.rsi_overbought}"
                    )

    def stop(self):
        """Rapport de diagnostic"""
        print("\n" + "=" * 80)
        print("📊 DIAGNOSTIC STRATÉGIE RSI")
        print("=" * 80)

        print(f"\n📅 Période:")
        print(f"   Jours totaux: {self.total_days}")
        print(f"   Jours RSI calculable: {self.rsi_ready_days}")

        if self.rsi_ready_days > 0:
            print(f"\n📈 Distribution RSI:")
            rsi_array = pd.Series(self.rsi_history)
            print(f"   Moyenne: {rsi_array.mean():.1f}")
            print(f"   Min: {rsi_array.min():.1f}")
            print(f"   Max: {rsi_array.max():.1f}")
            print(f"   Médiane: {rsi_array.median():.1f}")

            print(
                f"\n🎯 Signaux (Paramètres: oversold={self.params.rsi_oversold}, overbought={self.params.rsi_overbought}):"
            )
            print(
                f"   Jours RSI < {self.params.rsi_oversold}: {self.oversold_days} ({self.oversold_days/self.rsi_ready_days*100:.1f}%)"
            )
            print(
                f"   Jours RSI > {self.params.rsi_overbought}: {self.overbought_days} ({self.overbought_days/self.rsi_ready_days*100:.1f}%)"
            )
            print(f"   Signaux d'achat générés: {self.buy_signals}")
            print(f"   Signaux de vente générés: {self.sell_signals}")

            print(f"\n💡 ANALYSE:")
            if self.buy_signals < 5:
                print(
                    f"   ❌ PROBLÈME: Seuil RSI oversold ({self.params.rsi_oversold}) trop BAS"
                )
                print(
                    f"   → RSI descend rarement en-dessous de {self.params.rsi_oversold}"
                )
                print(
                    f"   → Seulement {self.oversold_days} jours sur {self.rsi_ready_days} ({self.oversold_days/self.rsi_ready_days*100:.1f}%)"
                )
                print()
                print(f"   💊 SOLUTION:")
                print(f"      • Augmenter rsi_oversold à 30-35")
                print(
                    f"      • Cela générera ~{int(self.rsi_ready_days * 0.1)} signaux (10% des jours)"
                )

            if self.sell_signals < 5:
                print(
                    f"   ❌ PROBLÈME: Seuil RSI overbought ({self.params.rsi_overbought}) trop HAUT"
                )
                print(
                    f"   → RSI monte rarement au-dessus de {self.params.rsi_overbought}"
                )
                print(
                    f"   → Seulement {self.overbought_days} jours sur {self.rsi_ready_days} ({self.overbought_days/self.rsi_ready_days*100:.1f}%)"
                )
                print()
                print(f"   💊 SOLUTION:")
                print(f"      • Réduire rsi_overbought à 65-70")
                print(
                    f"      • Cela générera ~{int(self.rsi_ready_days * 0.1)} signaux (10% des jours)"
                )

            # Distribution détaillée
            print(f"\n📊 Distribution détaillée RSI:")
            bins = [0, 20, 30, 40, 50, 60, 70, 80, 100]
            hist, _ = pd.cut(rsi_array, bins=bins, retbins=True)
            counts = hist.value_counts().sort_index()

            for interval, count in counts.items():
                pct = count / len(rsi_array) * 100
                bar = "█" * int(pct / 2)
                print(f"   {interval}: {count:4d} ({pct:5.1f}%) {bar}")

        print("\n" + "=" * 80)

        # Recommandations
        print("\n🔧 RECOMMANDATIONS YAML:")
        print("\nparam_grid:")
        print("  rsi_oversold:")
        print("    type: 'int'")
        print("    low: 25      # ⬆️ Plus haut (au lieu de 20)")
        print("    high: 40     # Zone plus réaliste")
        print("    step: 5")
        print()
        print("  rsi_overbought:")
        print("    type: 'int'")
        print("    low: 60")
        print("    high: 75     # ⬇️ Plus bas (au lieu de 80-90)")
        print("    step: 5")
        print("\n" + "=" * 80 + "\n")


def analyze_rsi_thresholds(symbol="AAPL", start="2021-01-01", end="2025-01-01"):
    """
    Analyse l'impact de différents seuils RSI
    """
    print("=" * 80)
    print("🧪 ANALYSE COMPARATIVE DES SEUILS RSI")
    print("=" * 80)

    configs = [
        {"name": "Actuel (20/80)", "oversold": 20, "overbought": 80},
        {"name": "Standard (30/70)", "oversold": 30, "overbought": 70},
        {"name": "Modéré (35/65)", "oversold": 35, "overbought": 65},
        {"name": "Agressif (40/60)", "oversold": 40, "overbought": 60},
    ]

    results = []

    for config in configs:
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)

        # Données
        data_handler = DataHandler()
        df = data_handler.fetch_data(symbol, start, end)
        data_feed = create_data_feed(df, name=symbol)
        cerebro.adddata(data_feed)

        # Stratégie
        cerebro.addstrategy(
            RSIDiagnostic,
            rsi_period=14,
            rsi_oversold=config["oversold"],
            rsi_overbought=config["overbought"],
            printlog=False,
        )

        # Analyseurs
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # Run
        start_val = cerebro.broker.getvalue()
        strats = cerebro.run()
        end_val = cerebro.broker.getvalue()

        strat = strats[0]
        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", 0) or 0
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get("total", {}).get("total", 0)

        results.append(
            {
                "config": config["name"],
                "oversold": config["oversold"],
                "overbought": config["overbought"],
                "buy_signals": strat.buy_signals,
                "sell_signals": strat.sell_signals,
                "total_trades": total_trades,
                "sharpe": sharpe,
                "return": ((end_val - start_val) / start_val) * 100,
            }
        )

    # Afficher
    print(
        f"\n{'Config':<20} {'Buy':<6} {'Sell':<6} {'Trades':<8} {'Sharpe':<8} {'Return':<10} {'Évaluation'}"
    )
    print("-" * 90)

    for r in results:
        if r["total_trades"] == 0:
            eval_str = "❌ Aucun"
        elif r["total_trades"] < 5:
            eval_str = "⚠️  Trop peu"
        elif r["total_trades"] < 15:
            eval_str = "✓ OK"
        else:
            eval_str = "✅ Bon"

        print(
            f"{r['config']:<20} {r['buy_signals']:<6} {r['sell_signals']:<6} "
            f"{r['total_trades']:<8} {r['sharpe']:<8.2f} {r['return']:<10.1f}% {eval_str}"
        )

    print("\n" + "=" * 80)

    # Meilleure config
    best = max(results, key=lambda x: x["sharpe"])
    print(f"\n🏆 MEILLEURE CONFIGURATION:")
    print(f"   {best['config']}")
    print(f"   RSI oversold: {best['oversold']}")
    print(f"   RSI overbought: {best['overbought']}")
    print(f"   Trades: {best['total_trades']}")
    print(f"   Sharpe: {best['sharpe']:.2f}")
    print(f"   Return: {best['return']:.1f}%")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diagnostic RSI Strategy")
    parser.add_argument("--symbol", default="AAPL", help="Symbole")
    parser.add_argument(
        "--compare", action="store_true", help="Comparer plusieurs configs"
    )

    args = parser.parse_args()

    if args.compare:
        analyze_rsi_thresholds(args.symbol)
    else:
        # Diagnostic simple
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(100000)

        data_handler = DataHandler()
        df = data_handler.fetch_data(args.symbol, "2021-01-01", "2025-01-01")
        data_feed = create_data_feed(df, name=args.symbol)
        cerebro.adddata(data_feed)

        cerebro.addstrategy(
            RSIDiagnostic,
            rsi_period=10,
            rsi_oversold=20,
            rsi_overbought=80,
            printlog=True,
        )

        cerebro.run()
