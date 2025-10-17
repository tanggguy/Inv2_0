#!/usr/bin/env python3
"""
Système de Trading Algorithmique - Point d'entrée principal
Supporte: Backtesting (mono et multi-symbole), Paper Trading, Live Trading
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from config import settings
from monitoring.logger import setup_logger

# Configuration du logger principal
logger = setup_logger("main")


def parse_arguments():
    """Parse les arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Système de Trading Algorithmique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  
  Backtesting mono-symbole (mode classique):
    python main.py --mode backtest --strategy MovingAverage --symbols AAPL
    
  Backtesting multi-symbole avec poids égaux:
    python main.py --mode backtest --strategy MaRSI \\
        --symbols AAPL,MSFT,GOOGL,AMZN \\
        --start-date 2018-12-31 --end-date 2025-10-06 \\
        --multi-symbol --capital 100000
    
  Backtesting multi-symbole avec poids custom:
    python main.py --mode backtest --strategy MaRSI \\
        --symbols AAPL,MSFT,GOOGL,AMZN \\
        --multi-symbol \\
        --symbol-weights "AAPL:0.4,MSFT:0.3,GOOGL:0.2,AMZN:0.1" \\
        --max-positions 3
    
  Paper Trading avec Alpaca:
    python main.py --mode paper
    
  Mode Test:
    python main.py --test
        """,
    )

    # Mode principal
    parser.add_argument(
        "--mode",
        choices=["backtest", "paper", "live"],
        default="backtest",
        help="Mode de trading (default: backtest)",
    )

    # Stratégie
    parser.add_argument("--strategy", type=str, help="Nom de la stratégie à utiliser")

    # Symboles
    parser.add_argument(
        "--symbols",
        type=str,
        help="Symboles à trader (séparés par des virgules, ex: AAPL,MSFT,GOOGL)",
    )

    # Dates pour le backtesting
    parser.add_argument(
        "--start-date", type=str, help="Date de début (format: YYYY-MM-DD)"
    )

    parser.add_argument("--end-date", type=str, help="Date de fin (format: YYYY-MM-DD)")

    # Capital
    parser.add_argument(
        "--capital",
        type=float,
        default=100000,
        help="Capital initial (default: 100000)",
    )

    # === NOUVEAUX ARGUMENTS MULTI-SYMBOLE ===

    parser.add_argument(
        "--multi-symbol",
        action="store_true",
        help="Active le mode backtest multi-symbole avec portfolios séparés",
    )

    parser.add_argument(
        "--symbol-weights",
        type=str,
        default=None,
        help="Poids custom par symbole (ex: 'AAPL:0.4,MSFT:0.3,GOOGL:0.2,AMZN:0.1'). Si non spécifié, equal-weight.",
    )

    parser.add_argument(
        "--max-positions",
        type=int,
        default=None,
        help="Nombre maximum de positions simultanées (optionnel)",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Exporte les résultats (JSON, CSV, HTML) pour le mode multi-symbole",
    )

    parser.add_argument(
        "--export-dir",
        type=str,
        default=None,
        help="Répertoire d'export personnalisé (par défaut: results/multi_symbol/)",
    )

    # === FIN NOUVEAUX ARGUMENTS ===

    # Broker pour le live trading
    parser.add_argument(
        "--broker",
        choices=["alpaca", "ibkr", "binance"],
        default="alpaca",
        help="Broker pour le live trading (default: alpaca)",
    )

    # Mode test
    parser.add_argument(
        "--test", action="store_true", help="Lance les tests du système"
    )

    # Verbosité
    parser.add_argument("--verbose", action="store_true", help="Mode verbeux")

    return parser.parse_args()


def parse_symbol_weights(weights_str: str) -> dict:
    """
    Parse une chaîne de poids en dict

    Args:
        weights_str: "AAPL:0.4,MSFT:0.3,GOOGL:0.2,AMZN:0.1"

    Returns:
        Dict {symbol: weight}
    """
    if not weights_str:
        return None

    weights = {}

    try:
        for pair in weights_str.split(","):
            symbol, weight = pair.split(":")
            weights[symbol.strip()] = float(weight.strip())

        logger.info(f"Poids parsés: {weights}")
        return weights

    except Exception as e:
        logger.error(f"Erreur parsing poids: {e}")
        logger.error("Format attendu: 'AAPL:0.4,MSFT:0.3,GOOGL:0.2,AMZN:0.1'")
        return None


def run_backtest(args):
    """Lance un backtest (mono ou multi-symbole)"""
    logger.info("📊 Mode Backtesting")

    try:
        # Récupérer les paramètres
        strategy_name = args.strategy or "MovingAverage"
        symbols = args.symbols.split(",") if args.symbols else ["AAPL"]
        start_date = args.start_date or "2023-01-01"
        end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Stratégie: {strategy_name}")
        logger.info(f"Symboles: {symbols}")
        logger.info(f"Période: {start_date} à {end_date}")
        logger.info(f"Capital: ${args.capital:,.2f}")

        # === MODE MULTI-SYMBOLE ===
        if args.multi_symbol or len(symbols) > 1:
            logger.info("🔀 Mode MULTI-SYMBOLE activé")

            from backtesting.multi_symbol_engine import MultiSymbolBacktestEngine

            # Parser les poids si fournis
            symbol_weights = parse_symbol_weights(args.symbol_weights)

            # Créer le moteur multi-symbole
            engine = MultiSymbolBacktestEngine(
                strategy_name=strategy_name,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=args.capital,
                symbol_weights=symbol_weights,
                max_positions=args.max_positions,
                verbose=args.verbose,
            )

            # Lancer le backtest
            logger.info("Lancement du backtest multi-symbole...\n")
            results = engine.run()

            if results:
                logger.info("\n✅ Backtest multi-symbole terminé avec succès!")

                # Export si demandé
                if args.export:
                    logger.info("\n📦 Export des résultats...")
                    from backtesting.multi_symbol_exporter import MultiSymbolExporter

                    exporter = MultiSymbolExporter(
                        results=results, output_dir=args.export_dir
                    )

                    exported_files = exporter.export_all()

                    logger.info("\n✅ Export terminé:")
                    for file_type, filepath in exported_files.items():
                        logger.info(f"   • {file_type}: {filepath}")

                # Analyse détaillée
                logger.info("\n📊 Analyse détaillée:")
                from backtesting.symbol_analyzer import SymbolAnalyzer

                analyzer = SymbolAnalyzer(results["by_symbol"])

                # Utiliser vraies corrélations si disponibles
                returns_data = results.get("daily_returns", {})
                if returns_data:
                    logger.info("✓ Utilisation des returns réels pour corrélations")

                    # Calculer matrice de corrélation
                    corr_matrix = analyzer.calculate_correlation_matrix(returns_data)
                    logger.info(f"\n🔗 Matrice de Corrélation:")
                    logger.info(corr_matrix.round(2).to_string())

                    # Calculer diversification ratio
                    div_ratio = analyzer.calculate_diversification_ratio(returns_data)
                else:
                    logger.warning(
                        "⚠️  Returns non disponibles, corrélations simplifiées"
                    )

                analyzer.print_analysis()

            else:
                logger.error("❌ Erreur lors du backtest")
                return None

        # === MODE MONO-SYMBOLE (classique) ===
        else:
            logger.info("📈 Mode MONO-SYMBOLE (classique)")

            from backtesting.backtest_engine import BacktestEngine

            # Créer et lancer le backtest classique
            engine = BacktestEngine(
                strategy_name=strategy_name,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=args.capital,
                verbose=args.verbose,
            )

            # Lancer le backtest
            logger.info("Lancement du backtest...\n")
            results = engine.run()

            if results:
                logger.info("\n✅ Backtest terminé avec succès!")

                # Générer rapport
                report_path = engine.generate_report()
                if report_path:
                    logger.info(f"📄 Rapport: {report_path}")
            else:
                logger.error("❌ Erreur lors du backtest")
                return None

        return results

    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return None


def run_paper_trading(args):
    """Lance le paper trading"""
    logger.info("📃 Mode Paper Trading")

    try:
        from paper_trading.paper_engine import PaperTradingEngine

        logger.info("Démarrage du paper trading avec Alpaca...")

        engine = PaperTradingEngine()
        engine.start()

        logger.info("✅ Paper trading lancé avec succès!")
        logger.info("Appuyez sur Ctrl+C pour arrêter")

    except KeyboardInterrupt:
        logger.info("\n⏹️  Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


def run_live_trading(args):
    """Lance le live trading"""
    logger.error("🚫 Live trading non encore implémenté")
    logger.info("Utilisez --mode paper pour le paper trading")


def run_tests():
    """Lance les tests du système"""
    logger.info("🧪 Lancement des tests...")

    try:
        import pytest

        exit_code = pytest.main(["-v", "tests/"])

        if exit_code == 0:
            logger.info("✅ Tous les tests ont réussi!")
        else:
            logger.error(f"❌ Certains tests ont échoué (code: {exit_code})")

    except ImportError:
        logger.error("❌ pytest n'est pas installé")
        logger.info("Installez-le avec: pip install pytest")


def main():
    """Point d'entrée principal"""
    args = parse_arguments()

    # Configuration du niveau de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Bannière
    logger.info("=" * 80)
    logger.info("🚀 SYSTÈME DE TRADING ALGORITHMIQUE")
    logger.info("=" * 80)

    # Mode test
    if args.test:
        run_tests()
        return

    # Dispatcher selon le mode
    if args.mode == "backtest":
        run_backtest(args)
    elif args.mode == "paper":
        run_paper_trading(args)
    elif args.mode == "live":
        run_live_trading(args)
    else:
        logger.error(f"Mode inconnu: {args.mode}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Programme interrompu")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
