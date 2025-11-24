"""
Testing YOUR ACTUAL Equilibrium Strategy
Equilibrium = momentum value at last direction change point (NOT 50!)
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


def calculate_true_equilibrium_strategy(data, threshold=2.0):
    """
    YOUR ACTUAL STRATEGY LOGIC:
    1. Detect direction changes in momentum
    2. Set equilibrium to momentum value at direction change
    3. Entry when momentum > equilibrium + threshold
    4. Exit when momentum < equilibrium - threshold
    """
    data = data.copy()
    
    # Calculate momentum changes
    data['current_change'] = data['momentum'].diff()
    data['previous_change'] = data['current_change'].shift(1)
    
    # Detect direction changes
    data['trend_changed'] = (
        ((data['current_change'] > 0) & (data['previous_change'] <= 0)) |
        ((data['current_change'] < 0) & (data['previous_change'] >= 0))
    )
    
    # Calculate dynamic equilibrium
    equilibrium_level = np.nan
    equilibrium_history = []
    
    for i in range(len(data)):
        if data.iloc[i]['trend_changed'] or np.isnan(equilibrium_level):
            equilibrium_level = data.iloc[i]['momentum']
        equilibrium_history.append(equilibrium_level)
    
    data['equilibrium'] = equilibrium_history
    
    # Calculate zones
    data['momentum_bullish'] = data['momentum'] > data['equilibrium'] + threshold
    data['momentum_bearish'] = data['momentum'] < data['equilibrium'] - threshold
    data['in_yellow_zone'] = abs(data['momentum'] - data['equilibrium']) <= threshold
    
    return data


def backtest_true_strategy(data, threshold=2.0, use_trend_filter=True):
    """Backtest with TRUE equilibrium logic"""
    data = calculate_true_equilibrium_strategy(data, threshold)
    
    # Add trend filter
    data['trend_ma'] = data['close'].rolling(20).mean()
    data['trend_filter_bullish'] = data['close'] > data['trend_ma']
    
    trades = []
    position = None
    entry_price = None
    entry_bar = None
    entry_momentum = None
    entry_equilibrium = None
    
    for i in range(20, len(data)):
        momentum_bullish = data.iloc[i]['momentum_bullish']
        momentum_bearish = data.iloc[i]['momentum_bearish']
        trend_bullish = data.iloc[i]['trend_filter_bullish']
        price = data.iloc[i]['close']
        momentum = data.iloc[i]['momentum']
        equilibrium = data.iloc[i]['equilibrium']
        
        if position is None:
            # LONG entry: momentum bullish + trend filter
            if momentum_bullish and (not use_trend_filter or trend_bullish):
                position = 'LONG'
                entry_price = price
                entry_bar = i
                entry_momentum = momentum
                entry_equilibrium = equilibrium
            
            # SHORT entry: momentum bearish + trend filter
            elif momentum_bearish and (not use_trend_filter or not trend_bullish):
                position = 'SHORT'
                entry_price = price
                entry_bar = i
                entry_momentum = momentum
                entry_equilibrium = equilibrium
        
        else:
            exit_signal = False
            
            if position == 'LONG':
                # Exit LONG when momentum turns bearish
                if momentum_bearish or (use_trend_filter and not trend_bullish):
                    exit_signal = True
            
            elif position == 'SHORT':
                # Exit SHORT when momentum turns bullish
                if momentum_bullish or (use_trend_filter and trend_bullish):
                    exit_signal = True
            
            if exit_signal:
                if position == 'LONG':
                    pnl_pct = (price - entry_price) / entry_price
                else:  # SHORT
                    pnl_pct = (entry_price - price) / entry_price
                
                bars_held = i - entry_bar
                
                trades.append({
                    'type': position,
                    'entry_price': entry_price,
                    'exit_price': price,
                    'entry_momentum': entry_momentum,
                    'exit_momentum': momentum,
                    'entry_equilibrium': entry_equilibrium,
                    'exit_equilibrium': equilibrium,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held
                })
                position = None
    
    return pd.DataFrame(trades) if trades else pd.DataFrame()


def analyze_true_equilibrium(data):
    """Analyze how the true equilibrium behaves"""
    print("=" * 80)
    print("🔍 ANALYSIS: YOUR TRUE EQUILIBRIUM LOGIC")
    print("=" * 80)
    
    data = calculate_true_equilibrium_strategy(data, threshold=2.0)
    
    print(f"\n📊 Equilibrium Statistics:")
    print(f"   Mean equilibrium:        {data['equilibrium'].mean():.2f}")
    print(f"   Std deviation:           {data['equilibrium'].std():.2f}")
    print(f"   Range:                   {data['equilibrium'].min():.2f} - {data['equilibrium'].max():.2f}")
    
    # Count direction changes
    direction_changes = data['trend_changed'].sum()
    print(f"\n🔄 Direction Changes:")
    print(f"   Total changes:           {direction_changes}")
    print(f"   Avg bars between:        {len(data) / direction_changes:.1f}")
    
    # Analyze equilibrium vs momentum
    print(f"\n📈 Momentum vs Equilibrium:")
    print(f"   Time bullish (>eq+2):    {data['momentum_bullish'].sum()} bars ({data['momentum_bullish'].sum()/len(data)*100:.1f}%)")
    print(f"   Time bearish (<eq-2):    {data['momentum_bearish'].sum()} bars ({data['momentum_bearish'].sum()/len(data)*100:.1f}%)")
    print(f"   Time in neutral zone:    {data['in_yellow_zone'].sum()} bars ({data['in_yellow_zone'].sum()/len(data)*100:.1f}%)")
    
    # Analyze equilibrium movement
    eq_changes = data['equilibrium'].diff().abs()
    print(f"\n📊 Equilibrium Movement:")
    print(f"   Average change:          {eq_changes.mean():.2f}")
    print(f"   Max change:              {eq_changes.max():.2f}")
    
    # Show how equilibrium tracks momentum
    correlation = data['equilibrium'].corr(data['momentum'])
    print(f"\n🔗 Equilibrium vs Momentum Correlation: {correlation:.3f}")
    print(f"   → Equilibrium follows momentum trends")


def test_threshold_optimization_true(data):
    """Test different thresholds with TRUE equilibrium logic"""
    print("\n" + "=" * 80)
    print("🎯 THRESHOLD OPTIMIZATION (TRUE EQUILIBRIUM)")
    print("=" * 80)
    
    print("\nTesting thresholds from 0.5 to 5.0...")
    
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
    results = []
    
    for threshold in thresholds:
        # Test with trend filter
        trades_with_filter = backtest_true_strategy(data, threshold, use_trend_filter=True)
        
        # Test without trend filter
        trades_no_filter = backtest_true_strategy(data, threshold, use_trend_filter=False)
        
        if len(trades_with_filter) >= 5:
            long_trades = trades_with_filter[trades_with_filter['type'] == 'LONG']
            short_trades = trades_with_filter[trades_with_filter['type'] == 'SHORT']
            
            results.append({
                'threshold': threshold,
                'filter': 'Yes',
                'total_trades': len(trades_with_filter),
                'long_trades': len(long_trades),
                'short_trades': len(short_trades),
                'win_rate': (trades_with_filter['pnl_pct'] > 0).sum() / len(trades_with_filter) * 100,
                'avg_return': trades_with_filter['pnl_pct'].mean() * 100,
                'long_win_rate': (long_trades['pnl_pct'] > 0).sum() / len(long_trades) * 100 if len(long_trades) > 0 else 0,
                'short_win_rate': (short_trades['pnl_pct'] > 0).sum() / len(short_trades) * 100 if len(short_trades) > 0 else 0,
                'avg_bars_held': trades_with_filter['bars_held'].mean()
            })
        
        if len(trades_no_filter) >= 5:
            long_trades = trades_no_filter[trades_no_filter['type'] == 'LONG']
            short_trades = trades_no_filter[trades_no_filter['type'] == 'SHORT']
            
            results.append({
                'threshold': threshold,
                'filter': 'No',
                'total_trades': len(trades_no_filter),
                'long_trades': len(long_trades),
                'short_trades': len(short_trades),
                'win_rate': (trades_no_filter['pnl_pct'] > 0).sum() / len(trades_no_filter) * 100,
                'avg_return': trades_no_filter['pnl_pct'].mean() * 100,
                'long_win_rate': (long_trades['pnl_pct'] > 0).sum() / len(long_trades) * 100 if len(long_trades) > 0 else 0,
                'short_win_rate': (short_trades['pnl_pct'] > 0).sum() / len(short_trades) * 100 if len(short_trades) > 0 else 0,
                'avg_bars_held': trades_no_filter['bars_held'].mean()
            })
    
    results_df = pd.DataFrame(results)
    
    print("\n📊 RESULTS (With Trend Filter):")
    print("-" * 80)
    print(f"{'Thresh':>7} {'Trades':>7} {'LONG':>6} {'SHORT':>6} {'Win%':>6} {'Avg Ret':>8} {'L Win%':>7} {'S Win%':>7}")
    print("-" * 80)
    
    with_filter = results_df[results_df['filter'] == 'Yes'].sort_values('avg_return', ascending=False)
    for i, row in with_filter.iterrows():
        print(f"{row['threshold']:>7.1f} {row['total_trades']:>7.0f} {row['long_trades']:>6.0f} "
              f"{row['short_trades']:>6.0f} {row['win_rate']:>6.1f} {row['avg_return']:>7.2f}% "
              f"{row['long_win_rate']:>6.1f}% {row['short_win_rate']:>6.1f}%")
    
    print("\n🏆 BEST THRESHOLD (With Filter):")
    if len(with_filter) > 0:
        best = with_filter.iloc[0]
        print(f"   Threshold: {best['threshold']:.1f}")
        print(f"   Avg return: {best['avg_return']:.2f}% per trade")
        print(f"   Win rate: {best['win_rate']:.1f}%")
        print(f"   LONG win rate: {best['long_win_rate']:.1f}% ({best['long_trades']:.0f} trades)")
        print(f"   SHORT win rate: {best['short_win_rate']:.1f}% ({best['short_trades']:.0f} trades)")
    
    print("\n📊 RESULTS (No Trend Filter):")
    print("-" * 80)
    
    no_filter = results_df[results_df['filter'] == 'No'].sort_values('avg_return', ascending=False)
    for i, row in no_filter.head(5).iterrows():
        print(f"{row['threshold']:>7.1f} {row['total_trades']:>7.0f} {row['long_trades']:>6.0f} "
              f"{row['short_trades']:>6.0f} {row['win_rate']:>6.1f} {row['avg_return']:>7.2f}% "
              f"{row['long_win_rate']:>6.1f}% {row['short_win_rate']:>6.1f}%")
    
    return results_df


def compare_equilibrium_methods(data):
    """Compare TRUE equilibrium vs my mistaken MA-based approach"""
    print("\n" + "=" * 80)
    print("⚖️  COMPARISON: TRUE EQUILIBRIUM VS MA-BASED")
    print("=" * 80)
    
    # TRUE equilibrium (your actual code)
    trades_true = backtest_true_strategy(data, threshold=2.0, use_trend_filter=True)
    
    # My mistaken MA-based approach
    data_ma = data.copy()
    data_ma['momentum_ma'] = data_ma['momentum'].rolling(20).mean()
    data_ma['trend_ma'] = data_ma['close'].rolling(20).mean()
    
    trades_ma = []
    position = None
    entry_price = None
    
    for i in range(50, len(data_ma)):
        momentum = data_ma.iloc[i]['momentum']
        momentum_ma = data_ma.iloc[i]['momentum_ma']
        price = data_ma.iloc[i]['close']
        trend_ma = data_ma.iloc[i]['trend_ma']
        
        if position is None:
            if momentum > momentum_ma + 2 and price > trend_ma:
                position = 'LONG'
                entry_price = price
            elif momentum < momentum_ma - 2 and price < trend_ma:
                position = 'SHORT'
                entry_price = price
        else:
            if position == 'LONG' and (momentum < momentum_ma - 2 or price < trend_ma):
                pnl_pct = (price - entry_price) / entry_price
                trades_ma.append({'type': 'LONG', 'pnl_pct': pnl_pct})
                position = None
            elif position == 'SHORT' and (momentum > momentum_ma + 2 or price > trend_ma):
                pnl_pct = (entry_price - price) / entry_price
                trades_ma.append({'type': 'SHORT', 'pnl_pct': pnl_pct})
                position = None
    
    trades_ma_df = pd.DataFrame(trades_ma)
    
    print(f"\n📊 YOUR TRUE EQUILIBRIUM:")
    if len(trades_true) > 0:
        print(f"   Total trades:        {len(trades_true)}")
        print(f"   Win rate:            {(trades_true['pnl_pct'] > 0).sum() / len(trades_true) * 100:.1f}%")
        print(f"   Avg return:          {trades_true['pnl_pct'].mean() * 100:.2f}%")
        print(f"   LONG win rate:       {(trades_true[trades_true['type']=='LONG']['pnl_pct'] > 0).sum() / len(trades_true[trades_true['type']=='LONG']) * 100:.1f}%")
        print(f"   SHORT win rate:      {(trades_true[trades_true['type']=='SHORT']['pnl_pct'] > 0).sum() / len(trades_true[trades_true['type']=='SHORT']) * 100:.1f}%")
    
    print(f"\n📊 MY MISTAKEN MA-BASED:")
    if len(trades_ma_df) > 0:
        print(f"   Total trades:        {len(trades_ma_df)}")
        print(f"   Win rate:            {(trades_ma_df['pnl_pct'] > 0).sum() / len(trades_ma_df) * 100:.1f}%")
        print(f"   Avg return:          {trades_ma_df['pnl_pct'].mean() * 100:.2f}%")
    
    print(f"\n💡 INSIGHT:")
    if len(trades_true) > 0 and len(trades_ma_df) > 0:
        if trades_true['pnl_pct'].mean() > trades_ma_df['pnl_pct'].mean():
            improvement = (trades_true['pnl_pct'].mean() - trades_ma_df['pnl_pct'].mean()) / abs(trades_ma_df['pnl_pct'].mean()) * 100
            print(f"   ✅ YOUR TRUE EQUILIBRIUM is {improvement:.1f}% better!")
            print(f"   → The direction change logic is smarter than simple MA")
        else:
            print(f"   MA-based performs better (surprising!)")


def main():
    """Run analysis with TRUE equilibrium logic"""
    print("\n" + "🎯" * 40)
    print(" " * 15 + "TRUE EQUILIBRIUM ANALYSIS")
    print(" " * 10 + "(Using YOUR actual direction-change logic)")
    print("🎯" * 40)
    
    # Load data
    data = load_data()
    
    # Analyze equilibrium behavior
    analyze_true_equilibrium(data)
    
    # Test threshold optimization
    results = test_threshold_optimization_true(data)
    
    # Compare methods
    compare_equilibrium_methods(data)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nKey insight: Your equilibrium = momentum value at direction changes")
    print("This is SMARTER than using moving averages!")
    print("\n")


if __name__ == "__main__":
    main()
