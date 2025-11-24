"""
MEAN REVERSION MOMENTUM TRACKER
Modified version that buys LOW and sells HIGH (opposite of trend following)

Strategy Logic:
- BUY when momentum is LOW (0-25) = Oversold
- SELL when momentum is HIGH (75-100) = Overbought
"""
import numpy as np
import pandas as pd
import sys
import os

# Import the original momentum calculation
sys.path.append(os.path.dirname(__file__))
from actual_momentum_tracker import ActualMomentumTracker


def calculate_mean_reversion_signals(df: pd.DataFrame, 
                                     length: int = 7,
                                     buy_below: float = 25.0,
                                     sell_above: float = 75.0) -> dict:
    """
    Calculate mean reversion signals
    
    Args:
        df: DataFrame with OHLC data
        length: Momentum length parameter (default: 7)
        buy_below: Buy when momentum BELOW this (default: 25)
        sell_above: Sell when momentum ABOVE this (default: 75)
    
    Returns:
        Dictionary with momentum and signals
    """
    # Use same momentum calculation
    tracker = ActualMomentumTracker(length=length, threshold=2.0)
    momentum = tracker.calculate(df)
    equilibrium = tracker.calculate_equilibrium(momentum)
    
    # MEAN REVERSION SIGNALS (opposite of momentum following!)
    buy_signal = momentum < buy_below      # Buy when LOW (oversold)
    sell_signal = momentum > sell_above    # Sell when HIGH (overbought)
    
    return {
        'momentum': momentum,
        'equilibrium': equilibrium,
        'buy': buy_signal,      # True when oversold
        'sell': sell_signal,    # True when overbought
        'distance': momentum - equilibrium
    }


def backtest_mean_reversion(data: pd.DataFrame, 
                            initial_capital: float = 10000,
                            risk_pct: float = 2.0,
                            trailing_stop_pct: float = 3.0,
                            buy_below: float = 25.0,
                            sell_above: float = 75.0,
                            take_profit_pct: float = 5.0) -> dict:
    """
    Backtest MEAN REVERSION strategy
    
    Strategy:
    - BUY when momentum drops below buy_below (oversold)
    - SELL when momentum rises above sell_above (overbought)
    - OR take profit at take_profit_pct gain
    - OR trailing stop hit
    
    Args:
        data: DataFrame with OHLC data
        initial_capital: Starting capital
        risk_pct: Risk per trade (%)
        trailing_stop_pct: Trailing stop percentage
        buy_below: Buy threshold (0-25 typical)
        sell_above: Sell threshold (75-100 typical)
        take_profit_pct: Take profit target (%)
    
    Returns:
        Dictionary with results
    """
    # Calculate signals
    signals = calculate_mean_reversion_signals(
        data, 
        buy_below=buy_below, 
        sell_above=sell_above
    )
    
    momentum = signals['momentum']
    buy_signals = signals['buy']
    sell_signals = signals['sell']
    
    # Backtest
    capital = initial_capital
    position = 0
    entry_price = 0
    trail_stop = 0
    take_profit = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(100, len(data)):
        current_price = data.iloc[i]['close']
        
        # ENTRY LOGIC - Buy when OVERSOLD
        if position == 0:
            if buy_signals[i]:
                # Calculate position size
                risk_amount = capital * (risk_pct / 100)
                stop_distance = current_price * (trailing_stop_pct / 100)
                shares = int(risk_amount / stop_distance)
                
                if shares > 0 and shares * current_price <= capital:
                    position = shares
                    entry_price = current_price
                    trail_stop = entry_price * (1 - trailing_stop_pct / 100)
                    take_profit = entry_price * (1 + take_profit_pct / 100)
                    
                    trades.append({
                        'entry_bar': i,
                        'entry_price': entry_price,
                        'entry_momentum': momentum[i],
                        'shares': shares,
                        'type': 'ENTRY'
                    })
        
        # UPDATE TRAILING STOP
        elif position > 0:
            new_stop = current_price * (1 - trailing_stop_pct / 100)
            if new_stop > trail_stop:
                trail_stop = new_stop
            
            # EXIT LOGIC - Multiple conditions
            exit_signal = False
            exit_reason = ""
            
            # Exit 1: Overbought (momentum HIGH)
            if sell_signals[i]:
                exit_signal = True
                exit_reason = "OVERBOUGHT"
            
            # Exit 2: Take profit hit
            elif current_price >= take_profit:
                exit_signal = True
                exit_reason = "TAKE_PROFIT"
            
            # Exit 3: Trailing stop hit
            elif current_price <= trail_stop:
                exit_signal = True
                exit_reason = "STOP_LOSS"
            
            if exit_signal:
                pnl = position * (current_price - entry_price)
                capital += pnl
                
                trades.append({
                    'exit_bar': i,
                    'exit_price': current_price,
                    'exit_momentum': momentum[i],
                    'pnl': pnl,
                    'return': (current_price / entry_price - 1) * 100,
                    'exit_reason': exit_reason,
                    'type': 'EXIT'
                })
                
                position = 0
        
        # Track equity
        if position > 0:
            unrealized = position * (current_price - entry_price)
            current_equity = capital + unrealized
        else:
            current_equity = capital
        
        equity_curve.append(current_equity)
    
    return {
        'final_capital': capital,
        'trades': trades,
        'equity_curve': equity_curve
    }


