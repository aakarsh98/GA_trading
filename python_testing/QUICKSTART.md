# Quick Start Guide

Get started with the Trading Strategy Testing Suite in 5 minutes.

## 🚀 Installation

```bash
cd "GG_ Script/python_testing"
pip install -r requirements.txt
```

## ⚡ Quick Test

Run the comprehensive test to verify everything works:

```bash
cd "GG_ Script/python_testing"
PYTHONPATH=$(pwd) python3 test_all_features.py
```

You should see all 6 tests pass with detailed output!

## 📖 Basic Usage

### 1. Fetch Market Data

```python
from data.collector import DataCollector

collector = DataCollector()

# Fetch hourly BTC data for 1 month
data = collector.fetch_data('BTC-USD', timeframe='1h', period='1mo')

# Fetch daily data for multiple assets
symbols = ['BTC-USD', 'ETH-USD', 'SPY']
data_dict = collector.fetch_multiple(symbols, timeframe='1d', period='3mo')
```

**Supported Assets:**
- Crypto: BTC-USD, ETH-USD, BNB-USD, etc.
- Stocks: SPY, QQQ, AAPL, MSFT, TSLA, etc.
- Forex: EURUSD=X, GBPUSD=X, USDJPY=X, etc.
- Commodities: GC=F (Gold), CL=F (Oil), SI=F (Silver)

**Supported Timeframes:**
- 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1wk, 1mo

### 2. Calculate Momentum

```python
from indicators.momentum_tracker import MomentumTracker

mt = MomentumTracker(length=7, threshold=2.0)
momentum = mt.calculate(data)

# Get current signal
current = mt.get_current_signal(data)
print(f"Signal: {current['signal_name']} ({current['color']})")
print(f"Momentum: {current['momentum']:.2f}")
print(f"Strength: {current['strength']:.2f}x threshold")
```

### 3. Add Research Indicators

```python
from indicators.survival_analysis import SurvivalAnalysisFilter
from indicators.hmm_regime import HMMRegimeDetector
from indicators.edge_scoring import EdgeScoringSystem

# Survival analysis (35-45% Sharpe improvement)
saf = SurvivalAnalysisFilter()
survival = saf.calculate(momentum)

# HMM regime detection (40-60% improvement)
hmm = HMMRegimeDetector()
regime = hmm.calculate(data, momentum)

# Composite edge scoring
edge_system = EdgeScoringSystem()
edge = edge_system.calculate(data, momentum, survival, regime)

# Get trading decision
current_edge = edge['CompositeEdge'].iloc[-1]
decision = edge_system.get_trading_decision(current_edge)
print(f"Edge: {current_edge:.3f} - {decision['decision']}")
```

### 4. Backtest the Strategy

```python
from strategy.backtest_engine import BacktestEngine
from indicators.utils import atr

# Calculate ATR for stop losses
atr_values = atr(data, 14)

# Create backtest engine
engine = BacktestEngine(
    initial_capital=10000,
    risk_percent=1.0,
    commission_pct=0.1,
    atr_stop_multiplier=2.0
)

# Run backtest
results = engine.run(data, momentum, atr_values, edge['CompositeEdge'])

# Print results
engine.print_results(results)
```

## 📊 Running Individual Tests

### Test Momentum Tracker Only

```bash
PYTHONPATH=$(pwd) python3 indicators/momentum_tracker.py
```

### Test Survival Analysis

```bash
PYTHONPATH=$(pwd) python3 indicators/survival_analysis.py
```

### Test HMM Regime Detection

```bash
PYTHONPATH=$(pwd) python3 indicators/hmm_regime.py
```

### Test Edge Scoring

```bash
PYTHONPATH=$(pwd) python3 indicators/edge_scoring.py
```

### Test Backtesting Engine

```bash
PYTHONPATH=$(pwd) python3 strategy/backtest_engine.py
```

## 🎯 Common Workflows

### Workflow 1: Test a Single Asset

```python
# 1. Fetch data
data = collector.fetch_data('BTC-USD', timeframe='1h', period='3mo')

# 2. Calculate all indicators
momentum = mt.calculate(data)
survival = saf.calculate(momentum)
regime = hmm.calculate(data, momentum)
edge = edge_system.calculate(data, momentum, survival, regime)

# 3. Backtest
atr_values = atr(data, 14)
results = engine.run(data, momentum, atr_values, edge['CompositeEdge'])

# 4. Analyze
engine.print_results(results)
```

### Workflow 2: Compare Multiple Assets

```python
assets = ['BTC-USD', 'ETH-USD', 'SPY']
results_comparison = {}

for asset in assets:
    data = collector.fetch_data(asset, timeframe='1h', period='3mo')
    
    # Calculate indicators
    momentum = mt.calculate(data)
    # ... (calculate other indicators)
    
    # Backtest
    result = engine.run(data, momentum, atr_values, edge['CompositeEdge'])
    results_comparison[asset] = {
        'return': result['ReturnPct'],
        'sharpe': result['SharpeRatio'],
        'win_rate': result['WinRate']
    }

# Print comparison
for asset, metrics in results_comparison.items():
    print(f"{asset}: Return={metrics['return']:.2f}%, Sharpe={metrics['sharpe']:.2f}")
```

