"""
Adaptateurs pour différentes sources de données
"""
import backtrader as bt
import pandas as pd


class PandasData(bt.feeds.PandasData):
    """
    Feed Backtrader depuis un DataFrame pandas
    """
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )


def create_data_feed(df, name="data"):
    """
    Crée un feed Backtrader depuis un DataFrame
    
    Args:
        df: DataFrame avec colonnes OHLCV et index datetime
        name: Nom du feed
    
    Returns:
        PandasData feed
    """
    # Vérifier que l'index est datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Créer le feed
    data_feed = PandasData(
        dataname=df,
        name=name
    )
    
    return data_feed
