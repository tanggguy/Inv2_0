import pandas as pd
import pytest
import backtrader as bt
from unittest.mock import call

# Assuming the source code is in a file named data_adapters.py
from data.data_fetcher import PandasData, create_data_feed


@pytest.fixture
def ohlcv_dataframe_datetime_index():
    """
    Fixture for a sample pandas DataFrame with a DatetimeIndex
    and standard OHLCV columns.
    """
    data = {
        "open": [100, 102, 101, 103],
        "high": [103, 104, 103, 105],
        "low": [99, 101, 100, 102],
        "close": [102, 103, 102, 104],
        "volume": [1000, 1500, 1200, 1800],
    }
    index = pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"])
    return pd.DataFrame(data, index=index)


@pytest.fixture
def ohlcv_dataframe_string_index():
    """
    Fixture for a sample pandas DataFrame with a string index
    that can be converted to datetime objects.
    """
    data = {
        "open": [200, 202],
        "high": [203, 204],
        "low": [199, 201],
        "close": [202, 203],
        "volume": [2000, 2500],
    }
    index = ["2024-05-10", "2024-05-11"]
    return pd.DataFrame(data, index=index)


class TestPandasData:
    """
    Tests for the PandasData class configuration.
    """

    def test_params_configuration(self, ohlcv_dataframe_datetime_index):
        """
        Tests that the params tuple is correctly configured as expected
        by Backtrader for a standard OHLCV feed.
        """
        feed = PandasData(dataname=ohlcv_dataframe_datetime_index)

        assert feed.p.datetime is None
        assert feed.p.open == "open"
        assert feed.p.high == "high"
        assert feed.p.low == "low"
        assert feed.p.close == "close"
        assert feed.p.volume == "volume"
        assert feed.p.openinterest == -1


class TestCreateDataFeed:
    """
    Tests for the create_data_feed factory function.
    """

    def test_nominal_case_with_datetime_index(
        self, ohlcv_dataframe_datetime_index, mocker
    ):
        """
        Tests successful data feed creation with a DataFrame that already
        has a DatetimeIndex.
        """
        # Arrange
        df = ohlcv_dataframe_datetime_index
        feed_name = "test_feed"
        mock_to_datetime = mocker.patch("pandas.to_datetime")

        # Act
        data_feed = create_data_feed(df, name=feed_name)

        # Assert
        assert isinstance(data_feed, PandasData)
        assert isinstance(data_feed, bt.feeds.PandasData)
        assert data_feed.p.dataname is df
        assert data_feed.p.name == feed_name
        mock_to_datetime.assert_not_called()

    def test_index_conversion_from_string_to_datetime(
        self, ohlcv_dataframe_string_index, mocker
    ):
        """
        Tests that the function correctly converts a string-based index
        to a DatetimeIndex before creating the feed.
        """
        # Arrange
        df = ohlcv_dataframe_string_index
        # FIX: Copy the original index before the function mutates the DataFrame.
        original_index = df.index.copy()
        spy_to_datetime = mocker.spy(pd, "to_datetime")

        # Act
        data_feed = create_data_feed(df)

        # Assert
        # Check that the final index is the correct type
        assert isinstance(data_feed.p.dataname.index, pd.DatetimeIndex)

        # Check that the conversion function was called with the original index
        spy_to_datetime.assert_called_once()
        called_with_arg = spy_to_datetime.call_args[0][0]
        pd.testing.assert_index_equal(called_with_arg, original_index)

    def test_edge_case_with_empty_dataframe(self):
        """
        Tests that the function handles an empty DataFrame gracefully without errors.
        """
        # Arrange
        empty_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"]
        ).set_index(pd.to_datetime([]))

        # Act
        data_feed = create_data_feed(empty_df, name="empty_feed")

        # Assert
        assert isinstance(data_feed, PandasData)
        assert data_feed.p.dataname.empty
        assert len(data_feed) == 0

    def test_error_case_with_unconvertible_index(self):
        """
        Tests that the function raises a ValueError when the DataFrame index
        cannot be converted to datetime.
        """
        # Arrange
        data = {
            "open": [100],
            "high": [100],
            "low": [100],
            "close": [100],
            "volume": [100],
        }
        df_invalid_index = pd.DataFrame(data, index=["not-a-date"])

        # Act & Assert
        expected_error_msg = (
            r"Unknown datetime string format, unable to parse: not-a-date"
        )
        with pytest.raises(ValueError, match=expected_error_msg):
            create_data_feed(df_invalid_index)

    def test_default_name_is_applied(self, ohlcv_dataframe_datetime_index):
        """
        Tests that the default name 'data' is used when no name is provided.
        """
        # Arrange
        df = ohlcv_dataframe_datetime_index

        # Act
        data_feed = create_data_feed(df)

        # Assert
        assert data_feed.p.name == "data"
