"""
Threshold Optimization for YOUR Momentum Indicator
Find the optimal entry/exit threshold levels
"""
import numpy as np
import pandas as pd
import itertools
from datetime import datetime
import sys
sys.path.append('.')


def load_data():
    """Load data with momentum"""
    data = pd.read_csv('momentum_indicator_data.csv', index_col=0, parse_dates=True)
    print(f"✅ Loaded {len(data)} bars\n")
    return data


def backtest_strategy(data, entry_threshold, exit_threshold, use_fixed_levels=False, 
                     fixed_entry=None, fixed_exit=None):
    """
    Backtest with specific thresholds
    
    Two modes:
    1. Dynamic: Uses equilibrium (20-MA) ± threshold
    2. Fixed: Uses absolute momentum levels (e.g., 60/40)
    """
    data = data.copy()
    data['momentum_ma'] = data['momentum'].rolling(20).mean()
    
    trades = []
    position = None
    entry_price = None
    entry_bar = None
    
    for i in range(50, len(data)):
        momentum = data.iloc[i]['momentum']
        momentum_ma = data.iloc[i]['momentum_ma']
        price = data.iloc[i]['close']
        
        if position is None:
            # Entry logic
            if use_fixed_levels:
                # Fixed level entry (e.g., momentum > 60)
                if momentum > fixed_entry:
                    position = 'LONG'
                    entry_price = price
                    entry_bar = i
            else:
                # Dynamic equilibrium entry
                if momentum > momentum_ma + entry_threshold:
                    position = 'LONG'
                    entry_price = price
                    entry_bar = i
        else:
            # Exit logic
            exit_signal = False
            
            if use_fixed_levels:
                # Fixed level exit (e.g., momentum < 40)
                if momentum < fixed_exit:
                    exit_signal = True
            else:
                # Dynamic equilibrium exit
                if momentum < momentum_ma - exit_threshold:
                    exit_signal = True
            
            if exit_signal:
                pnl_pct = (price - entry_price) / entry_price
                bars_held = i - entry_bar
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': price,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held
                })
                position = None
    
    # Calculate metrics
    if len(trades) == 0:
        return None
    
    trades_df = pd.DataFrame(trades)
    
    metrics = {
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_pct'] > 0).sum() / len(trades_df) * 100,
        'avg_return': trades_df['pnl_pct'].mean() * 100,
        'total_return': trades_df['pnl_pct'].sum() * 100,
        'avg_win': trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() * 100 if (trades_df['pnl_pct'] > 0).sum() > 0 else 0,
        'avg_loss': trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean() * 100 if (trades_df['pnl_pct'] < 0).sum() > 0 else 0,
        'avg_bars_held': trades_df['bars_held'].mean(),
        'sharpe': trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std() if trades_df['pnl_pct'].std() > 0 else 0
    }
    
    return metrics


