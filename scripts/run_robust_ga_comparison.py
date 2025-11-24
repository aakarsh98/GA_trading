"""
COMPREHENSIVE GA COMPARISON WITH CROSS-SYMBOL VALIDATION AND ENSEMBLE
Runs both unrestricted and top-down GAs with full robustness testing
Includes: Cross-symbol validation, ensemble methods, complete reports
"""
import sys
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

from ga_mtf_unrestricted_robust import (
    MultiTimeframeDataProvider,
    run_robust_mtf_ga,
    backtest_mtf_strategy
)
from ga_mtf_topdown_robust import (
    TopDownDataProvider,
    run_robust_topdown_ga,
    backtest_topdown_strategy
)
from ga_anti_overfitting import RobustnessAnalyzer

print("=" * 80)
print("  🎯 COMPREHENSIVE ROBUST GA COMPARISON")
print("  ✅ Both Unrestricted & Top-Down")
print("  ✅ Cross-Symbol Validation")
print("  ✅ Ensemble Methods")
print("  ✅ Complete Performance Reports")
print("=" * 80)

# ==============================================================================
# CROSS-SYMBOL VALIDATION
# ==============================================================================

def cross_symbol_validation(gene, backtest_func, provider, symbols: list, 
                            start: datetime, end: datetime) -> dict:
    """
    Test strategy across multiple symbols to ensure generalization
    
    Args:
        gene: Strategy to test
        backtest_func: Backtesting function
        provider: Data provider
        symbols: List of symbols to test
        start, end: Date range
    
    Returns:
        Dict with cross-symbol results
    """
    print(f"\n🔄 Cross-Symbol Validation ({len(symbols)} symbols)...")
    
    results = {}
    
    for symbol in symbols:
        try:
            print(f"   Testing {symbol}...", end=' ')
            
            # Download data
            if hasattr(provider, 'download_multi_timeframe'):
                data = provider.download_multi_timeframe(symbol, start, end)
            else:
                data = provider.download_topdown_data(symbol, start, end)
            
            # Backtest
            symbol_results = backtest_func(gene, data)
            
            results[symbol] = {
                'return': symbol_results['return'],
                'trades': symbol_results['trades'],
                'win_rate': symbol_results.get('win_rate', 0),
                'sharpe': symbol_results.get('sharpe', 0)
            }
            
            print(f"✓ Return: {symbol_results['return']:.2f}%")
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            results[symbol] = {'return': -100, 'error': str(e)}
    
    # Calculate consistency
    returns = [r['return'] for r in results.values() if 'error' not in r]
    
    if len(returns) > 0:
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        consistency = 100 - (std_return / (abs(avg_return) + 1) * 100)
        success_rate = len([r for r in returns if r > 0]) / len(returns) * 100
    else:
        avg_return = -100
        std_return = 0
        consistency = 0
        success_rate = 0
    
    return {
        'results': results,
        'avg_return': avg_return,
        'std_return': std_return,
        'consistency_score': consistency,
        'success_rate': success_rate,
        'symbols_tested': len(symbols),
        'symbols_succeeded': len(returns)
    }

# ==============================================================================
# ENSEMBLE STRATEGY GENERATION
# ==============================================================================

def generate_ensemble_strategies(ga_func, data, n_strategies: int = 5, 
                                 population_size: int = 30, 
                                 generations: int = 30) -> list:
    """
    Generate multiple strategies with different random seeds
    For ensemble voting
    
    Args:
        ga_func: GA function to run
        data: Data to train on
        n_strategies: Number of strategies to generate
        population_size, generations: GA parameters
    
    Returns:
        List of (gene, results) tuples
    """
    print(f"\n🎲 Generating Ensemble ({n_strategies} strategies)...")
    
    strategies = []
    
    for i in range(n_strategies):
        print(f"\n   Strategy {i+1}/{n_strategies} (seed={i*100})...")
        
        # Set random seed for reproducibility
        np.random.seed(i * 100)
        import random
        random.seed(i * 100)
        
        # Run GA
        _, best_gene, best_results, _ = ga_func(
            data,
            population_size=population_size,
            generations=generations,
            elite_size=3,
            complexity_weight=0.3,
            use_validation_split=False  # Use full data for ensemble
        )
        
        strategies.append((best_gene, best_results))
        print(f"   ✓ Return: {best_results['return']:.2f}%")
    
    return strategies

