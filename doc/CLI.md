## Optimisation
# Dashboard optuna
optuna-dashboard sqlite:///results/optuna_studies/optuna.db

# Optimisation optuna
python scripts/run_optuna_from_yaml.py config/optuna_SqueezeMomentumStrategy.yaml  
python scripts/run_optuna_from_yaml.py config/optuna_MaRSI.yaml  
python scripts/run_optuna_from_yaml.py config/optuna_RSI.yaml  


## Backtest
# Multi-symboles
python main.py --strategy MaSuperStrategie --symbols AAPL MSFT GOOGL AMZN

# Avec capital initial personnalisé
python main.py --strategy MovingAverage --symbols AAPL --capital 50000

# Avec graphiques

python main.py --strategy RSITrailingStop --symbols NKE --start-date 2018-12-31 --end-date 2025-10-06
# Mode verbose (plus de logs)
python main.py --strategy RSI --symbols TSLA --verbose

# Symbols
AAPL MSFT GOOGL AMZN NVDA META TSLA
JPM BAC DIS NKE
SPY QQQ DIA IWM 
ETH-USD BTC-USD
MC.PA OR.PA SAN.PA TTE.PA
EURUSD=X GBPUSD=X USDJPY=X 

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

# Strategies
MovingAverage 
RSI 
MACrossoverAdvanced
RSITrailingStop
BreakoutATRStop
MomentumMultipleStops
MaRSI
MeanReversionStrategy
SqueezeMomentumStrategy