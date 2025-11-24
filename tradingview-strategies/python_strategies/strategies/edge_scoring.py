"""
Real-Time Edge Scoring Strategy
Based on: Real-time edge detection and scoring systems
Expected Performance: 20-30% improvement
Complexity: Medium

Dynamically scores and ranks trading opportunities in real-time
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.base_strategy import BaseStrategy, Signal
from utils.indicators import (calculate_rsi, calculate_macd, calculate_atr, 
                              calculate_adx, calculate_volatility, calculate_momentum)


class EdgeScoring(BaseStrategy):
    """
    Real-time edge scoring system combining multiple factors
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 min_edge_score: float = 7.0,
                 max_edge_score: float = 10.0,
                 risk_per_trade: float = 0.01):
        super().__init__("Real-Time Edge Scoring", initial_capital)
        self.min_edge_score = min_edge_score
        self.max_edge_score = max_edge_score
        self.risk_per_trade = risk_per_trade
        self.score_history = []
        
    def calculate_trend_edge(self, data: pd.DataFrame, idx: int) -> float:
        """Score: 0-2 based on trend strength"""
        current_idx = data.index[idx]
        
        adx = data.loc[current_idx, 'adx']
        ema_fast = data.loc[current_idx, 'ema_fast']
        ema_slow = data.loc[current_idx, 'ema_slow']
        
        # ADX component (0-1)
        adx_score = min(adx / 40, 1.0) if adx > 20 else 0.0
        
        # Trend direction component (0-1)
        trend_strength = abs(ema_fast - ema_slow) / ema_slow
        trend_score = min(trend_strength * 20, 1.0)
        
        return adx_score + trend_score
    
    def calculate_momentum_edge(self, data: pd.DataFrame, idx: int) -> float:
        """Score: 0-2 based on momentum quality"""
        current_idx = data.index[idx]
        
        macd = data.loc[current_idx, 'macd']
        macd_signal = data.loc[current_idx, 'macd_signal']
        momentum = data.loc[current_idx, 'momentum']
        
        # MACD component (0-1)
        macd_diff = abs(macd - macd_signal)
        macd_score = min(macd_diff * 10, 1.0)
        
        # Momentum component (0-1)
        momentum_score = min(abs(momentum) * 50, 1.0)
        
        return macd_score + momentum_score
    
    def calculate_volatility_edge(self, data: pd.DataFrame, idx: int) -> float:
        """Score: 0-2 based on volatility regime"""
        current_idx = data.index[idx]
        
        current_vol = data.loc[current_idx, 'volatility']
        vol_sma = data.loc[current_idx, 'volatility_sma']
        atr = data.loc[current_idx, 'atr']
        atr_sma = data.loc[current_idx, 'atr_sma']
        
        # Volatility expansion/contraction (0-1)
        vol_ratio = current_vol / vol_sma if vol_sma > 0 else 1.0
        vol_score = 1.0 if 0.8 < vol_ratio < 1.5 else 0.5
        
        # ATR component (0-1)
        atr_ratio = atr / atr_sma if atr_sma > 0 else 1.0
        atr_score = 1.0 if 0.8 < atr_ratio < 1.5 else 0.5
        
        return vol_score + atr_score
    
    def calculate_mean_reversion_edge(self, data: pd.DataFrame, idx: int) -> float:
        """Score: 0-2 based on mean reversion potential"""
        current_idx = data.index[idx]
        
        rsi = data.loc[current_idx, 'rsi']
        bb_position = data.loc[current_idx, 'bb_position']
        
        # RSI extremes (0-1)
        if rsi < 30:
            rsi_score = (30 - rsi) / 30
        elif rsi > 70:
            rsi_score = (rsi - 70) / 30
        else:
            rsi_score = 0.0
        
        # Bollinger Band position (0-1)
        if bb_position < 0.2:
            bb_score = (0.2 - bb_position) / 0.2
        elif bb_position > 0.8:
            bb_score = (bb_position - 0.8) / 0.2
        else:
            bb_score = 0.0
        
        return min(rsi_score, 1.0) + min(bb_score, 1.0)
    
    def calculate_timing_edge(self, data: pd.DataFrame, idx: int) -> float:
        """Score: 0-2 based on entry timing quality"""
        if idx < 5:
            return 0.0
        
        current_idx = data.index[idx]
        
        # Recent price action (0-1)
        recent_returns = data['close'].pct_change().iloc[idx-5:idx]
        volatility_of_returns = recent_returns.std()
        consistency = 1.0 / (1.0 + volatility_of_returns * 100)
        
        # Volume confirmation (0-1) - if available
        if 'volume' in data.columns:
            vol_ratio = data.loc[current_idx, 'volume'] / data['volume'].iloc[idx-20:idx].mean()
            volume_score = min(vol_ratio / 1.5, 1.0) if vol_ratio > 1.0 else 0.5
        else:
            volume_score = 0.5
        
        return consistency + volume_score
    
    def calculate_total_edge_score(self, data: pd.DataFrame, idx: int, direction: str) -> Tuple[float, Dict]:
        """Calculate total edge score (0-10)"""
        trend_edge = self.calculate_trend_edge(data, idx)
        momentum_edge = self.calculate_momentum_edge(data, idx)
        volatility_edge = self.calculate_volatility_edge(data, idx)
        mr_edge = self.calculate_mean_reversion_edge(data, idx)
        timing_edge = self.calculate_timing_edge(data, idx)
        
        # Direction alignment
        current_idx = data.index[idx]
        ema_fast = data.loc[current_idx, 'ema_fast']
        ema_slow = data.loc[current_idx, 'ema_slow']
        
        if direction == 'LONG':
            direction_alignment = 1.0 if ema_fast > ema_slow else 0.5
        else:
            direction_alignment = 1.0 if ema_fast < ema_slow else 0.5
        
        # Weighted total
        total_score = (
            trend_edge * 0.25 +
            momentum_edge * 0.25 +
            volatility_edge * 0.15 +
            mr_edge * 0.20 +
            timing_edge * 0.15
        ) * direction_alignment * 2  # Scale to 0-10
        
        components = {
            'trend_edge': trend_edge,
            'momentum_edge': momentum_edge,
            'volatility_edge': volatility_edge,
            'mr_edge': mr_edge,
            'timing_edge': timing_edge,
            'direction_alignment': direction_alignment,
            'total_score': total_score
        }
        
        return total_score, components
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals based on edge scoring"""
        signals = []
        
        # Calculate all indicators
        data['rsi'] = calculate_rsi(data['close'])
        data['atr'] = calculate_atr(data['high'], data['low'], data['close'])
        data['adx'] = calculate_adx(data['high'], data['low'], data['close'])
        data['volatility'] = calculate_volatility(data['close'])
        data['momentum'] = calculate_momentum(data['close'], 10)
        
        data['ema_fast'] = data['close'].ewm(span=12).mean()
        data['ema_slow'] = data['close'].ewm(span=26).mean()
        
        macd, macd_signal, macd_hist = calculate_macd(data['close'])
        data['macd'] = macd
        data['macd_signal'] = macd_signal
        data['macd_hist'] = macd_hist
        
        # Rolling statistics
        data['volatility_sma'] = data['volatility'].rolling(20).mean()
        data['atr_sma'] = data['atr'].rolling(20).mean()
        
        # Bollinger Bands position
        sma = data['close'].rolling(20).mean()
        std = data['close'].rolling(20).std()
        bb_upper = sma + 2 * std
        bb_lower = sma - 2 * std
        data['bb_position'] = (data['close'] - bb_lower) / (bb_upper - bb_lower)
        
        position = None
        
        for i in range(50, len(data)):
            current_idx = data.index[i]
            current_price = data.loc[current_idx, 'close']
            
            # Calculate edge scores for both directions
            long_score, long_components = self.calculate_total_edge_score(data, i, 'LONG')
            short_score, short_components = self.calculate_total_edge_score(data, i, 'SHORT')
            
            # Long signal
            if (long_score >= self.min_edge_score and
                long_score > short_score and
                position is None):
                
                confidence = min(long_score / self.max_edge_score, 1.0)
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='LONG',
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'edge_score': long_score,
                        'components': long_components
                    }
                ))
                position = 'LONG'
                self.score_history.append({
                    'timestamp': current_idx,
                    'score': long_score,
                    'direction': 'LONG'
                })
            
            # Short signal
            elif (short_score >= self.min_edge_score and
                  short_score > long_score and
                  position is None):
                
                confidence = min(short_score / self.max_edge_score, 1.0)
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='SHORT',
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'edge_score': short_score,
                        'components': short_components
                    }
                ))
                position = 'SHORT'
                self.score_history.append({
                    'timestamp': current_idx,
                    'score': short_score,
                    'direction': 'SHORT'
                })
            
            # Exit management
            if position == 'LONG':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                profit_pct = (current_price - entry_price) / entry_price
                
                # Recalculate edge score
                current_long_score, _ = self.calculate_total_edge_score(data, i, 'LONG')
                
                # Exit if edge deteriorates or targets hit
                if (current_long_score < self.min_edge_score * 0.6 or
                    profit_pct > 0.05 or
                    profit_pct < -0.02):
                    
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_LONG',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct, 'exit_score': current_long_score}
                    ))
                    position = None
            
            elif position == 'SHORT':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                profit_pct = (entry_price - current_price) / entry_price
                
                current_short_score, _ = self.calculate_total_edge_score(data, i, 'SHORT')
                
                if (current_short_score < self.min_edge_score * 0.6 or
                    profit_pct > 0.05 or
                    profit_pct < -0.02):
                    
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_SHORT',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct, 'exit_score': current_short_score}
                    ))
                    position = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on edge score"""
        base_risk = self.current_capital * self.risk_per_trade
        
        # Scale position size with edge quality
        edge_score = signal.metadata['edge_score']
        score_multiplier = edge_score / self.max_edge_score
        
        adjusted_risk = base_risk * score_multiplier * 1.5
        position_size = adjusted_risk / current_price
        
        return position_size
