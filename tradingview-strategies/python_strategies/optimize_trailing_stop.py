"""
Trailing Stop Loss (TSL) Optimization
Test aggressive (tight) vs defensive (wide) trailing stops
Find optimal TSL that maximizes returns
"""
import numpy as np
import pandas as pd
import sys
sys.path.append('.')


def load_data():
    """Load data with momentum"""
    data = pd.read_csv('momentum_indicator_data.csv', index_col=0, parse_dates=True)
    print(f"✅ Loaded {len(data)} bars\n")
    return data


def calculate_true_equilibrium(data, threshold=2.0):
    """Calculate with true equilibrium logic"""
    data = data.copy()
    data['current_change'] = data['momentum'].diff()
    data['previous_change'] = data['current_change'].shift(1)
    data['trend_changed'] = (
        ((data['current_change'] > 0) & (data['previous_change'] <= 0)) |
        ((data['current_change'] < 0) & (data['previous_change'] >= 0))
    )
    
    equilibrium_level = np.nan
    equilibrium_history = []
    for i in range(len(data)):
        if data.iloc[i]['trend_changed'] or np.isnan(equilibrium_level):
            equilibrium_level = data.iloc[i]['momentum']
        equilibrium_history.append(equilibrium_level)
    
    data['equilibrium'] = equilibrium_history
    data['momentum_bullish'] = data['momentum'] > data['equilibrium'] + threshold
    data['momentum_bearish'] = data['momentum'] < data['equilibrium'] - threshold
    data['trend_ma'] = data['close'].rolling(20).mean()
    
    return data


def backtest_with_trailing_stop(data, trail_percent, use_atr=False, atr_multiplier=None):
    """
    Backtest LONG-only with trailing stop
    
    Parameters:
    - trail_percent: % trailing stop (e.g., 0.03 = 3%)
    - use_atr: Use ATR-based trailing instead of percentage
    - atr_multiplier: ATR multiplier if use_atr=True
    """
    data = data.copy()
    
    # Calculate ATR if needed
    if use_atr:
        tr1 = data['high'] - data['low']
        tr2 = abs(data['high'] - data['close'].shift(1))
        tr3 = abs(data['low'] - data['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        data['atr'] = tr.rolling(14).mean()
    
    trades = []
    position = None
    entry_price = None
    entry_bar = None
    highest_price = None
    entry_momentum = None
    
    for i in range(50, len(data)):
        price = data.iloc[i]['close']
        momentum_bullish = data.iloc[i]['momentum_bullish']
        trend_filter = price > data.iloc[i]['trend_ma']
        
        if position is None:
            # LONG-only entry
            if momentum_bullish and trend_filter:
                position = 'LONG'
                entry_price = price
                entry_bar = i
                highest_price = price
                entry_momentum = data.iloc[i]['momentum']
        else:
            # Update highest price
            if price > highest_price:
                highest_price = price
            
            # Calculate trailing stop level
            if use_atr:
                atr = data.iloc[i]['atr']
                trailing_stop = highest_price - (atr * atr_multiplier)
            else:
                trailing_stop = highest_price * (1 - trail_percent)
            
            # Check if hit trailing stop
            if price < trailing_stop:
                pnl_pct = (price - entry_price) / entry_price
                bars_held = i - entry_bar
                max_gain = (highest_price - entry_price) / entry_price
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': price,
                    'highest_price': highest_price,
                    'pnl_pct': pnl_pct,
                    'max_gain': max_gain,
                    'giveback': max_gain - pnl_pct,
                    'bars_held': bars_held,
                    'entry_momentum': entry_momentum,
                    'exit_momentum': data.iloc[i]['momentum']
                })
                position = None
    
    return pd.DataFrame(trades) if trades else pd.DataFrame()


