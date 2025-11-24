"""
Real Market Data Loader
Downloads actual market data from Yahoo Finance instead of synthetic data
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def download_stock_data(
    symbol: str,
    start_date: str = '2020-01-01',
    end_date: Optional[str] = None,
    interval: str = '1h'
) -> pd.DataFrame:
    """
    Download real stock data from Yahoo Finance
    
    Args:
        symbol: Ticker symbol (e.g., 'SPY', 'AAPL', 'EURUSD=X')
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD' (None = today)
        interval: Data interval ('1m', '5m', '15m', '1h', '1d')
                  Note: 1m only available for last 7 days
    
    Returns:
        DataFrame with OHLCV data
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Downloading {symbol} from {start_date} to {end_date}...")
    
    try:
        # Download data
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            print(f"⚠️  No data returned for {symbol}")
            return None
        
        # Standardize column names (lowercase)
        data.columns = data.columns.str.lower()
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            print(f"⚠️  Missing required columns for {symbol}")
            return None
        
        print(f"✅ Downloaded {len(data)} bars for {symbol}")
        return data
        
    except Exception as e:
        print(f"❌ Error downloading {symbol}: {e}")
        return None


def download_multiple_assets(
    symbols: List[str],
    start_date: str = '2020-01-01',
    end_date: Optional[str] = None,
    interval: str = '1h'
) -> Dict[str, pd.DataFrame]:
    """
    Download data for multiple assets
    
    Args:
        symbols: List of ticker symbols
        start_date: Start date
        end_date: End date (None = today)
        interval: Data interval
    
    Returns:
        Dictionary mapping symbol to DataFrame
    """
    data_dict = {}
    
    for symbol in symbols:
        data = download_stock_data(symbol, start_date, end_date, interval)
        if data is not None:
            data_dict[symbol] = data
    
    return data_dict


def load_correlated_pairs() -> Dict[str, pd.DataFrame]:
    """
    Load commonly correlated asset pairs for lead-lag and cross-asset strategies
    
    Returns:
        Dictionary of correlated asset data
    """
    pairs = {
        # US Equity Indexes (high correlation ~0.90)
        'SPY': 'SPY',      # S&P 500
        'QQQ': 'QQQ',      # Nasdaq 100
        'IWM': 'IWM',      # Russell 2000
        'DIA': 'DIA',      # Dow Jones
        
        # Sector ETFs (moderate correlation ~0.70-0.85)
        'XLF': 'XLF',      # Financials
        'XLE': 'XLE',      # Energy
        'XLK': 'XLK',      # Technology
        'XLV': 'XLV',      # Healthcare
        
        # Major Stocks
        'AAPL': 'AAPL',    # Apple
        'MSFT': 'MSFT',    # Microsoft
        'GOOGL': 'GOOGL',  # Google
    }
    
    print("Loading correlated asset pairs...")
    symbols_to_load = list(pairs.values())
    
    # Try daily data (more reliable)
    data = download_multiple_assets(
        symbols_to_load,
        start_date='2020-01-01',
        interval='1d'
    )
    
    return data


def load_forex_pairs() -> Dict[str, pd.DataFrame]:
    """
    Load forex pairs (requires =X suffix)
    
    Returns:
        Dictionary of forex pair data
    """
    pairs = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'USDJPY=X',
        'AUDUSD': 'AUDUSD=X',
        'USDCAD': 'USDCAD=X',
    }
    
    print("Loading forex pairs...")
    symbols = list(pairs.values())
    
    data = download_multiple_assets(
        symbols,
        start_date='2020-01-01',
        interval='1h'
    )
    
    # Rename to friendly names
    result = {}
    for name, symbol in pairs.items():
        if symbol in data:
            result[name] = data[symbol]
    
    return result


def load_commodities() -> Dict[str, pd.DataFrame]:
    """
    Load commodity futures (requires =F suffix)
    
    Returns:
        Dictionary of commodity data
    """
    commodities = {
        'Gold': 'GC=F',      # Gold futures
        'Silver': 'SI=F',    # Silver futures
        'Oil': 'CL=F',       # Crude Oil
        'NatGas': 'NG=F',    # Natural Gas
    }
    
    print("Loading commodities...")
    symbols = list(commodities.values())
    
    data = download_multiple_assets(
        symbols,
        start_date='2020-01-01',
        interval='1d'
    )
    
    # Rename to friendly names
    result = {}
    for name, symbol in commodities.items():
        if symbol in data:
            result[name] = data[symbol]
    
    return result


def prepare_data_for_strategy(data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare downloaded data for strategy testing
    
    Args:
        data: Raw OHLCV data
    
    Returns:
        Cleaned and prepared DataFrame
    """
    # Make a copy
    df = data.copy()
    
    # Remove any NaN values
    df = df.dropna()
    
    # Ensure volume is not zero (causes issues in some strategies)
    if 'volume' in df.columns:
        df = df[df['volume'] > 0]
    
    # Sort by index (time)
    df = df.sort_index()
    
    return df


# ============================================================================
# Quick Access Functions
# ============================================================================

def get_spy_data(days: int = 365, interval: str = '1d') -> pd.DataFrame:
    """Get S&P 500 (SPY) data for last N days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return download_stock_data('SPY', start_date.strftime('%Y-%m-%d'), interval=interval)


def get_forex_pair(pair: str = 'EURUSD', days: int = 90, interval: str = '1h') -> pd.DataFrame:
    """Get forex pair data (pair name without =X, that's added automatically)"""
    symbol = f"{pair}=X"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return download_stock_data(symbol, start_date.strftime('%Y-%m-%d'), interval=interval)


def get_crypto_data(symbol: str = 'BTC', days: int = 90, interval: str = '1h') -> pd.DataFrame:
    """Get cryptocurrency data"""
    crypto_symbol = f"{symbol}-USD"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return download_stock_data(crypto_symbol, start_date.strftime('%Y-%m-%d'), interval=interval)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Real Market Data Loader - Examples")
    print("=" * 60)
    
    # Example 1: Download single stock
    print("\n1. Downloading SPY (S&P 500)...")
    spy = download_stock_data('SPY', '2023-01-01', interval='1d')
    if spy is not None:
        print(f"   Shape: {spy.shape}")
        print(f"   Date range: {spy.index[0]} to {spy.index[-1]}")
        print(f"   Columns: {list(spy.columns)}")
        print(f"   First 3 rows:\n{spy.head(3)}")
    
    # Example 2: Download correlated pairs
    print("\n2. Downloading correlated pairs (may take a minute)...")
    pairs = load_correlated_pairs()
    print(f"   Loaded {len(pairs)} assets")
    for name, data in pairs.items():
        if data is not None:
            print(f"   {name}: {len(data)} bars")
    
    # Example 3: Quick access function
    print("\n3. Using quick access functions...")
    spy_quick = get_spy_data(days=180)
    if spy_quick is not None:
        print(f"   SPY (last 180 days): {len(spy_quick)} bars")
    
    print("\n" + "=" * 60)
    print("✅ Real data loader ready to use!")
    print("=" * 60)
    print("\nQuick start:")
    print("  from utils.real_data_loader import get_spy_data")
    print("  data = get_spy_data(days=365)")
    print("  # Now use with any strategy")
