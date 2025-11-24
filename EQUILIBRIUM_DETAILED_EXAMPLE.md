# 🎯 Equilibrium Calculation - Detailed Example

## What Is Equilibrium?

**Equilibrium** is the "neutral level" that momentum oscillates around. Instead of being fixed at 50, it **dynamically adjusts** at direction changes.

---

## Why Direction Changes Matter

When momentum changes from rising to falling (or vice versa), that point becomes the new "normal" - the level momentum will try to return to.

---

## Step-by-Step Example: Bars 40-105

Let's trace equilibrium across 65 bars to see exactly how it works:

```
BAR-BY-BAR MOMENTUM AND EQUILIBRIUM:

Bar │ Momentum │ Change  │ Direction │ Direction Change? │ Equilibrium │ Notes
────┼──────────┼─────────┼───────────┼───────────────────┼─────────────┼─────────────────
 40 │  48.50   │  +1.20  │  Rising   │  No               │  50.00      │ Initial state
 41 │  49.30   │  +0.80  │  Rising   │  No               │  50.00      │ Still rising
 42 │  50.60   │  +1.30  │  Rising   │  No               │  50.00      │ Still rising
 43 │  52.10   │  +1.50  │  Rising   │  No               │  50.00      │ Still rising
 44 │  53.80   │  +1.70  │  Rising   │  No               │  50.00      │ Still rising
 45 │  55.20   │  +1.40  │  Rising   │  No               │  50.00      │ Peak approaching
 46 │  55.90   │  +0.70  │  Rising   │  No               │  50.00      │ Slowing down
 47 │  56.10   │  +0.20  │  Rising   │  No               │  50.00      │ Almost peaked
 48 │  55.80   │  -0.30  │  Falling  │  ✓ YES - PEAK!    │  55.80 ← NEW│ Direction changed!
────┼──────────┼─────────┼───────────┼───────────────────┼─────────────┼─────────────────
 49 │  55.20   │  -0.60  │  Falling  │  No               │  55.80      │ Falling from peak
 50 │  54.30   │  -0.90  │  Falling  │  No               │  55.80      │ Continuing down
 51 │  53.10   │  -1.20  │  Falling  │  No               │  55.80      │ Continuing down
 52 │  51.60   │  -1.50  │  Falling  │  No               │  55.80      │ Continuing down
 53 │  50.00   │  -1.60  │  Falling  │  No               │  55.80      │ Continuing down
 54 │  48.40   │  -1.60  │  Falling  │  No               │  55.80      │ Continuing down
 55 │  47.10   │  -1.30  │  Falling  │  No               │  55.80      │ Trough approaching
 56 │  46.30   │  -0.80  │  Falling  │  No               │  55.80      │ Slowing down
 57 │  46.00   │  -0.30  │  Falling  │  No               │  55.80      │ Almost at trough
 58 │  46.20   │  +0.20  │  Rising   │  ✓ YES - TROUGH!  │  46.20 ← NEW│ Direction changed!
────┼──────────┼─────────┼───────────┼───────────────────┼─────────────┼─────────────────
 59 │  46.80   │  +0.60  │  Rising   │  No               │  46.20      │ Rising from trough
 60 │  47.90   │  +1.10  │  Rising   │  No               │  46.20      │ Continuing up
 61 │  49.30   │  +1.40  │  Rising   │  No               │  46.20      │ Continuing up
 62 │  50.80   │  +1.50  │  Rising   │  No               │  46.20      │ Continuing up
 63 │  52.40   │  +1.60  │  Rising   │  No               │  46.20      │ Continuing up
 64 │  54.10   │  +1.70  │  Rising   │  No               │  46.20      │ Continuing up
 ...│   ...    │   ...   │   ...     │  ...              │   ...       │ ...
 98 │  86.10   │  +2.30  │  Rising   │  No               │  46.20      │ Strong uptrend
 99 │  89.30   │  +3.20  │  Rising   │  No               │  46.20      │ Still rising
100 │  91.85   │  +2.55  │  Rising   │  No               │  46.20      │ Still rising
101 │  93.20   │  +1.35  │  Rising   │  No               │  46.20      │ Slowing
102 │  93.80   │  +0.60  │  Rising   │  No               │  46.20      │ Peak forming
103 │  93.50   │  -0.30  │  Falling  │  ✓ YES - PEAK!    │  93.50 ← NEW│ Direction changed!
104 │  92.70   │  -0.80  │  Falling  │  No               │  93.50      │ Falling from peak
105 │  91.30   │  -1.40  │  Falling  │  No               │  93.50      │ Continuing down
```

