"""
Configuration globale du système de trading
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins du projet
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_cache"
LOGS_DIR = BASE_DIR / "logs"
RESULTS_DIR = BASE_DIR / "results" / "rapports_backtest"

# Créer les dossiers s'ils n'existent pas
for directory in [DATA_DIR, LOGS_DIR, RESULTS_DIR]:
    directory.mkdir(exist_ok=True)

# Mode de trading
TRADING_MODE = os.getenv("TRADING_MODE", "backtest")  # backtest, paper, live
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Capital et configuration de base
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))
COMMISSION = 0.001  # 0.1% par transaction

# Sources de données
DATA_SOURCE = os.getenv("DATA_SOURCE", "yfinance")
DATA_CACHE_ENABLED = os.getenv("DATA_CACHE_ENABLED", "true").lower() == "true"

# API Keys
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Alpaca Configuration
ALPACA_CONFIG = {
    "api_key": os.getenv("ALPACA_API_KEY"),
    "secret_key": os.getenv("ALPACA_SECRET_KEY"),
    "base_url": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
}

# Binance Configuration
BINANCE_CONFIG = {
    "api_key": os.getenv("BINANCE_API_KEY"),
    "secret_key": os.getenv("BINANCE_SECRET_KEY"),
}

# Risk Management
RISK_MANAGEMENT = {
    "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "0.1")),
    "max_risk_per_trade": float(os.getenv("MAX_RISK_PER_TRADE", "0.02")),
    "max_portfolio_risk": float(os.getenv("MAX_PORTFOLIO_RISK", "0.06")),
    "max_correlation": 0.7,
    "max_drawdown": 0.2,
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Telegram Notifications
TELEGRAM_CONFIG = {
    "enabled": False,
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
}

# Backtesting Configuration
BACKTEST_CONFIG = {
    "start_date": "2020-01-01",
    "end_date": "2024-12-31",
    "data_frequency": "15Min",  # 1d, 1h, 15m, etc.
    "slippage": 0.0005,  # 0.05%
}

# Stratégies disponibles
AVAILABLE_STRATEGIES = [
    "MovingAverage",
    "RSI",
    "MACD",
    "BollingerBands",
    "MeanReversionStrategy",
    "SqueezeMomentumStrategy",
    "RSITrailingStop",
    "BreakoutATRStop",
    "Custom",
]

# Symboles par défaut
DEFAULT_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN"]


def get_config():
    """Retourne la configuration complète"""
    return {
        "trading_mode": TRADING_MODE,
        "environment": ENVIRONMENT,
        "initial_capital": INITIAL_CAPITAL,
        "commission": COMMISSION,
        "risk_management": RISK_MANAGEMENT,
        "backtest": BACKTEST_CONFIG,
    }