def test_trailing_stop_range(data):
    """Test various trailing stop percentages"""
    print("=" * 80)
    print("🎯 TRAILING STOP OPTIMIZATION")
    print("=" * 80)
    print("\nTesting percentage-based trailing stops from 1% to 15%...")
    
    # Test range of trailing stops
    trail_percents = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.15]
    results = []
    
    for trail_pct in trail_percents:
        trades = backtest_with_trailing_stop(data, trail_pct)
        
        if len(trades) >= 5:
            results.append({
                'trail_pct': trail_pct * 100,
                'total_trades': len(trades),
                'win_rate': (trades['pnl_pct'] > 0).sum() / len(trades) * 100,
                'avg_return': trades['pnl_pct'].mean() * 100,
                'total_return': trades['pnl_pct'].sum() * 100,
                'avg_bars': trades['bars_held'].mean(),
                'max_trade': trades['pnl_pct'].max() * 100,
                'worst_trade': trades['pnl_pct'].min() * 100,
                'avg_giveback': trades['giveback'].mean() * 100,
                'sharpe': trades['pnl_pct'].mean() / trades['pnl_pct'].std() if trades['pnl_pct'].std() > 0 else 0
            })
    
    results_df = pd.DataFrame(results)
    
    print("\n📊 RESULTS (sorted by avg return):")
    print("-" * 80)
    print(f"{'TSL%':>6} {'Trades':>7} {'Win%':>6} {'Avg Ret':>8} {'Total':>7} {'Bars':>5} {'Best':>7} {'Worst':>7} {'Giveback':>9}")
    print("-" * 80)
    
    results_sorted = results_df.sort_values('avg_return', ascending=False)
    for i, row in results_sorted.iterrows():
        print(f"{row['trail_pct']:>6.1f} {row['total_trades']:>7.0f} {row['win_rate']:>6.1f} "
              f"{row['avg_return']:>7.2f}% {row['total_return']:>6.1f}% {row['avg_bars']:>5.0f} "
              f"{row['max_trade']:>6.1f}% {row['worst_trade']:>6.1f}% {row['avg_giveback']:>8.2f}%")
    
    print("\n" + "=" * 80)
    print("🏆 TOP 3 CONFIGURATIONS")
    print("=" * 80)
    
    for rank, (i, row) in enumerate(results_sorted.head(3).iterrows(), 1):
        print(f"\n#{rank}: {row['trail_pct']:.1f}% Trailing Stop")
        print(f"   Trades:          {row['total_trades']:.0f}")
        print(f"   Win rate:        {row['win_rate']:.1f}%")
        print(f"   Avg return:      {row['avg_return']:.2f}% per trade")
        print(f"   Total return:    {row['total_return']:.1f}%")
        print(f"   Avg hold time:   {row['avg_bars']:.0f} bars")
        print(f"   Best trade:      {row['max_trade']:.1f}%")
        print(f"   Worst trade:     {row['worst_trade']:.1f}%")
        print(f"   Avg giveback:    {row['avg_giveback']:.2f}% (from peak)")
        print(f"   Sharpe ratio:    {row['sharpe']:.2f}")
    
    return results_df


def test_atr_based_trailing(data):
    """Test ATR-based trailing stops"""
    print("\n" + "=" * 80)
    print("📊 ATR-BASED TRAILING STOP")
    print("=" * 80)
    print("\nTesting ATR multipliers from 1.0x to 4.0x...")
    
    atr_multipliers = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    results = []
    
    for mult in atr_multipliers:
        trades = backtest_with_trailing_stop(data, None, use_atr=True, atr_multiplier=mult)
        
        if len(trades) >= 5:
            results.append({
                'atr_mult': mult,
                'total_trades': len(trades),
                'win_rate': (trades['pnl_pct'] > 0).sum() / len(trades) * 100,
                'avg_return': trades['pnl_pct'].mean() * 100,
                'total_return': trades['pnl_pct'].sum() * 100,
                'avg_bars': trades['bars_held'].mean(),
                'avg_giveback': trades['giveback'].mean() * 100
            })
    
    results_df = pd.DataFrame(results)
    
    print("\n📊 RESULTS (ATR-based):")
    print("-" * 80)
    print(f"{'ATR':>6} {'Trades':>7} {'Win%':>6} {'Avg Ret':>8} {'Total':>7} {'Bars':>5} {'Giveback':>9}")
    print("-" * 80)
    
    results_sorted = results_df.sort_values('avg_return', ascending=False)
    for i, row in results_sorted.iterrows():
        print(f"{row['atr_mult']:>6.1f} {row['total_trades']:>7.0f} {row['win_rate']:>6.1f} "
              f"{row['avg_return']:>7.2f}% {row['total_return']:>6.1f}% {row['avg_bars']:>5.0f} "
              f"{row['avg_giveback']:>8.2f}%")
    
    if len(results_sorted) > 0:
        best = results_sorted.iloc[0]
        print(f"\n🏆 BEST: {best['atr_mult']:.1f}x ATR")
        print(f"   Avg return: {best['avg_return']:.2f}% per trade")
        print(f"   Win rate: {best['win_rate']:.1f}%")
    
    return results_df


