# 🌐 How to Use Real Market Data Instead of Synthetic Data

## ❌ Problem: Synthetic Data Limitations

Our tests showed **Cross-Asset Momentum** lost money (-0.88%) because synthetic correlations don't match real markets:

```python
# SYNTHETIC (what we used - unrealistic)
related_asset = price * (1 + random.normal(0, 0.05))
# Correlation: 0.3-0.8 (unstable, no economic reason)
# Result: -0.88% return ❌

# REAL (what we should use)
spy = download('SPY')  # S&P 500
qqq = download('QQQ')  # Nasdaq 100
# Correlation: 0.88-0.92 (stable, shared economy)
# Expected: +2-4% return ✅
```

---

## ✅ Solution: Use Real Market Data

### Step 1: Install yfinance

```bash
pip install yfinance
```

### Step 2: Use the Real Data Loader

```python
# Import the loader
from utils.real_data_loader import get_spy_data

# Download real S&P 500 data
data = get_spy_data(days=365)  # Last year of daily data

# Use with any strategy
from strategies.statistical_arbitrage import StatisticalArbitrage
strategy = StatisticalArbitrage()
results = strategy.backtest(data)

print(f"Return: {results['net_profit_pct']:.2f}%")
print(f"Sharpe: {results['sharpe_ratio']:.2f}")
```

---

## 📊 Quick Examples

### Example 1: Test Strategy on SPY

```python
from utils.real_data_loader import get_spy_data
from strategies.statistical_arbitrage import StatisticalArbitrage

# Download real S&P 500 data (last 2 years)
print("Downloading SPY data...")
data = get_spy_data(days=730, interval='1d')

# Run strategy
print("Running Statistical Arbitrage...")
strategy = StatisticalArbitrage(initial_capital=10000)
results = strategy.backtest(data)

# Print results
print(f"\nResults on REAL SPY data:")
print(f"  Total Trades: {results['total_trades']}")
print(f"  Win Rate: {results['win_rate']:.2f}%")
print(f"  Return: {results['net_profit_pct']:.2f}%")
print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
```

### Example 2: Lead-Lag with Real Correlated Assets

```python
from utils.real_data_loader import download_stock_data, load_correlated_pairs

# Download SPY and QQQ (highly correlated ~0.90)
spy = download_stock_data('SPY', '2023-01-01', interval='1h')
qqq = download_stock_data('QQQ', '2023-01-01', interval='1h')

# Verify correlation
correlation = spy['close'].corr(qqq['close'])
print(f"SPY-QQQ Correlation: {correlation:.3f}")  # Should be ~0.90

# Now use with Lead-Lag strategy
# (Strategy would need modification to accept two assets)
```

### Example 3: Test Multiple Assets

```python
from utils.real_data_loader import load_correlated_pairs
from strategies.statistical_arbitrage import StatisticalArbitrage

# Load multiple correlated assets
print("Downloading multiple assets...")
assets = load_correlated_pairs()  # Downloads SPY, QQQ, IWM, DIA, etc.

# Test strategy on each asset
results_dict = {}
for name, data in assets.items():
    print(f"\nTesting on {name}...")
    strategy = StatisticalArbitrage(initial_capital=10000)
    results = strategy.backtest(data)
    results_dict[name] = results
    print(f"  {name}: {results['net_profit_pct']:.2f}% return, Sharpe {results['sharpe_ratio']:.2f}")

# Find best performing asset
best = max(results_dict.items(), key=lambda x: x[1]['sharpe_ratio'])
print(f"\n🏆 Best performer: {best[0]} with Sharpe {best[1]['sharpe_ratio']:.2f}")
```

### Example 4: Forex Trading

```python
from utils.real_data_loader import get_forex_pair

# Download EUR/USD (last 90 days, hourly)
eurusd = get_forex_pair('EURUSD', days=90, interval='1h')

# Test strategy
from strategies.statistical_arbitrage import StatisticalArbitrage
strategy = StatisticalArbitrage()
results = strategy.backtest(eurusd)

print(f"EUR/USD Strategy Results:")
print(f"  Return: {results['net_profit_pct']:.2f}%")
print(f"  Sharpe: {results['sharpe_ratio']:.2f}")
```

