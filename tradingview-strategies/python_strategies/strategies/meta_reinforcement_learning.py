"""
Meta-Reinforcement Learning Strategy
Based on: StockGPT & Meta-RL approaches (2024-2025)
Expected Performance: Advanced optimization
Complexity: Very High

Adaptive strategy selection using reinforcement learning principles
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import deque
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.base_strategy import BaseStrategy, Signal


class MetaReinforcementLearning(BaseStrategy):
    """
    Meta-learning system that learns which strategy works best in which market regime
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 learning_rate: float = 0.1,
                 exploration_rate: float = 0.2,
                 memory_size: int = 1000,
                 risk_per_trade: float = 0.01):
        super().__init__("Meta-Reinforcement Learning", initial_capital)
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.memory = deque(maxlen=memory_size)
        self.risk_per_trade = risk_per_trade
        
        # Define meta-strategies
        self.strategies = {
            'trend_following': self.trend_following_action,
            'mean_reversion': self.mean_reversion_action,
            'breakout': self.breakout_action,
            'momentum': self.momentum_action
        }
        
        # Q-table: state -> action -> value
        self.q_table = {strategy: {} for strategy in self.strategies.keys()}
        
        # Performance tracking
        self.strategy_performance = {strategy: {'wins': 0, 'losses': 0, 'total_return': 0.0} 
                                    for strategy in self.strategies.keys()}
        
    def get_market_state(self, data: pd.DataFrame, idx: int) -> str:
        """Identify current market state"""
        if idx < 20:
            return 'UNKNOWN'
        
        current_idx = data.index[idx]
        lookback = data.iloc[idx-20:idx]
        
        # Calculate state features
        returns = lookback['close'].pct_change()
        volatility = returns.std()
        trend = (lookback['close'].iloc[-1] - lookback['close'].iloc[0]) / lookback['close'].iloc[0]
        
        # Classify state
        if volatility > 0.03:
            vol_state = 'HIGH_VOL'
        elif volatility < 0.01:
            vol_state = 'LOW_VOL'
        else:
            vol_state = 'MED_VOL'
        
        if trend > 0.02:
            trend_state = 'UPTREND'
        elif trend < -0.02:
            trend_state = 'DOWNTREND'
        else:
            trend_state = 'SIDEWAYS'
        
        state = f"{trend_state}_{vol_state}"
        return state
    
    def select_strategy(self, state: str) -> str:
        """Select best strategy for current state using epsilon-greedy"""
        # Exploration
        if np.random.random() < self.exploration_rate:
            return np.random.choice(list(self.strategies.keys()))
        
        # Exploitation: Choose best Q-value
        if state not in self.q_table[list(self.strategies.keys())[0]]:
            return np.random.choice(list(self.strategies.keys()))
        
        q_values = {strategy: self.q_table[strategy].get(state, 0.0) 
                   for strategy in self.strategies.keys()}
        
        return max(q_values, key=q_values.get)
    
    def update_q_value(self, state: str, strategy: str, reward: float, next_state: str):
        """Update Q-value using Q-learning algorithm"""
        if state not in self.q_table[strategy]:
            self.q_table[strategy][state] = 0.0
        
        # Get max Q-value for next state
        next_max_q = 0.0
        if next_state != 'UNKNOWN':
            next_q_values = [self.q_table[s].get(next_state, 0.0) for s in self.strategies.keys()]
            next_max_q = max(next_q_values) if next_q_values else 0.0
        
        # Q-learning update
        current_q = self.q_table[strategy][state]
        new_q = current_q + self.learning_rate * (reward + 0.9 * next_max_q - current_q)
        self.q_table[strategy][state] = new_q
    
    def trend_following_action(self, data: pd.DataFrame, idx: int) -> Tuple[str, float]:
        """Trend following strategy logic"""
        if idx < 20:
            return None, 0.0
        
        current_idx = data.index[idx]
        ema_fast = data['close'].iloc[idx-10:idx].mean()
        ema_slow = data['close'].iloc[idx-20:idx].mean()
        
        confidence = abs(ema_fast - ema_slow) / ema_slow
        
        if ema_fast > ema_slow * 1.01:
            return 'LONG', min(confidence * 10, 1.0)
        elif ema_fast < ema_slow * 0.99:
            return 'SHORT', min(confidence * 10, 1.0)
        
        return None, 0.0
    
    def mean_reversion_action(self, data: pd.DataFrame, idx: int) -> Tuple[str, float]:
        """Mean reversion strategy logic"""
        if idx < 20:
            return None, 0.0
        
        current_idx = data.index[idx]
        sma = data['close'].iloc[idx-20:idx].mean()
        std = data['close'].iloc[idx-20:idx].std()
        current_price = data.loc[current_idx, 'close']
        
        zscore = (current_price - sma) / std if std > 0 else 0
        confidence = abs(zscore) / 2.0
        
        if zscore < -2:
            return 'LONG', min(confidence, 1.0)
        elif zscore > 2:
            return 'SHORT', min(confidence, 1.0)
        
        return None, 0.0
    
    def breakout_action(self, data: pd.DataFrame, idx: int) -> Tuple[str, float]:
        """Breakout strategy logic"""
        if idx < 20:
            return None, 0.0
        
        current_idx = data.index[idx]
        lookback = data.iloc[idx-20:idx]
        high_20 = lookback['high'].max()
        low_20 = lookback['low'].min()
        current_price = data.loc[current_idx, 'close']
        
        if current_price > high_20:
            confidence = (current_price - high_20) / high_20
            return 'LONG', min(confidence * 50, 1.0)
        elif current_price < low_20:
            confidence = (low_20 - current_price) / low_20
            return 'SHORT', min(confidence * 50, 1.0)
        
        return None, 0.0
    
    def momentum_action(self, data: pd.DataFrame, idx: int) -> Tuple[str, float]:
        """Momentum strategy logic"""
        if idx < 10:
            return None, 0.0
        
        current_idx = data.index[idx]
        momentum = data['close'].pct_change(10).iloc[idx]
        
        confidence = abs(momentum) * 10
        
        if momentum > 0.03:
            return 'LONG', min(confidence, 1.0)
        elif momentum < -0.03:
            return 'SHORT', min(confidence, 1.0)
        
        return None, 0.0
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals using meta-RL strategy selection"""
        signals = []
        position = None
        current_strategy = None
        entry_state = None
        
        for i in range(50, len(data)):
            current_idx = data.index[i]
            current_price = data.loc[current_idx, 'close']
            
            # Get current market state
            state = self.get_market_state(data, i)
            
            if position is None:
                # Select strategy based on meta-learning
                current_strategy = self.select_strategy(state)
                
                # Execute selected strategy
                action, confidence = self.strategies[current_strategy](data, i)
                
                if action in ['LONG', 'SHORT'] and confidence > 0.3:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type=action,
                        price=current_price,
                        confidence=confidence,
                        metadata={
                            'strategy': current_strategy,
                            'state': state
                        }
                    ))
                    position = action
                    entry_state = state
            
            else:
                # Exit management
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                
                if position == 'LONG':
                    profit_pct = (current_price - entry_price) / entry_price
                else:
                    profit_pct = (entry_price - current_price) / entry_price
                
                # Exit conditions
                if profit_pct > 0.04 or profit_pct < -0.02:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type=f'EXIT_{position}',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct}
                    ))
                    
                    # Update Q-value with reward
                    reward = profit_pct * 100
                    next_state = self.get_market_state(data, i)
                    self.update_q_value(entry_state, current_strategy, reward, next_state)
                    
                    # Update strategy performance
                    if profit_pct > 0:
                        self.strategy_performance[current_strategy]['wins'] += 1
                    else:
                        self.strategy_performance[current_strategy]['losses'] += 1
                    self.strategy_performance[current_strategy]['total_return'] += profit_pct
                    
                    position = None
                    current_strategy = None
                    entry_state = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on strategy confidence"""
        base_risk = self.current_capital * self.risk_per_trade
        
        # Adjust based on strategy performance
        strategy = signal.metadata['strategy']
        if strategy in self.strategy_performance:
            perf = self.strategy_performance[strategy]
            total_trades = perf['wins'] + perf['losses']
            if total_trades > 10:
                win_rate = perf['wins'] / total_trades
                performance_multiplier = max(0.5, min(win_rate * 2, 2.0))
            else:
                performance_multiplier = 1.0
        else:
            performance_multiplier = 1.0
        
        adjusted_risk = base_risk * signal.confidence * performance_multiplier
        position_size = adjusted_risk / current_price
        
        return position_size
