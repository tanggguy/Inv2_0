"""
Telegram Notifier - Système de notifications via Telegram
"""
import asyncio
import threading
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from monitoring.logger import setup_logger

logger = setup_logger("telegram_notifier")


class TelegramNotifier:
    """
    Gestionnaire de notifications Telegram
    Envoie des alertes et rapports via bot Telegram
    """
    
    def __init__(self, bot_token, chat_id):
        """
        Initialise le notifier Telegram
        
        Args:
            bot_token: Token du bot Telegram
            chat_id: ID du chat/canal de destination
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = None
        self._loop = None
        self._thread = None
        
        # Initialiser le bot
        try:
            self.bot = Bot(token=bot_token)
            self._start_async_loop()
            logger.info("TelegramNotifier initialisé")
        except Exception as e:
            logger.error(f"Erreur initialisation Telegram: {e}")
            self.bot = None
    
    def _start_async_loop(self):
        """Démarre une boucle asyncio dans un thread séparé"""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def send_message(self, message, parse_mode='Markdown'):
        """
        Envoie un message simple
        
        Args:
            message: Message à envoyer
            parse_mode: Format du message (Markdown ou HTML)
        """
        if not self.bot:
            logger.warning("Bot Telegram non initialisé")
            return False
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._send_message_async(message, parse_mode),
                self._loop
            )
            result = future.result(timeout=10)
            return result
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return False
    
    async def _send_message_async(self, message, parse_mode):
        """Envoie un message de manière asynchrone"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            logger.debug(f"Message envoyé: {message[:50]}...")
            return True
        except TelegramError as e:
            logger.error(f"Erreur Telegram: {e}")
            return False
    
    def send_alert(self, alert_message):
        """
        Envoie une alerte urgente
        
        Args:
            alert_message: Message d'alerte
        """
        # Ajouter emoji et timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"🚨 **ALERTE** [{timestamp}]\n\n{alert_message}"
        return self.send_message(formatted_message)
    
    def send_trade_notification(self, trade_info):
        """
        Envoie une notification de trade
        
        Args:
            trade_info: Dictionnaire avec les infos du trade
        """
        try:
            # Formater le message
            side = trade_info.get('side', '').upper()
            symbol = trade_info.get('symbol', '')
            quantity = trade_info.get('quantity', 0)
            price = trade_info.get('price', 0)
            strategy = trade_info.get('strategy', 'Unknown')
            
            # Choisir l'emoji
            emoji = "📈" if side == "BUY" else "📉"
            
            message = f"""{emoji} **TRADE EXÉCUTÉ**

**Stratégie:** {strategy}
**Action:** {side}
**Symbole:** {symbol}
**Quantité:** {quantity}
**Prix:** ${price:.2f}
**Valeur:** ${quantity * price:.2f}
**Heure:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            # Ajouter le P&L si c'est une vente
            if side == "SELL" and 'pnl' in trade_info:
                pnl = trade_info['pnl']
                pnl_emoji = "✅" if pnl > 0 else "❌"
                message += f"\n**P&L:** {pnl_emoji} ${pnl:+.2f}"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Erreur notification trade: {e}")
            return False
    
    def send_daily_summary(self, summary_data):
        """
        Envoie un résumé quotidien
        
        Args:
            summary_data: Données du résumé
        """
        try:
            message = f"""📊 **RÉSUMÉ QUOTIDIEN**
{datetime.now().strftime('%Y-%m-%d')}
{'='*30}

💰 **PORTEFEUILLE**
• Valeur: ${summary_data.get('portfolio_value', 0):,.2f}
• Cash: ${summary_data.get('cash', 0):,.2f}
• P&L Jour: ${summary_data.get('daily_pnl', 0):+,.2f}
• P&L Total: ${summary_data.get('total_pnl', 0):+,.2f}

📈 **TRADING**
• Trades Jour: {summary_data.get('daily_trades', 0)}
• Trades Total: {summary_data.get('total_trades', 0)}
• Win Rate: {summary_data.get('win_rate', 0):.1%}
• Sharpe Ratio: {summary_data.get('sharpe_ratio', 0):.2f}

📉 **RISQUES**
• Drawdown: {summary_data.get('drawdown', 0):.1%}
• Exposure: {summary_data.get('exposure', 0):.1%}
• Circuit Breakers: {"🟢 OK" if not summary_data.get('breakers_triggered') else "🔴 DÉCLENCHÉ"}
"""
            
            # Ajouter les performances par stratégie
            if 'strategies' in summary_data:
                message += "\n🎯 **STRATÉGIES**\n"
                for name, perf in summary_data['strategies'].items():
                    status = "✅" if perf.get('active') else "⏸️"
                    message += f"• {name}: {status} ${perf.get('pnl', 0):+,.2f} ({perf.get('trades', 0)} trades)\n"
            
            # Ajouter les positions ouvertes
            if 'positions' in summary_data and summary_data['positions']:
                message += "\n📦 **POSITIONS OUVERTES**\n"
                for pos in summary_data['positions'][:5]:  # Max 5 positions
                    message += f"• {pos['symbol']}: {pos['quantity']} @ ${pos['entry_price']:.2f} (P&L: ${pos.get('unrealized_pnl', 0):+.2f})\n"
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Erreur résumé quotidien: {e}")
            return False
    
    def send_error_notification(self, error_info):
        """
        Envoie une notification d'erreur
        
        Args:
            error_info: Information sur l'erreur
        """
        message = f"""❌ **ERREUR SYSTÈME**

