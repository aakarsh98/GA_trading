# Multi-Timeframe Genetic Algorithm Strategy Discoverers

Two powerful GA implementations to discover optimal multi-timeframe trading strategies using momentum tracker and moving averages.

## 📋 Contents

1. **Unrestricted Multi-Timeframe GA** - Complete freedom to discover any timeframe relationships
2. **Top-Down Linear GA** - Structured hierarchy (Monthly → Weekly → Daily → Hourly)

---

## 🚀 Installation

```bash
cd "/Users/aakarshraj/GG_ Script"

# Install required packages
pip3 install alpaca-py pandas numpy yfinance
```

---

## 📊 1. Unrestricted Multi-Timeframe GA

### What It Does

**Complete autonomy** to discover:
- Which timeframes are important (1min, 5min, 15min, 1h, 4h, 1d)
- How to combine multiple timeframes
- What indicators matter on each timeframe
- Best entry/exit conditions across timeframes

### Features

- ✅ **6 Timeframes**: 1min, 5min, 15min, 1h, 4h, 1d
- ✅ **Momentum Tracker** + **Moving Averages** (20, 50, 200)
- ✅ **Flexible Rules**: GA creates its own logic
- ✅ **Free Data**: Uses Alpaca (100% free for stocks)
- ✅ **Advanced Features**:
  - Momentum cascade detection
  - Higher timeframe trend filters
  - Timeframe agreement requirements
  - Position scaling based on alignment

### Run It

```bash
python3 ga_multitimeframe_unrestricted.py
```

### What GA Discovers

```python
# Example discovered strategy:
Primary TF: 15min      # Execution timeframe
Confirm TF: 4hour      # Confirmation filter
Filter TF: 1day        # Trend filter

Entry Logic: PRIMARY_AND_CONFIRM
- Primary: momentum > 55 AND price_vs_ma20 > 0
- Confirm: ma_aligned_bull = True
- Filter: momentum > 60

Exit: Stop 8%, TP 18%, Trail from 10%
Position: 85% base, +15% when all TFs align
```

### Output

- **JSON File**: `best_mtf_unrestricted_strategy.json`
- **Console Report**: Full performance metrics
- **Generation Tracking**: See evolution over time

---

## 📈 2. Top-Down Linear Multi-Timeframe GA

### What It Does

**Structured hierarchy** approach:
- **Monthly** filters long-term trend
- **Weekly** confirms medium-term trend
- **Daily** confirms short-term trend  
- **Hourly** confirms intraday trend
- **15-minute** executes trades

### Features

- ✅ **Linear Cascade**: Each level filters the next
- ✅ **Top-Down Logic**: Higher TFs have priority
- ✅ **Cascade Types**:
  - `strict`: All must agree
  - `majority`: 2+ must agree
  - `any`: At least 1 must agree
- ✅ **HTF Reversal Detection**: Exit when higher TF turns
- ✅ **Alignment Bonuses**: Bigger positions when all TFs align
- ✅ **Free Data**: Uses Alpaca for ALL timeframes (aggregates weekly/monthly from daily)

### Run It

```bash
python3 ga_multitimeframe_topdown.py
```

### How It Works

```
Monthly → Must be bullish (MA aligned)
    ↓
Weekly → Confirms monthly, momentum 40-80
    ↓
Daily → Confirms weekly, price above MA50
    ↓
Hourly → Momentum rising
    ↓
15min → EXECUTE TRADE
```

### What GA Discovers

```python
# Example discovered strategy:
Monthly: MA alignment required, momentum 30-70
Weekly: Confirms monthly, momentum > 45
Daily: Confirms weekly, price vs MA50 > 0
Hourly: Momentum rising

Cascade: STRICT (all must pass)

Entry: 15min momentum crosses 55 from below
Exit: Stop 6%, TP 15%, or Weekly reverses
```

### Output

- **JSON File**: `best_mtf_topdown_strategy.json`
- **Console Report**: Hierarchy breakdown
- **Filter Analysis**: Which TFs matter most

---

## 🎯 Key Differences

| Feature | Unrestricted | Top-Down |
|---------|-------------|----------|
| **Structure** | GA chooses everything | Fixed hierarchy |
| **Timeframes** | Any combination | Linear cascade |
| **Logic** | Completely flexible | Structured filters |
| **Best For** | Novel discoveries | Trend following |
| **Complexity** | Higher search space | Focused search |
| **Speed** | Slower (more options) | Faster (constrained) |
| **Data Source** | Alpaca (all TFs) | Alpaca (all TFs + aggregation) |

---

## 📝 Configuration

