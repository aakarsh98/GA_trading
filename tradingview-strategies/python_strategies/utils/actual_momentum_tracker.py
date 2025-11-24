"""
YOUR ACTUAL MOMENTUM TRACKER
Exact implementation from Pine Script - NO SIMPLIFICATIONS

This is the REAL momentum calculation used in your strategy.
All research tests should import this module.
"""
import numpy as np
import pandas as pd


class ActualMomentumTracker:
    """
    YOUR exact momentum tracker from Pine Script
    
    Features:
    - Triple-layer EMA smoothing
    - Noise normalization (absolute value smoothing)
    - Dynamic equilibrium detection
    - Threshold-based signals
    """
    
    def __init__(self, length: int = 7, threshold: float = 2.0):
        self.length = length
        self.threshold = threshold
        
        # State variables (from Pine Script)
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
    
    def reset(self):
        """Reset state variables"""
        self.__init__(self.length, self.threshold)
    
    def calculate_single(self, high: float, low: float, close: float) -> float:
        """
        Calculate momentum for a single bar
        
        Args:
            high: High price
            low: Low price
            close: Close price
        
        Returns:
            Momentum value (0-100)
        """
        # Typical price
        tp = (high + low + close) / 3.0
        
        # Default value
        v24 = 50.0
        
        # Main calculation (exact from Pine Script)
        if self.v8 == 0.0:
            self.v8 = 1.0
            self.v16 = 0.0
            self.v0 = self.length - 1.0 if self.length - 1 >= 5 else 5.0
            self.v80 = 100.0 * tp
            self.v96 = 3.0 / (self.length + 2.0)
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
    
    def calculate(self, df: pd.DataFrame) -> np.ndarray:
        """
        Calculate momentum for entire dataframe
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
        
        Returns:
            Array of momentum values
        """
        self.reset()
        momentum_values = []
        
        for i in range(len(df)):
            high = df.iloc[i]['high']
            low = df.iloc[i]['low']
            close = df.iloc[i]['close']
            
            momentum = self.calculate_single(high, low, close)
            momentum_values.append(momentum)
        
        return np.array(momentum_values)
    
    def calculate_equilibrium(self, momentum: np.ndarray) -> np.ndarray:
        """
        Calculate equilibrium levels (set at direction changes)
        
        Args:
            momentum: Array of momentum values
        
        Returns:
            Array of equilibrium levels
        """
        if len(momentum) < 3:
            return np.full_like(momentum, 50.0)
        
        # Calculate direction changes
        current_change = np.diff(momentum)
        previous_change = np.concatenate([[0], current_change[:-1]])
        
        # Detect when direction changes
        trend_changed = ((current_change > 0) & (previous_change <= 0)) | \
                       ((current_change < 0) & (previous_change >= 0))
        
        # Prepend False for first value
        trend_changed = np.concatenate([[False], trend_changed])
        
        # Set equilibrium at direction changes
        equilibrium = momentum.copy()
        equilibrium[~trend_changed] = np.nan
        
        # Forward fill
        equilibrium = pd.Series(equilibrium).fillna(method='ffill').fillna(50.0).values
        
        return equilibrium
    
    def generate_signals(self, momentum: np.ndarray, equilibrium: np.ndarray) -> dict:
        """
        Generate trading signals - REVERSAL STRATEGY
        BUY when momentum is oversold (0-25), SELL when overbought (75-100)
        
        Args:
            momentum: Array of momentum values
            equilibrium: Array of equilibrium levels
        
        Returns:
            Dictionary with 'bullish' and 'bearish' boolean arrays
        """
        # REVERSAL LOGIC: Buy oversold, sell overbought
        bullish = momentum <= 25  # Buy when momentum is 0-25 (oversold)
        bearish = momentum >= 75  # Sell when momentum is 75-100 (overbought)
        
        return {
            'bullish': bullish,
            'bearish': bearish,
            'momentum': momentum,
            'equilibrium': equilibrium
        }


def calculate_momentum_indicator(df: pd.DataFrame, length: int = 7, threshold: float = 2.0) -> dict:
    """
    Convenience function to calculate momentum and signals
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        length: Momentum length parameter (default: 7)
        threshold: Signal threshold (default: 2.0)
    
    Returns:
        Dictionary with momentum, equilibrium, and signals
    """
    tracker = ActualMomentumTracker(length=length, threshold=threshold)
    momentum = tracker.calculate(df)
    equilibrium = tracker.calculate_equilibrium(momentum)
    signals = tracker.generate_signals(momentum, equilibrium)
    
    return {
        'momentum': momentum,
        'equilibrium': equilibrium,
        'bullish': signals['bullish'],
        'bearish': signals['bearish']
    }


