optuna-dashboard sqlite:///optimization/optuna_studies/optuna.db


# Test simple sur Apple
python main.py --strategy MovingAverage --symbols AAPL

# Test RSI sur Tesla
python main.py --strategy RSI --symbols TSLA

# Multi-symboles
python main.py --strategy MaSuperStrategie --symbols AAPL MSFT GOOGL AMZN

# Période personnalisée
python main.py --strategy RSI --symbols AAPL \
  --start-date 2020-01-01 --end-date 2023-12-31

# Avec capital initial personnalisé
python main.py --strategy MovingAverage --symbols AAPL --capital 50000

# Avec graphiques
python main.py --strategy SqueezeMomentumStrategy --symbols AAPL --plot
python main.py --strategy RSITrailingStop --symbols BTC-USD --plot
python main.py --strategy SqueezeMomentumStrategy --symbols MSFT --start-date 2020-12-31 --end-date 2025-10-06
# Mode verbose (plus de logs)
python main.py --strategy RSI --symbols TSLA --verbose

AAPL MSFT GOOGL AMZN NVDA META TSLA
JPM BAC DIS NKE
SPY QQQ DIA IWM 
ETH-USD BTC-USD
MC.PA OR.PA SAN.PA TTE.PA
EURUSD=X GBPUSD=X USDJPY=X 

MovingAverage 
RSI 
MACrossoverAdvanced
RSITrailingStop
BreakoutATRStop
MomentumMultipleStops
MaSuperStrategie
MeanReversionStrategy
SqueezeMomentumStrategy

python optimization\cli\optimize_cli.py --interactive
symbols = [
    # US Large Cap
    "SPY",      # S&P 500 (top 500 entreprises US)
    "QQQ",      # NASDAQ 100 (top tech)
    "DIA",      # Dow Jones 30
    "IWM",      # Russell 2000 (small caps)
    
    # Secteurs diversifiés
    "XLF",      # Finance
    "XLE",      # Énergie
    "XLK",      # Tech
    "XLV",      # Santé
    "XLI",      # Industrie
    "XLY",      # Consumer Discretionary
    "XLP",      # Consumer Staples
    
    # International
    "EFA",      # Developed Markets (Europe, Asia)
    "EEM",      # Emerging Markets
    "VEA",      # FTSE Developed Markets
    
    # Bonds (diversification)
    "AGG",      # US Bonds
    "TLT",      # Long-term Treasury
]
symbols = ["SPY", "QQQ", "IWM", "XLF", "XLE"]
