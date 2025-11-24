"""
Hypothesis-Driven Testing of Momentum Indicator
Test specific theories based on our analysis
"""
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import sys
sys.path.append('.')


class MomentumIndicatorCalculator:
    """Calculate momentum indicator"""
    
    def __init__(self):
        self.len = 7
        self.v8 = 0.0
        self.v16 = 0.0
        self.v0 = 0.0
        self.v80 = 0.0
        self.v88 = 0.0
        self.v96 = 0.0
        self.v104 = 0.0
        self.v112 = 0.0
        self.v120 = 0.0
        self.v128 = 0.0
        self.v208 = 0.0
        self.v136 = 0.0
        self.v152 = 0.0
        self.v160 = 0.0
        self.v168 = 0.0
        self.v176 = 0.0
        self.v184 = 0.0
        self.v192 = 0.0
        self.v200 = 0.0
        
    def calculate(self, high, low, close):
        """Calculate momentum value"""
        tp = (high + low + close) / 3.0
        v24 = 50.0
        
        if self.v8 == 0.0:
            self.v8 = 1.0
            self.v16 = 0.0
            self.v0 = self.len - 1.0 if self.len - 1 >= 5 else 5.0
            self.v80 = 100.0 * tp
            self.v96 = 3.0 / (self.len + 2.0)
            self.v104 = 1.0 - self.v96
        else:
            if self.v0 <= self.v8:
                self.v8 = self.v0 + 1.0
            else:
                self.v8 = self.v8 + 1.0
            
            self.v88 = self.v80
            self.v80 = 100.0 * tp
            v32 = self.v80 - self.v88
            
            self.v112 = self.v104 * self.v112 + self.v96 * v32
            self.v120 = self.v96 * self.v112 + self.v104 * self.v120
            v40 = 1.5 * self.v112 - self.v120 / 2.0
            
            self.v128 = self.v104 * self.v128 + self.v96 * v40
            self.v208 = self.v96 * self.v128 + self.v104 * self.v208
            v48 = 1.5 * self.v128 - self.v208 / 2.0
            
            self.v136 = self.v104 * self.v136 + self.v96 * v48
            self.v152 = self.v96 * self.v136 + self.v104 * self.v152
            v56 = 1.5 * self.v136 - self.v152 / 2.0
            
            self.v160 = self.v104 * self.v160 + self.v96 * abs(v32)
            self.v168 = self.v96 * self.v160 + self.v104 * self.v168
            v64 = 1.5 * self.v160 - self.v168 / 2.0
            
            self.v176 = self.v104 * self.v176 + self.v96 * v64
            self.v184 = self.v96 * self.v176 + self.v104 * self.v184
            v144 = 1.5 * self.v176 - self.v184 / 2.0
            
            self.v192 = self.v104 * self.v192 + self.v96 * v144
            self.v200 = self.v96 * self.v192 + self.v104 * self.v200
            v72 = 1.5 * self.v192 - self.v200 / 2.0
            
            if self.v0 >= self.v8 and self.v80 != self.v88:
                self.v16 = 1.0
            if self.v0 == self.v8 and self.v16 == 0.0:
                self.v8 = 0.0
            
            if self.v0 < self.v8 and v72 > 0.0000000001:
                v24 = 50.0 * (v56 / v72 + 1.0)
                if v24 > 100.0:
                    v24 = 100.0
                if v24 < 0.0:
                    v24 = 0.0
        
        return v24


def load_data():
    """Load data with momentum calculated"""
    try:
        data = pd.read_csv('momentum_indicator_data.csv', index_col=0, parse_dates=True)
        print(f"✅ Loaded {len(data)} bars from saved data\n")
        return data
    except:
        print("⚠️  No saved data found, downloading...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        data = yf.download('SPY', start=start_date, end=end_date, interval='1d', progress=False)
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0].lower() for col in data.columns]
        else:
            data.columns = data.columns.str.lower()
        
        # Calculate momentum
        calc = MomentumIndicatorCalculator()
        momentum_values = []
        for i in range(len(data)):
            m = calc.calculate(data.iloc[i]['high'], data.iloc[i]['low'], data.iloc[i]['close'])
            momentum_values.append(m)
        data['momentum'] = momentum_values
        
        return data


