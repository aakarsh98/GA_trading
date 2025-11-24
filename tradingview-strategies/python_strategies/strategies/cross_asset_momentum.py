"""
Cross-Asset Momentum Analysis Strategy
Based on: Cross-market momentum research & International validation (2024)
Expected Performance: International validation improvements
Complexity: High

Analyzes momentum across multiple related assets for signal confirmation
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.base_strategy import BaseStrategy, Signal
from utils.indicators import calculate_correlation, calculate_momentum


class CrossAssetMomentum(BaseStrategy):
    """
    Multi-asset momentum strategy with cross-correlation analysis
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 momentum_threshold: float = 0.02,
                 correlation_threshold: float = 0.6,
                 lookback_period: int = 20,
                 risk_per_trade: float = 0.01):
        super().__init__("Cross-Asset Momentum", initial_capital)
        self.momentum_threshold = momentum_threshold
        self.correlation_threshold = correlation_threshold
        self.lookback_period = lookback_period
        self.risk_per_trade = risk_per_trade
        
    def create_synthetic_related_assets(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Create synthetic 'related' assets for demonstration
        In production, you would use actual related market data
        """
        # Simulate related assets with various correlation levels
        related_assets = {}
        
        # High correlation asset (e.g., correlated sector stock)
        noise_high = np.random.normal(0, 0.02, len(data))
        related_assets['high_corr'] = data['close'] * (1 + noise_high)
        
        # Medium correlation asset (e.g., related commodity)
        noise_med = np.random.normal(0, 0.05, len(data))
        related_assets['med_corr'] = data['close'] * (1 + noise_med) * 1.1
        
        # Market index proxy
        smoothed = data['close'].rolling(5).mean()
        noise_idx = np.random.normal(0, 0.01, len(data))
        related_assets['market_index'] = smoothed * (1 + noise_idx)
        
        return related_assets
    
    def calculate_cross_asset_momentum_score(self, 
                                            data: pd.DataFrame,
                                            related_assets: Dict[str, pd.Series],
                                            idx: int) -> Tuple[float, Dict]:
        """Calculate momentum score across multiple assets"""
        if idx < self.lookback_period:
            return 0.0, {}
        
        # Calculate primary asset momentum
        primary_momentum = (data['close'].iloc[idx] - data['close'].iloc[idx-self.lookback_period]) / data['close'].iloc[idx-self.lookback_period]
        
        # Calculate momentum for related assets
        related_momentums = {}
        momentum_agreement = 0
        total_weight = 0
        
        for asset_name, asset_prices in related_assets.items():
            if idx < len(asset_prices):
                asset_momentum = (asset_prices.iloc[idx] - asset_prices.iloc[idx-self.lookback_period]) / asset_prices.iloc[idx-self.lookback_period]
                
                # Calculate correlation as weight
                lookback_data = data['close'].iloc[idx-self.lookback_period:idx]
                asset_lookback = asset_prices.iloc[idx-self.lookback_period:idx]
                
                correlation = lookback_data.corr(asset_lookback)
                weight = abs(correlation) if abs(correlation) > self.correlation_threshold else 0
                
                related_momentums[asset_name] = {
                    'momentum': asset_momentum,
                    'correlation': correlation,
                    'weight': weight
                }
                
                # Agreement score
                if np.sign(asset_momentum) == np.sign(primary_momentum):
                    momentum_agreement += weight
                
                total_weight += weight
        
        # Normalized momentum agreement score
        agreement_score = momentum_agreement / total_weight if total_weight > 0 else 0
        
        # Combined momentum strength
        weighted_momentum = primary_momentum
        for asset_name, metrics in related_momentums.items():
            if metrics['weight'] > 0:
                weighted_momentum += metrics['momentum'] * metrics['weight']
        
        if total_weight > 0:
            weighted_momentum /= (1 + total_weight)
        
        score_components = {
            'primary_momentum': primary_momentum,
            'weighted_momentum': weighted_momentum,
            'agreement_score': agreement_score,
            'related_assets': related_momentums
        }
        
        # Final score: combination of momentum strength and cross-asset agreement
        final_score = abs(weighted_momentum) * agreement_score
        
        return final_score, score_components
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate cross-asset momentum signals"""
        signals = []
        
        # Create synthetic related assets
        related_assets = self.create_synthetic_related_assets(data)
        
        position = None
        
        for i in range(self.lookback_period + 10, len(data)):
            current_idx = data.index[i]
            current_price = data.loc[current_idx, 'close']
            
            # Calculate cross-asset momentum score
            momentum_score, components = self.calculate_cross_asset_momentum_score(
                data, related_assets, i
            )
            
            primary_momentum = components['primary_momentum']
            agreement_score = components['agreement_score']
            
            # Long signal: Strong positive momentum with cross-asset confirmation
            if (primary_momentum > self.momentum_threshold and
                agreement_score > 0.6 and
                momentum_score > 0.015 and
                position is None):
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='LONG',
                    price=current_price,
                    confidence=agreement_score,
                    metadata={
                        'momentum_score': momentum_score,
                        'primary_momentum': primary_momentum,
                        'agreement_score': agreement_score,
                        'components': components
                    }
                ))
                position = 'LONG'
            
            # Short signal: Strong negative momentum with cross-asset confirmation
            elif (primary_momentum < -self.momentum_threshold and
                  agreement_score > 0.6 and
                  momentum_score > 0.015 and
                  position is None):
                
                signals.append(Signal(
                    timestamp=current_idx,
                    signal_type='SHORT',
                    price=current_price,
                    confidence=agreement_score,
                    metadata={
                        'momentum_score': momentum_score,
                        'primary_momentum': primary_momentum,
                        'agreement_score': agreement_score,
                        'components': components
                    }
                ))
                position = 'SHORT'
            
            # Exit management
            if position == 'LONG':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                profit_pct = (current_price - entry_price) / entry_price
                
                # Check if momentum weakens
                current_score, current_components = self.calculate_cross_asset_momentum_score(
                    data, related_assets, i
                )
                
                if (current_components['primary_momentum'] < 0 or
                    current_components['agreement_score'] < 0.4 or
                    profit_pct > 0.06 or
                    profit_pct < -0.025):
                    
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_LONG',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct}
                    ))
                    position = None
            
            elif position == 'SHORT':
                entry_signal = signals[-1]
                entry_price = entry_signal.price
                profit_pct = (entry_price - current_price) / entry_price
                
                current_score, current_components = self.calculate_cross_asset_momentum_score(
                    data, related_assets, i
                )
                
                if (current_components['primary_momentum'] > 0 or
                    current_components['agreement_score'] < 0.4 or
                    profit_pct > 0.06 or
                    profit_pct < -0.025):
                    
                    signals.append(Signal(
                        timestamp=current_idx,
                        signal_type='EXIT_SHORT',
                        price=current_price,
                        confidence=1.0,
                        metadata={'profit_pct': profit_pct}
                    ))
                    position = None
        
        return signals
    
    def calculate_position_size(self, signal: Signal, current_price: float) -> float:
        """Calculate position size based on cross-asset agreement"""
        base_risk = self.current_capital * self.risk_per_trade
        
        agreement_score = signal.metadata['agreement_score']
        momentum_score = signal.metadata['momentum_score']
        
        # Higher position size when cross-asset signals align strongly
        confidence_multiplier = agreement_score * min(momentum_score * 30, 1.5)
        
        adjusted_risk = base_risk * confidence_multiplier
        position_size = adjusted_risk / current_price
        
        return position_size
