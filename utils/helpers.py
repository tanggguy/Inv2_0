"""
Fonctions utilitaires diverses
"""
import pandas as pd
from datetime import datetime, timedelta


def format_currency(amount, symbol='$'):
    """Formate un montant en devise"""
    return f"{symbol}{amount:,.2f}"


def format_percentage(value, decimals=2):
    """Formate un pourcentage"""
    return f"{value:.{decimals}f}%"


def calculate_returns(prices):
    """Calcule les rendements simples"""
    return prices.pct_change()


def calculate_log_returns(prices):
    """Calcule les rendements logarithmiques"""
    import numpy as np
    return np.log(prices / prices.shift(1))


def resample_data(df, timeframe='1D'):
    """
    Rééchantillonne les données OHLCV
    
    Args:
        df: DataFrame OHLCV
        timeframe: Nouvelle fréquence ('1D', '1H', etc.)
    
    Returns:
        DataFrame rééchantillonné
    """
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    return resampled.dropna()


def get_trading_days(start_date, end_date):
    """Calcule le nombre de jours de trading"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Approximation: 252 jours de trading par an
    days = (end - start).days
    return int(days * (252 / 365))


def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calcule le ratio de Sharpe
    
    Args:
        returns: Series de rendements
        risk_free_rate: Taux sans risque annuel
    
    Returns:
        Sharpe ratio
    """
    import numpy as np
    
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()


def calculate_max_drawdown(portfolio_values):
    """
    Calcule le drawdown maximum
    
    Args:
        portfolio_values: Series des valeurs du portefeuille
    
    Returns:
        Max drawdown en pourcentage
    """
    rolling_max = portfolio_values.expanding().max()
    drawdowns = (portfolio_values - rolling_max) / rolling_max
    return drawdowns.min() * 100
