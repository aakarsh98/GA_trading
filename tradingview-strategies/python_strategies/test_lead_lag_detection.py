"""
LEAD-LAG DETECTION TEST
Tests cross-asset lead-lag relationships for edge detection

Source: "Lead-Lag Relationships in Market Microstructure" (SSRN, 2024)
Expected: 51-72% faster detection, 25-35% Sharpe improvement

✅ NOW USING YOUR ACTUAL MOMENTUM TRACKER (NOT SIMPLIFIED!)
"""
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/utils')

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import YOUR actual momentum tracker
from actual_momentum_tracker import calculate_momentum_indicator as calc_momentum_full, backtest_baseline

print("\n" + "🔗"*40)
print(" "*10 + "LEAD-LAG DETECTION TEST")
print(" "*5 + "Cross-Asset Predictive Relationships")
print(" "*8 + "(Using YOUR Actual Momentum Tracker)")
print("🔗"*40)

def calculate_momentum_indicator(df):
    """Calculate momentum using YOUR exact algorithm"""
    result = calc_momentum_full(df, length=7, threshold=2.0)
    return result['momentum']


def calculate_lead_lag_relationships(leading_asset, lagging_asset, window=50):
    """
    Calculate lead-lag relationships between assets
    
    Args:
        leading_asset: Data for leading indicator (e.g., SPY)
        lagging_asset: Data for lagging indicator (current asset)
        window: Correlation window
    
    Returns:
        DataFrame with lead-lag metrics
    """
    print(f"\n📊 Calculating lead-lag relationships...")
    
    # Calculate momentum for both assets
    leading_momentum = calculate_momentum_indicator(leading_asset)
    lagging_momentum = calculate_momentum_indicator(lagging_asset)
    
    # Volume imbalance for leading asset
    leading_volume_imbalance = (leading_asset['volume'].values - 
                               pd.Series(leading_asset['volume']).rolling(20).mean().values)
    
    # Align data
    min_len = min(len(leading_momentum), len(lagging_momentum))
    leading_momentum = leading_momentum[:min_len]
    lagging_momentum = lagging_momentum[:min_len]
    leading_volume_imbalance = leading_volume_imbalance[:min_len]
    
    # Calculate lead-lag correlations
    lead_lag_strength = []
    volume_price_correlation = []
    prediction_accuracy = []
    
    for i in range(window, min_len):
        # Lead-lag correlation (leading momentum 5 bars ago vs current lagging momentum)
        if i >= 10:
            corr = np.corrcoef(leading_momentum[i-window:i-5], 
                             lagging_momentum[i-window+5:i])[0, 1]
            lead_lag_strength.append(corr if not np.isnan(corr) else 0.0)
            
            # Volume-price correlation
            vol_corr = np.corrcoef(leading_volume_imbalance[i-window:i], 
                                 lagging_momentum[i-window:i])[0, 1]
            volume_price_correlation.append(vol_corr if not np.isnan(vol_corr) else 0.0)
            
            # Prediction accuracy (did leading indicator predict direction correctly?)
            leading_direction = 1 if leading_momentum[i-5] > leading_momentum[i-6] else -1
            lagging_direction = 1 if lagging_momentum[i] > lagging_momentum[i-1] else -1
            prediction_accuracy.append(1 if leading_direction == lagging_direction else 0)
        else:
            lead_lag_strength.append(0.0)
            volume_price_correlation.append(0.0)
            prediction_accuracy.append(0.0)
    
    # Create results DataFrame
    results = pd.DataFrame({
        'LeadLagStrength': [0.0] * window + lead_lag_strength,
        'VolumeCorrelation': [0.0] * window + volume_price_correlation,
        'PredictionAccuracy': [0.0] * window + prediction_accuracy,
        'LeadingMomentum': leading_momentum,
        'LaggingMomentum': lagging_momentum
    })
    
    # Calculate edge signal
    results['LeadLagEdge'] = (results['LeadLagStrength'].abs() > 0.7) & \
                             (results['VolumeCorrelation'].abs() > 0.5)
    
    # Calculate composite lead-lag score
    results['LeadLagScore'] = (results['LeadLagStrength'].abs() * 0.6 + 
                               results['VolumeCorrelation'].abs() * 0.3 + 
                               results['PredictionAccuracy'] * 0.1)
    
    return results


