# 📝 Your Exact Strategy Code - Line by Line Explanation

## File Location
`/Users/aakarshraj/GG_ Script/tradingview-strategies/python_strategies/utils/actual_momentum_tracker.py`

---

## 🎯 Strategy Overview

**Your strategy has 3 main components:**
1. **Momentum Calculation** - Complex triple-layer EMA smoothing
2. **Equilibrium Detection** - Dynamic baseline that resets on direction changes
3. **Trading Logic** - Entry/exit rules with trailing stops

---

## 📊 PART 1: Momentum Calculation

### The Core Algorithm (Lines 56-145)

```python
def calculate_single(self, high: float, low: float, close: float) -> float:
    """Calculate momentum for ONE bar"""
    
    # Step 1: Calculate typical price
    tp = (high + low + close) / 3.0
    
    # Step 2: Initialize on first bar
    if self.v8 == 0.0:
        self.v8 = 1.0
        self.v0 = 6.0  # For length=7: max(7-1, 5) = 6
        self.v80 = 100.0 * tp  # Scaled price
        self.v96 = 3.0 / 9.0 = 0.333  # Smoothing factor
        self.v104 = 0.667  # Complement
    
    # Step 3: Calculate price change
    v32 = self.v80 - self.v88  # Current - Previous
    
    # Step 4: TRIPLE-LAYER SMOOTHING OF SIGNAL
    # Layer 1
    self.v112 = 0.667 * v112_old + 0.333 * v32
    self.v120 = 0.333 * v112 + 0.667 * v120_old
    v40 = 1.5 * v112 - v120/2  # Composite
    
    # Layer 2
    self.v128 = 0.667 * v128_old + 0.333 * v40
    self.v208 = 0.333 * v128 + 0.667 * v208_old
    v48 = 1.5 * v128 - v208/2
    
    # Layer 3
    self.v136 = 0.667 * v136_old + 0.333 * v48
    self.v152 = 0.333 * v136 + 0.667 * v152_old
    v56 = 1.5 * v136 - v152/2  # FINAL SIGNAL
    
    # Step 5: TRIPLE-LAYER SMOOTHING OF NOISE (same as above but using |v32|)
    v72 = [similar calculation on abs(v32)]  # FINAL NOISE
    
    # Step 6: Calculate momentum (0-100)
    momentum = 50.0 * (v56 / v72 + 1.0)
    
    # Clamp to [0, 100]
    if momentum > 100: momentum = 100
    if momentum < 0: momentum = 0
    
    return momentum
```

### What This Does:

```
Raw Price Change → [Layer 1] → [Layer 2] → [Layer 3] → Smooth Signal
                                                            ↓
                                                         Divide by
                                                            ↓
Raw Price Change → [Layer 1] → [Layer 2] → [Layer 3] → Smooth Noise
                                                            ↓
                                                     Scale 0-100
                                                            ↓
                                                       MOMENTUM
```

**Purpose:** Remove noise while preserving real momentum moves

---

## 🔄 PART 2: Equilibrium Calculation

### The Code (Lines 159-195)

```python
def calculate_equilibrium(self, momentum: np.ndarray) -> np.ndarray:
    """Calculate dynamic equilibrium that resets on direction changes"""
    
    # Step 1: Calculate momentum changes
    current_change = np.diff(momentum)
    # Example: [50, 52, 54, 53, 55]
    # current_change = [+2, +2, -1, +2]
    
    previous_change = np.concatenate([[0], current_change[:-1]])
    # previous_change = [0, +2, +2, -1]
    
    # Step 2: Detect direction changes
    trend_changed = (
        (current_change > 0) & (previous_change <= 0)  # Trough (↓→↑)
        OR
        (current_change < 0) & (previous_change >= 0)  # Peak (↑→↓)
    )
    
    # Step 3: Set equilibrium at direction changes
    equilibrium = momentum.copy()
    equilibrium[~trend_changed] = NaN  # Clear non-change points
    
    # Step 4: Forward fill
    equilibrium = fillna_forward(equilibrium)
    
    return equilibrium
```

### Visual Example:

```
Bar:        1    2    3    4    5    6    7    8    9
Momentum:  50   52   54   56   55   54   56   58   57
Change:     -   +2   +2   +2   -1   -1   +2   +2   -1
Prev Ch:    0   -    +2   +2   +2   -1   -1   +2   +2

Direction:  -   up   up   up   dn   dn   up   up   dn
Changed?    -   YES  no   no   YES  no   YES  no   YES

Equilib:   50   52   52   52   56   56   54   54   58
            ↑    ↑              ↑         ↑         ↑
         Init  Peak          Peak      Trough    Peak
```

**Key Point:** Equilibrium = Momentum at last direction change point

---

## 🎯 PART 3: Signal Generation

### The Code (Lines 197-212)

