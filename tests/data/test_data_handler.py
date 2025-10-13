# test_data_handler.py
import sys
from pathlib import Path
import pytest
import pandas as pd
import pickle
from unittest.mock import patch, MagicMock, mock_open

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock dependencies BEFORE importing the module under test.
# This prevents real file system access or network calls when the module is first loaded.
mock_settings = MagicMock()
mock_settings.DATA_CACHE_ENABLED = True
mock_settings.LOG_LEVEL = (
    "INFO"  # Provide a valid string to prevent TypeError on import
)
mock_settings.DATA_DIR = Path("/tmp/fake_dir")  # This will be patched further in tests

sys.modules["config"] = MagicMock(settings=mock_settings)
sys.modules["monitoring.logger"] = MagicMock(
    setup_logger=MagicMock(return_value=MagicMock())
)

# Now, import the module to be tested
from data.data_handler import DataHandler


@pytest.fixture(autouse=True)
def mock_logger_autouse():
    """
    This fixture automatically mocks the logger imported by the data_handler module.
    It ensures all tests use the same mock logger without needing to pass it as an argument.
    """
    with patch("data.data_handler.logger", MagicMock()) as mock_log:
        yield mock_log


@pytest.fixture
def sample_ohlcv_df():
    """Provides a sample DataFrame similar to what yfinance returns."""
    data = {
        "Open": [100, 102, 101],
        "High": [103, 104, 102],
        "Low": [99, 101, 100],
        "Close": [102, 103, 101],
        "Volume": [1000, 1200, 1100],
        "Adj Close": [102, 103, 101],
    }
    return pd.DataFrame(
        data, index=pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"])
    )


@pytest.fixture
def standardized_df():
    """Provides a standardized version of the sample DataFrame."""
    data = {
        "open": [100, 102, 101],
        "high": [103, 104, 102],
        "low": [99, 101, 100],
        "close": [102, 103, 101],
        "volume": [1000, 1200, 1100],
    }
    return pd.DataFrame(
        data, index=pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"])
    )


