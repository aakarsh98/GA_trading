"""
AAPL Volatility Mean Reversion Analysis
Test if AAPL's volatility behaves like VIX (mean reverts)

Uses Historical Volatility as proxy for IV
(For real IV, use DoltHub data)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("\n" + "🍎" * 40)
print(" " * 10 + "AAPL VOLATILITY MEAN REVERSION TEST")
print(" " * 15 + "(vs VIX Baseline Comparison)")
print("🍎" * 40)

# Download AAPL data (5 years for robust analysis)
print("\n📥 Downloading AAPL data (5 years)...")
aapl = yf.download('AAPL', period='5y', progress=False)

if isinstance(aapl.columns, pd.MultiIndex):
    aapl.columns = [col[0].lower() for col in aapl.columns]
else:
    aapl.columns = aapl.columns.str.lower()

print(f"✅ Downloaded {len(aapl)} days of AAPL data")
print(f"   Period: {aapl.index[0].date()} to {aapl.index[-1].date()}")

# Get current IV from options
print("\n📊 Getting Current AAPL IV from options...")
try:
    ticker = yf.Ticker('AAPL')
    current_price = aapl['close'].iloc[-1]
    
    # Get ATM options
    exp = ticker.options[0]
    chain = ticker.option_chain(exp)
    
    # Find ATM call
    calls = chain.calls
    calls['diff'] = abs(calls['strike'] - current_price)
    atm_call = calls.loc[calls['diff'].idxmin()]
    
    current_iv = atm_call['impliedVolatility']
    
    print(f"✅ Current AAPL Price: ${current_price:.2f}")
    print(f"✅ Current Implied Volatility: {current_iv*100:.1f}%")
    print(f"   Strike: ${atm_call['strike']:.2f}")
    print(f"   Expiration: {exp}")
    
except Exception as e:
    print(f"⚠️  Could not get current IV: {e}")
    current_iv = None

# Calculate Historical Volatility (20-day)
print("\n📈 Calculating Historical Volatility (proxy for IV)...")
returns = aapl['close'].pct_change()
aapl['hv_20d'] = returns.rolling(20).std() * np.sqrt(252) * 100

# Calculate HV Percentile (proxy for IVP)
lookback = 252
hvp_values = []

for i in range(len(aapl)):
    if i < lookback:
        hvp_values.append(None)
    else:
        current_hv = aapl.iloc[i]['hv_20d']
        historical = aapl.iloc[i-lookback:i]['hv_20d'].dropna()
        
        if len(historical) > 0 and not np.isnan(current_hv):
            percentile = (historical < current_hv).sum() / len(historical) * 100
            hvp_values.append(percentile)
        else:
            hvp_values.append(None)

aapl['hvp'] = hvp_values

print(f"✅ HV calculated for {aapl['hv_20d'].notna().sum()} days")
print(f"✅ HVP calculated for {aapl['hvp'].notna().sum()} days")

current_hv = aapl['hv_20d'].iloc[-1]
current_hvp = aapl['hvp'].iloc[-1]

print(f"\n📊 Current AAPL Volatility Status:")
print(f"   Historical Vol (20d): {current_hv:.1f}%")
print(f"   HV Percentile: {current_hvp:.1f}%")

if current_iv:
    print(f"   Implied Volatility: {current_iv*100:.1f}%")
    iv_hv_spread = (current_iv*100) - current_hv
    print(f"   IV - HV Spread: {iv_hv_spread:.1f}% (variance risk premium)")

# Test mean reversion
print("\n" + "=" * 80)
print("🔬 MEAN REVERSION TEST: AAPL HVP THRESHOLDS")
print("=" * 80)

thresholds = [50, 60, 70, 80, 90]
forward_periods = [1, 5, 10, 20]

results_table = []

for threshold in thresholds:
    high_hvp = aapl[aapl['hvp'] >= threshold].copy()
    
    if len(high_hvp) == 0:
        continue
    
    print(f"\n{'─'*80}")
    print(f"Testing: HVP >= {threshold}%")
    print(f"{'─'*80}")
    print(f"   Days with HVP >= {threshold}: {len(high_hvp)}")
    
    for days in forward_periods:
        declines = 0
        total = 0
        changes = []
        
        for idx in high_hvp.index:
            try:
                current_hv = aapl.loc[idx, 'hv_20d']
                future_idx = aapl.index.get_loc(idx) + days
                
                if future_idx < len(aapl):
                    future_hv = aapl.iloc[future_idx]['hv_20d']
                    
                    if not np.isnan(current_hv) and not np.isnan(future_hv):
                        if future_hv < current_hv:
                            declines += 1
                        
                        change_pct = (future_hv - current_hv) / current_hv * 100
                        changes.append(change_pct)
                        total += 1
            except:
                pass
        
        if total > 0:
            win_rate = declines / total * 100
            avg_change = np.mean(changes)
            median_change = np.median(changes)
            
            results_table.append({
                'threshold': threshold,
                'forward_days': days,
                'tests': total,
                'declines': declines,
                'win_rate': win_rate,
                'avg_change': avg_change,
                'median_change': median_change
            })
            
            print(f"   {days}-day: Win Rate {win_rate:.1f}% ({declines}/{total}), "
                  f"Avg Change {avg_change:.1f}%, Median {median_change:.1f}%")

# Create results dataframe
df_results = pd.DataFrame(results_table)

# Summary
print("\n" + "=" * 80)
print("🏆 BEST OPPORTUNITIES (10-day forward)")
print("=" * 80)

best_10d = df_results[df_results['forward_days'] == 10].sort_values('win_rate', ascending=False)

print(f"\n{'HVP Threshold':<15} | {'Win Rate':<10} | {'Avg Change':<12} | {'Tests':<8}")
print("-" * 60)

for _, row in best_10d.iterrows():
    print(f"HVP >= {row['threshold']:>3.0f}%      | "
          f"{row['win_rate']:>7.1f}%  | "
          f"{row['avg_change']:>9.1f}%  | "
          f"{row['tests']:>5.0f}")

# Compare to VIX
print("\n" + "=" * 80)
print("📊 AAPL vs VIX COMPARISON")
print("=" * 80)

print("\nDownloading VIX for comparison...")
vix = yf.download('^VIX', period='5y', progress=False)

if isinstance(vix.columns, pd.MultiIndex):
    vix.columns = [col[0].lower() for col in vix.columns]
else:
    vix.columns = vix.columns.str.lower()

# Calculate VIX percentile
vix_ivp = []
for i in range(len(vix)):
    if i < lookback:
        vix_ivp.append(None)
    else:
        current = vix.iloc[i]['close']
        historical = vix.iloc[i-lookback:i]['close']
        percentile = (historical < current).sum() / len(historical) * 100
        vix_ivp.append(percentile)

vix['ivp'] = vix_ivp

# Test VIX mean reversion at same thresholds
vix_results = []

for threshold in [80, 90]:
    high_vix = vix[vix['ivp'] >= threshold]
    
    declines = 0
    total = 0
    
    for idx in high_vix.index:
        try:
            current = vix.loc[idx, 'close']
            future_idx = vix.index.get_loc(idx) + 10
            
            if future_idx < len(vix):
                future = vix.iloc[future_idx]['close']
                
                if future < current:
                    declines += 1
                total += 1
        except:
            pass
    
    if total > 0:
        vix_results.append({
            'threshold': threshold,
            'win_rate': declines / total * 100,
            'tests': total
        })

print(f"\n{'Asset':<8} | {'Threshold':<12} | {'Win Rate':<10} | {'Tests':<8}")
print("-" * 50)

# AAPL results
for _, row in best_10d.iterrows():
    if row['threshold'] in [80, 90]:
        print(f"AAPL    | HVP >= {row['threshold']:>2.0f}%  | "
              f"{row['win_rate']:>7.1f}%  | "
              f"{row['tests']:>5.0f}")

# VIX results
for result in vix_results:
    print(f"VIX     | IVP >= {result['threshold']:>2.0f}%  | "
          f"{result['win_rate']:>7.1f}%  | "
          f"{result['tests']:>5.0f}")

# Trading strategy simulation
print("\n" + "=" * 80)
print("💰 AAPL TRADING STRATEGY BACKTEST")
print("=" * 80)

print("""
Strategy: Sell AAPL premium when HVP > 80%
  • Entry: HVP > 80
  • Hold: 10 days or until HVP < 50
  • Profit if HV declines