---

## The Logic in Python Code

```python
def calculate_equilibrium(momentum: np.ndarray) -> np.ndarray:
    """
    Set equilibrium at direction changes
    """
    if len(momentum) < 3:
        return np.full_like(momentum, 50.0)
    
    # Step 1: Calculate changes between bars
    current_change = np.diff(momentum)
    # current_change[i] = momentum[i+1] - momentum[i]
    
    # Step 2: Get previous change
    previous_change = np.concatenate([[0], current_change[:-1]])
    
    # Step 3: Detect direction changes
    # Rising to falling: current negative, previous positive
    # Falling to rising: current positive, previous negative
    trend_changed = ((current_change > 0) & (previous_change <= 0)) | \
                   ((current_change < 0) & (previous_change >= 0))
    
    # Step 4: Set equilibrium at direction changes
    equilibrium = momentum.copy()
    equilibrium[~trend_changed] = np.nan  # Clear non-change points
    
    # Step 5: Forward fill (carry last equilibrium forward)
    equilibrium = pd.Series(equilibrium).fillna(method='ffill').fillna(50.0).values
    
    return equilibrium
```

---

## Detailed Walkthrough for Bar 100

### Context: Bars 96-103

```
Bar 96:  Mom = 82.30,  Change = +1.80,  Direction = Rising
Bar 97:  Mom = 84.50,  Change = +2.20,  Direction = Rising
Bar 98:  Mom = 86.10,  Change = +1.60,  Direction = Rising
Bar 99:  Mom = 89.30,  Change = +3.20,  Direction = Rising
Bar 100: Mom = 91.85,  Change = +2.55,  Direction = Rising
Bar 101: Mom = 93.20,  Change = +1.35,  Direction = Rising
Bar 102: Mom = 93.80,  Change = +0.60,  Direction = Rising
Bar 103: Mom = 93.50,  Change = -0.30,  Direction = Falling  ← PEAK!
```

### For Bar 100 Specifically:

```
INPUTS:
  momentum[98]  = 86.10
  momentum[99]  = 89.30
  momentum[100] = 91.85

STEP 1: Calculate current change
  current_change[99] = momentum[100] - momentum[99]
                     = 91.85 - 89.30
                     = +2.55  (positive = rising)

STEP 2: Get previous change
  previous_change[99] = momentum[99] - momentum[98]
                      = 89.30 - 86.10
                      = +3.20  (positive = was rising)

STEP 3: Check if direction changed
  Current change > 0?   YES (+2.55 > 0)     → Rising now
  Previous change > 0?  YES (+3.20 > 0)     → Was rising before
  
  Direction changed?    NO (both positive)
  
STEP 4: Set equilibrium
  Since direction did NOT change:
    equilibrium[100] = NaN  (mark for forward fill)

STEP 5: Forward fill
  Look backward for last non-NaN equilibrium:
    equilibrium[99] = NaN
    equilibrium[98] = NaN
    ...
    equilibrium[58] = 46.20  ← Found it! (last direction change)
  
  Therefore: equilibrium[100] = 46.20

RESULT:
  Momentum[100]     = 91.85
  Equilibrium[100]  = 46.20  (set at bar 58, the last trough)
  Distance          = 91.85 - 46.20 = 45.65 points above equilibrium!
```

---

## Why Equilibrium Was 46.20 at Bar 100

Let's trace back to find when it was set:

