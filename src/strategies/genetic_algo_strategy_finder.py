"""
Genetic Algorithm to Automatically Discover Trading Strategies
Uses only: Momentum Tracker + Price
Evolves rules for entry, exit, position sizing, and risk management
"""
import sys
import numpy as np
import pandas as pd
import yfinance as yf
from typing import List, Dict, Tuple
import random
from dataclasses import dataclass
import json

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🧬 GENETIC ALGORITHM - AUTOMATIC STRATEGY DISCOVERY")
print("  📊 Using: Momentum Tracker + Price Data Only")
print("=" * 80)

# ==============================================================================
# GENE STRUCTURE - Define what makes a trading strategy
# ==============================================================================

@dataclass
class TradingGene:
    """
    A gene represents a complete trading strategy
    Each parameter is a gene that can mutate and crossover
    """
    # Entry conditions
    entry_momentum_low: float       # Buy when momentum below this (20-50)
    entry_momentum_high: float      # Sell when momentum above this (50-80)
    
    # Exit conditions  
    exit_momentum_low: float        # Exit short when momentum below (15-45)
    exit_momentum_high: float       # Exit long when momentum above (55-85)
    
    # Alternative exit: opposite signal
    use_opposite_signal: bool       # True = exit long on short signal
    
    # Stop loss
    stop_loss_pct: float           # Stop loss percentage (1-10%)
    use_trailing_stop: bool        # True = trailing stop, False = fixed
    
    # Position sizing
    position_size_pct: float       # % of capital per trade (10-100%)
    use_kelly_criterion: bool      # True = Kelly position sizing
    
    # Price filters
    use_price_trend: bool          # Only trade with trend
    price_ma_period: int           # Moving average period (10-200)
    
    # Time filters
    min_hold_days: int             # Minimum holding period (1-30)
    max_hold_days: int             # Maximum holding period (5-200)
    
    # Strategy mode
    long_only: bool                # True = long only, False = long+short
    
    def __repr__(self):
        return f"Gene(entry:{self.entry_momentum_low:.1f}-{self.entry_momentum_high:.1f}, " \
               f"exit:{self.exit_momentum_low:.1f}-{self.exit_momentum_high:.1f}, " \
               f"stop:{self.stop_loss_pct:.1f}%, size:{self.position_size_pct:.0f}%)"

# ==============================================================================
# GENETIC OPERATIONS
# ==============================================================================

def create_random_gene() -> TradingGene:
    """Create a random trading strategy gene"""
    return TradingGene(
        entry_momentum_low=random.uniform(20, 45),
        entry_momentum_high=random.uniform(55, 80),
        exit_momentum_low=random.uniform(15, 40),
        exit_momentum_high=random.uniform(60, 85),
        use_opposite_signal=random.choice([True, False]),
        stop_loss_pct=random.uniform(1, 10),
        use_trailing_stop=random.choice([True, False]),
        position_size_pct=random.uniform(20, 100),
        use_kelly_criterion=random.choice([True, False]),
        use_price_trend=random.choice([True, False]),
        price_ma_period=random.randint(10, 200),
        min_hold_days=random.randint(1, 10),
        max_hold_days=random.randint(10, 100),
        long_only=random.choice([True, False])
    )

def mutate(gene: TradingGene, mutation_rate: float = 0.15) -> TradingGene:
    """Mutate a gene - randomly change some parameters"""
    mutated = TradingGene(**gene.__dict__)
    
    if random.random() < mutation_rate:
        mutated.entry_momentum_low = np.clip(gene.entry_momentum_low + random.gauss(0, 5), 15, 50)
    if random.random() < mutation_rate:
        mutated.entry_momentum_high = np.clip(gene.entry_momentum_high + random.gauss(0, 5), 50, 85)
    if random.random() < mutation_rate:
        mutated.exit_momentum_low = np.clip(gene.exit_momentum_low + random.gauss(0, 5), 10, 45)
    if random.random() < mutation_rate:
        mutated.exit_momentum_high = np.clip(gene.exit_momentum_high + random.gauss(0, 5), 55, 90)
    if random.random() < mutation_rate:
        mutated.use_opposite_signal = not gene.use_opposite_signal
    if random.random() < mutation_rate:
        mutated.stop_loss_pct = np.clip(gene.stop_loss_pct + random.gauss(0, 2), 1, 15)
    if random.random() < mutation_rate:
        mutated.use_trailing_stop = not gene.use_trailing_stop
    if random.random() < mutation_rate:
        mutated.position_size_pct = np.clip(gene.position_size_pct + random.gauss(0, 10), 10, 100)
    if random.random() < mutation_rate:
        mutated.use_kelly_criterion = not gene.use_kelly_criterion
    if random.random() < mutation_rate:
        mutated.use_price_trend = not gene.use_price_trend
    if random.random() < mutation_rate:
        mutated.price_ma_period = int(np.clip(gene.price_ma_period + random.randint(-20, 20), 10, 200))
    if random.random() < mutation_rate:
        mutated.min_hold_days = int(np.clip(gene.min_hold_days + random.randint(-2, 2), 1, 20))
    if random.random() < mutation_rate:
        mutated.max_hold_days = int(np.clip(gene.max_hold_days + random.randint(-10, 10), 10, 200))
    if random.random() < mutation_rate:
        mutated.long_only = not gene.long_only
    
    return mutated

