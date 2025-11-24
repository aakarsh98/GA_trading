# 🤖 FinRL Setup Guide - AI-Based Automated Trading

## What is FinRL?

**FinRL** (Financial Reinforcement Learning) is a framework for training AI agents to trade automatically using:
- **Deep Reinforcement Learning** (DRL) - Agents learn optimal trading strategies
- **Multiple algorithms** - PPO, A2C, SAC, TD3, DDPG
- **Real market data** - Integrates with yfinance, Alpaca, etc.
- **Backtesting** - Test strategies before live trading

---

## 🎯 What FinRL Can Do For You

### 1. **Train AI Agents** to:
- Learn when to buy/sell automatically
- Adapt to changing market conditions
- Optimize position sizing
- Manage risk dynamically

### 2. **Use Your Momentum Tracker** as:
- A custom indicator/feature for the AI
- Initial signal generator
- Pre-filter before AI decisions

### 3. **Automate Trading**:
- Connect to Alpaca/Interactive Brokers
- Execute trades automatically
- Monitor positions 24/7
- Rebalance portfolio

---

## 📋 Installation Steps

### Step 1: Install FinRL

```bash
cd "/Users/aakarshraj/GG_ Script"

# Install FinRL and dependencies
pip3 install finrl

# Or install specific version
pip3 install finrl==0.3.8
```

### Step 2: Install Additional Dependencies

```bash
# Core ML libraries
pip3 install stable-baselines3
pip3 install gym
pip3 install matplotlib
pip3 install empyrical

# Data sources
pip3 install yfinance
pip3 install alpaca-trade-api
pip3 install wrds

# Optional: GPU support (if you have Apple Silicon)
pip3 install torch torchvision
```

### Step 3: Verify Installation

```bash
python3 -c "import finrl; print(f'FinRL version: {finrl.__version__}')"
```

---

## 🚀 Quick Start Example

### Example 1: Train a Simple Trading Agent

```python
"""
Simple FinRL example - Train AI to trade using your momentum
"""
import pandas as pd
import numpy as np
from finrl.meta.preprocessor.yahoodownloader import YahooDownloader
from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
from finrl.agents.stablebaselines3.models import DRLAgent
from finrl.config import INDICATORS

# Import your momentum tracker
import sys
sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

# 1. Download data
ticker_list = ['SPY', 'QQQ', 'AAPL']
start_date = '2020-01-01'
end_date = '2023-12-31'

df = YahooDownloader(
    start_date=start_date,
    end_date=end_date,
    ticker_list=ticker_list
).fetch_data()

# 2. Add your momentum indicator as a feature
def add_momentum_feature(data):
    """Add your momentum tracker to the data"""
    momentum_values = []
    
    for ticker in ticker_list:
        ticker_data = data[data['tic'] == ticker].copy()
        
        # Calculate your momentum
        result = calculate_momentum_indicator(ticker_data, length=7, threshold=2.0)
        ticker_data['momentum'] = result['momentum']
        ticker_data['equilibrium'] = result['equilibrium']
        ticker_data['bullish'] = result['bullish'].astype(int)
        
        momentum_values.append(ticker_data)
    
    return pd.concat(momentum_values, ignore_index=True)

df = add_momentum_feature(df)

# 3. Create trading environment
stock_dimension = len(ticker_list)
state_space = 1 + 2 * stock_dimension + len(['momentum', 'equilibrium', 'bullish']) * stock_dimension

env_kwargs = {
    "hmax": 100,  # Max shares to trade
    "initial_amount": 100000,
    "buy_cost_pct": 0.001,
    "sell_cost_pct": 0.001,
    "state_space": state_space,
    "stock_dim": stock_dimension,
    "tech_indicator_list": ['momentum', 'equilibrium', 'bullish'],
    "action_space": stock_dimension,
    "reward_scaling": 1e-4
}

e_train_gym = StockTradingEnv(df=df, **env_kwargs)

# 4. Train agent using PPO (Proximal Policy Optimization)
agent = DRLAgent(env=e_train_gym)

PPO_PARAMS = {
    "n_steps": 2048,
    "ent_coef": 0.01,
    "learning_rate": 0.00025,
    "batch_size": 128,
}

model_ppo = agent.get_model("ppo", model_kwargs=PPO_PARAMS)

# Train for 50,000 timesteps
trained_ppo = agent.train_model(
    model=model_ppo, 
    tb_log_name='ppo',
    total_timesteps=50000
)

# 5. Save the trained model
trained_ppo.save("momentum_ai_agent.zip")

print("✅ AI agent trained and saved!")
```