**Type:** {error_info.get('type', 'Unknown')}
**Message:** {error_info.get('message', 'No details')}
**Composant:** {error_info.get('component', 'Unknown')}
**Heure:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ Vérifiez les logs pour plus de détails.
"""
        return self.send_alert(message)
    
    def send_circuit_breaker_alert(self, breaker_info):
        """
        Envoie une alerte de circuit breaker
        
        Args:
            breaker_info: Information sur le circuit breaker déclenché
        """
        message = f"""🚨 **CIRCUIT BREAKER DÉCLENCHÉ**

**Type:** {breaker_info.get('type', 'Unknown').upper()}
**Raison:** {breaker_info.get('reason', 'No details')}
**Valeur:** {breaker_info.get('value', 'N/A')}
**Seuil:** {breaker_info.get('threshold', 'N/A')}

⏸️ **Trading suspendu pour {breaker_info.get('pause_duration', 60)} minutes**

Action requise: Vérifiez les conditions du marché et les paramètres de risque.
"""
        return self.send_alert(message)
    
    def send_performance_update(self, perf_data):
        """
        Envoie une mise à jour de performance
        
        Args:
            perf_data: Données de performance
        """
        # Déterminer l'emoji basé sur la performance
        pnl = perf_data.get('pnl', 0)
        if pnl > 0:
            emoji = "🟢"
            trend = "PROFIT"
        elif pnl < 0:
            emoji = "🔴"
            trend = "PERTE"
        else:
            emoji = "⚪"
            trend = "NEUTRE"
        
        message = f"""{emoji} **PERFORMANCE UPDATE - {trend}**

**P&L Actuel:** ${pnl:+,.2f}
**Valeur Portfolio:** ${perf_data.get('portfolio_value', 0):,.2f}
**Rendement:** {perf_data.get('return_pct', 0):+.2%}
**Trades Aujourd'hui:** {perf_data.get('trades_today', 0)}

Mise à jour: {datetime.now().strftime('%H:%M:%S')}
"""
        return self.send_message(message)
    
    def send_startup_message(self, config_info):
        """
        Envoie un message au démarrage du système
        
        Args:
            config_info: Information de configuration
        """
        message = f"""🚀 **SYSTÈME DÉMARRÉ**

**Mode:** {config_info.get('mode', 'Unknown').upper()}
**Capital Initial:** ${config_info.get('initial_capital', 0):,.2f}
**Stratégies Actives:** {config_info.get('active_strategies', 0)}
**Circuit Breakers:** {"✅ Activés" if config_info.get('circuit_breakers_enabled') else "⚠️ Désactivés"}

Heure de démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Bonne chance! 🍀
"""
        return self.send_message(message)
    
    def send_shutdown_message(self, final_stats):
        """
        Envoie un message à l'arrêt du système
        
        Args:
            final_stats: Statistiques finales
        """
        message = f"""🛑 **SYSTÈME ARRÊTÉ**

**Durée Session:** {final_stats.get('duration', 'N/A')}
**P&L Final:** ${final_stats.get('final_pnl', 0):+,.2f}
**Trades Total:** {final_stats.get('total_trades', 0)}
**Erreurs:** {final_stats.get('errors', 0)}

Heure d'arrêt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

À bientôt! 👋
"""
        return self.send_message(message)
    
    def test_connection(self):
        """Teste la connexion Telegram"""
        try:
            test_message = "✅ Connexion Telegram établie avec succès!"
            return self.send_message(test_message)
        except Exception as e:
            logger.error(f"Test connexion échoué: {e}")
            return False
    
    def close(self):
        """Ferme les connexions"""
        if self._loop :
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("TelegramNotifier fermé")


# Fonction utilitaire pour tester les notifications
def test_telegram_notifications():
    """Teste l'envoi de notifications Telegram"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("❌ Variables TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID requises dans .env")
        return
    
    print("Test des notifications Telegram...")
    notifier = TelegramNotifier(bot_token, chat_id)
    
    # Test connexion
    if notifier.test_connection():
        print("✅ Connexion réussie")
        
        # Test notification de trade
        trade_info = {
            'side': 'buy',
            'symbol': 'AAPL',
            'quantity': 100,
            'price': 150.50,
            'strategy': 'MovingAverage'
        }
        notifier.send_trade_notification(trade_info)
        print("✅ Notification de trade envoyée")
        
        # Test alerte
        notifier.send_alert("Test d'alerte système")
        print("✅ Alerte envoyée")
        
        notifier.close()
    else:
        print("❌ Échec de la connexion")


if __name__ == "__main__":
    test_telegram_notifications()