""")

trades = []
in_trade = False
entry_date = None
entry_hv = None
entry_hvp = None

for i in range(len(aapl)):
    if aapl.iloc[i]['hvp'] is None:
        continue
    
    current_date = aapl.index[i]
    current_hv = aapl.iloc[i]['hv_20d']
    current_hvp = aapl.iloc[i]['hvp']
    
    # Entry signal
    if not in_trade and current_hvp > 80:
        in_trade = True
        entry_date = current_date
        entry_hv = current_hv
        entry_hvp = current_hvp
    
    # Exit conditions
    elif in_trade:
        days_in_trade = (current_date - entry_date).days
        
        # Exit if HVP < 50 or 10 days passed
        if current_hvp < 50 or days_in_trade >= 10:
            exit_date = current_date
            exit_hv = current_hv
            exit_hvp = current_hvp
            
            hv_change = (exit_hv - entry_hv) / entry_hv * 100
            
            # If HV declined, profitable (sold premium at high HV)
            profitable = hv_change < 0
            
            trades.append({
                'entry_date': entry_date,
                'entry_hv': entry_hv,
                'entry_hvp': entry_hvp,
                'exit_date': exit_date,
                'exit_hv': exit_hv,
                'exit_hvp': exit_hvp,
                'days_held': days_in_trade,
                'hv_change': hv_change,
                'profitable': profitable
            })
            
            in_trade = False

df_trades = pd.DataFrame(trades)

if len(df_trades) > 0:
    print(f"\n📊 Backtest Results:")
    print(f"   Total Trades: {len(df_trades)}")
    print(f"   Profitable: {df_trades['profitable'].sum()} ({df_trades['profitable'].mean()*100:.1f}%)")
    print(f"   Average HV Change: {df_trades['hv_change'].mean():.1f}%")
    print(f"   Average Days Held: {df_trades['days_held'].mean():.1f}")
    print(f"   Best Trade: {df_trades['hv_change'].min():.1f}% decline")
    print(f"   Worst Trade: {df_trades['hv_change'].max():.1f}% increase")
    
    # Show recent trades
    print(f"\n📅 Recent Trades (Last 10):")
    print(f"\n{'Entry Date':<12} | {'Entry HVP':<10} | {'HV Change':<12} | {'Days':<6} | {'Result':<10}")
    print("-" * 70)
    
    for _, trade in df_trades.tail(10).iterrows():
        result = "✅ WIN" if trade['profitable'] else "❌ LOSS"
        print(f"{trade['entry_date'].date()} | "
              f"{trade['entry_hvp']:>8.1f}% | "
              f"{trade['hv_change']:>9.1f}% | "
              f"{trade['days_held']:>4.0f}  | "
              f"{result}")

# Current signal
print("\n" + "=" * 80)
print("🎯 CURRENT AAPL SIGNAL")
print("=" * 80)

print(f"\nDate: {aapl.index[-1].date()}")
print(f"Price: ${aapl['close'].iloc[-1]:.2f}")
print(f"Historical Vol: {current_hv:.1f}%")
print(f"HV Percentile: {current_hvp:.1f}%")

if current_iv:
    print(f"Implied Vol: {current_iv*100:.1f}%")
    print(f"IV/HV Spread: {(current_iv*100 - current_hv):.1f}%")

print("\n🚦 SIGNAL:")
if current_hvp >= 80:
    print("   🔴 SELL SIGNAL - High HVP, sell AAPL premium")
    win_rate_80 = best_10d[best_10d['threshold'] == 80]['win_rate'].values[0] if len(best_10d[best_10d['threshold'] == 80]) > 0 else 0
    print(f"   Expected win rate: {win_rate_80:.1f}%")
elif current_hvp >= 70:
    print("   🟠 MODERATE SELL SIGNAL - Elevated HVP")
elif current_hvp <= 30:
    print("   🟢 BUY SIGNAL - Low HVP, buy AAPL options")
else:
    print("   ⚪ NEUTRAL - HVP in normal range")

# Summary
print("\n" + "=" * 80)
print("💡 KEY FINDINGS FOR AAPL")
print("=" * 80)

if len(df_results) > 0:
    avg_80_win = df_results[(df_results['threshold'] == 80) & (df_results['forward_days'] == 10)]['win_rate'].values
    
    if len(avg_80_win) > 0:
        print(f"""