---

## 🔧 Integration with Your Momentum Tracker

### Strategy: Use Momentum + AI

```python
"""
Hybrid Strategy: Your momentum tracker + FinRL AI
"""

class MomentumAIStrategy:
    def __init__(self, model_path):
        # Load trained AI model
        from stable_baselines3 import PPO
        self.ai_model = PPO.load(model_path)
        
        # Your momentum tracker
        from actual_momentum_tracker import calculate_momentum_indicator
        self.momentum_calc = calculate_momentum_indicator
    
    def get_signal(self, market_data):
        """
        Combined decision:
        1. Your momentum tracker identifies momentum bursts
        2. AI decides optimal position size and timing
        """
        # Calculate momentum
        momentum_result = self.momentum_calc(market_data)
        
        # Get AI prediction
        state = self.prepare_state(market_data, momentum_result)
        action, _states = self.ai_model.predict(state)
        
        return {
            'momentum_signal': momentum_result['bullish'][-1],
            'ai_action': action,
            'confidence': self.calculate_confidence(action)
        }
    
    def prepare_state(self, data, momentum):
        """Prepare state for AI model"""
        return np.concatenate([
            [data['close'].iloc[-1]],  # Current price
            [momentum['momentum'][-1]],  # Your momentum
            [momentum['equilibrium'][-1]],  # Your equilibrium
            [1.0 if momentum['bullish'][-1] else 0.0]  # Your signal
        ])
    
    def calculate_confidence(self, action):
        """Calculate confidence in AI action"""
        return abs(action[0])  # Higher = more confident

# Usage
strategy = MomentumAIStrategy('momentum_ai_agent.zip')

# Get trading signal
signal = strategy.get_signal(current_market_data)

if signal['momentum_signal'] and signal['confidence'] > 0.7:
    print("🟢 STRONG BUY - Both momentum and AI agree!")
elif signal['momentum_signal']:
    print("🟡 WEAK BUY - Momentum says yes, AI uncertain")
else:
    print("🔴 NO TRADE - No momentum signal")
```

---

## 🎓 FinRL Algorithms Comparison

| Algorithm | Best For | Speed | Stability | Use Case |
|-----------|----------|-------|-----------|----------|
| **PPO** | Beginners, stable learning | Medium | High | General trading |
| **A2C** | Fast training | Fast | Medium | Quick prototyping |
| **SAC** | Continuous actions | Medium | High | Portfolio optimization |
| **TD3** | Noisy environments | Medium | Medium | High-frequency trading |
| **DDPG** | Simple continuous control | Fast | Low | Basic strategies |

**Recommendation for your momentum strategy: PPO**
- Stable learning
- Works well with discrete signals (buy/sell/hold)
- Good balance of exploration vs exploitation

---

## 📊 Complete Example: Automated Trading System