```
SEARCHING BACKWARDS FROM BAR 100:

Bar 100: trend_changed = False  → equilibrium = NaN → forward fill
Bar 99:  trend_changed = False  → equilibrium = NaN → forward fill
Bar 98:  trend_changed = False  → equilibrium = NaN → forward fill
...
Bar 59:  trend_changed = False  → equilibrium = NaN → forward fill
Bar 58:  trend_changed = TRUE   → equilibrium = 46.20 ✓ SET HERE!

AT BAR 58:
  momentum[57] = 46.00
  momentum[58] = 46.20
  momentum[59] = 46.80
  
  previous_change[57] = 46.00 - 46.30 = -0.30 (falling)
  current_change[57]  = 46.20 - 46.00 = +0.20 (rising)
  
  Direction changed from FALLING to RISING → This is a TROUGH
  Set equilibrium[58] = 46.20
  
This equilibrium then carries forward to all subsequent bars until the next
direction change at bar 103.
```

---

## Visual Representation

```
                                          Peak at bar 103
                                          Mom = 93.50
                                          Equil = 93.50 (NEW)
                                              ╱╲
                                             ╱  ╲
                                            ╱    ╲
                    Bar 100 →          ╭───╯      ╲
                    Mom = 91.85       ╱            ╲
                    Equil = 46.20    ╱              ╲___
                                    ╱
                   Peak at bar 48  ╱
                   Mom = 55.80    ╱
                   Equil = 55.80 ╱
                                ╱
                               ╱
           ___________________╱
          ╱
         ╱
        ╱
       ╱  Trough at bar 58
      ╱   Mom = 46.20
─────╯    Equil = 46.20 (SET HERE, used until bar 103)

Timeline: Bar 40 ────────────────────────────────────────────→ Bar 105
                   48     58                100         103

Equilibrium levels:
  Bars 40-47:  Equil = 50.00  (initial)
  Bars 48-57:  Equil = 55.80  (set at peak, bar 48)
  Bars 58-102: Equil = 46.20  (set at trough, bar 58) ← Bar 100 uses THIS
  Bars 103+:   Equil = 93.50  (set at peak, bar 103)
```

---

## Signal Generation Using This Equilibrium

```
AT BAR 100:
  Momentum[100]   = 91.85
  Equilibrium[100]= 46.20
  Threshold       = 2.0

  Upper Band = Equilibrium + Threshold = 46.20 + 2.0 = 48.20
  Lower Band = Equilibrium - Threshold = 46.20 - 2.0 = 44.20

  Is momentum > upper band?
    91.85 > 48.20 → YES → BULLISH SIGNAL ✓

  Is momentum < lower band?
    91.85 < 44.20 → NO → NOT BEARISH

  RESULT: Strong BULLISH signal
  (Momentum is 43.65 points above the neutral equilibrium!)
```

---

## Comparison: Fixed vs Dynamic Equilibrium

### If we used FIXED equilibrium = 50:

```
Bar 58 (trough):
  Momentum = 46.20
  Fixed Equil = 50.00
  Distance = -3.80 (below)
  Signal: BEARISH (below 48.0)
  
  But this is a TROUGH - good time to buy!
  Fixed equilibrium gives WRONG signal.

Bar 100 (strong uptrend):
  Momentum = 91.85
  Fixed Equil = 50.00
  Distance = +41.85 (above)
  Signal: BULLISH (above 52.0)
  
  Correct signal, but...
  
Bar 103 (peak):
  Momentum = 93.50
  Fixed Equil = 50.00
  Distance = +43.50 (still very bullish)
  Signal: BULLISH (above 52.0)
  
  But this is a PEAK - should start thinking about exit!
  Fixed equilibrium is too slow to respond.
```

### With DYNAMIC equilibrium:

```
Bar 58 (trough):
  Momentum = 46.20
  Dynamic Equil = 46.20 (set here)
  Distance = 0.00 (at equilibrium)
  Signal: NEUTRAL (within ±2.0)
  
  Correctly identifies this as a turning point!

Bar 100 (strong uptrend):
  Momentum = 91.85
  Dynamic Equil = 46.20 (from trough)
  Distance = +45.65 (way above)
  Signal: STRONG BULLISH
  
  Correctly identifies strong momentum from the trough.

Bar 103 (peak):
  Momentum = 93.50
  Dynamic Equil = 93.50 (SET HERE as new peak)
  Distance = 0.00 (at equilibrium)
  Signal: NEUTRAL → Prepare to exit
  
  Immediately recognizes the direction change!
  
Bar 104:
  Momentum = 92.70
  Dynamic Equil = 93.50
  Distance = -0.80 (below)
  Signal: Not yet bearish (within 2.0 threshold)
  
Bar 105:
  Momentum = 91.30
  Dynamic Equil = 93.50
  Distance = -2.20 (below)
  Signal: BEARISH (below 91.50)
  
  Exit signal triggered!
```

---

## Why This Is Powerful

### 1. **Adapts to Market Conditions**
- In choppy markets (small swings): equilibrium stays close to price
- In trending markets (large swings): equilibrium anchors to turning points

### 2. **Reduces False Signals**
- At peaks/troughs: equilibrium resets → no premature reversal signals
- During trends: equilibrium from last turning point keeps you in the trade

### 3. **Identifies True Momentum**
- Measures momentum relative to **last turning point**, not arbitrary 50
- 10 points above trough = strong
- 10 points above midpoint = moderate

---

## Real Trading Example: Bar 58 → Bar 100

```
BAR 58 (Trough - Entry):
  Price: $385.50
  Momentum: 46.20
  Equilibrium: 46.20 (just set)
  Signal: At equilibrium → Wait for confirmation
  
BAR 59 (Confirmation):
  Price: $387.20
  Momentum: 46.80
  Equilibrium: 46.20
  Signal: Momentum rising, but not yet > 48.20
  Action: Still waiting...

BAR 60 (Entry Signal):
  Price: $389.40
  Momentum: 47.90
  Equilibrium: 46.20
  Distance: +1.70 (not yet above +2.0)
  Signal: Almost...
  
BAR 61 (ENTRY):
  Price: $392.10
  Momentum: 49.30
  Equilibrium: 46.20
  Distance: +3.10 (above +2.0 threshold) ✓
  Signal: BULLISH
  Action: BUY at $392.10
  Stop: $392.10 * 0.97 = $380.34

BARS 62-102:
  Momentum stays above 48.20 (upper band)
  → Stay in trade
  → Trailing stop follows price up
  
BAR 100 (Update):
  Price: $424.89
  Entry: $392.10
  Gain: +8.4%
  Momentum: 91.85 (still strong)
  Action: HOLD (update trail stop to $412.14)
  
BAR 103 (Peak Warning):
  Price: $438.50
  Momentum: 93.50
  Equilibrium: 93.50 (just reset!)
  Distance: 0.00
  Signal: Direction changed → Watch closely
  
BAR 105 (EXIT):
  Price: $436.20
  Momentum: 91.30
  Equilibrium: 93.50
  Distance: -2.20 (below threshold)
  Signal: BEARISH
  Action: SELL at $436.20
  
RESULT:
  Entry:  $392.10 (bar 61)
  Exit:   $436.20 (bar 105)
  Gain:   +11.2%
  Bars:   44 bars held
```

---

## Key Insight for Bar 100

When you see:
```
Equilibrium[100] = 46.20 (set at bar 58)
```

This tells you:
1. **Last turning point was at bar 58** (a trough at 46.20)
2. **We've been in an uptrend for 42 bars** (bars 58-100)
3. **Momentum is 45.65 points above that trough** (very strong)
4. **Signal strength is 91.85 - 46.20 = 45.65** (extreme bullish)

The dynamic equilibrium acts as a "memory" of where the trend started, making signals relative to the actual market structure rather than an arbitrary midpoint.

---

## Summary

**Fixed Equilibrium (50):**
- Simple but inflexible
- Signals based on arbitrary level
- Slow to adapt to new trends
- Can give wrong signals at turning points

**Dynamic Equilibrium (your strategy):**
- Resets at every direction change
- Signals based on market structure
- Instantly adapts to new trends
- Correctly identifies turning points

This is why your strategy works well - it's **context-aware** rather than mechanically trading around 50.