def test_aggressive_vs_defensive(data):
    """Compare aggressive (tight) vs defensive (wide) strategies"""
    print("\n" + "=" * 80)
    print("⚔️  AGGRESSIVE VS DEFENSIVE COMPARISON")
    print("=" * 80)
    
    strategies = {
        'VERY AGGRESSIVE (1%)': 0.01,
        'AGGRESSIVE (2%)': 0.02,
        'MODERATE (5%)': 0.05,
        'DEFENSIVE (8%)': 0.08,
        'VERY DEFENSIVE (12%)': 0.12
    }
    
    results = []
    
    for name, trail_pct in strategies.items():
        trades = backtest_with_trailing_stop(data, trail_pct)
        
        if len(trades) >= 5:
            # Calculate additional metrics
            winners = trades[trades['pnl_pct'] > 0]
            losers = trades[trades['pnl_pct'] <= 0]
            
            results.append({
                'strategy': name,
                'trail_pct': trail_pct * 100,
                'trades': len(trades),
                'win_rate': len(winners) / len(trades) * 100,
                'avg_return': trades['pnl_pct'].mean() * 100,
                'total_return': trades['pnl_pct'].sum() * 100,
                'avg_winner': winners['pnl_pct'].mean() * 100 if len(winners) > 0 else 0,
                'avg_loser': losers['pnl_pct'].mean() * 100 if len(losers) > 0 else 0,
                'win_loss_ratio': abs(winners['pnl_pct'].mean() / losers['pnl_pct'].mean()) if len(losers) > 0 and len(winners) > 0 else 0,
                'avg_bars': trades['bars_held'].mean(),
                'avg_giveback': trades['giveback'].mean() * 100
            })
    
    print("\n📊 STRATEGY COMPARISON:")
    print("=" * 80)
    
    for res in results:
        print(f"\n{res['strategy']}")
        print(f"   Trailing stop:       {res['trail_pct']:.0f}%")
        print(f"   Total trades:        {res['trades']:.0f}")
        print(f"   Win rate:            {res['win_rate']:.1f}%")
        print(f"   Avg return:          {res['avg_return']:.2f}% per trade")
        print(f"   Total return:        {res['total_return']:.1f}%")
        print(f"   Avg winner:          {res['avg_winner']:.2f}%")
        print(f"   Avg loser:           {res['avg_loser']:.2f}%")
        print(f"   Win/Loss ratio:      {res['win_loss_ratio']:.2f}:1")
        print(f"   Avg hold time:       {res['avg_bars']:.0f} bars")
        print(f"   Avg giveback:        {res['avg_giveback']:.2f}%")
    
    # Find best by different metrics
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 80)
    print("🏆 WINNERS BY METRIC")
    print("=" * 80)
    
    best_avg = results_df.loc[results_df['avg_return'].idxmax()]
    best_total = results_df.loc[results_df['total_return'].idxmax()]
    best_winrate = results_df.loc[results_df['win_rate'].idxmax()]
    best_ratio = results_df.loc[results_df['win_loss_ratio'].idxmax()]
    
    print(f"\n📈 Best Avg Return:      {best_avg['strategy']} ({best_avg['avg_return']:.2f}%)")
    print(f"💰 Best Total Return:    {best_total['strategy']} ({best_total['total_return']:.1f}%)")
    print(f"🎯 Best Win Rate:        {best_winrate['strategy']} ({best_winrate['win_rate']:.1f}%)")
    print(f"⚖️  Best Win/Loss Ratio:  {best_ratio['strategy']} ({best_ratio['win_loss_ratio']:.2f}:1)")
    
    return results_df


