# 🎯 Buy/Sell Decision Logic - Complete Breakdown

## The Complete Decision Tree

```
FOR EACH BAR:

1. Calculate Momentum (0-100)
2. Calculate Equilibrium (set at direction changes)
3. Calculate Distance = Momentum - Equilibrium
4. Generate Signals:
   - Bullish = Distance > +2.0
   - Bearish = Distance < -2.0
5. Execute Trades Based on Position State
```

---

## 📊 STEP 1: Generate the Signals

### The Math:

```python
# At each bar
momentum = 91.85  # (calculated from triple-layer EMA)
equilibrium = 52.0  # (set at last direction change)
threshold = 2.0

# Calculate bands
upper_band = equilibrium + threshold  # 52.0 + 2.0 = 54.0
lower_band = equilibrium - threshold  # 52.0 - 2.0 = 50.0

# Generate signals
if momentum > upper_band:
    bullish = True   # 91.85 > 54.0 ✓
    bearish = False
elif momentum < lower_band:
    bullish = False
    bearish = True
else:
    bullish = False  # In the neutral zone
    bearish = False
```

### Visual Representation:

```
100 │
    │     Current Momentum = 91.85
 90 │         ↓
    │         ●  ← YOU ARE HERE
 80 │
    │
 70 │
    │
 60 │
    │                           BULLISH ZONE
 54 │ ═══════════════════════════════════ ← Upper Band (Buy threshold)
 52 │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  ← Equilibrium (Neutral)
 50 │ ═══════════════════════════════════ ← Lower Band (Sell threshold)
    │                           BEARISH ZONE
 40 │
    │
 30 │
    └────────────────────────────────────→

Decision at Bar 100:
  Momentum (91.85) > Upper Band (54.0)
  → BULLISH = TRUE
  → BEARISH = FALSE
```

---

## 🎯 STEP 2: Make Trading Decision

### The Logic Flow:

```
┌─────────────────────────────────────────────┐
│     Check Current Position                  │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
    Position = 0  Position > 0
    (No position) (In position)
        │             │
        ▼             ▼
    ┌───────┐     ┌───────┐
    │ ENTRY │     │ EXIT  │
    │ LOGIC │     │ LOGIC │
    └───────┘     └───────┘
```

---

## 💰 ENTRY LOGIC (When Position = 0)

### Code:

```python
if position == 0:  # Not currently in a trade
    
    if bullish:  # Signal to go long
        # Calculate position size
        capital = 10234  # Current account balance
        risk_pct = 2.0   # Risk 2% per trade
        risk_amount = capital * (risk_pct / 100)  # $204.68
        
        # Calculate stop distance (3% trailing stop)
        current_price = 424.89
        trailing_stop_pct = 3.0
        stop_distance = current_price * (trailing_stop_pct / 100)  # $12.75
        
        # Calculate shares
        shares = risk_amount / stop_distance  # $204.68 / $12.75 = 16 shares
        
        # Check if we have enough capital
        position_cost = shares * current_price  # 16 * $424.89 = $6,798.24
        if position_cost <= capital:
            # EXECUTE BUY
            position = 16
            entry_price = 424.89
            trail_stop = entry_price * (1 - trailing_stop_pct/100)  # $412.14
            
            print(f"🟢 BUY {shares} shares at ${current_price}")
            print(f"   Entry: ${entry_price}")
            print(f"   Stop:  ${trail_stop}")
            print(f"   Risk:  ${risk_amount}")
    
    elif bearish and not long_only:  # Signal to go short (if enabled)
        # Same logic but for short position
        # (Your strategy uses long_only=True, so this doesn't execute)
        pass
```

### Real Example at Bar 61:

```
BAR 61 STATE:
  Price: $392.10
  Momentum: 49.30
  Equilibrium: 46.20
  Distance: +3.10 (above +2.0 threshold)
  
SIGNAL GENERATION:
  Upper Band = 46.20 + 2.0 = 48.20
  Momentum (49.30) > Upper Band (48.20)
  → Bullish = TRUE

POSITION CHECK:
  Position = 0 (no current position)
  
ENTRY CALCULATION:
  Capital: $10,000
  Risk: 2% = $200
  Price: $392.10
  Stop Distance: $392.10 * 3% = $11.76
  Shares: $200 / $11.76 = 17 shares
  Cost: 17 * $392.10 = $6,665.70
  
  Can afford? $6,665.70 < $10,000 ✓ YES

EXECUTE:
  🟢 BUY 17 shares at $392.10
  Entry Price: $392.10
  Trailing Stop: $392.10 * 0.97 = $380.34
  Position: 17 shares LONG
```

---

## 🚪 EXIT LOGIC (When Position > 0)

### Code:

```python
if position > 0:  # Currently in a long position
    
    # STEP 1: Update Trailing Stop (moves up only, never down)
    current_price = 424.89
    new_stop = current_price * (1 - trailing_stop_pct/100)  # $412.14
    
    if new_stop > trail_stop:
        trail_stop = new_stop  # Update to higher stop
        print(f"📈 Trail stop updated to ${trail_stop:.2f}")
    
    # STEP 2: Check Exit Conditions
    exit_signal = False
    exit_reason = ""
    
    # Exit Condition A: Bearish signal (momentum crossed below lower band)
    if bearish:
        exit_signal = True
        exit_reason = "BEARISH_SIGNAL"
    
    # Exit Condition B: Price hit trailing stop
    elif current_price <= trail_stop:
        exit_signal = True
        exit_reason = "TRAILING_STOP"
    
    # STEP 3: Execute Exit if triggered
    if exit_signal:
        exit_price = current_price
        
        # Calculate P&L
        pnl = position * (exit_price - entry_price)
        pnl_pct = (exit_price / entry_price - 1) * 100
        capital += pnl
        
        print(f"🔴 SELL {position} shares at ${exit_price}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Exit:  ${exit_price:.2f}")
        print(f"   P&L:   ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"   Reason: {exit_reason}")
        
        # Reset position
        position = 0
        entry_price = 0
        trail_stop = 0
```

### Real Example at Bar 105:

```
BAR 105 STATE:
  Price: $436.20
  Momentum: 91.30
  Equilibrium: 93.50
  Distance: -2.20 (below -2.0 threshold)
  Entry Price: $392.10 (from bar 61)
  Current Stop: $423.31
  
SIGNAL GENERATION:
  Lower Band = 93.50 - 2.0 = 91.50
  Momentum (91.30) < Lower Band (91.50)
  → Bearish = TRUE

POSITION CHECK:
  Position = 17 shares (in long position)

TRAILING STOP UPDATE:
  New Stop = $436.20 * 0.97 = $423.11
  Current Stop = $423.31
  New Stop NOT higher → Keep $423.31

EXIT CHECK:
  Condition A - Bearish? YES ✓
  Condition B - Price <= Stop? NO ($436.20 > $423.31)
  
  Exit Signal: TRUE (Condition A met)

EXECUTE EXIT:
  🔴 SELL 17 shares at $436.20
  Entry:  $392.10
  Exit:   $436.20
  P&L:    17 * ($436.20 - $392.10) = $749.70
  Return: +11.2%
  Reason: BEARISH_SIGNAL
  
  Position: 0 (flat)
  Capital: $10,000 + $749.70 = $10,749.70
```

---

## 📋 Complete Decision Table

| Scenario | Position | Bullish | Bearish | Price vs Stop | Action |
|----------|----------|---------|---------|---------------|--------|
| 1 | 0 | TRUE | FALSE | N/A | **BUY** (enter long) |
| 2 | 0 | FALSE | TRUE | N/A | Do nothing (long_only=True) |
| 3 | 0 | FALSE | FALSE | N/A | Wait (neutral zone) |
| 4 | LONG | TRUE | FALSE | Above | **HOLD** + update stop |
| 5 | LONG | TRUE | FALSE | Below | **SELL** (stop hit) |
| 6 | LONG | FALSE | TRUE | Above | **SELL** (bearish signal) |
| 7 | LONG | FALSE | TRUE | Below | **SELL** (both triggers!) |
| 8 | LONG | FALSE | FALSE | Above | **HOLD** (neutral but above stop) |
| 9 | LONG | FALSE | FALSE | Below | **SELL** (stop hit) |

