import yfinance as yf
import pandas as pd
import numpy as np

# Download SPY data for different periods
print("=" * 80)
print("  BUY-AND-HOLD BENCHMARK ANALYSIS")
print("=" * 80)

# Full 25 years (2000-2024)
data = yf.download('SPY', start='2000-01-01', end='2024-12-31', progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = [col[0].lower() for col in data.columns]
else:
    data.columns = data.columns.str.lower()

start_price = float(data['close'].iloc[0])
end_price = float(data['close'].iloc[-1])
total_return = ((end_price / start_price) - 1) * 100
annual_return = total_return / 25

print(f"\n📊 SPY BUY-AND-HOLD (2000-2024, 25 years):")
print(f"   Start Price: ${start_price:.2f}")
print(f"   End Price:   ${end_price:.2f}")
print(f"   Total Return: +{total_return:.2f}%")
print(f"   Annual Return: +{annual_return:.2f}%")
print(f"   $10,000 becomes: ${10000 * (1 + total_return/100):,.2f}")

# 5-year rolling periods
print("\n📊 5-YEAR ROLLING PERIODS (Buy-and-Hold):")
periods = [(2000, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2024)]

bh_returns = []
for start, end in periods:
    data_period = yf.download('SPY', start=f'{start}-01-01', end=f'{end}-12-31', progress=False)
    if isinstance(data_period.columns, pd.MultiIndex):
        data_period.columns = [col[0].lower() for col in data_period.columns]
    else:
        data_period.columns = data_period.columns.str.lower()
    
    p_start = float(data_period['close'].iloc[0])
    p_end = float(data_period['close'].iloc[-1])
    p_return = ((p_end / p_start) - 1) * 100
    p_annual = p_return / 5
    bh_returns.append(p_return)
    
    print(f"   {start}-{end}: +{p_return:6.2f}% total (+{p_annual:5.2f}% annual)")

avg_bh = np.mean(bh_returns)
print(f"\n   Average 5-year: +{avg_bh:.2f}%")

# Recent periods
print("\n📊 SPECIFIC PERIODS:")

# 2000-2015 (training period)
data_train = yf.download('SPY', start='2000-01-01', end='2015-12-31', progress=False)
if isinstance(data_train.columns, pd.MultiIndex):
    data_train.columns = [col[0].lower() for col in data_train.columns]
else:
    data_train.columns = data_train.columns.str.lower()
train_return = ((float(data_train['close'].iloc[-1]) / float(data_train['close'].iloc[0])) - 1) * 100
print(f"   2000-2015 (15y): +{train_return:.2f}% (+{train_return/15:.2f}% annual)")

# 2016-2020 (validation)
data_val = yf.download('SPY', start='2016-01-01', end='2020-12-31', progress=False)
if isinstance(data_val.columns, pd.MultiIndex):
    data_val.columns = [col[0].lower() for col in data_val.columns]
else:
    data_val.columns = data_val.columns.str.lower()
val_return = ((float(data_val['close'].iloc[-1]) / float(data_val['close'].iloc[0])) - 1) * 100
print(f"   2016-2020 (5y):  +{val_return:.2f}% (+{val_return/5:.2f}% annual)")

# 2021-2024 (test)
data_test = yf.download('SPY', start='2021-01-01', end='2024-12-31', progress=False)
if isinstance(data_test.columns, pd.MultiIndex):
    data_test.columns = [col[0].lower() for col in data_test.columns]
else:
    data_test.columns = data_test.columns.str.lower()
test_return = ((float(data_test['close'].iloc[-1]) / float(data_test['close'].iloc[0])) - 1) * 100
print(f"   2021-2024 (4y):  +{test_return:.2f}% (+{test_return/4:.2f}% annual)")

# 2024 only
data_2024 = yf.download('SPY', start='2024-01-01', end='2024-12-31', progress=False)
if isinstance(data_2024.columns, pd.MultiIndex):
    data_2024.columns = [col[0].lower() for col in data_2024.columns]
else:
    data_2024.columns = data_2024.columns.str.lower()
return_2024 = ((float(data_2024['close'].iloc[-1]) / float(data_2024['close'].iloc[0])) - 1) * 100
print(f"   2024 (1y):       +{return_2024:.2f}%")

# 2000-2020 for original GA
data_0020 = yf.download('SPY', start='2000-01-01', end='2020-12-31', progress=False)
if isinstance(data_0020.columns, pd.MultiIndex):
    data_0020.columns = [col[0].lower() for col in data_0020.columns]
else:
    data_0020.columns = data_0020.columns.str.lower()
bh_0020 = ((float(data_0020['close'].iloc[-1]) / float(data_0020['close'].iloc[0])) - 1) * 100

print("\n" + "=" * 80)
print("  GA STRATEGIES vs BUY-AND-HOLD COMPARISON")
print("=" * 80)

print("\n❌ Original Long-term GA:")
print(f"   Training (2000-2020): +2520.88% (GA) vs +{bh_0020:.2f}% (B&H)")
print(f"   GA appears better but had -99% in most years (overfitting!)")
print(f"   Out-of-sample (2021-2025): -96.85% (GA) vs +{test_return:.2f}% (B&H)")
print(f"   Verdict: FAILED - Severe overfitting")

print("\n❌ Robust GA:")
print(f"   Training (2000-2015): +84.41% (GA) vs +{train_return:.2f}% (B&H)")
print(f"   Validation (2016-2020): +45.91% (GA) vs +{val_return:.2f}% (B&H)")
print(f"   Test (2021-2024): -63.50% (GA) vs +{test_return:.2f}% (B&H)")
print(f"   Verdict: FAILED - Underperforms in all periods")

print("\n❌ Ultra-Robust GA (5-year periods):")
ga_returns = [5.97, 13.47, 24.03, 12.59, -16.40]
for i, (start, end) in enumerate(periods):
    print(f"   {start}-{end}: +{ga_returns[i]:6.2f}% (GA) vs +{bh_returns[i]:6.2f}% (B&H) - {'WIN' if ga_returns[i] > bh_returns[i] else 'LOSE'}")
print(f"   Average: +{np.mean(ga_returns):.2f}% (GA) vs +{avg_bh:.2f}% (B&H)")
print(f"   Verdict: FAILED - Loses in 4 out of 5 periods")

print("\n" + "=" * 80)
print("  💡 ROOT CAUSE ANALYSIS")
print("=" * 80)

print("\n🔍 Why GA Strategies Fail:")
print("   1. FITNESS FUNCTION doesn't compare to buy-and-hold")
print("   2. GA optimizes for Sharpe/Win Rate, not total return")
print("   3. Conservative position sizing (40-70%) caps upside")
print("   4. Frequent trading (68-180 trades) → transaction costs")
print("   5. Market timing is HARD - missing bull runs hurts")
print("   6. Stop losses lock in losses during volatility")

print("\n✅ What We Need:")
print("   1. Fitness = Strategy Return - Buy&Hold Return (RELATIVE)")
print("   2. Higher position sizing when in market")
print("   3. Fewer trades (reduce costs)")
print("   4. Catch major trends (not exit too early)")
print("   5. Accept that beating buy-and-hold is very difficult")

print("\n💰 REALITY CHECK:")
print(f"   Buy-and-hold SPY (2000-2024): +{total_return:.2f}%")
print(f"   This is +{annual_return:.2f}% annualized")
print(f"   $10,000 → ${10000 * (1 + total_return/100):,.2f}")
print(f"   Very hard to beat with timing strategies!")
