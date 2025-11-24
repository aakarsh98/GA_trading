"""
MINIMAL Genetic Algorithm - NO MOVING AVERAGES
Uses ONLY: Raw Momentum + Raw Price
Can the GA still discover a winning strategy with minimal inputs?
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
print("  🧬 MINIMAL GENETIC ALGORITHM")
print("  🎯 NO Moving Averages - ONLY Momentum + Price")
print("  📊 Can GA Discover Strategy With Minimal Inputs?")
print("=" * 80)

# ==============================================================================
# MINIMAL GENE STRUCTURE - Only momentum and price
# ==============================================================================

@dataclass
class MinimalGene:
    """
    Absolute minimal gene - only momentum level and price change
    No MAs, no derivatives, no complex indicators
    """
    # === ENTRY - Multiple simple rules ===
    entry_momentum_threshold: float     # Momentum level (0-100)
    entry_momentum_operator: str        # '<', '>', '<=', '>='
    
    entry_price_change_bars: int        # Look back N bars for price change
    entry_price_change_pct: float       # Price change % threshold
    entry_price_change_operator: str    # '<', '>', '<=', '>='
    
    entry_combinator: str               # 'AND', 'OR', 'XOR', 'ONLY_MOMENTUM', 'ONLY_PRICE'
    
    # === EXIT - Simple rules ===
    exit_momentum_threshold: float
    exit_momentum_operator: str
    
    exit_price_change_bars: int
    exit_price_change_pct: float
    exit_price_change_operator: str
    
    exit_combinator: str
    
    # === POSITION MANAGEMENT ===
    position_size_pct: float            # Fixed % (20-100)
    
    # === RISK MANAGEMENT ===
    stop_loss_pct: float                # Fixed stop (1-20%)
    trailing_stop: bool                 # Trailing vs fixed
    
    take_profit_enabled: bool
    take_profit_pct: float              # 2-50%
    
    # === TIME ===
    min_hold_bars: int                  # 1-50
    max_hold_bars: int                  # 10-500
    
    # === DIRECTION ===
    long_only: bool
    
    def __repr__(self):
        return f"MinimalGene(entry:M{self.entry_momentum_operator}{self.entry_momentum_threshold:.0f} " \
               f"{self.entry_combinator} P{self.entry_price_change_operator}{self.entry_price_change_pct:.1f}%, " \
               f"size:{self.position_size_pct:.0f}%)"

# ==============================================================================
# RULE EVALUATION
# ==============================================================================

OPERATORS = ['<', '>', '<=', '>=']
COMBINATORS = ['AND', 'OR', 'XOR', 'ONLY_MOMENTUM', 'ONLY_PRICE']

def evaluate_momentum_rule(momentum: float, threshold: float, operator: str) -> bool:
    """Evaluate momentum threshold rule"""
    if operator == '<':
        return momentum < threshold
    elif operator == '>':
        return momentum > threshold
    elif operator == '<=':
        return momentum <= threshold
    elif operator == '>=':
        return momentum >= threshold
    return False

def evaluate_price_change_rule(current_price: float, past_price: float, 
                               threshold_pct: float, operator: str) -> bool:
    """Evaluate price change rule"""
    if past_price == 0:
        return False
    
    price_change_pct = ((current_price / past_price) - 1) * 100
    
    if operator == '<':
        return price_change_pct < threshold_pct
    elif operator == '>':
        return price_change_pct > threshold_pct
    elif operator == '<=':
        return price_change_pct <= threshold_pct
    elif operator == '>=':
        return price_change_pct >= threshold_pct
    return False

def combine_rules(momentum_result: bool, price_result: bool, combinator: str) -> bool:
    """Combine two rule results"""
    if combinator == 'AND':
        return momentum_result and price_result
    elif combinator == 'OR':
        return momentum_result or price_result
    elif combinator == 'XOR':
        return momentum_result != price_result
    elif combinator == 'ONLY_MOMENTUM':
        return momentum_result
    elif combinator == 'ONLY_PRICE':
        return price_result
    return False

# ==============================================================================
# GENETIC OPERATIONS
# ==============================================================================

def create_random_gene() -> MinimalGene:
    """Create random minimal gene"""
    return MinimalGene(
        # Entry
        entry_momentum_threshold=random.uniform(10, 90),
        entry_momentum_operator=random.choice(OPERATORS),
        entry_price_change_bars=random.randint(1, 50),
        entry_price_change_pct=random.uniform(-10, 10),
        entry_price_change_operator=random.choice(OPERATORS),
        entry_combinator=random.choice(COMBINATORS),
        
        # Exit
        exit_momentum_threshold=random.uniform(10, 90),
        exit_momentum_operator=random.choice(OPERATORS),
        exit_price_change_bars=random.randint(1, 50),
        exit_price_change_pct=random.uniform(-10, 10),
        exit_price_change_operator=random.choice(OPERATORS),
        exit_combinator=random.choice(COMBINATORS),
        
        # Position
        position_size_pct=random.uniform(30, 100),
        
        # Risk
        stop_loss_pct=random.uniform(2, 15),
        trailing_stop=random.choice([True, False]),
        take_profit_enabled=random.choice([True, False]),
        take_profit_pct=random.uniform(3, 40),
        
        # Time
        min_hold_bars=random.randint(1, 30),
        max_hold_bars=random.randint(20, 300),
        
        # Direction
        long_only=random.choice([True, False])
    )

def mutate(gene: MinimalGene, mutation_rate: float = 0.12) -> MinimalGene:
    """Mutate gene"""
    mutated = MinimalGene(**gene.__dict__)
    
    if random.random() < mutation_rate:
        mutated.entry_momentum_threshold = np.clip(gene.entry_momentum_threshold + random.gauss(0, 10), 5, 95)
    if random.random() < mutation_rate:
        mutated.entry_momentum_operator = random.choice(OPERATORS)
    if random.random() < mutation_rate:
        mutated.entry_price_change_bars = int(np.clip(gene.entry_price_change_bars + random.randint(-5, 5), 1, 50))
    if random.random() < mutation_rate:
        mutated.entry_price_change_pct = np.clip(gene.entry_price_change_pct + random.gauss(0, 2), -15, 15)
    if random.random() < mutation_rate:
        mutated.entry_price_change_operator = random.choice(OPERATORS)
    if random.random() < mutation_rate:
        mutated.entry_combinator = random.choice(COMBINATORS)
    
    # Exit mutations
    if random.random() < mutation_rate:
        mutated.exit_momentum_threshold = np.clip(gene.exit_momentum_threshold + random.gauss(0, 10), 5, 95)
    if random.random() < mutation_rate:
        mutated.exit_momentum_operator = random.choice(OPERATORS)
    if random.random() < mutation_rate:
        mutated.exit_price_change_bars = int(np.clip(gene.exit_price_change_bars + random.randint(-5, 5), 1, 50))
    if random.random() < mutation_rate:
        mutated.exit_price_change_pct = np.clip(gene.exit_price_change_pct + random.gauss(0, 2), -15, 15)
    if random.random() < mutation_rate:
        mutated.exit_price_change_operator = random.choice(OPERATORS)
    if random.random() < mutation_rate:
        mutated.exit_combinator = random.choice(COMBINATORS)
    
    # Position/Risk mutations
    if random.random() < mutation_rate:
        mutated.position_size_pct = np.clip(gene.position_size_pct + random.gauss(0, 10), 20, 100)
    if random.random() < mutation_rate:
        mutated.stop_loss_pct = np.clip(gene.stop_loss_pct + random.gauss(0, 2), 1, 20)
    if random.random() < mutation_rate:
        mutated.trailing_stop = not gene.trailing_stop
    if random.random() < mutation_rate:
        mutated.take_profit_enabled = not gene.take_profit_enabled
    if random.random() < mutation_rate:
        mutated.take_profit_pct = np.clip(gene.take_profit_pct + random.gauss(0, 5), 2, 50)
    
    # Time mutations
    if random.random() < mutation_rate:
        mutated.min_hold_bars = int(np.clip(gene.min_hold_bars + random.randint(-3, 3), 1, 40))
    if random.random() < mutation_rate:
        mutated.max_hold_bars = int(np.clip(gene.max_hold_bars + random.randint(-20, 20), 10, 400))
    
    # Direction mutation
    if random.random() < mutation_rate:
        mutated.long_only = not gene.long_only
    
    return mutated

def crossover(parent1: MinimalGene, parent2: MinimalGene) -> Tuple[MinimalGene, MinimalGene]:
    """Crossover two parents"""
    child1_dict = {}
    child2_dict = {}
    
    for key in parent1.__dict__.keys():
        if random.random() < 0.5:
            child1_dict[key] = getattr(parent1, key)
            child2_dict[key] = getattr(parent2, key)
        else:
            child1_dict[key] = getattr(parent2, key)
            child2_dict[key] = getattr(parent1, key)
    
    return MinimalGene(**child1_dict), MinimalGene(**child2_dict)

# ==============================================================================
# BACKTEST ENGINE
# ==============================================================================

def backtest_gene(gene: MinimalGene, data: pd.DataFrame, momentum: np.ndarray,
                  initial_capital: float = 10000) -> Dict:
    """Backtest minimal gene using only momentum + price"""
    
    capital = initial_capital
    position = 0
    position_side = None
    entry_price = 0
    entry_bar = 0
    stop_loss = 0
    take_profit = 0
    
    trades = []
    equity_curve = []
    
    prices = data['close'].values
    
    start_bar = max(100, gene.entry_price_change_bars, gene.exit_price_change_bars)
    
    for i in range(start_bar, len(data)):
        current_price = prices[i]
        current_momentum = momentum[i]
        bars_held = i - entry_bar
        
        # ENTRY LOGIC
        if position == 0:
            # Momentum rule
            momentum_signal = evaluate_momentum_rule(
                current_momentum,
                gene.entry_momentum_threshold,
                gene.entry_momentum_operator
            )
            
            # Price change rule
            past_price = prices[i - gene.entry_price_change_bars]
            price_signal = evaluate_price_change_rule(
                current_price,
                past_price,
                gene.entry_price_change_pct,
                gene.entry_price_change_operator
            )
            
            # Combine rules
            entry_signal = combine_rules(momentum_signal, price_signal, gene.entry_combinator)
            
            if entry_signal:
                # Determine direction
                if gene.long_only:
                    direction = 'long'
                else:
                    # Use momentum to decide direction
                    direction = 'long' if current_momentum < 50 else 'short'
                
                # Position size
                size = capital * (gene.position_size_pct / 100)
                shares = int(size / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_bar = i
                    capital -= shares * current_price * 1.001
                    position_side = direction
                    
                    # Set stops
                    if direction == 'long':
                        stop_loss = entry_price * (1 - gene.stop_loss_pct / 100)
                        if gene.take_profit_enabled:
                            take_profit = entry_price * (1 + gene.take_profit_pct / 100)
                    else:
                        stop_loss = entry_price * (1 + gene.stop_loss_pct / 100)
                        if gene.take_profit_enabled:
                            take_profit = entry_price * (1 - gene.take_profit_pct / 100)
        
        # POSITION MANAGEMENT
        elif position > 0:
            # Update trailing stop
            if gene.trailing_stop:
                if position_side == 'long':
                    new_stop = current_price * (1 - gene.stop_loss_pct / 100)
                    if new_stop > stop_loss:
                        stop_loss = new_stop
                else:
                    new_stop = current_price * (1 + gene.stop_loss_pct / 100)
                    if new_stop < stop_loss:
                        stop_loss = new_stop
            
            # Check exit conditions
            exit_signal = False
            exit_reason = ''
            
            # Stop loss
            if position_side == 'long' and current_price <= stop_loss:
                exit_signal = True
                exit_reason = 'stop_loss'
            elif position_side == 'short' and current_price >= stop_loss:
                exit_signal = True
                exit_reason = 'stop_loss'
            
            # Take profit
            if gene.take_profit_enabled and not exit_signal:
                if position_side == 'long' and current_price >= take_profit:
                    exit_signal = True
                    exit_reason = 'take_profit'
                elif position_side == 'short' and current_price <= take_profit:
                    exit_signal = True
                    exit_reason = 'take_profit'
            
            # Exit rules (if min hold met)
            if not exit_signal and bars_held >= gene.min_hold_bars:
                # Momentum rule
                momentum_exit = evaluate_momentum_rule(
                    current_momentum,
                    gene.exit_momentum_threshold,
                    gene.exit_momentum_operator
                )
                
                # Price change rule
                exit_past_price = prices[i - gene.exit_price_change_bars]
                price_exit = evaluate_price_change_rule(
                    current_price,
                    exit_past_price,
                    gene.exit_price_change_pct,
                    gene.exit_price_change_operator
                )
                
                # Combine
                if combine_rules(momentum_exit, price_exit, gene.exit_combinator):
                    exit_signal = True
                    exit_reason = 'rule_exit'
            
            # Max hold time
            if bars_held >= gene.max_hold_bars:
                exit_signal = True
                exit_reason = 'time_exit'
            
            # Execute exit
            if exit_signal:
                if position_side == 'long':
                    pnl = position * (current_price - entry_price) * 0.999
                else:
                    pnl = position * (entry_price - current_price) * 0.999
                
                capital += pnl + (position * entry_price)
                
                trades.append({
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position * entry_price)) * 100,
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
    
    # Calculate fitness
    if len(trades) == 0:
        return {
            'fitness': -1000,
            'total_return': -100,
            'total_trades': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0
        }
    
    total_return = (capital / initial_capital - 1) * 100
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / len(trades)) * 100
    
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 0 and np.std(returns) > 0 else 0
    
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    avg_trade_return = np.mean([t['pnl_pct'] for t in trades])
    
    # Fitness function
    fitness = (
        total_return * 0.35 +
        sharpe_ratio * 100 * 0.30 +
        win_rate * 0.20 +
        -abs(max_drawdown) * 0.10 +
        avg_trade_return * 5 * 0.05
    )
    
    # Trade count adjustments
    if len(trades) < 15:
        fitness *= (len(trades) / 15)
    elif len(trades) > 250:
        fitness *= 0.85
    
    return {
        'fitness': fitness,
        'total_return': total_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'avg_trade_return': avg_trade_return,
        'final_capital': capital
    }

# ==============================================================================
# EVOLUTION
# ==============================================================================

def evolve_minimal(data: pd.DataFrame, momentum: np.ndarray,
                  population_size: int = 100, generations: int = 100) -> Tuple:
    """Evolve minimal strategy"""
    print(f"\n🧬 Evolution Parameters:")
    print(f"   Population: {population_size}")
    print(f"   Generations: {generations}")
    print(f"   Inputs: ONLY Momentum + Price (NO MAs!)")
    
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    fitness_history = []
    
    for gen in range(generations):
        fitness_scores = []
        results = []
        
        for gene in population:
            result = backtest_gene(gene, data, momentum)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
        
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        fitness_history.append({'gen': gen, 'avg': avg_fitness, 'max': max_fitness})
        
        if (gen + 1) % 5 == 0 or gen == 0:
            best_idx = np.argmax(fitness_scores)
            best_result = results[best_idx]
            print(f"\n📊 Gen {gen+1}/{generations}: Avg={avg_fitness:7.2f} | Max={max_fitness:7.2f}")
            print(f"   Best: {best_result['total_return']:+6.2f}%, {best_result['total_trades']:3d} trades, "
                  f"{best_result['win_rate']:5.1f}% win, Sharpe={best_result['sharpe_ratio']:.2f}")
        
        # Evolution
        elite_count = int(population_size * 0.15)
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        new_population = elite.copy()
        
        while len(new_population) < population_size:
            parent1 = elite[random.randint(0, len(elite)-1)]
            parent2 = elite[random.randint(0, len(elite)-1)]
            
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1)
            child2 = mutate(child2)
            
            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)
        
        population = new_population
    
    final_result = backtest_gene(best_gene, data, momentum)
    
    return best_gene, final_result, fitness_history

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print(f"\n⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n📥 Downloading training data (2013-2020)...")
    train_data = yf.download('SPY', start='2013-01-01', end='2020-12-31', progress=False)
    
    if isinstance(train_data.columns, pd.MultiIndex):
        train_data.columns = [col[0].lower() for col in train_data.columns]
    else:
        train_data.columns = train_data.columns.str.lower()
    
    print(f"✅ {len(train_data)} bars")
    
    print("📊 Calculating momentum...")
    result = calculate_momentum_indicator(train_data, length=7, threshold=2.0)
    momentum = result['momentum']
    
    # Run evolution
    best_gene, best_result, history = evolve_minimal(
        train_data,
        momentum,
        population_size=100,
        generations=100
    )
    
    # Results
    print("\n" + "=" * 80)
    print("  🏆 BEST MINIMAL STRATEGY (NO MOVING AVERAGES)")
    print("=" * 80)
    
    print(f"\n🧬 ENTRY LOGIC:")
    print(f"   Momentum: {best_gene.entry_momentum_operator} {best_gene.entry_momentum_threshold:.1f}")
    print(f"   Price Change ({best_gene.entry_price_change_bars} bars): {best_gene.entry_price_change_operator} {best_gene.entry_price_change_pct:.2f}%")
    print(f"   Combinator: {best_gene.entry_combinator}")
    
    print(f"\n🚪 EXIT LOGIC:")
    print(f"   Momentum: {best_gene.exit_momentum_operator} {best_gene.exit_momentum_threshold:.1f}")
    print(f"   Price Change ({best_gene.exit_price_change_bars} bars): {best_gene.exit_price_change_operator} {best_gene.exit_price_change_pct:.2f}%")
    print(f"   Combinator: {best_gene.exit_combinator}")
    
    print(f"\n💼 POSITION & RISK:")
    print(f"   Size: {best_gene.position_size_pct:.1f}%")
    print(f"   Stop: {best_gene.stop_loss_pct:.1f}% ({'Trailing' if best_gene.trailing_stop else 'Fixed'})")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}% (enabled: {best_gene.take_profit_enabled})")
    print(f"   Hold: {best_gene.min_hold_bars}-{best_gene.max_hold_bars} bars")
    print(f"   Direction: {'Long Only' if best_gene.long_only else 'Long + Short'}")
    
    print(f"\n💰 TRAINING PERFORMANCE (2013-2020):")
    print(f"   Total Return:     {best_result['total_return']:+.2f}%")
    print(f"   Annualized:       ~{best_result['total_return']/8:+.2f}%")
    print(f"   Total Trades:     {best_result['total_trades']}")
    print(f"   Win Rate:         {best_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {best_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {best_result['max_drawdown']:.2f}%")
    print(f"   Final Capital:    ${best_result['final_capital']:,.2f}")
    
    # Out-of-sample
    print("\n📥 Out-of-sample test (2021-2023)...")
    test_data = yf.download('SPY', start='2021-01-01', end='2023-12-31', progress=False)
    
    if isinstance(test_data.columns, pd.MultiIndex):
        test_data.columns = [col[0].lower() for col in test_data.columns]
    else:
        test_data.columns = test_data.columns.str.lower()
    
    test_result_obj = calculate_momentum_indicator(test_data, length=7, threshold=2.0)
    test_momentum = test_result_obj['momentum']
    
    test_result = backtest_gene(best_gene, test_data, test_momentum)
    
    print(f"\n💰 OUT-OF-SAMPLE (2021-2023):")
    print(f"   Total Return:     {test_result['total_return']:+.2f}%")
    print(f"   Total Trades:     {test_result['total_trades']}")
    print(f"   Win Rate:         {test_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {test_result['sharpe_ratio']:.2f}")
    print(f"   Final Capital:    ${test_result['final_capital']:,.2f}")
    
    # Save
    gene_dict = best_gene.__dict__.copy()
    with open('best_minimal_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Saved to: best_minimal_strategy.json")
    print(f"⏰ Finished: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n" + "=" * 80)
    print("  📊 COMPARISON: Minimal vs Unrestricted")
    print("=" * 80)
    print(f"\n{'Metric':<20} {'Minimal (No MA)':<20} {'Unrestricted (With MA)':<20}")
    print("-" * 60)
    print(f"{'Training Return':<20} {best_result['total_return']:>18.2f}% {'276.83%':>20}")
    print(f"{'Test Return':<20} {test_result['total_return']:>18.2f}% {'+22.48%':>20}")
    print(f"{'Win Rate':<20} {best_result['win_rate']:>18.1f}% {'85.0%':>20}")
    print(f"{'Sharpe Ratio':<20} {best_result['sharpe_ratio']:>18.2f} {'1.22':>20}")
    
    print("\n" + "=" * 80)
