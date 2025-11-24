"""
Train AI Agent using FinRL + Reversal Momentum Strategy
This script trains a PPO agent on REVERSAL strategy:
- BUY when momentum is OVERSOLD (0-25)
- SELL when momentum is OVERBOUGHT (75-100)
- Using 10 YEARS of historical data (2013-2023)
"""
import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import FinRL
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
import gymnasium as gym
from gymnasium import spaces

# Your momentum tracker
sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🤖 AI AGENT TRAINING - REVERSAL MOMENTUM STRATEGY")
print("  📊 Buy Oversold (0-25) | Sell Overbought (75-100)")
print("  📅 Training Period: 10 YEARS (2013-2023)")
print("=" * 80)

# ==============================================================================
# STEP 1: CREATE CUSTOM TRADING ENVIRONMENT
# ==============================================================================

class MomentumTradingEnv(gym.Env):
    """
    Custom trading environment using your momentum tracker
    """
    metadata = {'render.modes': ['human']}
    
    def __init__(self, df, initial_capital=10000, transaction_cost=0.001):
        super(MomentumTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        
        # Calculate all features
        print("  📊 Calculating momentum features...")
        momentum_result = calculate_momentum_indicator(df, length=7, threshold=2.0)
        
        self.df['momentum'] = momentum_result['momentum']
        self.df['equilibrium'] = momentum_result['equilibrium']
        self.df['distance'] = momentum_result['momentum'] - momentum_result['equilibrium']
        self.df['bullish'] = momentum_result['bullish'].astype(float)
        
        # Additional features
        self.df['returns'] = self.df['close'].pct_change()
        self.df['volume_ratio'] = self.df['volume'] / self.df['volume'].rolling(20).mean()
        
        self.df = self.df.dropna().reset_index(drop=True)
        
        # Number of features
        self.feature_dim = 7  # [momentum, equilibrium, distance, bullish, returns, volume_ratio, position]
        
        # Action space: [0, 1, 2] = [sell/flat, hold, buy]
        self.action_space = spaces.Discrete(3)
        
        # Observation space: normalized features
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(self.feature_dim,), 
            dtype=np.float32
        )
        
        # Trading state
        self.current_step = 100  # Start after enough history
        self.capital = initial_capital
        self.position = 0  # 0 = no position, 1 = long
        self.entry_price = 0
        self.total_trades = 0
        self.winning_trades = 0
        
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        self.current_step = 100
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.total_trades = 0
        self.winning_trades = 0
        
        return self._get_observation(), {}
    
    def _get_observation(self):
        """Get current state observation"""
        row = self.df.iloc[self.current_step]
        
        # Normalize features
        obs = np.array([
            row['momentum'] / 100.0,  # Normalize to [0, 1]
            row['equilibrium'] / 100.0,
            row['distance'] / 50.0,  # Normalize distance
            row['bullish'],
            row['returns'] * 100,  # Percentage returns
            np.clip(row['volume_ratio'], 0, 3),  # Clip volume ratio
            float(self.position)  # Current position state
        ], dtype=np.float32)
        
        return obs
    
    def step(self, action):
        """Execute one trading step"""
        current_price = self.df.iloc[self.current_step]['close']
        
        # Execute action
        reward = 0
        done = False
        
        # Action: 0=sell/flat, 1=hold, 2=buy
        if action == 2 and self.position == 0:
            # BUY
            shares = int((self.capital * 0.95) / current_price)
            if shares > 0:
                cost = shares * current_price * (1 + self.transaction_cost)
                if cost <= self.capital:
                    self.position = 1
                    self.entry_price = current_price
                    self.capital -= cost
                    self.total_trades += 1
                    reward = -0.01  # Small negative reward for trading cost
        
        elif action == 0 and self.position == 1:
            # SELL
            proceeds = (current_price / self.entry_price - 1) * self.entry_price * \
                      (self.capital / self.entry_price) * (1 - self.transaction_cost)
            
            pnl_pct = (current_price / self.entry_price - 1) * 100
            
            if pnl_pct > 0:
                self.winning_trades += 1
                reward = pnl_pct / 10.0  # Positive reward for profit
            else:
                reward = pnl_pct / 5.0  # Larger negative reward for loss
            
            self.capital += proceeds
            self.position = 0
            self.entry_price = 0
        
        elif action == 1:
            # HOLD
            if self.position == 1:
                # Reward for holding profitable position
                unrealized_pnl = (current_price / self.entry_price - 1) * 100
                reward = unrealized_pnl * 0.01  # Small reward for unrealized gains
            else:
                reward = 0
        
        # Move to next step
        self.current_step += 1
        
        # Check if done
        if self.current_step >= len(self.df) - 1:
            done = True
            # Final close of position if open
            if self.position == 1:
                final_pnl = (current_price / self.entry_price - 1) * 100
                reward += final_pnl / 10.0
                self.capital += (current_price / self.entry_price - 1) * self.entry_price * \
                               (self.capital / self.entry_price)
        
        # Get next observation
        obs = self._get_observation() if not done else np.zeros(self.feature_dim, dtype=np.float32)
        
        # Additional info
        info = {
            'capital': self.capital,
            'position': self.position,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades
        }
        
        return obs, reward, done, False, info
    
    def render(self, mode='human'):
        """Render environment state"""
        profit = self.capital - self.initial_capital
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        print(f"Step: {self.current_step}, Capital: ${self.capital:.2f}, " +
              f"P&L: ${profit:.2f}, Trades: {self.total_trades}, Win Rate: {win_rate:.1f}%")


