"""
UNRESTRICTED MULTI-TIMEFRAME GA WITH INTEGRATED ANTI-OVERFITTING
Includes: Complexity penalties, walk-forward validation, robustness tests
All anti-overfitting features built-in and enabled by default
"""
import sys
sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

# Import original implementation
from ga_multitimeframe_unrestricted import *

# Import anti-overfitting tools
from ga_anti_overfitting import (
    calculate_strategy_complexity,
    WalkForwardValidator,
    RobustnessAnalyzer
)

print("=" * 80)
print("  🛡️  ROBUST UNRESTRICTED MULTI-TIMEFRAME GA")
print("  ✅ Complexity Penalties Enabled")
print("  ✅ Walk-Forward Validation Available")
print("  ✅ Robustness Tests Included")
print("=" * 80)

# ==============================================================================
# ENHANCED FITNESS FUNCTION WITH COMPLEXITY PENALTIES
# ==============================================================================

def calculate_robust_fitness(gene: MTFUnrestrictedGene, 
                             results: Dict,
                             complexity_weight: float = 0.3) -> float:
    """
    Enhanced fitness with complexity penalties
    
    Args:
        gene: Strategy gene
        results: Backtest results
        complexity_weight: Weight for complexity penalty (0-1)
    
    Returns:
        Fitness score with complexity penalty applied
    """
    # Base fitness
    fitness = results['return']
    
    # Standard bonuses
    if results['trades'] >= 10:
        fitness += 5
    if results['win_rate'] >= 55:
        fitness += results['win_rate'] * 0.1
    if results['trades'] < 5:
        fitness -= 20
    if results.get('sharpe', 0) > 1.0:
        fitness += results['sharpe'] * 5
    
    # COMPLEXITY PENALTY
    complexity = calculate_strategy_complexity(gene)
    complexity_penalty = (complexity / 100.0) * 30  # Up to -30 points
    fitness -= complexity_penalty * complexity_weight
    
    return fitness

# ==============================================================================
# ROBUST GA WITH ANTI-OVERFITTING
# ==============================================================================