def optimize_dynamic_thresholds(data):
    """
    Optimization 1: Find best entry/exit thresholds around equilibrium
    Test: Entry threshold from 0.5 to 5.0
          Exit threshold from 0 to 3.0
    """
    print("=" * 80)
    print("🔍 OPTIMIZATION 1: DYNAMIC EQUILIBRIUM THRESHOLDS")
    print("=" * 80)
    print("\nTesting entry thresholds from 0.5 to 5.0")
    print("Testing exit thresholds from 0.0 to 3.0")
    print("(This will take a moment...)\n")
    
    # Test ranges
    entry_thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    exit_thresholds = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    results = []
    
    for entry_t in entry_thresholds:
        for exit_t in exit_thresholds:
            metrics = backtest_strategy(data, entry_t, exit_t, use_fixed_levels=False)
            if metrics and metrics['total_trades'] >= 10:  # Minimum 10 trades
                results.append({
                    'entry_threshold': entry_t,
                    'exit_threshold': exit_t,
                    **metrics
                })
    
    results_df = pd.DataFrame(results)
    
    # Sort by average return
    results_df = results_df.sort_values('avg_return', ascending=False)
    
    print("📊 TOP 10 CONFIGURATIONS (by avg return per trade):")
    print("-" * 80)
    print(f"{'Entry':>6} {'Exit':>6} {'Trades':>7} {'Win%':>6} {'Avg Ret':>8} {'Total':>7} {'Sharpe':>7}")
    print("-" * 80)
    
    for i, row in results_df.head(10).iterrows():
        print(f"{row['entry_threshold']:>6.1f} {row['exit_threshold']:>6.1f} "
              f"{row['total_trades']:>7.0f} {row['win_rate']:>6.1f} "
              f"{row['avg_return']:>7.2f}% {row['total_return']:>6.1f}% "
              f"{row['sharpe']:>7.2f}")
    
    best = results_df.iloc[0]
    print("\n🏆 BEST CONFIGURATION:")
    print(f"   Entry threshold:     {best['entry_threshold']:.1f}")
    print(f"   Exit threshold:      {best['exit_threshold']:.1f}")
    print(f"   Average return:      {best['avg_return']:.2f}% per trade")
    print(f"   Win rate:            {best['win_rate']:.1f}%")
    print(f"   Total trades:        {best['total_trades']:.0f}")
    print(f"   Sharpe ratio:        {best['sharpe']:.2f}")
    
    # Compare to current (2.0 entry, 0.0 exit)
    current = results_df[(results_df['entry_threshold'] == 2.0) & 
                         (results_df['exit_threshold'] == 0.0)]
    if len(current) > 0:
        current = current.iloc[0]
        improvement = ((best['avg_return'] - current['avg_return']) / abs(current['avg_return']) * 100 
                      if current['avg_return'] != 0 else 0)
        print(f"\n📈 IMPROVEMENT vs CURRENT (2.0/0.0):")
        print(f"   Current avg return:  {current['avg_return']:.2f}%")
        print(f"   Best avg return:     {best['avg_return']:.2f}%")
        print(f"   Improvement:         {improvement:+.1f}%")
    
    return results_df


def optimize_fixed_levels(data):
    """
    Optimization 2: Find best fixed momentum levels
    Test: Entry levels from 50 to 75
          Exit levels from 25 to 50
    """
    print("\n" + "=" * 80)
    print("🔍 OPTIMIZATION 2: FIXED MOMENTUM LEVELS")
    print("=" * 80)
    print("\nTesting entry levels from 50 to 75")
    print("Testing exit levels from 25 to 50")
    print("(This will take a moment...)\n")
    
    # Test ranges
    entry_levels = [50, 52, 55, 58, 60, 62, 65, 68, 70, 72, 75]
    exit_levels = [25, 28, 30, 32, 35, 38, 40, 42, 45, 48, 50]
    
    results = []
    
    for entry_l in entry_levels:
        for exit_l in exit_levels:
            if exit_l >= entry_l:  # Skip invalid combinations
                continue
            
            metrics = backtest_strategy(data, None, None, use_fixed_levels=True,
                                       fixed_entry=entry_l, fixed_exit=exit_l)
            if metrics and metrics['total_trades'] >= 10:
                results.append({
                    'entry_level': entry_l,
                    'exit_level': exit_l,
                    'spread': entry_l - exit_l,
                    **metrics
                })
    
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("⚠️  No valid configurations found")
        return None
    
    # Sort by average return
    results_df = results_df.sort_values('avg_return', ascending=False)
    
    print("📊 TOP 10 CONFIGURATIONS (by avg return per trade):")
    print("-" * 80)
    print(f"{'Entry':>6} {'Exit':>6} {'Spread':>7} {'Trades':>7} {'Win%':>6} {'Avg Ret':>8} {'Total':>7}")
    print("-" * 80)
    
    for i, row in results_df.head(10).iterrows():
        print(f"{row['entry_level']:>6.0f} {row['exit_level']:>6.0f} "
              f"{row['spread']:>7.0f} {row['total_trades']:>7.0f} "
              f"{row['win_rate']:>6.1f} {row['avg_return']:>7.2f}% "
              f"{row['total_return']:>6.1f}%")
    
    best = results_df.iloc[0]
    print("\n🏆 BEST CONFIGURATION:")
    print(f"   Entry level:         {best['entry_level']:.0f}")
    print(f"   Exit level:          {best['exit_level']:.0f}")
    print(f"   Spread:              {best['spread']:.0f}")
    print(f"   Average return:      {best['avg_return']:.2f}% per trade")
    print(f"   Win rate:            {best['win_rate']:.1f}%")
    print(f"   Total trades:        {best['total_trades']:.0f}")
    
    return results_df


