#!/usr/bin/env python3
"""
Système de Trading Algorithmique - Point d'entrée principal
Supporte: Backtesting, Paper Trading (Alpaca), Live Trading
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
  
  Backtesting:
    python main2.py --mode backtest --strategy MovingAverage --symbols AAPL,MSFT
    
  Paper Trading avec Alpaca:
    python main2.py --mode paper
    
  Live Trading:
    python main.py --mode live --strategy RSI --broker alpaca
    
  Mode Test:
    python main.py --test
        """
    )
    
    # Mode principal
    parser.add_argument(
        '--mode', 
        choices=['backtest', 'paper', 'live'],
        default='backtest',
        help='Mode de trading (default: backtest)'
    )
    
    # Stratégie
    parser.add_argument(
        '--strategy',
        type=str,
        help='Nom de la stratégie à utiliser'
    )
    
    # Symboles
    parser.add_argument(
        '--symbols',
        type=str,
        help='Symboles à trader (séparés par des virgules)'
    )
    
    # Dates pour le backtesting
    parser.add_argument(
        '--start-date',
        type=str,
        help='Date de début (format: YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='Date de fin (format: YYYY-MM-DD)'
    )
    
    # Capital
    parser.add_argument(
        '--capital',
        type=float,
        default=100000,
        help='Capital initial (default: 100000)'
    )
    
    # Broker pour le live trading
    parser.add_argument(
        '--broker',
        choices=['alpaca', 'ibkr', 'binance'],
        default='alpaca',
        help='Broker pour le live trading (default: alpaca)'
    )
    
    # Mode test
    parser.add_argument(
        '--test',
        action='store_true',
        help='Lance les tests du système'
    )
    
    # Verbosité
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Mode verbeux'
    )
    
    return parser.parse_args()


def run_backtest(args):
    """Lance un backtest"""
    logger.info("📊 Mode Backtesting")
    
    try:
        from backtesting.backtest_engine import BacktestEngine
        
        # Récupérer les paramètres
        strategy_name = args.strategy or "MovingAverage"
        symbols = args.symbols.split(',') if args.symbols else ["AAPL"]
        start_date = args.start_date or "2023-01-01"
        end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Stratégie: {strategy_name}")
        logger.info(f"Symboles: {symbols}")
        logger.info(f"Période: {start_date} à {end_date}")
        logger.info(f"Capital: ${args.capital:,.2f}")
        
        # Créer et lancer le backtest
        engine = BacktestEngine(
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=args.capital,
            verbose=args.verbose
        )
        
        # Lancer le backtest
        logger.info("Lancement du backtest...")
        results = engine.run()
        
        # Afficher les résultats
        engine.plot_results()
        
        # Sauvegarder les résultats
        engine.generate_report()
        
        logger.info("✅ Backtest terminé avec succès")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du backtest: {e}")
        return 1


def run_paper_trading(args):
    """Lance le mode paper trading avec Alpaca"""
    logger.info("🤖 Mode Paper Trading avec Alpaca")
    
    try:
        # Importer le moteur de paper trading
        from paper_trading.paper_engine import PaperTradingEngine
        
        # Créer et initialiser le moteur
        logger.info("Initialisation du Paper Trading Engine...")
        engine = PaperTradingEngine()
        
        if not engine.initialize():
            logger.error("Échec de l'initialisation du paper trading")
            return 1
        
        # Démarrer le trading
        logger.info("Démarrage du paper trading...")
        engine.start()
        
        return 0
        
    except ImportError as e:
        logger.error(f"Module paper_trading non trouvé: {e}")
        logger.error("Assurez-vous d'avoir installé les dépendances: pip install alpaca-trade-api")
        return 1
    except KeyboardInterrupt:
        logger.info("Paper trading interrompu par l'utilisateur")
        return 0
    except Exception as e:
        logger.error(f"Erreur dans le paper trading: {e}")
        return 1


def run_live_trading(args):
    """Lance le mode live trading"""
    logger.info("💰 Mode Live Trading")
    logger.warning("⚠️  ATTENTION: Mode LIVE - Argent réel en jeu!")
    
    # Demander confirmation
    confirmation = input("Êtes-vous sûr de vouloir lancer le trading LIVE? (oui/non): ")
    if confirmation.lower() != 'oui':
        logger.info("Trading live annulé")
        return 0
    
    logger.warning("⚠️  Mode live trading non encore implémenté pour la sécurité")
    logger.info("Utilisez le mode paper trading pour tester vos stratégies")
    
    return 0


def run_tests():
    """Lance les tests du système"""
    logger.info("🧪 Lancement des tests")
    
    try:
        import pytest
        
        # Créer le dossier tests s'il n'existe pas
        tests_dir = Path("tests")
        if not tests_dir.exists():
            logger.warning("Dossier tests non trouvé, création...")
            tests_dir.mkdir()
            
            # Créer un test basique
            test_file = tests_dir / "test_basic.py"
            test_file.write_text("""
def test_import():
    '''Test que les imports fonctionnent'''
    import backtrader
    import pandas
    import numpy
    assert True

def test_config():
    '''Test la configuration'''
    from config import settings
    assert settings.INITIAL_CAPITAL > 0
""")
        
        # Lancer pytest
        result = pytest.main(["-v", "tests/"])
        
        if result == 0:
            logger.info("✅ Tous les tests sont passés")
        else:
            logger.error("❌ Certains tests ont échoué")
        
        return result
        
    except ImportError:
        logger.error("pytest n'est pas installé. Installez-le avec: pip install pytest")
        return 1
    except Exception as e:
        logger.error(f"Erreur lors des tests: {e}")
        return 1


def check_dependencies():
    """Vérifie que les dépendances sont installées"""
    required_packages = [
        'backtrader',
        'pandas',
        'numpy',
        'yfinance',
    ]
    
    optional_packages = [
        ('alpaca_trade_api', 'Paper Trading avec Alpaca'),
        ('telegram', 'Notifications Telegram'),
        ('streamlit', 'Dashboard d\'optimisation'),
    ]
    
    missing_required = []
    missing_optional = []
    
    # Vérifier les packages requis
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_required.append(package)
    
    # Vérifier les packages optionnels
    for package, description in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append((package, description))
    
    # Afficher les résultats
    if missing_required:
        logger.error("❌ Packages requis manquants:")
        for package in missing_required:
            logger.error(f"  - {package}")
        logger.error("Installez-les avec: pip install -r requirements.txt")
        return False
    
    if missing_optional:
        logger.warning("⚠️  Packages optionnels manquants:")
        for package, desc in missing_optional:
            logger.warning(f"  - {package} ({desc})")
    
    return True


def main():
    """Fonction principale"""
    args = parse_arguments()
    
    # Configuration du logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Afficher le banner
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        🤖 SYSTÈME DE TRADING ALGORITHMIQUE 🤖          ║
    ║                                                          ║
    ║              Powered by Backtrader                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Vérifier les dépendances
    if not check_dependencies():
        return 1
    
    # Mode test
    if args.test:
        return run_tests()
    
    # Sélectionner le mode
    if args.mode == 'backtest':
        return run_backtest(args)
    elif args.mode == 'paper':
        return run_paper_trading(args)
    elif args.mode == 'live':
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