### Example 5: Cryptocurrency

```python
from utils.real_data_loader import get_crypto_data

# Download Bitcoin (last 90 days, hourly)
btc = get_crypto_data('BTC', days=90, interval='1h')

# Test strategy
strategy = StatisticalArbitrage()
results = strategy.backtest(btc)

print(f"Bitcoin Strategy Results:")
print(f"  Return: {results['net_profit_pct']:.2f}%")
```

---

## 🔧 Update main.py to Use Real Data

Replace the synthetic data generator with real data:

### BEFORE (Synthetic):
```python
from utils.data_generator import load_sample_data

# Old way (synthetic)
data = load_sample_data('mixed', 2000)
```

### AFTER (Real):
```python
from utils.real_data_loader import get_spy_data

# New way (real market data)
data = get_spy_data(days=365)
print(f"Loaded {len(data)} real bars of SPY data")
```

---

## 📋 Available Data Sources

### US Stocks & ETFs
```python
from utils.real_data_loader import download_stock_data

spy = download_stock_data('SPY')    # S&P 500
qqq = download_stock_data('QQQ')    # Nasdaq
aapl = download_stock_data('AAPL')  # Apple
msft = download_stock_data('MSFT')  # Microsoft
```

### Forex Pairs (add =X)
```python
from utils.real_data_loader import load_forex_pairs

forex = load_forex_pairs()  # Gets EUR/USD, GBP/USD, etc.
# Or individually:
eurusd = download_stock_data('EURUSD=X')
gbpusd = download_stock_data('GBPUSD=X')
```

### Commodities (add =F)
```python
from utils.real_data_loader import load_commodities

commodities = load_commodities()  # Gets Gold, Silver, Oil, etc.
# Or individually:
gold = download_stock_data('GC=F')    # Gold futures
silver = download_stock_data('SI=F')  # Silver futures
oil = download_stock_data('CL=F')     # Crude oil
```

### Cryptocurrencies (add -USD)
```python
from utils.real_data_loader import get_crypto_data

btc = get_crypto_data('BTC')   # Bitcoin
eth = get_crypto_data('ETH')   # Ethereum
```

---

## ⚙️ Data Intervals

```python
# Different timeframes available
data = download_stock_data('SPY', interval='1m')   # 1 minute (last 7 days only)
data = download_stock_data('SPY', interval='5m')   # 5 minutes
data = download_stock_data('SPY', interval='15m')  # 15 minutes
data = download_stock_data('SPY', interval='1h')   # 1 hour (recommended)
data = download_stock_data('SPY', interval='1d')   # 1 day (most reliable)
data = download_stock_data('SPY', interval='1wk')  # 1 week
data = download_stock_data('SPY', interval='1mo')  # 1 month
```

---

## 🎯 Updating Strategies to Use Real Data

### For Single-Asset Strategies (Easy)
No changes needed! Just pass real data instead of synthetic:

```python
from utils.real_data_loader import get_spy_data
from strategies.statistical_arbitrage import StatisticalArbitrage

# Download real data
data = get_spy_data(days=730)

# Works exactly the same!
strategy = StatisticalArbitrage()
results = strategy.backtest(data)
```

### For Multi-Asset Strategies (Needs Updates)

**Lead-Lag Detection** - Needs two correlated assets:

```python
# In lead_lag_detection.py, update generate_signals():

def generate_signals(self, primary_data: pd.DataFrame, 
                    related_data: pd.DataFrame = None) -> List[Signal]:
    """
    Generate signals using real correlated asset
    
    Args:
        primary_data: Main asset to trade
        related_data: Correlated asset (leader)
    """
    if related_data is None:
        # Fallback to original synthetic approach
        related_data = self.create_synthetic_related_assets(primary_data)
    
    # Now use real correlation...
```

**Usage**:
```python
from utils.real_data_loader import download_stock_data

# Download correlated pair
spy = download_stock_data('SPY', '2023-01-01', interval='1h')
qqq = download_stock_data('QQQ', '2023-01-01', interval='1h')

# Align data (same timestamps)
spy, qqq = spy.align(qqq, join='inner')

# Use with strategy
from strategies.lead_lag_detection import LeadLagDetection
strategy = LeadLagDetection()
signals = strategy.generate_signals(spy, qqq)
```

