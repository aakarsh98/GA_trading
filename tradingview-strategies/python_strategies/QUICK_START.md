# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install numpy pandas scipy
```

### 2. Run Tests
```bash
cd python_strategies

# Quick test (500 bars, ~30 seconds)
python main.py --mode quick

# Full test (multiple conditions, ~2 minutes)
python main.py --mode full

# Single strategy test
python main.py --mode single --strategy arbitrage --bars 2000
```

### 3. Available Strategies
- `survival` - Survival Analysis Filter
- `leadlag` - Lead-Lag Detection
- `attention` - Multi-Timeframe Attention
- `hmm` - Hidden Markov Models
- `arbitrage` - Statistical Arbitrage ⭐
- `edge` - Real-Time Edge Scoring
- `meta` - Meta-Reinforcement Learning
- `crossasset` - Cross-Asset Momentum
- `llm` - LLM-Inspired Features

⭐ = Top performing strategies

## 📊 Best Strategies to Start With

### 1. Statistical Arbitrage
```python
from strategies.statistical_arbitrage import StatisticalArbitrage
from utils.data_generator import load_sample_data

data = load_sample_data('mixed', 2000)
strategy = StatisticalArbitrage(initial_capital=10000)
results = strategy.backtest(data)
print(results)
```

**Performance**: 2.20 Sharpe, 0.85% return, 49.45% win rate

### 2. Multi-Timeframe Attention
```python
from strategies.multi_timeframe_attention import MultiTimeframeAttention

strategy = MultiTimeframeAttention(initial_capital=10000)
results = strategy.backtest(data)
```

**Performance**: 3.35 Sharpe, 0.10% return, 50% win rate

### 3. Meta-Reinforcement Learning
```python
from strategies.meta_reinforcement_learning import MetaReinforcementLearning

strategy = MetaReinforcementLearning(initial_capital=10000)
results = strategy.backtest(data)
```

**Performance**: 0.70 Sharpe, 0.40% return, 213 trades

## 🔧 Using Real Data

Replace synthetic data with your own:

```python
import pandas as pd

# Load your CSV data
data = pd.read_csv('your_data.csv', parse_dates=['timestamp'])
data.set_index('timestamp', inplace=True)

# Required columns: open, high, low, close, volume
# Run strategy
strategy = StatisticalArbitrage()
results = strategy.backtest(data)
```

## 📈 Combining Strategies

```python
from tests.test_strategies import StrategyTester

tester = StrategyTester(initial_capital=10000)

# Test multiple strategies
strategies = [
    StatisticalArbitrage,
    MultiTimeframeAttention,
    MetaReinforcementLearning
]

for StrategyClass in strategies:
    result = tester.test_strategy(StrategyClass, data)
    print(f"{result['strategy_name']}: {result['sharpe_ratio']:.2f} Sharpe")
```

## ⚙️ Customizing Parameters

```python
strategy = StatisticalArbitrage(
    initial_capital=10000,
    zscore_entry=2.0,        # Entry threshold
    zscore_exit=0.5,         # Exit threshold
    lookback_period=20,      # Calculation window
    risk_per_trade=0.01      # 1% risk per trade
)
```

## 📊 Analyzing Results

```python
results = strategy.backtest(data)

print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")
print(f"Final Capital: ${results['final_capital']:,.2f}")
```

## 🎯 Market-Specific Testing

```python
from utils.data_generator import generate_trending_data, generate_volatile_data

# Test on trending markets
trending_data = generate_trending_data(2000, 'strong_up')
results_trending = strategy.backtest(trending_data)

# Test on volatile markets
volatile_data = generate_volatile_data(2000, 'high')
results_volatile = strategy.backtest(volatile_data)
```

## 🔍 Debugging and Analysis

```python
# Access individual trades
for trade in strategy.trades:
    if trade.exit_time:
        print(f"Entry: {trade.entry_price}, Exit: {trade.exit_price}, PnL: {trade.pnl}")

# Access signals
for signal in strategy.signals:
    print(f"{signal.timestamp}: {signal.signal_type} @ {signal.price} (confidence: {signal.confidence})")
```

## 📝 Performance Tips

1. **Start with tested strategies**: Statistical Arbitrage and Multi-Timeframe Attention
2. **Use sufficient data**: At least 1000 bars for meaningful results
3. **Test multiple conditions**: Trending, ranging, volatile markets
4. **Parameter optimization**: Grid search for best parameters
5. **Risk management**: Never risk more than 2% per trade
6. **Monitor drawdowns**: Exit if strategy exceeds historical max drawdown by 50%

## ⚠️ Common Issues

### No Trades Generated
- **Cause**: Entry criteria too strict
- **Fix**: Lower confidence thresholds or adjust parameters

### Poor Performance
- **Cause**: Strategy not suited for market condition
- **Fix**: Use regime-adaptive strategies or ensemble approach

### High Drawdowns
- **Cause**: Position sizing too aggressive
- **Fix**: Reduce risk_per_trade parameter

## 📚 Further Reading

- `README.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Implementation details and results
- Individual strategy files - Algorithm explanations

## 🆘 Support

Check these files for detailed information:
- Strategy implementations: `strategies/*.py`
- Technical indicators: `utils/indicators.py`
- Testing framework: `tests/test_strategies.py`
- Base classes: `utils/base_strategy.py`

---

**Ready to trade?** Start with Statistical Arbitrage or Multi-Timeframe Attention strategies!
