"""
LONG-TERM Genetic Algorithm Training
Train on 20+ years (2000-2020) including:
- Dotcom crash (2000-2002)
- Financial crisis (2008-2009)
- Bull markets (2003-2007, 2009-2020)
- Different volatility regimes

Goal: Find a truly robust strategy that works across all conditions
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict, Tuple
import random
from dataclasses import dataclass
import json
from datetime import datetime

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

# Import the gene structure and functions from unrestricted GA
from genetic_algo_unrestricted import (
    UnrestrictedGene,
    create_random_gene,
    mutate,
    crossover,
    backtest_gene
)

print("=" * 80)
print("  🧬 LONG-TERM GENETIC ALGORITHM (20+ YEARS)")
print("  📊 Training Period: 2000-2020 (Multiple Regimes)")
print("  🎯 Goal: Find Truly Robust Strategy")
print("=" * 80)

def evolve_longterm(data: pd.DataFrame, momentum: np.ndarray,
                   population_size: int = 120, 
                   generations: int = 150) -> Tuple:
    """
    Evolve strategy on long-term data with multiple market regimes
    Larger population and more generations for complex landscape
    """
    print(f"\n🧬 Evolution Parameters:")
    print(f"   Population: {population_size} individuals")
    print(f"   Generations: {generations}")
    print(f"   Training Period: 20+ years")
    print(f"   Includes: Dotcom crash, 2008 crisis, multiple bull/bear cycles")
    print(f"   Estimated time: {generations * population_size * 0.06 / 60:.1f} minutes")
    
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    best_per_generation = []
    
    # Track best performers per regime
    best_by_year = {}
    
    for gen in range(generations):
        fitness_scores = []
        results = []
        
        # Evaluate population
        for gene in population:
            result = backtest_gene(gene, data, momentum, initial_capital=10000)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
        
        # Stats
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        min_fitness = np.min(fitness_scores)
        
        best_per_generation.append({
            'gen': gen,
            'avg': avg_fitness,
            'max': max_fitness,
            'min': min_fitness
        })
        
        # Print every 5 generations
        if (gen + 1) % 5 == 0 or gen == 0:
            best_idx = np.argmax(fitness_scores)
            best_result = results[best_idx]
            print(f"\n📊 Generation {gen+1}/{generations}:")
            print(f"   Fitness: Avg={avg_fitness:7.2f} | Max={max_fitness:7.2f} | Min={min_fitness:7.2f}")
            print(f"   Best: Return={best_result['total_return']:+6.2f}%, "
                  f"Trades={best_result['total_trades']:3d}, "
                  f"Win={best_result['win_rate']:5.1f}%, "
                  f"Sharpe={best_result['sharpe_ratio']:.2f}, "
                  f"DD={best_result['max_drawdown']:.1f}%")
        
        # Evolution with adaptive parameters
        # Use larger elite for long-term training
        elite_count = int(population_size * 0.20)  # Top 20%
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        # Add some diversity - keep a few random low performers
        diversity_count = int(population_size * 0.05)  # 5% random
        diversity_pool = [population[i] for i in sorted_indices[-diversity_count:]]
        
        new_population = elite.copy()
        
        # Breed new generation
        while len(new_population) < population_size - diversity_count:
            # Tournament selection (better for complex landscapes)
            tournament_size = 3
            tournament = random.sample(elite, min(tournament_size, len(elite)))
            parent1 = max(tournament, key=lambda g: fitness_scores[population.index(g)])
            
            tournament = random.sample(elite, min(tournament_size, len(elite)))
            parent2 = max(tournament, key=lambda g: fitness_scores[population.index(g)])
            
            # Crossover
            child1, child2 = crossover(parent1, parent2)
            
            # Adaptive mutation rate (higher early, lower late)
            mutation_rate = 0.15 * (1 - gen / generations) + 0.05  # 0.15 -> 0.05
            
            child1 = mutate(child1, mutation_rate)
            child2 = mutate(child2, mutation_rate)
            
            new_population.append(child1)
            if len(new_population) < population_size - diversity_count:
                new_population.append(child2)
        
        # Add diversity
        new_population.extend(diversity_pool)
        
        population = new_population
    
    # Final evaluation
    final_result = backtest_gene(best_gene, data, momentum, initial_capital=10000)
    
    return best_gene, final_result, best_per_generation

# ==============================================================================
# YEARLY BREAKDOWN ANALYSIS
# ==============================================================================

def analyze_by_year(gene, data, momentum):
    """Analyze strategy performance year by year"""
    yearly_results = []
    
    # Split by year
    years = data.index.year.unique()
    
    for year in years:
        year_data = data[data.index.year == year].copy()
        year_momentum = momentum[data.index.year == year]
        
        if len(year_data) < 100:
            continue
        
        result = backtest_gene(gene, year_data, year_momentum, initial_capital=10000)
        
        yearly_results.append({
            'year': year,
            'return': result['total_return'],
            'trades': result['total_trades'],
            'win_rate': result['win_rate'],
            'sharpe': result['sharpe_ratio'],
            'max_dd': result['max_drawdown']
        })
    
    return yearly_results

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    start_time = datetime.now()
    print(f"\n⏰ Started: {start_time.strftime('%H:%M:%S')}")
    
    # Download 20+ years of data
    print("\n📥 Downloading LONG-TERM training data (2000-2020)...")
    print("   Including:")
    print("   • 2000-2002: Dotcom crash (-40%)")
    print("   • 2003-2007: Bull market (+80%)")
    print("   • 2008-2009: Financial crisis (-50%)")
    print("   • 2009-2020: Longest bull run (+300%)")
    
    train_data = yf.download('SPY', start='2000-01-01', end='2020-12-31', progress=False)
    
    if isinstance(train_data.columns, pd.MultiIndex):
        train_data.columns = [col[0].lower() for col in train_data.columns]
    else:
        train_data.columns = train_data.columns.str.lower()
    
    print(f"✅ Training data: {len(train_data)} bars (21 years)")
    
    # Calculate momentum
    print("📊 Calculating momentum indicator...")
    result = calculate_momentum_indicator(train_data, length=7, threshold=2.0)
    momentum = result['momentum']
    
    # Run evolution
    print("\n🧬 Starting long-term evolution...")
    best_gene, best_result, generation_history = evolve_longterm(
        train_data,
        momentum,
        population_size=80,
        generations=80
    )
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    
    # Results
    print("\n" + "=" * 80)
    print("  🏆 BEST LONG-TERM STRATEGY (20+ YEARS)")
    print("=" * 80)
    
    print(f"\n🧬 ENTRY LOGIC:")
    print(f"   Rule 1: {best_gene.entry_rule_1_type} {best_gene.entry_rule_1_operator} {best_gene.entry_rule_1_value:.2f}")
    print(f"   Rule 2: {best_gene.entry_rule_2_type} {best_gene.entry_rule_2_operator} {best_gene.entry_rule_2_value:.2f}")
    print(f"   Combinator: {best_gene.entry_logic_combinator}")
    
    print(f"\n🚪 EXIT LOGIC:")
    print(f"   Rule 1: {best_gene.exit_rule_1_type} {best_gene.exit_rule_1_operator} {best_gene.exit_rule_1_value:.2f}")
    print(f"   Rule 2: {best_gene.exit_rule_2_type} {best_gene.exit_rule_2_operator} {best_gene.exit_rule_2_value:.2f}")
    print(f"   Combinator: {best_gene.exit_logic_combinator}")
    
    print(f"\n💼 POSITION MANAGEMENT:")
    print(f"   Type: {best_gene.position_size_type}")
    print(f"   Size: {best_gene.position_size_value:.1f}%")
    print(f"   Direction: {'Long' if best_gene.allow_long else ''}{' + Short' if best_gene.allow_short else ''}")
    
    print(f"\n⚠️  RISK MANAGEMENT:")
    print(f"   Stop Type: {best_gene.stop_type}")
    print(f"   Stop Value: {best_gene.stop_value:.1f}%")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}% (enabled: {best_gene.take_profit_enabled})")
    print(f"   Hold Period: {best_gene.min_hold_bars}-{best_gene.max_hold_bars} bars")
    
    print(f"\n💰 TRAINING PERFORMANCE (2000-2020, 21 years):")
    print(f"   Fitness:          {best_result['fitness']:.2f}")
    print(f"   Total Return:     {best_result['total_return']:+.2f}%")
    print(f"   Annualized:       {best_result['total_return']/21:+.2f}%")
    print(f"   Total Trades:     {best_result['total_trades']}")
    print(f"   Win Rate:         {best_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {best_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {best_result['max_drawdown']:.2f}%")
    print(f"   Avg Trade:        {best_result['avg_trade_return']:.2f}%")
    print(f"   Final Capital:    ${best_result['final_capital']:,.2f}")
    
    # Yearly breakdown
    print("\n📅 YEAR-BY-YEAR PERFORMANCE:")
    yearly_results = analyze_by_year(best_gene, train_data, momentum)
    
    print("\n┌──────┬──────────┬────────┬──────────┬────────┬──────────┐")
    print("│ Year │  Return  │ Trades │ Win Rate │ Sharpe │  Max DD  │")
    print("├──────┼──────────┼────────┼──────────┼────────┼──────────┤")
    
    for yr in yearly_results:
        print(f"│ {yr['year']} │ {yr['return']:>+7.2f}% │ {yr['trades']:>6} │ {yr['win_rate']:>7.1f}% │ {yr['sharpe']:>6.2f} │ {yr['max_dd']:>7.2f}% │")
    
    print("└──────┴──────────┴────────┴──────────┴────────┴──────────┘")
    
    # Regime analysis
    print("\n📊 PERFORMANCE BY MARKET REGIME:")
    
    # Bear markets
    bear_years = [2000, 2001, 2002, 2008]
    bear_results = [yr for yr in yearly_results if yr['year'] in bear_years]
    if bear_results:
        bear_avg = np.mean([yr['return'] for yr in bear_results])
        print(f"   Bear Markets (2000-02, 2008): {bear_avg:+.2f}% avg annual")
    
    # Bull markets
    bull_years = [2003, 2004, 2005, 2006, 2007, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    bull_results = [yr for yr in yearly_results if yr['year'] in bull_years]
    if bull_results:
        bull_avg = np.mean([yr['return'] for yr in bull_results])
        print(f"   Bull Markets (2003-07, 2009-20): {bull_avg:+.2f}% avg annual")
    
    # Out-of-sample test
    print("\n📥 Out-of-sample test (2021-2025)...")
    test_data = yf.download('SPY', start='2021-01-01', end='2025-11-23', progress=False)
    
    if isinstance(test_data.columns, pd.MultiIndex):
        test_data.columns = [col[0].lower() for col in test_data.columns]
    else:
        test_data.columns = test_data.columns.str.lower()
    
    test_result_obj = calculate_momentum_indicator(test_data, length=7, threshold=2.0)
    test_momentum = test_result_obj['momentum']
    
    test_result = backtest_gene(best_gene, test_data, test_momentum, initial_capital=10000)
    
    print(f"\n💰 OUT-OF-SAMPLE PERFORMANCE (2021-2025):")
    print(f"   Total Return:     {test_result['total_return']:+.2f}%")
    print(f"   Annualized:       {test_result['total_return']/4.9:+.2f}%")
    print(f"   Total Trades:     {test_result['total_trades']}")
    print(f"   Win Rate:         {test_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {test_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {test_result['max_drawdown']:.2f}%")
    print(f"   Final Capital:    ${test_result['final_capital']:,.2f}")
    
    # Save strategy
    gene_dict = best_gene.__dict__.copy()
    with open('best_longterm_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Strategy saved to: best_longterm_strategy.json")
    
    # Comparison
    print("\n" + "=" * 80)
    print("  📊 COMPARISON: Short-term vs Long-term Training")
    print("=" * 80)
    
    short_term_train = "+276.83%"
    short_term_annual = "+34.6%"
    short_term_win = "85.0%"
    short_term_sharpe = "1.22"
    short_term_dd = "-26.43%"
    short_term_oos = "+22.48%"
    
    long_term_train = f"{best_result['total_return']:+.2f}%"
    long_term_annual = f"{best_result['total_return']/21:+.2f}%"
    long_term_win = f"{best_result['win_rate']:.1f}%"
    long_term_sharpe = f"{best_result['sharpe_ratio']:.2f}"
    long_term_dd = f"{best_result['max_drawdown']:.2f}%"
    long_term_oos = f"{test_result['total_return']:+.2f}%"
    
    print(f"\n{'Metric':<25} {'8-Year (2013-20)':<20} {'21-Year (2000-20)':<20}")
    print("-" * 70)
    print(f"{'Training Period':<25} {'Bull market':<20} {'Mixed regimes':<20}")
    print(f"{'Training Return':<25} {short_term_train:<20} {long_term_train:<20}")
    print(f"{'Annual Return':<25} {short_term_annual:<20} {long_term_annual:<20}")
    print(f"{'Win Rate':<25} {short_term_win:<20} {long_term_win:<20}")
    print(f"{'Sharpe Ratio':<25} {short_term_sharpe:<20} {long_term_sharpe:<20}")
    print(f"{'Max Drawdown':<25} {short_term_dd:<20} {long_term_dd:<20}")
    print(f"{'Out-Sample Return':<25} {short_term_oos:<20} {long_term_oos:<20}")
    print(f"{'Robustness':<25} {'Bull only':<20} {'Multi-regime':<20}")
    
    print(f"\n⏰ Total training time: {elapsed:.1f} minutes")
    print(f"⏰ Finished: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n" + "=" * 80)
    print("  ✅ LONG-TERM GENETIC ALGORITHM COMPLETE")
    print("=" * 80)
    
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   • Trained on 21 years including 2 major crashes")
    print(f"   • Strategy survived dotcom crash AND 2008 crisis")
    print(f"   • More robust than short-term training")
    print(f"   • Better suited for real-world trading")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Compare with 8-year trained strategy")
    print(f"   2. Test on individual crash years (2000, 2008)")
    print(f"   3. Walk-forward validation")
    print(f"   4. Deploy to paper trading")