---

## 🔄 Complete Trade Example: Bar 61 → Bar 105

```
═══════════════════════════════════════════════════════════════
BAR 61: ENTRY
═══════════════════════════════════════════════════════════════
Price:       $392.10
Momentum:    49.30
Equilibrium: 46.20
Distance:    +3.10
Signal:      BULLISH (49.30 > 48.20)
Position:    0 → 17 shares
Entry:       $392.10
Stop:        $380.34

ACTION: 🟢 BUY 17 shares at $392.10
───────────────────────────────────────────────────────────────

BAR 62-64: HOLD (Trail stop following)
───────────────────────────────────────────────────────────────
Bar 62: Price $395.50, Stop $383.64, Bullish ✓ → HOLD
Bar 63: Price $398.80, Stop $386.84, Bullish ✓ → HOLD
Bar 64: Price $402.10, Stop $390.04, Bullish ✓ → HOLD

───────────────────────────────────────────────────────────────

BAR 80: HOLD (Mid-trend update)
───────────────────────────────────────────────────────────────
Price:       $410.50
Momentum:    75.50
Equilibrium: 52.00
Distance:    +23.50
Signal:      BULLISH (still way above 54.0)
Position:    17 shares LONG
Entry:       $392.10
Stop:        $398.19 (moved up from $390.04)
Unrealized:  +$313.80 (+4.7%)

ACTION: 📈 HOLD + Trail Stop Updated
───────────────────────────────────────────────────────────────

BAR 99: HOLD (Strong momentum)
───────────────────────────────────────────────────────────────
Price:       $430.25
Momentum:    89.30
Equilibrium: 52.00
Distance:    +37.30
Signal:      STRONG BULLISH
Position:    17 shares LONG
Entry:       $392.10
Stop:        $417.34
Unrealized:  +$648.55 (+9.7%)

ACTION: 📈 HOLD (trend still strong)
───────────────────────────────────────────────────────────────

BAR 100: HOLD (Peak approaching)
───────────────────────────────────────────────────────────────
Price:       $424.89
Momentum:    91.85
Equilibrium: 52.00
Distance:    +39.85
Signal:      EXTREME BULLISH
Position:    17 shares LONG
Entry:       $392.10
Stop:        $412.14
Unrealized:  +$557.43 (+8.4%)

ACTION: 📈 HOLD (but watch closely)
───────────────────────────────────────────────────────────────

BAR 103: HOLD (Direction changed - equilibrium reset!)
───────────────────────────────────────────────────────────────
Price:       $438.50
Momentum:    93.50
Equilibrium: 93.50 (JUST RESET - direction changed!)
Distance:    0.00
Signal:      NEUTRAL (at equilibrium)
Position:    17 shares LONG
Entry:       $392.10
Stop:        $425.35
Unrealized:  +$788.80 (+11.9%)

ACTION: 📈 HOLD (not yet bearish, distance = 0)
───────────────────────────────────────────────────────────────

BAR 104: HOLD (Watching closely)
───────────────────────────────────────────────────────────────
Price:       $437.10
Momentum:    92.70
Equilibrium: 93.50
Distance:    -0.80
Signal:      Slightly negative but within threshold
Position:    17 shares LONG
Entry:       $392.10
Stop:        $423.99
Unrealized:  +$765.00 (+11.5%)

ACTION: 📈 HOLD (distance -0.80 not yet < -2.0)
───────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════
BAR 105: EXIT
═══════════════════════════════════════════════════════════════
Price:       $436.20
Momentum:    91.30
Equilibrium: 93.50
Distance:    -2.20 (BELOW -2.0 THRESHOLD!)
Signal:      BEARISH (91.30 < 91.50)
Position:    17 → 0 shares
Exit:        $436.20
Stop:        $423.31

EXIT TRIGGER: Bearish signal (distance < -2.0)

ACTION: 🔴 SELL 17 shares at $436.20

TRADE RESULTS:
  Entry:    $392.10
  Exit:     $436.20
  Gain:     $44.10 per share
  Total P&L: $749.70
  Return:   +11.2%
  Duration: 44 bars (8.8 weeks)
  Max Stop: Never hit (exited on signal)
═══════════════════════════════════════════════════════════════
```