# ==============================================================================
# STEP 2: PREPARE DATA - 10 YEARS OF TRAINING DATA
# ==============================================================================

print("\n📥 STEP 1: Downloading 10 YEARS of training data...")
ticker = 'SPY'
train_start = '2013-01-01'  # 10 years of data
train_end = '2023-12-31'

train_data = yf.download(ticker, start=train_start, end=train_end, progress=False)

# Standardize columns
if isinstance(train_data.columns, pd.MultiIndex):
    train_data.columns = [col[0].lower() for col in train_data.columns]
else:
    train_data.columns = train_data.columns.str.lower()

print(f"✅ Training data: {len(train_data)} bars ({train_start} to {train_end}) - 10 YEARS")

# Test data - use 2024-2025 for out-of-sample testing
print("\n📥 STEP 2: Downloading test data...")
test_start = '2024-01-01'
test_end = '2025-11-23'

test_data = yf.download(ticker, start=test_start, end=test_end, progress=False)

if isinstance(test_data.columns, pd.MultiIndex):
    test_data.columns = [col[0].lower() for col in test_data.columns]
else:
    test_data.columns = test_data.columns.str.lower()

print(f"✅ Test data: {len(test_data)} bars ({test_start} to {test_end})")

# ==============================================================================
# STEP 3: CREATE ENVIRONMENTS
# ==============================================================================

print("\n🏗️  STEP 3: Creating training environment...")
train_env = MomentumTradingEnv(train_data, initial_capital=10000)
print(f"✅ Training environment created")
print(f"   Observation space: {train_env.observation_space}")
print(f"   Action space: {train_env.action_space}")

# Wrap in DummyVecEnv for stable-baselines3
vec_train_env = DummyVecEnv([lambda: train_env])

# ==============================================================================
# STEP 4: TRAIN AI AGENT
# ==============================================================================

print("\n🤖 STEP 4: Training AI agent with PPO...")
print("   Algorithm: Proximal Policy Optimization (PPO)")
print("   Policy: Multi-Layer Perceptron (MLP)")
print("   Training timesteps: 50,000")
print("   This will take 5-15 minutes...")

# PPO hyperparameters
model = PPO(
    "MlpPolicy",
    vec_train_env,
    learning_rate=0.0003,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    verbose=1
)

print("\n🚀 Training started...")
print("=" * 80)

# Train the model
model.learn(total_timesteps=50000, progress_bar=False)

print("=" * 80)
print("✅ Training complete!")

# Save model
model_path = "momentum_ai_agent.zip"
model.save(model_path)
print(f"✅ Model saved to: {model_path}")

# ==============================================================================
# STEP 5: TEST TRAINED AGENT
# ==============================================================================

print("\n📊 STEP 5: Testing trained agent...")

# Create test environment
test_env = MomentumTradingEnv(test_data, initial_capital=10000)

# Test AI agent
obs, _ = test_env.reset()
done = False
ai_equity = [10000]

while not done:
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, done, truncated, info = test_env.step(action)
    ai_equity.append(info['capital'])

ai_final = info['capital']
ai_return = (ai_final / 10000 - 1) * 100
ai_trades = info['total_trades']
ai_win_rate = (info['winning_trades'] / ai_trades * 100) if ai_trades > 0 else 0

print(f"\n🤖 AI AGENT RESULTS (2023):")
print(f"   Initial Capital:  $10,000.00")
print(f"   Final Capital:    ${ai_final:,.2f}")
print(f"   Total Return:     {ai_return:.2f}%")
print(f"   Total Trades:     {ai_trades}")
print(f"   Winning Trades:   {info['winning_trades']}")
print(f"   Win Rate:         {ai_win_rate:.1f}%")

# ==============================================================================
# STEP 6: COMPARE WITH BASELINE
# ==============================================================================

print("\n📊 STEP 6: Running baseline strategy for comparison...")

