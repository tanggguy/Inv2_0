"""
Configuration du module Paper Trading avec Alpaca
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAPER_TRADING_CONFIG = {
    # ========== ALPACA CONFIGURATION ==========
    "alpaca": {
        "api_key": os.getenv("ALPACA_API_KEY"),
        "secret_key": os.getenv("ALPACA_SECRET_KEY"),
        "base_url": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        "data_url": os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets"),
        "data_feed": os.getenv("ALPACA_DATA_FEED", "iex"),  # 'iex' ou 'sip'
        "retry_attempts": 3,
        "timeout": 30,
    },
    # ========== DONNÉES TEMPS RÉEL ==========
    "data": {
        "timeframe": "1H",  # Barres 1 heure
        "compression": 1,
        "historical_days": 100,  # Jours d'historique à charger
        "buffer_size": 200,  # Nombre de barres en mémoire
        "reconnect_attempts": 5,
        "reconnect_delay": 5,  # Délai entre tentatives (secondes)
        "websocket_ping_interval": 30,
        "cache_enabled": True,
    },
    # ========== MULTI-STRATÉGIES ==========
    "strategies": [
        {
            "name": "MovingAverage",
            "enabled": False,
            "symbols": ["BTC-USD", "MSFT", "GOOGL"],
            "capital_allocation": 50000,
            "max_positions": 3,
            "params": {
                "ma_period": 20,
                "ma_fast": 10,
                "ma_slow": 30,
                "stop_loss_pct": 0.02,
                "take_profit_pct": 0.05,
            },
        },
        {
            "name": "RSITrailingStop",
            "enabled": True,
            "symbols": ["NVDA", "AMZN", "BTC-USD"],
            "capital_allocation": 30000,
            "max_positions": 2,
            "params": {
                "rsi_period": 10,
                "rsi_oversold": 30,
                "rsi_overbought": 60,
                "stop_loss_pct": 0.03,
                "trailing_stop_pct": 0.02,
                "use_take_profit": False,
                "use_stop_loss": True,
                "use_trailing_stop": True,
                "printlog": False,
            },
        },
        {
            "name": "MaRSI",
            "enabled": False,
            "symbols": ["SPY", "QQQ"],
            "capital_allocation": 20000,
            "max_positions": 2,
            "params": {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
        },
    ],
    # ========== CIRCUIT BREAKERS ==========
    "circuit_breakers": {
        "enabled": True,
        "max_drawdown_pct": 0.20,  # 20% drawdown max
        "max_daily_trades": 50,
        "max_trades_per_symbol": 10,
        "max_consecutive_losses": 5,
        "max_daily_loss_pct": 0.05,  # 5% perte max par jour
        "pause_duration_minutes": 60,
        "market_hours_only": True,
        "pre_market_allowed": False,
        "after_hours_allowed": False,
        "check_interval_seconds": 60,
    },
    # ========== SAUVEGARDE ÉTAT PORTEFEUILLE ==========
    "portfolio_state": {
        "enabled": True,
        "save_interval_seconds": 300,  # Toutes les 5 minutes
        "backup_dir": Path("data_cache/portfolio_states"),
        "max_backups": 100,
        "rotate_backups": True,
        "compression": True,  # Compression gzip des backups
        "save_on_trade": True,
        "save_on_shutdown": True,
    },
    # ========== NOTIFICATIONS ==========
    "notifications": {
        "telegram_enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "telegram_on_trade": True,
        "telegram_on_breaker": True,
        "telegram_on_error": True,
        "telegram_daily_summary": True,
        "telegram_summary_time": "16:00",  # Heure du résumé quotidien
        "email_enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "email_from": os.getenv("EMAIL_FROM"),
        "email_to": os.getenv("EMAIL_TO"),
        "email_smtp_server": os.getenv("EMAIL_SMTP_SERVER"),
        "email_smtp_port": os.getenv("EMAIL_SMTP_PORT", 587),
        "email_username": os.getenv("EMAIL_USERNAME"),
        "email_password": os.getenv("EMAIL_PASSWORD"),
        "email_daily_summary": False,
    },
    # ========== MONITORING ==========
    "monitoring": {
        "dashboard_enabled": True,
        "dashboard_port": 8501,
        "metrics_interval": 60,  # Mise à jour métriques (secondes)
        "performance_tracking": True,
        "log_trades_to_db": True,
        "database_path": Path("data_cache/paper_trading.db"),
    },
    # ========== EXÉCUTION ==========
    "execution": {
        "order_timeout_seconds": 30,
        "partial_fill_handling": "wait",  # 'wait' ou 'cancel'
        "slippage_model": "fixed",  # 'fixed' ou 'percentage'
        "slippage_value": 0.0005,  # 0.05%
        "order_size_rounding": True,
        "min_order_value": 100,  # Valeur minimale d'ordre en $
        "max_position_pct": 0.25,  # 25% max par position
    },
    # ========== HEURES DE MARCHÉ ==========
    "market_hours": {
        "timezone": "US/Eastern",
        "regular_open": "09:30",
        "regular_close": "16:00",
        "pre_market_open": "04:00",
        "pre_market_close": "09:30",
        "after_hours_open": "16:00",
        "after_hours_close": "20:00",
        "trading_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    },
}


def get_paper_config():
    """Retourne la configuration complète du paper trading"""
    return PAPER_TRADING_CONFIG


def validate_config():
    """Valide la configuration"""
    config = PAPER_TRADING_CONFIG

    # Vérifier les clés API Alpaca
    if not config["alpaca"]["api_key"] or not config["alpaca"]["secret_key"]:
        raise ValueError("Les clés API Alpaca sont requises dans le fichier .env")

    # Vérifier l'allocation de capital
    total_allocation = sum(
        s["capital_allocation"] for s in config["strategies"] if s["enabled"]
    )
    if total_allocation <= 0:
        raise ValueError(
            "Au moins une stratégie doit être activée avec du capital alloué"
        )

    # Créer les dossiers nécessaires
    config["portfolio_state"]["backup_dir"].mkdir(parents=True, exist_ok=True)

    return True
