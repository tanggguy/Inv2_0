#!/usr/bin/env python3
"""
Walk-Forward Optimization - VERSION CORRIGÉE
Gère les cas où aucun trade n'est effectué
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from scripts.optimize_strategy import StrategyOptimizer
from backtesting.backtest_engine import BacktestEngine
from strategies.marsi import MaSuperStrategie
from monitoring.logger import setup_logger

logger = setup_logger("walk_forward")


class WalkForwardOptimizer:
    """Optimisation Walk-Forward pour éviter l'overfitting"""

    def __init__(
        self,
        strategy_class,
        symbols,
        in_sample_months=12,
        out_sample_months=3,
        start_date="2020-01-01",
        end_date="2024-01-01",
    ):

        self.strategy_class = strategy_class
        self.symbols = symbols
        self.in_sample_months = in_sample_months
        self.out_sample_months = out_sample_months
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)

        self.periods = []
        self.results = []

    def generate_periods(self):
        """Génère les périodes In-Sample et Out-Sample"""

        current_date = self.start_date

        while (
            current_date
            + relativedelta(months=self.in_sample_months + self.out_sample_months)
            <= self.end_date
        ):

            # Période In-Sample
            in_start = current_date
            in_end = current_date + relativedelta(months=self.in_sample_months)

            # Période Out-Sample
            out_start = in_end
            out_end = out_start + relativedelta(months=self.out_sample_months)

            self.periods.append(
                {
                    "in_sample": (
                        in_start.strftime("%Y-%m-%d"),
                        in_end.strftime("%Y-%m-%d"),
                    ),
                    "out_sample": (
                        out_start.strftime("%Y-%m-%d"),
                        out_end.strftime("%Y-%m-%d"),
                    ),
                }
            )

            # Avancer
            current_date = out_start

        logger.info(f"✓ {len(self.periods)} périodes générées")
        return self.periods

    def run_walk_forward(self, param_grid):
        """Exécute le walk-forward complet"""

        print("\n" + "=" * 80)
        print("🚶 WALK-FORWARD OPTIMIZATION")
        print("=" * 80)
        print(f"In-Sample: {self.in_sample_months} mois")
        print(f"Out-Sample: {self.out_sample_months} mois")
        print(f"Périodes totales: {len(self.periods)}")
        print("=" * 80 + "\n")

        for i, period in enumerate(self.periods, 1):
            print(f"\n{'='*80}")
            print(f"PÉRIODE {i}/{len(self.periods)}")
            print(f"{'='*80}")

            in_start, in_end = period["in_sample"]
            out_start, out_end = period["out_sample"]

            print(f"📊 In-Sample:  {in_start} → {in_end}")
            print(f"📈 Out-Sample: {out_start} → {out_end}\n")

            # 1. Optimiser sur In-Sample
            print("🔬 Optimisation sur In-Sample...")
            optimizer = StrategyOptimizer(
                strategy_class=self.strategy_class,
                symbols=self.symbols,
                start_date=in_start,
                end_date=in_end,
                capital=100000,
            )

            best_params = optimizer.optimize(param_grid)

            if not best_params:
                logger.warning(f"Pas de résultats pour période {i} (In-Sample)")
                continue

            # Extraire les paramètres (sans les métriques)
            strategy_params = {
                k: v
                for k, v in best_params.items()
                if k not in ["sharpe", "return", "drawdown", "trades", "win_rate"]
            }

            # Valeurs par défaut si None
            in_sharpe = best_params.get("sharpe", 0) or 0
            in_return = best_params.get("return", 0) or 0

            print(f"\n✓ Meilleurs paramètres In-Sample: {strategy_params}")
            print(f"  Sharpe: {in_sharpe:.2f}")
            print(f"  Return: {in_return:.2f}%")

            # 2. Tester sur Out-Sample avec ces paramètres
            print(f"\n🧪 Test sur Out-Sample...")

            engine = BacktestEngine(
                strategy_name=self.strategy_class.__name__,
                symbols=self.symbols,
                start_date=out_start,
                end_date=out_end,
                initial_capital=100000,
                verbose=False,
            )

            out_results = engine.run()

            # ===== GESTION DES CAS PROBLÉMATIQUES =====
            if out_results:
                # Valeurs par défaut si None
                out_sharpe = out_results.get("sharpe_ratio") or 0
                out_return = out_results.get("total_return") or 0
                out_trades = out_results.get("total_trades", 0)

                print(f"✓ Résultats Out-Sample:")
                print(f"  Sharpe: {out_sharpe:.2f}")
                print(f"  Return: {out_return:.2f}%")
                print(f"  Trades: {out_trades}")

                # Vérifier si des trades ont été effectués
                if out_trades == 0:
                    print(f"  ⚠️  AUCUN TRADE - Période ignorée dans l'analyse")
                    logger.warning(f"Période {i}: Aucun trade en Out-Sample")
                    continue

                # Calculer la dégradation (gérer les None)
                degradation = in_sharpe - out_sharpe

                # Stocker les résultats
                self.results.append(
                    {
                        "period": i,
                        "in_sample_start": in_start,
                        "in_sample_end": in_end,
                        "out_sample_start": out_start,
                        "out_sample_end": out_end,
                        "params": strategy_params,
                        "in_sample_sharpe": in_sharpe,
                        "in_sample_return": in_return,
                        "out_sample_sharpe": out_sharpe,
                        "out_sample_return": out_return,
                        "out_sample_trades": out_trades,
                        "degradation": degradation,
                    }
                )
            else:
                logger.warning(f"Période {i}: Pas de résultats Out-Sample")
                print(f"  ⚠️  Pas de résultats - Période ignorée")

        # Analyser les résultats
        if self.results:
            self._analyze_walk_forward()
        else:
            print("\n" + "=" * 80)
            print("❌ AUCUN RÉSULTAT VALIDE")
            print("=" * 80)
            print("\nProblèmes possibles:")
            print("  • Période trop courte (pas assez de trades)")
            print("  • Paramètres trop restrictifs")
            print("  • Stratégie ne génère pas de signaux")
            print("\nRecommandations:")
            print("  • Augmenter la durée des périodes")
            print("  • Assouplir les conditions d'entrée")
            print("  • Vérifier les paramètres de la stratégie")

    def _analyze_walk_forward(self):
        """Analyse les résultats du walk-forward"""

        if not self.results:
            logger.error("Aucun résultat à analyser")
            return

        df = pd.DataFrame(self.results)

        print("\n" + "=" * 80)
        print("📊 ANALYSE WALK-FORWARD")
        print("=" * 80)

        # Filtrer les périodes sans trades
        valid_periods = len(df)
        total_periods = len(self.periods)

        print(f"\n📈 COUVERTURE:")
        print(f"   Périodes totales: {total_periods}")
        print(f"   Périodes valides: {valid_periods}")
        print(f"   Taux de couverture: {valid_periods/total_periods*100:.1f}%")

        if valid_periods < total_periods * 0.5:
            print(f"   ⚠️  ATTENTION: Moins de 50% de couverture")
            print(f"      → Stratégie trop restrictive ou périodes trop courtes")

        # Statistiques globales
        print("\n🎯 PERFORMANCE MOYENNE:")
        print(
            f"   In-Sample Sharpe:   {df['in_sample_sharpe'].mean():.2f} (±{df['in_sample_sharpe'].std():.2f})"
        )
        print(
            f"   Out-Sample Sharpe:  {df['out_sample_sharpe'].mean():.2f} (±{df['out_sample_sharpe'].std():.2f})"
        )
        print(f"   In-Sample Return:   {df['in_sample_return'].mean():.2f}%")
        print(f"   Out-Sample Return:  {df['out_sample_return'].mean():.2f}%")
        print(f"   Trades Out-Sample:  {df['out_sample_trades'].mean():.1f}")

        # Dégradation
        avg_degradation = df["degradation"].mean()
        print(f"\n📉 DÉGRADATION MOYENNE: {avg_degradation:.2f}")

        if avg_degradation < 0.3:
            print("   ✅ EXCELLENT - Stratégie robuste, peu d'overfitting")
        elif avg_degradation < 0.5:
            print("   ✓ BON - Dégradation acceptable")
        elif avg_degradation < 0.8:
            print("   ⚠️  MOYEN - Attention à l'overfitting")
        else:
            print("   ❌ MAUVAIS - Fort overfitting détecté")

        # Tableau détaillé
        print("\n" + "=" * 80)
        print("📋 RÉSULTATS PAR PÉRIODE")
        print("=" * 80)

        summary = df[
            [
                "period",
                "in_sample_sharpe",
                "out_sample_sharpe",
                "in_sample_return",
                "out_sample_return",
                "out_sample_trades",
                "degradation",
            ]
        ]
        print(summary.to_string(index=False))

        # Sauvegarder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        from config import settings

        results_file = settings.RESULTS_DIR / f"walk_forward_{timestamp}.csv"
        df.to_csv(results_file, index=False)

        print(f"\n✅ Résultats sauvegardés: {results_file}")

        # Recommandations
        print("\n" + "=" * 80)
        print("💡 RECOMMANDATIONS")
        print("=" * 80)

        # Vérifier si assez de périodes valides
        if valid_periods < 3:
            print("\n⚠️  ATTENTION: Trop peu de périodes valides")
            print("→ Augmenter la période In-Sample (ex: 18 mois)")
            print("→ Augmenter la période Out-Sample (ex: 6 mois)")
            print("→ Assouplir les conditions de la stratégie")
            return

        # Analyser la performance Out-Sample
        avg_out_sharpe = df["out_sample_sharpe"].mean()

        if avg_out_sharpe > 1.0:
            print("✓ La stratégie est robuste et rentable")

            if avg_degradation < 0.5:
                print("✓ Pas d'overfitting significatif")
                print("✅ PRÊT POUR LE PAPER TRADING")
            else:
                print("⚠️  Overfitting détecté mais performance acceptable")
                print("→ Simplifier la stratégie si possible")
        else:
            print("⚠️  Performance Out-Sample insuffisante")
            print("→ Ajuster les paramètres ou changer de stratégie")

        if avg_degradation > 0.5:
            print("\n⚠️  Overfitting détecté:")
            print("→ Simplifier la stratégie (moins de paramètres)")
            print("→ Augmenter la période In-Sample")
            print("→ Tester sur plus de symboles")

        # Analyse de stabilité
        sharpe_std = df["out_sample_sharpe"].std()
        if sharpe_std > 1.0:
            print("\n⚠️  Performance instable entre périodes")
            print(f"   Écart-type Sharpe: {sharpe_std:.2f}")
            print("→ Stratégie potentiellement non robuste")