def baseline_strategy(df):
    """REVERSAL momentum strategy - OPTIONS MODE
    Buy CALLS when oversold (≤25), Buy PUTS when overbought (≥75)
    Can switch directions on each signal
    """
    momentum_result = calculate_momentum_indicator(df, length=7, threshold=2.0)
    
    capital = 10000
    position = 0
    position_side = None
    entry_price = 0
    trades = 0
    winning = 0
    equity = [10000]
    
    # Track previous signals to detect new ones
    prev_bullish = False
    prev_bearish = False
    
    for i in range(100, len(df)):
        current_price = df.iloc[i]['close']
        
        # New BULLISH signal (oversold - buy CALLS)
        if momentum_result['bullish'][i] and not prev_bullish:
            # Close existing PUT position if any
            if position > 0 and position_side == 'short':
                pnl = position * (entry_price - current_price)
                capital += pnl
                if pnl > 0:
                    winning += 1
                trades += 1
                position = 0
            
            # Open CALL position
            shares = int((capital * 0.95) / current_price)
            if shares > 0:
                position = shares
                entry_price = current_price
                capital -= shares * current_price * 1.001
                position_side = 'long'
        
        # New BEARISH signal (overbought - buy PUTS)
        elif momentum_result['bearish'][i] and not prev_bearish:
            # Close existing CALL position if any
            if position > 0 and position_side == 'long':
                pnl = position * (current_price - entry_price)
                capital += pnl
                if pnl > 0:
                    winning += 1
                trades += 1
                position = 0
            
            # Open PUT position
            shares = int((capital * 0.95) / current_price)
            if shares > 0:
                position = shares
                entry_price = current_price
                capital -= shares * current_price * 1.001
                position_side = 'short'
        
        prev_bullish = momentum_result['bullish'][i]
        prev_bearish = momentum_result['bearish'][i]
        
        # Track equity
        if position > 0:
            if position_side == 'long':
                equity.append(capital + position * current_price)
            else:  # short/put position
                equity.append(capital + position * (2 * entry_price - current_price))
        else:
            equity.append(capital)
    
    return {
        'capital': capital,
        'return': (capital / 10000 - 1) * 100,
        'trades': trades,
        'winning': winning,
        'equity': equity
    }

baseline_result = baseline_strategy(test_data)

print(f"\n📈 BASELINE STRATEGY RESULTS (2023):")
print(f"   Initial Capital:  $10,000.00")
print(f"   Final Capital:    ${baseline_result['capital']:,.2f}")
print(f"   Total Return:     {baseline_result['return']:.2f}%")
print(f"   Total Trades:     {baseline_result['trades']}")
print(f"   Winning Trades:   {baseline_result['winning']}")
win_rate_baseline = (baseline_result['winning'] / baseline_result['trades'] * 100) if baseline_result['trades'] > 0 else 0
print(f"   Win Rate:         {win_rate_baseline:.1f}%")

# ==============================================================================
# STEP 7: COMPARISON & ANALYSIS
# ==============================================================================

print("\n" + "=" * 80)
print("  📊 FINAL COMPARISON")
print("=" * 80)

improvement = ai_return - baseline_result['return']
improvement_pct = (improvement / baseline_result['return'] * 100) if baseline_result['return'] != 0 else 0

print(f"""
┌─────────────────────────┬──────────────┬──────────────┬─────────────┐
│ Metric                  │  Baseline    │  AI Agent    │  Change     │
├─────────────────────────┼──────────────┼──────────────┼─────────────┤
│ Total Return            │  {baseline_result['return']:>6.2f}%     │  {ai_return:>6.2f}%     │  {improvement:>+6.2f}%   │
│ Final Capital           │  ${baseline_result['capital']:>9,.2f} │  ${ai_final:>9,.2f} │  ${ai_final - baseline_result['capital']:>+8,.2f} │
│ Total Trades            │  {baseline_result['trades']:>10}   │  {ai_trades:>10}   │  {ai_trades - baseline_result['trades']:>+10}   │
│ Win Rate                │  {win_rate_baseline:>7.1f}%    │  {ai_win_rate:>7.1f}%    │  {ai_win_rate - win_rate_baseline:>+7.1f}%  │
└─────────────────────────┴──────────────┴──────────────┴─────────────┘

🎯 AI IMPROVEMENT: {improvement_pct:+.1f}%
""")

if improvement > 0:
    print("✅ AI agent OUTPERFORMED baseline strategy!")
    print(f"   Extra profit: ${ai_final - baseline_result['capital']:,.2f}")
elif improvement < -5:
    print("⚠️  AI agent underperformed. Consider:")
    print("   - More training timesteps (100,000+)")
    print("   - Different hyperparameters")
    print("   - More training data (5+ years)")
else:
    print("📊 AI agent performed similarly to baseline")
    print("   This is good for a first training run!")

print("\n" + "=" * 80)
print("  ✅ TRAINING COMPLETE!")
print("=" * 80)

print(f"""
📁 Files Created:
   • {model_path} - Trained AI model

🚀 Next Steps:
   1. Test on more recent data (2024-2025)
   2. Fine-tune hyperparameters
   3. Train with more timesteps (100k-500k)
   4. Deploy to paper trading

💡 Tips:
   - AI needs more data to learn well (try 5-10 years)
   - Retrain monthly on new data
   - Combine AI with your momentum signals for best results
   
🤖 To use the trained model:
   from stable_baselines3 import PPO
   model = PPO.load("{model_path}")
   action, _states = model.predict(observation)
""")
