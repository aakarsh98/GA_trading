"""
Analyze IV/IVP Cycles and Test Professional Strategies
Download VIX data and analyze volatility mean reversion
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def download_vix_data(years=5):
    """Download VIX historical data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    print(f"📥 Downloading VIX data ({years} years)...")
    vix = yf.download('^VIX', start=start_date, end=end_date, progress=False)
    
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = [col[0].lower() for col in vix.columns]
    else:
        vix.columns = vix.columns.str.lower()
    
    print(f"✅ Downloaded {len(vix)} days of VIX data\n")
    return vix


def calculate_ivp(data, lookback=252):
    """Calculate IV Percentile (IVP)"""
    ivp = []
    for i in range(len(data)):
        if i < lookback:
            ivp.append(np.nan)
        else:
            current = data.iloc[i]['close']
            historical = data.iloc[i-lookback:i]['close']
            percentile = (historical < current).sum() / len(historical) * 100
            ivp.append(percentile)
    
    data['ivp'] = ivp
    return data


def analyze_mean_reversion(data):
    """Analyze mean reversion characteristics"""
    print("=" * 80)
    print("📊 ANALYSIS 1: VIX MEAN REVERSION CHARACTERISTICS")
    print("=" * 80)
    
    # Calculate statistics
    vix_mean = data['close'].mean()
    vix_median = data['close'].median()
    vix_std = data['close'].std()
    
    print(f"\n📈 VIX Statistics:")
    print(f"   Mean:                {vix_mean:.2f}")
    print(f"   Median:              {vix_median:.2f}")
    print(f"   Std Deviation:       {vix_std:.2f}")
    print(f"   Min:                 {data['close'].min():.2f}")
    print(f"   Max:                 {data['close'].max():.2f}")
    
    # Analyze high VIX periods
    high_vix = data[data['close'] > vix_mean + vix_std]
    print(f"\n🔥 High VIX Periods (>1 SD above mean):")
    print(f"   Frequency:           {len(high_vix)} days ({len(high_vix)/len(data)*100:.1f}%)")
    print(f"   Average VIX:         {high_vix['close'].mean():.2f}")
    
    # Analyze mean reversion from high VIX
    reversion_stats = []
    for idx in high_vix.index:
        if idx < data.index[-30]:
            current_vix = data.loc[idx, 'close']
            future_10d = data.loc[idx:].iloc[1:11]['close'].mean()
            future_30d = data.loc[idx:].iloc[1:31]['close'].mean()
            
            if not np.isnan(future_10d) and not np.isnan(future_30d):
                reversion_stats.append({
                    'current_vix': current_vix,
                    'future_10d': future_10d,
                    'future_30d': future_30d,
                    'decline_10d': (future_10d - current_vix) / current_vix * 100,
                    'decline_30d': (future_30d - current_vix) / current_vix * 100
                })
    
    if reversion_stats:
        rev_df = pd.DataFrame(reversion_stats)
        print(f"\n📉 Mean Reversion from High VIX:")
        print(f"   Avg decline in 10 days:  {rev_df['decline_10d'].mean():.1f}%")
        print(f"   Avg decline in 30 days:  {rev_df['decline_30d'].mean():.1f}%")
        print(f"   Probability declined:    {(rev_df['decline_10d'] < 0).sum() / len(rev_df) * 100:.1f}%")
    
    # Analyze low VIX periods
    low_vix = data[data['close'] < vix_mean - 0.5 * vix_std]
    print(f"\n😴 Low VIX Periods (<0.5 SD below mean):")
    print(f"   Frequency:           {len(low_vix)} days ({len(low_vix)/len(data)*100:.1f}%)")
    print(f"   Average VIX:         {low_vix['close'].mean():.2f}")
    
    # Analyze mean reversion from low VIX
    expansion_stats = []
    for idx in low_vix.index:
        if idx < data.index[-30]:
            current_vix = data.loc[idx, 'close']
            future_10d = data.loc[idx:].iloc[1:11]['close'].mean()
            future_30d = data.loc[idx:].iloc[1:31]['close'].mean()
            
            if not np.isnan(future_10d) and not np.isnan(future_30d):
                expansion_stats.append({
                    'current_vix': current_vix,
                    'future_10d': future_10d,
                    'future_30d': future_30d,
                    'increase_10d': (future_10d - current_vix) / current_vix * 100,
                    'increase_30d': (future_30d - current_vix) / current_vix * 100
                })
    
    if expansion_stats:
        exp_df = pd.DataFrame(expansion_stats)
        print(f"\n📈 Mean Reversion from Low VIX:")
        print(f"   Avg increase in 10 days: {exp_df['increase_10d'].mean():.1f}%")
        print(f"   Avg increase in 30 days: {exp_df['increase_30d'].mean():.1f}%")
        print(f"   Probability increased:   {(exp_df['increase_10d'] > 0).sum() / len(exp_df) * 100:.1f}%")