```python
"""
Complete automated trading system with FinRL
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

# FinRL imports
from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
from finrl.agents.stablebaselines3.models import DRLAgent
from stable_baselines3 import PPO

# Your momentum tracker
from actual_momentum_tracker import calculate_momentum_indicator

class AutomatedTradingSystem:
    def __init__(self, tickers, initial_capital=100000):
        self.tickers = tickers
        self.capital = initial_capital
        self.model = None
        self.positions = {}
        
    def download_data(self, start_date, end_date):
        """Download historical data"""
        data = yf.download(self.tickers, start=start_date, end=end_date)
        return data
    
    def prepare_features(self, data):
        """Add momentum features"""
        result = calculate_momentum_indicator(data, length=7, threshold=2.0)
        
        data['momentum'] = result['momentum']
        data['equilibrium'] = result['equilibrium']
        data['momentum_signal'] = result['bullish'].astype(int)
        data['distance'] = result['momentum'] - result['equilibrium']
        
        return data
    
    def train_ai_agent(self, training_data, timesteps=100000):
        """Train RL agent"""
        print("🤖 Training AI agent...")
        
        # Create environment
        env_kwargs = {
            "hmax": 100,
            "initial_amount": self.capital,
            "buy_cost_pct": 0.001,
            "sell_cost_pct": 0.001,
            "tech_indicator_list": ['momentum', 'equilibrium', 'momentum_signal', 'distance'],
        }
        
        env = StockTradingEnv(df=training_data, **env_kwargs)
        
        # Train PPO agent
        agent = DRLAgent(env=env)
        model = agent.get_model("ppo")
        self.model = agent.train_model(model=model, total_timesteps=timesteps)
        
        print("✅ Training complete!")
        return self.model
    
    def backtest(self, test_data):
        """Backtest the trained agent"""
        print("📊 Running backtest...")
        
        env_kwargs = {
            "hmax": 100,
            "initial_amount": self.capital,
            "buy_cost_pct": 0.001,
            "sell_cost_pct": 0.001,
            "tech_indicator_list": ['momentum', 'equilibrium', 'momentum_signal', 'distance'],
        }
        
        env = StockTradingEnv(df=test_data, **env_kwargs)
        
        # Run backtest
        obs = env.reset()
        done = False
        equity_curve = [self.capital]
        
        while not done:
            action, _states = self.model.predict(obs)
            obs, rewards, done, info = env.step(action)
            equity_curve.append(env.state_memory[-1][0])
        
        final_value = equity_curve[-1]
        total_return = (final_value / self.capital - 1) * 100
        
        print(f"✅ Backtest complete!")
        print(f"   Initial: ${self.capital:,.2f}")
        print(f"   Final: ${final_value:,.2f}")
        print(f"   Return: {total_return:.2f}%")
        
        return {
            'final_value': final_value,
            'return': total_return,
            'equity_curve': equity_curve
        }
    
    def live_trade(self, broker_api):
        """Execute live trades (paper trading recommended)"""
        print("🚀 Starting live trading...")
        
        while True:
            # Get current market data
            current_data = self.download_data(
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # Prepare features
            current_data = self.prepare_features(current_data)
            
            # Get AI decision
            state = self.prepare_state(current_data)
            action, _states = self.model.predict(state)
            
            # Execute trade via broker API
            self.execute_trade(action, broker_api)
            
            # Wait for next trading signal (e.g., daily)
            time.sleep(60 * 60 * 24)  # 24 hours
    
    def save_model(self, path):
        """Save trained model"""
        self.model.save(path)
        print(f"✅ Model saved to {path}")
    
    def load_model(self, path):
        """Load trained model"""
        self.model = PPO.load(path)
        print(f"✅ Model loaded from {path}")

# Usage example
if __name__ == '__main__':
    # Initialize system
    system = AutomatedTradingSystem(
        tickers=['SPY', 'QQQ'],
        initial_capital=100000
    )
    
    # Download and prepare data
    train_data = system.download_data('2020-01-01', '2022-12-31')
    train_data = system.prepare_features(train_data)
    
    test_data = system.download_data('2023-01-01', '2023-12-31')
    test_data = system.prepare_features(test_data)
    
    # Train AI agent
    system.train_ai_agent(train_data, timesteps=50000)
    
    # Backtest
    results = system.backtest(test_data)
    
    # Save model
    system.save_model('momentum_ai_system.zip')
    
    print("\n🎉 Automated trading system ready!")
    print("Next: Connect to broker API for live trading")
```

