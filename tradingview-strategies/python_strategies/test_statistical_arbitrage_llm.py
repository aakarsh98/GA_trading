"""
STATISTICAL ARBITRAGE & LLM-INSPIRED FACTOR EXTRACTION TEST
Combined test for mean reversion edges and evidence-based factor reasoning

Sources:
- "The Statistical Limit of Arbitrage" (BFI, 2024)
- "LLMFactor: Extracting Profitable Factors through Prompts" (arXiv, 2024)

✅ NOW USING YOUR ACTUAL MOMENTUM TRACKER

Expected: 15-25% Sharpe improvement (stat arb), 20-30% improvement (LLM factors)
"""
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/utils')

# Import YOUR actual momentum tracker
from actual_momentum_tracker import calculate_momentum_indicator as calc_momentum_full, backtest_baseline


import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("\n" + "🤖"*40)
print(" "*5 + "STATISTICAL ARBITRAGE & LLM FACTOR TEST")
print(" "*10 + "Mean Reversion + Evidence-Based Reasoning")
print("🤖"*40)


def calculate_momentum_indicator(df):
    """Calculate momentum using YOUR exact algorithm"""
    result = calc_momentum_full(df, length=7, threshold=2.0)
    return result['momentum']


def calculate_statistical_arbitrage_signals(data, momentum, lookback=50):
    """
    Calculate statistical arbitrage signals based on mean reversion
    
    Args:
        data: Price data
        momentum: Momentum values
        lookback: Lookback period for mean calculation
    
    Returns:
        DataFrame with stat arb signals
    """
    print(f"\n📊 Calculating statistical arbitrage signals...")
    
    results = []
    
    for i in range(lookback, len(data)):
        # Calculate momentum mean and std
        momentum_window = momentum[i-lookback:i]
        momentum_mean = np.mean(momentum_window)
        momentum_std = np.std(momentum_window)
        
        current_momentum = momentum[i]
        
        # Z-score (standard deviations from mean)
        z_score = (current_momentum - momentum_mean) / momentum_std if momentum_std > 0 else 0
        
        # Mean reversion signal
        # Extreme positive = overbought (expect reversion)
        # Extreme negative = oversold (expect bounce)
        mean_reversion_signal = -1 if z_score > 2.0 else 1 if z_score < -2.0 else 0
        
        # Estimate alpha strength and estimation error
        # Correlation between momentum and price changes
        price_changes = np.diff(data['close'].iloc[i-lookback:i+1].values)
        momentum_changes = np.diff(momentum[i-lookback:i+1])
        
        if len(price_changes) > 1 and len(momentum_changes) > 1:
            alpha_strength = np.corrcoef(price_changes, momentum_changes)[0, 1] if len(price_changes) == len(momentum_changes) else 0
            alpha_strength = abs(alpha_strength) if not np.isnan(alpha_strength) else 0
        else:
            alpha_strength = 0
        
        # Estimation error
        estimation_error = np.sqrt(1 - alpha_strength**2) / np.sqrt(lookback) if alpha_strength < 1 else 0
        
        # Reliable edge when alpha strong and error low
        reliable_edge = alpha_strength > 0.3 and estimation_error < 0.4
        
        # Statistical arbitrage edge
        stat_arb_edge = reliable_edge and abs(z_score) > 1.5
        
        results.append({
            'MomentumMean': momentum_mean,
            'MomentumStd': momentum_std,
            'ZScore': z_score,
            'MeanReversionSignal': mean_reversion_signal,
            'AlphaStrength': alpha_strength,
            'EstimationError': estimation_error,
            'ReliableEdge': reliable_edge,
            'StatArbEdge': stat_arb_edge
        })
    
    return pd.DataFrame(results)


