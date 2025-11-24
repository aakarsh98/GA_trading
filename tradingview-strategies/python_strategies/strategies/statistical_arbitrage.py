"""
Statistical Arbitrage Strategy
Based on: Mean-Reverting Arbitrage & Statistical learning bounds (2024)
Expected Performance: 15-25% improvement
Complexity: Low

Exploits mean-reversion opportunities using z-score based entries
"""
import numpy as np
import pandas as pd
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.base_strategy import BaseStrategy, Signal
from utils.indicators import calculate_zscore, calculate_bollinger_bands, calculate_atr


class StatisticalArbitrage(BaseStrategy):
    """
    Mean-reversion strategy using statistical arbitrage principles
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 zscore_entry: float = 2.0,
                 zscore_exit: float = 0.5,
                 lookback_period: int = 20,
                 risk_per_trade: float = 0.01):
        super().__init__("Statistical Arbitrage", initial_capital)
        self.zscore_entry = zscore_entry
        self.zscore_exit = zscore_exit
        self.lookback_period = lookback_period
        self.risk_per_trade = risk_per_trade
        
    def calculate_half_life(self, series: pd.Series) -> float:
        """Calculate mean reversion half-life (Ornstein-Uhlenbeck)"""
        series_lag = series.shift(1).dropna()
        series_diff = series.diff().dropna()
        
        # Align indices
        common_idx = series_lag.index.intersection(series_diff.index)
        series_lag = series_lag.loc[common_idx]
        series_diff = series_diff.loc[common_idx]
        
        if len(series_lag) < 2:
            return np.inf
        
        # OLS regression: diff = lambda * lag + epsilon
        try:
            lambda_param = np.polyfit(series_lag, series_diff, 1)[0]
            if lambda_param >= 0:
                return np.inf
            half_life = -np.log(2) / lambda_param
            return half_life
        except:
            return np.inf
    
    def calculate_mean_reversion_strength(self, data: pd.DataFrame, idx: int) -> float:
        """Calculate strength of mean reversion"""
        if idx < self.lookback_period:
            return 0.0
        
        lookback_data = data.iloc[idx-self.lookback_period:idx]
        prices = lookback_data['close']
        
        # Calculate half-life
        half_life = self.calculate_half_life(prices)
        
        # Shorter half-life = stronger mean reversion
        if half_life < 5:
            strength = 1.0
        elif half_life < 10:
            strength = 0.8
        elif half_life < 20:
            strength = 0.6
        else:
            strength = 0.3
        
        # Adjust for current deviation from mean
        current_zscore = abs(data.loc[data.index[idx], 'zscore'])
        if current_zscore > 2.5:
            strength *= 1.2
        elif current_zscore > 2.0:
            strength *= 1.0
        else:
            strength *= 0.8
        
        return min(strength, 1.0)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate mean-reversion signals"""
        signals = []
        
        # Calculate technical indicators
        data['sma'] = data['close'].rolling(window=self.lookback_period).mean()
        data['std'] = data['close'].rolling(window=self.lookback_period).std()
        data['zscore'] = (data['close'] - data['sma']) / data['std']
        data['atr'] = calculate_atr(data['high'], data['low'], data['close'])
        
        # Bollinger Bands for confirmation
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(data['close'], self.lookback_period)
        data['bb_upper'] = bb_upper
        data['bb_middle'] = bb_middle
        data['bb_lower'] = bb_lower
        data['bb_position'] = (data['close'] - bb_lower) / (bb_upper - bb_lower)
        
        position = None
        
        for i in range(self.lookback_period * 2, len(data)):
            current_idx = data.index[i]
            current_price = data.loc[current_idx, 'close']
            current_zscore = data.loc[current_idx, 'zscore']
            
            # Calculate mean reversion strength
            mr_strength = self.calculate_mean_reversion_strength(data, i)
            
            # Long signal: Price below mean (negative z-score)
            if (current_zscore < -self.zscore_entry and
                mr_strength > 0.5 and
                position is None):
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='LONG',
                    price=current_price,
                    confidence=mr_strength,
                    metadata={
                        'zscore': current_zscore,
                        'mr_strength': mr_strength,
                        'entry_type': 'oversold'
                    }
                ))
                position = 'LONG'
            
            # Short signal: Price above mean (positive z-score)
            elif (current_zscore > self.zscore_entry and
                  mr_strength > 0.5 and
                  position is None):
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='SHORT',
                    price=current_price,
                    confidence=mr_strength,
                    metadata={
                        'zscore': current_zscore,
                        'mr_strength': mr_strength,
                        'entry_type': 'overbought'
                    }
                ))
                position = 'SHORT'
            
            # Exit conditions
            if position == 'LONG':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                entry_zscore = entry_signal.metadata['zscore']
                profit_pct = (current_price - entry_price) / entry_price
                
                # Exit on mean reversion or stop loss
                exit_condition = (
                    current_zscore > -self.zscore_exit or  # Reverted to mean
                    profit_pct > 0.04 or  # Take profit
                    profit_pct < -0.02 or  # Stop loss
                    current_zscore > self.zscore_entry  # Reversed too much
                )
                
                if exit_condition:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_LONG',
                        price=current_price,
                        confidence=1.0,
                        metadata={
                            'profit_pct': profit_pct,
                            'exit_zscore': current_zscore
                        }
                    ))
                    position = None
            
            elif position == 'SHORT':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                entry_zscore = entry_signal.metadata['zscore']
                profit_pct = (entry_price - current_price) / entry_price
                
                exit_condition = (
                    current_zscore < self.zscore_exit or  # Reverted to mean
                    profit_pct > 0.04 or  # Take profit
                    profit_pct < -0.02 or  # Stop loss
                    current_zscore < -self.zscore_entry  # Reversed too much
                )
                
                if exit_condition:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_SHORT',
                        price=current_price,
                        confidence=1.0,
                        metadata={
                            'profit_pct': profit_pct,
                            'exit_zscore': current_zscore
                        }
                    ))
                    position = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on mean-reversion strength"""
        base_risk = self.current_capital * self.risk_per_trade
        
        mr_strength = signal.confidence
        zscore_magnitude = abs(signal.metadata['zscore'])
        
        # Higher position size for stronger mean reversion + larger deviations
        size_multiplier = mr_strength * min(zscore_magnitude / 2.0, 1.5)
        
        adjusted_risk = base_risk * size_multiplier
        position_size = adjusted_risk / current_price
        
        return position_size