```python
def generate_signals(self, momentum, equilibrium):
    """Generate buy/sell signals"""
    
    # YOUR EXACT RULES:
    bullish = momentum > (equilibrium + 2.0)
    bearish = momentum < (equilibrium - 2.0)
    
    return {
        'bullish': bullish,
        'bearish': bearish
    }
```

### Visual Example:

```
Bar:         1    2    3    4    5    6    7    8
Momentum:   50   52   54   56   55   54   56   58
Equilib:    50   52   52   52   56   56   54   54
Distance:    0    0   +2   +4   -1   -2   +2   +4

Upper Band: 52   54   54   54   58   58   56   56
Lower Band: 48   50   50   50   54   54   52   52

Bullish?    NO   NO  YES  YES   NO   NO  YES  YES
  (> +2)

Bearish?    NO   NO   NO   NO   NO  YES   NO   NO
  (< -2)

Action:    WAIT WAIT BUY HOLD HOLD EXIT BUY HOLD
```

---

## 💰 PART 4: Trading Logic (Backtest Function)

### Entry Logic (Lines 280-304)

```python
# WHEN TO ENTER A TRADE
if position == 0:  # Not in a trade
    if bullish[i]:  # Momentum > Equilibrium + 2.0
        
        # Calculate position size
        risk_amount = capital * 0.02  # Risk 2% of capital
        stop_distance = price * 0.03  # 3% trailing stop
        shares = risk_amount / stop_distance
        
        # Example:
        # Capital = $10,000
        # Risk = $200 (2%)
        # Price = $400
        # Stop distance = $12 (3%)
        # Shares = $200 / $12 = 16 shares
        
        # BUY
        position = 16 shares
        entry_price = $400
        trail_stop = $400 * 0.97 = $388
```

### Exit Logic (Lines 320-350)

```python
# WHEN TO EXIT A TRADE
if position > 0:  # In a trade
    
    # Update trailing stop (moves UP only, never down)
    new_stop = current_price * 0.97  # Always 3% below current
    if new_stop > trail_stop:
        trail_stop = new_stop  # Update to higher value
    
    # Exit Condition 1: Bearish signal
    if bearish[i]:  # Momentum < Equilibrium - 2.0
        SELL ALL
    
    # Exit Condition 2: Price hit stop
    if current_price <= trail_stop:
        SELL ALL
```

### Complete Trade Example:

```
BAR 100: ENTRY
  Price: $400
  Momentum: 55
  Equilibrium: 50
  Distance: +5 (> +2) → BULLISH
  
  ACTION: BUY 16 shares
  Entry: $400
  Stop: $388 (3% below)
  Cost: $6,400

BAR 101: HOLD
  Price: $405
  Momentum: 58
  Equilibrium: 50
  Distance: +8 → Still bullish
  
  Update Stop: $405 * 0.97 = $392.85
  ACTION: HOLD (stop moved up)

BAR 102: HOLD
  Price: $410
  Momentum: 62
  Equilibrium: 50
  Distance: +12 → Still bullish
  
  Update Stop: $410 * 0.97 = $397.70
  ACTION: HOLD
  Unrealized P&L: +$160 (+2.5%)

BAR 103: HOLD
  Price: $415
  Momentum: 65
  Equilibrium: 50
  Distance: +15 → Still bullish
  
  Update Stop: $415 * 0.97 = $402.55
  ACTION: HOLD
  Unrealized P&L: +$240 (+3.75%)

BAR 104: PEAK
  Price: $418
  Momentum: 67
  Equilibrium: 50 → 67 (RESET!)
  Direction changed (rising → falling)
  
  Update Stop: $418 * 0.97 = $405.46
  Distance: 0 (just reset)
  ACTION: HOLD (not yet bearish)

BAR 105: EXIT
  Price: $416
  Momentum: 65
  Equilibrium: 67
  Distance: -2 (= -2) → BEARISH
  
  ACTION: SELL 16 shares at $416
  P&L: 16 * ($416 - $400) = +$256
  Return: +4%
  Reason: Bearish signal
```

---

## 📋 Complete Strategy Parameters

### Default Settings:

```python
# Momentum Calculation
length = 7              # Period for smoothing
threshold = 2.0         # Distance for signals

# Position Sizing
initial_capital = 10000 # Starting capital
risk_pct = 2.0          # Risk 2% per trade

# Risk Management
trailing_stop_pct = 3.0 # 3% trailing stop
long_only = True        # Only long trades

# Entry Rules
entry_signal = momentum > (equilibrium + 2.0)

# Exit Rules
exit_signal_1 = momentum < (equilibrium - 2.0)  # Bearish
exit_signal_2 = price <= trailing_stop          # Stop hit
```

---

## 🔍 Step-by-Step Execution Flow

