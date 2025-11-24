"""
Deep Analysis of YOUR Momentum Tracker Indicator
Understand the relationship between price and indicator BEFORE trading
"""
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks
import sys
sys.path.append('.')


class MomentumIndicatorAnalyzer:
    """
    Analyzes YOUR momentum tracker indicator properties
    No trading - just understanding the indicator behavior
    """
    
    def __init__(self):
        self.len = 7
        # Momentum tracker variables
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
        
    def calculate_momentum(self, high: float, low: float, close: float) -> float:
        """Calculate momentum tracker value - YOUR algorithm"""
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
            
            # Triple smoothing
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


def download_data(symbol='SPY', days=730):
    """Download real market data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"📥 Downloading {symbol} data...")
    data = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    print(f"✅ Downloaded {len(data)} bars\n")
    return data


def calculate_indicator_for_data(data):
    """Calculate momentum indicator for all bars"""
    analyzer = MomentumIndicatorAnalyzer()
    momentum_values = []
    
    for i in range(len(data)):
        high = data.iloc[i]['high']
        low = data.iloc[i]['low']
        close = data.iloc[i]['close']
        
        momentum = analyzer.calculate_momentum(high, low, close)
        momentum_values.append(momentum)
    
    data['momentum'] = momentum_values
    return data


def analyze_indicator_properties(data):
    """Analyze basic statistical properties of the indicator"""
    print("=" * 80)
    print("📊 ANALYSIS 1: INDICATOR STATISTICAL PROPERTIES")
    print("=" * 80)
    
    momentum = data['momentum']
    
    print(f"\n📈 Distribution Statistics:")
    print(f"   Mean:                {momentum.mean():.2f}")
    print(f"   Median:              {momentum.median():.2f}")
    print(f"   Std Deviation:       {momentum.std():.2f}")
    print(f"   Min:                 {momentum.min():.2f}")
    print(f"   Max:                 {momentum.max():.2f}")
    print(f"   Range:               {momentum.max() - momentum.min():.2f}")
    
    print(f"\n📊 Percentiles:")
    for p in [5, 10, 25, 50, 75, 90, 95]:
        print(f"   {p}th percentile:     {np.percentile(momentum, p):.2f}")
    
    print(f"\n🎯 Key Levels:")
    print(f"   Time above 50:       {(momentum > 50).sum() / len(momentum) * 100:.1f}%")
    print(f"   Time below 50:       {(momentum < 50).sum() / len(momentum) * 100:.1f}%")
    print(f"   Time above 60:       {(momentum > 60).sum() / len(momentum) * 100:.1f}%")
    print(f"   Time below 40:       {(momentum < 40).sum() / len(momentum) * 100:.1f}%")
    
    return {
        'mean': momentum.mean(),
        'median': momentum.median(),
        'std': momentum.std(),
        'percentiles': {p: np.percentile(momentum, p) for p in [5, 10, 25, 50, 75, 90, 95]}
    }


def analyze_price_momentum_correlation(data):
    """Analyze correlation between price and momentum"""
    print("\n" + "=" * 80)
    print("🔗 ANALYSIS 2: PRICE-MOMENTUM CORRELATION")
    print("=" * 80)
    
    # Calculate price returns
    data['returns_1d'] = data['close'].pct_change(1)
    data['returns_5d'] = data['close'].pct_change(5)
    data['returns_10d'] = data['close'].pct_change(10)
    data['returns_20d'] = data['close'].pct_change(20)
    
    # Calculate momentum changes
    data['momentum_change'] = data['momentum'].diff()
    
    print(f"\n📊 Correlation with Price Returns:")
    print(f"   1-day returns:       {data['momentum'].corr(data['returns_1d']):.3f}")
    print(f"   5-day returns:       {data['momentum'].corr(data['returns_5d']):.3f}")
    print(f"   10-day returns:      {data['momentum'].corr(data['returns_10d']):.3f}")
    print(f"   20-day returns:      {data['momentum'].corr(data['returns_20d']):.3f}")
    
    print(f"\n📈 Momentum Change vs Future Returns:")
    # Check if momentum change predicts future returns
    data['future_returns_1d'] = data['returns_1d'].shift(-1)
    data['future_returns_5d'] = data['returns_5d'].shift(-5)
    data['future_returns_10d'] = data['returns_10d'].shift(-10)
    
    print(f"   Momentum → 1-day ahead:   {data['momentum'].corr(data['future_returns_1d']):.3f}")
    print(f"   Momentum → 5-day ahead:   {data['momentum'].corr(data['future_returns_5d']):.3f}")
    print(f"   Momentum → 10-day ahead:  {data['momentum'].corr(data['future_returns_10d']):.3f}")
    
    return {
        'current_correlation': data['momentum'].corr(data['returns_1d']),
        'predictive_1d': data['momentum'].corr(data['future_returns_1d']),
        'predictive_5d': data['momentum'].corr(data['future_returns_5d'])
    }


def analyze_momentum_extremes(data):
    """Analyze what happens at extreme momentum values"""
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS 3: EXTREME MOMENTUM LEVELS")
    print("=" * 80)
    
    # Define extremes
    high_momentum = data['momentum'] > 70
    low_momentum = data['momentum'] < 30
    very_high = data['momentum'] > 80
    very_low = data['momentum'] < 20
    
    print(f"\n📊 Frequency of Extremes:")
    print(f"   Momentum > 70:       {high_momentum.sum()} times ({high_momentum.sum()/len(data)*100:.1f}%)")
    print(f"   Momentum < 30:       {low_momentum.sum()} times ({low_momentum.sum()/len(data)*100:.1f}%)")
    print(f"   Momentum > 80:       {very_high.sum()} times ({very_high.sum()/len(data)*100:.1f}%)")
    print(f"   Momentum < 20:       {very_low.sum()} times ({very_low.sum()/len(data)*100:.1f}%)")
    
    # Future returns after extremes
    print(f"\n📈 Average 5-Day Returns After:")
    
    if high_momentum.sum() > 0:
        future_after_high = data.loc[high_momentum, 'future_returns_5d'].mean()
        print(f"   Momentum > 70:       {future_after_high*100:.2f}%")
    
    if low_momentum.sum() > 0:
        future_after_low = data.loc[low_momentum, 'future_returns_5d'].mean()
        print(f"   Momentum < 30:       {future_after_low*100:.2f}%")
    
    # Mean reversion test
    mid_range = (data['momentum'] > 45) & (data['momentum'] < 55)
    if mid_range.sum() > 0:
        future_after_mid = data.loc[mid_range, 'future_returns_5d'].mean()
        print(f"   Momentum 45-55:      {future_after_mid*100:.2f}%")
    
    return {
        'high_freq': high_momentum.sum()/len(data),
        'low_freq': low_momentum.sum()/len(data)
    }


def analyze_momentum_direction_changes(data):
    """Analyze equilibrium and direction changes"""
    print("\n" + "=" * 80)
    print("🔄 ANALYSIS 4: DIRECTION CHANGES (EQUILIBRIUM)")
    print("=" * 80)
    
    # Detect direction changes
    data['momentum_change'] = data['momentum'].diff()
    
    # Find peaks and troughs
    peaks, _ = find_peaks(data['momentum'].values, distance=5)
    troughs, _ = find_peaks(-data['momentum'].values, distance=5)
    
    print(f"\n📊 Direction Change Statistics:")
    print(f"   Total peaks:         {len(peaks)}")
    print(f"   Total troughs:       {len(troughs)}")
    print(f"   Avg bars between:    {len(data) / (len(peaks) + len(troughs)):.1f}")
    
    # Analyze what happens after direction change
    direction_changes = list(peaks) + list(troughs)
    direction_changes.sort()
    
    if len(direction_changes) > 10:
        returns_after_change = []
        for change_idx in direction_changes:
            if change_idx + 10 < len(data):
                ret = (data.iloc[change_idx + 10]['close'] - data.iloc[change_idx]['close']) / data.iloc[change_idx]['close']
                returns_after_change.append(ret)
        
        print(f"\n📈 After Direction Change (10 days):")
        print(f"   Average return:      {np.mean(returns_after_change)*100:.2f}%")
        print(f"   Positive moves:      {sum(r > 0 for r in returns_after_change)} ({sum(r > 0 for r in returns_after_change)/len(returns_after_change)*100:.1f}%)")
    
    return {
        'peaks': len(peaks),
        'troughs': len(troughs),
        'avg_period': len(data) / (len(peaks) + len(troughs)) if (len(peaks) + len(troughs)) > 0 else 0
    }


def analyze_momentum_persistence(data):
    """Analyze how long momentum stays in a direction"""
    print("\n" + "=" * 80)
    print("⏱️  ANALYSIS 5: MOMENTUM PERSISTENCE")
    print("=" * 80)
    
    # Count consecutive bars above/below 50
    above_50 = data['momentum'] > 50
    below_50 = data['momentum'] < 50
    
    # Calculate streaks
    above_streaks = []
    below_streaks = []
    current_streak = 0
    
    for val in above_50:
        if val:
            current_streak += 1
        else:
            if current_streak > 0:
                above_streaks.append(current_streak)
            current_streak = 0
    
    current_streak = 0
    for val in below_50:
        if val:
            current_streak += 1
        else:
            if current_streak > 0:
                below_streaks.append(current_streak)
            current_streak = 0
    
    print(f"\n📊 Persistence Statistics (Above 50):")
    if above_streaks:
        print(f"   Average duration:    {np.mean(above_streaks):.1f} bars")
        print(f"   Median duration:     {np.median(above_streaks):.1f} bars")
        print(f"   Longest streak:      {max(above_streaks)} bars")
    
    print(f"\n📊 Persistence Statistics (Below 50):")
    if below_streaks:
        print(f"   Average duration:    {np.mean(below_streaks):.1f} bars")
        print(f"   Median duration:     {np.median(below_streaks):.1f} bars")
        print(f"   Longest streak:      {max(below_streaks)} bars")
    
    return {
        'above_avg': np.mean(above_streaks) if above_streaks else 0,
        'below_avg': np.mean(below_streaks) if below_streaks else 0
    }


def analyze_momentum_vs_volatility(data):
    """Analyze relationship with volatility"""
    print("\n" + "=" * 80)
    print("📉 ANALYSIS 6: MOMENTUM VS VOLATILITY")
    print("=" * 80)
    
    # Calculate volatility (ATR-like)
    data['price_range'] = data['high'] - data['low']
    data['volatility'] = data['price_range'].rolling(14).mean()
    
    # Correlation
    corr = data['momentum'].corr(data['volatility'])
    print(f"\n🔗 Correlation with Volatility: {corr:.3f}")
    
    # High vs low volatility momentum behavior
    high_vol = data['volatility'] > data['volatility'].median()
    low_vol = data['volatility'] <= data['volatility'].median()
    
    print(f"\n📊 Momentum Behavior:")
    print(f"   High Volatility:")
    print(f"      Avg momentum:     {data.loc[high_vol, 'momentum'].mean():.2f}")
    print(f"      Std deviation:    {data.loc[high_vol, 'momentum'].std():.2f}")
    
    print(f"   Low Volatility:")
    print(f"      Avg momentum:     {data.loc[low_vol, 'momentum'].mean():.2f}")
    print(f"      Std deviation:    {data.loc[low_vol, 'momentum'].std():.2f}")
    
    return {
        'correlation': corr,
        'high_vol_avg': data.loc[high_vol, 'momentum'].mean(),
        'low_vol_avg': data.loc[low_vol, 'momentum'].mean()
    }


def create_summary_report(all_results, data):
    """Create summary of findings"""
    print("\n" + "=" * 80)
    print("📋 SUMMARY: KEY FINDINGS ABOUT YOUR MOMENTUM INDICATOR")
    print("=" * 80)
    
    print(f"\n1️⃣  INDICATOR CHARACTERISTICS:")
    print(f"   • Centers around {all_results['properties']['mean']:.1f}")
    print(f"   • Typical range: {all_results['properties']['percentiles'][10]:.1f} - {all_results['properties']['percentiles'][90]:.1f}")
    print(f"   • Extreme readings rare (>70: {(data['momentum'] > 70).sum()} times, <30: {(data['momentum'] < 30).sum()} times)")
    
    print(f"\n2️⃣  PRICE RELATIONSHIP:")
    print(f"   • Current correlation: {all_results['correlation']['current_correlation']:.3f}")
    print(f"   • Predictive power (1d): {all_results['correlation']['predictive_1d']:.3f}")
    print(f"   • Predictive power (5d): {all_results['correlation']['predictive_5d']:.3f}")
    
    if abs(all_results['correlation']['predictive_1d']) < 0.1:
        print(f"   ⚠️  Weak predictive power - not a leading indicator")
    
    print(f"\n3️⃣  DIRECTION CHANGES:")
    print(f"   • Changes direction every ~{all_results['direction']['avg_period']:.1f} bars")
    print(f"   • {all_results['direction']['peaks']} peaks, {all_results['direction']['troughs']} troughs")
    
    print(f"\n4️⃣  PERSISTENCE:")
    print(f"   • Stays bullish (>50) for ~{all_results['persistence']['above_avg']:.1f} bars")
    print(f"   • Stays bearish (<50) for ~{all_results['persistence']['below_avg']:.1f} bars")
    
    print(f"\n5️⃣  VOLATILITY INTERACTION:")
    print(f"   • Correlation: {all_results['volatility']['correlation']:.3f}")
    print(f"   • High vol momentum: {all_results['volatility']['high_vol_avg']:.1f}")
    print(f"   • Low vol momentum: {all_results['volatility']['low_vol_avg']:.1f}")


def main():
    """Run all analyses"""
    print("\n" + "🎯" * 40)
    print(" " * 15 + "MOMENTUM INDICATOR DEEP ANALYSIS")
    print(" " * 20 + "(Understanding Before Trading)")
    print("🎯" * 40)
    
    # Download data
    data = download_data('SPY', days=730)
    
    # Calculate indicator
    print("🔄 Calculating momentum indicator for all bars...")
    data = calculate_indicator_for_data(data)
    print(f"✅ Calculated momentum for {len(data)} bars\n")
    
    # Run all analyses
    all_results = {}
    
    all_results['properties'] = analyze_indicator_properties(data)
    all_results['correlation'] = analyze_price_momentum_correlation(data)
    all_results['extremes'] = analyze_momentum_extremes(data)
    all_results['direction'] = analyze_momentum_direction_changes(data)
    all_results['persistence'] = analyze_momentum_persistence(data)
    all_results['volatility'] = analyze_momentum_vs_volatility(data)
    
    # Create summary
    create_summary_report(all_results, data)
    
    # Save data for further analysis
    print(f"\n" + "=" * 80)
    print("💾 SAVING DATA")
    print("=" * 80)
    
    output_file = 'momentum_indicator_data.csv'
    data.to_csv(output_file)
    print(f"✅ Saved data with momentum values to: {output_file}")
    print(f"   You can analyze this in Excel or other tools")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Review the findings above")
    print("  2. Look at momentum_indicator_data.csv")
    print("  3. Based on findings, we'll design entry/exit rules")
    print("  4. Test those rules systematically")
    print("\n")


if __name__ == "__main__":
    main()
