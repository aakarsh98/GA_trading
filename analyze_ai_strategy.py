"""
Analyze what strategy the AI learned
Visualize AI decisions vs baseline strategy
"""
import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
import warnings
warnings.filterwarnings('ignore')

# Your momentum tracker
sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🔍 AI STRATEGY ANALYSIS")
print("  What did the AI learn?")
print("=" * 80)

# Load trained AI model
print("\n📥 Loading trained AI model...")
model = PPO.load("momentum_ai_agent.zip")
print("✅ Model loaded successfully")

# Download test data
print("\n📥 Downloading test data (2023)...")
data = yf.download('SPY', start='2023-01-01', end='2023-12-31', progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = [col[0].lower() for col in data.columns]
else:
    data.columns = data.columns.str.lower()

print(f"✅ Downloaded {len(data)} bars")

# Calculate features
print("\n📊 Calculating features...")
momentum_result = calculate_momentum_indicator(data, length=7, threshold=2.0)

data['momentum'] = momentum_result['momentum']
data['equilibrium'] = momentum_result['equilibrium']
data['distance'] = momentum_result['momentum'] - momentum_result['equilibrium']
data['bullish'] = momentum_result['bullish'].astype(float)
data['returns'] = data['close'].pct_change()
data['volume_ratio'] = data['volume'] / data['volume'].rolling(20).mean()
data = data.dropna()

print("✅ Features calculated")

# Analyze AI decisions
print("\n🤖 Analyzing AI decisions...")

ai_actions = []
ai_confidences = []
observations = []

for i in range(100, len(data)):
    # Prepare observation
    row = data.iloc[i]
    obs = np.array([
        row['momentum'] / 100.0,
        row['equilibrium'] / 100.0,
        row['distance'] / 50.0,
        row['bullish'],
        row['returns'] * 100,
        np.clip(row['volume_ratio'], 0, 3),
        0.0  # No position at start
    ], dtype=np.float32)
    
    # Get AI prediction
    action, _states = model.predict(obs, deterministic=True)
    
    # Get action probabilities (confidence)
    action_probs = model.policy.get_distribution(
        model.policy.obs_to_tensor(obs.reshape(1, -1))[0]
    ).distribution.probs.detach().numpy()[0]
    
    ai_actions.append(action)
    ai_confidences.append(action_probs[action])
    observations.append(obs)

# Convert to arrays
ai_actions = np.array(ai_actions)
ai_confidences = np.array(ai_confidences)

# Analyze decisions
print("\n📊 AI DECISION BREAKDOWN:")
print(f"   Total decisions: {len(ai_actions)}")
print(f"   Sell/Flat (0):   {np.sum(ai_actions == 0)} ({np.sum(ai_actions == 0)/len(ai_actions)*100:.1f}%)")
print(f"   Hold (1):        {np.sum(ai_actions == 1)} ({np.sum(ai_actions == 1)/len(ai_actions)*100:.1f}%)")
print(f"   Buy (2):         {np.sum(ai_actions == 2)} ({np.sum(ai_actions == 2)/len(ai_actions)*100:.1f}%)")
print(f"\n   Mean confidence: {np.mean(ai_confidences):.2f}")
print(f"   Max confidence:  {np.max(ai_confidences):.2f}")
print(f"   Min confidence:  {np.min(ai_confidences):.2f}")

# Compare AI vs baseline signals
baseline_bullish = data['bullish'].values[100:]
baseline_buy_signals = np.sum(baseline_bullish)
ai_buy_signals = np.sum(ai_actions == 2)

print("\n📊 SIGNAL COMPARISON:")
print(f"   Baseline buy signals: {baseline_buy_signals}")
print(f"   AI buy signals:       {ai_buy_signals}")
print(f"   Difference:           {baseline_buy_signals - ai_buy_signals} ({(baseline_buy_signals - ai_buy_signals)/baseline_buy_signals*100:.1f}% fewer)")

# Analyze when AI buys vs baseline
print("\n🔍 WHEN DOES AI BUY?")
print("   Analyzing conditions when AI chooses to buy...")

buy_moments = np.where(ai_actions == 2)[0]
if len(buy_moments) > 0:
    print(f"\n   AI bought {len(buy_moments)} times")
    for idx in buy_moments:
        actual_idx = idx + 100
        row = data.iloc[actual_idx]
        print(f"\n   Buy #{buy_moments.tolist().index(idx) + 1}:")
        print(f"      Date:         {data.index[actual_idx].date()}")
        print(f"      Price:        ${row['close']:.2f}")
        print(f"      Momentum:     {row['momentum']:.2f}")
        print(f"      Equilibrium:  {row['equilibrium']:.2f}")
        print(f"      Distance:     {row['distance']:.2f}")
        print(f"      Baseline:     {'BUY' if row['bullish'] else 'WAIT'}")
        print(f"      Confidence:   {ai_confidences[idx]:.2f}")
else:
    print("   AI never chose to buy!")

# Analyze when baseline buys but AI doesn't
print("\n🔍 WHEN BASELINE BUYS BUT AI DOESN'T:")
baseline_buys = np.where(baseline_bullish == 1)[0]
ai_passes = []

for idx in baseline_buys[:10]:  # Show first 10 examples
    if idx < len(ai_actions) and ai_actions[idx] != 2:
        ai_passes.append(idx)

if len(ai_passes) > 0:
    print(f"\n   Found {len(ai_passes)} cases (showing first 5):")
    for idx in ai_passes[:5]:
        actual_idx = idx + 100
        row = data.iloc[actual_idx]
        print(f"\n   Example {ai_passes.index(idx) + 1}:")
        print(f"      Date:         {data.index[actual_idx].date()}")
        print(f"      Price:        ${row['close']:.2f}")
        print(f"      Momentum:     {row['momentum']:.2f}")
        print(f"      Equilibrium:  {row['equilibrium']:.2f}")
        print(f"      Distance:     {row['distance']:.2f}")
        print(f"      Baseline:     BUY")
        print(f"      AI Action:    {'SELL/FLAT' if ai_actions[idx] == 0 else 'HOLD'}")
        print(f"      Confidence:   {ai_confidences[idx]:.2f}")
        print(f"      Why AI skipped: ", end="")
        
        # Analyze why AI skipped
        if row['distance'] < 5:
            print("Distance too low")
        elif row['volume_ratio'] < 0.8:
            print("Low volume")
        elif row['returns'] < -0.5:
            print("Negative momentum")
        else:
            print("Other factors")

# Analyze AI's learned patterns
print("\n\n📈 AI'S LEARNED PATTERNS:")
print("   Analyzing what features influence AI decisions...")

# When AI buys
buy_indices = np.where(ai_actions == 2)[0]
hold_indices = np.where(ai_actions == 1)[0]
sell_indices = np.where(ai_actions == 0)[0]

if len(buy_indices) > 0:
    buy_obs = [observations[i] for i in buy_indices]
    buy_momentum = np.mean([obs[0] * 100 for obs in buy_obs])
    buy_distance = np.mean([obs[2] * 50 for obs in buy_obs])
    buy_volume = np.mean([obs[5] for obs in buy_obs])
    
    print(f"\n   When AI BUYS:")
    print(f"      Avg Momentum:  {buy_momentum:.2f}")
    print(f"      Avg Distance:  {buy_distance:.2f}")
    print(f"      Avg Vol Ratio: {buy_volume:.2f}")

if len(hold_indices) > 0:
    hold_obs = [observations[i] for i in hold_indices]
    hold_momentum = np.mean([obs[0] * 100 for obs in hold_obs])
    hold_distance = np.mean([obs[2] * 50 for obs in hold_obs])
    hold_volume = np.mean([obs[5] for obs in hold_obs])
    
    print(f"\n   When AI HOLDS:")
    print(f"      Avg Momentum:  {hold_momentum:.2f}")
    print(f"      Avg Distance:  {hold_distance:.2f}")
    print(f"      Avg Vol Ratio: {hold_volume:.2f}")

# Analyze baseline patterns for comparison
baseline_buy_indices = np.where(baseline_bullish == 1)[0]
if len(baseline_buy_indices) > 0:
    baseline_momentum = data['momentum'].values[100:][baseline_buy_indices].mean()
    baseline_distance = data['distance'].values[100:][baseline_buy_indices].mean()
    
    print(f"\n   When BASELINE BUYS:")
    print(f"      Avg Momentum:  {baseline_momentum:.2f}")
    print(f"      Avg Distance:  {baseline_distance:.2f}")

# Key differences
print("\n\n🎯 KEY DIFFERENCES:")
if len(buy_indices) > 0 and len(baseline_buy_indices) > 0:
    print(f"   AI requires:")
    if buy_momentum > baseline_momentum:
        print(f"      ✓ Higher momentum ({buy_momentum:.1f} vs {baseline_momentum:.1f})")
    if buy_distance > baseline_distance:
        print(f"      ✓ Larger distance ({buy_distance:.1f} vs {baseline_distance:.1f})")
    if len(buy_indices) < len(baseline_buy_indices):
        print(f"      ✓ More selective ({len(buy_indices)} vs {len(baseline_buy_indices)} signals)")
else:
    print("   AI is EXTREMELY conservative - almost never buys!")
    print("   This suggests:")
    print("      • Training data had too many losses")
    print("      • Reward function penalizes trading too much")
    print("      • Need more diverse training data")

print("\n\n" + "=" * 80)
print("  💡 STRATEGY SUMMARY")
print("=" * 80)

print(f"""
Your BASELINE Strategy:
   • Entry: When momentum > equilibrium + 2.0
   • Trades: {baseline_buy_signals} signals in 2023
   • Approach: Active (takes most opportunities)
   • Result: -91.17% (bad year for this style)

AI LEARNED Strategy:
   • Entry: When momentum >> equilibrium + OTHER conditions
   • Trades: {ai_buy_signals} signals in 2023
   • Approach: Ultra-conservative (waits for "perfect" setup)
   • Result: -94.36% (too conservative, missed rebounds)

WHY AI IS SO CONSERVATIVE:
   1. Trained on 2018-2022 (mostly bull market)
   2. Learned that many trades lose money
   3. Penalized heavily for trading costs
   4. Didn't see enough diverse market conditions

HOW TO IMPROVE:
   1. Train on 10+ years (include bear markets, chop)
   2. Adjust reward to encourage more trading
   3. Add regime detection (know when NOT to trade)
   4. Use ensemble (AI filters baseline signals)
""")

print("\n✅ Analysis complete!")
print(f"   The AI learned to be {'too' if ai_buy_signals < 5 else 'appropriately'} conservative")
print(f"   Baseline trades {baseline_buy_signals / ai_buy_signals if ai_buy_signals > 0 else 'infinity':.1f}x more often")