def analyze_ivp_predictability(data):
    """Analyze if IVP predicts future IV changes"""
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS 2: IVP PREDICTABILITY")
    print("=" * 80)
    
    data_clean = data.dropna()
    
    # Categorize by IVP
    print(f"\n📊 Future VIX Changes by Current IVP:")
    
    ivp_buckets = [
        ('Very Low (0-20)', 0, 20),
        ('Low (20-40)', 20, 40),
        ('Neutral (40-60)', 40, 60),
        ('High (60-80)', 60, 80),
        ('Very High (80-100)', 80, 100)
    ]
    
    for name, low, high in ivp_buckets:
        bucket_data = data_clean[(data_clean['ivp'] >= low) & (data_clean['ivp'] < high)]
        
        if len(bucket_data) > 10:
            # Calculate future changes
            future_changes = []
            for idx in bucket_data.index:
                if idx < data_clean.index[-30]:
                    current = data_clean.loc[idx, 'close']
                    future = data_clean.loc[idx:].iloc[1:31]['close'].mean()
                    if not np.isnan(future):
                        change_pct = (future - current) / current * 100
                        future_changes.append(change_pct)
            
            if future_changes:
                avg_change = np.mean(future_changes)
                prob_decline = sum(c < 0 for c in future_changes) / len(future_changes) * 100
                
                print(f"\n   {name}:")
                print(f"      Occurrences:        {len(bucket_data)} days")
                print(f"      Avg 30-day change:  {avg_change:+.1f}%")
                print(f"      Prob decline:       {prob_decline:.1f}%")


def backtest_sell_high_ivp(data, ivp_threshold=70, exit_target=-20):
    """Backtest: Sell premium when IVP > threshold"""
    print("\n" + "=" * 80)
    print(f"💰 STRATEGY BACKTEST: SELL WHEN IVP > {ivp_threshold}")
    print("=" * 80)
    
    print(f"\nStrategy Rules:")
    print(f"   Entry: IVP > {ivp_threshold}")
    print(f"   Exit: VIX declines {abs(exit_target)}% OR 30 days")
    print(f"   Position: Short volatility (simulated)")
    
    data_clean = data.dropna()
    trades = []
    in_trade = False
    entry_vix = None
    entry_date = None
    
    for i in range(len(data_clean)):
        current_date = data_clean.index[i]
        current_vix = data_clean.iloc[i]['close']
        current_ivp = data_clean.iloc[i]['ivp']
        
        if not in_trade:
            # Entry signal
            if current_ivp > ivp_threshold:
                in_trade = True
                entry_vix = current_vix
                entry_date = current_date
        else:
            # Exit conditions
            days_held = (current_date - entry_date).days
            vix_change = (current_vix - entry_vix) / entry_vix * 100
            
            exit_signal = False
            exit_reason = ""
            
            if vix_change <= exit_target:
                exit_signal = True
                exit_reason = "Target hit"
            elif days_held >= 30:
                exit_signal = True
                exit_reason = "Time stop"
            
            if exit_signal:
                # Calculate P&L (simplified: inverse of VIX change)
                pnl = -vix_change  # If VIX down 20%, we profit ~20%
                
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': current_date,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'days_held': days_held,
                    'pnl': pnl,
                    'exit_reason': exit_reason
                })
                
                in_trade = False
                entry_vix = None
                entry_date = None
    
    if trades:
        trades_df = pd.DataFrame(trades)
        
        print(f"\n📊 Results:")
        print(f"   Total trades:        {len(trades_df)}")
        print(f"   Win rate:            {(trades_df['pnl'] > 0).sum() / len(trades_df) * 100:.1f}%")
        print(f"   Avg profit:          {trades_df['pnl'].mean():.1f}%")
        print(f"   Best trade:          {trades_df['pnl'].max():.1f}%")
        print(f"   Worst trade:         {trades_df['pnl'].min():.1f}%")
        print(f"   Avg hold time:       {trades_df['days_held'].mean():.1f} days")
        
        print(f"\n💡 Interpretation:")
        if trades_df['pnl'].mean() > 0:
            print(f"   ✅ Strategy profitable on average")
            print(f"   📈 Selling high IVP (>{ivp_threshold}) has positive edge")
        else:
            print(f"   ⚠️  Strategy needs optimization")
    else:
        print(f"\n   No trades generated with these parameters")


