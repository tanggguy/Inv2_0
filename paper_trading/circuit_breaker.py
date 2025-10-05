"""
Circuit Breaker - Système de protection et gestion des risques
"""
from datetime import datetime, timedelta
import threading
from collections import deque
import pytz
from monitoring.logger import setup_logger

logger = setup_logger("circuit_breaker")


class CircuitBreaker:
    """
    Système de circuit breaker pour protéger le capital
    Arrête le trading en cas de conditions dangereuses
    """
    
    def __init__(self, config, notification_manager=None):
        """
        Initialise le circuit breaker
        
        Args:
            config: Configuration du paper trading
            notification_manager: Gestionnaire de notifications (optionnel)
        """
        self.config = config['circuit_breakers']
        self.notification_manager = notification_manager
        
        # État des breakers
        self.breakers_status = {
            'drawdown': {'triggered': False, 'value': 0, 'timestamp': None},
            'daily_trades': {'triggered': False, 'value': 0, 'timestamp': None},
            'consecutive_losses': {'triggered': False, 'value': 0, 'timestamp': None},
            'daily_loss': {'triggered': False, 'value': 0, 'timestamp': None},
            'market_hours': {'triggered': False, 'value': None, 'timestamp': None},
        }
        
        # Historique des trades
        self.trade_history = deque(maxlen=100)
        self.daily_trades = {}
        self.consecutive_losses = 0
        
        # Valeurs de référence
        self.initial_capital = 0
        self.peak_value = 0
        self.daily_starting_value = 0
        self.last_check_time = None
        
        # États de pause
        self.paused = False
        self.pause_until = None
        
        # Thread de vérification
        self._check_thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        logger.info("CircuitBreaker initialisé")
    
    def start(self, initial_capital):
        """Démarre le circuit breaker"""
        self.initial_capital = initial_capital
        self.peak_value = initial_capital
        self.daily_starting_value = initial_capital
        
        if self.config['enabled']:
            self._stop_event.clear()
            self._check_thread = threading.Thread(target=self._check_loop)
            self._check_thread.daemon = True
            self._check_thread.start()
            logger.info(f"Circuit breaker démarré - Capital initial: ${initial_capital:.2f}")
    
    def stop(self):
        """Arrête le circuit breaker"""
        if self._check_thread:
            self._stop_event.set()
            self._check_thread.join(timeout=5)
            self._check_thread = None
            logger.info("Circuit breaker arrêté")
    
    def _check_loop(self):
        """Boucle de vérification périodique"""
        check_interval = self.config.get('check_interval_seconds', 60)
        
        while not self._stop_event.is_set():
            try:
                if self._stop_event.wait(check_interval):
                    break
                
                # Vérifier les heures de marché
                if self.config.get('market_hours_only', True):
                    self._check_market_hours()
                
                # Réinitialiser les compteurs quotidiens si nouveau jour
                self._reset_daily_counters()
                
                # Vérifier si la pause est terminée
                self._check_pause_status()
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de vérification: {e}")
    
    def check_conditions(self, account_value, positions=None):
        """
        Vérifie toutes les conditions du circuit breaker
        
        Args:
            account_value: Valeur actuelle du compte
            positions: Positions actuelles (optionnel)
            
        Returns:
            bool: True si le trading est autorisé, False sinon
        """
        if not self.config['enabled']:
            return True
        
        with self._lock:
            # Si en pause, vérifier si c'est terminé
            if self.paused:
                if self.pause_until and datetime.now() > self.pause_until:
                    self._reset_pause()
                else:
                    return False
            
            # Vérifier le drawdown
            if self._check_drawdown(account_value):
                return False
            
            # Vérifier la perte quotidienne
            if self._check_daily_loss(account_value):
                return False
            
            # Vérifier les heures de marché
            if not self._is_market_open():
                return False
            
            return True
    
    def _check_drawdown(self, current_value):
        """Vérifie le drawdown maximum"""
        # Mettre à jour le pic
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        # Calculer le drawdown
        drawdown = (self.peak_value - current_value) / self.peak_value if self.peak_value > 0 else 0
        
        self.breakers_status['drawdown']['value'] = drawdown
        
        # Vérifier le seuil
        if drawdown > self.config['max_drawdown_pct']:
            if not self.breakers_status['drawdown']['triggered']:
                self.breakers_status['drawdown']['triggered'] = True
                self.breakers_status['drawdown']['timestamp'] = datetime.now()
                self._trigger_breaker('drawdown', f"Drawdown de {drawdown:.1%} > {self.config['max_drawdown_pct']:.1%}")
            return True
        
        return False
    
    def _check_daily_loss(self, current_value):
        """Vérifie la perte quotidienne maximale"""
        daily_loss = (self.daily_starting_value - current_value) / self.daily_starting_value if self.daily_starting_value > 0 else 0
        
        self.breakers_status['daily_loss']['value'] = daily_loss
        
        # Vérifier le seuil
        if daily_loss > self.config['max_daily_loss_pct']:
            if not self.breakers_status['daily_loss']['triggered']:
                self.breakers_status['daily_loss']['triggered'] = True
                self.breakers_status['daily_loss']['timestamp'] = datetime.now()
                self._trigger_breaker('daily_loss', f"Perte quotidienne de {daily_loss:.1%} > {self.config['max_daily_loss_pct']:.1%}")
            return True
        
        return False
    
    def _check_market_hours(self):
        """Vérifie si on est dans les heures de marché"""
        if not self.config.get('market_hours_only', True):
            return True
        
        now = datetime.now(pytz.timezone('US/Eastern'))
        current_time = now.time()
        weekday = now.strftime('%A')
        
        # Vérifier le jour de trading
        trading_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        if weekday not in trading_days:
            self.breakers_status['market_hours']['triggered'] = True
            self.breakers_status['market_hours']['value'] = 'Weekend'
            return False
        
        # Heures régulières : 9:30 - 16:00 ET
        market_open = datetime.strptime('09:30', '%H:%M').time()
        market_close = datetime.strptime('16:00', '%H:%M').time()
        
        # Pre-market : 4:00 - 9:30 ET
        if self.config.get('pre_market_allowed', False):
            pre_market_open = datetime.strptime('04:00', '%H:%M').time()
            if pre_market_open <= current_time < market_open:
                return True
        
        # After-hours : 16:00 - 20:00 ET
        if self.config.get('after_hours_allowed', False):
            after_hours_close = datetime.strptime('20:00', '%H:%M').time()
            if market_close <= current_time < after_hours_close:
                return True
        
        # Heures régulières
        if market_open <= current_time < market_close:
            self.breakers_status['market_hours']['triggered'] = False
            return True
        
        self.breakers_status['market_hours']['triggered'] = True
        self.breakers_status['market_hours']['value'] = f'Fermé ({current_time})'
        return False
    
    def _is_market_open(self):
        """Retourne True si le marché est ouvert"""
        return self._check_market_hours()
    
    def record_trade(self, symbol, side, quantity, price, pnl=None):
        """
        Enregistre un trade
        
        Args:
            symbol: Symbole tradé
            side: 'buy' ou 'sell'
            quantity: Quantité
            price: Prix d'exécution
            pnl: P&L si c'est une vente (optionnel)
        """
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'pnl': pnl
        }
        
        with self._lock:
            # Ajouter à l'historique
            self.trade_history.append(trade)
            
            # Compter les trades quotidiens
            today = datetime.now().date()
            if today not in self.daily_trades:
                self.daily_trades[today] = []
            self.daily_trades[today].append(trade)
            
            # Vérifier le nombre de trades quotidiens
            if len(self.daily_trades[today]) > self.config['max_daily_trades']:
                if not self.breakers_status['daily_trades']['triggered']:
                    self.breakers_status['daily_trades']['triggered'] = True
                    self.breakers_status['daily_trades']['timestamp'] = datetime.now()
                    self._trigger_breaker('daily_trades', 
                        f"{len(self.daily_trades[today])} trades > {self.config['max_daily_trades']} max")
            
            # Vérifier les pertes consécutives
            if pnl is not None and pnl < 0:
                self.consecutive_losses += 1
                
                if self.consecutive_losses >= self.config['max_consecutive_losses']:
                    if not self.breakers_status['consecutive_losses']['triggered']:
                        self.breakers_status['consecutive_losses']['triggered'] = True
                        self.breakers_status['consecutive_losses']['timestamp'] = datetime.now()
                        self._trigger_breaker('consecutive_losses',
                            f"{self.consecutive_losses} pertes consécutives")
            elif pnl is not None and pnl > 0:
                self.consecutive_losses = 0
        
        logger.info(f"Trade enregistré: {side} {quantity} {symbol} @ ${price:.2f}")
    
    def _trigger_breaker(self, breaker_type, message):
        """Déclenche un circuit breaker"""
        self.paused = True
        self.pause_until = datetime.now() + timedelta(minutes=self.config['pause_duration_minutes'])
        
        alert_msg = f"🚨 CIRCUIT BREAKER DÉCLENCHÉ - {breaker_type.upper()}\n{message}\nTrading suspendu jusqu'à {self.pause_until.strftime('%H:%M:%S')}"
        logger.warning(alert_msg)
        
        # Envoyer notification si configuré
        if self.notification_manager and self.config.get('telegram_on_breaker', True):
            self.notification_manager.send_alert(alert_msg)
    
    def _reset_pause(self):
        """Réinitialise l'état de pause"""
        self.paused = False
        self.pause_until = None
        
        # Réinitialiser certains breakers
        for breaker in ['daily_trades', 'consecutive_losses']:
            self.breakers_status[breaker]['triggered'] = False
        
        logger.info("Circuit breaker réinitialisé - Trading autorisé")
    
    def _reset_daily_counters(self):
        """Réinitialise les compteurs quotidiens"""
        now = datetime.now()
        
        # Nouveau jour ?
        if self.last_check_time and self.last_check_time.date() != now.date():
            # Nettoyer les anciens trades
            today = now.date()
            self.daily_trades = {today: self.daily_trades.get(today, [])}
            
            # Réinitialiser les breakers quotidiens
            self.breakers_status['daily_trades']['triggered'] = False
            self.breakers_status['daily_trades']['value'] = 0
            self.breakers_status['daily_loss']['triggered'] = False
            
            logger.info("Compteurs quotidiens réinitialisés")
        
        self.last_check_time = now
    
    def _check_pause_status(self):
        """Vérifie si la pause est terminée"""
        if self.paused and self.pause_until:
            if datetime.now() > self.pause_until:
                self._reset_pause()
    
    def get_status(self):
        """Retourne le statut actuel des circuit breakers"""
        with self._lock:
            status = {
                'paused': self.paused,
                'pause_until': self.pause_until.isoformat() if self.pause_until else None,
                'breakers': {}
            }
            
            for name, breaker in self.breakers_status.items():
                status['breakers'][name] = {
                    'triggered': breaker['triggered'],
                    'value': breaker['value'],
                    'timestamp': breaker['timestamp'].isoformat() if breaker['timestamp'] else None
                }
            
            # Ajouter des statistiques
            today = datetime.now().date()
            status['stats'] = {
                'daily_trades': len(self.daily_trades.get(today, [])),
                'consecutive_losses': self.consecutive_losses,
                'current_drawdown': self.breakers_status['drawdown']['value'],
                'daily_pnl': self.breakers_status['daily_loss']['value']
            }
            
            return status
    
    def override_pause(self):
        """Force la reprise du trading (override manuel)"""
        logger.warning("Override manuel du circuit breaker")
        self._reset_pause()