1. AAPL Mean Reversion (HVP >= 80):
   • 10-day win rate: {avg_80_win[0]:.1f}%
   • Number of tests: {df_results[(df_results['threshold'] == 80) & (df_results['forward_days'] == 10)]['tests'].values[0]:.0f}
   
2. Comparison to VIX:
   • VIX IVP >= 80: ~71% win rate
   • AAPL HVP >= 80: {avg_80_win[0]:.1f}% win rate
   • Similarity: {"Strong" if abs(avg_80_win[0] - 71) < 10 else "Moderate"}
   
3. Trading Implications:
   {"✅" if avg_80_win[0] > 60 else "⚠️"} {"Tradeable edge exists" if avg_80_win[0] > 60 else "Weak edge"}
   • Sell AAPL premium when HVP > 80
   • Expected win rate: {avg_80_win[0]:.1f}%
   • Hold 10 days or exit at HVP < 50
   
4. Limitations:
   ⚠️  Using HV as proxy for IV (not perfect)
   ⚠️  Need real IV history for precise IVP
   ⚠️  DoltHub has real AAPL IV history (free)
   ⚠️  HV underestimates vol spikes (earnings, etc)
""")

print("\n" + "=" * 80)
print("✅ AAPL ANALYSIS COMPLETE")
print("=" * 80)

print("""
Next Steps:
1. If HVP > 80: Consider selling AAPL premium
2. Access DoltHub for real AAPL IV history
3. Recalculate with true IV (not HV proxy)
4. Compare earnings vs non-earnings periods
5. Test with real IV data for better accuracy

For Real IV Data:
  URL: https://www.dolthub.com/repositories/post-no-preference/options
  Query: SELECT date, symbol, AVG(iv) as avg_iv
         FROM option_chain
         WHERE symbol = 'AAPL'
         GROUP BY date
         ORDER BY date
""")