def crossover(parent1: TradingGene, parent2: TradingGene) -> Tuple[TradingGene, TradingGene]:
    """Create two children by combining parents' genes"""
    child1_dict = {}
    child2_dict = {}
    
    for key in parent1.__dict__.keys():
        if random.random() < 0.5:
            child1_dict[key] = getattr(parent1, key)
            child2_dict[key] = getattr(parent2, key)
        else:
            child1_dict[key] = getattr(parent2, key)
            child2_dict[key] = getattr(parent1, key)
    
    return TradingGene(**child1_dict), TradingGene(**child2_dict)

# ==============================================================================
# BACKTEST ENGINE - Evaluate fitness of a gene
# ==============================================================================

def backtest_gene(gene: TradingGene, data: pd.DataFrame, momentum: np.ndarray, 
                  initial_capital: float = 10000) -> Dict:
    """
    Backtest a trading gene and return performance metrics
    """
    capital = initial_capital
    position = 0
    position_side = None  # 'long' or 'short'
    entry_price = 0
    entry_date_idx = 0
    stop_loss = 0
    
    trades = []
    equity_curve = []
    
    # Calculate price MA if needed
    if gene.use_price_trend:
        price_ma = data['close'].rolling(gene.price_ma_period).mean().values
    else:
        price_ma = np.zeros(len(data))
    
    for i in range(max(100, gene.price_ma_period), len(data)):
        current_price = data.iloc[i]['close']
        current_momentum = momentum[i]
        
        # Check if we should enter a position
        if position == 0:
            # Long entry signal
            long_signal = current_momentum <= gene.entry_momentum_low
            
            # Apply price trend filter
            if gene.use_price_trend and long_signal:
                long_signal = current_price > price_ma[i]
            
            if long_signal:
                # Calculate position size
                size = capital * (gene.position_size_pct / 100)
                shares = int(size / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_date_idx = i
                    capital -= shares * current_price * 1.001  # 0.1% commission
                    position_side = 'long'
                    
                    # Set stop loss
                    if gene.use_trailing_stop:
                        stop_loss = entry_price * (1 - gene.stop_loss_pct / 100)
                    else:
                        stop_loss = entry_price * (1 - gene.stop_loss_pct / 100)
            
            # Short entry signal (if not long only)
            elif not gene.long_only:
                short_signal = current_momentum >= gene.entry_momentum_high
                
                if gene.use_price_trend and short_signal:
                    short_signal = current_price < price_ma[i]
                
                if short_signal:
                    size = capital * (gene.position_size_pct / 100)
                    shares = int(size / current_price)
                    
                    if shares > 0:
                        position = shares
                        entry_price = current_price
                        entry_date_idx = i
                        capital -= shares * current_price * 1.001
                        position_side = 'short'
                        stop_loss = entry_price * (1 + gene.stop_loss_pct / 100)
        
        # Check if we should exit position
        elif position > 0:
            days_held = i - entry_date_idx
            exit_signal = False
            exit_reason = ''
            
            # Update trailing stop
            if gene.use_trailing_stop and position_side == 'long':
                new_stop = current_price * (1 - gene.stop_loss_pct / 100)
                if new_stop > stop_loss:
                    stop_loss = new_stop
            elif gene.use_trailing_stop and position_side == 'short':
                new_stop = current_price * (1 + gene.stop_loss_pct / 100)
                if new_stop < stop_loss:
                    stop_loss = new_stop
            
            # Exit conditions for LONG
            if position_side == 'long':
                # Stop loss hit
                if current_price <= stop_loss:
                    exit_signal = True
                    exit_reason = 'stop_loss'
                # Momentum exit signal
                elif current_momentum >= gene.exit_momentum_high:
                    exit_signal = True
                    exit_reason = 'momentum_high'
                # Opposite signal exit
                elif gene.use_opposite_signal and current_momentum >= gene.entry_momentum_high:
                    exit_signal = True
                    exit_reason = 'opposite_signal'
                # Time-based exit
                elif days_held >= gene.max_hold_days:
                    exit_signal = True
                    exit_reason = 'max_hold'
            
            # Exit conditions for SHORT
            elif position_side == 'short':
                if current_price >= stop_loss:
                    exit_signal = True
                    exit_reason = 'stop_loss'
                elif current_momentum <= gene.exit_momentum_low:
                    exit_signal = True
                    exit_reason = 'momentum_low'
                elif gene.use_opposite_signal and current_momentum <= gene.entry_momentum_low:
                    exit_signal = True
                    exit_reason = 'opposite_signal'
                elif days_held >= gene.max_hold_days:
                    exit_signal = True
                    exit_reason = 'max_hold'
            
            # Minimum holding period
            if exit_signal and days_held < gene.min_hold_days:
                exit_signal = False
            
            # Execute exit
            if exit_signal:
                if position_side == 'long':
                    pnl = position * (current_price - entry_price) * 0.999  # 0.1% commission
                else:
                    pnl = position * (entry_price - current_price) * 0.999
                
                capital += pnl + (position * entry_price)
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': (pnl / (position * entry_price)) * 100,
                    'days_held': days_held,
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
            'fitness': -1000,  # Very bad fitness
            'total_return': -100,
            'total_trades': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'avg_trade_return': 0
        }
    
    total_return = (capital / initial_capital - 1) * 100
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / len(trades)) * 100
    
    # Calculate Sharpe ratio
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if len(returns) > 0 and np.std(returns) > 0 else 0
    
    # Max drawdown
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
    
    avg_trade_return = np.mean([t['pnl_pct'] for t in trades])
    
    # Fitness function: weighted combination of metrics
    fitness = (
        total_return * 0.3 +           # 30% weight on total return
        sharpe_ratio * 100 * 0.25 +    # 25% weight on Sharpe
        win_rate * 0.2 +                # 20% weight on win rate
        -abs(max_drawdown) * 0.15 +     # 15% weight on drawdown (negative)
        avg_trade_return * 5 * 0.1      # 10% weight on avg trade
    )
    
    # Penalty for too few trades
    if len(trades) < 10:
        fitness *= (len(trades) / 10)
    
    # Penalty for too many trades (overtrading)
    if len(trades) > 500:
        fitness *= 0.8
    
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
# GENETIC ALGORITHM EVOLUTION
# ==============================================================================