def backtest_baseline(data: pd.DataFrame, initial_capital: float = 10000, 
                     risk_pct: float = 2.0, trailing_stop_pct: float = 3.0,
                     long_only: bool = True, options_mode: bool = False) -> dict:
    """
    Baseline backtest using YOUR exact momentum tracker
    
    Args:
        data: DataFrame with OHLC data
        initial_capital: Starting capital
        risk_pct: Risk per trade (%)
        trailing_stop_pct: Trailing stop percentage
        long_only: Only take long trades (ignored if options_mode=True)
        options_mode: If True, can trade both directions independently (buy calls/puts)
    
    Returns:
        Dictionary with results
    """
    # Calculate momentum and signals
    result = calculate_momentum_indicator(data, length=7, threshold=2.0)
    momentum = result['momentum']
    bullish = result['bullish']
    bearish = result['bearish']
    
    # Calculate ATR
    tr = np.maximum(
        data['high'].values - data['low'].values,
        np.maximum(
            np.abs(data['high'].values - np.roll(data['close'].values, 1)),
            np.abs(data['low'].values - np.roll(data['close'].values, 1))
        )
    )
    atr = pd.Series(tr).rolling(14).mean().values
    
    # Backtest
    capital = initial_capital
    position = 0
    position_side = None
    entry_price = 0
    trail_stop = 0
    trades = []
    equity_curve = [initial_capital]
    
    # Previous signal state to detect new signals
    prev_bullish = False
    prev_bearish = False
    
    for i in range(100, len(data)):
        current_price = data.iloc[i]['close']
        current_atr = atr[i] if not np.isnan(atr[i]) else current_price * 0.02
        
        # OPTIONS MODE: Can open new trades on each signal regardless of current position
        if options_mode:
            # New BULLISH signal (oversold - buy calls)
            if bullish[i] and not prev_bullish:
                # Close any existing short position first
                if position > 0 and position_side == 'short':
                    pnl = position * (entry_price - current_price)
                    capital += pnl
                    trades.append({
                        'pnl': pnl,
                        'return': pnl / (position * entry_price),
                        'side': position_side,
                        'exit_reason': 'signal_flip'
                    })
                
                # Open new long position (buy calls)
                risk_amount = capital * (risk_pct / 100)
                stop_distance = current_price * (trailing_stop_pct / 100)
                shares = int(risk_amount / stop_distance)
                
                if shares > 0 and shares * current_price <= capital:
                    position = shares
                    entry_price = current_price
                    trail_stop = entry_price * (1 - trailing_stop_pct / 100)
                    position_side = 'long'
            
            # New BEARISH signal (overbought - buy puts)
            elif bearish[i] and not prev_bearish:
                # Close any existing long position first
                if position > 0 and position_side == 'long':
                    pnl = position * (current_price - entry_price)
                    capital += pnl
                    trades.append({
                        'pnl': pnl,
                        'return': pnl / (position * entry_price),
                        'side': position_side,
                        'exit_reason': 'signal_flip'
                    })
                
                # Open new short position (buy puts)
                risk_amount = capital * (risk_pct / 100)
                stop_distance = current_price * (trailing_stop_pct / 100)
                shares = int(risk_amount / stop_distance)
                
                if shares > 0 and shares * current_price <= capital:
                    position = shares
                    entry_price = current_price
                    trail_stop = entry_price * (1 + trailing_stop_pct / 100)
                    position_side = 'short'
            
            prev_bullish = bullish[i]
            prev_bearish = bearish[i]
        
        # STOCK MODE: Traditional entry logic (can only be in one position at a time)
        else:
            if position == 0:
                if bullish[i]:
                    # Calculate position size
                    risk_amount = capital * (risk_pct / 100)
                    stop_distance = current_price * (trailing_stop_pct / 100)
                    shares = int(risk_amount / stop_distance)
                    
                    if shares > 0 and shares * current_price <= capital:
                        position = shares
                        entry_price = current_price
                        trail_stop = entry_price * (1 - trailing_stop_pct / 100)
                        position_side = 'long'
                
                elif bearish[i] and not long_only:
                    risk_amount = capital * (risk_pct / 100)
                    stop_distance = current_price * (trailing_stop_pct / 100)
                    shares = int(risk_amount / stop_distance)
                    
                    if shares > 0 and shares * current_price <= capital:
                        position = shares
                        entry_price = current_price
                        trail_stop = entry_price * (1 + trailing_stop_pct / 100)
                        position_side = 'short'
        
        # Update trailing stop
        if position > 0:
            if position_side == 'long':
                new_stop = current_price * (1 - trailing_stop_pct / 100)
                if new_stop > trail_stop:
                    trail_stop = new_stop
            elif position_side == 'short':
                new_stop = current_price * (1 + trailing_stop_pct / 100)
                if new_stop < trail_stop:
                    trail_stop = new_stop
        
        # Exit logic (trailing stop hit)
        if position > 0 and not options_mode:
            exit_signal = False
            
            if position_side == 'long':
                if bearish[i] or current_price <= trail_stop:
                    exit_signal = True
            elif position_side == 'short':
                if bullish[i] or current_price >= trail_stop:
                    exit_signal = True
            
            if exit_signal:
                if position_side == 'long':
                    pnl = position * (current_price - entry_price)
                else:
                    pnl = position * (entry_price - current_price)
                
                capital += pnl
                
                trades.append({
                    'pnl': pnl,
                    'return': pnl / (position * entry_price),
                    'side': position_side,
                    'exit_reason': 'stop' if current_price <= trail_stop else 'signal'
                })
                
                position = 0
                position_side = None
        
        # Check trailing stop in options mode
        if position > 0 and options_mode:
            hit_stop = False
            if position_side == 'long' and current_price <= trail_stop:
                hit_stop = True
            elif position_side == 'short' and current_price >= trail_stop:
                hit_stop = True
            
            if hit_stop:
                if position_side == 'long':
                    pnl = position * (current_price - entry_price)
                else:
                    pnl = position * (entry_price - current_price)
                
                capital += pnl
                trades.append({
                    'pnl': pnl,
                    'return': pnl / (position * entry_price),
                    'side': position_side,
                    'exit_reason': 'stop'
                })
                position = 0
                position_side = None
        
        # Track equity
        if position > 0:
            if position_side == 'long':
                unrealized = position * (current_price - entry_price)
            else:
                unrealized = position * (entry_price - current_price)
            current_equity = capital + unrealized
        else:
            current_equity = capital
        
        equity_curve.append(current_equity)
    
    return {
        'final_capital': capital,
        'trades': trades,
        'equity_curve': equity_curve
    }


