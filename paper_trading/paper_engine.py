"""
Paper Trading Engine - Moteur principal de paper trading avec Alpaca
"""
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from config.paper_trading_config import PAPER_TRADING_CONFIG, validate_config
from paper_trading.alpaca_store import AlpacaStore
from paper_trading.portfolio_state import PortfolioStateManager
from paper_trading.circuit_breaker import CircuitBreaker
from paper_trading.multi_strategy_runner import MultiStrategyRunner
from monitoring.logger import setup_logger
from monitoring.telegram_notifier import TelegramNotifier

logger = setup_logger("paper_engine")


class PaperTradingEngine:
    """
    Moteur principal de paper trading
    Coordonne tous les composants du système
    """
    
    def __init__(self, config=None):
        """
        Initialise le moteur de paper trading
        
        Args:
            config: Configuration personnalisée (optionnel)
        """
        # Configuration
        self.config = config or PAPER_TRADING_CONFIG
        
        # Valider la configuration
        try:
            validate_config()
        except ValueError as e:
            logger.error(f"Configuration invalide: {e}")
            raise
        
        # Composants principaux
        self.store = None
        self.portfolio_manager = None
        self.circuit_breaker = None
        self.strategy_runner = None
        self.notification_manager = None
        
        # État du système
        self.running = False
        self.start_time = None
        self.stats = {
            'trades_executed': 0,
            'trades_won': 0,
            'trades_lost': 0,
            'total_pnl': 0,
            'peak_value': 0,
            'lowest_value': float('inf'),
            'errors': 0
        }
        
        # Gestionnaire de signaux pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("PaperTradingEngine initialisé")
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"Signal {signum} reçu, arrêt en cours...")
        self.stop()
        sys.exit(0)
    
    def initialize(self):
        """Initialise tous les composants"""
        try:
            logger.info("="*60)
            logger.info("INITIALISATION DU SYSTÈME DE PAPER TRADING")
            logger.info("="*60)
            
            # 1. Initialiser le store Alpaca
            logger.info("1. Initialisation d'Alpaca Store...")
            self.store = AlpacaStore(
                api_key=self.config['alpaca']['api_key'],
                secret_key=self.config['alpaca']['secret_key'],
                base_url=self.config['alpaca']['base_url'],
                data_url=self.config['alpaca']['data_url'],
                data_feed=self.config['alpaca']['data_feed']
            )
            account = self.store.get_account()
            logger.info(f"   ✓ Connecté - Cash: ${float(account.cash):,.2f}")
            
            # 2. Initialiser les notifications
            if self.config['notifications']['telegram_enabled']:
                logger.info("2. Initialisation des notifications Telegram...")
                self.notification_manager = TelegramNotifier(
                    bot_token=self.config['notifications']['telegram_bot_token'],
                    chat_id=self.config['notifications']['telegram_chat_id']
                )
                self.notification_manager.send_message("🚀 Paper Trading Engine démarré")
                logger.info("   ✓ Notifications activées")
            else:
                logger.info("2. Notifications désactivées")
            
            # 3. Initialiser le gestionnaire de portefeuille
            logger.info("3. Initialisation du Portfolio Manager...")
            self.portfolio_manager = PortfolioStateManager(self.config)
            
            # Essayer de restaurer l'état précédent
            previous_state = self.portfolio_manager.load_latest_state()
            if previous_state:
                logger.info(f"   ✓ État précédent restauré ({previous_state['timestamp']})")
            else:
                logger.info("   ✓ Nouvel état créé")
            
            # 4. Initialiser le circuit breaker
            logger.info("4. Initialisation du Circuit Breaker...")
            self.circuit_breaker = CircuitBreaker(
                self.config,
                self.notification_manager
            )
            initial_capital = float(account.portfolio_value)
            self.circuit_breaker.start(initial_capital)
            logger.info(f"   ✓ Circuit breaker activé (Capital: ${initial_capital:,.2f})")
            
            # 5. Initialiser le runner multi-stratégies
            logger.info("5. Initialisation des stratégies...")
            self.strategy_runner = MultiStrategyRunner(
                self.config,
                self.store,
                self.circuit_breaker,
                self.portfolio_manager
            )
            self.strategy_runner.initialize()
            
            # Afficher les stratégies actives
            active_strategies = [s['name'] for s in self.config['strategies'] if s.get('enabled', True)]
            logger.info(f"   ✓ {len(active_strategies)} stratégies prêtes: {', '.join(active_strategies)}")
            
            logger.info("="*60)
            logger.info("SYSTÈME PRÊT")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
            if self.notification_manager:
                self.notification_manager.send_alert(f"❌ Erreur initialisation: {e}")
            raise
    
    def start(self):
        """Démarre le paper trading"""
        try:
            if self.running:
                logger.warning("Le système est déjà en cours d'exécution")
                return
            
            logger.info("\n" + "="*60)
            logger.info("DÉMARRAGE DU PAPER TRADING")
            logger.info("="*60)
            
            self.running = True
            self.start_time = datetime.now()
            
            # Démarrer les composants
            self.store.start()
            self.portfolio_manager.start()
            self.strategy_runner.start()
            
            logger.info("✓ Tous les composants démarrés")
            
            # Notification de démarrage
            if self.notification_manager:
                self.notification_manager.send_message(
                    f"✅ Paper Trading démarré\n"
                    f"Stratégies actives: {len(self.strategy_runner.strategies)}\n"
                    f"Capital initial: ${self.circuit_breaker.initial_capital:,.2f}"
                )
            
            # Boucle principale
            self._run_main_loop()
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage: {e}")
            self.stats['errors'] += 1
            if self.notification_manager:
                self.notification_manager.send_alert(f"❌ Erreur démarrage: {e}")
            raise
    
    def _run_main_loop(self):
        """Boucle principale du système"""
        logger.info("Boucle principale démarrée - Ctrl+C pour arrêter")
        
        last_performance_check = time.time()
        last_summary_time = datetime.now()
        performance_check_interval = 60  # Vérifier toutes les minutes
        
        try:
            while self.running:
                current_time = time.time()
                
                # Vérifier les performances périodiquement
                if current_time - last_performance_check > performance_check_interval:
                    self._check_performance()
                    last_performance_check = current_time
                
                # Envoyer un résumé quotidien
                if self.config['notifications'].get('telegram_daily_summary'):
                    now = datetime.now()
                    summary_time = datetime.strptime(
                        self.config['notifications']['telegram_summary_time'], 
                        '%H:%M'
                    ).time()
                    
                    if now.time() >= summary_time and now.date() != last_summary_time.date():
                        self._send_daily_summary()
                        last_summary_time = now
                
                # Pause pour éviter de surcharger le CPU
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interruption utilisateur détectée")
        except Exception as e:
            logger.error(f"Erreur dans la boucle principale: {e}")
            self.stats['errors'] += 1
    
    def _check_performance(self):
        """Vérifie et met à jour les performances"""
        try:
            # Récupérer les infos du compte
            account = self.store.get_account()
            if not account:
                return
            
            current_value = float(account.portfolio_value)
            
            # Mettre à jour les stats
            self.stats['peak_value'] = max(self.stats['peak_value'], current_value)
            self.stats['lowest_value'] = min(self.stats['lowest_value'], current_value)
            
            # Vérifier le circuit breaker
            can_trade = self.circuit_breaker.check_conditions(current_value)
            
            # Récupérer les performances des stratégies
            strategy_perf = self.strategy_runner.get_performance()
            
            # Mettre à jour l'état du portefeuille
            self.portfolio_manager.update_state('account', {
                'portfolio_value': current_value,
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'timestamp': datetime.now().isoformat()
            })
            
            self.portfolio_manager.update_state('performance', {
                'total_pnl': strategy_perf['total_pnl'],
                'total_trades': strategy_perf['total_trades'],
                'can_trade': can_trade,
                'strategies': strategy_perf['strategies']
            })
            
            # Log périodique
            logger.info(f"Performance Check - Value: ${current_value:,.2f} | "
                       f"PnL: ${strategy_perf['total_pnl']:+,.2f} | "
                       f"Trades: {strategy_perf['total_trades']} | "
                       f"Trading: {'✓' if can_trade else '✗'}")
            
        except Exception as e:
            logger.error(f"Erreur vérification performance: {e}")
            self.stats['errors'] += 1
    
    def _send_daily_summary(self):
        """Envoie un résumé quotidien"""
        try:
            if not self.notification_manager:
                return
            
            # Récupérer les infos
            account = self.store.get_account()
            strategy_perf = self.strategy_runner.get_performance()
            breaker_status = self.circuit_breaker.get_status()
            
            # Créer le message
            message = f"""📊 **RÉSUMÉ QUOTIDIEN**
            
💰 **Portefeuille**
• Valeur: ${float(account.portfolio_value):,.2f}
• Cash: ${float(account.cash):,.2f}
• P&L Total: ${strategy_perf['total_pnl']:+,.2f}

📈 **Trading**
• Trades: {strategy_perf['total_trades']}
• Circuit Breaker: {'🔴 PAUSE' if breaker_status['paused'] else '🟢 ACTIF'}

🎯 **Stratégies**"""
            
            for name, perf in strategy_perf['strategies'].items():
                message += f"\n• {name}: ${perf['pnl']:+,.2f} ({perf['trades']} trades)"
            
            # Ajouter les alertes si nécessaire
            if breaker_status['paused']:
                message += f"\n\n⚠️ Trading suspendu jusqu'à {breaker_status['pause_until']}"
            
            # Envoyer
            self.notification_manager.send_message(message)
            logger.info("Résumé quotidien envoyé")
            
        except Exception as e:
            logger.error(f"Erreur envoi résumé: {e}")
    
    def stop(self):
        """Arrête le paper trading"""
        try:
            if not self.running:
                return
            
            logger.info("\n" + "="*60)
            logger.info("ARRÊT DU PAPER TRADING EN COURS...")
            logger.info("="*60)
            
            self.running = False
            
            # Arrêter les composants dans l'ordre inverse
            if self.strategy_runner:
                logger.info("Arrêt des stratégies...")
                self.strategy_runner.stop()
            
            if self.circuit_breaker:
                logger.info("Arrêt du circuit breaker...")
                self.circuit_breaker.stop()
            
            if self.portfolio_manager:
                logger.info("Sauvegarde finale du portefeuille...")
                self.portfolio_manager.save_state()
                self.portfolio_manager.stop()
            
            if self.store:
                logger.info("Fermeture des connexions Alpaca...")
                self.store.stop()
            
            # Envoyer le résumé final
            self._send_final_summary()
            
            logger.info("="*60)
            logger.info("SYSTÈME ARRÊTÉ PROPREMENT")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt: {e}")
    
    def _send_final_summary(self):
        """Envoie un résumé final à l'arrêt"""
        try:
            if not self.notification_manager:
                return
            
            # Calculer la durée
            if self.start_time:
                duration = datetime.now() - self.start_time
                hours = duration.total_seconds() / 3600
            else:
                hours = 0
            
            # Récupérer les performances finales
            strategy_perf = self.strategy_runner.get_performance() if self.strategy_runner else {}
            
            message = f"""🛑 **PAPER TRADING ARRÊTÉ**
            
⏱️ Durée: {hours:.1f} heures
📊 P&L Final: ${strategy_perf.get('total_pnl', 0):+,.2f}
📈 Trades Total: {strategy_perf.get('total_trades', 0)}
⚠️ Erreurs: {self.stats['errors']}

Système arrêté proprement."""
            
            self.notification_manager.send_message(message)
            
        except Exception as e:
            logger.error(f"Erreur envoi résumé final: {e}")
    
    def get_status(self):
        """Retourne le statut complet du système"""
        status = {
            'running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'stats': self.stats.copy()
        }
        
        # Ajouter les statuts des composants
        if self.store:
            account = self.store.get_account()
            status['account'] = {
                'value': float(account.portfolio_value) if account else 0,
                'cash': float(account.cash) if account else 0
            }
        
        if self.circuit_breaker:
            status['circuit_breaker'] = self.circuit_breaker.get_status()
        
        if self.strategy_runner:
            status['strategies'] = self.strategy_runner.get_status()
        
        if self.portfolio_manager:
            status['portfolio'] = self.portfolio_manager.get_state_summary()
        
        return status


def main():
    """Fonction principale pour lancer le paper trading"""
    logger.info("="*60)
    logger.info("PAPER TRADING SYSTEM v1.0")
    logger.info("="*60)
    
    try:
        # Créer et initialiser le moteur
        engine = PaperTradingEngine()
        
        if engine.initialize():
            # Démarrer le trading
            engine.start()
        else:
            logger.error("Échec de l'initialisation")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()