def ensemble_signal(strategies, backtest_func, data, index: int, 
                   vote_threshold: int = 3) -> str:
    """
    Get ensemble signal at specific index
    
    Args:
        strategies: List of (gene, results)
        backtest_func: Backtesting function
        data: Multi-timeframe data
        index: Bar index to check
        vote_threshold: Minimum votes to take action
    
    Returns:
        'buy', 'sell', or 'hold'
    """
    # This is simplified - would need actual signal extraction logic
    # For now, just demonstrate the concept
    
    votes = {'buy': 0, 'sell': 0, 'hold': 0}
    
    for gene, _ in strategies:
        # Would evaluate gene's signal at this index
        # Simplified: random for demonstration
        signal = np.random.choice(['buy', 'sell', 'hold'])
        votes[signal] += 1
    
    # Return signal with most votes if above threshold
    max_vote = max(votes.values())
    
    if max_vote >= vote_threshold:
        return max(votes, key=votes.get)
    else:
        return 'hold'

# ==============================================================================
# COMPREHENSIVE COMPARISON
# ==============================================================================

def run_comprehensive_comparison(primary_symbol: str = 'SPY',
                                test_symbols: list = ['QQQ', 'IWM', 'DIA'],
                                lookback_days: int = 180,
                                population_size: int = 50,
                                generations: int = 50,
                                enable_cross_symbol: bool = True,
                                enable_ensemble: bool = True) -> dict:
    """
    Run complete comparison with all features
    
    Returns:
        Comprehensive results dictionary
    """
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    print(f"\n📊 Configuration:")
    print(f"   Primary Symbol: {primary_symbol}")
    print(f"   Test Symbols: {', '.join(test_symbols)}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Population: {population_size}, Generations: {generations}")
    
    results = {
        'config': {
            'primary_symbol': primary_symbol,
            'test_symbols': test_symbols,
            'period': f"{start_date.date()} to {end_date.date()}",
            'population_size': population_size,
            'generations': generations
        },
        'unrestricted': {},
        'topdown': {},
        'comparison': {}
    }
    
    # === UNRESTRICTED GA ===
    print(f"\n{'='*80}")
    print("🧬 RUNNING UNRESTRICTED GA")
    print(f"{'='*80}")
    
    unrestricted_provider = MultiTimeframeDataProvider()
    unrestricted_data = unrestricted_provider.download_multi_timeframe(
        primary_symbol, start_date, end_date
    )
    
    if len(unrestricted_data) >= 3:
        _, unr_gene, unr_results, unr_validation = run_robust_mtf_ga(
            unrestricted_data,
            population_size=population_size,
            generations=generations,
            complexity_weight=0.3,
            use_validation_split=True
        )
        
        results['unrestricted'] = {
            'train_return': unr_results['return'],
            'val_return': unr_validation.get('val_return', 0),
            'overfitting_gap': unr_validation.get('overfitting_gap', 0),
            'complexity': unr_validation.get('complexity', 0),
            'monte_carlo_robust': unr_validation.get('monte_carlo', {}).get('is_robust', False),
            'parameter_robust': unr_validation.get('sensitivity', {}).get('is_robust', False)
        }
        
        # Cross-symbol validation
        if enable_cross_symbol:
            cross_sym_results = cross_symbol_validation(
                unr_gene, backtest_mtf_strategy, unrestricted_provider,
                test_symbols, start_date, end_date
            )
            results['unrestricted']['cross_symbol'] = cross_sym_results
        
        # Ensemble
        if enable_ensemble:
            unr_ensemble = generate_ensemble_strategies(
                run_robust_mtf_ga, unrestricted_data, n_strategies=5,
                population_size=30, generations=30
            )
            
            ensemble_returns = [r['return'] for _, r in unr_ensemble]
            results['unrestricted']['ensemble'] = {
                'strategies': len(unr_ensemble),
                'avg_return': np.mean(ensemble_returns),
                'std_return': np.std(ensemble_returns),
                'min_return': np.min(ensemble_returns),
                'max_return': np.max(ensemble_returns)
            }
    else:
        print("❌ Insufficient data for unrestricted GA")
        results['unrestricted']['error'] = 'insufficient_data'
    
    # === TOP-DOWN GA ===
    print(f"\n{'='*80}")
    print("📊 RUNNING TOP-DOWN GA")
    print(f"{'='*80}")
    
    topdown_provider = TopDownDataProvider()
    topdown_data = topdown_provider.download_topdown_data(
        primary_symbol, start_date, end_date
    )
    
    if len(topdown_data) >= 3:
        _, td_gene, td_results, td_validation = run_robust_topdown_ga(
            topdown_data,
            population_size=population_size,
            generations=generations,
            complexity_weight=0.3,
            use_validation_split=True
        )
        
        results['topdown'] = {
            'train_return': td_results['return'],
            'val_return': td_validation.get('val_return', 0),
            'overfitting_gap': td_validation.get('overfitting_gap', 0),
            'complexity': td_validation.get('complexity', 0),
            'monte_carlo_robust': td_validation.get('monte_carlo', {}).get('is_robust', False)
        }
        
        # Cross-symbol validation
        if enable_cross_symbol:
            cross_sym_results = cross_symbol_validation(
                td_gene, backtest_topdown_strategy, topdown_provider,
                test_symbols, start_date, end_date
            )
            results['topdown']['cross_symbol'] = cross_sym_results
        
        # Ensemble
        if enable_ensemble:
            td_ensemble = generate_ensemble_strategies(
                run_robust_topdown_ga, topdown_data, n_strategies=5,
                population_size=30, generations=30
            )
            
            ensemble_returns = [r['return'] for _, r in td_ensemble]
            results['topdown']['ensemble'] = {
                'strategies': len(td_ensemble),
                'avg_return': np.mean(ensemble_returns),
                'std_return': np.std(ensemble_returns)
            }
    else:
        print("❌ Insufficient data for top-down GA")
        results['topdown']['error'] = 'insufficient_data'
    
    # === COMPARISON ===
    print(f"\n{'='*80}")
    print("⚖️  FINAL COMPARISON")
    print(f"{'='*80}")
    
    if 'error' not in results['unrestricted'] and 'error' not in results['topdown']:
        print(f"\n📊 Performance Comparison:")
        print(f"{'='*80}")
        print(f"{'Metric':<30} {'Unrestricted':<20} {'Top-Down':<20}")
        print(f"{'-'*80}")
        
        metrics = [
            ('Train Return', 'train_return'),
            ('Val Return', 'val_return'),
            ('Overfitting Gap', 'overfitting_gap'),
            ('Complexity', 'complexity'),
            ('Monte Carlo Robust', 'monte_carlo_robust'),
        ]
        
        for label, key in metrics:
            unr_val = results['unrestricted'].get(key, 'N/A')
            td_val = results['topdown'].get(key, 'N/A')
            
            if isinstance(unr_val, (int, float)):
                unr_str = f"{unr_val:.2f}"
                td_str = f"{td_val:.2f}"
            else:
                unr_str = str(unr_val)
                td_str = str(td_val)
            
            print(f"{label:<30} {unr_str:<20} {td_str:<20}")
        
        # Determine winner
        print(f"\n{'='*80}")
        
        unr_score = 0
        td_score = 0
        
        # Score: higher val return is better
        if results['unrestricted']['val_return'] > results['topdown']['val_return']:
            unr_score += 1
        else:
            td_score += 1
        
        # Score: lower overfitting gap is better
        unr_gap = abs(results['unrestricted']['overfitting_gap'])
        td_gap = abs(results['topdown']['overfitting_gap'])
        if unr_gap < td_gap:
            unr_score += 1
        else:
            td_score += 1
        
        # Score: lower complexity is better
        if results['unrestricted']['complexity'] < results['topdown']['complexity']:
            unr_score += 1
        else:
            td_score += 1
        
        # Score: robustness tests
        if results['unrestricted']['monte_carlo_robust']:
            unr_score += 1
        if results['topdown']['monte_carlo_robust']:
            td_score += 1
        
        results['comparison'] = {
            'unrestricted_score': unr_score,
            'topdown_score': td_score,
            'winner': 'unrestricted' if unr_score > td_score else 'topdown' if td_score > unr_score else 'tie'
        }
        
        print(f"🏆 WINNER: {results['comparison']['winner'].upper()}")
        print(f"   Unrestricted Score: {unr_score}/4")
        print(f"   Top-Down Score: {td_score}/4")
    
    # Cross-symbol summary
    if enable_cross_symbol:
        print(f"\n{'='*80}")
        print("🌍 Cross-Symbol Validation Summary")
        print(f"{'='*80}")
        
        if 'cross_symbol' in results['unrestricted']:
            cs_unr = results['unrestricted']['cross_symbol']
            print(f"\nUnrestricted:")
            print(f"   Avg Return: {cs_unr['avg_return']:.2f}%")
            print(f"   Consistency: {cs_unr['consistency_score']:.1f}/100")
            print(f"   Success Rate: {cs_unr['success_rate']:.1f}%")
        
        if 'cross_symbol' in results['topdown']:
            cs_td = results['topdown']['cross_symbol']
            print(f"\nTop-Down:")
            print(f"   Avg Return: {cs_td['avg_return']:.2f}%")
            print(f"   Consistency: {cs_td['consistency_score']:.1f}/100")
            print(f"   Success Rate: {cs_td['success_rate']:.1f}%")
    
    # Ensemble summary
    if enable_ensemble:
        print(f"\n{'='*80}")
        print("🎲 Ensemble Summary")
        print(f"{'='*80}")
        
        if 'ensemble' in results['unrestricted']:
            ens_unr = results['unrestricted']['ensemble']
            print(f"\nUnrestricted Ensemble:")
            print(f"   Strategies: {ens_unr['strategies']}")
            print(f"   Avg Return: {ens_unr['avg_return']:.2f}%")
            print(f"   Std Return: {ens_unr['std_return']:.2f}%")
        
        if 'ensemble' in results['topdown']:
            ens_td = results['topdown']['ensemble']
            print(f"\nTop-Down Ensemble:")
            print(f"   Strategies: {ens_td['strategies']}")
            print(f"   Avg Return: {ens_td['avg_return']:.2f}%")
            print(f"   Std Return: {ens_td['std_return']:.2f}%")
    
    return results

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    # Run comprehensive comparison
    results = run_comprehensive_comparison(
        primary_symbol='SPY',
        test_symbols=['QQQ', 'IWM'],  # Reduced for speed
        lookback_days=180,
        population_size=30,  # Smaller for faster execution
        generations=30,
        enable_cross_symbol=True,
        enable_ensemble=True
    )
    
    # Save results
    print(f"\n💾 Saving comprehensive results...")
    
    with open('ga_comprehensive_comparison.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("✅ Saved to: ga_comprehensive_comparison.json")
    
    print(f"\n{'='*80}")
    print("✅ COMPREHENSIVE COMPARISON COMPLETE!")
    print(f"{'='*80}")
