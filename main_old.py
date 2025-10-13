#!/usr/bin/env python3
"""
Point d'entrée principal du système de trading algorithmique
"""

import argparse
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from monitoring.logger import setup_logger
from backtesting.backtest_engine import BacktestEngine

# Configuration du logger
logger = setup_logger("main")


def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Système de Trading Algorithmique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py --mode backtest --strategy MovingAverage --symbols AAPL MSFT
  python main.py --mode paper --strategy RSI
  python main.py --test
        """,
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["backtest", "paper", "live"],
        default="backtest",
        help="Mode de trading (default: backtest)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default="MovingAverage",
        help="Nom de la stratégie à utiliser (default: MovingAverage)",
    )

    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        default=["AAPL"],
        help="Liste des symboles à trader (default: AAPL)",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=settings.BACKTEST_CONFIG["start_date"],
        help="Date de début (format: YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=settings.BACKTEST_CONFIG["end_date"],
        help="Date de fin (format: YYYY-MM-DD)",
    )

    parser.add_argument(
        "--capital",
        type=float,
        default=settings.INITIAL_CAPITAL,
        help=f"Capital initial (default: {settings.INITIAL_CAPITAL})",
    )

    parser.add_argument(
        "--test", action="store_true", help="Exécuter un test rapide du système"
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Afficher les graphiques à la fin du backtest",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Mode verbose (plus de logs)"
    )

    return parser.parse_args()


def run_backtest(args):
    """Exécute un backtest"""
    logger.info("=" * 80)
    logger.info("🚀 DÉMARRAGE DU BACKTEST")
    logger.info("=" * 80)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Stratégie: {args.strategy}")
    logger.info(f"Symboles: {', '.join(args.symbols)}")
    logger.info(f"Période: {args.start_date} → {args.end_date}")
    logger.info(f"Capital initial: ${args.capital:,.2f}")
    logger.info("=" * 80)

    try:
        # Initialiser le moteur de backtesting
        engine = BacktestEngine(
            strategy_name=args.strategy,
            symbols=args.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.capital,
            verbose=args.verbose,
        )

        # Exécuter le backtest
        results = engine.run()

        # Afficher les résultats
        logger.info("\n" + "=" * 80)
        logger.info("📊 RÉSULTATS DU BACKTEST")
        logger.info("=" * 80)

        if results:
            logger.info(f"Capital final: ${results.get('final_value', 0):,.2f}")
            logger.info(f"Rendement total: {results.get('total_return', 0):.2f}%")
            logger.info(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
            logger.info(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
            logger.info(f"Nombre de trades: {results.get('total_trades', 0)}")
            logger.info(f"Taux de réussite: {results.get('win_rate', 0):.2f}%")

            # Générer le rapport
            logger.info("\n📝 Génération du rapport détaillé...")
            report_path = engine.generate_report()
            logger.info(f"✅ Rapport sauvegardé: {report_path}")

            # Afficher les graphiques si demandé
            if args.plot:
                logger.info("\n📈 Affichage des graphiques...")
                engine.plot_results()
        else:
            logger.error("❌ Aucun résultat disponible")

        logger.info("=" * 80)
        logger.info("✅ Backtest terminé avec succès")

    except Exception as e:
        logger.error(f"❌ Erreur lors du backtest: {e}", exc_info=True)
        return 1

    return 0


def run_paper_trading(args):
    """Lance le paper trading"""
    logger.info("🔄 Mode Paper Trading (En développement)")
    logger.warning("Cette fonctionnalité sera disponible prochainement")
    return 0


def run_live_trading(args):
    """Lance le live trading"""
    logger.warning("⚠️  MODE LIVE TRADING")
    logger.warning("Ce mode utilise de l'argent réel !")

    response = input("Êtes-vous sûr de vouloir continuer ? (oui/non): ")
    if response.lower() not in ["oui", "yes", "y"]:
        logger.info("Opération annulée")
        return 0

    logger.info("🔄 Mode Live Trading (En développement)")
    logger.warning("Cette fonctionnalité sera disponible prochainement")
    return 0


def run_tests():
    """Exécute des tests rapides du système"""
    logger.info("🧪 Exécution des tests du système")
    logger.info("=" * 80)

    # Test 1: Configuration
    logger.info("Test 1: Chargement de la configuration...")
    try:
        config = settings.get_config()
        logger.info(f"✅ Configuration chargée: Mode {config['trading_mode']}")
    except Exception as e:
        logger.error(f"❌ Erreur configuration: {e}")
        return 1

    # Test 2: Data Handler
    logger.info("\nTest 2: Data Handler...")
    try:
        from data.data_handler import DataHandler

        data_handler = DataHandler()
        logger.info("✅ Data Handler initialisé")
    except Exception as e:
        logger.error(f"❌ Erreur Data Handler: {e}")
        return 1

    # Test 3: Téléchargement de données
    logger.info("\nTest 3: Téléchargement de données...")
    try:
        df = data_handler.fetch_data("AAPL", "2024-01-01", "2024-01-31")
        if df is not None and not df.empty:
            logger.info(f"✅ Données téléchargées: {len(df)} barres")
            logger.info(f"   Période: {df.index[0]} → {df.index[-1]}")
        else:
            logger.warning("⚠️  Aucune donnée récupérée")
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement: {e}")
        return 1

    # Test 4: Stratégie
    logger.info("\nTest 4: Chargement d'une stratégie...")
    try:
        from strategies.moving_average import MovingAverageStrategy

        logger.info("✅ Stratégie MovingAverage chargée")
    except Exception as e:
        logger.error(f"❌ Erreur stratégie: {e}")
        return 1

    logger.info("\n" + "=" * 80)
    logger.info("✅ Tous les tests sont passés avec succès !")
    logger.info("🎯 Le système est prêt à être utilisé")
    return 0


def main():
    """Fonction principale"""
    args = parse_arguments()

    # Afficher le banner
    print(
        """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🤖 SYSTÈME DE TRADING ALGORITHMIQUE 🤖           ║
    ║                                                           ║
    ║              Powered by Backtrader                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    )

    # Mode test
    if args.test:
        return run_tests()

    # Sélectionner le mode
    if args.mode == "backtest":
        return run_backtest(args)
    elif args.mode == "paper":
        return run_paper_trading(args)
    elif args.mode == "live":
        return run_live_trading(args)
    else:
        logger.error(f"Mode inconnu: {args.mode}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        sys.exit(1)