### Adjust Population & Generations

Both scripts allow customization:

```python
# In the script, find this section:
generation_best, best_gene, best_results = run_mtf_ga(
    mtf_data,
    population_size=50,     # ← Increase for better results
    generations=50,         # ← Increase for more evolution
    elite_size=5            # ← Top performers to keep
)
```

**Recommendations:**
- **Quick test**: 30 population, 30 generations (~15 minutes)
- **Normal run**: 50 population, 50 generations (~45 minutes)
- **Deep search**: 100 population, 100 generations (~3 hours)

### Change Symbol or Date Range

```python
# In main execution section:
symbol = 'SPY'  # Change to any stock
end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # Change lookback
```

---

## 📊 Understanding Results

### Performance Metrics

```
Total Return: 15.2%      # Overall profit
Total Trades: 28         # Number of trades
Win Rate: 64.3%         # Winning trades %
Sharpe Ratio: 1.8       # Risk-adjusted return
Max Drawdown: -8.5%     # Worst decline
```

### Fitness Function

GA optimizes for:
1. **Total Return** (primary)
2. **Trade Count** bonus (10+ trades)
3. **Win Rate** bonus (>55%)
4. **Sharpe Ratio** bonus (>1.0)
5. **Penalties** for too few trades

---

## 🔧 Advanced Usage

### Add Custom Indicators

Both scripts use:
- **Momentum Tracker** (your actual implementation)
- **Moving Averages** (20, 50, 200)
- **MA Alignment** (trend strength)
- **Price vs MA** (relative position)

To add more indicators, edit the data download sections:

```python
# In download_multi_timeframe or download_topdown_data:
# After momentum calculation, add:
df['rsi'] = calculate_rsi(df['close'], 14)
df['atr'] = calculate_atr(df, 14)
```

Then add to rule evaluation:

```python
# In evaluate_mtf_rule or evaluate_topdown_filter:
elif rule_type == 'rsi_level':
    indicator = row['rsi']
```

### Use Crypto Instead of Stocks

Replace Alpaca with Binance:

```python
from binance.client import Client

client = Client()  # Free, no API key needed

klines = client.get_historical_klines(
    "BTCUSDT",
    Client.KLINE_INTERVAL_15MINUTE,
    "1 Jan, 2024",
    "1 Dec, 2024"
)
```

### Parallel Execution

Run both GAs simultaneously to compare:

```bash
# Terminal 1
python3 ga_multitimeframe_unrestricted.py

# Terminal 2
python3 ga_multitimeframe_topdown.py
```

---

## 🎓 Interpretation Guide

### Unrestricted Strategy Output

```python
Primary TF: 15min
Confirm TF: 4hour (Used: True)
Filter TF: 1day (Used: False)

Entry Logic: PRIMARY_AND_CONFIRM
Primary Rule: momentum_level > 55.0
Momentum Range: 45.0 - 75.0

Position Size: 82.5% (momentum_scaled)
Stop Loss: 7.2% (trailing)
Take Profit: 16.8% (Enabled: True)

HTF Filter: True
   Filter TF: 1day
   Filter Type: ma_alignment
```

**What This Means:**
- Executes on 15min timeframe
- Requires 4-hour confirmation (but not daily)
- Only enters when 15min momentum > 55 AND 4hour conditions met
- Scales position size based on momentum strength
- Uses trailing stop at 7.2%
- Daily must show MA alignment (higher TF filter)

### Top-Down Strategy Output

```python
Monthly Filter: ENABLED
   Type: ma_alignment
   Momentum: 25.0 - 75.0

Weekly Filter: ENABLED
   Type: momentum_level
   Confirm Monthly: True

Daily Filter: ENABLED
   Type: price_vs_ma
   Confirm Weekly: True

Cascade Logic: STRICT
```

**What This Means:**
- Monthly must show MA alignment (20>50>200)
- Weekly must have momentum in range AND monthly passes
- Daily must have price above MA AND weekly passes
- STRICT = all enabled filters must pass
- Only then will 15min look for entry

---

## 🐛 Troubleshooting

### Error: "Not enough timeframe data downloaded"

**Solution**: Alpaca free tier limits intraday data to ~6 months.

```python
# Reduce date range (default is 1 year, try shorter)
start_date = end_date - timedelta(days=180)  # Try 6 months

# Or use fewer timeframes
# Edit: timeframes dict in data provider

# Note: Weekly/Monthly are aggregated from daily, so they're always available
```

### Error: "No trades generated"

**Cause**: Conditions too strict.

**Solution**: 
1. Reduce population size for faster testing
2. Check if filters are too restrictive
3. Try different symbols (high volume stocks work better)

