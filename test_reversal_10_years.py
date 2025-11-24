"""
Test options mode reversal strategy over 10 YEARS (2013-2023)
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🧪 TESTING REVERSAL STRATEGY - 10 YEARS (2013-2023)")
print("=" * 80)

# Download 10 years of data
print("\n📥 Downloading SPY data (2013-2023)...")
data = yf.download('SPY', start='2013-01-01', end='2023-12-31', progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = [col[0].lower() for col in data.columns]
else:
    data.columns = data.columns.str.lower()

print(f"✅ Downloaded {len(data)} bars")

# Calculate momentum
print("\n📊 Calculating momentum signals...")
result = calculate_momentum_indicator(data, length=7, threshold=2.0)

momentum = result['momentum']
bullish = result['bullish']  # momentum <= 25
bearish = result['bearish']  # momentum >= 75

print(f"\n📈 Signal Statistics:")
print(f"   Oversold signals (≤25):  {bullish.sum()} ({bullish.sum()/len(momentum)*100:.2f}%)")
print(f"   Overbought signals (≥75): {bearish.sum()} ({bearish.sum()/len(momentum)*100:.2f}%)")

# Simulate options trading
print("\n💰 Running OPTIONS MODE backtest...")
capital = 10000
position = 0
position_side = None
entry_price = 0
entry_date = None
trades = []
equity_curve = [10000]
dates = [data.index[100]]

prev_bullish = False
prev_bearish = False

trade_count = 0

for i in range(100, len(data)):
    date = data.index[i]
    current_price = data.iloc[i]['close']
    current_momentum = momentum[i]
    
    # New BULLISH signal (buy CALLS)
    if bullish[i] and not prev_bullish:
        # Close existing PUT position if any
        if position > 0 and position_side == 'short':
            days_held = (date - entry_date).days
            pnl = position * (entry_price - current_price)
            pnl_pct = (pnl / (position * entry_price)) * 100
            capital += pnl
            
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
            trade_count += 1
        
        # Open CALL position
        shares = int((capital * 0.95) / current_price)
        if shares > 0:
            position = shares
            entry_price = current_price
            entry_date = date
            capital -= shares * current_price * 1.001
            position_side = 'long'
    
    # New BEARISH signal (buy PUTS)
    elif bearish[i] and not prev_bearish:
        # Close existing CALL position if any
        if position > 0 and position_side == 'long':
            days_held = (date - entry_date).days
            pnl = position * (current_price - entry_price)
            pnl_pct = (pnl / (position * entry_price)) * 100
            capital += pnl
            
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
            trade_count += 1
        
        # Open PUT position
        shares = int((capital * 0.95) / current_price)
        if shares > 0:
            position = shares
            entry_price = current_price
            entry_date = date
            capital -= shares * current_price * 1.001
            position_side = 'short'
    
    prev_bullish = bullish[i]
    prev_bearish = bearish[i]
    
    # Track equity
    if position > 0:
        if position_side == 'long':
            current_equity = capital + position * current_price
        else:
            current_equity = capital + position * (2 * entry_price - current_price)
    else:
        current_equity = capital
    
    equity_curve.append(current_equity)
    dates.append(date)

# Summary
print("\n" + "=" * 80)
print("  📊 10-YEAR BACKTEST RESULTS")
print("=" * 80)

print(f"\n💰 PERFORMANCE:")
print(f"   Initial Capital:    $10,000.00")
print(f"   Final Capital:      ${capital:,.2f}")
print(f"   Total Return:       {(capital / 10000 - 1) * 100:+.2f}%")
print(f"   Annualized Return:  {((capital / 10000) ** (1/10) - 1) * 100:+.2f}%")

if len(trades) > 0:
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    losing_trades = len(trades) - winning_trades
    total_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    total_loss = sum(t['pnl'] for t in trades if t['pnl'] < 0)
    avg_win = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss = total_loss / losing_trades if losing_trades > 0 else 0
    avg_days = np.mean([t['days_held'] for t in trades])
    
    print(f"\n📈 TRADE STATISTICS:")
    print(f"   Total Trades:       {len(trades)}")
    print(f"   Winning Trades:     {winning_trades} ({winning_trades/len(trades)*100:.1f}%)")
    print(f"   Losing Trades:      {losing_trades} ({losing_trades/len(trades)*100:.1f}%)")
    print(f"   Total Profit:       ${total_profit:,.2f}")
    print(f"   Total Loss:         ${total_loss:,.2f}")
    print(f"   Average Win:        ${avg_win:,.2f}")
    print(f"   Average Loss:       ${avg_loss:,.2f}")
    print(f"   Profit Factor:      {abs(total_profit / total_loss) if total_loss != 0 else 0:.2f}")
    print(f"   Average Days Held:  {avg_days:.1f}")
    
    # Yearly breakdown
    print(f"\n📅 YEARLY PERFORMANCE:")
    yearly_returns = {}
    for year in range(2013, 2024):
        year_trades = [t for t in trades if t['exit_date'].year == year]
        if year_trades:
            year_pnl = sum(t['pnl'] for t in year_trades)
            yearly_returns[year] = year_pnl
            print(f"   {year}: ${year_pnl:+8,.2f} ({len(year_trades):2d} trades)")
    
    # Trade type breakdown
    call_trades = [t for t in trades if t['type'] == 'CALL']
    put_trades = [t for t in trades if t['type'] == 'PUT']
    
    print(f"\n📊 TRADE TYPE BREAKDOWN:")
    if call_trades:
        call_wins = sum(1 for t in call_trades if t['pnl'] > 0)
        call_pnl = sum(t['pnl'] for t in call_trades)
        print(f"   CALL Trades: {len(call_trades)} trades, {call_wins} wins ({call_wins/len(call_trades)*100:.1f}%), P&L: ${call_pnl:+,.2f}")
    
    if put_trades:
        put_wins = sum(1 for t in put_trades if t['pnl'] > 0)
        put_pnl = sum(t['pnl'] for t in put_trades)
        print(f"   PUT Trades:  {len(put_trades)} trades, {put_wins} wins ({put_wins/len(put_trades)*100:.1f}%), P&L: ${put_pnl:+,.2f}")
    
    # Max drawdown
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    print(f"\n⚠️  RISK METRICS:")
    print(f"   Max Drawdown:       {max_dd:.2f}%")
    print(f"   Peak Equity:        ${running_max.max():,.2f}")
    print(f"   Current Position:   {'CALL' if position_side == 'long' else 'PUT' if position_side == 'short' else 'None'}")
    
    # Sample of trades
    print(f"\n📋 SAMPLE TRADES (First 10):")
    for i, trade in enumerate(trades[:10], 1):
        print(f"   {i:2d}. {trade['type']:4s} | {trade['entry_date'].strftime('%Y-%m-%d')} → {trade['exit_date'].strftime('%Y-%m-%d')} | "
              f"${trade['entry_price']:6.2f} → ${trade['exit_price']:6.2f} | "
              f"${trade['pnl']:+7.2f} ({trade['pnl_pct']:+6.2f}%) | {trade['days_held']:3d} days")
    
    if len(trades) > 10:
        print(f"   ... and {len(trades) - 10} more trades")
    
    # Create equity curve chart
    print(f"\n📈 Generating equity curve chart...")
    plt.figure(figsize=(14, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(dates, equity_curve, linewidth=2, label='Reversal Strategy', color='blue')
    plt.axhline(y=10000, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
    plt.title('10-Year Equity Curve - Reversal Strategy (Buy Oversold ≤25, Sell Overbought ≥75)', 
              fontsize=14, fontweight='bold')
    plt.ylabel('Portfolio Value ($)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Add buy & hold comparison
    spy_data = data['close'].values[100:]
    spy_returns = (spy_data / spy_data[0]) * 10000
    # Make sure lengths match
    if len(spy_returns) == len(dates):
        plt.plot(dates, spy_returns, linewidth=2, label='SPY Buy & Hold', color='green', alpha=0.7)
        plt.legend()
    
    # Drawdown chart
    plt.subplot(2, 1, 2)
    plt.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
    plt.plot(dates, drawdown, color='red', linewidth=1)
    plt.title('Drawdown %', fontsize=12, fontweight='bold')
    plt.ylabel('Drawdown (%)', fontsize=12)
    plt.xlabel('Date', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    chart_path = 'reversal_strategy_10y_equity_curve.png'
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    print(f"✅ Chart saved to: {chart_path}")
    
    # Compare to Buy & Hold
    spy_final = data.iloc[-1]['close']
    spy_initial = data.iloc[100]['close']
    spy_return = (spy_final / spy_initial - 1) * 100
    spy_annual = ((spy_final / spy_initial) ** (1/10) - 1) * 100
    
    print(f"\n" + "=" * 80)
    print(f"  📊 COMPARISON: REVERSAL STRATEGY vs BUY & HOLD")
    print("=" * 80)
    print(f"\n{'Metric':<25} {'Reversal':>15} {'Buy & Hold':>15} {'Difference':>15}")
    print("-" * 80)
    print(f"{'Total Return':<25} {(capital/10000-1)*100:>14.2f}% {spy_return:>14.2f}% {(capital/10000-1)*100-spy_return:>+14.2f}%")
    print(f"{'Annualized Return':<25} {((capital/10000)**(1/10)-1)*100:>14.2f}% {spy_annual:>14.2f}% {((capital/10000)**(1/10)-1)*100-spy_annual:>+14.2f}%")
    print(f"{'Max Drawdown':<25} {max_dd:>14.2f}% {'N/A':>15} {'N/A':>15}")
    print(f"{'Total Trades':<25} {len(trades):>15} {0:>15} {len(trades):>+15}")

else:
    print("\n❌ NO TRADES EXECUTED!")

print("\n" + "=" * 80)
print("  ✅ ANALYSIS COMPLETE")
print("=" * 80)
