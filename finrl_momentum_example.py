"""
FinRL + Your Momentum Tracker Integration
Simple example to train an AI agent using your momentum indicators
"""
import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add path to your momentum tracker
sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  FinRL + Momentum Tracker Integration Example")
print("=" * 80)

# Step 1: Download data
print("\n📥 Step 1: Downloading market data...")
ticker = 'SPY'
start_date = '2020-01-01'
end_date = '2023-12-31'

data = yf.download(ticker, start=start_date, end=end_date, progress=False)

# Standardize column names
if isinstance(data.columns, pd.MultiIndex):
    data.columns = [col[0].lower() for col in data.columns]
else:
    data.columns = data.columns.str.lower()

print(f"✅ Downloaded {len(data)} bars for {ticker}")
print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")

# Step 2: Add your momentum indicators
print("\n📊 Step 2: Calculating momentum indicators...")
momentum_result = calculate_momentum_indicator(data, length=7, threshold=2.0)

data['momentum'] = momentum_result['momentum']
data['equilibrium'] = momentum_result['equilibrium']
data['distance'] = momentum_result['momentum'] - momentum_result['equilibrium']
data['bullish'] = momentum_result['bullish'].astype(int)
data['bearish'] = momentum_result['bearish'].astype(int)

print(f"✅ Added momentum features:")
print(f"   - Momentum (0-100)")
print(f"   - Equilibrium (dynamic baseline)")
print(f"   - Distance (momentum - equilibrium)")
print(f"   - Bullish signal (0/1)")
print(f"   - Bearish signal (0/1)")

# Step 3: Calculate additional technical indicators
print("\n📈 Step 3: Calculating additional indicators...")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Add simple technical indicators
data['sma_20'] = data['close'].rolling(20).mean()
data['sma_50'] = data['close'].rolling(50).mean()
data['rsi'] = calculate_rsi(data['close'], 14)
data['volume_ma'] = data['volume'].rolling(20).mean()

# Drop NaN values
data = data.dropna()

print(f"✅ Added technical indicators")
print(f"   Final dataset: {len(data)} bars")

# Step 4: Create simple trading environment (manual, not FinRL yet)
print("\n🤖 Step 4: Testing with simple trading logic...")

def simple_momentum_strategy(df, initial_capital=10000):
    """
    Simple strategy to establish baseline before AI training
    Uses your momentum signals directly
    """
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(100, len(df)):
        current_price = df.iloc[i]['close']
        bullish = df.iloc[i]['bullish']
        bearish = df.iloc[i]['bearish']
        
        # Entry
        if position == 0 and bullish:
            shares = int((capital * 0.95) / current_price)  # 95% of capital
            if shares > 0:
                position = shares
                entry_price = current_price
        
        # Exit
        elif position > 0 and bearish:
            pnl = position * (current_price - entry_price)
            capital += pnl
            trades.append({
                'entry': entry_price,
                'exit': current_price,
                'pnl': pnl,
                'return': (current_price / entry_price - 1) * 100
            })
            position = 0
        
        # Track equity
        if position > 0:
            current_equity = capital + position * (current_price - entry_price)
        else:
            current_equity = capital
        
        equity_curve.append(current_equity)
    
    return {
        'final_capital': capital,
        'return': (capital / initial_capital - 1) * 100,
        'trades': trades,
        'equity_curve': equity_curve
    }

# Run baseline strategy
baseline_results = simple_momentum_strategy(data)

print(f"\n📊 Baseline Strategy Results (2020-2023):")
print(f"   Initial Capital:  ${10000:,.2f}")
print(f"   Final Capital:    ${baseline_results['final_capital']:,.2f}")
print(f"   Total Return:     {baseline_results['return']:.2f}%")
print(f"   Total Trades:     {len(baseline_results['trades'])}")

if len(baseline_results['trades']) > 0:
    winning_trades = sum(1 for t in baseline_results['trades'] if t['pnl'] > 0)
    win_rate = (winning_trades / len(baseline_results['trades'])) * 100
    avg_return = np.mean([t['return'] for t in baseline_results['trades']])
    
    print(f"   Winning Trades:   {winning_trades}/{len(baseline_results['trades'])}")
    print(f"   Win Rate:         {win_rate:.1f}%")
    print(f"   Avg Return/Trade: {avg_return:.2f}%")

# Step 5: Prepare data for FinRL format
print("\n🔧 Step 5: Preparing data for FinRL...")

# FinRL expects specific format
finrl_data = data.reset_index()
finrl_data['tic'] = ticker

# Handle index name - could be 'Date' or index without name
if 'Date' in finrl_data.columns:
    finrl_data['day'] = finrl_data['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    finrl_data = finrl_data.rename(columns={'Date': 'timestamp'})
elif finrl_data.index.name == 'Date' or 'date' in str(finrl_data.columns[0]).lower():
    date_col = finrl_data.columns[0]
    finrl_data['day'] = finrl_data[date_col].apply(lambda x: x.strftime('%Y-%m-%d'))
    finrl_data = finrl_data.rename(columns={date_col: 'timestamp'})

# Rename columns to FinRL format
finrl_data = finrl_data.rename(columns={
    'date': 'timestamp',
    'open': 'open',
    'high': 'high', 
    'low': 'low',
    'close': 'close',
    'volume': 'volume'
})

# Select features for FinRL
feature_columns = [
    'momentum', 'equilibrium', 'distance', 'bullish', 'bearish',
    'sma_20', 'sma_50', 'rsi', 'volume_ma'
]

print(f"✅ Data prepared for FinRL")
print(f"   Format: {len(finrl_data)} rows x {len(finrl_data.columns)} columns")
print(f"   Features: {len(feature_columns)} indicators")

# Step 6: Show next steps
print("\n" + "=" * 80)
print("  ✅ SETUP COMPLETE!")
print("=" * 80)

print(f"""
📋 Summary:
   • Downloaded {len(data)} bars of {ticker} data (2020-2023)
   • Your momentum tracker calculated successfully
   • Baseline strategy: {baseline_results['return']:.2f}% return
   • Data prepared for FinRL training

🚀 Next Steps:

1. TRAIN AI AGENT (requires more code - FinRL environment setup)
   - Create custom trading environment
   - Define reward function
   - Train PPO agent (50,000-100,000 timesteps)
   - Expected time: 10-30 minutes

2. BACKTEST AI AGENT
   - Test on 2024 data
   - Compare vs baseline
   - Analyze improvements

3. PAPER TRADE
   - Connect to Alpaca paper trading
   - Run AI agent on live data
   - Monitor performance

📊 Expected Improvements with AI:
   Baseline:   {baseline_results['return']:.2f}%
   Target:     {baseline_results['return'] * 1.3:.2f}% (+30% improvement)
   
   AI can optimize:
   - Position sizing (based on momentum strength)
   - Entry/exit timing (based on multiple signals)
   - Risk management (dynamic stop losses)

💡 Your momentum tracker provides excellent features for the AI:
   - Momentum value (trend strength)
   - Equilibrium (dynamic baseline)  
   - Distance (signal strength)
   - Bullish/Bearish flags (clear signals)

Want to continue? The full FinRL training requires additional code.
I can create that next if you'd like!
""")

print("\n✅ Script completed successfully!")
print(f"   Baseline performance: {baseline_results['return']:.2f}%")
print(f"   Ready for AI training!")