---

## 🔌 Broker Integration

### Alpaca (Recommended for Beginners)

```python
"""
Connect to Alpaca for live/paper trading
"""
import alpaca_trade_api as tradeapi

# Alpaca credentials (get from alpaca.markets)
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
BASE_URL = 'https://paper-api.alpaca.markets'  # Paper trading

api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def execute_trade(action, ticker):
    """Execute trade on Alpaca"""
    if action > 0:  # Buy signal
        api.submit_order(
            symbol=ticker,
            qty=int(action * 10),  # Convert action to shares
            side='buy',
            type='market',
            time_in_force='gtc'
        )
        print(f"🟢 BUY {int(action * 10)} shares of {ticker}")
    
    elif action < 0:  # Sell signal
        api.submit_order(
            symbol=ticker,
            qty=int(abs(action) * 10),
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        print(f"🔴 SELL {int(abs(action) * 10)} shares of {ticker}")

# Check account
account = api.get_account()
print(f"Account Value: ${float(account.portfolio_value):,.2f}")
print(f"Buying Power: ${float(account.buying_power):,.2f}")
```

---

## 📈 Advantages of FinRL + Your Momentum

### Your Momentum Tracker:
✅ Identifies momentum bursts (when trends start)
✅ Fast exit on reversals (scalping feature)
✅ Proven over 15 years (6.1% annual)

### FinRL AI Adds:
✅ **Optimal position sizing** - AI learns how much to trade
✅ **Better timing** - AI refines entry/exit points
✅ **Multi-asset** - AI manages portfolio allocation
✅ **Adaptation** - AI adjusts to changing markets

### Combined System:
🚀 **Your momentum = Signal generator**
🚀 **FinRL AI = Execution optimizer**
🚀 **Result = Better risk-adjusted returns**

---

## ⚠️ Important Considerations

### 1. **Training Time**
- Initial training: 1-4 hours
- Retraining: Weekly/monthly recommended
- GPU recommended for faster training

### 2. **Data Quality**
- More data = better learning
- Use at least 3-5 years for training
- Validate on out-of-sample data

### 3. **Risk Management**
- Start with paper trading
- Use position limits (max 10% per trade)
- Set stop losses
- Monitor daily

### 4. **Computational Requirements**
- Minimum: 8GB RAM
- Recommended: 16GB RAM + GPU
- Storage: 5-10GB for models

---

## 🎯 Next Steps

### Option 1: Quick Start (Recommended)
```bash
# Install FinRL
pip3 install finrl stable-baselines3

# Run simple example
python3 finrl_momentum_example.py
```

### Option 2: Full Setup
1. Install all dependencies
2. Train AI agent on your momentum features
3. Backtest on historical data
4. Paper trade for 1 month
5. Go live with small capital

### Option 3: Just Explore
1. Read FinRL documentation
2. Run example notebooks
3. Experiment with different algorithms
4. Compare with your current strategy

---

## 📚 Resources

- **FinRL GitHub**: https://github.com/AI4Finance-Foundation/FinRL
- **FinRL Docs**: https://finrl.readthedocs.io/
- **Tutorials**: https://github.com/AI4Finance-Foundation/FinRL-Tutorials
- **Discord Community**: https://discord.gg/trsr8SXpW5

---

## 🤔 Should You Use FinRL?

**YES if you want:**
- Automated trading
- AI-optimized decisions
- Portfolio management
- Continuous learning/adaptation

**NO if you prefer:**
- Manual trading
- Simple strategies only
- Full control over every trade
- No coding/ML complexity

---

Want me to:
1. **Install FinRL and run a test?**
2. **Create a custom integration with your momentum tracker?**
3. **Set up paper trading with Alpaca?**
4. **Just explain more about how it works?**
