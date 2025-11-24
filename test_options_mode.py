"""
Test options mode reversal strategy to see actual trades
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🧪 TESTING OPTIONS MODE REVERSAL STRATEGY")
print("=" * 80)

# Download test data
print("\n📥 Downloading SPY data (2024-2025)...")
test_data = yf.download('SPY', start='2024-01-01', end='2025-11-23', progress=False)

if isinstance(test_data.columns, pd.MultiIndex):
    test_data.columns = [col[0].lower() for col in test_data.columns]
else:
    test_data.columns = test_data.columns.str.lower()

print(f"✅ Downloaded {len(test_data)} bars")

# Calculate momentum
print("\n📊 Calculating momentum signals...")
result = calculate_momentum_indicator(test_data, length=7, threshold=2.0)

momentum = result['momentum']
bullish = result['bullish']  # momentum <= 25
bearish = result['bearish']  # momentum >= 75

# Simulate options trading
print("\n💰 Running OPTIONS MODE backtest...")
capital = 10000
position = 0
position_side = None
entry_price = 0
entry_date = None
trades = []
equity = [10000]

prev_bullish = False
prev_bearish = False

print("\n" + "=" * 80)
print("  📋 TRADE LOG")
print("=" * 80)

for i in range(100, len(test_data)):
    date = test_data.index[i]
    current_price = test_data.iloc[i]['close']
    current_momentum = momentum[i]
    
    # New BULLISH signal (buy CALLS)
    if bullish[i] and not prev_bullish:
        # Close existing PUT position if any
        if position > 0 and position_side == 'short':
            days_held = (date - entry_date).days
            pnl = position * (entry_price - current_price)
            pnl_pct = (pnl / (position * entry_price)) * 100
            capital += pnl
            
            print(f"\n📉 CLOSE PUT POSITION:")
            print(f"   Date: {date.strftime('%Y-%m-%d')}")
            print(f"   Entry: ${entry_price:.2f} → Exit: ${current_price:.2f}")
            print(f"   Momentum at exit: {current_momentum:.2f}")
            print(f"   Days held: {days_held}")
            print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"   New Capital: ${capital:.2f}")
            
            trades.append({
                'type': 'PUT',
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'days_held': days_held
            })
            position = 0
        
        # Open CALL position
        shares = int((capital * 0.95) / current_price)
        if shares > 0:
            position = shares
            entry_price = current_price
            entry_date = date
            capital -= shares * current_price * 1.001
            position_side = 'long'
            
            print(f"\n📈 OPEN CALL POSITION:")
            print(f"   Date: {date.strftime('%Y-%m-%d')}")
            print(f"   Price: ${entry_price:.2f}")
            print(f"   Momentum: {current_momentum:.2f} (OVERSOLD)")
            print(f"   Shares: {shares}")
            print(f"   Cost: ${shares * entry_price * 1.001:.2f}")
            print(f"   Remaining Capital: ${capital:.2f}")
    
    # New BEARISH signal (buy PUTS)
    elif bearish[i] and not prev_bearish:
        # Close existing CALL position if any
        if position > 0 and position_side == 'long':
            days_held = (date - entry_date).days
            pnl = position * (current_price - entry_price)
            pnl_pct = (pnl / (position * entry_price)) * 100
            capital += pnl
            
            print(f"\n📈 CLOSE CALL POSITION:")
            print(f"   Date: {date.strftime('%Y-%m-%d')}")
            print(f"   Entry: ${entry_price:.2f} → Exit: ${current_price:.2f}")
            print(f"   Momentum at exit: {current_momentum:.2f}")
            print(f"   Days held: {days_held}")
            print(f"   P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"   New Capital: ${capital:.2f}")
            
            trades.append({
                'type': 'CALL',
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'days_held': days_held
            })
            position = 0
        
        # Open PUT position
        shares = int((capital * 0.95) / current_price)
        if shares > 0:
            position = shares
            entry_price = current_price
            entry_date = date
            capital -= shares * current_price * 1.001
            position_side = 'short'
            
            print(f"\n📉 OPEN PUT POSITION:")
            print(f"   Date: {date.strftime('%Y-%m-%d')}")
            print(f"   Price: ${entry_price:.2f}")
            print(f"   Momentum: {current_momentum:.2f} (OVERBOUGHT)")
            print(f"   Shares: {shares}")
            print(f"   Cost: ${shares * entry_price * 1.001:.2f}")
            print(f"   Remaining Capital: ${capital:.2f}")
    
    prev_bullish = bullish[i]
    prev_bearish = bearish[i]
    
    # Track equity
    if position > 0:
        if position_side == 'long':
            equity.append(capital + position * current_price)
        else:
            equity.append(capital + position * (2 * entry_price - current_price))
    else:
        equity.append(capital)

# Summary
print("\n" + "=" * 80)
print("  📊 BACKTEST SUMMARY")
print("=" * 80)

print(f"\nTotal Trades: {len(trades)}")
print(f"Initial Capital: $10,000.00")
print(f"Final Capital: ${capital:.2f}")
print(f"Total Return: {(capital / 10000 - 1) * 100:.2f}%")

if len(trades) > 0:
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    total_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    total_loss = sum(t['pnl'] for t in trades if t['pnl'] < 0)
    avg_days = np.mean([t['days_held'] for t in trades])
    
    print(f"\nWinning Trades: {winning_trades}/{len(trades)} ({winning_trades/len(trades)*100:.1f}%)")
    print(f"Total Profit: ${total_profit:.2f}")
    print(f"Total Loss: ${total_loss:.2f}")
    print(f"Average Days Held: {avg_days:.1f}")
    
    print(f"\n📋 DETAILED TRADES:")
    for i, trade in enumerate(trades, 1):
        print(f"\n  Trade #{i} - {trade['type']}:")
        print(f"    Entry: {trade['entry_date'].strftime('%Y-%m-%d')} @ ${trade['entry_price']:.2f}")
        print(f"    Exit:  {trade['exit_date'].strftime('%Y-%m-%d')} @ ${trade['exit_price']:.2f}")
        print(f"    P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:+.2f}%)")
        print(f"    Days: {trade['days_held']}")

print("\n" + "=" * 80)