class TestDataHandler:
    """Test suite for the DataHandler class."""

    # 1. __init__ tests
    def test_init_nominal_cache_enabled(self, tmp_path, mock_logger_autouse):
        """Test nominal initialization with cache enabled."""
        with patch("data.data_handler.settings.DATA_DIR", tmp_path):
            handler = DataHandler(data_source="yfinance", cache_enabled=True)
            assert handler.data_source == "yfinance"
            assert handler.cache_enabled is True
            assert handler.cache_dir == tmp_path
            mock_logger_autouse.info.assert_called_with(
                "DataHandler initialisé: source=yfinance, cache=True"
            )

    def test_init_cache_disabled_by_argument(self, mock_logger_autouse):
        """Test initialization with cache disabled via argument."""
        handler = DataHandler(cache_enabled=False)
        assert handler.cache_enabled is False
        mock_logger_autouse.info.assert_called_with(
            "DataHandler initialisé: source=yfinance, cache=False"
        )

    def test_init_cache_disabled_by_settings(self, mock_logger_autouse):
        """Test initialization with cache disabled via global settings."""
        with patch("data.data_handler.settings.DATA_CACHE_ENABLED", False):
            handler = DataHandler(cache_enabled=True)
            assert handler.cache_enabled is False
            mock_logger_autouse.info.assert_called_with(
                "DataHandler initialisé: source=yfinance, cache=False"
            )

    # 2. fetch_data tests
    def test_fetch_data_from_cache_hit_nominal(
        self, mocker, standardized_df, mock_logger_autouse
    ):
        """Test nominal case for fetch_data with a cache hit."""
        handler = DataHandler()
        mocker.patch.object(handler, "_load_from_cache", return_value=standardized_df)
        mocker.patch.object(handler, "_fetch_yfinance")

        result_df = handler.fetch_data("AAPL", "2023-01-01", "2023-01-03")

        handler._load_from_cache.assert_called_once_with(
            "AAPL", "2023-01-01", "2023-01-03", "1d"
        )
        handler._fetch_yfinance.assert_not_called()
        pd.testing.assert_frame_equal(result_df, standardized_df)
        mock_logger_autouse.info.assert_any_call(
            "✓ Données chargées depuis le cache: AAPL"
        )

    def test_fetch_data_from_network_cache_miss(
        self, mocker, sample_ohlcv_df, standardized_df, mock_logger_autouse
    ):
        """Test nominal case for fetch_data with a cache miss, fetching from network."""
        handler = DataHandler()
        mocker.patch.object(handler, "_load_from_cache", return_value=None)
        mocker.patch.object(handler, "_fetch_yfinance", return_value=sample_ohlcv_df)
        mocker.patch.object(handler, "_save_to_cache")

        result_df = handler.fetch_data("MSFT", "2023-01-01", "2023-01-03")

        handler._load_from_cache.assert_called_once()
        handler._fetch_yfinance.assert_called_once()
        handler._save_to_cache.assert_called_once()
        pd.testing.assert_frame_equal(result_df, standardized_df)
        mock_logger_autouse.info.assert_any_call("✓ 3 barres téléchargées pour MSFT")

    def test_fetch_data_network_returns_empty(self, mocker, mock_logger_autouse):
        """Test edge case where yfinance returns an empty DataFrame."""
        handler = DataHandler(cache_enabled=False)
        mocker.patch.object(handler, "_fetch_yfinance", return_value=pd.DataFrame())

        result = handler.fetch_data("EMPTY", "2023-01-01", "2023-01-03")

        assert result is None
        mock_logger_autouse.warning.assert_called_with(
            "Aucune donnée récupérée pour EMPTY"
        )

    def test_fetch_data_network_returns_none(self, mocker, mock_logger_autouse):
        """Test edge case where yfinance returns None."""
        handler = DataHandler(cache_enabled=False)
        mocker.patch.object(handler, "_fetch_yfinance", return_value=None)

        result = handler.fetch_data("NONE", "2023-01-01", "2023-01-03")

        assert result is None
        mock_logger_autouse.warning.assert_called_with(
            "Aucune donnée récupérée pour NONE"
        )

    def test_fetch_data_unsupported_source_error(self, mock_logger_autouse):
        """Test error case where unsupported source is caught and logged."""
        handler = DataHandler(data_source="invalid_source", cache_enabled=False)
        result = handler.fetch_data("TSLA", "2023-01-01", "2023-01-03")
        assert result is None
        mock_logger_autouse.error.assert_called_with(
            "Erreur lors du téléchargement de TSLA: Source de données non supportée: invalid_source"
        )

    def test_fetch_data_network_exception_error(self, mocker, mock_logger_autouse):
        """Test error case when _fetch_yfinance raises an exception."""
        handler = DataHandler(cache_enabled=False)
        mocker.patch.object(
            handler, "_fetch_yfinance", side_effect=Exception("Network Error")
        )

        result = handler.fetch_data("ERROR", "2023-01-01", "2023-01-03")

        assert result is None
        mock_logger_autouse.error.assert_called_with(
            "Erreur lors du téléchargement de ERROR: Network Error"
        )

    def test_get_cache_filename_format(self, tmp_path):
        """Test the format of the generated cache filename using a temporary path."""
        handler = DataHandler()
        handler.cache_dir = tmp_path
        filename = handler._get_cache_filename("UBER", "2022-01-01", "2022-12-31", "1h")
        expected = tmp_path / "UBER_2022-01-01_2022-12-31_1h.pkl"
        assert filename == expected

    def test_save_to_cache_nominal(self, mocker, standardized_df, tmp_path):
        """Test nominal case for saving data to cache."""
        mocker.patch("data.data_handler.pickle.dump")
        mock_file_open = mock_open()
        mocker.patch("builtins.open", mock_file_open)

        handler = DataHandler()
        handler.cache_dir = tmp_path
        handler._save_to_cache(
            standardized_df, "SAVE", "2023-01-01", "2023-01-03", "1d"
        )

        expected_path = tmp_path / "SAVE_2023-01-01_2023-01-03_1d.pkl"
        mock_file_open.assert_called_once_with(expected_path, "wb")
        pickle.dump.assert_called_once_with(standardized_df, mock_file_open())

    def test_save_to_cache_exception_error(
        self, mocker, standardized_df, mock_logger_autouse
    ):
        """Test error case when saving to cache fails."""
        mocker.patch("data.data_handler.pickle.dump", side_effect=IOError("Disk full"))
        mocker.patch("builtins.open", mock_open())

        handler = DataHandler()
        handler._save_to_cache(
            standardized_df, "FAIL", "2023-01-01", "2023-01-03", "1d"
        )
        mock_logger_autouse.warning.assert_called_with(
            "Impossible de sauvegarder le cache: Disk full"
        )

    def test_load_from_cache_exception_error(self, mocker, mock_logger_autouse):
        """Test error case when loading a corrupted cache file."""
        mocker.patch("pathlib.Path.exists", return_value=True)
        mocker.patch(
            "data.data_handler.pickle.load",
            side_effect=pickle.UnpicklingError("Corrupted file"),
        )
        mocker.patch("builtins.open", mock_open(read_data=b"corrupted"))

        handler = DataHandler()
        result = handler._load_from_cache("CORRUPT", "2023-01-01", "2023-01-03", "1d")

        assert result is None
        mock_logger_autouse.debug.assert_called_with(
            "Cache non disponible: Corrupted file"
        )

    def test_fetch_multiple_nominal(self, mocker, standardized_df, mock_logger_autouse):
        """Test nominal case for fetching multiple symbols."""
        handler = DataHandler(cache_enabled=False)
        mocker.patch.object(handler, "fetch_data", return_value=standardized_df)

        symbols = ["AAPL", "MSFT"]
        data_dict = handler.fetch_multiple(symbols, "2023-01-01", "2023-01-03")

        assert handler.fetch_data.call_count == 2
        assert list(data_dict.keys()) == symbols
        pd.testing.assert_frame_equal(data_dict["AAPL"], standardized_df)
        mock_logger_autouse.info.assert_called_with(
            "Données récupérées pour 2/2 symboles"
        )

    def test_fetch_multiple_partial_failure(
        self, mocker, standardized_df, mock_logger_autouse
    ):
        """Test edge case where some symbols fail to fetch."""
        handler = DataHandler(cache_enabled=False)
        mocker.patch.object(
            handler, "fetch_data", side_effect=[standardized_df, None, standardized_df]
        )

        symbols = ["AAPL", "FAIL", "GOOG"]
        data_dict = handler.fetch_multiple(symbols, "2023-01-01", "2023-01-03")

        assert handler.fetch_data.call_count == 3
        assert len(data_dict) == 2
        assert "FAIL" not in data_dict
        mock_logger_autouse.info.assert_called_with(
            "Données récupérées pour 2/3 symboles"
        )

    def test_fetch_multiple_empty_list_edge_case(self, mocker, mock_logger_autouse):
        """Test edge case with an empty list of symbols."""
        handler = DataHandler()
        mocker.patch.object(handler, "fetch_data")

        data_dict = handler.fetch_multiple([], "2023-01-01", "2023-01-03")

        assert data_dict == {}
        handler.fetch_data.assert_not_called()
        mock_logger_autouse.info.assert_called_with(
            "Données récupérées pour 0/0 symboles"
        )
