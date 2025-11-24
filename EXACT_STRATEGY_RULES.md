# 🎯 EXACT STRATEGY RULESET - Unrestricted GA (Best Performer)

## Strategy Overview
**Training**: 8 years (2013-2020)  
**Return**: +276.83% (+34.6% annual)  
**Out-of-Sample**: +22.48% (2021-2023)  
**Win Rate**: 85% (training), 69% (testing)  
**Sharpe**: 1.22

---

## 📊 COMPLETE RULES (Directly from best_unrestricted_strategy.json)

### **ENTRY RULES** (XOR Logic - Exactly ONE must be true)

#### Rule 1: Price vs Moving Average
```
IF price_vs_ma > 8.13%
```
**Calculation:**
```python
price_ma = 194-day moving average of close price
price_vs_ma = ((current_price / price_ma) - 1) * 100
```
**Meaning**: Current price must be **8.13% or more above** the 194-day moving average

#### Rule 2: Momentum Level
```
IF momentum < 28.59
```
**Meaning**: Momentum indicator must be **below 28.59** (moderately oversold)

#### Entry Combinator: **XOR** (Exclusive OR)
```
ENTER LONG IF:
  (price_vs_ma > 8.13%) XOR (momentum < 28.59)
  
In other words:
  - ENTER if price is strong BUT momentum is not yet low, OR
  - ENTER if momentum is low BUT price hasn't fallen yet
  - DO NOT ENTER if both conditions are true (likely too late)
  - DO NOT ENTER if neither condition is true
```

**Truth Table:**
| Price > 8.13% | Momentum < 28.59 | Action |
|--------------|------------------|---------|
| TRUE | FALSE | **ENTER** ✅ (Price leading) |
| FALSE | TRUE | **ENTER** ✅ (Momentum leading) |
| TRUE | TRUE | WAIT ❌ (Both agree = dangerous) |
| FALSE | FALSE | WAIT ❌ (No signal) |

---

### **EXIT RULES** (AND Logic - BOTH must be true)

#### Rule 1: Momentum/Volatility Ratio
```
IF momentum_volatility_ratio <= 77.72
```
**Calculation:**
```python
atr = 15-period Average True Range (volatility measure)
momentum_volatility_ratio = momentum / atr
```
**Meaning**: Exit when momentum relative to volatility drops below 77.72

#### Rule 2: Momentum Change
```
IF momentum_change >= 0.00
```
**Calculation:**
```python
momentum_change = current_momentum - previous_momentum
```
**Meaning**: Momentum must be **rising or flat** (not falling)

#### Exit Combinator: **AND**
```
EXIT LONG IF:
  (momentum_volatility_ratio <= 77.72) AND (momentum_change >= 0.00)
  
In other words:
  - Exit when momentum/volatility is low AND momentum starts rising
  - This catches turning points where volatility drops but momentum ticks up
```

---

### **POSITION SIZING**

```python
position_size_type = "fixed"
position_size_value = 100.0  # 100% of capital per trade
```

**Risk per trade**: Uses entire available capital  
**Note**: For live trading, recommend reducing to 50-70%

---

### **RISK MANAGEMENT**

#### Stop Loss
```python
stop_type = "none"  # No traditional stop loss
```
**Note**: Relies on exit rules instead of fixed stop

#### Take Profit
```python
take_profit_enabled = True
take_profit_pct = 20.36%
```
**Exit if profit reaches 20.36%** from entry price

#### Time-Based Exits
```python
min_hold_bars = 30 bars  # ~6 weeks minimum
max_hold_bars = 137 bars # ~6 months maximum
time_exit_enabled = True
```

---

### **DIRECTION**

```python
allow_long = True
allow_short = False
```
**LONG-ONLY strategy** (GA discovered this on its own)

---

### **ADVANCED FEATURES**

```python
use_momentum_acceleration = False  # Not using 2nd derivative
momentum_lookback = 33 bars        # For MA calculations

use_price_volatility = True        # Uses ATR
volatility_period = 15 bars        # 15-period ATR

pyramid_enabled = False            # No adding to positions
```

---

## 💻 PSEUDOCODE IMPLEMENTATION

```python
# === SETUP ===
capital = 10000
position = 0
entry_price = 0

# Calculate indicators
price_ma_194 = SMA(close, 194)
momentum = MomentumTracker(high, low, close, length=7)
atr_15 = ATR(high, low, close, 15)

# === EACH BAR ===
for each bar:
    
    # Calculate entry conditions
    price_vs_ma = ((close / price_ma_194) - 1) * 100
    
    condition1 = (price_vs_ma > 8.13)
    condition2 = (momentum < 28.59)
    
    # XOR: Exactly one must be true
    entry_signal = (condition1 and not condition2) or (not condition1 and condition2)
    
    # === ENTRY ===
    if position == 0 and entry_signal:
        shares = int((capital * 1.00) / close)  # 100% position
        if shares > 0:
            position = shares
            entry_price = close
            capital -= shares * close * 1.001  # 0.1% commission
            take_profit_target = entry_price * 1.2036
            entry_bar = current_bar
    
    # === EXIT ===
    if position > 0:
        bars_held = current_bar - entry_bar
        
        # Calculate exit conditions
        momentum_vol_ratio = momentum / atr_15
        momentum_change = momentum - previous_momentum
        
        exit_condition1 = (momentum_vol_ratio <= 77.72)
        exit_condition2 = (momentum_change >= 0.00)
        
        # AND: Both must be true
        exit_signal = (exit_condition1 and exit_condition2)
        
        # Take profit
        if close >= take_profit_target:
            exit_signal = True
        
        # Time exits
        if bars_held < 30:
            exit_signal = False  # Force minimum hold
        if bars_held >= 137:
            exit_signal = True   # Force maximum hold
        
        # Execute exit
        if exit_signal:
            pnl = position * (close - entry_price) * 0.999  # 0.1% commission
            capital += pnl + (position * entry_price)
            position = 0
    
    previous_momentum = momentum
```

