"""
LLM-Inspired Features Strategy
Based on: LLMFactor & Evidence-based reasoning (arXiv 2024)
Expected Performance: Evidence-based reasoning improvements
Complexity: Very High

Uses pattern recognition and evidence-based reasoning inspired by LLM approaches
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.base_strategy import BaseStrategy, Signal


class LLMInspiredFeatures(BaseStrategy):
    """
    Pattern recognition and reasoning system inspired by LLM capabilities
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 pattern_memory_size: int = 500,
                 confidence_threshold: float = 0.7,
                 risk_per_trade: float = 0.01):
        super().__init__("LLM-Inspired Features", initial_capital)
        self.pattern_memory = []
        self.pattern_memory_size = pattern_memory_size
        self.confidence_threshold = confidence_threshold
        self.risk_per_trade = risk_per_trade
        
        # Pattern categories
        self.pattern_outcomes = defaultdict(lambda: {'success': 0, 'failure': 0})
        
    def extract_market_context(self, data: pd.DataFrame, idx: int, window: int = 10) -> Dict:
        """
        Extract contextual features similar to how LLMs extract context
        """
        if idx < window:
            return {}
        
        lookback = data.iloc[idx-window:idx]
        current_idx = data.index[idx]
        
        context = {
            'price_trend': self._classify_trend(lookback['close']),
            'volatility_regime': self._classify_volatility(lookback['close']),
            'momentum_state': self._classify_momentum(lookback['close']),
            'volume_profile': self._classify_volume(lookback.get('volume', pd.Series([1]*len(lookback)))),
            'price_pattern': self._identify_price_pattern(lookback['close']),
        }
        
        return context
    
    def _classify_trend(self, prices: pd.Series) -> str:
        """Classify trend direction and strength"""
        if len(prices) < 2:
            return 'UNKNOWN'
        
        linear_fit = np.polyfit(range(len(prices)), prices, 1)
        slope = linear_fit[0]
        
        if slope > prices.mean() * 0.005:
            return 'STRONG_UP'
        elif slope > 0:
            return 'WEAK_UP'
        elif slope < -prices.mean() * 0.005:
            return 'STRONG_DOWN'
        elif slope < 0:
            return 'WEAK_DOWN'
        else:
            return 'FLAT'
    
    def _classify_volatility(self, prices: pd.Series) -> str:
        """Classify volatility regime"""
        if len(prices) < 2:
            return 'UNKNOWN'
        
        returns = prices.pct_change().dropna()
        volatility = returns.std()
        
        if volatility > 0.03:
            return 'HIGH'
        elif volatility > 0.015:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _classify_momentum(self, prices: pd.Series) -> str:
        """Classify momentum characteristics"""
        if len(prices) < 5:
            return 'UNKNOWN'
        
        recent_momentum = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5]
        
        if recent_momentum > 0.02:
            return 'STRONG_POSITIVE'
        elif recent_momentum > 0:
            return 'WEAK_POSITIVE'
        elif recent_momentum < -0.02:
            return 'STRONG_NEGATIVE'
        elif recent_momentum < 0:
            return 'WEAK_NEGATIVE'
        else:
            return 'NEUTRAL'
    
    def _classify_volume(self, volume: pd.Series) -> str:
        """Classify volume profile"""
        if len(volume) < 5:
            return 'UNKNOWN'
        
        recent_vol = volume.iloc[-3:].mean()
        avg_vol = volume.mean()
        
        if recent_vol > avg_vol * 1.5:
            return 'INCREASING'
        elif recent_vol > avg_vol * 1.1:
            return 'SLIGHTLY_INCREASING'
        elif recent_vol < avg_vol * 0.7:
            return 'DECREASING'
        else:
            return 'STABLE'
    
    def _identify_price_pattern(self, prices: pd.Series) -> str:
        """Identify common price patterns"""
        if len(prices) < 5:
            return 'UNKNOWN'
        
        # Calculate price changes
        changes = prices.diff().iloc[-5:]
        
        # Higher highs and higher lows
        if all(changes.iloc[i] > 0 for i in [1, 3]) and prices.iloc[-1] > prices.iloc[-5]:
            return 'ASCENDING'
        
        # Lower highs and lower lows
        elif all(changes.iloc[i] < 0 for i in [1, 3]) and prices.iloc[-1] < prices.iloc[-5]:
            return 'DESCENDING'
        
        # V-shaped recovery
        elif changes.iloc[0] < 0 and changes.iloc[-2:].mean() > 0:
            return 'V_RECOVERY'
        
        # Inverted V
        elif changes.iloc[0] > 0 and changes.iloc[-2:].mean() < 0:
            return 'INVERTED_V'
        
        # Range-bound
        elif prices.max() - prices.min() < prices.mean() * 0.02:
            return 'RANGE_BOUND'
        
        else:
            return 'MIXED'
    
    def reason_about_context(self, context: Dict) -> Tuple[str, float, str]:
        """
        Evidence-based reasoning about trading decision
        Returns: (action, confidence, reasoning)
        """
        reasoning_points = []
        bullish_score = 0
        bearish_score = 0
        
        # Reasoning based on trend
        if context['price_trend'] in ['STRONG_UP', 'WEAK_UP']:
            bullish_score += 2 if context['price_trend'] == 'STRONG_UP' else 1
            reasoning_points.append(f"Uptrend detected ({context['price_trend']})")
        elif context['price_trend'] in ['STRONG_DOWN', 'WEAK_DOWN']:
            bearish_score += 2 if context['price_trend'] == 'STRONG_DOWN' else 1
            reasoning_points.append(f"Downtrend detected ({context['price_trend']})")
        
        # Reasoning based on momentum
        if context['momentum_state'] in ['STRONG_POSITIVE', 'WEAK_POSITIVE']:
            bullish_score += 1.5 if context['momentum_state'] == 'STRONG_POSITIVE' else 0.5
            reasoning_points.append(f"Positive momentum ({context['momentum_state']})")
        elif context['momentum_state'] in ['STRONG_NEGATIVE', 'WEAK_NEGATIVE']:
            bearish_score += 1.5 if context['momentum_state'] == 'STRONG_NEGATIVE' else 0.5
            reasoning_points.append(f"Negative momentum ({context['momentum_state']})")
        
        # Reasoning based on pattern
        if context['price_pattern'] == 'ASCENDING':
            bullish_score += 1
            reasoning_points.append("Ascending price pattern")
        elif context['price_pattern'] == 'DESCENDING':
            bearish_score += 1
            reasoning_points.append("Descending price pattern")
        elif context['price_pattern'] == 'V_RECOVERY':
            bullish_score += 1.5
            reasoning_points.append("V-shaped recovery pattern")
        
        # Reasoning based on volume
        if context['volume_profile'] in ['INCREASING', 'SLIGHTLY_INCREASING']:
            if bullish_score > bearish_score:
                bullish_score += 0.5
                reasoning_points.append("Volume confirms bullish move")
            elif bearish_score > bullish_score:
                bearish_score += 0.5
                reasoning_points.append("Volume confirms bearish move")
        
        # Reasoning based on volatility
        if context['volatility_regime'] == 'HIGH':
            reasoning_points.append("High volatility - reduce confidence")
            bullish_score *= 0.8
            bearish_score *= 0.8
        elif context['volatility_regime'] == 'LOW':
            reasoning_points.append("Low volatility - ideal for trend following")
            bullish_score *= 1.2
            bearish_score *= 1.2
        
        # Make decision
        max_score = 8.0
        if bullish_score > bearish_score and bullish_score > 3:
            confidence = min(bullish_score / max_score, 1.0)
            reasoning = " | ".join(reasoning_points)
            return 'LONG', confidence, reasoning
        elif bearish_score > bullish_score and bearish_score > 3:
            confidence = min(bearish_score / max_score, 1.0)
            reasoning = " | ".join(reasoning_points)
            return 'SHORT', confidence, reasoning
        else:
            return None, 0.0, "Insufficient evidence for trade"
    
    def update_pattern_memory(self, context: Dict, outcome: bool):
        """Learn from outcomes"""
        pattern_key = f"{context['price_trend']}_{context['momentum_state']}_{context['price_pattern']}"
        
        if outcome:
            self.pattern_outcomes[pattern_key]['success'] += 1
        else:
            self.pattern_outcomes[pattern_key]['failure'] += 1
        
        # Store in memory
        self.pattern_memory.append({
            'context': context,
            'outcome': outcome
        })
        
        # Limit memory size
        if len(self.pattern_memory) > self.pattern_memory_size:
            self.pattern_memory.pop(0)
    
    def adjust_confidence_with_memory(self, context: Dict, initial_confidence: float) -> float:
        """Adjust confidence based on historical pattern success"""
        pattern_key = f"{context['price_trend']}_{context['momentum_state']}_{context['price_pattern']}"
        
        if pattern_key in self.pattern_outcomes:
            stats = self.pattern_outcomes[pattern_key]
            total = stats['success'] + stats['failure']
            
            if total > 5:
                success_rate = stats['success'] / total
                # Adjust confidence based on historical success
                adjusted_confidence = initial_confidence * (0.5 + success_rate)
                return min(adjusted_confidence, 1.0)
        
        return initial_confidence
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals using LLM-inspired reasoning"""
        signals = []
        position = None
        
        for i in range(20, len(data)):
            current_idx = data.index[i]
            current_price = data.loc[current_idx, 'close']
            
            # Extract context
            context = self.extract_market_context(data, i)
            
            if not context or position is not None:
                continue
            
            # Reason about action
            action, confidence, reasoning = self.reason_about_context(context)
            
            # Adjust confidence with memory
            adjusted_confidence = self.adjust_confidence_with_memory(context, confidence)
            
            if action and adjusted_confidence > self.confidence_threshold:
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type=action,
                    price=current_price,
                    confidence=adjusted_confidence,
                    metadata={
                        'context': context,
                        'reasoning': reasoning,
                        'initial_confidence': confidence,
                        'adjusted_confidence': adjusted_confidence
                    }
                ))
                position = action
            
            # Exit management
            elif position:
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                entry_context = entry_signal.metadata['context']
                
                if position == 'LONG':
                    profit_pct = (current_price - entry_price) / entry_price
                else:
                    profit_pct = (entry_price - current_price) / entry_price
                
                # Exit on target, stop, or context change
                current_context = self.extract_market_context(data, i)
                context_changed = (current_context.get('price_trend') != entry_context.get('price_trend') or
                                 current_context.get('momentum_state') != entry_context.get('momentum_state'))
                
                if profit_pct > 0.05 or profit_pct < -0.02 or context_changed:
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type=f'EXIT_{position}',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct, 'reason': 'target/stop/context_change'}
                    ))
                    
                    # Learn from outcome
                    self.update_pattern_memory(entry_context, profit_pct > 0)
                    
                    position = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on reasoning confidence"""
        base_risk = self.current_capital * self.risk_per_trade
        
        adjusted_confidence = signal.metadata['adjusted_confidence']
        confidence_multiplier = adjusted_confidence * 1.5
        
        adjusted_risk = base_risk * confidence_multiplier
        position_size = adjusted_risk / current_price
        
        return position_size