def analyze_vix_spikes(data):
    """Analyze what happens after VIX spikes"""
    print("\n" + "=" * 80)
    print("⚡ ANALYSIS 3: VIX SPIKE ANALYSIS")
    print("=" * 80)
    
    # Define spike as >20% single-day increase
    data['daily_change'] = data['close'].pct_change() * 100
    spikes = data[data['daily_change'] > 20]
    
    print(f"\n🚨 VIX Spikes (>20% single day):")
    print(f"   Total spikes:        {len(spikes)}")
    print(f"   Frequency:           1 spike every {len(data)//len(spikes) if len(spikes) > 0 else 0} days")
    
    if len(spikes) > 0:
        # Analyze what happens after spikes
        post_spike_stats = []
        
        for idx in spikes.index:
            if idx < data.index[-60]:
                spike_vix = data.loc[idx, 'close']
                
                # Check future periods
                for days in [5, 10, 20, 30, 60]:
                    future_idx = data.index.get_loc(idx) + days
                    if future_idx < len(data):
                        future_vix = data.iloc[future_idx]['close']
                        change = (future_vix - spike_vix) / spike_vix * 100
                        
                        post_spike_stats.append({
                            'days_after': days,
                            'spike_vix': spike_vix,
                            'future_vix': future_vix,
                            'change': change
                        })
        
        if post_spike_stats:
            stats_df = pd.DataFrame(post_spike_stats)
            
            print(f"\n📉 Average VIX Decline After Spike:")
            for days in [5, 10, 20, 30, 60]:
                subset = stats_df[stats_df['days_after'] == days]
                if len(subset) > 0:
                    avg_change = subset['change'].mean()
                    prob_decline = (subset['change'] < 0).sum() / len(subset) * 100
                    print(f"   {days:2d} days after:     {avg_change:+.1f}% (decline prob: {prob_decline:.0f}%)")


def main():
    """Run all IV/IVP analyses"""
    print("\n" + "🎯" * 40)
    print(" " * 15 + "IV/IVP CYCLE ANALYSIS")
    print(" " * 10 + "(Understanding Professional Vol Trading)")
    print("🎯" * 40)
    
    # Download data
    vix_data = download_vix_data(years=10)
    
    # Calculate IVP
    print("🔄 Calculating IV Percentile (IVP)...")
    vix_data = calculate_ivp(vix_data, lookback=252)
    print("✅ IVP calculated\n")
    
    # Run analyses
    analyze_mean_reversion(vix_data)
    analyze_ivp_predictability(vix_data)
    backtest_sell_high_ivp(vix_data, ivp_threshold=70, exit_target=-20)
    backtest_sell_high_ivp(vix_data, ivp_threshold=80, exit_target=-25)
    analyze_vix_spikes(vix_data)
    
    # Save data
    print("\n" + "=" * 80)
    print("💾 SAVING DATA")
    print("=" * 80)
    
    output_file = 'vix_ivp_analysis.csv'
    vix_data.to_csv(output_file)
    print(f"✅ Saved VIX/IVP data to: {output_file}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. VIX mean reverts (high → low, low → high)")
    print("  2. IVP helps predict direction of mean reversion")
    print("  3. Selling high IVP has positive expectancy")
    print("  4. BUT tail risk exists (VIX can spike further!)")
    print("  5. Professional edge = systematic premium collection + risk mgmt")
    print("\n")


if __name__ == "__main__":
    main()