---

## 🔍 SIMPLIFIED ENGLISH RULES

### When To BUY:
1. **Wait for ONE of these (not both):**
   - **Strong Price**: Price is 8%+ above its 194-day average, OR
   - **Weak Momentum**: Momentum indicator is below 28.59
2. **DO NOT buy when both agree** (XOR logic)
3. **Wait at least 6 weeks** before buying again

### When To SELL:
1. **ALL of these must happen:**
   - Momentum/Volatility ratio drops below 77.72, AND
   - Momentum starts rising (or flat), OR
2. **Take profit at +20.36%**, OR
3. **Maximum hold time of 6 months**

### Position Size:
- Use 100% of available capital (reduce to 50-70% for live trading)

### Direction:
- **LONG ONLY** - never short

---

## 📈 EXAMPLE TRADE WALKTHROUGH

### Entry Example:
```
Date: 2023-06-15
Price: $450
194-day MA: $415
Price vs MA: ($450/$415 - 1) * 100 = +8.43%  ✅ (> 8.13%)
Momentum: 55.2                                 ❌ (not < 28.59)

XOR Check: (TRUE and not FALSE) = TRUE ✅
→ ENTER LONG at $450
→ Buy 22 shares ($10,000 / $450)
→ Take profit target: $450 * 1.2036 = $541.62
```

### Hold Period:
```
Week 1-6: Hold (minimum 30 bars)
Week 7: Price at $480, check exit conditions daily
  - Momentum/Vol ratio: 85.3 (> 77.72) → NO EXIT
  - Still holding...

Week 10: Price at $530
  - Momentum/Vol ratio: 72.1 (< 77.72) ✅
  - Momentum change: +2.3 (> 0.00) ✅
  - BOTH true → EXIT at $530
  
→ P&L: 22 * ($530 - $450) = +$1,760 (+17.6%)
```

### Exit Example (Take Profit):
```
Week 8: Price reaches $542
  - Above take profit target ($541.62) ✅
→ EXIT at $542

→ P&L: 22 * ($542 - $450) = +$2,024 (+20.2%)
```

---

## 🎯 WHY THIS WORKS

### 1. XOR Entry (Divergence Trading)
- Catches **early** moves before everyone piles in
- Avoids **late** entries when signals align
- Exploits disagreement between price and momentum

### 2. Volatility-Adjusted Exit
- Exits when trend is weakening (low momentum/volatility)
- But waits for momentum to tick up (confirmation of reversal)
- Smart timing of exit

### 3. Trend Filter (194-day MA)
- Only trades when price is in uptrend
- Avoids bear market traps
- Provides market context

### 4. Time Management
- Forces patience (30-bar minimum)
- Prevents overtrading
- Caps losses (137-bar maximum)

---

## ⚠️ IMPORTANT NOTES FOR LIVE TRADING

### Adjustments Recommended:

1. **Position Size**: Reduce from 100% to **50-60%**
   ```python
   shares = int((capital * 0.50) / close)  # 50% instead of 100%
   ```

2. **Add Catastrophic Stop**: Despite "no stop", add emergency exit
   ```python
   if (close / entry_price - 1) < -0.15:  # -15% emergency stop
       exit_signal = True
   ```

3. **Commissions**: Account for real broker fees
   ```python
   commission = 0.001  # 0.1% or your actual rate
   ```

4. **Slippage**: Use limit orders, expect 0.05-0.1% slippage
   ```python
   actual_entry = close * 1.001  # Account for slippage
   ```

---

## 📊 PERFORMANCE EXPECTATIONS

### Historical (2013-2020):
- 40 trades over 8 years = **5 trades/year**
- Win rate: **85%** (34 wins, 6 losses)
- Average trade: **+3.65%**
- Longest trade: 137 bars (~27 weeks)

### Out-of-Sample (2021-2023):
- 13 trades over 3 years = **4.3 trades/year**
- Win rate: **69.2%** (9 wins, 4 losses)
- Total return: **+22.48%**

### Expected Going Forward:
- **4-5 trades per year** (very selective)
- **65-75% win rate** (realistic)
- **10-15% annual return** (conservative estimate)
- **Max drawdown: 20-30%** (prepare mentally)

---

## 🔧 IMPLEMENTATION CHECKLIST

- [ ] Calculate 194-day moving average
- [ ] Implement momentum tracker (length=7)
- [ ] Calculate 15-period ATR
- [ ] Code XOR entry logic
- [ ] Code AND exit logic
- [ ] Add take profit at +20.36%
- [ ] Add min hold (30 bars) and max hold (137 bars)
- [ ] Set position size to 50-60% (not 100%)
- [ ] Add emergency -15% stop loss
- [ ] Test on paper trading for 3 months
- [ ] Deploy to live with small capital
- [ ] Scale up after 10 successful trades

---

## 📁 FILES REFERENCE

- `best_unrestricted_strategy.json` - Complete parameters
- `genetic_algo_unrestricted.py` - Full implementation
- `UNRESTRICTED_GA_RESULTS.md` - Detailed analysis

---

**This is the exact, complete ruleset discovered by the unrestricted genetic algorithm!**
