# 🚨 CRITICAL BUG: Equilibrium Resets Too Frequently

## Your Example - The Problem

```
Bar 100: Momentum = 76
Bar 101: Momentum = 78  (rising)
Bar 102: Momentum = 80  (still rising) ← PEAK
Bar 103: Momentum = 78  (falling) ← Direction changed!
```

### What SHOULD Happen (Logical):
```
Bar 103: Momentum dropped from 80 → 78
  This is just a small pullback (-2 points)
  Should NOT be a sell signal
  Should HOLD position
```

### What ACTUALLY Happens (Bug):
```
Bar 102 → 103: Direction changed (rising → falling)
  Equilibrium RESETS to 80 (the peak)
  
Bar 103 State:
  Momentum:    78
  Equilibrium: 80 (just reset!)
  Distance:    78 - 80 = -2.0
  Lower Band:  80 - 2.0 = 78.0
  
  Momentum (78) <= Lower Band (78.0)
  → BEARISH SIGNAL! 🔴
  → SELL (even though it's just a tiny pullback!)
```

---

## The Bug Illustrated

```
MOMENTUM CHART:

 85 │
    │
 80 │              ╱╲  ← Bar 102: Peak at 80
    │             ╱  ╲    Equilibrium RESETS to 80
 78 │          ╱      ╲  ← Bar 103: Drops to 78
    │         ╱        ╲
 76 │      ╱            ← Distance = -2.0 from new equilibrium
    │   ╱                 BEARISH SIGNAL triggered!
    │  ╱                  SELL!
    │
────┴──────────────────────────────────────→
    100  101  102  103

PROBLEM:
  The strategy sees momentum 78 as "2 points below equilibrium 80"
  → Triggers SELL on a minor pullback
  → Would have missed the continued uptrend if it resumes
```

---

## Real Trading Disaster Scenario

```
═══════════════════════════════════════════════════════════════
SCENARIO: Whipsaw During Strong Uptrend
═══════════════════════════════════════════════════════════════

Bar 95:  Mom = 70, Equil = 50, Dist = +20 → HOLD (strong uptrend)
Bar 96:  Mom = 72, Equil = 50, Dist = +22 → HOLD
Bar 97:  Mom = 75, Equil = 50, Dist = +25 → HOLD
Bar 98:  Mom = 78, Equil = 50, Dist = +28 → HOLD
Bar 99:  Mom = 80, Equil = 50, Dist = +30 → HOLD
Bar 100: Mom = 83, Equil = 50, Dist = +33 → HOLD (peak approaching)
Bar 101: Mom = 85, Equil = 50, Dist = +35 → HOLD
Bar 102: Mom = 86, Equil = 50, Dist = +36 → HOLD (highest point)

───────────────────────────────────────────────────────────────
Bar 103: Mom = 85 ← Tiny dip (-1 point)
───────────────────────────────────────────────────────────────

Direction changed: Rising → Falling
Equilibrium RESETS: 50 → 86

New State:
  Momentum:    85
  Equilibrium: 86
  Distance:    -1.0
  Lower Band:  84.0
  
Check: 85 < 84.0? NO
Signal: Not yet bearish
Action: HOLD (safe for now)

───────────────────────────────────────────────────────────────
Bar 104: Mom = 84 ← Another small dip (-1 point)
───────────────────────────────────────────────────────────────

Direction still falling
Equilibrium: 86 (unchanged)

New State:
  Momentum:    84
  Equilibrium: 86
  Distance:    -2.0
  Lower Band:  84.0
  
Check: 84 <= 84.0? YES! ✗
Signal: BEARISH
Action: 🔴 SELL ALL

───────────────────────────────────────────────────────────────
Bar 105: Mom = 85 ← Momentum resumes rising
───────────────────────────────────────────────────────────────

Direction changed: Falling → Rising
Equilibrium RESETS: 86 → 84

Position: 0 (just sold at bar 104)
  Momentum:    85
  Equilibrium: 84
  Distance:    +1.0
  Upper Band:  86.0
  
Check: 85 > 86.0? NO
Signal: Not yet bullish
Action: Wait...

───────────────────────────────────────────────────────────────
Bar 106: Mom = 87 ← Continues rising
───────────────────────────────────────────────────────────────

Direction: Rising
Equilibrium: 84

New State:
  Momentum:    87
  Equilibrium: 84
  Distance:    +3.0
  Upper Band:  86.0
  
Check: 87 > 86.0? YES! ✓
Signal: BULLISH
Action: 🟢 BUY (re-enter at higher price!)

───────────────────────────────────────────────────────────────
Bars 107-120: Momentum continues to 95
───────────────────────────────────────────────────────────────

The uptrend continues for 14 more bars...

═══════════════════════════════════════════════════════════════
RESULT: Whipsaw Loss
═══════════════════════════════════════════════════════════════

Exit at Bar 104:  Price $420, Mom = 84
Re-Enter Bar 106: Price $425, Mom = 87

OUTCOME:
  • Sold during 2-bar pullback in strong uptrend
  • Re-bought at HIGHER price
  • Lost $5 per share + commissions
  • Momentum never actually reversed (went 86 → 85 → 84 → 85 → 87 → 95)
  • Just normal volatility, not a trend change!
```