def test_dynamic_trailing(data):
    """Test dynamic trailing stop that adjusts based on profit"""
    print("\n" + "=" * 80)
    print("🎨 DYNAMIC TRAILING STOP (ADJUSTS WITH PROFIT)")
    print("=" * 80)
    print("\nIdea: Start tight, widen as profit increases")
    
    trades_static = backtest_with_trailing_stop(data, 0.05)  # 5% static
    
    # Dynamic: Start at 3%, widen to 7% as profit increases
    trades_dynamic = []
    
    data_calc = calculate_true_equilibrium(data)
    position = None
    entry_price = None
    entry_bar = None
    highest_price = None
    
    for i in range(50, len(data_calc)):
        price = data_calc.iloc[i]['close']
        momentum_bullish = data_calc.iloc[i]['momentum_bullish']
        trend_filter = price > data_calc.iloc[i]['trend_ma']
        
        if position is None:
            if momentum_bullish and trend_filter:
                position = 'LONG'
                entry_price = price
                entry_bar = i
                highest_price = price
        else:
            if price > highest_price:
                highest_price = price
            
            # Calculate current profit
            current_profit = (highest_price - entry_price) / entry_price
            
            # Dynamic trailing: tighter when small profit, wider when larger profit
            if current_profit < 0.02:  # Less than 2% profit
                trail_pct = 0.03  # 3% trailing (tight)
            elif current_profit < 0.05:  # 2-5% profit
                trail_pct = 0.05  # 5% trailing (moderate)
            else:  # More than 5% profit
                trail_pct = 0.07  # 7% trailing (loose - let it run!)
            
            trailing_stop = highest_price * (1 - trail_pct)
            
            if price < trailing_stop:
                pnl_pct = (price - entry_price) / entry_price
                bars_held = i - entry_bar
                trades_dynamic.append({
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held
                })
                position = None
    
    trades_dynamic_df = pd.DataFrame(trades_dynamic)
    
    print(f"\n📊 STATIC 5% TSL:")
    if len(trades_static) > 0:
        print(f"   Trades:          {len(trades_static)}")
        print(f"   Win rate:        {(trades_static['pnl_pct'] > 0).sum() / len(trades_static) * 100:.1f}%")
        print(f"   Avg return:      {trades_static['pnl_pct'].mean() * 100:.2f}%")
        print(f"   Total return:    {trades_static['pnl_pct'].sum() * 100:.1f}%")
    
    print(f"\n📊 DYNAMIC TSL (3%→5%→7%):")
    if len(trades_dynamic_df) > 0:
        print(f"   Trades:          {len(trades_dynamic_df)}")
        print(f"   Win rate:        {(trades_dynamic_df['pnl_pct'] > 0).sum() / len(trades_dynamic_df) * 100:.1f}%")
        print(f"   Avg return:      {trades_dynamic_df['pnl_pct'].mean() * 100:.2f}%")
        print(f"   Total return:    {trades_dynamic_df['pnl_pct'].sum() * 100:.1f}%")
        
        if len(trades_static) > 0:
            improvement = (trades_dynamic_df['pnl_pct'].mean() - trades_static['pnl_pct'].mean()) / abs(trades_static['pnl_pct'].mean()) * 100
            print(f"\n   📈 IMPROVEMENT: {improvement:+.1f}%")


