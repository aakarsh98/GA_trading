"""
YOUR Momentum Tracker Strategy - Python Implementation
Converted from Pine Script v6
This is YOUR actual trading strategy
"""
import numpy as np
import pandas as pd
from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.base_strategy import BaseStrategy, Signal


class MomentumTrackerStrategy(BaseStrategy):
    """
    Your Momentum Tracker Strategy from Pine Script
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 momentum_threshold: float = 2.0,
                 trend_length: int = 20,
                 risk_percent: float = 0.01,
                 atr_multiplier: float = 2.0,
                 atr_length: int = 14,
                 use_trend_filter: bool = True,
                 use_take_profit: bool = True,
                 take_profit_ratio: float = 2.0):
        
        super().__init__("Your Momentum Tracker", initial_capital)
        
        # Strategy parameters
        self.momentum_threshold = momentum_threshold
        self.trend_length = trend_length
        self.risk_percent = risk_percent
        self.atr_multiplier = atr_multiplier
        self.atr_length = atr_length
        self.use_trend_filter = use_trend_filter
        self.use_take_profit = use_take_profit
        self.take_profit_ratio = take_profit_ratio
        
        # Momentum tracker variables (from Pine Script)
        self.v8 = 0.0
        self.v16 = 0.0
        self.v0 = 0.0
        self.v80 = 0.0
        self.v88 = 0.0
        self.v96 = 0.0
        self.v104 = 0.0
        self.v112 = 0.0
        self.v120 = 0.0
        self.v128 = 0.0
        self.v208 = 0.0
        self.v136 = 0.0
        self.v152 = 0.0
        self.v160 = 0.0
        self.v168 = 0.0
        self.v176 = 0.0
        self.v184 = 0.0
        self.v192 = 0.0
        self.v200 = 0.0
        
        self.len = 7  # Hardcoded as in Pine Script
        self.equilibrium_level = None
        self.momentum_history = []
        
    def calculate_momentum_tracker(self, high: float, low: float, close: float) -> float:
        """
        Calculate momentum tracker value (v24)
        This is YOUR algorithm from Pine Script
        """
        # Typical price
        tp = (high + low + close) / 3.0
        
        # Default value
        v24 = 50.0
        
        # Main calculation (from Pine Script)
        if self.v8 == 0.0:
            self.v8 = 1.0
            self.v16 = 0.0
            self.v0 = self.len - 1.0 if self.len - 1 >= 5 else 5.0
            self.v80 = 100.0 * tp
            self.v96 = 3.0 / (self.len + 2.0)
            self.v104 = 1.0 - self.v96
        else:
            if self.v0 <= self.v8:
                self.v8 = self.v0 + 1.0
            else:
                self.v8 = self.v8 + 1.0
            
            self.v88 = self.v80
            self.v80 = 100.0 * tp
            
            # Price change
            v32 = self.v80 - self.v88
            
            # First smoothing layer
            self.v112 = self.v104 * self.v112 + self.v96 * v32
            self.v120 = self.v96 * self.v112 + self.v104 * self.v120
            v40 = 1.5 * self.v112 - self.v120 / 2.0
            
            # Second smoothing layer
            self.v128 = self.v104 * self.v128 + self.v96 * v40
            self.v208 = self.v96 * self.v128 + self.v104 * self.v208
            v48 = 1.5 * self.v128 - self.v208 / 2.0
            
            # Third smoothing layer
            self.v136 = self.v104 * self.v136 + self.v96 * v48
            self.v152 = self.v96 * self.v136 + self.v104 * self.v152
            v56 = 1.5 * self.v136 - self.v152 / 2.0
            
            # Absolute value smoothing - first layer
            self.v160 = self.v104 * self.v160 + self.v96 * abs(v32)
            self.v168 = self.v96 * self.v160 + self.v104 * self.v168
            v64 = 1.5 * self.v160 - self.v168 / 2.0
            
            # Absolute value smoothing - second layer
            self.v176 = self.v104 * self.v176 + self.v96 * v64
            self.v184 = self.v96 * self.v176 + self.v104 * self.v184
            v144 = 1.5 * self.v176 - self.v184 / 2.0
            
            # Absolute value smoothing - third layer
            self.v192 = self.v104 * self.v192 + self.v96 * v144
            self.v200 = self.v96 * self.v192 + self.v104 * self.v200
            v72 = 1.5 * self.v192 - self.v200 / 2.0
            
            if self.v0 >= self.v8 and self.v80 != self.v88:
                self.v16 = 1.0
            
            if self.v0 == self.v8 and self.v16 == 0.0:
                self.v8 = 0.0
            
            # Calculate final indicator value
            if self.v0 < self.v8 and v72 > 0.0000000001:
                v24 = 50.0 * (v56 / v72 + 1.0)
                if v24 > 100.0:
                    v24 = 100.0
                if v24 < 0.0:
                    v24 = 0.0
        
        return v24
    
    def calculate_atr(self, data: pd.DataFrame, idx: int) -> float:
        """Calculate ATR"""
        if idx < self.atr_length:
            return data.loc[data.index[idx], 'close'] * 0.02  # 2% default
        
        lookback = data.iloc[max(0, idx-self.atr_length):idx+1]
        
        tr_list = []
        for i in range(1, len(lookback)):
            high = lookback.iloc[i]['high']
            low = lookback.iloc[i]['low']
            prev_close = lookback.iloc[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)
        
        return np.mean(tr_list) if tr_list else data.loc[data.index[idx], 'close'] * 0.02
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals using YOUR momentum tracker logic
        """
        signals = []
        
        # Calculate trend MA
        data['trend_ma'] = data['close'].ewm(span=self.trend_length, adjust=False).mean()
        
        position = None
        entry_price = None
        stop_loss = None
        take_profit = None
        
        for i in range(50, len(data)):
            current_idx = data.index[i]
            high = data.loc[current_idx, 'high']
            low = data.loc[current_idx, 'low']
            close = data.loc[current_idx, 'close']
            
            # Calculate momentum tracker value
            v24 = self.calculate_momentum_tracker(high, low, close)
            self.momentum_history.append(v24)
            
            # Detect momentum direction change (equilibrium)
            if len(self.momentum_history) >= 3:
                current_change = v24 - self.momentum_history[-2]
                previous_change = self.momentum_history[-2] - self.momentum_history[-3]
                
                trend_changed = (current_change > 0 and previous_change <= 0) or \
                               (current_change < 0 and previous_change >= 0)
                
                if trend_changed or self.equilibrium_level is None:
                    self.equilibrium_level = v24
            
            if self.equilibrium_level is None:
                continue
            
            # Momentum signals
            momentum_bullish = v24 > self.equilibrium_level + self.momentum_threshold
            momentum_bearish = v24 < self.equilibrium_level - self.momentum_threshold
            
            # Trend filter
            trend_filter_bullish = close > data.loc[current_idx, 'trend_ma']
            trend_filter_bearish = close < data.loc[current_idx, 'trend_ma']
            
            # ATR for stops
            atr = self.calculate_atr(data, i)
            
            # Entry signals
            if position is None:
                # Long condition
                if momentum_bullish and (not self.use_trend_filter or trend_filter_bullish):
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='LONG',
                        price=close,
                        confidence=min((v24 - self.equilibrium_level) / 10.0, 1.0),
                        metadata={
                            'momentum': v24,
                            'equilibrium': self.equilibrium_level,
                            'atr': atr
                        }
                    ))
                    position = 'LONG'
                    entry_price = close
                    stop_loss = close - (atr * self.atr_multiplier)
                    take_profit = close + (atr * self.atr_multiplier * self.take_profit_ratio) if self.use_take_profit else None
                
                # Short condition
                elif momentum_bearish and (not self.use_trend_filter or trend_filter_bearish):
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='SHORT',
                        price=close,
                        confidence=min((self.equilibrium_level - v24) / 10.0, 1.0),
                        metadata={
                            'momentum': v24,
                            'equilibrium': self.equilibrium_level,
                            'atr': atr
                        }
                    ))
                    position = 'SHORT'
                    entry_price = close
                    stop_loss = close + (atr * self.atr_multiplier)
                    take_profit = close - (atr * self.atr_multiplier * self.take_profit_ratio) if self.use_take_profit else None
            
            # Exit signals
            elif position == 'LONG':
                profit_pct = (close - entry_price) / entry_price
                
                # Exit conditions
                exit_condition = momentum_bearish or \
                               (self.use_trend_filter and not trend_filter_bullish) or \
                               (close <= stop_loss) or \
                               (take_profit and close >= take_profit)
                
                if exit_condition:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_LONG',
                        price=close,
                        confidence=1.0,
                        metadata={
                            'profit_pct': profit_pct,
                            'reason': 'momentum_changed' if momentum_bearish else 'target_or_stop'
                        }
                    ))
                    position = None
            
            elif position == 'SHORT':
                profit_pct = (entry_price - close) / entry_price
                
                # Exit conditions
                exit_condition = momentum_bullish or \
                               (self.use_trend_filter and not trend_filter_bearish) or \
                               (close >= stop_loss) or \
                               (take_profit and close <= take_profit)
                
                if exit_condition:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_SHORT',
                        price=close,
                        confidence=1.0,
                        metadata={
                            'profit_pct': profit_pct,
                            'reason': 'momentum_changed' if momentum_bullish else 'target_or_stop'
                        }
                    ))
                    position = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on ATR risk"""
        atr = signal.metadata.get('atr', current_price * 0.02)
        risk_amount = self.current_capital * self.risk_percent
        stop_distance = atr * self.atr_multiplier
        
        position_size = risk_amount / stop_distance if stop_distance > 0 else self.current_capital * 0.01 / current_price
        
        return position_size