# Usage example
if __name__ == '__main__':
    import yfinance as yf
    
    print("\n" + "="*80)
    print("  TESTING ACTUAL MOMENTUM TRACKER MODULE")
    print("="*80)
    
    # Download data
    print("\n📥 Downloading SPY data...")
    spy = yf.download('SPY', start='2023-01-01', progress=False)
    
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = [col[0].lower() for col in spy.columns]
    else:
        spy.columns = spy.columns.str.lower()
    
    print(f"✅ Downloaded {len(spy)} bars")
    
    # Calculate momentum
    print("\n📊 Calculating momentum with YOUR exact algorithm...")
    result = calculate_momentum_indicator(spy, length=7, threshold=2.0)
    
    print(f"\n📈 RESULTS:")
    print(f"  Momentum range: {result['momentum'].min():.2f} to {result['momentum'].max():.2f}")
    print(f"  Mean momentum: {result['momentum'].mean():.2f}")
    print(f"  Mean equilibrium: {result['equilibrium'].mean():.2f}")
    print(f"  Bullish signals: {result['bullish'].sum()} ({result['bullish'].sum()/len(spy)*100:.1f}%)")
    print(f"  Bearish signals: {result['bearish'].sum()} ({result['bearish'].sum()/len(spy)*100:.1f}%)")
    
    # Run baseline backtest
    print("\n🔄 Running baseline backtest...")
    baseline = backtest_baseline(spy, initial_capital=10000, risk_pct=2.0)
    
    print(f"\n💰 BASELINE RESULTS:")
    print(f"  Final Capital: ${baseline['final_capital']:,.2f}")
    print(f"  Total Return: {(baseline['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades: {len(baseline['trades'])}")
    
    if len(baseline['trades']) > 0:
        winning = sum(1 for t in baseline['trades'] if t['pnl'] > 0)
        print(f"  Win Rate: {winning/len(baseline['trades'])*100:.1f}%")
    
    print("\n✅ Module test complete!")