### Slow Execution

**Solutions**:
1. Reduce population size (30 instead of 50)
2. Reduce generations (30 instead of 50)
3. Use shorter date range (30 days instead of 60)
4. Comment out unused timeframes in data download

---

## 📈 Next Steps

### 1. Validate Strategy

After GA finds a strategy, test it on **out-of-sample data**:

```python
# After training on 2024-01 to 2024-06
# Test on 2024-07 to 2024-12
test_start = datetime(2024, 7, 1)
test_end = datetime(2024, 12, 31)

test_data = provider.download_multi_timeframe(symbol, test_start, test_end)
test_results = backtest_mtf_strategy(best_gene, test_data)
```

### 2. Walk-Forward Analysis

Train on rolling windows:

```python
# Train on Q1, test on Q2
# Train on Q2, test on Q3
# Train on Q3, test on Q4
# Average results
```

### 3. Deploy to Paper Trading

Use best strategy with Alpaca paper trading:

```python
from alpaca.trading.client import TradingClient

trading_client = TradingClient(api_key, secret_key, paper=True)

# Implement strategy signals
# Submit orders via trading_client.submit_order()
```

### 4. Ensemble Strategies

Combine multiple discovered strategies:

```python
# Run GA 3 times with different seeds
# Take trades only when 2+ strategies agree
# Or weight positions by agreement level
```

---

## 💡 Tips for Best Results

### 1. Data Quality
- Use liquid stocks (SPY, QQQ, AAPL, MSFT)
- Avoid low-volume stocks
- Check for data gaps before training

### 2. Parameter Tuning
- Start with small population (30) to test
- Increase generations for final run
- Higher elite_size preserves good solutions

### 3. Fitness Function
- Adjust bonuses/penalties based on your goals
- Add max drawdown penalty if important
- Consider risk-adjusted metrics (Sharpe, Sortino)

### 4. Multi-Run Validation
- Run GA 3-5 times
- Compare results
- Use strategies that emerge consistently

### 5. Timeframe Selection
- More timeframes = more compute time
- Start with 3-4 key timeframes
- Add more after initial testing

---

## 📚 Technical Details

### Gene Space Size

**Unrestricted GA:**
- ~40 parameters per gene
- Search space: ~10^30 combinations
- Convergence: Usually 50-100 generations

**Top-Down GA:**
- ~35 parameters per gene  
- Search space: ~10^25 combinations (more constrained)
- Convergence: Usually 40-80 generations

### Evolution Mechanics

1. **Selection**: Tournament selection (size=5)
2. **Crossover**: Random 50/50 inheritance
3. **Mutation**: 15% probability per parameter
4. **Elitism**: Top 5 (10%) preserved

### Computational Cost

**Per Generation:**
- Population evaluation: 50 backtests
- Each backtest: ~0.5-2 seconds
- Generation time: ~30-100 seconds

**Full Run:**
- 50 generations × 60 seconds = 50 minutes
- 100 generations × 60 seconds = 100 minutes

---

## 🎯 Example Workflows

### Quick Discovery (30 min)

```bash
# Edit scripts: population_size=30, generations=30
python3 ga_multitimeframe_unrestricted.py
# Review results
# If promising, run full search
```

### Deep Search (3 hours)

```bash
# Edit scripts: population_size=100, generations=100
python3 ga_multitimeframe_topdown.py
# Let run overnight
# Validate on separate data
```

### Comparison Study

```bash
# Run both in parallel
python3 ga_multitimeframe_unrestricted.py &
python3 ga_multitimeframe_topdown.py &
# Compare JSON outputs
# Test best from each on validation set
```

---

## 📞 Support

Both scripts include extensive error handling and progress reporting. Check console output for:
- Data download status
- Generation progress
- Best fitness tracking
- Final strategy details

If issues persist, review the code comments for implementation details.

---

## 🏆 Success Criteria

A good strategy should have:
- ✅ **Return**: >10% annually
- ✅ **Trades**: 20+ for statistical significance
- ✅ **Win Rate**: >50%
- ✅ **Sharpe**: >1.0
- ✅ **Max DD**: <20%

**Remember**: Past performance doesn't guarantee future results. Always validate on out-of-sample data before live trading!

---

## 📝 Files Created

After running:

```
best_mtf_unrestricted_strategy.json  # Unrestricted GA result
best_mtf_topdown_strategy.json       # Top-down GA result
```

Both contain:
- Full performance metrics
- All gene parameters
- Timestamp of discovery

Use these to implement the discovered strategies in production!