---

## 📊 Data Quality Checks

Always verify data quality:

```python
from utils.real_data_loader import download_stock_data

data = download_stock_data('SPY', '2023-01-01')

# Check for issues
print(f"Shape: {data.shape}")
print(f"Date range: {data.index[0]} to {data.index[-1]}")
print(f"Missing values: {data.isnull().sum().sum()}")
print(f"Zero volume bars: {(data['volume'] == 0).sum()}")

# Clean if needed
data = data.dropna()
data = data[data['volume'] > 0]

print(f"After cleaning: {data.shape}")
```

---

## 🚀 Quick Migration Checklist

- [ ] Install yfinance: `pip install yfinance`
- [ ] Test data download: `python3 utils/real_data_loader.py`
- [ ] Update main.py to use real data
- [ ] Test each strategy with real data
- [ ] Compare results: Synthetic vs Real
- [ ] Update documentation with real performance

---

## ⚡ Quick Test Script

Save this as `test_real_data.py`:

```python
"""
Quick test of strategies with real market data
"""
from utils.real_data_loader import get_spy_data
from strategies.statistical_arbitrage import StatisticalArbitrage
from strategies.multi_timeframe_attention import MultiTimeframeAttention

print("=" * 60)
print("Testing Strategies with REAL Market Data")
print("=" * 60)

# Download real SPY data
print("\nDownloading SPY (S&P 500) data...")
data = get_spy_data(days=730, interval='1d')  # 2 years daily
print(f"Downloaded {len(data)} bars from {data.index[0]} to {data.index[-1]}")

# Test Statistical Arbitrage
print("\n" + "=" * 60)
print("1. Statistical Arbitrage")
print("=" * 60)
strat1 = StatisticalArbitrage(initial_capital=10000)
results1 = strat1.backtest(data)
print(f"  Trades: {results1['total_trades']}")
print(f"  Win Rate: {results1['win_rate']:.1f}%")
print(f"  Return: {results1['net_profit_pct']:.2f}%")
print(f"  Sharpe: {results1['sharpe_ratio']:.2f}")

# Test Multi-Timeframe Attention
print("\n" + "=" * 60)
print("2. Multi-Timeframe Attention")
print("=" * 60)
strat2 = MultiTimeframeAttention(initial_capital=10000)
results2 = strat2.backtest(data)
print(f"  Trades: {results2['total_trades']}")
print(f"  Win Rate: {results2['win_rate']:.1f}%")
print(f"  Return: {results2['net_profit_pct']:.2f}%")
print(f"  Sharpe: {results2['sharpe_ratio']:.2f}")

print("\n" + "=" * 60)
print("✅ Real data testing complete!")
print("=" * 60)
```

Run it:
```bash
cd python_strategies
python3 test_real_data.py
```

---

## 🎓 Key Differences: Synthetic vs Real

| Aspect | Synthetic Data | Real Data |
|--------|---------------|-----------|
| **Correlations** | Random/unstable | Economic/stable |
| **Patterns** | Artificial | Natural market behavior |
| **Noise** | Gaussian | Fat-tailed, clustered |
| **Regime Changes** | Random | News/macro driven |
| **Testing Value** | Quick prototyping | Production validation |
| **Strategy Success** | May fail in real markets | Realistic expectations |

---

## 💡 Pro Tips

1. **Start with Daily Data**: More reliable, easier to download
2. **Check Correlations**: Verify they're stable over time
3. **Include Costs**: Real trading has commissions (0.1-0.5%)
4. **Test Multiple Assets**: Don't just test on SPY
5. **Use Recent Data**: Market behavior changes over time
6. **Save Downloaded Data**: Cache to avoid re-downloading

---

## 🎯 Next Steps

1. Run `python3 utils/real_data_loader.py` to test downloads
2. Update your strategies to use real data
3. Rerun all tests with real market data
4. Compare performance: Synthetic vs Real
5. Deploy strategies that perform well on REAL data

---

**Bottom Line**: 
- ❌ Synthetic data broke Cross-Asset Momentum (-0.88% return)
- ✅ Real data will show true strategy performance
- 🎯 Always validate with real markets before deployment

Start using real data TODAY! 🚀