def calculate_llm_inspired_factors(data, momentum):
    """
    Calculate LLM-inspired factors using evidence accumulation
    
    Simulates LLM reasoning by combining multiple "prompt" factors
    
    Args:
        data: Price data
        momentum: Momentum values
    
    Returns:
        DataFrame with LLM factor scores
    """
    print(f"\n🤖 Calculating LLM-inspired factors...")
    
    results = []
    
    # Calculate indicators
    sma_20 = data['close'].rolling(20).mean()
    sma_50 = data['close'].rolling(50).mean()
    vol_sma = data['volume'].rolling(50).mean()
    
    for i in range(100, len(data)):
        # Factor Prompt 1: Trending market
        factor_prompt_1 = 1.0 if sma_20.iloc[i] > sma_20.iloc[i-20] else 0.0
        
        # Factor Prompt 2: High volume confirmation
        factor_prompt_2 = 1.0 if data['volume'].iloc[i] > vol_sma.iloc[i] * 1.5 else 0.0
        
        # Factor Prompt 3: Strong buying pressure
        day_range = data['high'].iloc[i] - data['low'].iloc[i]
        if day_range > 0:
            buying_pressure = (data['close'].iloc[i] - data['low'].iloc[i]) / day_range
            factor_prompt_3 = 1.0 if buying_pressure > 0.8 else 0.0
        else:
            factor_prompt_3 = 0.0
        
        # Factor Prompt 4: Momentum confirmation
        factor_prompt_4 = 1.0 if momentum[i] > momentum[i-10] + 5.0 else 0.0
        
        # Factor Prompt 5: Trend alignment
        factor_prompt_5 = 1.0 if data['close'].iloc[i] > sma_50.iloc[i] else 0.0
        
        # Evidence accumulation (LLM-like reasoning)
        # Weighted combination of factors
        evidence_score = (factor_prompt_1 * 0.25 + 
                         factor_prompt_2 * 0.20 + 
                         factor_prompt_3 * 0.20 + 
                         factor_prompt_4 * 0.20 +
                         factor_prompt_5 * 0.15)
        
        # LLM edge: high evidence threshold
        llm_edge = evidence_score > 0.75
        
        # Calculate factor confidence
        factor_agreement = np.std([factor_prompt_1, factor_prompt_2, factor_prompt_3, 
                                  factor_prompt_4, factor_prompt_5])
        factor_confidence = 1.0 - factor_agreement  # Lower std = higher agreement
        
        results.append({
            'FactorPrompt1_Trending': factor_prompt_1,
            'FactorPrompt2_Volume': factor_prompt_2,
            'FactorPrompt3_Buying': factor_prompt_3,
            'FactorPrompt4_Momentum': factor_prompt_4,
            'FactorPrompt5_Trend': factor_prompt_5,
            'EvidenceScore': evidence_score,
            'FactorConfidence': factor_confidence,
            'LLMEdge': llm_edge
        })
    
    return pd.DataFrame(results)


def backtest_combined_strategy(data, stat_arb_df, llm_df, initial_capital=10000, risk_pct=0.02):
    """Backtest with statistical arbitrage and LLM factors"""
    print(f"\n🔄 Running backtest with combined signals...")
    
    momentum = calculate_momentum_indicator(data)
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(100, len(data)):
        # Align dataframes
        stat_idx = i - 50 if i >= 50 else 0
        llm_idx = i - 100 if i >= 100 else 0
        
        if stat_idx >= len(stat_arb_df) or llm_idx >= len(llm_df):
            break
        
        # Get signals
        stat_arb_edge = stat_arb_df.iloc[stat_idx]['StatArbEdge']
        mean_rev_signal = stat_arb_df.iloc[stat_idx]['MeanReversionSignal']
        
        llm_edge = llm_df.iloc[llm_idx]['LLMEdge']
        evidence_score = llm_df.iloc[llm_idx]['EvidenceScore']
        factor_confidence = llm_df.iloc[llm_idx]['FactorConfidence']
        
        # Combined edge: Both stat arb and LLM agree
        combined_edge = stat_arb_edge and llm_edge
        
        # Momentum signal
        momentum_bullish = momentum[i] > momentum[i-1]
        
        # Calculate ATR
        high_slice = data['high'].iloc[max(0, i-14):i]
        low_slice = data['low'].iloc[max(0, i-14):i]
        close_slice = data['close'].iloc[max(0, i-14):i]
        
        tr1 = high_slice - low_slice
        tr2 = abs(high_slice - close_slice.shift(1))
        tr3 = abs(low_slice - close_slice.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()
        
        current_price = data['close'].iloc[i]
        
        # Entry
        if position == 0 and momentum_bullish and combined_edge:
            # Position sizing based on factor confidence
            position_multiplier = 1.0 + (factor_confidence * 0.5)
            risk_amount = capital * risk_pct * position_multiplier
            
            position_size = risk_amount / (atr * 2.0)
            position = position_size
            entry_price = current_price
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
            
            trades.append({
                'entry_bar': i,
                'entry_price': entry_price,
                'evidence_score': evidence_score,
                'factor_confidence': factor_confidence,
                'type': 'ENTRY'
            })
        
        # Exit
        elif position > 0:
            if current_price <= stop_loss:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'STOP', 'type': 'EXIT'})
                position = 0
            elif current_price >= take_profit:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'TARGET', 'type': 'EXIT'})
                position = 0
            elif not llm_edge or not momentum_bullish:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'SIGNAL', 'type': 'EXIT'})
                position = 0
        
        equity_curve.append(capital)
    
    return {'final_capital': capital, 'trades': trades, 'equity_curve': equity_curve}