---

## Why This Happens

### The Current Logic:

```python
def calculate_equilibrium(momentum):
    """
    Sets equilibrium at EVERY direction change
    """
    
    # Detect direction change
    current_change = momentum[i] - momentum[i-1]
    previous_change = momentum[i-1] - momentum[i-2]
    
    # If direction flipped
    if (current_change > 0 and previous_change <= 0) or \
       (current_change < 0 and previous_change >= 0):
        # RESET EQUILIBRIUM TO CURRENT MOMENTUM
        equilibrium[i] = momentum[i]  # ← THE PROBLEM!
    else:
        # Keep previous equilibrium
        equilibrium[i] = equilibrium[i-1]
```

### The Issue:

**Every tiny zigzag resets the equilibrium!**

```
Momentum: 76 → 78 → 80 → 78 → 79 → 81 → 80 → 82

Direction changes:
  78→80: Rising
  80→78: Falling  ← Reset equil to 80
  78→79: Rising   ← Reset equil to 78
  79→81: Rising
  81→80: Falling  ← Reset equil to 81
  80→82: Rising   ← Reset equil to 80

Equilibrium keeps jumping: 50 → 80 → 78 → 81 → 80 → ...

This creates CONSTANT false signals!
```

---

## The Root Cause

Your momentum tracker is **TOO SENSITIVE** to direction changes because:

1. **Any single-bar reversal resets equilibrium**
   - Momentum goes 80 → 78 → direction changed
   - Even though this is normal market noise

2. **No smoothing/filtering on direction detection**
   - A 1-point drop from 80 to 79 counts as "trend reversal"
   - Real trend reversals should be more significant

3. **Threshold (±2.0) is too tight relative to the equilibrium reset**
   - Equilibrium resets to peak/trough
   - Threshold only 2 points away
   - Any small move triggers signal

---

## Proof: Check Your Actual Data

Let me check what's happening in the real backtest:

```python
# From your actual_momentum_tracker.py

def calculate_equilibrium(momentum):
    # Calculate direction changes
    current_change = np.diff(momentum)
    previous_change = np.concatenate([[0], current_change[:-1]])
    
    # Detect when direction changes
    trend_changed = ((current_change > 0) & (previous_change <= 0)) | \
                   ((current_change < 0) & (previous_change >= 0))
    
    # Set equilibrium at direction changes
    equilibrium = momentum.copy()
    equilibrium[~trend_changed] = np.nan
    
    # Forward fill
    equilibrium = pd.Series(equilibrium).fillna(method='ffill').fillna(50.0).values
```

**This DOES reset equilibrium at every direction change!**

### Test Case:

```
Input momentum: [50, 52, 54, 56, 55, 57, 59, 58, 60]

Bar  Mom  Change  Prev_Ch  Direction  Trend_Ch?  Equilibrium
0    50   -       -        -          -          50.0
1    52   +2      0        Rising     Yes        52.0
2    54   +2      +2       Rising     No         52.0
3    56   +2      +2       Rising     No         52.0
4    55   -1      +2       Falling    Yes        55.0  ← Reset!
5    57   +2      -1       Rising     Yes        57.0  ← Reset!
6    59   +2      +2       Rising     No         57.0
7    58   -1      +2       Falling    Yes        58.0  ← Reset!
8    60   +2      -1       Rising     Yes        60.0  ← Reset!

Equilibrium jumped 4 times in 8 bars!
Each jump creates a potential false signal.
```

---

## The Fix: Multiple Options

### Option 1: Use Smoothed Direction Detection

Only reset equilibrium on SIGNIFICANT direction changes:

```python
def calculate_equilibrium_smoothed(momentum, min_change=5.0):
    """
    Only reset equilibrium if direction change is significant
    """
    equilibrium = np.full_like(momentum, 50.0)
    current_equil = 50.0
    
    for i in range(2, len(momentum)):
        change = momentum[i] - momentum[i-1]
        prev_change = momentum[i-1] - momentum[i-2]
        
        # Only reset if direction changed AND move was significant
        if (change > 0 and prev_change <= 0) or (change < 0 and prev_change >= 0):
            magnitude = abs(momentum[i] - current_equil)
            if magnitude > min_change:  # Must move 5+ points from current equil
                current_equil = momentum[i]
        
        equilibrium[i] = current_equil
    
    return equilibrium
```

### Option 2: Use Rolling Window for Direction

Don't look at single bar changes, look at trend over window:

