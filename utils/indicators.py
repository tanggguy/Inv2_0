"""
Indicateurs techniques personnalisés
"""
import pandas as pd
import numpy as np


def calculate_rsi(data, period=14):
    """
    Calcule le RSI (Relative Strength Index)
    
    Args:
        data: Series de prix
        period: Période de calcul
    
    Returns:
        Series avec valeurs RSI
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(data, fast=12, slow=26, signal=9):
    """
    Calcule le MACD
    
    Args:
        data: Series de prix
        fast: Période EMA rapide
        slow: Période EMA lente
        signal: Période signal
    
    Returns:
        DataFrame avec MACD, signal et histogramme
    """
    exp1 = data.ewm(span=fast, adjust=False).mean()
    exp2 = data.ewm(span=slow, adjust=False).mean()
    
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    
    return pd.DataFrame({
        'macd': macd,
        'signal': signal_line,
        'histogram': histogram
    })


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """
    Calcule les bandes de Bollinger
    
    Args:
        data: Series de prix
        period: Période
        std_dev: Nombre d'écarts-types
    
    Returns:
        DataFrame avec bandes supérieure, moyenne et inférieure
    """
    middle_band = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return pd.DataFrame({
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    })


def calculate_atr(high, low, close, period=14):
    """
    Calcule l'Average True Range
    
    Args:
        high: Series des plus hauts
        low: Series des plus bas
        close: Series des clôtures
        period: Période
    
    Returns:
        Series avec valeurs ATR
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(high, low, close, period=14):
    """
    Calcule l'oscillateur stochastique
    
    Args:
        high: Series des plus hauts
        low: Series des plus bas
        close: Series des clôtures
        period: Période
    
    Returns:
        Series avec valeurs %K
    """
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    return k