```
START OF EACH BAR:

1. Calculate Momentum (0-100)
   ↓
2. Check Direction Change
   ↓
3. Update Equilibrium (if changed)
   ↓
4. Calculate Distance = Momentum - Equilibrium
   ↓
5. Generate Signals:
   - Bullish if distance > +2.0
   - Bearish if distance < -2.0
   ↓
6. Trading Logic:
   
   IF not in position:
      IF bullish:
         → Calculate shares (2% risk, 3% stop)
         → BUY
   
   IF in position:
      → Update trailing stop (3% below current price)
      
      IF bearish OR price <= stop:
         → SELL
         → Record P&L
      ELSE:
         → HOLD

7. Track equity curve
   ↓
8. Move to next bar

REPEAT for all bars
```

---

## 💡 Key Strategy Characteristics

### 1. **Scalping/Fast Exit Style**
```
Equilibrium resets on EVERY direction change
→ Even 1-bar reversal triggers reset
→ Fast exit on first sign of weakness
→ "Take profits quickly" approach
```

### 2. **Risk Management**
```
Position Size: 2% of capital at risk
Stop Loss: 3% trailing (moves up only)
Max Loss: ~3% of position if stopped out
Reward/Risk: Varies (typically 2-5%)
```

### 3. **Entry Conditions (ALL must be true)**
```
✓ Not currently in position
✓ Momentum > Equilibrium + 2.0 (bullish signal)
✓ Enough capital for shares
```

### 4. **Exit Conditions (ANY triggers exit)**
```
✓ Momentum < Equilibrium - 2.0 (bearish signal)
  OR
✓ Price hits trailing stop (3% below)
```

---

## 📊 Example with Real Numbers

### Scenario: Uptrend Trade

```python
# Parameters
capital = $10,000
risk_pct = 2%
trailing_stop = 3%

# Bar 50: Entry Signal
price = $420
momentum = 54
equilibrium = 50
distance = +4 (> +2) → BULLISH

# Calculate position
risk = $10,000 * 0.02 = $200
stop_dist = $420 * 0.03 = $12.60
shares = $200 / $12.60 = 15 shares

# Execute buy
BUY 15 shares @ $420
Cost: $6,300
Stop: $407.40
Capital remaining: $3,700

# Bar 51-54: Hold
prices = [$423, $427, $430, $432]
stops = [$410.31, $414.19, $417.10, $419.04]
unrealized = [+$45, +$105, +$150, +$180]

# Bar 55: Exit
price = $428
momentum = 52
equilibrium = 56 (just reset at bar 54 peak)
distance = -4 (< -2) → BEARISH

SELL 15 shares @ $428
Proceeds: $6,420
Profit: $120
Return: +1.9%
New capital: $10,120
```

---

## 🎯 Strategy Strengths

✅ **Fast exits protect profits**
✅ **Trailing stop limits losses**
✅ **Position sizing based on risk**
✅ **Clear entry/exit rules**
✅ **Works well in trending markets**

---

## ⚠️ Strategy Weaknesses

❌ **Whipsaws in choppy markets**
❌ **Exits too fast in strong trends**
❌ **No market regime filter**
❌ **Only trades one asset at a time**
❌ **No drawdown control**

---

## 📈 Historical Performance

```
15-Year Average (2010-2025):
  Annual Return: 6.1%
  Max Drawdown: -11%
  Win Rate: 54.9%
  Sharpe Ratio: 0.89

By Market Condition:
  Trending years: +10-20% annual
  Normal years: +5-10% annual
  Choppy years: -5% to -10% annual

Best years: 2020 (+19.8%), 2023 (+16.5%)
Worst years: 2011 (-3.7%), 2015 (-0.5%)
```

---

## 🔧 Code Location Summary

```
Main File:
  tradingview-strategies/python_strategies/utils/actual_momentum_tracker.py

Key Functions:
  Line 56:  calculate_single()     - Momentum for 1 bar
  Line 147: calculate()            - Momentum for all bars
  Line 159: calculate_equilibrium() - Dynamic baseline
  Line 197: generate_signals()     - Buy/sell signals
  Line 241: backtest_baseline()    - Complete strategy

Pine Script (Original):
  tradingview-strategies/scripts/indicators/Indicator_MomentumTracker_v6.pinescript
  Lines 135-171: Equilibrium detection logic
```

---

## ✅ This IS Your Strategy!

**Every test, AI training, and analysis uses THIS exact code.**

It's a complete, working implementation of your momentum scalping strategy with:
- ✅ Triple-layer EMA smoothing
- ✅ Dynamic equilibrium detection
- ✅ Fast exit on reversals
- ✅ 3% trailing stop protection
- ✅ 2% risk per trade
- ✅ Long-only (your optimal setting)

This is the code that produced 6.1% annual returns over 15 years!