def backtest_with_lead_lag(data, lead_lag_df, initial_capital=10000, risk_pct=0.02):
    """
    Backtest strategy using lead-lag edge detection
    """
    print(f"\n🔄 Running backtest with lead-lag detection...")
    
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(100, len(data)):
        # Only trade when we have strong lead-lag edge
        has_lead_lag_edge = lead_lag_df.iloc[i]['LeadLagEdge']
        lead_lag_score = lead_lag_df.iloc[i]['LeadLagScore']
        
        # Momentum signal
        momentum_bullish = lead_lag_df.iloc[i]['LaggingMomentum'] > lead_lag_df.iloc[i-1]['LaggingMomentum']
        
        # Calculate ATR for stops
        high_slice = data['high'].iloc[max(0, i-14):i]
        low_slice = data['low'].iloc[max(0, i-14):i]
        close_slice = data['close'].iloc[max(0, i-14):i]
        
        tr1 = high_slice - low_slice
        tr2 = abs(high_slice - close_slice.shift(1))
        tr3 = abs(low_slice - close_slice.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()
        
        current_price = data['close'].iloc[i]
        
        # Entry logic
        if position == 0 and momentum_bullish and has_lead_lag_edge:
            # Position size based on lead-lag score
            position_multiplier = 1.0 + (lead_lag_score * 0.5)  # Up to 1.5x position
            risk_amount = capital * risk_pct * position_multiplier
            
            position_size = risk_amount / (atr * 2.0)
            position = position_size
            entry_price = current_price
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
            
            trades.append({
                'entry_bar': i,
                'entry_price': entry_price,
                'position_size': position,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'lead_lag_score': lead_lag_score,
                'type': 'ENTRY'
            })
        
        # Exit logic
        elif position > 0:
            # Check stops
            if current_price <= stop_loss:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({
                    'exit_bar': i,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'exit_reason': 'STOP_LOSS',
                    'type': 'EXIT'
                })
                position = 0
            elif current_price >= take_profit:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({
                    'exit_bar': i,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'exit_reason': 'TAKE_PROFIT',
                    'type': 'EXIT'
                })
                position = 0
            # Exit on lead-lag edge disappearing
            elif not has_lead_lag_edge and not momentum_bullish:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({
                    'exit_bar': i,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'exit_reason': 'EDGE_LOST',
                    'type': 'EXIT'
                })
                position = 0
        
        equity_curve.append(capital)
    
    return {
        'final_capital': capital,
        'trades': trades,
        'equity_curve': equity_curve
    }


def run_lead_lag_test():
    """Main test function"""
    
    # Download data
    print("\n📥 Downloading data...")
    print("  Leading asset: SPY (market leader)")
    print("  Lagging asset: QQQ (tech sector)")
    
    spy = yf.download('SPY', start='2023-01-01', progress=False)
    qqq = yf.download('QQQ', start='2023-01-01', progress=False)
    
    # Standardize column names
    for df in [spy, qqq]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() for col in df.columns]
        else:
            df.columns = df.columns.str.lower()
    
    print(f"✅ SPY: {len(spy)} bars")
    print(f"✅ QQQ: {len(qqq)} bars")
    
    # Calculate lead-lag relationships
    lead_lag_results = calculate_lead_lag_relationships(spy, qqq, window=50)
    
    print(f"\n📈 LEAD-LAG ANALYSIS RESULTS:")
    print(f"  Mean Lead-Lag Strength:     {lead_lag_results['LeadLagStrength'].mean():.3f}")
    print(f"  Max Lead-Lag Strength:      {lead_lag_results['LeadLagStrength'].max():.3f}")
    print(f"  Mean Volume Correlation:    {lead_lag_results['VolumeCorrelation'].mean():.3f}")
    print(f"  Mean Prediction Accuracy:   {lead_lag_results['PredictionAccuracy'].mean():.3f}")
    print(f"  Mean Lead-Lag Score:        {lead_lag_results['LeadLagScore'].mean():.3f}")
    
    # Edge detection statistics
    strong_edges = lead_lag_results['LeadLagEdge'].sum()
    print(f"\n🎯 EDGE DETECTION:")
    print(f"  Strong Lead-Lag Edges:      {strong_edges} bars ({strong_edges/len(lead_lag_results)*100:.1f}%)")
    print(f"  High Score Edges (>0.7):    {(lead_lag_results['LeadLagScore'] > 0.7).sum()} bars")
    
    # Current status
    current = lead_lag_results.iloc[-1]
    print(f"\n📍 CURRENT LEAD-LAG STATUS:")
    print(f"  Lead-Lag Strength:          {current['LeadLagStrength']:.3f}")
    print(f"  Volume Correlation:         {current['VolumeCorrelation']:.3f}")
    print(f"  Prediction Accuracy:        {current['PredictionAccuracy']:.3f}")
    print(f"  Lead-Lag Score:             {current['LeadLagScore']:.3f}")
    print(f"  Edge Present:               {'✓ YES' if current['LeadLagEdge'] else '✗ NO'}")
    
    # Backtest without lead-lag
    print("\n" + "="*80)
    print("  BASELINE BACKTEST (No Lead-Lag Detection)")
    print("="*80)
    
    baseline_results = backtest_without_lead_lag(qqq)
    print(f"\n📊 BASELINE RESULTS:")
    print(f"  Final Capital:    ${baseline_results['final_capital']:,.2f}")
    print(f"  Total Return:     {(baseline_results['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:     {len(baseline_results['trades'])}")
    
    # Backtest with lead-lag
    print("\n" + "="*80)
    print("  ENHANCED BACKTEST (With Lead-Lag Detection)")
    print("="*80)
    
    enhanced_results = backtest_with_lead_lag(qqq, lead_lag_results)
    print(f"\n📊 ENHANCED RESULTS:")
    print(f"  Final Capital:    ${enhanced_results['final_capital']:,.2f}")
    print(f"  Total Return:     {(enhanced_results['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:     {len(enhanced_results['trades'])}")
    
    # Calculate improvement
    baseline_return = (baseline_results['final_capital']/10000-1)*100
    enhanced_return = (enhanced_results['final_capital']/10000-1)*100
    improvement = enhanced_return - baseline_return
    
    print(f"\n" + "="*80)
    print("  COMPARISON")
    print("="*80)
    print(f"  Baseline Return:       {baseline_return:.2f}%")
    print(f"  Enhanced Return:       {enhanced_return:.2f}%")
    print(f"  Improvement:           {improvement:+.2f}%")
    print(f"  Improvement Factor:    {enhanced_results['final_capital']/baseline_results['final_capital']:.2f}x")
    
    # Calculate Sharpe ratios
    baseline_returns = np.diff(baseline_results['equity_curve']) / baseline_results['equity_curve'][:-1]
    enhanced_returns = np.diff(enhanced_results['equity_curve']) / enhanced_results['equity_curve'][:-1]
    
    baseline_sharpe = np.mean(baseline_returns) / np.std(baseline_returns) * np.sqrt(252)
    enhanced_sharpe = np.mean(enhanced_returns) / np.std(enhanced_returns) * np.sqrt(252)
    
    print(f"\n  Baseline Sharpe:       {baseline_sharpe:.2f}")
    print(f"  Enhanced Sharpe:       {enhanced_sharpe:.2f}")
    print(f"  Sharpe Improvement:    {(enhanced_sharpe/baseline_sharpe-1)*100:+.1f}%")
    
    print(f"\n✅ Lead-lag detection test complete!")
    print(f"\n🎯 KEY FINDINGS:")
    print(f"  • Lead-lag edges detected in {strong_edges/len(lead_lag_results)*100:.1f}% of bars")
    print(f"  • Strategy improvement: {improvement:+.2f}%")
    print(f"  • Sharpe improvement: {(enhanced_sharpe/baseline_sharpe-1)*100:+.1f}%")
    print(f"  • Expected from research: 25-35% Sharpe improvement, 51-72% faster detection")
    
    return {
        'lead_lag_results': lead_lag_results,
        'baseline_results': baseline_results,
        'enhanced_results': enhanced_results,
        'sharpe_improvement': (enhanced_sharpe/baseline_sharpe-1)*100
    }


def backtest_without_lead_lag(data, initial_capital=10000, risk_pct=2.0):
    """Baseline backtest using YOUR actual momentum tracker"""
    result = backtest_baseline(data, initial_capital=initial_capital, 
                               risk_pct=risk_pct, trailing_stop_pct=3.0, long_only=True)
    return result


if __name__ == '__main__':
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = run_lead_lag_test()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
