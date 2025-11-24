"""Generate synthetic market data for testing"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple


def generate_ohlcv_data(
    n_bars: int = 1000,
    start_price: float = 100.0,
    trend: float = 0.0001,
    volatility: float = 0.02,
    seed: int = None
) -> pd.DataFrame:
    """
    Generate realistic OHLCV data with configurable parameters
    
    Args:
        n_bars: Number of bars to generate
        start_price: Starting price
        trend: Drift/trend component
        volatility: Volatility parameter
        seed: Random seed for reproducibility
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate timestamps (hourly bars)
    timestamps = [datetime(2020, 1, 1) + timedelta(hours=i) for i in range(n_bars)]
    
    # Generate close prices using geometric Brownian motion
    returns = np.random.normal(trend, volatility, n_bars)
    prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    data = pd.DataFrame(index=timestamps)
    data['close'] = prices
    
    # Generate high/low with realistic spreads
    bar_ranges = np.abs(np.random.normal(0, volatility * 0.5, n_bars))
    high_offset = np.random.uniform(0.3, 0.7, n_bars)
    
    data['high'] = data['close'] * (1 + bar_ranges * high_offset)
    data['low'] = data['close'] * (1 - bar_ranges * (1 - high_offset))
    
    # Generate open prices
    data['open'] = data['close'].shift(1)
    data.loc[data.index[0], 'open'] = start_price
    
    # Add some noise to make it realistic
    data['open'] = data['open'] * (1 + np.random.normal(0, volatility * 0.2, n_bars))
    
    # Ensure high is highest and low is lowest
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    # Generate volume
    base_volume = 1000000
    volume_volatility = np.random.lognormal(0, 0.5, n_bars)
    data['volume'] = base_volume * volume_volatility
    
    return data


def generate_trending_data(n_bars: int = 1000, trend_strength: str = 'medium') -> pd.DataFrame:
    """Generate data with specific trend characteristics"""
    trend_params = {
        'strong_up': 0.001,
        'medium_up': 0.0005,
        'weak_up': 0.0002,
        'sideways': 0.0,
        'weak_down': -0.0002,
        'medium_down': -0.0005,
        'strong_down': -0.001
    }
    
    trend = trend_params.get(trend_strength, 0.0)
    return generate_ohlcv_data(n_bars=n_bars, trend=trend)


def generate_volatile_data(n_bars: int = 1000, volatility_level: str = 'medium') -> pd.DataFrame:
    """Generate data with specific volatility characteristics"""
    vol_params = {
        'low': 0.01,
        'medium': 0.02,
        'high': 0.04,
        'extreme': 0.08
    }
    
    vol = vol_params.get(volatility_level, 0.02)
    return generate_ohlcv_data(n_bars=n_bars, volatility=vol)


def generate_regime_switching_data(n_bars: int = 1000) -> pd.DataFrame:
    """Generate data with regime switches (bull, bear, sideways)"""
    regimes = []
    regime_types = ['bull', 'sideways', 'bear']
    
    bars_per_regime = n_bars // 6
    
    for _ in range(2):
        for regime in regime_types:
            if regime == 'bull':
                regimes.append(generate_trending_data(bars_per_regime, 'medium_up'))
            elif regime == 'bear':
                regimes.append(generate_trending_data(bars_per_regime, 'medium_down'))
            else:
                regimes.append(generate_trending_data(bars_per_regime, 'sideways'))
    
    # Concatenate all regimes
    data = pd.concat(regimes, ignore_index=True)
    
    # Reset timestamps
    timestamps = [datetime(2020, 1, 1) + timedelta(hours=i) for i in range(len(data))]
    data.index = timestamps
    
    return data


def load_sample_data(data_type: str = 'mixed', n_bars: int = 2000) -> pd.DataFrame:
    """
    Load sample data for testing
    
    Args:
        data_type: Type of data ('mixed', 'trending', 'volatile', 'regime_switching')
        n_bars: Number of bars to generate
    """
    if data_type == 'trending':
        return generate_trending_data(n_bars, 'medium_up')
    elif data_type == 'volatile':
        return generate_volatile_data(n_bars, 'high')
    elif data_type == 'regime_switching':
        return generate_regime_switching_data(n_bars)
    else:
        # Mixed: combination of different market conditions
        return generate_regime_switching_data(n_bars)
