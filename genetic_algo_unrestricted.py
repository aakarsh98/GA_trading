"""
UNRESTRICTED Genetic Algorithm - Let GA Discover EVERYTHING
No preset entry/exit rules - complete freedom to evolve any strategy
Uses: Momentum + Price + Their derivatives/combinations
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
print("  🧬 UNRESTRICTED GENETIC ALGORITHM")
print("  🎯 GA Will Discover Its Own Entry/Exit Logic")
print("  📊 100 Generations | Larger Gene Space")
print("=" * 80)

# ==============================================================================
# UNRESTRICTED GENE STRUCTURE
# ==============================================================================

@dataclass
class UnrestrictedGene:
    """
    Completely flexible gene - GA decides what indicators to use and how
    """
    # === ENTRY LOGIC ===
    # Multiple entry conditions that can be combined
    entry_rule_1_type: str          # 'momentum_level', 'momentum_change', 'price_vs_ma', 'momentum_vs_ma'
    entry_rule_1_value: float       # Threshold value
    entry_rule_1_operator: str      # '<', '>', '<=', '>='
    
    entry_rule_2_type: str
    entry_rule_2_value: float
    entry_rule_2_operator: str
    
    entry_logic_combinator: str     # 'AND', 'OR', 'XOR', 'ONLY_1', 'ONLY_2'
    
    # === EXIT LOGIC ===
    exit_rule_1_type: str
    exit_rule_1_value: float
    exit_rule_1_operator: str
    
    exit_rule_2_type: str
    exit_rule_2_value: float
    exit_rule_2_operator: str
    
    exit_logic_combinator: str
    
    # === POSITION MANAGEMENT ===
    position_size_type: str         # 'fixed', 'volatility_adjusted', 'momentum_scaled'
    position_size_value: float      # Base size (10-100%)
    
    # === RISK MANAGEMENT ===
    stop_type: str                  # 'fixed', 'trailing', 'volatility', 'momentum_based', 'none'
    stop_value: float               # Stop distance (1-20%)
    
    take_profit_enabled: bool
    take_profit_pct: float          # Take profit level (2-50%)
    
    # === TIME MANAGEMENT ===
    min_hold_bars: int              # Minimum hold period (1-50)
    max_hold_bars: int              # Maximum hold period (10-500)
    time_exit_enabled: bool
    
    # === DIRECTION ===
    allow_long: bool
    allow_short: bool
    
    # === ADVANCED FEATURES ===
    use_momentum_acceleration: bool  # Use 2nd derivative
    momentum_lookback: int          # Bars to look back (5-50)
    
    use_price_volatility: bool
    volatility_period: int          # ATR period (5-50)
    
    pyramid_enabled: bool           # Add to winning positions
    pyramid_threshold: float        # When to add (1-10%)
    
    def __repr__(self):
        return f"UnrestrictedGene(entry:{self.entry_rule_1_type}_{self.entry_rule_1_operator}{self.entry_rule_1_value:.1f} " \
               f"{self.entry_logic_combinator} {self.entry_rule_2_type}, " \
               f"stop:{self.stop_type}={self.stop_value:.1f}%)"

# ==============================================================================
# RULE EVALUATION ENGINE
# ==============================================================================

def evaluate_rule(rule_type: str, rule_value: float, rule_operator: str,
                 momentum: float, price: float, 
                 momentum_change: float, momentum_accel: float,
                 price_ma: float, momentum_ma: float,
                 volatility: float) -> bool:
    """
    Evaluate a trading rule based on type, value, and operator
    """
    # Get the indicator value based on rule type
    if rule_type == 'momentum_level':
        indicator = momentum
    elif rule_type == 'momentum_change':
        indicator = momentum_change
    elif rule_type == 'momentum_accel':
        indicator = momentum_accel
    elif rule_type == 'price_vs_ma':
        indicator = (price / price_ma - 1) * 100 if price_ma > 0 else 0
    elif rule_type == 'momentum_vs_ma':
        indicator = momentum - momentum_ma
    elif rule_type == 'price_momentum_ratio':
        indicator = (price / momentum) if momentum > 0 else 0
    elif rule_type == 'volatility_level':
        indicator = volatility
    elif rule_type == 'momentum_volatility_ratio':
        indicator = momentum / volatility if volatility > 0 else 0
    else:
        return False
    
    # Apply operator
    if rule_operator == '<':
        return indicator < rule_value
    elif rule_operator == '>':
        return indicator > rule_value
    elif rule_operator == '<=':
        return indicator <= rule_value
    elif rule_operator == '>=':
        return indicator >= rule_value
    else:
        return False

def combine_rules(result1: bool, result2: bool, combinator: str) -> bool:
    """Combine two rule results using logic operator"""
    if combinator == 'AND':
        return result1 and result2
    elif combinator == 'OR':
        return result1 or result2
    elif combinator == 'XOR':
        return result1 != result2
    elif combinator == 'ONLY_1':
        return result1
    elif combinator == 'ONLY_2':
        return result2
    else:
        return False

# ==============================================================================
# GENETIC OPERATIONS
# ==============================================================================

RULE_TYPES = ['momentum_level', 'momentum_change', 'momentum_accel', 
              'price_vs_ma', 'momentum_vs_ma', 'price_momentum_ratio',
              'volatility_level', 'momentum_volatility_ratio']

OPERATORS = ['<', '>', '<=', '>=']
COMBINATORS = ['AND', 'OR', 'XOR', 'ONLY_1', 'ONLY_2']
STOP_TYPES = ['fixed', 'trailing', 'volatility', 'momentum_based', 'none']
POSITION_TYPES = ['fixed', 'volatility_adjusted', 'momentum_scaled']

def create_random_gene() -> UnrestrictedGene:
    """Create completely random gene"""
    return UnrestrictedGene(
        # Entry rules
        entry_rule_1_type=random.choice(RULE_TYPES),
        entry_rule_1_value=random.uniform(0, 100),
        entry_rule_1_operator=random.choice(OPERATORS),
        
        entry_rule_2_type=random.choice(RULE_TYPES),
        entry_rule_2_value=random.uniform(0, 100),
        entry_rule_2_operator=random.choice(OPERATORS),
        
        entry_logic_combinator=random.choice(COMBINATORS),
        
        # Exit rules
        exit_rule_1_type=random.choice(RULE_TYPES),
        exit_rule_1_value=random.uniform(0, 100),
        exit_rule_1_operator=random.choice(OPERATORS),
        
        exit_rule_2_type=random.choice(RULE_TYPES),
        exit_rule_2_value=random.uniform(0, 100),
        exit_rule_2_operator=random.choice(OPERATORS),
        
        exit_logic_combinator=random.choice(COMBINATORS),
        
        # Position management
        position_size_type=random.choice(POSITION_TYPES),
        position_size_value=random.uniform(20, 100),
        
        # Risk management
        stop_type=random.choice(STOP_TYPES),
        stop_value=random.uniform(1, 20),
        
        take_profit_enabled=random.choice([True, False]),
        take_profit_pct=random.uniform(2, 30),
        
        # Time management
        min_hold_bars=random.randint(1, 30),
        max_hold_bars=random.randint(20, 300),
        time_exit_enabled=random.choice([True, False]),
        
        # Direction
        allow_long=random.choice([True, False]),
        allow_short=random.choice([True, False]),
        
        # Advanced
        use_momentum_acceleration=random.choice([True, False]),
        momentum_lookback=random.randint(5, 50),
        
        use_price_volatility=random.choice([True, False]),
        volatility_period=random.randint(5, 50),
        
        pyramid_enabled=random.choice([True, False]),
        pyramid_threshold=random.uniform(1, 10)
    )

def mutate(gene: UnrestrictedGene, mutation_rate: float = 0.1) -> UnrestrictedGene:
    """Mutate gene with given rate"""
    mutated = UnrestrictedGene(**gene.__dict__)
    
    # Mutate each field with probability
    if random.random() < mutation_rate:
        mutated.entry_rule_1_type = random.choice(RULE_TYPES)
    if random.random() < mutation_rate:
        mutated.entry_rule_1_value = np.clip(gene.entry_rule_1_value + random.gauss(0, 10), 0, 100)
    if random.random() < mutation_rate:
        mutated.entry_rule_1_operator = random.choice(OPERATORS)
    
    if random.random() < mutation_rate:
        mutated.entry_rule_2_type = random.choice(RULE_TYPES)
    if random.random() < mutation_rate:
        mutated.entry_rule_2_value = np.clip(gene.entry_rule_2_value + random.gauss(0, 10), 0, 100)
    if random.random() < mutation_rate:
        mutated.entry_rule_2_operator = random.choice(OPERATORS)
    
    if random.random() < mutation_rate:
        mutated.entry_logic_combinator = random.choice(COMBINATORS)
    
    # Exit rules
    if random.random() < mutation_rate:
        mutated.exit_rule_1_type = random.choice(RULE_TYPES)
    if random.random() < mutation_rate:
        mutated.exit_rule_1_value = np.clip(gene.exit_rule_1_value + random.gauss(0, 10), 0, 100)
    if random.random() < mutation_rate:
        mutated.exit_rule_1_operator = random.choice(OPERATORS)
    
    if random.random() < mutation_rate:
        mutated.exit_rule_2_type = random.choice(RULE_TYPES)
    if random.random() < mutation_rate:
        mutated.exit_rule_2_value = np.clip(gene.exit_rule_2_value + random.gauss(0, 10), 0, 100)
    if random.random() < mutation_rate:
        mutated.exit_rule_2_operator = random.choice(OPERATORS)
    
    if random.random() < mutation_rate:
        mutated.exit_logic_combinator = random.choice(COMBINATORS)
    
    # Position/Risk
    if random.random() < mutation_rate:
        mutated.position_size_type = random.choice(POSITION_TYPES)
    if random.random() < mutation_rate:
        mutated.position_size_value = np.clip(gene.position_size_value + random.gauss(0, 10), 10, 100)
    
    if random.random() < mutation_rate:
        mutated.stop_type = random.choice(STOP_TYPES)
    if random.random() < mutation_rate:
        mutated.stop_value = np.clip(gene.stop_value + random.gauss(0, 2), 1, 20)
    
    if random.random() < mutation_rate:
        mutated.take_profit_enabled = not gene.take_profit_enabled
    if random.random() < mutation_rate:
        mutated.take_profit_pct = np.clip(gene.take_profit_pct + random.gauss(0, 5), 2, 50)
    
    # Time
    if random.random() < mutation_rate:
        mutated.min_hold_bars = int(np.clip(gene.min_hold_bars + random.randint(-5, 5), 1, 50))
    if random.random() < mutation_rate:
        mutated.max_hold_bars = int(np.clip(gene.max_hold_bars + random.randint(-30, 30), 10, 500))
    if random.random() < mutation_rate:
        mutated.time_exit_enabled = not gene.time_exit_enabled
    
    # Direction
    if random.random() < mutation_rate:
        mutated.allow_long = not gene.allow_long
    if random.random() < mutation_rate:
        mutated.allow_short = not gene.allow_short
    
    # Advanced
    if random.random() < mutation_rate:
        mutated.use_momentum_acceleration = not gene.use_momentum_acceleration
    if random.random() < mutation_rate:
        mutated.momentum_lookback = int(np.clip(gene.momentum_lookback + random.randint(-5, 5), 5, 50))
    
    if random.random() < mutation_rate:
        mutated.use_price_volatility = not gene.use_price_volatility
    if random.random() < mutation_rate:
        mutated.volatility_period = int(np.clip(gene.volatility_period + random.randint(-5, 5), 5, 50))
    
    if random.random() < mutation_rate:
        mutated.pyramid_enabled = not gene.pyramid_enabled
    if random.random() < mutation_rate:
        mutated.pyramid_threshold = np.clip(gene.pyramid_threshold + random.gauss(0, 2), 1, 10)
    
    # Ensure at least one direction is allowed
    if not mutated.allow_long and not mutated.allow_short:
        mutated.allow_long = True
    
    return mutated

def crossover(parent1: UnrestrictedGene, parent2: UnrestrictedGene) -> Tuple[UnrestrictedGene, UnrestrictedGene]:
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
    
    return UnrestrictedGene(**child1_dict), UnrestrictedGene(**child2_dict)

# ==============================================================================
# BACKTEST ENGINE
# ==============================================================================

def backtest_gene(gene: UnrestrictedGene, data: pd.DataFrame, momentum: np.ndarray,
                  initial_capital: float = 10000) -> Dict:
    """Backtest unrestricted gene"""
    
    # Prepare indicators
    momentum_change = np.concatenate([[0], np.diff(momentum)])
    momentum_accel = np.concatenate([[0], np.diff(momentum_change)])
    
    price_ma = data['close'].rolling(gene.momentum_lookback).mean().values
    momentum_ma = pd.Series(momentum).rolling(gene.momentum_lookback).mean().values
    
    # Volatility (ATR)
    if gene.use_price_volatility:
        tr = np.maximum(
            data['high'].values - data['low'].values,
            np.maximum(
                np.abs(data['high'].values - np.roll(data['close'].values, 1)),
                np.abs(data['low'].values - np.roll(data['close'].values, 1))
            )
        )
        volatility = pd.Series(tr).rolling(gene.volatility_period).mean().values
    else:
        volatility = np.ones(len(data))
    
    capital = initial_capital
    position = 0
    position_side = None
    entry_price = 0
    entry_bar = 0
    stop_loss = 0
    take_profit = 0
    
    trades = []
    equity_curve = []
    
    start_bar = max(100, gene.momentum_lookback, gene.volatility_period)
    
    for i in range(start_bar, len(data)):
        current_price = data.iloc[i]['close']
        bars_held = i - entry_bar
        
        # Evaluate entry if no position
        if position == 0:
            # Evaluate entry rules
            entry_result_1 = evaluate_rule(
                gene.entry_rule_1_type, gene.entry_rule_1_value, gene.entry_rule_1_operator,
                momentum[i], current_price, momentum_change[i], momentum_accel[i],
                price_ma[i], momentum_ma[i], volatility[i]
            )
            
            entry_result_2 = evaluate_rule(
                gene.entry_rule_2_type, gene.entry_rule_2_value, gene.entry_rule_2_operator,
                momentum[i], current_price, momentum_change[i], momentum_accel[i],
                price_ma[i], momentum_ma[i], volatility[i]
            )
            
            entry_signal = combine_rules(entry_result_1, entry_result_2, gene.entry_logic_combinator)
            
            if entry_signal:
                # Determine direction (for now, prefer long if both allowed)
                if gene.allow_long and momentum[i] < 50:
                    direction = 'long'
                elif gene.allow_short and momentum[i] > 50:
                    direction = 'short'
                elif gene.allow_long:
                    direction = 'long'
                elif gene.allow_short:
                    direction = 'short'
                else:
                    continue
                
                # Calculate position size
                if gene.position_size_type == 'volatility_adjusted':
                    size_pct = gene.position_size_value * (1 / (volatility[i] + 0.01))
                    size_pct = np.clip(size_pct, 10, 100)
                elif gene.position_size_type == 'momentum_scaled':
                    size_pct = gene.position_size_value * (abs(momentum[i] - 50) / 50)
                    size_pct = np.clip(size_pct, 10, 100)
                else:
                    size_pct = gene.position_size_value
                
                size = capital * (size_pct / 100)
                shares = int(size / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_bar = i
                    capital -= shares * current_price * 1.001
                    position_side = direction
                    
                    # Set stops
                    if gene.stop_type == 'fixed':
                        stop_loss = entry_price * (1 - gene.stop_value/100) if direction == 'long' else entry_price * (1 + gene.stop_value/100)
                    elif gene.stop_type == 'volatility':
                        stop_dist = volatility[i] * gene.stop_value
                        stop_loss = entry_price - stop_dist if direction == 'long' else entry_price + stop_dist
                    elif gene.stop_type == 'trailing':
                        stop_loss = entry_price * (1 - gene.stop_value/100) if direction == 'long' else entry_price * (1 + gene.stop_value/100)
                    else:
                        stop_loss = 0
                    
                    # Set take profit
                    if gene.take_profit_enabled:
                        take_profit = entry_price * (1 + gene.take_profit_pct/100) if direction == 'long' else entry_price * (1 - gene.take_profit_pct/100)
        
        # Manage position
        elif position > 0:
            # Update trailing stop
            if gene.stop_type == 'trailing':
                if position_side == 'long':
                    new_stop = current_price * (1 - gene.stop_value/100)
                    if new_stop > stop_loss:
                        stop_loss = new_stop
                else:
                    new_stop = current_price * (1 + gene.stop_value/100)
                    if new_stop < stop_loss:
                        stop_loss = new_stop
            
            # Check exit conditions
            exit_signal = False
            exit_reason = ''
            
            # Stop loss
            if gene.stop_type != 'none' and stop_loss > 0:
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
            
            # Exit rule
            if not exit_signal and bars_held >= gene.min_hold_bars:
                exit_result_1 = evaluate_rule(
                    gene.exit_rule_1_type, gene.exit_rule_1_value, gene.exit_rule_1_operator,
                    momentum[i], current_price, momentum_change[i], momentum_accel[i],
                    price_ma[i], momentum_ma[i], volatility[i]
                )
                
                exit_result_2 = evaluate_rule(
                    gene.exit_rule_2_type, gene.exit_rule_2_value, gene.exit_rule_2_operator,
                    momentum[i], current_price, momentum_change[i], momentum_accel[i],
                    price_ma[i], momentum_ma[i], volatility[i]
                )
                
                exit_from_rules = combine_rules(exit_result_1, exit_result_2, gene.exit_logic_combinator)
                
                if exit_from_rules:
                    exit_signal = True
                    exit_reason = 'rule_signal'
            
            # Time exit
            if gene.time_exit_enabled and bars_held >= gene.max_hold_bars:
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
    
    # Enhanced fitness function
    fitness = (
        total_return * 0.35 +
        sharpe_ratio * 100 * 0.30 +
        win_rate * 0.20 +
        -abs(max_drawdown) * 0.10 +
        avg_trade_return * 5 * 0.05
    )
    
    # Trade count penalties/bonuses
    if len(trades) < 20:
        fitness *= (len(trades) / 20)
    elif len(trades) > 200:
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

def evolve_unrestricted(data: pd.DataFrame, momentum: np.ndarray,
                       population_size: int = 100, generations: int = 100) -> Tuple:
    """Evolve with complete freedom"""
    print(f"\n🧬 Evolution Parameters:")
    print(f"   Population: {population_size} individuals")
    print(f"   Generations: {generations}")
    print(f"   Gene Space: ~30 parameters, fully flexible")
    print(f"   Estimated time: {generations * population_size * 0.05 / 60:.1f} minutes")
    
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    fitness_history = []
    
    for gen in range(generations):
        fitness_scores = []
        results = []
        
        # Evaluate population
        for gene in population:
            result = backtest_gene(gene, data, momentum)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
        
        # Stats
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        fitness_history.append({'gen': gen, 'avg': avg_fitness, 'max': max_fitness})
        
        # Print every 5 generations
        if (gen + 1) % 5 == 0 or gen == 0:
            best_idx = np.argmax(fitness_scores)
            best_result = results[best_idx]
            print(f"\n📊 Generation {gen+1}/{generations}:")
            print(f"   Avg Fitness: {avg_fitness:8.2f} | Max: {max_fitness:8.2f}")
            print(f"   Best: Return={best_result['total_return']:+6.2f}%, Trades={best_result['total_trades']:3d}, "
                  f"Win={best_result['win_rate']:5.1f}%, Sharpe={best_result['sharpe_ratio']:.2f}")
        
        # Selection & reproduction
        elite_count = int(population_size * 0.15)
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        new_population = elite.copy()
        
        while len(new_population) < population_size:
            parent1 = elite[random.randint(0, len(elite)-1)]
            parent2 = elite[random.randint(0, len(elite)-1)]
            
            child1, child2 = crossover(parent1, parent2)
            child1 = mutate(child1, mutation_rate=0.1)
            child2 = mutate(child2, mutation_rate=0.1)
            
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
    print(f"\n⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Download data
    print("\n📥 Downloading training data (2013-2020)...")
    train_data = yf.download('SPY', start='2013-01-01', end='2020-12-31', progress=False)
    
    if isinstance(train_data.columns, pd.MultiIndex):
        train_data.columns = [col[0].lower() for col in train_data.columns]
    else:
        train_data.columns = train_data.columns.str.lower()
    
    print(f"✅ Training data: {len(train_data)} bars")
    
    # Calculate momentum
    print("📊 Calculating momentum...")
    result = calculate_momentum_indicator(train_data, length=7, threshold=2.0)
    momentum = result['momentum']
    
    # Run evolution
    best_gene, best_result, history = evolve_unrestricted(
        train_data,
        momentum,
        population_size=100,
        generations=100
    )
    
    # Results
    print("\n" + "=" * 80)
    print("  🏆 BEST UNRESTRICTED STRATEGY")
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
    
    print(f"\n💰 TRAINING PERFORMANCE (2013-2020):")
    print(f"   Fitness:          {best_result['fitness']:.2f}")
    print(f"   Total Return:     {best_result['total_return']:+.2f}%")
    print(f"   Annualized:       ~{best_result['total_return']/8:+.2f}%")
    print(f"   Total Trades:     {best_result['total_trades']}")
    print(f"   Win Rate:         {best_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {best_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {best_result['max_drawdown']:.2f}%")
    print(f"   Avg Trade:        {best_result['avg_trade_return']:.2f}%")
    print(f"   Final Capital:    ${best_result['final_capital']:,.2f}")
    
    # Out-of-sample test
    print("\n📥 Out-of-sample test (2021-2023)...")
    test_data = yf.download('SPY', start='2021-01-01', end='2023-12-31', progress=False)
    
    if isinstance(test_data.columns, pd.MultiIndex):
        test_data.columns = [col[0].lower() for col in test_data.columns]
    else:
        test_data.columns = test_data.columns.str.lower()
    
    test_result_obj = calculate_momentum_indicator(test_data, length=7, threshold=2.0)
    test_momentum = test_result_obj['momentum']
    
    test_result = backtest_gene(best_gene, test_data, test_momentum)
    
    print(f"\n💰 OUT-OF-SAMPLE PERFORMANCE (2021-2023):")
    print(f"   Total Return:     {test_result['total_return']:+.2f}%")
    print(f"   Total Trades:     {test_result['total_trades']}")
    print(f"   Win Rate:         {test_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {test_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {test_result['max_drawdown']:.2f}%")
    print(f"   Final Capital:    ${test_result['final_capital']:,.2f}")
    
    # Save
    gene_dict = best_gene.__dict__.copy()
    with open('best_unrestricted_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Strategy saved to: best_unrestricted_strategy.json")
    print(f"⏰ Finished at: {datetime.now().strftime('%H:%M:%S')}")
    
    print("\n" + "=" * 80)
