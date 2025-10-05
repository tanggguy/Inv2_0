#!/usr/bin/env python3
"""
Script de démarrage rapide pour le Paper Trading avec Alpaca
Usage: python start_paper_trading.py
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_trading.paper_engine import PaperTradingEngine
from config.paper_trading_config import PAPER_TRADING_CONFIG
from monitoring.logger import setup_logger

logger = setup_logger("paper_trading_launcher")


def check_environment():
    """Vérifie que l'environnement est correctement configuré"""
    print("\n" + "="*60)
    print("VÉRIFICATION DE L'ENVIRONNEMENT")
    print("="*60)
    
    errors = []
    warnings = []
    
    # Vérifier le fichier .env
    if not Path('.env').exists():
        errors.append("Fichier .env non trouvé. Copiez .env.example vers .env et configurez-le.")
    else:
        print("✅ Fichier .env trouvé")
    
    # Vérifier les clés API Alpaca
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('ALPACA_API_KEY'):
        errors.append("ALPACA_API_KEY non définie dans .env")
    else:
        print("✅ ALPACA_API_KEY configurée")
    
    if not os.getenv('ALPACA_SECRET_KEY'):
        errors.append("ALPACA_SECRET_KEY non définie dans .env")
    else:
        print("✅ ALPACA_SECRET_KEY configurée")
    
    # Vérifier les dépendances
    try:
        import alpaca_trade_api
        print("✅ alpaca-trade-api installé")
    except ImportError:
        errors.append("alpaca-trade-api non installé. Exécutez: pip install alpaca-trade-api")
    
    try:
        import backtrader
        print("✅ backtrader installé")
    except ImportError:
        errors.append("backtrader non installé. Exécutez: pip install backtrader")
    
    # Vérifier les répertoires
    data_dir = Path('data_cache/portfolio_states')
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Répertoire data_cache créé")
    else:
        print("✅ Répertoire data_cache existant")
    
    # Vérifier Telegram (optionnel)
    if os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true':
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            warnings.append("TELEGRAM_BOT_TOKEN non défini (notifications désactivées)")
        if not os.getenv('TELEGRAM_CHAT_ID'):
            warnings.append("TELEGRAM_CHAT_ID non défini (notifications désactivées)")
    
    print("\n" + "="*60)
    
    # Afficher les erreurs
    if errors:
        print("❌ ERREURS DÉTECTÉES:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # Afficher les avertissements
    if warnings:
        print("⚠️  AVERTISSEMENTS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("✅ ENVIRONNEMENT PRÊT")
    print("="*60)
    return True


def display_config():
    """Affiche la configuration actuelle"""
    print("\n" + "="*60)
    print("CONFIGURATION ACTUELLE")
    print("="*60)
    
    # Stratégies actives
    active_strategies = [s for s in PAPER_TRADING_CONFIG['strategies'] if s.get('enabled', True)]
    print(f"\n📊 STRATÉGIES ACTIVES ({len(active_strategies)}):")
    
    total_capital = 0
    for strat in active_strategies:
        capital = strat['capital_allocation']
        total_capital += capital
        symbols = ', '.join(strat['symbols'])
        print(f"  • {strat['name']:20} ${capital:>10,.0f}  [{symbols}]")
    
    print(f"\n💰 CAPITAL TOTAL ALLOUÉ: ${total_capital:,.0f}")
    
    # Circuit Breakers
    cb_config = PAPER_TRADING_CONFIG['circuit_breakers']
    print(f"\n🛡️  CIRCUIT BREAKERS:")
    print(f"  • Max Drawdown:        {cb_config['max_drawdown_pct']:.0%}")
    print(f"  • Max Perte Jour:      {cb_config['max_daily_loss_pct']:.0%}")
    print(f"  • Max Trades/Jour:     {cb_config['max_daily_trades']}")
    print(f"  • Max Pertes Consec.:  {cb_config['max_consecutive_losses']}")
    
    # Données
    data_config = PAPER_TRADING_CONFIG['data']
    print(f"\n📈 DONNÉES:")
    print(f"  • Timeframe:           {data_config['timeframe']}")
    print(f"  • Historique:          {data_config['historical_days']} jours")
    print(f"  • Buffer:              {data_config['buffer_size']} barres")
    
    # Notifications
    notif_config = PAPER_TRADING_CONFIG['notifications']
    print(f"\n📱 NOTIFICATIONS:")
    print(f"  • Telegram:            {'✅ Activé' if notif_config['telegram_enabled'] else '❌ Désactivé'}")
    print(f"  • Email:               {'✅ Activé' if notif_config['email_enabled'] else '❌ Désactivé'}")
    
    print("\n" + "="*60)


def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Démarrage du Paper Trading avec Alpaca",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help="Vérifier l'environnement sans lancer le trading"
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help="Afficher la configuration et quitter"
    )
    
    parser.add_argument(
        '--test-telegram',
        action='store_true',
        help="Tester les notifications Telegram"
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help="Restaurer depuis le dernier état sauvegardé"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Mode verbeux"
    )
    
    return parser.parse_args()


def test_telegram():
    """Teste les notifications Telegram"""
    from monitoring.telegram_notifier import test_telegram_notifications
    print("\nTest des notifications Telegram...")
    test_telegram_notifications()


def main():
    """Fonction principale"""
    args = parse_arguments()
    
    # Banner
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         📈 PAPER TRADING AVEC ALPACA 📉                ║
    ║                                                          ║
    ║           Mode Simulation - Pas d'argent réel           ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Mode verbose
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Test Telegram uniquement
    if args.test_telegram:
        test_telegram()
        return 0
    
    # Afficher config uniquement
    if args.config:
        if check_environment():
            display_config()
        return 0
    
    # Vérification uniquement
    if args.check_only:
        if check_environment():
            print("\n✅ Système prêt pour le paper trading!")
            print("Lancez 'python start_paper_trading.py' pour démarrer")
        return 0
    
    # Vérifier l'environnement
    if not check_environment():
        print("\n❌ Corrigez les erreurs avant de continuer")
        return 1
    
    # Afficher la configuration
    display_config()
    
    # Demander confirmation
    print("\n" + "="*60)
    response = input("Démarrer le paper trading? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("Annulé par l'utilisateur")
        return 0
    
    try:
        # Créer et initialiser le moteur
        print("\n🚀 DÉMARRAGE DU PAPER TRADING...")
        engine = PaperTradingEngine()
        
        # Restaurer l'état si demandé
        if args.restore:
            print("Restauration de l'état précédent...")
            state = engine.portfolio_manager.load_latest_state()
            if state:
                print(f"✅ État restauré: {state['timestamp']}")
        
        # Initialiser
        if not engine.initialize():
            print("❌ Échec de l'initialisation")
            return 1
        
        # Démarrer
        print("\n" + "="*60)
        print("PAPER TRADING EN COURS...")
        print("Appuyez sur Ctrl+C pour arrêter")
        print("="*60 + "\n")
        
        engine.start()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêt demandé par l'utilisateur...")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return 1
    
    print("\n✅ Paper trading terminé")
    return 0


if __name__ == "__main__":
    sys.exit(main())