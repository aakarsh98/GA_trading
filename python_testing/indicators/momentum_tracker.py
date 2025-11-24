"""
Momentum Tracker Indicator
Implements the proprietary triple-layer exponential smoothing algorithm
Matches the TradingView PineScript implementation exactly
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, Optional


class MomentumTracker:
    """
    Advanced Momentum Oscillator using triple-layer exponential smoothing.
    
    The indicator oscillates between 0-100 with:
    - Blue (bullish): Momentum broke above equilibrium
    - Red (bearish): Momentum broke below equilibrium
    - Yellow (neutral): Within equilibrium threshold
    
    Key Features:
    - Triple-layer exponential smoothing for noise reduction
    - Dynamic equilibrium level detection
    - Breakthrough momentum detection
    """
    
    def __init__(self, length: int = 7, threshold: float = 2.0):
        """
        Initialize Momentum Tracker.
        
        Args:
            length: Smoothing period (default 7, protected value)
            threshold: Breakthrough threshold for color changes (default 2.0)
        """
        self.length = length
        self.threshold = threshold
        self.reset()
    
    def reset(self):
        """Reset all internal state variables."""
        # State variables (matching PineScript var declarations)
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
        
        # Calculation variables
        self.v32 = 0.0
        self.v40 = 0.0
        self.v48 = 0.0
        self.v56 = 0.0
        self.v64 = 0.0
        self.v72 = 0.0
        self.v144 = 0.0
        
        # Equilibrium tracking
        self.equilibrium_level = 50.0
        self.prev_v24 = 50.0
        self.prev_prev_v24 = 50.0
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate momentum tracker values for the entire dataset.
        
        Args:
            data: DataFrame with OHLC columns
            
        Returns:
            DataFrame with momentum values and signals
        """
        # Calculate typical price
        tp = (data['High'] + data['Low'] + data['Close']) / 3.0
        
        # Initialize result arrays
        momentum_values = np.zeros(len(data))
        equilibrium_levels = np.zeros(len(data))
        signals = np.zeros(len(data))  # 1=bullish, -1=bearish, 0=neutral
        colors = ['yellow'] * len(data)
        
        # Reset state for fresh calculation
        self.reset()
        
        # Process each bar
        for i in range(len(data)):
            v24 = self._process_bar(tp.iloc[i])
            momentum_values[i] = v24
            equilibrium_levels[i] = self.equilibrium_level
            
            # Determine signal and color
            signal, color = self._determine_signal(v24)
            signals[i] = signal
            colors[i] = color
            
            # Update history
            self.prev_prev_v24 = self.prev_v24
            self.prev_v24 = v24
        
        # Create result DataFrame
        result = pd.DataFrame({
            'Momentum': momentum_values,
            'Equilibrium': equilibrium_levels,
            'Signal': signals,
            'Color': colors
        }, index=data.index)
        
        return result
    
    def _process_bar(self, tp: float) -> float:
        """
        Process a single bar through the momentum calculation.
        Matches PineScript algorithm exactly.
        
        Args:
            tp: Typical price (H+L+C)/3
            
        Returns:
            Momentum value (0-100)
        """
        v24 = 50.0
        
        if self.v8 == 0.0:
            # Initialize on first bar
            self.v8 = 1.0
            self.v16 = 0.0
            self.v0 = max(self.length - 1, 5.0)
            self.v80 = 100.0 * tp
            self.v96 = 3.0 / (self.length + 2.0)
            self.v104 = 1.0 - self.v96
        else:
            # Update bar counter
            if self.v0 <= self.v8:
                self.v8 = self.v0 + 1.0
            else:
                self.v8 = self.v8 + 1.0
            
            # Store previous price
            self.v88 = self.v80
            self.v80 = 100.0 * tp
            
            # Price change
            self.v32 = self.v80 - self.v88
            
            # === FIRST SMOOTHING LAYER ===
            self.v112 = self.v104 * self.v112 + self.v96 * self.v32
            self.v120 = self.v96 * self.v112 + self.v104 * self.v120
            self.v40 = 1.5 * self.v112 - self.v120 / 2.0
            
            # === SECOND SMOOTHING LAYER ===
            self.v128 = self.v104 * self.v128 + self.v96 * self.v40
            self.v208 = self.v96 * self.v128 + self.v104 * self.v208
            self.v48 = 1.5 * self.v128 - self.v208 / 2.0
            
            # === THIRD SMOOTHING LAYER ===
            self.v136 = self.v104 * self.v136 + self.v96 * self.v48
            self.v152 = self.v96 * self.v136 + self.v104 * self.v152
            self.v56 = 1.5 * self.v136 - self.v152 / 2.0
            
            # === ABSOLUTE VALUE SMOOTHING - FIRST LAYER ===
            self.v160 = self.v104 * self.v160 + self.v96 * abs(self.v32)
            self.v168 = self.v96 * self.v160 + self.v104 * self.v168
            self.v64 = 1.5 * self.v160 - self.v168 / 2.0
            
            # === ABSOLUTE VALUE SMOOTHING - SECOND LAYER ===
            self.v176 = self.v104 * self.v176 + self.v96 * self.v64
            self.v184 = self.v96 * self.v176 + self.v104 * self.v184
            self.v144 = 1.5 * self.v176 - self.v184 / 2.0
            
            # === ABSOLUTE VALUE SMOOTHING - THIRD LAYER ===
            self.v192 = self.v104 * self.v192 + self.v96 * self.v144
            self.v200 = self.v96 * self.v192 + self.v104 * self.v200
            self.v72 = 1.5 * self.v192 - self.v200 / 2.0
            
            # Update flags
            if self.v0 >= self.v8 and self.v80 != self.v88:
                self.v16 = 1.0
            
            if self.v0 == self.v8 and self.v16 == 0.0:
                self.v8 = 0.0
        
        # Calculate final indicator value
        if self.v0 < self.v8 and self.v72 > 0.0000000001:
            v24 = 50.0 * (self.v56 / self.v72 + 1.0)
            # Clamp between 0 and 100
            v24 = max(0.0, min(100.0, v24))
        else:
            v24 = 50.0
        
        # Update equilibrium level on trend changes
        current_change = v24 - self.prev_v24
        previous_change = self.prev_v24 - self.prev_prev_v24
        
        trend_changed = (
            (current_change > 0 and previous_change <= 0) or
            (current_change < 0 and previous_change >= 0)
        )
        
        if trend_changed or self.equilibrium_level == 50.0:
            self.equilibrium_level = v24
        
        return v24
    
    def _determine_signal(self, v24: float) -> Tuple[int, str]:
        """
        Determine trading signal based on momentum vs equilibrium.
        
        Args:
            v24: Current momentum value
            
        Returns:
            Tuple of (signal, color)
            signal: 1 (bullish), -1 (bearish), 0 (neutral)
            color: 'blue', 'red', or 'yellow'
        """
        deviation = abs(v24 - self.equilibrium_level)
        
        if deviation <= self.threshold:
            # Within equilibrium zone - neutral
            return 0, 'yellow'
        elif v24 > self.equilibrium_level + self.threshold:
            # Broke above equilibrium - bullish
            return 1, 'blue'
        elif v24 < self.equilibrium_level - self.threshold:
            # Broke below equilibrium - bearish
            return -1, 'red'
        else:
            return 0, 'yellow'
    
    def plot(self, data: pd.DataFrame, momentum: Optional[pd.DataFrame] = None, 
             title: str = "Momentum Tracker", figsize: Tuple[int, int] = (14, 10)):
        """
        Plot momentum tracker with price chart.
        
        Args:
            data: OHLC DataFrame
            momentum: Pre-calculated momentum (optional, will calculate if None)
            title: Plot title
            figsize: Figure size
        """
        if momentum is None:
            momentum = self.calculate(data)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                        gridspec_kw={'height_ratios': [2, 1]})
        
        # Plot price
        ax1.plot(data.index, data['Close'], label='Close', color='black', linewidth=1)
        ax1.set_title(f'{title} - Price Chart')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot momentum with color coding
        for i in range(len(momentum) - 1):
            color = momentum['Color'].iloc[i]
            color_map = {'blue': '#1E90FF', 'red': 'red', 'yellow': 'yellow'}
            ax2.plot(momentum.index[i:i+2], momentum['Momentum'].iloc[i:i+2], 
                    color=color_map[color], linewidth=2)
        
        # Plot equilibrium level
        ax2.plot(momentum.index, momentum['Equilibrium'], 
                color='gray', linewidth=1, linestyle='--', alpha=0.5, label='Equilibrium')
        
        # Add reference levels
        ax2.axhline(y=90, color='gray', linestyle=':', alpha=0.3, label='Overbought (90)')
        ax2.axhline(y=50, color='gray', linestyle=':', alpha=0.3, label='Midline (50)')
        ax2.axhline(y=10, color='gray', linestyle=':', alpha=0.3, label='Oversold (10)')
        
        # Fill zones
        ax2.fill_between(momentum.index, 90, 100, color='red', alpha=0.1)
        ax2.fill_between(momentum.index, 0, 10, color='blue', alpha=0.1)
        
        ax2.set_title('Momentum Tracker')
        ax2.set_ylabel('Momentum (0-100)')
        ax2.set_xlabel('Date')
        ax2.set_ylim(-5, 105)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, (ax1, ax2)
    
    def get_current_signal(self, data: pd.DataFrame) -> dict:
        """
        Get current momentum signal and statistics.
        
        Args:
            data: OHLC DataFrame
            
        Returns:
            Dictionary with signal information
        """
        momentum = self.calculate(data)
        latest = momentum.iloc[-1]
        
        return {
            'momentum': latest['Momentum'],
            'equilibrium': latest['Equilibrium'],
            'signal': latest['Signal'],
            'color': latest['Color'],
            'signal_name': {1: 'BULLISH', -1: 'BEARISH', 0: 'NEUTRAL'}[latest['Signal']],
            'deviation': abs(latest['Momentum'] - latest['Equilibrium']),
            'strength': abs(latest['Momentum'] - latest['Equilibrium']) / self.threshold
        }