def optimize_asymmetric_thresholds(data):
    """
    Optimization 3: Test asymmetric thresholds
    Based on finding: buy dips works better than buy strength
    """
    print("\n" + "=" * 80)
    print("🔍 OPTIMIZATION 3: ASYMMETRIC STRATEGIES")
    print("=" * 80)
    print("\nBased on insight: Buying dips (<40) outperforms buying strength (>60)")
    print("Testing variations...\n")
    
    strategies = [
        # (name, description, entry_condition, exit_condition)
        ("Current Equilibrium", "Entry: momentum > MA+2, Exit: momentum < MA", 
         lambda m, ma: m > ma + 2, lambda m, ma: m < ma),
        
        ("Buy Dips Only", "Entry: momentum < 40, Exit: momentum > 60",
         lambda m, ma: m < 40, lambda m, ma: m > 60),
        
        ("Buy Dips + Trend", "Entry: momentum < 40 & price > 20EMA, Exit: momentum > 60",
         lambda m, ma: m < 40, lambda m, ma: m > 60),
        
        ("Extreme Dips", "Entry: momentum < 35, Exit: momentum > 55",
         lambda m, ma: m < 35, lambda m, ma: m > 55),
        
        ("Moderate Dips", "Entry: momentum < 45, Exit: momentum > 60",
         lambda m, ma: m < 45, lambda m, ma: m > 60),
        
        ("Mean Reversion", "Entry: momentum < 40, Exit: momentum > 50",
         lambda m, ma: m < 40, lambda m, ma: m > 50),
    ]
    
    results = []
    
    for name, description, entry_cond, exit_cond in strategies:
        data_copy = data.copy()
        data_copy['momentum_ma'] = data_copy['momentum'].rolling(20).mean()
        data_copy['price_ma'] = data_copy['close'].rolling(20).mean()
        
        trades = []
        position = None
        entry_price = None
        entry_bar = None
        
        for i in range(50, len(data_copy)):
            momentum = data_copy.iloc[i]['momentum']
            momentum_ma = data_copy.iloc[i]['momentum_ma']
            price = data_copy.iloc[i]['close']
            price_ma = data_copy.iloc[i]['price_ma']
            
            if position is None:
                # Special handling for "Buy Dips + Trend"
                if "Trend" in name:
                    if entry_cond(momentum, momentum_ma) and price > price_ma:
                        position = 'LONG'
                        entry_price = price
                        entry_bar = i
                else:
                    if entry_cond(momentum, momentum_ma):
                        position = 'LONG'
                        entry_price = price
                        entry_bar = i
            else:
                if exit_cond(momentum, momentum_ma):
                    pnl_pct = (price - entry_price) / entry_price
                    bars_held = i - entry_bar
                    trades.append({
                        'pnl_pct': pnl_pct,
                        'bars_held': bars_held
                    })
                    position = None
        
        if len(trades) >= 5:
            trades_df = pd.DataFrame(trades)
            results.append({
                'strategy': name,
                'description': description,
                'total_trades': len(trades_df),
                'win_rate': (trades_df['pnl_pct'] > 0).sum() / len(trades_df) * 100,
                'avg_return': trades_df['pnl_pct'].mean() * 100,
                'total_return': trades_df['pnl_pct'].sum() * 100,
                'sharpe': trades_df['pnl_pct'].mean() / trades_df['pnl_pct'].std()
            })
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('avg_return', ascending=False)
    
    print("📊 STRATEGY COMPARISON:")
    print("-" * 80)
    
    for i, row in results_df.iterrows():
        print(f"\n{row['strategy']}")
        print(f"   {row['description']}")
        print(f"   Trades: {row['total_trades']:.0f} | Win Rate: {row['win_rate']:.1f}% | "
              f"Avg Return: {row['avg_return']:.2f}% | Total: {row['total_return']:.1f}%")
    
    print("\n🏆 WINNER:")
    best = results_df.iloc[0]
    print(f"   Strategy: {best['strategy']}")
    print(f"   Avg return: {best['avg_return']:.2f}% per trade")
    print(f"   Win rate: {best['win_rate']:.1f}%")
    
    return results_df


