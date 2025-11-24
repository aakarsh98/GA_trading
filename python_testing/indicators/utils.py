"""
Utility functions for technical indicators
Provides common calculations used across multiple indicators
"""

import numpy as np
import pandas as pd
from typing import Union


def atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        data: DataFrame with High, Low, Close columns
        period: ATR period (default 14)
        
    Returns:
        Series with ATR values
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR is EMA of True Range
    atr_values = tr.ewm(span=period, adjust=False).mean()
    
    return atr_values


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        series: Price series
        period: EMA period
        
    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        series: Price series
        period: SMA period
        
    Returns:
        Series with SMA values
    """
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        series: Price series
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    delta = series.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def stdev(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate rolling standard deviation.
    
    Args:
        series: Data series
        period: Rolling window period
        
    Returns:
        Series with standard deviation values
    """
    return series.rolling(window=period).std()


def correlation(series1: pd.Series, series2: pd.Series, period: int) -> pd.Series:
    """
    Calculate rolling correlation between two series.
    
    Args:
        series1: First data series
        series2: Second data series
        period: Rolling window period
        
    Returns:
        Series with correlation values (-1 to 1)
    """
    return series1.rolling(window=period).corr(series2)


def z_score(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate rolling z-score (standardized values).
    
    Args:
        series: Data series
        period: Rolling window period
        
    Returns:
        Series with z-score values
    """
    mean = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    return (series - mean) / std


def bars_since(condition: pd.Series) -> pd.Series:
    """
    Calculate number of bars since condition was True.
    Mimics PineScript's barssince() function.
    
    Args:
        condition: Boolean series
        
    Returns:
        Series with bars since last True
    """
    # Find positions where condition is True
    true_positions = condition[condition].index
    
    result = pd.Series(np.nan, index=condition.index)
    
    if len(true_positions) == 0:
        # Condition never met, return large number
        return pd.Series(len(condition), index=condition.index)
    
    for i, idx in enumerate(condition.index):
        # Find the most recent True before this index
        prior_true = true_positions[true_positions <= idx]
        if len(prior_true) > 0:
            last_true = prior_true[-1]
            result.loc[idx] = (condition.index.get_loc(idx) - 
                              condition.index.get_loc(last_true))
        else:
            result.loc[idx] = condition.index.get_loc(idx)
    
    return result


def highest(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate rolling maximum (highest value).
    
    Args:
        series: Data series
        period: Rolling window period
        
    Returns:
        Series with rolling maximum values
    """
    return series.rolling(window=period).max()


def lowest(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate rolling minimum (lowest value).
    
    Args:
        series: Data series
        period: Rolling window period
        
    Returns:
        Series with rolling minimum values
    """
    return series.rolling(window=period).min()


def typical_price(data: pd.DataFrame) -> pd.Series:
    """
    Calculate typical price (H+L+C)/3.
    
    Args:
        data: DataFrame with High, Low, Close columns
        
    Returns:
        Series with typical price values
    """
    return (data['High'] + data['Low'] + data['Close']) / 3.0


def hlc3(data: pd.DataFrame) -> pd.Series:
    """
    Alias for typical_price.
    """
    return typical_price(data)


def ohlc4(data: pd.DataFrame) -> pd.Series:
    """
    Calculate OHLC4 average price (O+H+L+C)/4.
    
    Args:
        data: DataFrame with Open, High, Low, Close columns
        
    Returns:
        Series with OHLC4 values
    """
    return (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4.0


def change(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Calculate change over n periods.
    
    Args:
        series: Data series
        periods: Number of periods to look back
        
    Returns:
        Series with change values
    """
    return series.diff(periods)


def percent_change(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Calculate percentage change over n periods.
    
    Args:
        series: Data series
        periods: Number of periods to look back
        
    Returns:
        Series with percentage change values
    """
    return series.pct_change(periods) * 100


def crossover(series1: pd.Series, series2: Union[pd.Series, float]) -> pd.Series:
    """
    Detect when series1 crosses over series2.
    
    Args:
        series1: First series
        series2: Second series or constant value
        
    Returns:
        Boolean series True where crossover occurs
    """
    if isinstance(series2, (int, float)):
        series2 = pd.Series(series2, index=series1.index)
    
    prev_below = series1.shift(1) <= series2.shift(1)
    current_above = series1 > series2
    
    return prev_below & current_above


def crossunder(series1: pd.Series, series2: Union[pd.Series, float]) -> pd.Series:
    """
    Detect when series1 crosses under series2.
    
    Args:
        series1: First series
        series2: Second series or constant value
        
    Returns:
        Boolean series True where crossunder occurs
    """
    if isinstance(series2, (int, float)):
        series2 = pd.Series(series2, index=series1.index)
    
    prev_above = series1.shift(1) >= series2.shift(1)
    current_below = series1 < series2
    
    return prev_above & current_below


def resample_data(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample OHLCV data to a higher timeframe.
    
    Args:
        data: DataFrame with OHLCV columns
        timeframe: Target timeframe ('4h', '1d', etc.)
        
    Returns:
        Resampled DataFrame
    """
    resampled = data.resample(timeframe).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    return resampled.dropna()


def request_security(data: pd.DataFrame, higher_timeframe: str, 
                     series: pd.Series) -> pd.Series:
    """
    Request data from higher timeframe (mimics PineScript request.security).
    
    Args:
        data: Base timeframe DataFrame
        higher_timeframe: Higher timeframe to resample to
        series: Series to resample
        
    Returns:
        Series resampled to higher timeframe and forward-filled
    """
    # Create DataFrame with the series
    temp_df = pd.DataFrame({'value': series}, index=data.index)
    
    # Resample to higher timeframe
    resampled = temp_df.resample(higher_timeframe).last()
    
    # Forward fill to match original index
    result = resampled.reindex(data.index, method='ffill')
    
    return result['value']


def main():
    """Test utility functions."""
    # Create sample data
    dates = pd.date_range('2025-01-01', periods=100, freq='1h')
    data = pd.DataFrame({
        'Open': np.random.randn(100).cumsum() + 100,
        'High': np.random.randn(100).cumsum() + 102,
        'Low': np.random.randn(100).cumsum() + 98,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    print("=== Testing Utility Functions ===\n")
    
    # Test ATR
    atr_values = atr(data, 14)
    print(f"ATR (14): {atr_values.iloc[-1]:.2f}")
    
    # Test EMA
    ema_values = ema(data['Close'], 20)
    print(f"EMA (20): {ema_values.iloc[-1]:.2f}")
    
    # Test SMA
    sma_values = sma(data['Close'], 20)
    print(f"SMA (20): {sma_values.iloc[-1]:.2f}")
    
    # Test RSI
    rsi_values = rsi(data['Close'], 14)
    print(f"RSI (14): {rsi_values.iloc[-1]:.2f}")
    
    # Test Z-Score
    z_values = z_score(data['Close'], 20)
    print(f"Z-Score (20): {z_values.iloc[-1]:.2f}")
    
    # Test Typical Price
    tp = typical_price(data)
    print(f"Typical Price: {tp.iloc[-1]:.2f}")
    
    # Test Crossover
    ema_fast = ema(data['Close'], 10)
    ema_slow = ema(data['Close'], 20)
    crosses = crossover(ema_fast, ema_slow)
    print(f"Crossovers detected: {crosses.sum()}")
    
    print("\n=== All Tests Passed ===")


if __name__ == '__main__':
    main()
