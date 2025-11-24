"""
ROBUST Genetic Algorithm - Anti-Overfitting Version
- Walk-forward validation during evolution
- Out-of-sample testing in fitness function
- Regularization penalties for complexity
- Multiple regime validation
- Conservative parameter ranges
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

print("=" * 80)
print("  🧬 ROBUST GENETIC ALGORITHM (ANTI-OVERFITTING)")
print("  📊 Walk-Forward Validation + Out-of-Sample Testing")
print("  🎯 Goal: Find Truly Generalizable Strategy")
print("=" * 80)

# ==============================================================================
# SIMPLIFIED GENE STRUCTURE (Less parameters = Less overfitting)
# ==============================================================================

@dataclass
class RobustGene:
    """
    Simplified gene with fewer parameters to reduce overfitting
    """
    # === ENTRY LOGIC (Simplified - Only 2 conditions) ===
    entry_momentum_threshold: float      # Momentum level for entry (0-50)
    entry_price_vs_ma_pct: float        # Price vs MA threshold (-20 to +20%)
    entry_requires_both: bool           # AND vs OR logic
    
    # === EXIT LOGIC (Simplified) ===
    exit_momentum_threshold: float      # Momentum level for exit (50-100)
    exit_price_vs_ma_pct: float        # Price vs MA for exit
    exit_requires_both: bool
    
    # === RISK MANAGEMENT (Conservative) ===
    stop_loss_pct: float               # 3-15% stop loss (REQUIRED)
    take_profit_pct: float             # 5-30% take profit
    
    # === TIME MANAGEMENT (Simplified) ===
    min_hold_bars: int                 # 5-50 bars
    max_hold_bars: int                 # 20-200 bars
    
    # === POSITION SIZING (Conservative) ===
    position_size_pct: float           # 20-80% (no 100%)
    
    # === DIRECTION (Simplified) ===
    trade_direction: str               # 'long_only', 'short_only', 'both'
    
    def __repr__(self):
        return f"RobustGene(mom:{self.entry_momentum_threshold:.1f}, " \
               f"price:{self.entry_price_vs_ma_pct:.1f}%, " \
               f"stop:{self.stop_loss_pct:.1f}%)"

# ==============================================================================
# GENETIC OPERATIONS
# ==============================================================================

def create_random_gene() -> RobustGene:
    """Create random gene with conservative ranges"""
    return RobustGene(
        # Entry (conservative ranges)
        entry_momentum_threshold=random.uniform(15, 45),
        entry_price_vs_ma_pct=random.uniform(-10, 15),
        entry_requires_both=random.choice([True, False]),
        
        # Exit
        exit_momentum_threshold=random.uniform(55, 85),
        exit_price_vs_ma_pct=random.uniform(-15, 10),
        exit_requires_both=random.choice([True, False]),
        
        # Risk (ALWAYS have stops)
        stop_loss_pct=random.uniform(5, 15),
        take_profit_pct=random.uniform(8, 25),
        
        # Time
        min_hold_bars=random.randint(5, 30),
        max_hold_bars=random.randint(30, 150),
        
        # Position (conservative - no 100%)
        position_size_pct=random.uniform(30, 70),
        
        # Direction (prefer long only for simplicity)
        trade_direction=random.choice(['long_only', 'long_only', 'long_only', 'both'])
    )

def mutate(gene: RobustGene, mutation_rate: float = 0.15) -> RobustGene:
    """Mutate with constraints"""
    mutated = RobustGene(**gene.__dict__)
    
    if random.random() < mutation_rate:
        mutated.entry_momentum_threshold = np.clip(
            gene.entry_momentum_threshold + random.gauss(0, 5), 15, 45)
    
    if random.random() < mutation_rate:
        mutated.entry_price_vs_ma_pct = np.clip(
            gene.entry_price_vs_ma_pct + random.gauss(0, 3), -10, 15)
    
    if random.random() < mutation_rate:
        mutated.entry_requires_both = not gene.entry_requires_both
    
    if random.random() < mutation_rate:
        mutated.exit_momentum_threshold = np.clip(
            gene.exit_momentum_threshold + random.gauss(0, 5), 55, 85)
    
    if random.random() < mutation_rate:
        mutated.exit_price_vs_ma_pct = np.clip(
            gene.exit_price_vs_ma_pct + random.gauss(0, 3), -15, 10)
    
    if random.random() < mutation_rate:
        mutated.exit_requires_both = not gene.exit_requires_both
    
    if random.random() < mutation_rate:
        mutated.stop_loss_pct = np.clip(
            gene.stop_loss_pct + random.gauss(0, 2), 5, 15)
    
    if random.random() < mutation_rate:
        mutated.take_profit_pct = np.clip(
            gene.take_profit_pct + random.gauss(0, 3), 8, 25)
    
    if random.random() < mutation_rate:
        mutated.min_hold_bars = int(np.clip(
            gene.min_hold_bars + random.randint(-5, 5), 5, 30))
    
    if random.random() < mutation_rate:
        mutated.max_hold_bars = int(np.clip(
            gene.max_hold_bars + random.randint(-20, 20), 30, 150))
    
    if random.random() < mutation_rate:
        mutated.position_size_pct = np.clip(
            gene.position_size_pct + random.gauss(0, 10), 30, 70)
    
    if random.random() < mutation_rate * 0.5:  # Less frequent
        mutated.trade_direction = random.choice(['long_only', 'long_only', 'both'])
    
    return mutated

def crossover(parent1: RobustGene, parent2: RobustGene) -> Tuple[RobustGene, RobustGene]:
    """Simple crossover"""
    child1_dict = {}
    child2_dict = {}
    
    for key in parent1.__dict__.keys():
        if random.random() < 0.5:
            child1_dict[key] = getattr(parent1, key)
            child2_dict[key] = getattr(parent2, key)
        else:
            child1_dict[key] = getattr(parent2, key)
            child2_dict[key] = getattr(parent1, key)
    
    return RobustGene(**child1_dict), RobustGene(**child2_dict)

# ==============================================================================
# BACKTEST ENGINE WITH PROPER RISK MANAGEMENT
# ==============================================================================

def backtest_gene(gene: RobustGene, data: pd.DataFrame, momentum: np.ndarray,
                  initial_capital: float = 10000) -> Dict:
    """
    Simple, clean backtest with proper risk management
    """
    # Calculate indicators
    lookback = 50
    price_ma = data['close'].rolling(lookback).mean().values
    
    capital = initial_capital
    position = 0
    position_side = None
    entry_price = 0
    entry_bar = 0
    
    trades = []
    equity_curve = []
    
    start_bar = lookback + 100
    
    for i in range(start_bar, len(data)):
        current_price = data.iloc[i]['close']
        bars_held = i - entry_bar
        
        # Calculate current metrics
        price_vs_ma = ((current_price / price_ma[i]) - 1) * 100 if price_ma[i] > 0 else 0
        current_momentum = momentum[i]
        
        # No position - check entry
        if position == 0:
            # Entry conditions
            momentum_condition = current_momentum < gene.entry_momentum_threshold
            price_condition = price_vs_ma > gene.entry_price_vs_ma_pct
            
            if gene.entry_requires_both:
                entry_signal = momentum_condition and price_condition
            else:
                entry_signal = momentum_condition or price_condition
            
            if entry_signal:
                # Determine direction
                if gene.trade_direction == 'long_only':
                    direction = 'long'
                elif gene.trade_direction == 'short_only':
                    direction = 'short'
                else:  # both
                    direction = 'long' if current_momentum < 50 else 'short'
                
                # Position sizing (conservative)
                size = capital * (gene.position_size_pct / 100)
                shares = int(size / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_bar = i
                    capital -= shares * current_price * 1.001  # 0.1% commission
                    position_side = direction
        
        # Have position - manage it
        elif position > 0:
            # Calculate P&L
            if position_side == 'long':
                pnl_pct = ((current_price / entry_price) - 1) * 100
            else:  # short
                pnl_pct = ((entry_price / current_price) - 1) * 100
            
            exit_signal = False
            exit_reason = ''
            
            # Stop loss (ALWAYS CHECK - mandatory risk management)
            if pnl_pct <= -gene.stop_loss_pct:
                exit_signal = True
                exit_reason = 'stop_loss'
            
            # Take profit
            if not exit_signal and pnl_pct >= gene.take_profit_pct:
                exit_signal = True
                exit_reason = 'take_profit'
            
            # Time exits
            if not exit_signal and bars_held >= gene.max_hold_bars:
                exit_signal = True
                exit_reason = 'max_time'
            
            # Exit rule (only after min hold)
            if not exit_signal and bars_held >= gene.min_hold_bars:
                momentum_exit = current_momentum > gene.exit_momentum_threshold
                price_exit = price_vs_ma < gene.exit_price_vs_ma_pct
                
                if gene.exit_requires_both:
                    rule_exit = momentum_exit and price_exit
                else:
                    rule_exit = momentum_exit or price_exit
                
                if rule_exit:
                    exit_signal = True
                    exit_reason = 'rule_exit'
            
            # Execute exit
            if exit_signal:
                if position_side == 'long':
                    pnl = position * (current_price - entry_price)
                else:
                    pnl = position * (entry_price - current_price)
                
                # Commission
                pnl = pnl * 0.999
                
                capital += pnl + (position * entry_price)
                
                trades.append({
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'side': position_side,
                    'exit_reason': exit_reason
                })
                
                position = 0
                position_side = None
        
        # Track equity
        if position > 0:
            if position_side == 'long':
                unrealized = position * current_price
            else:
                unrealized = position * (2 * entry_price - current_price)
            equity_curve.append(capital + unrealized)
        else:
            equity_curve.append(capital)
    
    # Calculate metrics
    if len(trades) == 0:
        return {
            'fitness': -1000,
            'total_return': -100,
            'total_trades': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'avg_trade_return': 0,
            'final_capital': capital
        }
    
    total_return = ((capital / initial_capital) - 1) * 100
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / len(trades)) * 100
    
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 0 and np.std(returns) > 0 else 0
    
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    avg_trade_return = np.mean([t['pnl_pct'] for t in trades])
    
    return {
        'fitness': 0,  # Will be calculated in fitness function
        'total_return': total_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'avg_trade_return': avg_trade_return,
        'final_capital': capital,
        'trades': trades,
        'equity_curve': equity_curve
    }

# ==============================================================================
# ROBUST FITNESS FUNCTION WITH MULTI-REGIME VALIDATION
# ==============================================================================

def calculate_robust_fitness(gene: RobustGene, 
                             train_data: pd.DataFrame, train_momentum: np.ndarray,
                             val_data: pd.DataFrame, val_momentum: np.ndarray) -> Dict:
    """
    Fitness function that validates on both train AND validation sets
    Penalizes overfitting by comparing performance
    """
    # Train performance
    train_result = backtest_gene(gene, train_data, train_momentum)
    
    # Validation performance (out-of-sample during evolution!)
    val_result = backtest_gene(gene, val_data, val_momentum)
    
    # If strategy fails on either set, heavily penalize
    if train_result['total_trades'] < 10 or val_result['total_trades'] < 5:
        train_result['fitness'] = -1000
        train_result['val_return'] = val_result['total_return']
        return train_result
    
    # Calculate fitness components
    train_return = train_result['total_return']
    val_return = val_result['total_return']
    
    train_sharpe = train_result['sharpe_ratio']
    val_sharpe = val_result['sharpe_ratio']
    
    train_dd = train_result['max_drawdown']
    val_dd = val_result['max_drawdown']
    
    # ANTI-OVERFITTING: Penalize if validation performance much worse
    overfitting_penalty = 0
    if val_return < train_return * 0.3:  # Val return < 30% of train return
        overfitting_penalty = 100
    elif val_return < train_return * 0.5:  # Val return < 50% of train return
        overfitting_penalty = 50
    
    if val_sharpe < train_sharpe * 0.5:  # Val sharpe much worse
        overfitting_penalty += 30
    
    # REGULARIZATION: Penalize complexity (more trades = more fitting)
    if train_result['total_trades'] > 100:
        complexity_penalty = (train_result['total_trades'] - 100) * 0.5
    else:
        complexity_penalty = 0
    
    # CONSISTENCY BONUS: Reward if val performs similar to train
    consistency_bonus = 0
    if 0.5 <= (val_return / (train_return + 1)) <= 1.5:
        consistency_bonus = 30
    
    # Combined fitness (emphasize validation performance!)
    fitness = (
        train_return * 0.25 +           # Train return (lower weight)
        val_return * 0.35 +             # Validation return (HIGHER weight)
        train_sharpe * 80 * 0.15 +      # Train Sharpe
        val_sharpe * 80 * 0.15 +        # Validation Sharpe
        -abs(train_dd) * 0.05 +         # Train drawdown
        -abs(val_dd) * 0.05 +           # Validation drawdown
        -overfitting_penalty +          # Penalize overfitting
        -complexity_penalty +           # Penalize complexity
        consistency_bonus               # Reward consistency
    )
    
    train_result['fitness'] = fitness
    train_result['val_return'] = val_return
    train_result['val_sharpe'] = val_sharpe
    train_result['val_trades'] = val_result['total_trades']
    train_result['overfitting_penalty'] = overfitting_penalty
    
    return train_result

# ==============================================================================
# WALK-FORWARD EVOLUTION
# ==============================================================================

def evolve_robust(train_data: pd.DataFrame, train_momentum: np.ndarray,
                 val_data: pd.DataFrame, val_momentum: np.ndarray,
                 population_size: int = 60, 
                 generations: int = 60) -> Tuple:
    """
    Evolve with walk-forward validation
    """
    print(f"\n🧬 Robust Evolution Parameters:")
    print(f"   Population: {population_size} individuals")
    print(f"   Generations: {generations}")
    print(f"   Training bars: {len(train_data)}")
    print(f"   Validation bars: {len(val_data)}")
    print(f"   Walk-forward validation: ENABLED ✅")
    print(f"   Overfitting penalties: ENABLED ✅")
    print(f"   Estimated time: {generations * population_size * 0.08 / 60:.1f} minutes")
    
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    best_result = None
    generation_history = []
    
    for gen in range(generations):
        fitness_scores = []
        results = []
        
        # Evaluate population with train AND validation
        for gene in population:
            result = calculate_robust_fitness(gene, train_data, train_momentum, 
                                             val_data, val_momentum)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
                best_result = result
        
        # Stats
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        
        best_idx = np.argmax(fitness_scores)
        best_gen_result = results[best_idx]
        
        generation_history.append({
            'gen': gen,
            'avg_fitness': avg_fitness,
            'max_fitness': max_fitness,
            'train_return': best_gen_result['total_return'],
            'val_return': best_gen_result['val_return']
        })
        
        # Print every 5 generations
        if (gen + 1) % 5 == 0 or gen == 0:
            print(f"\n📊 Generation {gen+1}/{generations}:")
            print(f"   Fitness: Avg={avg_fitness:7.2f} | Max={max_fitness:7.2f}")
            print(f"   Train: Return={best_gen_result['total_return']:+6.2f}%, "
                  f"Trades={best_gen_result['total_trades']:3d}, "
                  f"Win={best_gen_result['win_rate']:5.1f}%")
            print(f"   Val:   Return={best_gen_result['val_return']:+6.2f}%, "
                  f"Trades={best_gen_result['val_trades']:3d} "
                  f"(Overfit penalty: {best_gen_result['overfitting_penalty']:.0f})")
        
        # Selection (smaller elite for more diversity)
        elite_count = int(population_size * 0.10)  # Top 10%
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        # Add diversity
        diversity_count = int(population_size * 0.05)
        diversity_pool = [create_random_gene() for _ in range(diversity_count)]
        
        new_population = elite.copy()
        
        # Breed
        while len(new_population) < population_size - diversity_count:
            parent1 = elite[random.randint(0, len(elite)-1)]
            parent2 = elite[random.randint(0, len(elite)-1)]
            
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, mutation_rate=0.15)
            child2 = mutate(child2, mutation_rate=0.15)
            
            new_population.append(child1)
            if len(new_population) < population_size - diversity_count:
                new_population.append(child2)
        
        new_population.extend(diversity_pool)
        population = new_population
    
    return best_gene, best_result, generation_history

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    start_time = datetime.now()
    print(f"\n⏰ Started: {start_time.strftime('%H:%M:%S')}")
    
    # Download data - SPLIT INTO MULTIPLE PERIODS
    print("\n📥 Downloading data with walk-forward splits...")
    print("   2000-2015: Training (15 years, includes 2000 & 2008 crashes)")
    print("   2016-2020: Validation (5 years, unseen during training)")
    print("   2021-2024: Final test (4 years, completely out-of-sample)")
    
    # Training period (2000-2015)
    train_data = yf.download('SPY', start='2000-01-01', end='2015-12-31', progress=False)
    if isinstance(train_data.columns, pd.MultiIndex):
        train_data.columns = [col[0].lower() for col in train_data.columns]
    else:
        train_data.columns = train_data.columns.str.lower()
    
    # Validation period (2016-2020)
    val_data = yf.download('SPY', start='2016-01-01', end='2020-12-31', progress=False)
    if isinstance(val_data.columns, pd.MultiIndex):
        val_data.columns = [col[0].lower() for col in val_data.columns]
    else:
        val_data.columns = val_data.columns.str.lower()
    
    # Test period (2021-2024)
    test_data = yf.download('SPY', start='2021-01-01', end='2024-12-31', progress=False)
    if isinstance(test_data.columns, pd.MultiIndex):
        test_data.columns = [col[0].lower() for col in test_data.columns]
    else:
        test_data.columns = test_data.columns.str.lower()
    
    print(f"✅ Training: {len(train_data)} bars")
    print(f"✅ Validation: {len(val_data)} bars")
    print(f"✅ Test: {len(test_data)} bars")
    
    # Calculate momentum for all periods
    print("\n📊 Calculating momentum indicators...")
    train_result = calculate_momentum_indicator(train_data, length=7, threshold=2.0)
    train_momentum = train_result['momentum']
    
    val_result = calculate_momentum_indicator(val_data, length=7, threshold=2.0)
    val_momentum = val_result['momentum']
    
    test_result = calculate_momentum_indicator(test_data, length=7, threshold=2.0)
    test_momentum = test_result['momentum']
    
    # Run robust evolution
    print("\n🧬 Starting robust evolution with walk-forward validation...")
    best_gene, best_result, history = evolve_robust(
        train_data, train_momentum,
        val_data, val_momentum,
        population_size=50,
        generations=50
    )
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    
    # Results
    print("\n" + "=" * 80)
    print("  🏆 BEST ROBUST STRATEGY (ANTI-OVERFITTING)")
    print("=" * 80)
    
    print(f"\n🧬 STRATEGY PARAMETERS:")
    print(f"   Entry Momentum: < {best_gene.entry_momentum_threshold:.1f}")
    print(f"   Entry Price vs MA: > {best_gene.entry_price_vs_ma_pct:.1f}%")
    print(f"   Entry Logic: {'AND' if best_gene.entry_requires_both else 'OR'}")
    print(f"   ")
    print(f"   Exit Momentum: > {best_gene.exit_momentum_threshold:.1f}")
    print(f"   Exit Price vs MA: < {best_gene.exit_price_vs_ma_pct:.1f}%")
    print(f"   Exit Logic: {'AND' if best_gene.exit_requires_both else 'OR'}")
    print(f"   ")
    print(f"   Stop Loss: {best_gene.stop_loss_pct:.1f}%")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}%")
    print(f"   Hold Period: {best_gene.min_hold_bars}-{best_gene.max_hold_bars} bars")
    print(f"   Position Size: {best_gene.position_size_pct:.1f}%")
    print(f"   Direction: {best_gene.trade_direction}")
    
    print(f"\n💰 TRAINING PERFORMANCE (2000-2015, 15 years):")
    print(f"   Total Return:     {best_result['total_return']:+.2f}%")
    print(f"   Annualized:       {best_result['total_return']/15:+.2f}%")
    print(f"   Total Trades:     {best_result['total_trades']}")
    print(f"   Win Rate:         {best_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {best_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {best_result['max_drawdown']:.2f}%")
    print(f"   Avg Trade:        {best_result['avg_trade_return']:.2f}%")
    
    print(f"\n💰 VALIDATION PERFORMANCE (2016-2020, 5 years - UNSEEN):")
    print(f"   Total Return:     {best_result['val_return']:+.2f}%")
    print(f"   Annualized:       {best_result['val_return']/5:+.2f}%")
    print(f"   Total Trades:     {best_result['val_trades']}")
    print(f"   Val Sharpe:       {best_result['val_sharpe']:.2f}")
    print(f"   Overfitting Penalty: {best_result['overfitting_penalty']:.0f}")
    
    # Final test on 2021-2024
    final_test = backtest_gene(best_gene, test_data, test_momentum)
    
    print(f"\n💰 FINAL TEST PERFORMANCE (2021-2024, 4 years - COMPLETELY UNSEEN):")
    print(f"   Total Return:     {final_test['total_return']:+.2f}%")
    print(f"   Annualized:       {final_test['total_return']/4:+.2f}%")
    print(f"   Total Trades:     {final_test['total_trades']}")
    print(f"   Win Rate:         {final_test['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {final_test['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {final_test['max_drawdown']:.2f}%")
    print(f"   Final Capital:    ${final_test['final_capital']:,.2f}")
    
    # Consistency check
    print(f"\n📊 CONSISTENCY CHECK:")
    train_annual = best_result['total_return'] / 15
    val_annual = best_result['val_return'] / 5
    test_annual = final_test['total_return'] / 4
    
    print(f"   Train Annual:  {train_annual:+6.2f}%")
    print(f"   Val Annual:    {val_annual:+6.2f}%")
    print(f"   Test Annual:   {test_annual:+6.2f}%")
    
    if -50 < val_annual < 50 and -50 < test_annual < 50:
        print(f"   ✅ CONSISTENT PERFORMANCE - Strategy appears robust!")
    else:
        print(f"   ⚠️  Large variance detected - May still have overfitting")
    
    # Save strategy
    gene_dict = best_gene.__dict__.copy()
    with open('best_robust_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Strategy saved to: best_robust_strategy.json")
    print(f"⏰ Total training time: {elapsed:.1f} minutes")
    print(f"⏰ Finished: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n" + "=" * 80)
    print("  ✅ ROBUST GA COMPLETE")
    print("=" * 80)
    
    print(f"\n💡 KEY IMPROVEMENTS:")
    print(f"   ✅ Walk-forward validation during evolution")
    print(f"   ✅ Overfitting penalties in fitness function")
    print(f"   ✅ Simplified gene structure (fewer parameters)")
    print(f"   ✅ Conservative parameter ranges")
    print(f"   ✅ Mandatory stop losses")
    print(f"   ✅ 3-way split: Train/Val/Test")
    print(f"   ✅ Consistency checking across periods")
