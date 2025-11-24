"""
Analyze why the reversal strategy generates so few signals
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  📊 ANALYZING REVERSAL STRATEGY SIGNALS")
print("=" * 80)

# Download test data (2024-2025)
print("\n📥 Downloading SPY data (2024-2025)...")
test_data = yf.download('SPY', start='2024-01-01', end='2025-11-23', progress=False)

if isinstance(test_data.columns, pd.MultiIndex):
    test_data.columns = [col[0].lower() for col in test_data.columns]
else:
    test_data.columns = test_data.columns.str.lower()

print(f"✅ Downloaded {len(test_data)} bars")

# Calculate momentum
print("\n📊 Calculating momentum indicator...")
result = calculate_momentum_indicator(test_data, length=7, threshold=2.0)

momentum = result['momentum']
bullish = result['bullish']  # momentum <= 25
bearish = result['bearish']  # momentum >= 75

# Statistics
print("\n" + "=" * 80)
print("  📈 MOMENTUM STATISTICS")
print("=" * 80)

print(f"\nMomentum Range:")
print(f"  Min:    {momentum.min():.2f}")
print(f"  Max:    {momentum.max():.2f}")
print(f"  Mean:   {momentum.mean():.2f}")
print(f"  Median: {np.median(momentum):.2f}")
print(f"  Std:    {momentum.std():.2f}")

print(f"\nPercentile Distribution:")
for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(momentum, p)
    print(f"  {p:2d}th percentile: {val:6.2f}")

print(f"\nSignal Frequency:")
print(f"  Oversold (≤25):  {bullish.sum():4d} bars ({bullish.sum()/len(momentum)*100:5.2f}%)")
print(f"  Overbought (≥75): {bearish.sum():4d} bars ({bearish.sum()/len(momentum)*100:5.2f}%)")

# Find extreme values
print("\n" + "=" * 80)
print("  🔍 EXTREME MOMENTUM VALUES")
print("=" * 80)

oversold_dates = test_data.index[bullish]
overbought_dates = test_data.index[bearish]

if len(oversold_dates) > 0:
    print(f"\n✅ OVERSOLD SIGNALS (momentum ≤ 25): {len(oversold_dates)} occurrences")
    for i, date in enumerate(oversold_dates[:10]):  # Show first 10
        idx = test_data.index.get_loc(date)
        print(f"  {i+1}. {date.strftime('%Y-%m-%d')}: momentum = {momentum[idx]:.2f}, price = ${test_data.iloc[idx]['close']:.2f}")
    if len(oversold_dates) > 10:
        print(f"  ... and {len(oversold_dates) - 10} more")
else:
    print("\n❌ NO OVERSOLD SIGNALS (momentum never dropped to ≤25)")

if len(overbought_dates) > 0:
    print(f"\n✅ OVERBOUGHT SIGNALS (momentum ≥ 75): {len(overbought_dates)} occurrences")
    for i, date in enumerate(overbought_dates[:10]):  # Show first 10
        idx = test_data.index.get_loc(date)
        print(f"  {i+1}. {date.strftime('%Y-%m-%d')}: momentum = {momentum[idx]:.2f}, price = ${test_data.iloc[idx]['close']:.2f}")
    if len(overbought_dates) > 10:
        print(f"  ... and {len(overbought_dates) - 10} more")
else:
    print("\n❌ NO OVERBOUGHT SIGNALS (momentum never reached ≥75)")

# Test different thresholds
print("\n" + "=" * 80)
print("  🎯 TESTING DIFFERENT THRESHOLDS")
print("=" * 80)

print("\n┌──────────────┬──────────────┬────────────────┐")
print("│  Buy <= X    │  Sell >= Y   │  Total Signals │")
print("├──────────────┼──────────────┼────────────────┤")

for buy_thresh in [15, 20, 25, 30, 35, 40]:
    for sell_thresh in [60, 65, 70, 75, 80, 85]:
        buy_signals = (momentum <= buy_thresh).sum()
        sell_signals = (momentum >= sell_thresh).sum()
        total = buy_signals + sell_signals
        print(f"│     {buy_thresh:2d}       │     {sell_thresh:2d}       │      {total:3d}        │")

print("└──────────────┴──────────────┴────────────────┘")

# Distribution histogram
print("\n" + "=" * 80)
print("  📊 MOMENTUM DISTRIBUTION")
print("=" * 80)

bins = [0, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100]
hist, _ = np.histogram(momentum, bins=bins)

print("\nMomentum Range Distribution:")
for i in range(len(bins)-1):
    pct = hist[i] / len(momentum) * 100
    bar = "█" * int(pct)
    print(f"  {bins[i]:3.0f}-{bins[i+1]:3.0f}: {hist[i]:4d} bars ({pct:5.1f}%) {bar}")

print("\n" + "=" * 80)
print("  💡 INSIGHTS")
print("=" * 80)

if bullish.sum() < 10:
    print("\n⚠️  PROBLEM IDENTIFIED:")
    print(f"   Momentum rarely drops to ≤25 (only {bullish.sum()} times in {len(momentum)} bars)")
    print(f"   This is because SPY has been in a strong uptrend (2024-2025)")
    print(f"   The momentum indicator stays mostly in the 40-60 range")
    
if bearish.sum() < 10:
    print(f"\n⚠️  PROBLEM IDENTIFIED:")
    print(f"   Momentum rarely reaches ≥75 (only {bearish.sum()} times in {len(momentum)} bars)")
    print(f"   Extreme overbought levels are rare even in strong uptrends")

print("\n✅ RECOMMENDATIONS:")
print("   1. Lower thresholds: Try buy ≤35 and sell ≥65")
print("   2. Use percentiles: Buy at 10th percentile, sell at 90th")
print("   3. Combine with other indicators (RSI, volume)")
print("   4. Revert to original strategy (momentum > equilibrium + 2)")

print("\n" + "=" * 80)
