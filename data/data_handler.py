"""
Gestionnaire de données de marché
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
import pickle

from config import settings
from monitoring.logger import setup_logger

logger = setup_logger("data_handler")


class DataHandler:
    """Gère le téléchargement et le stockage des données de marché"""

    def __init__(self, data_source="yfinance", cache_enabled=True):
        self.data_source = data_source
        self.cache_enabled = cache_enabled and settings.DATA_CACHE_ENABLED
        self.cache_dir = settings.DATA_DIR

        logger.info(
            f"DataHandler initialisé: source={data_source}, cache={self.cache_enabled}"
        )

    def fetch_data(self, symbol, start_date, end_date, interval="1d"):
        """
        Récupère les données pour un symbole

        Args:
            symbol: Symbole du ticker (ex: AAPL)
            start_date: Date de début (YYYY-MM-DD)
            end_date: Date de fin (YYYY-MM-DD)
            interval: Intervalle (1d, 1h, etc.)

        Returns:
            DataFrame avec colonnes OHLCV
        """
        # Vérifier le cache
        if self.cache_enabled:
            cached_data = self._load_from_cache(symbol, start_date, end_date, interval)
            if cached_data is not None:
                logger.info(f"✓ Données chargées depuis le cache: {symbol}")
                return cached_data

        logger.info(f"Téléchargement des données: {symbol} ({start_date} → {end_date})")

        try:
            if self.data_source == "yfinance":
                data = self._fetch_yfinance(symbol, start_date, end_date, interval)
            else:
                raise ValueError(f"Source de données non supportée: {self.data_source}")

            if data is not None and not data.empty:
                # Standardiser les noms de colonnes
                data = self._standardize_columns(data)

                # Sauvegarder en cache
                if self.cache_enabled:
                    self._save_to_cache(data, symbol, start_date, end_date, interval)

                logger.info(f"✓ {len(data)} barres téléchargées pour {symbol}")
                return data
            else:
                logger.warning(f"Aucune donnée récupérée pour {symbol}")
                return None

        except Exception as e:
            logger.error(f"Erreur lors du téléchargement de {symbol}: {e}")
            return None

    def _fetch_yfinance(self, symbol, start_date, end_date, interval):
        """Télécharge depuis Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        return data

    def _standardize_columns(self, df):
        """Standardise les noms de colonnes"""
        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close",
        }

        df = df.rename(columns=column_mapping)

        # Garder seulement les colonnes essentielles
        required_cols = ["open", "high", "low", "close", "volume"]
        available_cols = [col for col in required_cols if col in df.columns]

        return df[available_cols]

    def _get_cache_filename(self, symbol, start_date, end_date, interval):
        """Génère le nom du fichier cache"""
        return self.cache_dir / f"{symbol}_{start_date}_{end_date}_{interval}.pkl"

    def _save_to_cache(self, data, symbol, start_date, end_date, interval):
        """Sauvegarde les données en cache"""
        try:
            cache_file = self._get_cache_filename(
                symbol, start_date, end_date, interval
            )
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
            logger.debug(f"Cache sauvegardé: {cache_file.name}")
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder le cache: {e}")

    def _load_from_cache(self, symbol, start_date, end_date, interval):
        """Charge les données depuis le cache"""
        try:
            cache_file = self._get_cache_filename(
                symbol, start_date, end_date, interval
            )
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                return data
        except Exception as e:
            logger.debug(f"Cache non disponible: {e}")

        return None

    def fetch_multiple(self, symbols, start_date, end_date, interval="1d"):
        """Télécharge les données pour plusieurs symboles"""
        data_dict = {}

        for symbol in symbols:
            data = self.fetch_data(symbol, start_date, end_date, interval)
            if data is not None:
                data_dict[symbol] = data

        logger.info(f"Données récupérées pour {len(data_dict)}/{len(symbols)} symboles")
        return data_dict