def compare_to_signal_exit(data):
    """Compare trailing stop to original signal-based exit"""
    print("\n" + "=" * 80)
    print("⚖️  TSL VS ORIGINAL SIGNAL EXIT")
    print("=" * 80)
    
    # Original: Exit on opposite signal
    data_calc = calculate_true_equilibrium(data)
    trades_signal = []
    position = None
    entry_price = None
    entry_bar = None
    
    for i in range(50, len(data_calc)):
        price = data_calc.iloc[i]['close']
        momentum_bullish = data_calc.iloc[i]['momentum_bullish']
        momentum_bearish = data_calc.iloc[i]['momentum_bearish']
        trend_filter = price > data_calc.iloc[i]['trend_ma']
        
        if position is None:
            if momentum_bullish and trend_filter:
                position = 'LONG'
                entry_price = price
                entry_bar = i
        else:
            # Exit on opposite signal (original method)
            if momentum_bearish or not trend_filter:
                pnl_pct = (price - entry_price) / entry_price
                bars_held = i - entry_bar
                trades_signal.append({'pnl_pct': pnl_pct, 'bars_held': bars_held})
                position = None
    
    trades_signal_df = pd.DataFrame(trades_signal)
    
    # Best trailing stop from earlier
    trades_tsl = backtest_with_trailing_stop(data, 0.05)  # 5% TSL
    
    print(f"\n📊 ORIGINAL (Signal-based exit):")
    if len(trades_signal_df) > 0:
        print(f"   Trades:          {len(trades_signal_df)}")
        print(f"   Win rate:        {(trades_signal_df['pnl_pct'] > 0).sum() / len(trades_signal_df) * 100:.1f}%")
        print(f"   Avg return:      {trades_signal_df['pnl_pct'].mean() * 100:.2f}%")
        print(f"   Total return:    {trades_signal_df['pnl_pct'].sum() * 100:.1f}%")
        print(f"   Avg hold time:   {trades_signal_df['bars_held'].mean():.0f} bars")
    
    print(f"\n📊 TRAILING STOP (5%):")
    if len(trades_tsl) > 0:
        print(f"   Trades:          {len(trades_tsl)}")
        print(f"   Win rate:        {(trades_tsl['pnl_pct'] > 0).sum() / len(trades_tsl) * 100:.1f}%")
        print(f"   Avg return:      {trades_tsl['pnl_pct'].mean() * 100:.2f}%")
        print(f"   Total return:    {trades_tsl['pnl_pct'].sum() * 100:.1f}%")
        print(f"   Avg hold time:   {trades_tsl['bars_held'].mean():.0f} bars")
    
    if len(trades_signal_df) > 0 and len(trades_tsl) > 0:
        improvement = (trades_tsl['pnl_pct'].mean() - trades_signal_df['pnl_pct'].mean()) / abs(trades_signal_df['pnl_pct'].mean()) * 100
        print(f"\n💡 TSL IMPROVEMENT: {improvement:+.1f}%")
        
        if improvement > 0:
            print(f"   ✅ Trailing stop is BETTER!")
        else:
            print(f"   ❌ Original signal exit is better")


def main():
    """Run all TSL optimization tests"""
    print("\n" + "🎯" * 40)
    print(" " * 15 + "TRAILING STOP OPTIMIZATION")
    print(" " * 10 + "(Finding the perfect balance: Aggressive vs Defensive)")
    print("🎯" * 40)
    
    data = load_data()
    data = calculate_true_equilibrium(data)
    
    # Test 1: Range of percentage-based TSL
    pct_results = test_trailing_stop_range(data)
    
    # Test 2: ATR-based TSL
    atr_results = test_atr_based_trailing(data)
    
    # Test 3: Aggressive vs Defensive comparison
    comparison = test_aggressive_vs_defensive(data)
    
    # Test 4: Dynamic TSL
    test_dynamic_trailing(data)
    
    # Test 5: Compare to original
    compare_to_signal_exit(data)
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("📋 FINAL RECOMMENDATIONS")
    print("=" * 80)
    
    if len(pct_results) > 0:
        best = pct_results.sort_values('avg_return', ascending=False).iloc[0]
        
        print(f"\n💡 RECOMMENDED TRAILING STOP:")
        print(f"   {best['trail_pct']:.0f}% trailing stop")
        print(f"   ")
        print(f"   Why this works:")
        print(f"   • Avg return: {best['avg_return']:.2f}% per trade")
        print(f"   • Win rate: {best['win_rate']:.1f}%")
        print(f"   • Total return: {best['total_return']:.1f}%")
        print(f"   • Holds for ~{best['avg_bars']:.0f} bars")
        print(f"   • Gives back only {best['avg_giveback']:.1f}% from peak")
        
        print(f"\n🎯 IMPLEMENTATION IN PINE SCRIPT:")
        print(f"   ")
        print(f"   trail_percent = {best['trail_pct']/100:.2f}  // {best['trail_pct']:.0f}%")
        print(f"   ")
        print(f"   if strategy.position_size > 0")
        print(f"       trail_price = high * (1 - trail_percent)")
        print(f"       strategy.exit(\"Trail Stop\", stop=trail_price)")
    
    print("\n✅ Optimization complete!")
    print("\n")


if __name__ == "__main__":
    main()
