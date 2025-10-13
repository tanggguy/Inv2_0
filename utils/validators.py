"""
Validateurs de données et paramètres
"""

import pandas as pd
from datetime import datetime


def validate_dataframe(df, required_columns=None):
    """
    Valide qu'un DataFrame a les colonnes requises

    Args:
        df: DataFrame à valider
        required_columns: Liste des colonnes requises

    Returns:
        True si valide, sinon lève une exception
    """
    if df is None or df.empty:
        raise ValueError("DataFrame vide ou None")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Colonnes manquantes: {missing}")

    # Vérifier l'index datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("L'index doit être un DatetimeIndex")

    return True


def validate_date_format(date_string):
    """
    Valide le format d'une date (YYYY-MM-DD)

    Args:
        date_string: String de date

    Returns:
        datetime object si valide
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Format de date invalide: {date_string}. Utilisez YYYY-MM-DD")


def validate_symbol(symbol):
    """
    Valide un symbole boursier

    Args:
        symbol: Symbole à valider

    Returns:
        True si valide
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbole invalide")

    # Symbole doit être alphanumérique
    if not symbol.replace(".", "").replace("-", "").isalnum():
        raise ValueError(f"Symbole invalide: {symbol}")

    return True


def validate_risk_parameters(params):
    """
    Valide les paramètres de risque

    Args:
        params: Dict de paramètres

    Returns:
        True si valide
    """
    if (
        params.get("max_position_size", 0) > 1
        or params.get("max_position_size", 0) <= 0
    ):
        raise ValueError("max_position_size doit être entre 0 et 1")

    if params.get("max_risk_per_trade", 0) > 0.1:
        raise ValueError("max_risk_per_trade ne devrait pas dépasser 0.1 (10%)")

    return True