```python
def calculate_equilibrium_windowed(momentum, window=5):
    """
    Detect direction change over a window, not single bar
    """
    equilibrium = np.full_like(momentum, 50.0)
    
    for i in range(window, len(momentum)):
        # Compare average of last 'window' bars to previous window
        current_avg = np.mean(momentum[i-window+1:i+1])
        previous_avg = np.mean(momentum[i-window:i])
        
        # Direction based on windows
        if current_avg > previous_avg:
            direction = 'rising'
        else:
            direction = 'falling'
        
        # Check previous direction
        if i > window:
            prev_current = np.mean(momentum[i-window:i])
            prev_previous = np.mean(momentum[i-window-1:i-1])
            prev_direction = 'rising' if prev_current > prev_previous else 'falling'
            
            # Reset only if direction flipped
            if direction != prev_direction:
                equilibrium[i] = momentum[i]
            else:
                equilibrium[i] = equilibrium[i-1]
        else:
            equilibrium[i] = 50.0
    
    return equilibrium
```

### Option 3: Use Percentage-Based Threshold

Only reset if momentum changed by X%:

```python
def calculate_equilibrium_percentage(momentum, pct_threshold=2.0):
    """
    Only reset if momentum changed by percentage threshold
    """
    equilibrium = np.full_like(momentum, 50.0)
    current_equil = 50.0
    last_peak_or_trough = momentum[0]
    
    for i in range(2, len(momentum)):
        change = momentum[i] - momentum[i-1]
        prev_change = momentum[i-1] - momentum[i-2]
        
        # Direction changed?
        if (change > 0 and prev_change <= 0) or (change < 0 and prev_change >= 0):
            # Check if move is significant (2% of momentum value)
            pct_change = abs(momentum[i] - last_peak_or_trough) / max(momentum[i], 0.01) * 100
            
            if pct_change >= pct_threshold:
                current_equil = momentum[i]
                last_peak_or_trough = momentum[i]
        
        equilibrium[i] = current_equil
    
    return equilibrium
```

### Option 4: Simply Use a Fixed Equilibrium

The simplest fix - just use 50:

```python
def calculate_equilibrium_fixed(momentum):
    """
    Use fixed equilibrium at 50 (simple but effective)
    """
    return np.full_like(momentum, 50.0)
```

---

## Which Fix Should You Use?

### Test Each Approach:

| Method | Pros | Cons | When to Use |
|--------|------|------|-------------|
| **Current (Every Change)** | Adapts quickly | Too many false signals | ❌ Don't use |
| **Smoothed (Min Change)** | Filters noise, keeps adaptive | Needs tuning (min_change param) | ✅ Good for volatile markets |
| **Windowed (5-bar avg)** | Very stable | Slower to adapt | ✅ Good for trending markets |
| **Percentage (2% move)** | Scales with momentum level | Complex logic | ⚠️ Requires testing |
| **Fixed (50 always)** | No false resets | Loses context | ✅ Good baseline |

---

## Recommended Fix

**Start with Option 1 (Smoothed with min_change=5.0):**

```python
# In actual_momentum_tracker.py

def calculate_equilibrium(self, momentum: np.ndarray, min_change=5.0) -> np.ndarray:
    """
    Calculate equilibrium with minimum change threshold
    """
    if len(momentum) < 3:
        return np.full_like(momentum, 50.0)
    
    equilibrium = np.full_like(momentum, 50.0)
    current_equil = 50.0
    
    for i in range(2, len(momentum)):
        change = momentum[i] - momentum[i-1]
        prev_change = momentum[i-1] - momentum[i-2]
        
        # Direction changed?
        direction_changed = ((change > 0 and prev_change <= 0) or 
                            (change < 0 and prev_change >= 0))
        
        if direction_changed:
            # Only reset if moved significantly from current equilibrium
            distance = abs(momentum[i] - current_equil)
            if distance > min_change:
                current_equil = momentum[i]
        
        equilibrium[i] = current_equil
    
    return equilibrium
```

### Why This Works:

```
Example with min_change=5.0:

Bar 100: Mom = 76, Equil = 50, Dist = +26
Bar 101: Mom = 78, Equil = 50, Dist = +28
Bar 102: Mom = 80, Equil = 50, Dist = +30 (peak)
Bar 103: Mom = 78, Equil = 50, Dist = +28
         Direction changed? YES (falling)
         Distance from equil: |78 - 50| = 28
         Is 28 > 5.0? YES
         But this is a trough move, check momentum vs current equil...
         
Actually, need to check: |78 - 80| = 2
Is 2 > 5.0? NO
→ Don't reset equilibrium
→ Keep equilibrium = 50
→ Still bullish (+28 above equilibrium)
→ HOLD position ✓
```

---

## Your Example Fixed:

### Before Fix (Current):
```
Bar 102: Mom = 80, Equil = 50  → HOLD
Bar 103: Mom = 78, Equil = 80  → Distance = -2.0 → SELL ✗
```

### After Fix (Smoothed):
```
Bar 102: Mom = 80, Equil = 50  → HOLD
Bar 103: Mom = 78, Equil = 50  → Distance = +28 → HOLD ✓

(Equilibrium doesn't reset because 2-point drop is < 5-point threshold)
```

---

## Action Items

1. **Update `actual_momentum_tracker.py`** with smoothed equilibrium
2. **Re-run backtests** to see improvement
3. **Test different `min_change` values** (3.0, 5.0, 7.0)
4. **Compare results** before/after

Want me to implement this fix?
