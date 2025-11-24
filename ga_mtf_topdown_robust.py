"""
TOP-DOWN MULTI-TIMEFRAME GA WITH INTEGRATED ANTI-OVERFITTING
Linear hierarchy with built-in robustness features
"""
import sys
sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

# Import original implementation
from ga_multitimeframe_topdown import *

# Import anti-overfitting tools
from ga_anti_overfitting import (
    calculate_strategy_complexity,
    WalkForwardValidator,
    RobustnessAnalyzer
)

print("=" * 80)
print("  🛡️  ROBUST TOP-DOWN MULTI-TIMEFRAME GA")
print("  ✅ Complexity Penalties Enabled")
print("  ✅ Walk-Forward Validation Available")
print("  ✅ Robustness Tests Included")
print("=" * 80)

# Use same robust fitness function as unrestricted
def calculate_robust_fitness(gene: TopDownGene, 
                             results: Dict,
                             complexity_weight: float = 0.3) -> float:
    """Enhanced fitness with complexity penalties"""
    fitness = results['return']
    
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
    complexity_penalty = (complexity / 100.0) * 30
    fitness -= complexity_penalty * complexity_weight
    
    return fitness

def run_robust_topdown_ga(topdown_data: Dict[str, pd.DataFrame],
                          population_size: int = 50,
                          generations: int = 50,
                          elite_size: int = 5,
                          complexity_weight: float = 0.3,
                          use_validation_split: bool = True,
                          validation_ratio: float = 0.2) -> Tuple:
    """Run top-down GA with anti-overfitting"""
    
    # Data splitting
    train_data = topdown_data
    val_data = None
    
    if use_validation_split:
        print(f"\n✂️  Splitting data: {int((1-validation_ratio)*100)}% train, {int(validation_ratio*100)}% validation")
        
        primary_tf = '15m' if '15m' in topdown_data else '1h'
        total_bars = len(topdown_data[primary_tf])
        split_idx = int(total_bars * (1 - validation_ratio))
        split_time = topdown_data[primary_tf].iloc[split_idx]['timestamp']
        
        train_data = {}
        val_data = {}
        
        for tf_name, tf_df in topdown_data.items():
            train_data[tf_name] = tf_df[tf_df['timestamp'] < split_time].reset_index(drop=True)
            val_data[tf_name] = tf_df[tf_df['timestamp'] >= split_time].reset_index(drop=True)
        
        print(f"   Train: {len(train_data[primary_tf])} bars")
        print(f"   Validation: {len(val_data[primary_tf])} bars")
    
    # Run GA
    print(f"\n🧬 Starting Top-Down GA: {population_size} population, {generations} generations")
    
    population = [create_random_topdown_gene() for _ in range(population_size)]
    
    best_ever_fitness = -float('inf')
    best_ever_gene = None
    best_ever_train_results = None
    best_ever_val_results = None
    
    generation_best = []
    
    for gen in range(generations):
        print(f"\n{'='*80}")
        print(f"Generation {gen+1}/{generations}")
        print(f"{'='*80}")
        
        fitness_scores = []
        
        for idx, gene in enumerate(population):
            train_results = backtest_topdown_strategy(gene, train_data)
            fitness = calculate_robust_fitness(gene, train_results, complexity_weight)
            
            val_results = None
            if val_data is not None and gen % 5 == 0:
                val_results = backtest_topdown_strategy(gene, val_data)
                overfitting_gap = train_results['return'] - val_results['return']
                if overfitting_gap > 15:
                    fitness -= (overfitting_gap - 15) * 2
            
            fitness_scores.append((gene, fitness, train_results, val_results))
            
            if idx % 10 == 0:
                print(f"  Evaluated {idx+1}/{population_size}...")
        
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
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
            print(f"   Complexity: {complexity:.1f}/100")
            
            if best_ever_val_results:
                val_gap = best_ever_train_results['return'] - best_ever_val_results['return']
                print(f"   Val Return: {best_ever_val_results['return']:.2f}%")
                print(f"   Overfitting Gap: {val_gap:.2f}%")
        
        print(f"\n📊 Generation {gen+1} Stats:")
        print(f"   Best Fitness: {current_best[1]:.2f}")
        print(f"   Avg Fitness: {np.mean([f[1] for f in fitness_scores]):.2f}")
        
        # Selection and reproduction
        new_population = [gene for gene, _, _, _ in fitness_scores[:elite_size]]
        
        while len(new_population) < population_size:
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent1 = max(tournament, key=lambda x: x[1])[0]
            
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent2 = max(tournament, key=lambda x: x[1])[0]
            
            child = crossover_topdown_genes(parent1, parent2)
            child = mutate_topdown_gene(child, 0.15)
            
            new_population.append(child)
        
        population = new_population
    
    # Final validation
    print(f"\n{'='*80}")
    print("🏆 GA COMPLETE - RUNNING FINAL VALIDATION")
    print(f"{'='*80}")
    
    validation_metrics = {}
    
    if val_data is not None:
        final_val_results = backtest_topdown_strategy(best_ever_gene, val_data)
        
        train_return = best_ever_train_results['return']
        val_return = final_val_results['return']
        overfitting_gap = train_return - val_return
        overfitting_pct = (overfitting_gap / train_return * 100) if train_return != 0 else 0
        
        validation_metrics = {
            'train_return': train_return,
            'val_return': val_return,
            'overfitting_gap': overfitting_gap,
            'overfitting_pct': overfitting_pct
        }
        
        print(f"\n📉 Train/Validation Results:")
        print(f"   Train Return: {train_return:.2f}%")
        print(f"   Val Return: {val_return:.2f}%")
        print(f"   Gap: {overfitting_gap:.2f}% ({overfitting_pct:.1f}% relative)")
    
    # Robustness tests
    print(f"\n🧪 Running Robustness Tests...")
    
    analyzer = RobustnessAnalyzer()
    
    mc_result = analyzer.monte_carlo_test(best_ever_train_results)
    validation_metrics['monte_carlo'] = mc_result
    print(f"   Monte Carlo: {'✅ Robust' if mc_result['is_robust'] else '🚨 May be luck'}")
    
    sensitivity_result = analyzer.parameter_sensitivity_test(
        best_ever_gene, backtest_topdown_strategy, train_data
    )
    validation_metrics['sensitivity'] = sensitivity_result
    print(f"   Sensitivity: {'✅ Robust' if sensitivity_result['is_robust'] else '🚨 Fragile'}")
    
    final_complexity = calculate_strategy_complexity(best_ever_gene)
    validation_metrics['complexity'] = final_complexity
    print(f"   Complexity: {final_complexity:.1f}/100")
    
    return generation_best, best_ever_gene, best_ever_train_results, validation_metrics

if __name__ == '__main__':
    provider = TopDownDataProvider()
    
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    topdown_data = provider.download_topdown_data(symbol, start_date, end_date)
    
    if len(topdown_data) < 3:
        print("❌ Insufficient data")
        sys.exit(1)
    
    print(f"\n✅ Downloaded {len(topdown_data)} timeframes")
    
    _, best_gene, best_results, validation_metrics = run_robust_topdown_ga(
        topdown_data,
        population_size=50,
        generations=50,
        complexity_weight=0.3,
        use_validation_split=True,
        validation_ratio=0.2
    )
    
    # Save
    strategy_dict = {
        'performance': {'train': best_results, 'validation': validation_metrics},
        'robustness': {
            'complexity': validation_metrics.get('complexity', 0),
            'monte_carlo_robust': validation_metrics.get('monte_carlo', {}).get('is_robust', False),
            'overfitting_gap': validation_metrics.get('overfitting_gap', 0)
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('best_mtf_topdown_robust.json', 'w') as f:
        json.dump(strategy_dict, f, indent=2)
    
    print("\n✅ Saved to: best_mtf_topdown_robust.json")
    print("✅ ROBUST TOP-DOWN GA COMPLETE!")