def evolve_strategy(data: pd.DataFrame, momentum: np.ndarray, 
                   population_size: int = 50, generations: int = 20) -> Tuple[TradingGene, Dict]:
    """
    Evolve trading strategies using genetic algorithm
    """
    print(f"\n🧬 Starting evolution with {population_size} individuals for {generations} generations...")
    
    # Initialize population
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    fitness_history = []
    
    for gen in range(generations):
        # Evaluate fitness of all individuals
        fitness_scores = []
        results = []
        
        for i, gene in enumerate(population):
            result = backtest_gene(gene, data, momentum)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
        
        # Statistics for this generation
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        fitness_history.append({'gen': gen, 'avg': avg_fitness, 'max': max_fitness})
        
        print(f"\n📊 Generation {gen+1}/{generations}:")
        print(f"   Average Fitness: {avg_fitness:8.2f}")
        print(f"   Best Fitness:    {max_fitness:8.2f}")
        
        # Get best performer stats
        best_idx = np.argmax(fitness_scores)
        best_result = results[best_idx]
        print(f"   Best Strategy: Return={best_result['total_return']:+.2f}%, "
              f"Trades={best_result['total_trades']}, WinRate={best_result['win_rate']:.1f}%, "
              f"Sharpe={best_result['sharpe_ratio']:.2f}")
        
        # Selection: Keep top 20% performers
        elite_count = int(population_size * 0.2)
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        # Create new population
        new_population = elite.copy()
        
        # Crossover and mutation
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = elite[random.randint(0, len(elite)-1)]
            parent2 = elite[random.randint(0, len(elite)-1)]
            
            # Crossover
            child1, child2 = crossover(parent1, parent2)
            
            # Mutation
            child1 = mutate(child1)
            child2 = mutate(child2)
            
            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)
        
        population = new_population
    
    # Final evaluation of best gene
    final_result = backtest_gene(best_gene, data, momentum)
    
    return best_gene, final_result, fitness_history

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    # Download training data (8 years)
    print("\n📥 Downloading training data (2013-2020)...")
    train_data = yf.download('SPY', start='2013-01-01', end='2020-12-31', progress=False)
    
    if isinstance(train_data.columns, pd.MultiIndex):
        train_data.columns = [col[0].lower() for col in train_data.columns]
    else:
        train_data.columns = train_data.columns.str.lower()
    
    print(f"✅ Training data: {len(train_data)} bars")
    
    # Calculate momentum
    print("📊 Calculating momentum indicator...")
    result = calculate_momentum_indicator(train_data, length=7, threshold=2.0)
    momentum = result['momentum']
    
    # Run genetic algorithm
    best_gene, best_result, fitness_history = evolve_strategy(
        train_data, 
        momentum,
        population_size=50,
        generations=30
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("  🏆 BEST EVOLVED STRATEGY")
    print("=" * 80)
    
    print(f"\n🧬 Gene Parameters:")
    print(f"   Entry: Momentum ≤ {best_gene.entry_momentum_low:.1f} (long) | ≥ {best_gene.entry_momentum_high:.1f} (short)")
    print(f"   Exit:  Momentum ≥ {best_gene.exit_momentum_high:.1f} (long) | ≤ {best_gene.exit_momentum_low:.1f} (short)")
    print(f"   Use Opposite Signal: {best_gene.use_opposite_signal}")
    print(f"   Stop Loss: {best_gene.stop_loss_pct:.1f}% ({'Trailing' if best_gene.use_trailing_stop else 'Fixed'})")
    print(f"   Position Size: {best_gene.position_size_pct:.1f}% of capital")
    print(f"   Price Trend Filter: {best_gene.use_price_trend} (MA={best_gene.price_ma_period})")
    print(f"   Hold Period: {best_gene.min_hold_days}-{best_gene.max_hold_days} days")
    print(f"   Mode: {'Long Only' if best_gene.long_only else 'Long+Short'}")
    
    print(f"\n💰 Training Performance:")
    print(f"   Fitness Score:    {best_result['fitness']:.2f}")
    print(f"   Total Return:     {best_result['total_return']:+.2f}%")
    print(f"   Total Trades:     {best_result['total_trades']}")
    print(f"   Win Rate:         {best_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {best_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {best_result['max_drawdown']:.2f}%")
    print(f"   Avg Trade Return: {best_result['avg_trade_return']:.2f}%")
    print(f"   Final Capital:    ${best_result['final_capital']:,.2f}")
    
    # Test on out-of-sample data
    print("\n📥 Testing on out-of-sample data (2021-2023)...")
    test_data = yf.download('SPY', start='2021-01-01', end='2023-12-31', progress=False)
    
    if isinstance(test_data.columns, pd.MultiIndex):
        test_data.columns = [col[0].lower() for col in test_data.columns]
    else:
        test_data.columns = test_data.columns.str.lower()
    
    test_result_obj = calculate_momentum_indicator(test_data, length=7, threshold=2.0)
    test_momentum = test_result_obj['momentum']
    
    test_result = backtest_gene(best_gene, test_data, test_momentum)
    
    print(f"\n💰 Out-of-Sample Performance (2021-2023):")
    print(f"   Total Return:     {test_result['total_return']:+.2f}%")
    print(f"   Total Trades:     {test_result['total_trades']}")
    print(f"   Win Rate:         {test_result['win_rate']:.1f}%")
    print(f"   Sharpe Ratio:     {test_result['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:     {test_result['max_drawdown']:.2f}%")
    print(f"   Final Capital:    ${test_result['final_capital']:,.2f}")
    
    # Save best gene
    gene_dict = best_gene.__dict__.copy()
    with open('best_evolved_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Best strategy saved to: best_evolved_strategy.json")
    
    print("\n" + "=" * 80)
    print("  ✅ GENETIC ALGORITHM COMPLETE")
    print("=" * 80)