def main():
    """Run all threshold optimizations"""
    print("\n" + "🎯" * 40)
    print(" " * 20 + "THRESHOLD OPTIMIZATION")
    print(" " * 15 + "(Finding Optimal Entry/Exit Levels)")
    print("🎯" * 40)
    
    # Load data
    data = load_data()
    
    # Run optimizations
    print("Running 3 optimization tests...\n")
    
    dynamic_results = optimize_dynamic_thresholds(data)
    fixed_results = optimize_fixed_levels(data)
    asymmetric_results = optimize_asymmetric_thresholds(data)
    
    # Final summary
    print("\n" + "=" * 80)
    print("📋 OPTIMIZATION SUMMARY")
    print("=" * 80)
    
    print("\n1️⃣  DYNAMIC EQUILIBRIUM (Best):")
    if dynamic_results is not None and len(dynamic_results) > 0:
        best_dyn = dynamic_results.iloc[0]
        print(f"   Entry: Momentum > MA + {best_dyn['entry_threshold']:.1f}")
        print(f"   Exit:  Momentum < MA - {best_dyn['exit_threshold']:.1f}")
        print(f"   Result: {best_dyn['avg_return']:.2f}% per trade, {best_dyn['win_rate']:.1f}% win rate")
    
    print("\n2️⃣  FIXED LEVELS (Best):")
    if fixed_results is not None and len(fixed_results) > 0:
        best_fix = fixed_results.iloc[0]
        print(f"   Entry: Momentum > {best_fix['entry_level']:.0f}")
        print(f"   Exit:  Momentum < {best_fix['exit_level']:.0f}")
        print(f"   Result: {best_fix['avg_return']:.2f}% per trade, {best_fix['win_rate']:.1f}% win rate")
    
    print("\n3️⃣  ASYMMETRIC STRATEGIES (Best):")
    if asymmetric_results is not None and len(asymmetric_results) > 0:
        best_asym = asymmetric_results.iloc[0]
        print(f"   Strategy: {best_asym['strategy']}")
        print(f"   Result: {best_asym['avg_return']:.2f}% per trade, {best_asym['win_rate']:.1f}% win rate")
    
    print("\n💡 RECOMMENDATION:")
    
    # Find overall best
    best_options = []
    if dynamic_results is not None and len(dynamic_results) > 0:
        best_options.append(('Dynamic', dynamic_results.iloc[0]['avg_return']))
    if fixed_results is not None and len(fixed_results) > 0:
        best_options.append(('Fixed', fixed_results.iloc[0]['avg_return']))
    if asymmetric_results is not None and len(asymmetric_results) > 0:
        best_options.append(('Asymmetric', asymmetric_results.iloc[0]['avg_return']))
    
    if best_options:
        best_approach = max(best_options, key=lambda x: x[1])
        print(f"   Best approach: {best_approach[0]} ({best_approach[1]:.2f}% per trade)")
    
    print("\n✅ Optimization complete!")
    print("\n")


if __name__ == "__main__":
    main()