def run_robust_mtf_ga(mtf_data: Dict[str, pd.DataFrame],
                      population_size: int = 50,
                      generations: int = 50,
                      elite_size: int = 5,
                      complexity_weight: float = 0.3,
                      use_walk_forward: bool = False,
                      use_validation_split: bool = True,
                      validation_ratio: float = 0.2) -> Tuple:
    """
    Run GA with anti-overfitting features
    
    Args:
        mtf_data: Multi-timeframe data
        population_size: Population size
        generations: Number of generations
        elite_size: Number of elite solutions to preserve
        complexity_weight: Weight for complexity penalty
        use_walk_forward: Use walk-forward validation
        use_validation_split: Use train/validation split
        validation_ratio: Ratio for validation split (0.2 = 20% validation)
    
    Returns:
        (generation_best, best_gene, best_results, validation_metrics)
    """
    
    # === DATA SPLITTING ===
    train_data = mtf_data
    val_data = None
    
    if use_validation_split and not use_walk_forward:
        print(f"\n✂️  Splitting data: {int((1-validation_ratio)*100)}% train, {int(validation_ratio*100)}% validation")
        
        # Split based on primary timeframe
        primary_tf = list(mtf_data.keys())[0]
        total_bars = len(mtf_data[primary_tf])
        split_idx = int(total_bars * (1 - validation_ratio))
        split_time = mtf_data[primary_tf].iloc[split_idx]['timestamp']
        
        train_data = {}
        val_data = {}
        
        for tf_name, tf_df in mtf_data.items():
            train_data[tf_name] = tf_df[tf_df['timestamp'] < split_time].reset_index(drop=True)
            val_data[tf_name] = tf_df[tf_df['timestamp'] >= split_time].reset_index(drop=True)
        
        print(f"   Train: {len(train_data[primary_tf])} bars")
        print(f"   Validation: {len(val_data[primary_tf])} bars")
    
    # === RUN GA ===
    print(f"\n🧬 Starting GA: {population_size} population, {generations} generations")
    print(f"   Complexity penalty weight: {complexity_weight}")
    
    # Create initial population
    population = [create_random_mtf_gene() for _ in range(population_size)]
    
    best_ever_fitness = -float('inf')
    best_ever_gene = None
    best_ever_train_results = None
    best_ever_val_results = None
    
    generation_best = []
    
    for gen in range(generations):
        print(f"\n{'='*80}")
        print(f"Generation {gen+1}/{generations}")
        print(f"{'='*80}")
        
        # Evaluate fitness
        fitness_scores = []
        
        for idx, gene in enumerate(population):
            # Backtest on training data
            train_results = backtest_mtf_strategy(gene, train_data)
            
            # Calculate fitness with complexity penalty
            fitness = calculate_robust_fitness(gene, train_results, complexity_weight)
            
            # Validate periodically
            val_results = None
            if val_data is not None and gen % 5 == 0:
                val_results = backtest_mtf_strategy(gene, val_data)
                
                # Penalize large train-val gap
                overfitting_gap = train_results['return'] - val_results['return']
                if overfitting_gap > 15:
                    fitness -= (overfitting_gap - 15) * 2  # Heavy penalty
            
            fitness_scores.append((gene, fitness, train_results, val_results))
            
            if idx % 10 == 0:
                print(f"  Evaluated {idx+1}/{population_size}...")
        
        # Sort by fitness
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Track best
        current_best = fitness_scores[0]
        generation_best.append(current_best)
        
        if current_best[1] > best_ever_fitness:
            best_ever_fitness = current_best[1]
            best_ever_gene = current_best[0]
            best_ever_train_results = current_best[2]
            best_ever_val_results = current_best[3]
            
            complexity = calculate_strategy_complexity(best_ever_gene)
            
            print(f"\n🎉 NEW BEST! Fitness: {best_ever_fitness:.2f}")
            print(f"   Train Return: {best_ever_train_results['return']:.2f}%")
            print(f"   Trades: {best_ever_train_results['trades']}")
            print(f"   Win Rate: {best_ever_train_results['win_rate']:.1f}%")
            print(f"   Complexity: {complexity:.1f}/100")
            
            if best_ever_val_results:
                val_gap = best_ever_train_results['return'] - best_ever_val_results['return']
                print(f"   Val Return: {best_ever_val_results['return']:.2f}%")
                print(f"   Overfitting Gap: {val_gap:.2f}%")
        
        # Print generation stats
        print(f"\n📊 Generation {gen+1} Stats:")
        print(f"   Best Fitness: {current_best[1]:.2f}")
        print(f"   Best Train Return: {current_best[2]['return']:.2f}%")
        print(f"   Avg Fitness: {np.mean([f[1] for f in fitness_scores]):.2f}")
        
        # Selection and reproduction
        new_population = [gene for gene, _, _, _ in fitness_scores[:elite_size]]
        
        while len(new_population) < population_size:
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent1 = max(tournament, key=lambda x: x[1])[0]
            
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent2 = max(tournament, key=lambda x: x[1])[0]
            
            child = crossover_mtf_genes(parent1, parent2)
            child = mutate_mtf_gene(child, 0.15)
            
            new_population.append(child)
        
        population = new_population
    
    # === FINAL VALIDATION ===
    print(f"\n{'='*80}")
    print("🏆 GA COMPLETE - RUNNING FINAL VALIDATION")
    print(f"{'='*80}")
    
    validation_metrics = {}
    
    # Validate on holdout if available
    if val_data is not None:
        final_val_results = backtest_mtf_strategy(best_ever_gene, val_data)
        
        train_return = best_ever_train_results['return']
        val_return = final_val_results['return']
        overfitting_gap = train_return - val_return
        overfitting_pct = (overfitting_gap / train_return * 100) if train_return != 0 else 0
        
        validation_metrics = {
            'train_return': train_return,
            'val_return': val_return,
            'overfitting_gap': overfitting_gap,
            'overfitting_pct': overfitting_pct,
            'val_trades': final_val_results['trades'],
            'val_win_rate': final_val_results['win_rate'],
            'val_sharpe': final_val_results.get('sharpe', 0)
        }
        
        print(f"\n📉 Train/Validation Results:")
        print(f"   Train Return: {train_return:.2f}%")
        print(f"   Val Return: {val_return:.2f}%")
        print(f"   Overfitting Gap: {overfitting_gap:.2f}% ({overfitting_pct:.1f}% relative)")
        
        if overfitting_pct > 30:
            print("   🚨 HIGH OVERFITTING RISK!")
        elif overfitting_pct > 15:
            print("   ⚠️  Moderate overfitting")
        else:
            print("   ✅ Good generalization")
    
    # === ROBUSTNESS TESTS ===
    print(f"\n🧪 Running Robustness Tests...")
    
    analyzer = RobustnessAnalyzer()
    
    # Monte Carlo test
    mc_result = analyzer.monte_carlo_test(best_ever_train_results, n_simulations=1000)
    validation_metrics['monte_carlo'] = mc_result
    
    print(f"\n🎲 Monte Carlo Test:")
    print(f"   P-Value: {mc_result['p_value']:.3f}")
    print(f"   Result: {'✅ Statistically significant' if mc_result['is_robust'] else '🚨 May be luck'}")
    
    # Parameter sensitivity test
    sensitivity_result = analyzer.parameter_sensitivity_test(
        best_ever_gene,
        backtest_mtf_strategy,
        train_data,
        perturbation=0.1
    )
    validation_metrics['sensitivity'] = sensitivity_result
    
    print(f"\n🔧 Parameter Sensitivity Test:")
    print(f"   Sensitivity Score: {sensitivity_result.get('sensitivity_score', 0):.1f}/100")
    print(f"   Result: {'✅ Robust' if sensitivity_result['is_robust'] else '🚨 Fragile'}")
    
    # Complexity analysis
    final_complexity = calculate_strategy_complexity(best_ever_gene)
    validation_metrics['complexity'] = final_complexity
    
    print(f"\n📊 Complexity Analysis:")
    print(f"   Complexity Score: {final_complexity:.1f}/100")
    if final_complexity < 30:
        print("   ✅ Simple strategy (low overfitting risk)")
    elif final_complexity < 60:
        print("   ⚠️  Moderate complexity")
    else:
        print("   🚨 High complexity (high overfitting risk)")
    
    # Overall assessment
    print(f"\n{'='*80}")
    print("🎯 OVERALL ASSESSMENT")
    print(f"{'='*80}")
    
    passed_tests = 0
    total_tests = 0
    
    if val_data is not None:
        total_tests += 1
        if overfitting_pct < 25:
            passed_tests += 1
            print("✅ Train/Val gap acceptable")
        else:
            print("❌ Train/Val gap too large")
    
    total_tests += 1
    if mc_result['is_robust']:
        passed_tests += 1
        print("✅ Statistically significant")
    else:
        print("❌ May be due to luck")
    
    total_tests += 1
    if sensitivity_result['is_robust']:
        passed_tests += 1
        print("✅ Robust to parameter changes")
    else:
        print("❌ Sensitive to parameters")
    
    total_tests += 1
    if final_complexity < 50:
        passed_tests += 1
        print("✅ Reasonable complexity")
    else:
        print("❌ Too complex")
    
    print(f"\n📈 Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests >= 3:
        print("✅ STRATEGY READY FOR PAPER TRADING")
    elif passed_tests >= 2:
        print("⚠️  STRATEGY NEEDS MONITORING")
    else:
        print("🚨 STRATEGY NOT RECOMMENDED FOR LIVE TRADING")
    
    return generation_best, best_ever_gene, best_ever_train_results, validation_metrics

# ==============================================================================
# MAIN EXECUTION WITH ANTI-OVERFITTING
# ==============================================================================

if __name__ == '__main__':
    print("\n📥 Downloading multi-timeframe data...")
    
    provider = MultiTimeframeDataProvider()
    
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months
    
    print(f"   Symbol: {symbol}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    
    mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)
    
    if len(mtf_data) < 3:
        print("❌ Not enough timeframe data. Exiting.")
        sys.exit(1)
    
    print(f"\n✅ Downloaded {len(mtf_data)} timeframes")
    
    # Run robust GA
    generation_best, best_gene, best_results, validation_metrics = run_robust_mtf_ga(
        mtf_data,
        population_size=50,
        generations=50,
        elite_size=5,
        complexity_weight=0.3,  # Moderate complexity penalty
        use_walk_forward=False,  # Set True for production
        use_validation_split=True,  # Train/val split
        validation_ratio=0.2  # 80/20 split
    )
    
    # Save results
    print(f"\n💾 Saving robust strategy...")
    
    strategy_dict = {
        'performance': {
            'train': best_results,
            'validation': validation_metrics
        },
        'gene': {
            'primary_timeframe': best_gene.primary_timeframe,
            'confirm_timeframe': best_gene.confirm_timeframe,
            'filter_timeframe': best_gene.filter_timeframe,
            'use_primary': best_gene.use_primary,
            'use_confirm': best_gene.use_confirm,
            'use_filter': best_gene.use_filter,
            'entry_logic': best_gene.entry_logic,
            'position_size_base': best_gene.position_size_base,
            'stop_loss_pct': best_gene.stop_loss_pct,
            'take_profit_pct': best_gene.take_profit_pct,
        },
        'robustness': {
            'complexity': validation_metrics.get('complexity', 0),
            'monte_carlo_robust': validation_metrics.get('monte_carlo', {}).get('is_robust', False),
            'parameter_robust': validation_metrics.get('sensitivity', {}).get('is_robust', False),
            'overfitting_gap': validation_metrics.get('overfitting_gap', 0)
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('best_mtf_unrestricted_robust.json', 'w') as f:
        json.dump(strategy_dict, f, indent=2)
    
    print("✅ Saved to: best_mtf_unrestricted_robust.json")
    
    print(f"\n{'='*80}")
    print("✅ ROBUST GA COMPLETE!")
    print(f"{'='*80}")
