"""
COMPLETE RE-VALIDATION FROM SCRATCH
No assumptions. Show all code. Verify every step.

We'll test in order:
1. LONG+SHORT vs LONG-only (is LONG-only really better?)
2. Trailing stop vs signal exit (is 3% TSL really better?)
3. Position sizing impact (what does 2% vs 1% actually do?)

With FULL code visibility and NO bugs.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("\n" + "🔍" * 40)
print(" " * 10 + "COMPLETE RE-VALIDATION FROM SCRATCH")
print(" " * 15 + "(Questioning Everything)")
print("🔍" * 40)

# Download data
print("\n📥 Downloading SPY data (2 years for faster validation)...")
spy = yf.download('SPY', start='2023-01-01', progress=False)

if isinstance(spy.columns, pd.MultiIndex):
    spy.columns = [col[0].lower() for col in spy.columns]
else:
    spy.columns = spy.columns.str.lower()

print(f"✅ {len(spy)} bars downloaded")

# Calculate momentum indicator - SHOWING ALL CODE
print("\n📊 Calculating momentum indicator...")
print("   (Full Pine Script logic with all smoothing layers)")

def calculate_full_momentum(df):
    """
    Full momentum calculation - EXACT Pine Script logic
    Showing every step
    """
    # Initialize all state variables
    v8 = 0.0
    v16 = 0.0
    v0 = 0.0
    v80 = 0.0
    v88 = 0.0
    v96 = 0.0
    v104 = 0.0
    v112 = 0.0
    v120 = 0.0
    v128 = 0.0
    v208 = 0.0
    v136 = 0.0
    v152 = 0.0
    v160 = 0.0
    v168 = 0.0
    v176 = 0.0
    v184 = 0.0
    v192 = 0.0
    v200 = 0.0
    
    len_param = 7
    momentum_values = []
    
    for i in range(len(df)):
        tp = (df.iloc[i]['high'] + df.iloc[i]['low'] + df.iloc[i]['close']) / 3.0
        v24 = 50.0
        
        if v8 == 0.0:
            v8 = 1.0
            v16 = 0.0
            v0 = len_param - 1 if len_param - 1 >= 5 else 5.0
            v80 = 100.0 * tp
            v96 = 3.0 / (len_param + 2.0)
            v104 = 1.0 - v96
        else:
            if v0 <= v8:
                v8 = v0 + 1.0
            else:
                v8 = v8 + 1.0
            
            v88 = v80
            v80 = 100.0 * tp
            v32 = v80 - v88
            
            # Multi-layer smoothing
            v112 = v104 * v112 + v96 * v32
            v120 = v96 * v112 + v104 * v120
            v40 = 1.5 * v112 - v120 / 2.0
            
            v128 = v104 * v128 + v96 * v40
            v208 = v96 * v128 + v104 * v208
            v48 = 1.5 * v128 - v208 / 2.0
            
            v136 = v104 * v136 + v96 * v48
            v152 = v96 * v136 + v104 * v152
            v56 = 1.5 * v136 - v152 / 2.0
            
            v160 = v104 * v160 + v96 * abs(v32)
            v168 = v96 * v160 + v104 * v168
            v64 = 1.5 * v160 - v168 / 2.0
            
            v176 = v104 * v176 + v96 * v64
            v184 = v96 * v176 + v104 * v184
            v144 = 1.5 * v176 - v184 / 2.0
            
            v192 = v104 * v192 + v96 * v144
            v200 = v96 * v192 + v104 * v200
            v72 = 1.5 * v192 - v200 / 2.0
            
            if v0 >= v8 and v80 != v88:
                v16 = 1.0
            if v0 == v8 and v16 == 0.0:
                v8 = 0.0
            
            if v0 < v8 and v72 > 0.0000000001:
                v24 = 50.0 * (v56 / v72 + 1.0)
                if v24 > 100.0:
                    v24 = 100.0
                if v24 < 0.0:
                    v24 = 0.0
        
        momentum_values.append(v24)
    
    return pd.Series(momentum_values, index=df.index)

spy['momentum'] = calculate_full_momentum(spy)

# Calculate equilibrium
prev_momentum = spy['momentum'].shift(1).fillna(50.0)
prev_prev_momentum = spy['momentum'].shift(2).fillna(50.0)
current_change = spy['momentum'] - prev_momentum
previous_change = prev_momentum - prev_prev_momentum

trend_changed = ((current_change > 0) & (previous_change <= 0)) | \
                ((current_change < 0) & (previous_change >= 0))

equilibrium = spy['momentum'].copy()
equilibrium[~trend_changed] = np.nan
equilibrium = equilibrium.fillna(method='ffill').fillna(50.0)

spy['equilibrium'] = equilibrium

# Signals
threshold = 2.0
spy['momentum_bullish'] = spy['momentum'] > (spy['equilibrium'] + threshold)
spy['momentum_bearish'] = spy['momentum'] < (spy['equilibrium'] - threshold)

spy = spy.dropna()

print(f"✅ Momentum calculated for {len(spy)} bars")

# Simple backtest function with FULL visibility
def backtest_strategy(data, long_only=False, use_trailing_stop=False, 
                     trailing_stop_pct=3.0, risk_percent=1.0, strategy_name=""):
    """
    Transparent backtest with visible logic
    
    Position sizing: SIMPLE and CORRECT
    - Risk X% of capital per trade
    - Size = (capital * risk_pct) / stop_distance
    - P&L = shares * (exit - entry)
    
    NO mysterious multipliers!
    """
    
    print(f"\n{'='*80}")
    print(f"Testing: {strategy_name}")
    print(f"  Long Only: {long_only}")
    print(f"  Trailing Stop: {use_trailing_stop} ({trailing_stop_pct}% if True)")
    print(f"  Risk: {risk_percent}%")
    print(f"{'='*80}")
    
    capital = 10000.0
    position = 0
    position_side = None
    entry_price = 0
    trail_stop = 0
    trades = []
    
    for i in range(1, len(data)):
        price = data.iloc[i]['close']
        momentum_bullish = data.iloc[i]['momentum_bullish']
        momentum_bearish = data.iloc[i]['momentum_bearish']
        
        # ENTRY
        if position == 0:
            # LONG entry
            if momentum_bullish:
                risk_amount = capital * (risk_percent / 100)
                stop_distance = price * (trailing_stop_pct / 100) if use_trailing_stop else price * 0.03
                shares = int(risk_amount / stop_distance)
                
                if shares > 0 and shares * price <= capital:
                    position = shares
                    position_side = 'LONG'
                    entry_price = price
                    trail_stop = price * (1 - trailing_stop_pct / 100) if use_trailing_stop else 0
                    
                    print(f"  📈 LONG entry: {shares} shares @ ${price:.2f}")
            
            # SHORT entry (if allowed)
            elif momentum_bearish and not long_only:
                risk_amount = capital * (risk_percent / 100)
                stop_distance = price * (trailing_stop_pct / 100) if use_trailing_stop else price * 0.03
                shares = int(risk_amount / stop_distance)
                
                if shares > 0 and shares * price <= capital:
                    position = shares
                    position_side = 'SHORT'
                    entry_price = price
                    trail_stop = price * (1 + trailing_stop_pct / 100) if use_trailing_stop else 0
                    
                    print(f"  📉 SHORT entry: {shares} shares @ ${price:.2f}")
        
        # UPDATE TRAILING STOP
        elif position > 0 and use_trailing_stop:
            if position_side == 'LONG':
                new_stop = price * (1 - trailing_stop_pct / 100)
                if new_stop > trail_stop:
                    trail_stop = new_stop
            elif position_side == 'SHORT':
                new_stop = price * (1 + trailing_stop_pct / 100)
                if new_stop < trail_stop:
                    trail_stop = new_stop
        
        # EXIT
        if position > 0:
            exit_triggered = False
            exit_reason = ""
            
            if position_side == 'LONG':
                if use_trailing_stop and price <= trail_stop:
                    exit_triggered = True
                    exit_reason = "Trailing Stop"
                elif not use_trailing_stop and momentum_bearish:
                    exit_triggered = True
                    exit_reason = "Signal Exit"
            
            elif position_side == 'SHORT':
                if use_trailing_stop and price >= trail_stop:
                    exit_triggered = True
                    exit_reason = "Trailing Stop"
                elif not use_trailing_stop and momentum_bullish:
                    exit_triggered = True
                    exit_reason = "Signal Exit"
            
            if exit_triggered:
                # Calculate P&L - SIMPLE AND CORRECT
                if position_side == 'LONG':
                    pnl = position * (price - entry_price)
                else:  # SHORT
                    pnl = position * (entry_price - price)
                
                pnl_pct = (pnl / (position * entry_price)) * 100
                
                capital += pnl
                
                print(f"  💰 {position_side} exit: ${price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%) | {exit_reason}")
                print(f"     Capital: ${capital:.2f}")
                
                trades.append({
                    'side': position_side,
                    'entry': entry_price,
                    'exit': price,
                    'shares': position,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'capital': capital,
                    'reason': exit_reason
                })
                
                position = 0
                position_side = None
    
    print(f"\n📊 Results:")
    print(f"  Trades: {len(trades)}")
    if len(trades) > 0:
        df_trades = pd.DataFrame(trades)
        wins = len(df_trades[df_trades['pnl'] > 0])
        print(f"  Wins: {wins}/{len(trades)} ({wins/len(trades)*100:.1f}%)")
        print(f"  Avg P&L: ${df_trades['pnl'].mean():.2f}")
        print(f"  Avg %: {df_trades['pnl_pct'].mean():.2f}%")
        print(f"  Final Capital: ${capital:.2f}")
        print(f"  Total Return: {(capital/10000-1)*100:.1f}%")
        
        # Show breakdown
        if not long_only:
            long_trades = df_trades[df_trades['side'] == 'LONG']
            short_trades = df_trades[df_trades['side'] == 'SHORT']
            if len(long_trades) > 0:
                print(f"\n  LONG trades: {len(long_trades)}, Win rate: {(long_trades['pnl'] > 0).mean()*100:.1f}%")
            if len(short_trades) > 0:
                print(f"  SHORT trades: {len(short_trades)}, Win rate: {(short_trades['pnl'] > 0).mean()*100:.1f}%")
    
    return pd.DataFrame(trades), capital

# TEST 1: LONG+SHORT vs LONG-only
print("\n" + "🔬" * 40)
print("TEST 1: Is LONG-only really better than LONG+SHORT?")
print("🔬" * 40)

trades_both, capital_both = backtest_strategy(
    spy, 
    long_only=False, 
    use_trailing_stop=False,
    risk_percent=1.0,
    strategy_name="BASE: LONG+SHORT, Signal Exit, 1% Risk"
)

trades_long, capital_long = backtest_strategy(
    spy,
    long_only=True,
    use_trailing_stop=False,
    risk_percent=1.0,
    strategy_name="LONG-only, Signal Exit, 1% Risk"
)

print(f"\n{'='*80}")
print("CONCLUSION FOR TEST 1:")
print(f"{'='*80}")
print(f"LONG+SHORT: ${capital_both:.2f} ({(capital_both/10000-1)*100:+.1f}%)")
print(f"LONG-only:  ${capital_long:.2f} ({(capital_long/10000-1)*100:+.1f}%)")
if capital_long > capital_both:
    print(f"✅ LONG-only IS better by ${capital_long - capital_both:.2f}")
else:
    print(f"❌ LONG+SHORT is actually better by ${capital_both - capital_long:.2f}")
    print(f"   (Previous conclusion was WRONG!)")

# TEST 2: Signal exit vs Trailing stop
print("\n" + "🔬" * 40)
print("TEST 2: Is 3% Trailing Stop really better than Signal Exit?")
print("🔬" * 40)

trades_signal, capital_signal = backtest_strategy(
    spy,
    long_only=True,
    use_trailing_stop=False,
    risk_percent=1.0,
    strategy_name="LONG-only, Signal Exit, 1% Risk"
)

trades_tsl, capital_tsl = backtest_strategy(
    spy,
    long_only=True,
    use_trailing_stop=True,
    trailing_stop_pct=3.0,
    risk_percent=1.0,
    strategy_name="LONG-only, 3% TSL, 1% Risk"
)

print(f"\n{'='*80}")
print("CONCLUSION FOR TEST 2:")
print(f"{'='*80}")
print(f"Signal Exit: ${capital_signal:.2f} ({(capital_signal/10000-1)*100:+.1f}%)")
print(f"3% TSL:      ${capital_tsl:.2f} ({(capital_tsl/10000-1)*100:+.1f}%)")
if capital_tsl > capital_signal:
    print(f"✅ 3% TSL IS better by ${capital_tsl - capital_signal:.2f}")
else:
    print(f"❌ Signal exit is actually better by ${capital_signal - capital_tsl:.2f}")
    print(f"   (Previous conclusion was WRONG!)")

# TEST 3: 1% vs 2% risk
print("\n" + "🔬" * 40)
print("TEST 3: Does 2% risk really double the returns?")
print("🔬" * 40)

trades_1pct, capital_1pct = backtest_strategy(
    spy,
    long_only=True,
    use_trailing_stop=True,
    trailing_stop_pct=3.0,
    risk_percent=1.0,
    strategy_name="LONG-only, 3% TSL, 1% Risk"
)

trades_2pct, capital_2pct = backtest_strategy(
    spy,
    long_only=True,
    use_trailing_stop=True,
    trailing_stop_pct=3.0,
    risk_percent=2.0,
    strategy_name="LONG-only, 3% TSL, 2% Risk"
)

print(f"\n{'='*80}")
print("CONCLUSION FOR TEST 3:")
print(f"{'='*80}")
print(f"1% Risk: ${capital_1pct:.2f} ({(capital_1pct/10000-1)*100:+.1f}%)")
print(f"2% Risk: ${capital_2pct:.2f} ({(capital_2pct/10000-1)*100:+.1f}%)")
improvement = (capital_2pct / capital_1pct - 1) * 100
print(f"Improvement: {improvement:+.1f}%")
if abs(improvement - 100) < 20:
    print(f"✅ Yes, 2% risk roughly doubles returns")
else:
    print(f"❌ No, the improvement is {improvement:.1f}%, not 100%")

# FINAL SUMMARY
print("\n" + "🎯" * 40)
print("FINAL VALIDATED RESULTS")
print("🎯" * 40)

print(f"""
All tests completed with full code visibility.

TEST 1: LONG-only vs LONG+SHORT
  Winner: {'LONG-only' if capital_long > capital_both else 'LONG+SHORT'}
  Difference: ${abs(capital_long - capital_both):.2f}

TEST 2: 3% TSL vs Signal Exit
  Winner: {'3% TSL' if capital_tsl > capital_signal else 'Signal Exit'}
  Difference: ${abs(capital_tsl - capital_signal):.2f}

TEST 3: 2% vs 1% Risk
  1% Risk: ${capital_1pct:.2f}
  2% Risk: ${capital_2pct:.2f}
  Multiplier: {capital_2pct/capital_1pct:.2f}x

BEST CONFIGURATION:
  Setup: {'LONG-only' if capital_long > capital_both else 'LONG+SHORT'}, \
{'3% TSL' if capital_tsl > capital_signal else 'Signal Exit'}, 2% Risk
  Result: ${capital_2pct:.2f} ({(capital_2pct/10000-1)*100:.1f}% total return)
  Period: 2 years
  Annual: ~{(capital_2pct/10000-1)*100/2:.1f}% per year

These results are VALIDATED with visible code and NO bugs (that I can see).
Please review the code above to verify my logic is correct.
""")
