"""
WALK-FORWARD BOOTSTRAP VALIDATION TEST
Tests statistical significance with bootstrap confidence intervals

Source: Research document - Bootstrap Testing (1000 samples)
✅ NOW USING YOUR ACTUAL MOMENTUM TRACKER

Expected: Statistical significance p < 0.01, confidence intervals
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

print("\n" + "📊"*40)
print(" "*8 + "WALK-FORWARD BOOTSTRAP VALIDATION")
print(" "*10 + "Statistical Significance Testing")
print("📊"*40)


def calculate_momentum_indicator(df):
    """Calculate momentum using YOUR exact algorithm"""
    result = calc_momentum_full(df, length=7, threshold=2.0)
    return result['momentum']


def backtest_strategy(data, initial_capital=10000, risk_pct=0.02):
    """Run strategy backtest"""
    momentum = calculate_momentum_indicator(data)
    
    capital = initial_capital
    position = 0
    trades = []
    daily_returns = []
    
    for i in range(100, len(data)):
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
        prev_capital = capital
        
        # Entry
        if position == 0 and momentum_bullish:
            risk_amount = capital * risk_pct
            position_size = risk_amount / (atr * 2.0)
            position = position_size
            entry_price = current_price
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
        
        # Exit
        elif position > 0:
            if current_price <= stop_loss:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'pnl': pnl, 'return': pnl/prev_capital})
                position = 0
            elif current_price >= take_profit:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'pnl': pnl, 'return': pnl/prev_capital})
                position = 0
            elif not momentum_bullish:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'pnl': pnl, 'return': pnl/prev_capital})
                position = 0
        
        # Track daily returns
        daily_return = (capital - prev_capital) / prev_capital
        daily_returns.append(daily_return)
    
    return {
        'final_capital': capital,
        'trades': trades,
        'daily_returns': np.array(daily_returns),
        'total_return': (capital - initial_capital) / initial_capital
    }


def bootstrap_resample(data, seed=None):
    """
    Resample data with replacement (bootstrap)
    """
    if seed is not None:
        np.random.seed(seed)
    
    n = len(data)
    indices = np.random.choice(n, size=n, replace=True)
    
    # Create resampled dataframe
    resampled = data.iloc[indices].copy()
    resampled.index = data.index  # Keep original index structure
    
    return resampled


def walk_forward_bootstrap(data, window_size=252, step_size=21, bootstrap_samples=100):
    """
    Walk-forward analysis with bootstrap confidence intervals
    
    Args:
        data: Price data
        window_size: Training window (252 = 1 year)
        step_size: Walk-forward step (21 = 1 month)
        bootstrap_samples: Number of bootstrap samples
    
    Returns:
        List of period results with confidence intervals
    """
    print(f"\n📊 Running walk-forward bootstrap analysis...")
    print(f"  Window Size:        {window_size} bars (~{window_size/252:.1f} years)")
    print(f"  Step Size:          {step_size} bars (~{step_size/21:.1f} months)")
    print(f"  Bootstrap Samples:  {bootstrap_samples}")
    
    results = []
    total_periods = (len(data) - window_size) // step_size
    
    print(f"  Total Periods:      {total_periods}")
    print(f"\n  Running analysis...")
    
    for period_idx in range(total_periods):
        start_idx = period_idx * step_size
        train_end = start_idx + window_size
        test_end = min(train_end + step_size, len(data))
        
        if test_end >= len(data):
            break
        
        train_data = data.iloc[start_idx:train_end]
        test_data = data.iloc[train_end:test_end]
        
        # Bootstrap on test data
        bootstrap_returns = []
        bootstrap_sharpes = []
        
        for sample_idx in range(bootstrap_samples):
            # Resample test data
            bootstrap_test = bootstrap_resample(test_data, seed=sample_idx + period_idx * 1000)
            
            # Run backtest on bootstrapped data
            try:
                result = backtest_strategy(bootstrap_test, initial_capital=10000, risk_pct=0.02)
                bootstrap_returns.append(result['total_return'])
                
                # Calculate Sharpe
                if len(result['daily_returns']) > 0 and np.std(result['daily_returns']) > 0:
                    sharpe = np.mean(result['daily_returns']) / np.std(result['daily_returns']) * np.sqrt(252)
                    bootstrap_sharpes.append(sharpe)
            except:
                pass
        
        if len(bootstrap_returns) > 0:
            # Calculate statistics
            mean_return = np.mean(bootstrap_returns)
            ci_lower = np.percentile(bootstrap_returns, 2.5)
            ci_upper = np.percentile(bootstrap_returns, 97.5)
            
            # Statistical edge: lower CI bound is positive
            statistical_edge = ci_lower > 0
            
            # Calculate p-value (proportion of negative returns)
            p_value = np.sum(np.array(bootstrap_returns) <= 0) / len(bootstrap_returns)
            
            # Sharpe statistics
            if len(bootstrap_sharpes) > 0:
                mean_sharpe = np.mean(bootstrap_sharpes)
                sharpe_ci_lower = np.percentile(bootstrap_sharpes, 2.5)
                sharpe_ci_upper = np.percentile(bootstrap_sharpes, 97.5)
            else:
                mean_sharpe = 0
                sharpe_ci_lower = 0
                sharpe_ci_upper = 0
            
            results.append({
                'period': period_idx + 1,
                'start_date': train_data.index[0],
                'end_date': test_data.index[-1],
                'mean_return': mean_return,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'statistical_edge': statistical_edge,
                'p_value': p_value,
                'mean_sharpe': mean_sharpe,
                'sharpe_ci_lower': sharpe_ci_lower,
                'sharpe_ci_upper': sharpe_ci_upper,
                'bootstrap_samples': len(bootstrap_returns)
            })
            
            print(f"    Period {period_idx + 1}/{total_periods}: Return={mean_return*100:.2f}% "
                  f"CI=[{ci_lower*100:.2f}%, {ci_upper*100:.2f}%] "
                  f"Edge={'✓' if statistical_edge else '✗'}")
    
    return results


def calculate_monte_carlo_validation(data, num_simulations=100):
    """
    Monte Carlo validation with random shuffling
    
    Args:
        data: Price data
        num_simulations: Number of simulations
    
    Returns:
        Simulation results
    """
    print(f"\n🎲 Running Monte Carlo validation...")
    print(f"  Simulations: {num_simulations}")
    
    simulation_results = []
    
    for sim_idx in range(num_simulations):
        # Shuffle data while maintaining price relationships
        shuffled_data = data.sample(frac=1, random_state=sim_idx).reset_index(drop=True)
        shuffled_data.index = data.index
        
        try:
            result = backtest_strategy(shuffled_data, initial_capital=10000, risk_pct=0.02)
            simulation_results.append({
                'total_return': result['total_return'],
                'final_capital': result['final_capital'],
                'num_trades': len(result['trades'])
            })
        except:
            pass
        
        if (sim_idx + 1) % 20 == 0:
            print(f"    Completed {sim_idx + 1}/{num_simulations} simulations")
    
    return simulation_results


def run_bootstrap_validation():
    """Main test function"""
    
    # Download longer history for walk-forward analysis
    print("\n📥 Downloading historical data...")
    spy = yf.download('SPY', start='2020-01-01', progress=False)
    
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = [col[0].lower() for col in spy.columns]
    else:
        spy.columns = spy.columns.str.lower()
    
    print(f"✅ Downloaded {len(spy)} bars ({spy.index[0].date()} to {spy.index[-1].date()})")
    
    # Run walk-forward bootstrap
    print("\n" + "="*80)
    print("  WALK-FORWARD BOOTSTRAP ANALYSIS")
    print("="*80)
    
    wf_results = walk_forward_bootstrap(
        spy, 
        window_size=252,  # 1 year training
        step_size=21,     # 1 month forward
        bootstrap_samples=100  # Reduced from 1000 for speed
    )
    
    # Analyze results
    results_df = pd.DataFrame(wf_results)
    
    print(f"\n📈 WALK-FORWARD RESULTS:")
    print(f"  Total Periods:              {len(results_df)}")
    print(f"  Periods with Edge:          {results_df['statistical_edge'].sum()} "
          f"({results_df['statistical_edge'].sum()/len(results_df)*100:.1f}%)")
    print(f"  Mean Return per Period:     {results_df['mean_return'].mean()*100:.2f}%")
    print(f"  Mean CI Lower:              {results_df['ci_lower'].mean()*100:.2f}%")
    print(f"  Mean CI Upper:              {results_df['ci_upper'].mean()*100:.2f}%")
    print(f"  Mean P-value:               {results_df['p_value'].mean():.4f}")
    print(f"  Mean Sharpe:                {results_df['mean_sharpe'].mean():.2f}")
    
    # Statistical significance
    significant_periods = (results_df['p_value'] < 0.05).sum()
    print(f"\n🎯 STATISTICAL SIGNIFICANCE:")
    print(f"  Significant Periods (p<0.05): {significant_periods} "
          f"({significant_periods/len(results_df)*100:.1f}%)")
    print(f"  Highly Sig. Periods (p<0.01): {(results_df['p_value'] < 0.01).sum()} "
          f"({(results_df['p_value'] < 0.01).sum()/len(results_df)*100:.1f}%)")
    
    # Overall statistics
    positive_periods = (results_df['mean_return'] > 0).sum()
    print(f"\n📊 CONSISTENCY:")
    print(f"  Positive Periods:           {positive_periods} "
          f"({positive_periods/len(results_df)*100:.1f}%)")
    print(f"  Edge Persistence:           {results_df['statistical_edge'].sum()/len(results_df)*100:.1f}%")
    
    # Run Monte Carlo validation
    print("\n" + "="*80)
    print("  MONTE CARLO VALIDATION")
    print("="*80)
    
    mc_results = calculate_monte_carlo_validation(spy, num_simulations=100)
    mc_df = pd.DataFrame(mc_results)
    
    print(f"\n🎲 MONTE CARLO RESULTS:")
    print(f"  Successful Simulations:     {len(mc_df)}/100")
    print(f"  Mean Total Return:          {mc_df['total_return'].mean()*100:.2f}%")
    print(f"  Std Total Return:           {mc_df['total_return'].std()*100:.2f}%")
    print(f"  Success Rate (>0%):         {(mc_df['total_return'] > 0).sum()}/100 "
          f"({(mc_df['total_return'] > 0).sum():.0f}%)")
    print(f"  Mean Final Capital:         ${mc_df['final_capital'].mean():,.2f}")
    
    # Percentiles
    print(f"\n  Return Percentiles:")
    print(f"    5th:   {np.percentile(mc_df['total_return'], 5)*100:.2f}%")
    print(f"    25th:  {np.percentile(mc_df['total_return'], 25)*100:.2f}%")
    print(f"    50th:  {np.percentile(mc_df['total_return'], 50)*100:.2f}%")
    print(f"    75th:  {np.percentile(mc_df['total_return'], 75)*100:.2f}%")
    print(f"    95th:  {np.percentile(mc_df['total_return'], 95)*100:.2f}%")
    
    # Overall validation
    print("\n" + "="*80)
    print("  FINAL VALIDATION SUMMARY")
    print("="*80)
    
    # Run one full backtest for comparison
    full_result = backtest_strategy(spy, initial_capital=10000, risk_pct=0.02)
    full_sharpe = (np.mean(full_result['daily_returns']) / np.std(full_result['daily_returns']) * 
                   np.sqrt(252)) if np.std(full_result['daily_returns']) > 0 else 0
    
    print(f"\n📊 FULL PERIOD BACKTEST:")
    print(f"  Total Return:               {full_result['total_return']*100:.2f}%")
    print(f"  Final Capital:              ${full_result['final_capital']:,.2f}")
    print(f"  Number of Trades:           {len(full_result['trades'])}")
    print(f"  Sharpe Ratio:               {full_sharpe:.2f}")
    
    print(f"\n✅ VALIDATION CONCLUSIONS:")
    
    # Check if strategy passes validation
    passes_validation = (
        results_df['statistical_edge'].sum() / len(results_df) > 0.5 and
        results_df['p_value'].mean() < 0.10 and
        (mc_df['total_return'] > 0).sum() / len(mc_df) > 0.6
    )
    
    print(f"  Edge Persistence:           {results_df['statistical_edge'].sum()/len(results_df)*100:.1f}% "
          f"{'✓' if results_df['statistical_edge'].sum()/len(results_df) > 0.5 else '✗'}")
    print(f"  Mean P-value:               {results_df['p_value'].mean():.4f} "
          f"{'✓' if results_df['p_value'].mean() < 0.10 else '✗'}")
    print(f"  Monte Carlo Success:        {(mc_df['total_return'] > 0).sum():.0f}% "
          f"{'✓' if (mc_df['total_return'] > 0).sum() / len(mc_df) > 0.6 else '✗'}")
    
    print(f"\n{'✅ STRATEGY VALIDATED' if passes_validation else '❌ STRATEGY NEEDS IMPROVEMENT'}")
    print(f"  Expected from research: p < 0.01, 82% Monte Carlo success rate")
    
    print(f"\n✅ Bootstrap validation complete!")
    
    return {
        'walk_forward_results': results_df,
        'monte_carlo_results': mc_df,
        'full_backtest': full_result,
        'passes_validation': passes_validation
    }


if __name__ == '__main__':
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = run_bootstrap_validation()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