def run_combined_test():
    """Main test function"""
    
    print("\n📥 Downloading data...")
    spy = yf.download('SPY', start='2022-01-01', progress=False)
    
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = [col[0].lower() for col in spy.columns]
    else:
        spy.columns = spy.columns.str.lower()
    
    print(f"✅ Downloaded {len(spy)} bars")
    
    # Calculate momentum
    momentum = calculate_momentum_indicator(spy)
    
    # Calculate statistical arbitrage signals
    stat_arb_results = calculate_statistical_arbitrage_signals(spy, momentum, lookback=50)
    
    print(f"\n📈 STATISTICAL ARBITRAGE RESULTS:")
    print(f"  Mean Z-Score:           {stat_arb_results['ZScore'].mean():.3f}")
    print(f"  Mean Alpha Strength:    {stat_arb_results['AlphaStrength'].mean():.3f}")
    print(f"  Mean Est. Error:        {stat_arb_results['EstimationError'].mean():.3f}")
    print(f"  Reliable Edges:         {stat_arb_results['ReliableEdge'].sum()} "
          f"({stat_arb_results['ReliableEdge'].sum()/len(stat_arb_results)*100:.1f}%)")
    print(f"  Stat Arb Edges:         {stat_arb_results['StatArbEdge'].sum()} "
          f"({stat_arb_results['StatArbEdge'].sum()/len(stat_arb_results)*100:.1f}%)")
    
    # Calculate LLM-inspired factors
    llm_results = calculate_llm_inspired_factors(spy, momentum)
    
    print(f"\n🤖 LLM FACTOR RESULTS:")
    print(f"  Mean Evidence Score:    {llm_results['EvidenceScore'].mean():.3f}")
    print(f"  Mean Factor Confidence: {llm_results['FactorConfidence'].mean():.3f}")
    print(f"  LLM Edges:              {llm_results['LLMEdge'].sum()} "
          f"({llm_results['LLMEdge'].sum()/len(llm_results)*100:.1f}%)")
    print(f"\n  Factor Activation Rates:")
    print(f"    Trending:    {llm_results['FactorPrompt1_Trending'].mean()*100:.1f}%")
    print(f"    Volume:      {llm_results['FactorPrompt2_Volume'].mean()*100:.1f}%")
    print(f"    Buying:      {llm_results['FactorPrompt3_Buying'].mean()*100:.1f}%")
    print(f"    Momentum:    {llm_results['FactorPrompt4_Momentum'].mean()*100:.1f}%")
    print(f"    Trend:       {llm_results['FactorPrompt5_Trend'].mean()*100:.1f}%")
    
    # Run backtests
    print("\n" + "="*80)
    print("  BASELINE BACKTEST")
    print("="*80)
    baseline = backtest_baseline_test(spy)
    print(f"\n  Final Capital:  ${baseline['final_capital']:,.2f}")
    print(f"  Total Return:   {(baseline['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:   {len(baseline.get('trades', []))}")
    
    print("\n" + "="*80)
    print("  ENHANCED BACKTEST (Stat Arb + LLM Factors)")
    print("="*80)
    enhanced = backtest_combined_strategy(spy, stat_arb_results, llm_results)
    print(f"\n  Final Capital:  ${enhanced['final_capital']:,.2f}")
    print(f"  Total Return:   {(enhanced['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:   {len(enhanced.get('trades', []))}")
    
    # Comparison
    baseline_ret = (baseline['final_capital']/10000-1)*100
    enhanced_ret = (enhanced['final_capital']/10000-1)*100
    improvement = enhanced_ret - baseline_ret
    
    print(f"\n" + "="*80)
    print("  COMPARISON")
    print("="*80)
    print(f"  Baseline Return:     {baseline_ret:.2f}%")
    print(f"  Enhanced Return:     {enhanced_ret:.2f}%")
    print(f"  Improvement:         {improvement:+.2f}%")
    print(f"  Improvement Factor:  {enhanced['final_capital']/baseline['final_capital']:.2f}x")
    
    baseline_returns = np.diff(baseline['equity_curve']) / baseline['equity_curve'][:-1]
    enhanced_returns = np.diff(enhanced['equity_curve']) / enhanced['equity_curve'][:-1]
    
    baseline_sharpe = np.mean(baseline_returns) / np.std(baseline_returns) * np.sqrt(252) if np.std(baseline_returns) > 0 else 0
    enhanced_sharpe = np.mean(enhanced_returns) / np.std(enhanced_returns) * np.sqrt(252) if np.std(enhanced_returns) > 0 else 0
    
    print(f"\n  Baseline Sharpe:     {baseline_sharpe:.2f}")
    print(f"  Enhanced Sharpe:     {enhanced_sharpe:.2f}")
    if baseline_sharpe > 0:
        print(f"  Sharpe Improvement:  {(enhanced_sharpe/baseline_sharpe-1)*100:+.1f}%")
    
    print(f"\n✅ Test complete!")
    print(f"  Expected: 15-25% (stat arb) + 20-30% (LLM) = 35-55% combined improvement")
    
    return {'stat_arb': stat_arb_results, 'llm': llm_results, 'baseline': baseline, 'enhanced': enhanced}


def backtest_baseline_test(data, initial_capital=10000, risk_pct=2.0):
    """Baseline backtest using YOUR actual momentum tracker"""
    result = backtest_baseline(data, initial_capital=initial_capital, 
                               risk_pct=risk_pct, long_only=True)
    return result


if __name__ == '__main__':
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = run_combined_test()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