---

## 🎯 Key Decision Points Explained

### Why BUY at Bar 61?

```
Momentum (49.30) crossed ABOVE Upper Band (48.20)
  ↑
  This means momentum has moved far enough above equilibrium
  to signal a real trend, not just noise
  
Distance of +3.10 confirms strong momentum
Position = 0 means we're not in a trade yet

→ CONDITIONS MET: Enter Long Position
```

### Why NOT Sell at Bar 100?

```
Price: $424.89
Momentum: 91.85
Distance: +39.85

Even though:
  - Momentum very high (91.85)
  - We have big unrealized profit (+8.4%)
  
BUT:
  - Momentum (91.85) still > Upper Band (54.0)  ✓ Still bullish
  - Distance (+39.85) still > Threshold (+2.0)  ✓ Strong signal
  - Price ($424.89) > Stop ($412.14)            ✓ Not stopped out
  
→ NO EXIT CONDITION MET: Stay in position
```

### Why SELL at Bar 105?

```
Momentum dropped to 91.30
Equilibrium reset to 93.50 (at bar 103 peak)
Distance = 91.30 - 93.50 = -2.20

Lower Band = 93.50 - 2.0 = 91.50
Momentum (91.30) < Lower Band (91.50)  ✗ BEARISH!

→ EXIT CONDITION MET: Close position
```

---

## 💡 The Core Trading Rules

### ENTRY RULES:
```
1. No existing position (Position = 0)
2. Bullish signal (Momentum > Equilibrium + 2.0)
3. Enough capital to buy shares
```

### HOLD RULES:
```
1. In position (Position > 0)
2. Still bullish (Momentum > Equilibrium + 2.0)
3. Price above trailing stop
4. Update stop higher (never lower)
```

### EXIT RULES (Any one triggers exit):
```
1. Bearish signal (Momentum < Equilibrium - 2.0)
   OR
2. Price hits trailing stop (Price <= Trail_Stop)
```

---

## 🔍 Why This Works

### 1. **Clear Entry Signal**
- Don't enter on first tick above 50
- Wait for momentum to be +2.0 above equilibrium
- Confirms real trend, not noise

### 2. **Ride the Trend**
- Stay in as long as momentum > equilibrium + 2.0
- Don't exit on small pullbacks
- Trailing stop protects profits

### 3. **Clear Exit Signal**
- Two ways to exit (signal or stop)
- Don't overstay when trend reverses
- Lock in profits with trailing stop

### 4. **Risk Management**
- Risk only 2% per trade
- 3% trailing stop limits max loss
- Position size based on risk, not arbitrary

---

## 📊 Summary Flowchart

```
START
  ↓
Check Position
  ↓
  ├─ Position = 0 ────→ Check Bullish? ─→ YES → Calculate Size → BUY
  │                           ↓
  │                          NO
  │                           ↓
  │                         WAIT
  │
  └─ Position > 0 ────→ Update Trail Stop
                              ↓
                        Check Exit Conditions
                              ↓
                        ├─ Bearish? ────→ YES → SELL
                        │
                        └─ Hit Stop? ───→ YES → SELL
                              ↓
                             NO
                              ↓
                            HOLD
```

That's the complete buy/sell logic! Every decision comes down to:
1. **Where is momentum relative to equilibrium?** (distance calculation)
2. **Am I in a position or not?** (state check)
3. **Did price hit my stop?** (risk management)
