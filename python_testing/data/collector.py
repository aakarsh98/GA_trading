"""
Data Collection Module
Fetches market data from open-source APIs (yfinance, ccxt)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import os


class DataCollector:
    """
    Collects and caches market data from various sources.
    
    Primary source: yfinance (stocks, ETFs, forex, crypto)
    Secondary source: ccxt (additional crypto exchanges)
    """
    
    def __init__(self, cache_dir='data/cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_data(self, symbol, start=None, end=None, timeframe='1d', period='1y', use_cache=True):
        """
        Fetch OHLCV data for a given symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC-USD', 'SPY', 'EURUSD=X')
            start: Start date (datetime or string 'YYYY-MM-DD')
            end: End date (datetime or string 'YYYY-MM-DD')
            timeframe: Data interval ('1m', '5m', '15m', '1h', '4h', '1d', '1wk', '1mo')
            period: Period to fetch if start/end not provided ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            use_cache: Whether to use cached data
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        # Convert timeframe to yfinance format
        interval_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '1h',  # yfinance doesn't have 4h, we'll resample
            '1d': '1d', '1wk': '1wk', '1mo': '1mo'
        }
        
        yf_interval = interval_map.get(timeframe, '1d')
        
        # Check cache
        cache_file = self._get_cache_path(symbol, start, end, period, timeframe)
        if use_cache and cache_file.exists():
            try:
                data = pd.read_pickle(cache_file)
                print(f"Loaded cached data for {symbol} ({timeframe}): {len(data)} bars")
                return data
            except Exception as e:
                print(f"Cache load failed: {e}, fetching fresh data...")
        
        # Fetch from yfinance
        print(f"Fetching {symbol} data ({timeframe})...")
        ticker = yf.Ticker(symbol)
        
        try:
            if start and end:
                data = ticker.history(start=start, end=end, interval=yf_interval)
            else:
                data = ticker.history(period=period, interval=yf_interval)
            
            if data.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Resample to 4h if needed
            if timeframe == '4h' and yf_interval == '1h':
                data = self._resample_to_4h(data)
            
            # Clean data
            data = self._clean_data(data)
            
            # Cache the data
            if use_cache:
                data.to_pickle(cache_file)
                print(f"Cached data to {cache_file}")
            
            print(f"Fetched {len(data)} bars for {symbol} ({timeframe})")
            return data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            raise
    
    def fetch_multiple(self, symbols, **kwargs):
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of ticker symbols
            **kwargs: Arguments passed to fetch_data
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.fetch_data(symbol, **kwargs)
            except Exception as e:
                print(f"Failed to fetch {symbol}: {e}")
        return results
    
    def _resample_to_4h(self, data):
        """Resample hourly data to 4-hour timeframe."""
        resampled = data.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        return resampled.dropna()
    
    def _clean_data(self, data):
        """Clean and standardize the data."""
        # Remove timezone info if present
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        
        # Remove any NaN rows
        data = data.dropna()
        
        # Ensure we have the required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Sort by index
        data = data.sort_index()
        
        return data[required_cols]
    
    def _get_cache_path(self, symbol, start, end, period, timeframe):
        """Generate cache file path."""
        # Create a unique filename based on parameters
        safe_symbol = symbol.replace('/', '_').replace('=', '_')
        if start and end:
            cache_name = f"{safe_symbol}_{start}_{end}_{timeframe}.pkl"
        else:
            cache_name = f"{safe_symbol}_{period}_{timeframe}.pkl"
        return self.cache_dir / cache_name
    
    def clear_cache(self, symbol=None):
        """Clear cached data."""
        if symbol:
            safe_symbol = symbol.replace('/', '_').replace('=', '_')
            for file in self.cache_dir.glob(f"{safe_symbol}_*.pkl"):
                file.unlink()
                print(f"Deleted cache: {file}")
        else:
            for file in self.cache_dir.glob("*.pkl"):
                file.unlink()
            print("Cleared all cache files")
    
    @staticmethod
    def get_available_timeframes():
        """Return list of supported timeframes."""
        return ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1wk', '1mo']
    
    @staticmethod
    def get_sample_symbols():
        """Return commonly used symbols for testing."""
        return {
            'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD'],
            'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'],
            'stocks': ['SPY', 'QQQ', 'AAPL', 'MSFT', 'TSLA'],
            'commodities': ['GC=F', 'CL=F', 'SI=F']  # Gold, Oil, Silver
        }


def main():
    """Demo usage of DataCollector."""
    collector = DataCollector()
    
    # Test fetching BTC data
    print("\n=== Testing BTC-USD data fetch ===")
    btc_data = collector.fetch_data('BTC-USD', timeframe='1h', period='1mo')
    print(f"\nBTC Data Shape: {btc_data.shape}")
    print(f"Date Range: {btc_data.index[0]} to {btc_data.index[-1]}")
    print("\nFirst 5 rows:")
    print(btc_data.head())
    print("\nLast 5 rows:")
    print(btc_data.tail())
    print(f"\nData Info:")
    print(btc_data.info())
    
    # Test multiple symbols
    print("\n=== Testing multiple symbols ===")
    symbols = ['BTC-USD', 'ETH-USD', 'SPY']
    data_dict = collector.fetch_multiple(symbols, timeframe='1d', period='3mo')
    for symbol, data in data_dict.items():
        print(f"{symbol}: {len(data)} bars")


if __name__ == '__main__':
    main()
