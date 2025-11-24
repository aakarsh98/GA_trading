"""
Compare Mean Reversion vs Momentum Following Strategies
"""
import sys
sys.path.append('tradingview-strategies/python_strategies/utils')

import yfinance as yf
import pandas as pd
import numpy as np
from actual_momentum_tracker import calculate_momentum_indicator, backtest_baseline
from mean_reversion_tracker import calculate_mean_reversion_signals, backtest_mean_reversion

print("=" * 80)
print("  STRATEGY COMPARISON: Mean Reversion vs Momentum Following")
print("=" * 80)

# Download data for multiple periods
periods = [
    ('2020-01-01', '2020-12-31', '2020'),
    ('2021-01-01', '2021-12-31', '2021'),
    ('2022-01-01', '2022-12-31', '2022'),
    ('2023-01-01', '2023-12-31', '2023'),
    ('2020-01-01', '2023-12-31', 'All (2020-2023)')
]

results_comparison = []

for start, end, label in periods:
    print(f"\n{'='*80}")
    print(f"  TESTING PERIOD: {label}")
    print(f"{'='*80}")
    
    # Download data
    print(f"\n📥 Downloading {label} data...")
    data = yf.download('SPY', start=start, end=end, progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    print(f"✅ Downloaded {len(data)} bars")
    
    # Test 1: Momentum Following (your original)
    print(f"\n📊 Testing MOMENTUM FOLLOWING...")
    momentum_result = backtest_baseline(
        data,
        initial_capital=10000,
        risk_pct=2.0,
        trailing_stop_pct=3.0,
        long_only=True
    )
    
    momentum_return = (momentum_result['final_capital'] / 10000 - 1) * 100
    momentum_trades = len(momentum_result['trades'])
    
    if momentum_trades > 0:
        momentum_wins = sum(1 for t in momentum_result['trades'] if t['pnl'] > 0)
        momentum_win_rate = (momentum_wins / momentum_trades) * 100
    else:
        momentum_wins = 0
        momentum_win_rate = 0
    
    print(f"   Return: {momentum_return:+.2f}%")
    print(f"   Trades: {momentum_trades}")
    print(f"   Win Rate: {momentum_win_rate:.1f}%")
    
    # Test 2: Mean Reversion
    print(f"\n📊 Testing MEAN REVERSION (buy < 25, sell > 75)...")
    mr_result = backtest_mean_reversion(
        data,
        initial_capital=10000,
        buy_below=25,
        sell_above=75,
        take_profit_pct=5.0
    )
    
    mr_return = (mr_result['final_capital'] / 10000 - 1) * 100
    mr_exits = [t for t in mr_result['trades'] if t['type'] == 'EXIT']
    mr_trades = len(mr_exits)
    
    if mr_trades > 0:
        mr_wins = sum(1 for t in mr_exits if t['pnl'] > 0)
        mr_win_rate = (mr_wins / mr_trades) * 100
    else:
        mr_wins = 0
        mr_win_rate = 0
    
    print(f"   Return: {mr_return:+.2f}%")
    print(f"   Trades: {mr_trades}")
    print(f"   Win Rate: {mr_win_rate:.1f}%")
    
    # Comparison
    better = "MEAN REVERSION" if mr_return > momentum_return else "MOMENTUM FOLLOWING"
    diff = abs(mr_return - momentum_return)
    
    print(f"\n🎯 WINNER: {better} (+{diff:.2f}%)")
    
    results_comparison.append({
        'period': label,
        'momentum_return': momentum_return,
        'momentum_trades': momentum_trades,
        'momentum_win_rate': momentum_win_rate,
        'mr_return': mr_return,
        'mr_trades': mr_trades,
        'mr_win_rate': mr_win_rate,
        'winner': better
    })

# Final summary
print("\n" + "=" * 80)
print("  COMPREHENSIVE COMPARISON")
print("=" * 80)

print(f"""
┌──────────────────┬────────────────────────────┬────────────────────────────┬─────────────┐
│ Period           │  Momentum Following        │  Mean Reversion            │  Winner     │
├──────────────────┼────────────────────────────┼────────────────────────────┼─────────────┤""")

for r in results_comparison:
    print(f"│ {r['period']:16s} │ {r['momentum_return']:+7.2f}% ({r['momentum_trades']:2d} trades) │ {r['mr_return']:+7.2f}% ({r['mr_trades']:2d} trades) │ {r['winner'][:12]:12s}│")

print(f"└──────────────────┴────────────────────────────┴────────────────────────────┴─────────────┘")

# Calculate statistics
momentum_wins = sum(1 for r in results_comparison if r['winner'] == 'MOMENTUM FOLLOWING')
mr_wins = sum(1 for r in results_comparison if r['winner'] == 'MEAN REVERSION')

avg_momentum = np.mean([r['momentum_return'] for r in results_comparison])
avg_mr = np.mean([r['mr_return'] for r in results_comparison])

print(f"""
📊 STATISTICS:
   Periods won by Momentum Following: {momentum_wins}/{len(results_comparison)}
   Periods won by Mean Reversion:     {mr_wins}/{len(results_comparison)}
   
   Average Return (Momentum):  {avg_momentum:+.2f}%
   Average Return (Mean Rev):  {avg_mr:+.2f}%
   
   Difference: {abs(avg_momentum - avg_mr):.2f}% in favor of {'MOMENTUM' if avg_momentum > avg_mr else 'MEAN REVERSION'}
""")

# Key insights
print("=" * 80)
print("  KEY INSIGHTS")
print("=" * 80)

if avg_mr > avg_momentum:
    print(f"""
✅ MEAN REVERSION WINS!
   Average: {avg_mr:+.2f}% vs {avg_momentum:+.2f}%
   
   Why it works better:
   • Buys at oversold levels (momentum < 25)
   • Sells at overbought levels (momentum > 75)
   • Takes profits on bounces
   • Better for ranging/choppy markets
   
   Best used when:
   • Market is sideways (no strong trend)
   • High volatility
   • SPY trading in range
""")
else:
    print(f"""
✅ MOMENTUM FOLLOWING WINS!
   Average: {avg_momentum:+.2f}% vs {avg_mr:+.2f}%
   
   Why it works better:
   • Catches strong trends
   • Rides momentum moves
   • Better for trending markets
   
   Best used when:
   • Market is trending (up or down)
   • Clear direction
   • Strong momentum bursts
""")

print("\n💡 RECOMMENDATION:")
print("   Consider using BOTH strategies with regime detection:")
print("   • Use MEAN REVERSION in choppy markets (VIX > 20)")
print("   • Use MOMENTUM FOLLOWING in trending markets (VIX < 20)")
print("   • Or use the one that performed better on average")

print("\n✅ Comparison complete!")