def main():
    """Demo usage of MomentumTracker."""
    import sys
    sys.path.append('..')
    from data.collector import DataCollector
    
    print("=== Momentum Tracker Demo ===\n")
    
    # Fetch data
    collector = DataCollector()
    print("Fetching BTC-USD hourly data...")
    data = collector.fetch_data('BTC-USD', timeframe='1h', period='1mo')
    
    # Calculate momentum
    print("Calculating momentum...")
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    # Show statistics
    print(f"\nMomentum Statistics:")
    print(f"Mean: {momentum['Momentum'].mean():.2f}")
    print(f"Std: {momentum['Momentum'].std():.2f}")
    print(f"Min: {momentum['Momentum'].min():.2f}")
    print(f"Max: {momentum['Momentum'].max():.2f}")
    
    # Show signal distribution
    print(f"\nSignal Distribution:")
    print(f"Bullish: {(momentum['Signal'] == 1).sum()} bars ({(momentum['Signal'] == 1).sum()/len(momentum)*100:.1f}%)")
    print(f"Bearish: {(momentum['Signal'] == -1).sum()} bars ({(momentum['Signal'] == -1).sum()/len(momentum)*100:.1f}%)")
    print(f"Neutral: {(momentum['Signal'] == 0).sum()} bars ({(momentum['Signal'] == 0).sum()/len(momentum)*100:.1f}%)")
    
    # Get current signal
    current = mt.get_current_signal(data)
    print(f"\nCurrent Signal:")
    print(f"Momentum: {current['momentum']:.2f}")
    print(f"Equilibrium: {current['equilibrium']:.2f}")
    print(f"Signal: {current['signal_name']} ({current['color']})")
    print(f"Strength: {current['strength']:.2f}x threshold")
    
    # Show last 10 values
    print(f"\nLast 10 Momentum Values:")
    print(momentum[['Momentum', 'Equilibrium', 'Signal', 'Color']].tail(10))
    
    # Create visualization
    print("\nGenerating plot...")
    try:
        fig, axes = mt.plot(data, momentum, title="BTC-USD Momentum Tracker")
        plt.savefig('momentum_tracker_demo.png', dpi=100, bbox_inches='tight')
        print("Plot saved as 'momentum_tracker_demo.png'")
    except Exception as e:
        print(f"Could not save plot: {e}")
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    main()