### Workflow 3: Parameter Optimization

```python
thresholds = [1.0, 1.5, 2.0, 2.5, 3.0]
best_return = -float('inf')
best_params = None

for threshold in thresholds:
    mt = MomentumTracker(threshold=threshold)
    momentum = mt.calculate(data)
    
    # Calculate edge and backtest
    # ... (full calculation)
    
    result = engine.run(data, momentum, atr_values, edge['CompositeEdge'])
    
    if result['ReturnPct'] > best_return:
        best_return = result['ReturnPct']
        best_params = {'threshold': threshold}

print(f"Best threshold: {best_params['threshold']}")
print(f"Best return: {best_return:.2f}%")
```

## 📈 Understanding the Output

### Momentum Signals
- **Bullish (Blue)**: Momentum above equilibrium - consider long positions
- **Bearish (Red)**: Momentum below equilibrium - consider short positions
- **Neutral (Yellow)**: Within equilibrium zone - wait for clearer signal

### Edge Scores
- **Strong (>0.8)**: High confidence - trade aggressively (1.4x size)
- **Medium (0.6-0.8)**: Good confidence - trade normally (1.0x size)
- **Weak (<0.6)**: Low confidence - reduce size or avoid (0.7x size)

### Backtest Results
- **Win Rate**: 45-55% is realistic and good
- **Profit Factor**: >1.5 is excellent, >1.2 is good
- **Sharpe Ratio**: >1.0 is excellent, >0.5 is acceptable
- **Max Drawdown**: <20% is good, <30% is acceptable

## ⚙️ Customization

### Adjust Momentum Sensitivity

```python
# More sensitive (more signals)
mt = MomentumTracker(length=7, threshold=1.0)

# Less sensitive (fewer signals)
mt = MomentumTracker(length=7, threshold=3.0)
```

### Adjust Risk Management

```python
# Conservative
engine = BacktestEngine(
    initial_capital=10000,
    risk_percent=0.5,  # Only 0.5% per trade
    atr_stop_multiplier=2.5  # Wider stops
)

# Aggressive
engine = BacktestEngine(
    initial_capital=10000,
    risk_percent=2.0,  # 2% per trade
    atr_stop_multiplier=1.5  # Tighter stops
)
```

### Adjust Survival Analysis

```python
# Faster decay (more conservative)
saf = SurvivalAnalysisFilter(hazard_multiplier=0.2)

# Slower decay (less conservative)
saf = SurvivalAnalysisFilter(hazard_multiplier=0.05)
```

## 🐛 Troubleshooting

### Import Errors
Make sure to set PYTHONPATH:
```bash
export PYTHONPATH=/Users/aakarshraj/GG_\ Script/python_testing
# or
PYTHONPATH=$(pwd) python3 your_script.py
```

### Data Fetch Fails
- Check internet connection
- Verify symbol format (BTC-USD not BTCUSD)
- Some symbols have limited historical data
- Use `use_cache=False` to force fresh data

### Poor Backtest Results
- Try different timeframes
- Test on different assets
- Optimize parameters
- Check if market was trending or ranging
- Verify data quality (enough bars, no gaps)

## 📚 Next Steps

1. **Read the full documentation**: `docs/INDICATORS_EXPLAINED.md`
2. **Understand each indicator**: Run individual test scripts
3. **Experiment with parameters**: Find what works for your style
4. **Test multiple assets**: Different assets behave differently
5. **Keep a trading journal**: Track your learning and improvements

## 💡 Tips for Success

1. **Start Simple**: Test momentum tracker alone first
2. **Add Complexity Gradually**: Add one indicator at a time
3. **Understand the Math**: Read how each indicator works
4. **Be Realistic**: 50% win rate with 2:1 RR is excellent
5. **Paper Trade First**: Test thoroughly before risking real money
6. **Focus on Process**: Good process leads to good results
7. **Stay Disciplined**: Follow your rules consistently

## 🆘 Getting Help

If you encounter issues:

1. Check the error message carefully
2. Verify all dependencies are installed
3. Make sure PYTHONPATH is set correctly
4. Review the documentation
5. Test with the demo scripts first
6. Try a simpler example to isolate the issue

## 📞 Support

For questions about:
- **Indicators**: See `docs/INDICATORS_EXPLAINED.md`
- **Usage**: See examples in each module's `if __name__ == '__main__'` section
- **Research**: See original TradingView strategy documentation

---

**Happy Trading! 🚀📈**

Remember: This is a testing framework to help you learn and improve. Always practice proper risk management and never trade with money you can't afford to lose.