def test_hypothesis_1_long_vs_short(data):
    """
    HYPOTHESIS 1: LONG-only performs better than LONG+SHORT
    Reason: Bullish bias (13.6 vs 6.3 bar persistence)
    """
    print("=" * 80)
    print("🧪 HYPOTHESIS TEST 1: LONG-ONLY VS LONG+SHORT")
    print("=" * 80)
    
    # Detect direction changes
    data['momentum_change'] = data['momentum'].diff()
    data['prev_change'] = data['momentum_change'].shift(1)
    
    # Simple equilibrium: when momentum crosses its 20-bar moving average
    data['momentum_ma'] = data['momentum'].rolling(20).mean()
    
    # LONG+SHORT strategy
    long_short_trades = []
    position = None
    entry_price = None
    
    for i in range(50, len(data)):
        momentum = data.iloc[i]['momentum']
        momentum_ma = data.iloc[i]['momentum_ma']
        price = data.iloc[i]['close']
        
        if position is None:
            if momentum > momentum_ma + 2:
                position = 'LONG'
                entry_price = price
            elif momentum < momentum_ma - 2:
                position = 'SHORT'
                entry_price = price
        else:
            if position == 'LONG' and momentum < momentum_ma:
                pnl_pct = (price - entry_price) / entry_price
                long_short_trades.append({'type': 'LONG', 'pnl': pnl_pct})
                position = None
            elif position == 'SHORT' and momentum > momentum_ma:
                pnl_pct = (entry_price - price) / entry_price
                long_short_trades.append({'type': 'SHORT', 'pnl': pnl_pct})
                position = None
    
    # LONG-only strategy  
    long_only_trades = []
    position = None
    entry_price = None
    
    for i in range(50, len(data)):
        momentum = data.iloc[i]['momentum']
        momentum_ma = data.iloc[i]['momentum_ma']
        price = data.iloc[i]['close']
        
        if position is None:
            if momentum > momentum_ma + 2:
                position = 'LONG'
                entry_price = price
        else:
            if momentum < momentum_ma:
                pnl_pct = (price - entry_price) / entry_price
                long_only_trades.append({'type': 'LONG', 'pnl': pnl_pct})
                position = None
    
    # Compare results
    ls_df = pd.DataFrame(long_short_trades)
    lo_df = pd.DataFrame(long_only_trades)
    
    print(f"\n📊 LONG+SHORT Strategy:")
    if len(ls_df) > 0:
        ls_long = ls_df[ls_df['type'] == 'LONG']
        ls_short = ls_df[ls_df['type'] == 'SHORT']
        
        print(f"   Total trades:        {len(ls_df)}")
        print(f"   LONG trades:         {len(ls_long)} ({(ls_long['pnl'] > 0).sum() / len(ls_long) * 100:.1f}% win rate)")
        print(f"   SHORT trades:        {len(ls_short)} ({(ls_short['pnl'] > 0).sum() / len(ls_short) * 100:.1f}% win rate)")
        print(f"   Average return:      {ls_df['pnl'].mean() * 100:.2f}%")
        print(f"   Win rate:            {(ls_df['pnl'] > 0).sum() / len(ls_df) * 100:.1f}%")
        print(f"   Total return:        {ls_df['pnl'].sum() * 100:.2f}%")
    
    print(f"\n📊 LONG-ONLY Strategy:")
    if len(lo_df) > 0:
        print(f"   Total trades:        {len(lo_df)}")
        print(f"   Average return:      {lo_df['pnl'].mean() * 100:.2f}%")
        print(f"   Win rate:            {(lo_df['pnl'] > 0).sum() / len(lo_df) * 100:.1f}%")
        print(f"   Total return:        {lo_df['pnl'].sum() * 100:.2f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if len(ls_df) > 0 and len(lo_df) > 0:
        if lo_df['pnl'].mean() > ls_df['pnl'].mean():
            print(f"   ✅ LONG-ONLY wins! ({lo_df['pnl'].mean()*100:.2f}% vs {ls_df['pnl'].mean()*100:.2f}%)")
            print(f"   → Disable SHORT trades")
        else:
            print(f"   ❌ LONG+SHORT better ({ls_df['pnl'].mean()*100:.2f}% vs {lo_df['pnl'].mean()*100:.2f}%)")


def test_hypothesis_2_buy_dips_vs_strength(data):
    """
    HYPOTHESIS 2: Buying dips (low momentum) outperforms buying strength (high momentum)
    Reason: <30 gives +0.97%, >70 gives +0.18%
    """
    print("\n" + "=" * 80)
    print("🧪 HYPOTHESIS TEST 2: BUY DIPS VS BUY STRENGTH")
    print("=" * 80)
    
    # Strategy A: Buy when momentum is high (>60)
    buy_strength_trades = []
    for i in range(50, len(data) - 10):
        if data.iloc[i]['momentum'] > 60 and data.iloc[i-1]['momentum'] <= 60:
            entry_price = data.iloc[i]['close']
            exit_price = data.iloc[i+10]['close']
            pnl_pct = (exit_price - entry_price) / entry_price
            buy_strength_trades.append(pnl_pct)
    
    # Strategy B: Buy when momentum is low (<40)
    buy_dip_trades = []
    for i in range(50, len(data) - 10):
        if data.iloc[i]['momentum'] < 40 and data.iloc[i-1]['momentum'] >= 40:
            entry_price = data.iloc[i]['close']
            exit_price = data.iloc[i+10]['close']
            pnl_pct = (exit_price - entry_price) / entry_price
            buy_dip_trades.append(pnl_pct)
    
    print(f"\n📊 Buy Strength (Enter when momentum > 60):")
    if buy_strength_trades:
        print(f"   Trades:              {len(buy_strength_trades)}")
        print(f"   Average return:      {np.mean(buy_strength_trades)*100:.2f}%")
        print(f"   Win rate:            {sum(r > 0 for r in buy_strength_trades)/len(buy_strength_trades)*100:.1f}%")
    
    print(f"\n📊 Buy Dips (Enter when momentum < 40):")
    if buy_dip_trades:
        print(f"   Trades:              {len(buy_dip_trades)}")
        print(f"   Average return:      {np.mean(buy_dip_trades)*100:.2f}%")
        print(f"   Win rate:            {sum(r > 0 for r in buy_dip_trades)/len(buy_dip_trades)*100:.1f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if buy_strength_trades and buy_dip_trades:
        if np.mean(buy_dip_trades) > np.mean(buy_strength_trades):
            print(f"   ✅ BUY DIPS wins! ({np.mean(buy_dip_trades)*100:.2f}% vs {np.mean(buy_strength_trades)*100:.2f}%)")
            print(f"   → Enter on pullbacks, not breakouts")
        else:
            print(f"   ❌ BUY STRENGTH better ({np.mean(buy_strength_trades)*100:.2f}% vs {np.mean(buy_dip_trades)*100:.2f}%)")


def test_hypothesis_3_volatility_filter(data):
    """
    HYPOTHESIS 3: Adding volatility filter improves performance
    Reason: Low vol has momentum 67.4, high vol has 55.1
    """
    print("\n" + "=" * 80)
    print("🧪 HYPOTHESIS TEST 3: VOLATILITY FILTER")
    print("=" * 80)
    
    # Calculate volatility
    data['price_range'] = data['high'] - data['low']
    data['volatility'] = data['price_range'].rolling(14).mean()
    data['vol_median'] = data['volatility'].rolling(50).median()
    
    data['momentum_ma'] = data['momentum'].rolling(20).mean()
    
    # Without filter
    no_filter_trades = []
    position = None
    entry_price = None
    
    for i in range(50, len(data)):
        momentum = data.iloc[i]['momentum']
        momentum_ma = data.iloc[i]['momentum_ma']
        price = data.iloc[i]['close']
        
        if position is None:
            if momentum > momentum_ma + 2:
                position = 'LONG'
                entry_price = price
        else:
            if momentum < momentum_ma:
                pnl_pct = (price - entry_price) / entry_price
                no_filter_trades.append(pnl_pct)
                position = None
    
    # With volatility filter
    with_filter_trades = []
    position = None
    entry_price = None
    
    for i in range(50, len(data)):
        momentum = data.iloc[i]['momentum']
        momentum_ma = data.iloc[i]['momentum_ma']
        price = data.iloc[i]['close']
        vol = data.iloc[i]['volatility']
        vol_med = data.iloc[i]['vol_median']
        
        if position is None:
            # Only enter in low volatility
            if momentum > momentum_ma + 2 and vol < vol_med:
                position = 'LONG'
                entry_price = price
        else:
            if momentum < momentum_ma:
                pnl_pct = (price - entry_price) / entry_price
                with_filter_trades.append(pnl_pct)
                position = None
    
    print(f"\n📊 Without Volatility Filter:")
    if no_filter_trades:
        print(f"   Trades:              {len(no_filter_trades)}")
        print(f"   Average return:      {np.mean(no_filter_trades)*100:.2f}%")
        print(f"   Win rate:            {sum(r > 0 for r in no_filter_trades)/len(no_filter_trades)*100:.1f}%")
    
    print(f"\n📊 With Volatility Filter (low vol only):")
    if with_filter_trades:
        print(f"   Trades:              {len(with_filter_trades)}")
        print(f"   Average return:      {np.mean(with_filter_trades)*100:.2f}%")
        print(f"   Win rate:            {sum(r > 0 for r in with_filter_trades)/len(with_filter_trades)*100:.1f}%")
    
    print(f"\n🎯 CONCLUSION:")
    if no_filter_trades and with_filter_trades:
        if np.mean(with_filter_trades) > np.mean(no_filter_trades):
            improvement = (np.mean(with_filter_trades) - np.mean(no_filter_trades)) * 100
            print(f"   ✅ FILTER helps! (+{improvement:.2f}% per trade)")
            print(f"   → Add volatility filter to strategy")
        else:
            print(f"   ❌ NO FILTER better")


def main():
    """Run all hypothesis tests"""
    print("\n" + "🧪" * 40)
    print(" " * 15 + "HYPOTHESIS-DRIVEN TESTING")
    print(" " * 10 + "(Testing specific theories from our analysis)")
    print("🧪" * 40)
    
    # Load data
    data = load_data()
    
    # Run tests
    test_hypothesis_1_long_vs_short(data)
    test_hypothesis_2_buy_dips_vs_strength(data)
    test_hypothesis_3_volatility_filter(data)
    
    print("\n" + "=" * 80)
    print("✅ HYPOTHESIS TESTING COMPLETE!")
    print("=" * 80)
    print("\nBased on these results, we can now design an optimized strategy.")
    print("\n")


if __name__ == "__main__":
    main()