def main():
    """Exemple d'utilisation"""

    print(
        """
╔═══════════════════════════════════════════════════════════════════════╗
║            🚶 WALK-FORWARD OPTIMIZATION 🚶                           ║
║                                                                       ║
║        Validation robuste pour éviter le surapprentissage           ║
╚═══════════════════════════════════════════════════════════════════════╝
    """
    )

    # Configuration
    wf_optimizer = WalkForwardOptimizer(
        strategy_class=MaSuperStrategie,
        symbols=["AAPL"],
        in_sample_months=24,  # 12 mois pour optimiser
        out_sample_months=6,  # 3 mois pour tester
        start_date="2015-01-01",
        end_date="2025-01-01",
    )
    # Grille de paramètres (réduite pour walk-forward)
    param_grid = {
        "ma_period": [20, 30, 50],
        "rsi_period": [14, 21],
        "stop_loss_pct": [0.02, 0.025],
    }
    # Générer les périodes
    periods = wf_optimizer.generate_periods()

    print(f"\n📅 Périodes générées:")
    for i, p in enumerate(periods, 1):
        print(
            f"   {i}. In: {p['in_sample'][0]} → {p['in_sample'][1]} | "
            f"Out: {p['out_sample'][0]} → {p['out_sample'][1]}"
        )

    print(f"\n⚙️  Grille de paramètres: {param_grid}")

    from itertools import product

    total_combos = 1
    for values in param_grid.values():
        total_combos *= len(values)
    print(f"   Total combinaisons par période: {total_combos}")
    print(f"   Total tests: {len(periods) * total_combos}")

    # Confirmation
    print("\n" + "=" * 70)
    confirm = input("▶ Lancer l'optimisation ? (o/n) [o]: ").strip().lower() or "o"

    if confirm != "o":
        print("Optimisation annulée")
        return

    # Lancer
    wf_optimizer.run_walk_forward(param_grid)


if __name__ == "__main__":
    main()