# Test example
if __name__ == '__main__':
    import yfinance as yf
    
    print("=" * 80)
    print("  MEAN REVERSION STRATEGY TEST")
    print("  Buy LOW (oversold), Sell HIGH (overbought)")
    print("=" * 80)
    
    # Download data
    print("\n📥 Downloading data...")
    data = yf.download('SPY', start='2023-01-01', end='2023-12-31', progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    print(f"✅ Downloaded {len(data)} bars")
    
    # Calculate signals
    print("\n📊 Calculating mean reversion signals...")
    signals = calculate_mean_reversion_signals(
        data,
        buy_below=25,
        sell_above=75
    )
    
    print(f"\n📈 SIGNAL ANALYSIS:")
    print(f"   Momentum range: {signals['momentum'].min():.1f} to {signals['momentum'].max():.1f}")
    print(f"   Mean momentum: {signals['momentum'].mean():.1f}")
    print(f"   Buy signals (< 25): {signals['buy'].sum()} ({signals['buy'].sum()/len(data)*100:.1f}%)")
    print(f"   Sell signals (> 75): {signals['sell'].sum()} ({signals['sell'].sum()/len(data)*100:.1f}%)")
    
    # Backtest
    print("\n🔄 Running mean reversion backtest...")
    result = backtest_mean_reversion(
        data,
        initial_capital=10000,
        buy_below=25,
        sell_above=75,
        take_profit_pct=5.0
    )
    
    print(f"\n💰 MEAN REVERSION RESULTS:")
    print(f"   Initial Capital:  ${10000:,.2f}")
    print(f"   Final Capital:    ${result['final_capital']:,.2f}")
    print(f"   Total Return:     {(result['final_capital']/10000-1)*100:.2f}%")
    print(f"   Total Trades:     {len([t for t in result['trades'] if t['type'] == 'EXIT'])}")
    
    # Trade analysis
    exits = [t for t in result['trades'] if t['type'] == 'EXIT']
    if len(exits) > 0:
        winning = sum(1 for t in exits if t['pnl'] > 0)
        print(f"   Winning Trades:   {winning}/{len(exits)}")
        print(f"   Win Rate:         {winning/len(exits)*100:.1f}%")
        print(f"   Avg Return:       {np.mean([t['return'] for t in exits]):.2f}%")
        
        print(f"\n📊 EXIT REASONS:")
        for reason in ['OVERBOUGHT', 'TAKE_PROFIT', 'STOP_LOSS']:
            count = sum(1 for t in exits if t['exit_reason'] == reason)
            print(f"   {reason:15s}: {count} ({count/len(exits)*100:.1f}%)")
    
    print("\n✅ Test complete!")
