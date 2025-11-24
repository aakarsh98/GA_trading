"""
Composite Edge Scoring System
Combines all research-backed indicators into a single confidence score
Provides real-time trading edge assessment (0-1 scale)
"""

import numpy as np
import pandas as pd
from typing import Optional


class EdgeScoringSystem:
    """
    Composite edge scoring combining multiple research-backed indicators.
    
    Components:
    1. Base Momentum Edge (40% weight)
    2. Lead-Lag Edge (25% weight) - cross-timeframe correlation
    3. Survival Edge (30% weight) - signal age and decay
    4. HMM Edge (20% weight) - regime detection
    5. Statistical Arbitrage (10% weight) - mean reversion extreme
    6. Attention Edge (15% weight) - multi-timeframe consistency
    
    Total weights > 100% to allow for dynamic adjustments.
    Final score is normalized and adjusted for volatility.
    """
    
    def __init__(self, 
                 base_weight: float = 0.4,
                 leadlag_weight: float = 0.25,
                 survival_weight: float = 0.30,
                 hmm_weight: float = 0.20,
                 statarb_weight: float = 0.10,
                 attention_weight: float = 0.15):
        """
        Initialize Edge Scoring System.
        
        Args:
            base_weight: Weight for base momentum edge
            leadlag_weight: Weight for lead-lag detection
            survival_weight: Weight for survival analysis
            hmm_weight: Weight for HMM regime detection
            statarb_weight: Weight for statistical arbitrage
            attention_weight: Weight for attention mechanism
        """
        self.base_weight = base_weight
        self.leadlag_weight = leadlag_weight
        self.survival_weight = survival_weight
        self.hmm_weight = hmm_weight
        self.statarb_weight = statarb_weight
        self.attention_weight = attention_weight
    
    def calculate(self,
                 data: pd.DataFrame,
                 momentum: pd.DataFrame,
                 survival: Optional[pd.DataFrame] = None,
                 regime: Optional[pd.DataFrame] = None,
                 momentum_threshold: float = 3.0) -> pd.DataFrame:
        """
        Calculate composite edge scores.
        
        Args:
            data: OHLCV DataFrame
            momentum: Momentum tracker results
            survival: Survival analysis results (optional)
            regime: HMM regime detection results (optional)
            momentum_threshold: Threshold for momentum normalization
            
        Returns:
            DataFrame with edge components and composite score
        """
        # 1. Base Momentum Edge (normalized 0-1)
        base_edge = self._calculate_base_edge(momentum, momentum_threshold)
        
        # 2. Lead-Lag Edge (cross-timeframe correlation)
        leadlag_edge = self._calculate_leadlag_edge(momentum)
        
        # 3. Survival Edge (from survival analysis or calculate basic version)
        if survival is not None:
            survival_edge = survival['SurvivalEdge']
        else:
            survival_edge = pd.Series(1.0, index=data.index)
        
        # 4. HMM Edge (from regime detection or use default)
        if regime is not None:
            hmm_edge = regime['HMMEdge']
        else:
            hmm_edge = pd.Series(0.4, index=data.index)
        
        # 5. Statistical Arbitrage Edge (mean reversion extremes)
        statarb_edge = self._calculate_statarb_edge(data)
        
        # 6. Attention Edge (multi-timeframe consistency)
        attention_edge = self._calculate_attention_edge(momentum)
        
        # Calculate volatility adjustment
        volatility_adjustment = self._calculate_volatility_adjustment(data)
        
        # Combine all edges with weights
        composite_edge = (
            self.base_weight * base_edge +
            self.leadlag_weight * leadlag_edge +
            self.survival_weight * survival_edge +
            self.hmm_weight * hmm_edge +
            self.statarb_weight * statarb_edge +
            self.attention_weight * attention_edge
        ) * volatility_adjustment
        
        # Normalize to 0-1 range
        composite_edge = np.clip(composite_edge, 0, 1)
        
        # Classify edge strength
        edge_classification = pd.Series('Weak', index=data.index)
        edge_classification[composite_edge >= 0.6] = 'Medium'
        edge_classification[composite_edge >= 0.8] = 'Strong'
        
        # Create result DataFrame
        result = pd.DataFrame({
            'BaseEdge': base_edge,
            'LeadLagEdge': leadlag_edge,
            'SurvivalEdge': survival_edge,
            'HMMEdge': hmm_edge,
            'StatArbEdge': statarb_edge,
            'AttentionEdge': attention_edge,
            'VolatilityAdjustment': volatility_adjustment,
            'CompositeEdge': composite_edge,
            'EdgeClassification': edge_classification
        }, index=data.index)
        
        return result
    
    def _calculate_base_edge(self, momentum: pd.DataFrame, threshold: float) -> pd.Series:
        """Calculate base momentum edge (normalized)."""
        deviation = (momentum['Momentum'] - momentum['Equilibrium']).abs()
        base_edge = np.minimum(deviation / threshold, 1.0)
        return base_edge
    
    def _calculate_leadlag_edge(self, momentum: pd.DataFrame) -> pd.Series:
        """
        Calculate lead-lag edge using momentum autocorrelation.
        Simpler version without multi-timeframe data.
        """
        # Use lagged correlation as proxy for lead-lag relationship
        mom_series = momentum['Momentum']
        
        # Calculate correlation with lagged version
        correlation = mom_series.rolling(window=50).corr(mom_series.shift(5))
        
        # Normalize to 0-1 (correlation is -1 to 1)
        # Higher correlation = stronger edge
        leadlag_edge = np.maximum(correlation, 0) / 0.7  # Normalize by 0.7 as in research
        leadlag_edge = np.clip(leadlag_edge, 0, 1)
        
        # Fill NaN with neutral value
        leadlag_edge = leadlag_edge.fillna(0.5)
        
        return leadlag_edge
    
    def _calculate_statarb_edge(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate statistical arbitrage edge (mean reversion).
        Higher edge during extreme deviations.
        """
        from indicators.utils import sma, stdev
        
        # Calculate z-score
        close = data['Close']
        mean = sma(close, 50)
        std = stdev(close, 50)
        
        z_score = (close - mean) / (std + 1e-10)  # Add small value to avoid division by zero
        
        # Edge increases with extreme z-scores
        # Long edge increases when z < -2.5 (oversold)
        # Short edge decreases when z > 2.5 (overbought)
        statarb_edge = pd.Series(1.0, index=data.index)
        
        # Enhance edge for extreme oversold (good for longs)
        oversold = z_score < -2.5
        statarb_edge[oversold] = np.minimum(z_score[oversold].abs() / 2.5, 2.0)
        
        # Reduce edge for extreme overbought (bad for longs)
        overbought = z_score > 2.5
        statarb_edge[overbought] = 0.6
        
        # Fill NaN
        statarb_edge = statarb_edge.fillna(1.0)
        
        return statarb_edge
    
    def _calculate_attention_edge(self, momentum: pd.DataFrame) -> pd.Series:
        """
        Calculate attention edge (multi-scale consistency).
        Measures consistency of momentum across different lookback periods.
        """
        mom = momentum['Momentum']
        
        # Calculate momentum at different scales
        short_mom = mom.rolling(window=5).mean()
        medium_mom = mom.rolling(window=20).mean()
        long_mom = mom.rolling(window=50).mean()
        
        # Calculate consistency (low standard deviation = high consistency)
        consistency = pd.Series(index=mom.index, dtype=float)
        
        for i in range(len(mom)):
            if i >= 50:
                values = [
                    short_mom.iloc[i],
                    medium_mom.iloc[i],
                    long_mom.iloc[i]
                ]
                if not any(pd.isna(values)):
                    stdev = np.std(values)
                    mean_val = np.mean(values)
                    # Normalize: lower relative stdev = higher edge
                    relative_stdev = stdev / (abs(mean_val) + 0.001)
                    # Anomaly when inconsistent (high stdev)
                    if relative_stdev > 0.3:
                        consistency.iloc[i] = 0.0  # Anomaly detected
                    else:
                        consistency.iloc[i] = 1.0  # Consistent
                else:
                    consistency.iloc[i] = 1.0
            else:
                consistency.iloc[i] = 1.0
        
        return consistency.fillna(1.0)
    
    def _calculate_volatility_adjustment(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate volatility adjustment factor.
        Lower volatility = higher confidence in signals.
        """
        from indicators.utils import atr
        
        atr_values = atr(data, 14)
        volatility_pct = (atr_values / data['Close']) * 100
        
        # Adjust: 2.0 / (volatility% + 1)
        # Higher volatility = lower adjustment (more conservative)
        adjustment = 2.0 / (volatility_pct + 1.0)
        
        return adjustment
    
    def get_trading_decision(self, edge_score: float, 
                            high_threshold: float = 0.8,
                            medium_threshold: float = 0.6) -> dict:
        """
        Get trading decision based on edge score.
        
        Args:
            edge_score: Composite edge score (0-1)
            high_threshold: Threshold for high confidence (default 0.8)
            medium_threshold: Threshold for medium confidence (default 0.6)
            
        Returns:
            Dictionary with trading decision
        """
        if edge_score >= high_threshold:
            return {
                'decision': 'STRONG_TRADE',
                'confidence': 'High',
                'position_size_multiplier': 1.4,
                'description': 'Strong edge detected - maximize position'
            }
        elif edge_score >= medium_threshold:
            return {
                'decision': 'TRADE',
                'confidence': 'Medium',
                'position_size_multiplier': 1.0,
                'description': 'Moderate edge - normal position size'
            }
        else:
            return {
                'decision': 'AVOID',
                'confidence': 'Low',
                'position_size_multiplier': 0.7,
                'description': 'Weak edge - reduce risk or avoid'
            }
    
    def plot_edge_components(self, edge: pd.DataFrame):
        """
        Plot all edge components and composite score.
        
        Args:
            edge: Edge scoring results
        """
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        
        # Plot 1: Individual edge components
        axes[0].plot(edge.index, edge['BaseEdge'], label='Base Edge', alpha=0.7)
        axes[0].plot(edge.index, edge['LeadLagEdge'], label='Lead-Lag', alpha=0.7)
        axes[0].plot(edge.index, edge['SurvivalEdge'], label='Survival', alpha=0.7)
        axes[0].plot(edge.index, edge['HMMEdge'], label='HMM', alpha=0.7)
        axes[0].plot(edge.index, edge['AttentionEdge'], label='Attention', alpha=0.7)
        axes[0].set_ylabel('Edge (0-1)')
        axes[0].set_title('Edge Components')
        axes[0].legend(loc='upper left', fontsize=8)
        axes[0].grid(True, alpha=0.3)
        
        # Plot 2: Composite edge with thresholds
        axes[1].plot(edge.index, edge['CompositeEdge'], 
                    label='Composite Edge', color='purple', linewidth=2)
        axes[1].axhline(y=0.8, color='green', linestyle='--', 
                       alpha=0.5, label='Strong (0.8)')
        axes[1].axhline(y=0.6, color='orange', linestyle='--', 
                       alpha=0.5, label='Medium (0.6)')
        
        # Fill zones
        axes[1].fill_between(edge.index, 0, edge['CompositeEdge'],
                            where=edge['CompositeEdge'] >= 0.8,
                            color='green', alpha=0.3, label='Strong Zone')
        axes[1].fill_between(edge.index, 0, edge['CompositeEdge'],
                            where=(edge['CompositeEdge'] >= 0.6) & (edge['CompositeEdge'] < 0.8),
                            color='orange', alpha=0.3, label='Medium Zone')
        axes[1].fill_between(edge.index, 0, edge['CompositeEdge'],
                            where=edge['CompositeEdge'] < 0.6,
                            color='red', alpha=0.3, label='Weak Zone')
        
        axes[1].set_ylabel('Composite Edge')
        axes[1].legend(loc='upper left')
        axes[1].grid(True, alpha=0.3)
        
        # Plot 3: Edge classification distribution
        classification_counts = edge['EdgeClassification'].value_counts()
        axes[2].bar(range(len(classification_counts)), classification_counts.values,
                   tick_label=classification_counts.index,
                   color=['red', 'orange', 'green'])
        axes[2].set_ylabel('Count')
        axes[2].set_xlabel('Edge Classification')
        axes[2].set_title('Edge Distribution')
        axes[2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return fig, axes


def main():
    """Demo usage of EdgeScoringSystem."""
    import sys
    sys.path.append('..')
    from data.collector import DataCollector
    from indicators.momentum_tracker import MomentumTracker
    from indicators.survival_analysis import SurvivalAnalysisFilter
    from indicators.hmm_regime import HMMRegimeDetector
    
    print("=== Edge Scoring System Demo ===\n")
    
    # Fetch data
    collector = DataCollector()
    print("Fetching BTC-USD data...")
    data = collector.fetch_data('BTC-USD', timeframe='1h', period='1mo')
    
    # Calculate momentum
    print("Calculating momentum...")
    mt = MomentumTracker()
    momentum = mt.calculate(data)
    
    # Calculate survival analysis
    print("Calculating survival analysis...")
    saf = SurvivalAnalysisFilter()
    survival = saf.calculate(momentum)
    
    # Detect regimes
    print("Detecting regimes...")
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    # Calculate composite edge
    print("Calculating composite edge scores...")
    edge_system = EdgeScoringSystem()
    edge = edge_system.calculate(data, momentum, survival, regime)
    
    # Show statistics
    print(f"\nEdge Score Statistics:")
    print(f"Mean Composite Edge: {edge['CompositeEdge'].mean():.3f}")
    print(f"Max Composite Edge: {edge['CompositeEdge'].max():.3f}")
    print(f"Min Composite Edge: {edge['CompositeEdge'].min():.3f}")
    print(f"Std Composite Edge: {edge['CompositeEdge'].std():.3f}")
    
    # Edge classification distribution
    print(f"\nEdge Classification Distribution:")
    class_counts = edge['EdgeClassification'].value_counts()
    for classification, count in class_counts.items():
        pct = count / len(edge) * 100
        print(f"{classification}: {count} bars ({pct:.1f}%)")
    
    # Show last 10 values
    print(f"\nLast 10 Composite Edge Scores:")
    print(edge[['CompositeEdge', 'EdgeClassification']].tail(10))
    
    # Current edge and decision
    current = edge.iloc[-1]
    decision = edge_system.get_trading_decision(current['CompositeEdge'])
    
    print(f"\nCurrent Edge Analysis:")
    print(f"Composite Edge: {current['CompositeEdge']:.3f}")
    print(f"Classification: {current['EdgeClassification']}")
    print(f"\nTrading Decision:")
    print(f"Decision: {decision['decision']}")
    print(f"Confidence: {decision['confidence']}")
    print(f"Position Size Multiplier: {decision['position_size_multiplier']}x")
    print(f"Description: {decision['description']}")
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    main()
