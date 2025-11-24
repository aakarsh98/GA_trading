"""
GA That Actually Tries to Beat Buy-and-Hold
- Fitness = Alpha (Strategy Return - Buy&Hold Return)
- Must consistently beat benchmark across periods
- Higher position sizing allowed
- Trend-following focus (catch bull runs)
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
print("  🧬 GA TO BEAT BUY-AND-HOLD")
print("  🎯 Fitness = Alpha (Outperformance vs Benchmark)")
print("=" * 80)

@dataclass
class TrendGene:
    """Gene designed to catch trends and beat buy-and-hold"""
    # Entry: Buy dips with momentum
    entry_momentum_threshold: float      # 20-45 (buy when momentum low)
    entry_rsi_threshold: float           # 25-45 (buy when oversold)
    
    # Exit: Let winners run
    exit_momentum_threshold: float       # 65-85 (exit when momentum peaks)
    trailing_stop_pct: float            # 5-15% (protect profits)
    
    # Position: Aggressive when trend is clear
    position_size_pct: float            # 70-100% (be aggressive)
    
    # Hold: Longer holds to catch trends
    min_hold_bars: int                  # 10-30
    max_hold_bars: int                  # 50-200 (let winners run!)

def create_random_gene() -> TrendGene:
    return TrendGene(
        entry_momentum_threshold=random.uniform(25, 42),
        entry_rsi_threshold=random.uniform(30, 45),
        exit_momentum_threshold=random.uniform(70, 85),
        trailing_stop_pct=random.uniform(7, 14),
        position_size_pct=random.uniform(80, 100),
        min_hold_bars=random.randint(15, 35),
        max_hold_bars=random.randint(60, 150)
    )

def mutate(gene: TrendGene, rate: float = 0.15) -> TrendGene:
    g = TrendGene(**gene.__dict__)
    
    if random.random() < rate:
        g.entry_momentum_threshold = np.clip(gene.entry_momentum_threshold + random.gauss(0, 3), 25, 42)
    if random.random() < rate:
        g.entry_rsi_threshold = np.clip(gene.entry_rsi_threshold + random.gauss(0, 3), 30, 45)
    if random.random() < rate:
        g.exit_momentum_threshold = np.clip(gene.exit_momentum_threshold + random.gauss(0, 3), 70, 85)
    if random.random() < rate:
        g.trailing_stop_pct = np.clip(gene.trailing_stop_pct + random.gauss(0, 1.5), 7, 14)
    if random.random() < rate:
        g.position_size_pct = np.clip(gene.position_size_pct + random.gauss(0, 5), 80, 100)
    if random.random() < rate:
        g.min_hold_bars = int(np.clip(gene.min_hold_bars + random.randint(-5, 5), 15, 35))
    if random.random() < rate:
        g.max_hold_bars = int(np.clip(gene.max_hold_bars + random.randint(-15, 15), 60, 150))
    
    return g

def crossover(p1: TrendGene, p2: TrendGene) -> Tuple[TrendGene, TrendGene]:
    c1 = TrendGene(
        entry_momentum_threshold=p1.entry_momentum_threshold if random.random() < 0.5 else p2.entry_momentum_threshold,
        entry_rsi_threshold=p1.entry_rsi_threshold if random.random() < 0.5 else p2.entry_rsi_threshold,
        exit_momentum_threshold=p1.exit_momentum_threshold if random.random() < 0.5 else p2.exit_momentum_threshold,
        trailing_stop_pct=p1.trailing_stop_pct if random.random() < 0.5 else p2.trailing_stop_pct,
        position_size_pct=p1.position_size_pct if random.random() < 0.5 else p2.position_size_pct,
        min_hold_bars=p1.min_hold_bars if random.random() < 0.5 else p2.min_hold_bars,
        max_hold_bars=p1.max_hold_bars if random.random() < 0.5 else p2.max_hold_bars
    )
    
    c2 = TrendGene(
        entry_momentum_threshold=p2.entry_momentum_threshold if random.random() < 0.5 else p1.entry_momentum_threshold,
        entry_rsi_threshold=p2.entry_rsi_threshold if random.random() < 0.5 else p1.entry_rsi_threshold,
        exit_momentum_threshold=p2.exit_momentum_threshold if random.random() < 0.5 else p1.exit_momentum_threshold,
        trailing_stop_pct=p2.trailing_stop_pct if random.random() < 0.5 else p1.trailing_stop_pct,
        position_size_pct=p2.position_size_pct if random.random() < 0.5 else p1.position_size_pct,
        min_hold_bars=p2.min_hold_bars if random.random() < 0.5 else p1.min_hold_bars,
        max_hold_bars=p2.max_hold_bars if random.random() < 0.5 else p1.max_hold_bars
    )
    
    return c1, c2

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.convolve(gains, np.ones(period)/period, mode='valid')
    avg_loss = np.convolve(losses, np.ones(period)/period, mode='valid')
    
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    
    # Pad to match original length
    rsi = np.concatenate([np.full(len(prices) - len(rsi), 50), rsi])
    return rsi

def backtest_gene(gene: TrendGene, data: pd.DataFrame, momentum: np.ndarray,
                  initial_capital: float = 10000) -> Dict:
    """Backtest with trend-following approach"""
    
    # Calculate RSI
    rsi = calculate_rsi(data['close'].values, period=14)
    
    capital = initial_capital
    position = 0
    entry_price = 0
    entry_bar = 0
    highest_price = 0
    trailing_stop = 0
    
    trades = []
    equity_curve = []
    
    for i in range(100, len(data)):
        current_price = data.iloc[i]['close']
        bars_held = i - entry_bar
        current_momentum = momentum[i]
        current_rsi = rsi[i]
        
        # No position - look for entry
        if position == 0:
            # Entry: Buy when momentum AND RSI both low (dip buying)
            if current_momentum < gene.entry_momentum_threshold and current_rsi < gene.entry_rsi_threshold:
                # Enter with large position
                size = capital * (gene.position_size_pct / 100)
                shares = int(size / current_price)
                
                if shares > 0 and capital >= size:
                    position = shares
                    entry_price = current_price
                    entry_bar = i
                    highest_price = current_price
                    trailing_stop = current_price * (1 - gene.trailing_stop_pct / 100)
                    capital -= shares * current_price * 1.001
        
        # Have position - manage it
        elif position > 0:
            # Update highest price and trailing stop
            if current_price > highest_price:
                highest_price = current_price
                trailing_stop = highest_price * (1 - gene.trailing_stop_pct / 100)
            
            pnl_pct = ((current_price / entry_price) - 1) * 100
            
            exit_signal = False
            exit_reason = ''
            
            # Trailing stop (protect profits)
            if current_price <= trailing_stop and bars_held >= gene.min_hold_bars:
                exit_signal = True
                exit_reason = 'trailing_stop'
            
            # Momentum exit (trend reversal)
            if current_momentum > gene.exit_momentum_threshold and bars_held >= gene.min_hold_bars:
                exit_signal = True
                exit_reason = 'momentum_exit'
            
            # Max hold (force exit)
            if bars_held >= gene.max_hold_bars:
                exit_signal = True
                exit_reason = 'max_hold'
            
            # Execute exit
            if exit_signal:
                pnl = position * (current_price - entry_price) * 0.999
                capital += pnl + (position * entry_price)
                
                trades.append({
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'exit_reason': exit_reason
                })
                
                position = 0
        
        # Track equity
        if position > 0:
            equity_curve.append(capital + position * current_price)
        else:
            equity_curve.append(capital)
    
    # Metrics
    if len(trades) < 3:
        return {
            'total_return': -100,
            'total_trades': len(trades),
            'win_rate': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
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
    
    return {
        'total_return': total_return,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'final_capital': capital
    }

def calculate_alpha_fitness(gene: TrendGene, periods: List[Dict]) -> Dict:
    """
    Fitness = ALPHA (outperformance vs buy-and-hold)
    Strategy must beat benchmark consistently
    """
    alphas = []
    period_results = []
    
    for period in periods:
        # Strategy performance
        strategy_result = backtest_gene(gene, period['data'], period['momentum'])
        
        # Buy-and-hold performance
        bh_return = period['bh_return']
        
        # Alpha = Strategy - Buy&Hold
        alpha = strategy_result['total_return'] - bh_return
        alphas.append(alpha)
        
        period_results.append({
            'strategy_return': strategy_result['total_return'],
            'bh_return': bh_return,
            'alpha': alpha,
            'trades': strategy_result['total_trades'],
            'sharpe': strategy_result['sharpe_ratio']
        })
    
    # Filter out periods with too few trades
    valid_periods = [p for p in period_results if p['trades'] >= 3]
    
    if len(valid_periods) < len(periods) * 0.6:  # Must work in at least 60% of periods
        return {'fitness': -1000, 'period_results': period_results, 'avg_alpha': -100}
    
    valid_alphas = [p['alpha'] for p in valid_periods]
    
    # Calculate fitness based on ALPHA
    avg_alpha = np.mean(valid_alphas)
    min_alpha = min(valid_alphas)
    positive_periods = sum(1 for a in valid_alphas if a > 0)
    positive_ratio = positive_periods / len(valid_alphas)
    
    # Fitness function emphasizing consistent outperformance
    fitness = (
        avg_alpha * 0.50 +                          # Average alpha (main driver)
        min_alpha * 0.20 +                          # Worst alpha (avoid disasters)
        positive_ratio * 100 * 0.20 +               # % of periods beating B&H
        np.mean([p['sharpe'] for p in valid_periods]) * 30 * 0.10  # Sharpe bonus
    )
    
    # Penalty for inconsistency
    alpha_std = np.std(valid_alphas)
    fitness -= alpha_std * 0.3
    
    return {
        'fitness': fitness,
        'period_results': period_results,
        'avg_alpha': avg_alpha,
        'min_alpha': min_alpha,
        'positive_ratio': positive_ratio,
        'alpha_std': alpha_std
    }

def evolve(periods: List[Dict], population_size: int = 50, generations: int = 50) -> Tuple:
    """Evolve to beat benchmark"""
    
    print(f"\n🧬 Evolution Parameters:")
    print(f"   Population: {population_size}")
    print(f"   Generations: {generations}")
    print(f"   Fitness: ALPHA (Strategy - Buy&Hold)")
    print(f"   Goal: Consistently beat benchmark")
    
    population = [create_random_gene() for _ in range(population_size)]
    
    best_gene = None
    best_fitness = -float('inf')
    best_result = None
    
    for gen in range(generations):
        fitness_scores = []
        results = []
        
        for gene in population:
            result = calculate_alpha_fitness(gene, periods)
            fitness_scores.append(result['fitness'])
            results.append(result)
            
            if result['fitness'] > best_fitness:
                best_fitness = result['fitness']
                best_gene = gene
                best_result = result
        
        avg_fitness = np.mean(fitness_scores)
        max_fitness = np.max(fitness_scores)
        best_idx = np.argmax(fitness_scores)
        best_gen = results[best_idx]
        
        if (gen + 1) % 5 == 0 or gen == 0:
            print(f"\n📊 Gen {gen+1}/{generations}: Fitness={max_fitness:6.1f} (Avg={avg_fitness:6.1f})")
            print(f"   Avg Alpha: {best_gen['avg_alpha']:+6.2f}% | Min: {best_gen['min_alpha']:+6.2f}% | "
                  f"Win Rate: {best_gen['positive_ratio']*100:.0f}%")
        
        # Selection
        elite_count = max(4, int(population_size * 0.12))
        sorted_indices = np.argsort(fitness_scores)[::-1]
        elite = [population[i] for i in sorted_indices[:elite_count]]
        
        new_population = elite.copy()
        
        # Breed
        while len(new_population) < population_size:
            p1 = elite[random.randint(0, len(elite)-1)]
            p2 = elite[random.randint(0, len(elite)-1)]
            
            c1, c2 = crossover(p1, p2)
            c1 = mutate(c1, rate=0.15)
            c2 = mutate(c2, rate=0.15)
            
            new_population.append(c1)
            if len(new_population) < population_size:
                new_population.append(c2)
        
        population = new_population
    
    return best_gene, best_result

if __name__ == '__main__':
    start_time = datetime.now()
    print(f"\n⏰ Started: {start_time.strftime('%H:%M:%S')}")
    
    # Download data
    print("\n📥 Downloading data...")
    all_data = yf.download('SPY', start='2000-01-01', end='2024-12-31', progress=False)
    
    if isinstance(all_data.columns, pd.MultiIndex):
        all_data.columns = [col[0].lower() for col in all_data.columns]
    else:
        all_data.columns = all_data.columns.str.lower()
    
    # Calculate momentum
    momentum_result = calculate_momentum_indicator(all_data, length=7, threshold=2.0)
    all_momentum = momentum_result['momentum']
    
    # Create 5-year periods with buy-and-hold returns
    print("\n📊 Creating periods with buy-and-hold benchmarks...")
    periods = []
    start_years = [2000, 2005, 2010, 2015, 2020]
    
    for start_year in start_years:
        end_year = start_year + 5
        mask = (all_data.index.year >= start_year) & (all_data.index.year < end_year)
        period_data = all_data[mask].copy()
        period_momentum = all_momentum[mask]
        
        if len(period_data) > 500:
            # Calculate buy-and-hold return for this period
            bh_return = ((period_data['close'].iloc[-1] / period_data['close'].iloc[0]) - 1) * 100
            
            periods.append({
                'name': f'{start_year}-{end_year-1}',
                'data': period_data,
                'momentum': period_momentum,
                'bh_return': bh_return
            })
            print(f"   {start_year}-{end_year-1}: B&H = +{bh_return:6.2f}%")
    
    # Run evolution
    print("\n🧬 Evolving strategy to beat buy-and-hold...")
    best_gene, best_result = evolve(periods, population_size=50, generations=50)
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    
    # Results
    print("\n" + "=" * 80)
    print("  🏆 BEST STRATEGY (OPTIMIZED TO BEAT BUY-AND-HOLD)")
    print("=" * 80)
    
    print(f"\n🧬 PARAMETERS:")
    print(f"   Entry Momentum: < {best_gene.entry_momentum_threshold:.1f}")
    print(f"   Entry RSI: < {best_gene.entry_rsi_threshold:.1f}")
    print(f"   Exit Momentum: > {best_gene.exit_momentum_threshold:.1f}")
    print(f"   Trailing Stop: {best_gene.trailing_stop_pct:.1f}%")
    print(f"   Position Size: {best_gene.position_size_pct:.0f}%")
    print(f"   Hold Period: {best_gene.min_hold_bars}-{best_gene.max_hold_bars} bars")
    
    print(f"\n💰 ALPHA ANALYSIS:")
    print(f"   Average Alpha: {best_result['avg_alpha']:+.2f}%")
    print(f"   Worst Alpha: {best_result['min_alpha']:+.2f}%")
    print(f"   Periods Beating B&H: {best_result['positive_ratio']*100:.0f}%")
    print(f"   Alpha Std Dev: {best_result['alpha_std']:.2f}%")
    
    print(f"\n📊 PERIOD-BY-PERIOD RESULTS:")
    print("\n┌────────────┬───────────────┬───────────────┬─────────────┬────────┐")
    print("│   Period   │  Strategy (%) │  Buy&Hold (%) │  Alpha (%)  │ Trades │")
    print("├────────────┼───────────────┼───────────────┼─────────────┼────────┤")
    
    for i, period in enumerate(periods):
        pr = best_result['period_results'][i]
        winner = "✅" if pr['alpha'] > 0 else "❌"
        print(f"│ {period['name']:10} │ {pr['strategy_return']:>12.2f}% │ {pr['bh_return']:>12.2f}% │ "
              f"{pr['alpha']:>+10.2f}% {winner} │ {pr['trades']:>6} │")
    
    print("└────────────┴───────────────┴───────────────┴─────────────┴────────┘")
    
    # Test on 2024
    print("\n📥 Testing on 2024...")
    data_2024 = all_data[all_data.index.year == 2024].copy()
    momentum_2024 = all_momentum[all_data.index.year == 2024]
    
    if len(data_2024) > 100:
        test_2024 = backtest_gene(best_gene, data_2024, momentum_2024)
        bh_2024 = ((data_2024['close'].iloc[-1] / data_2024['close'].iloc[0]) - 1) * 100
        alpha_2024 = test_2024['total_return'] - bh_2024
        
        print(f"\n💰 2024 RESULTS:")
        print(f"   Strategy: {test_2024['total_return']:+.2f}%")
        print(f"   Buy&Hold: {bh_2024:+.2f}%")
        print(f"   Alpha: {alpha_2024:+.2f}% {'✅' if alpha_2024 > 0 else '❌'}")
        print(f"   Trades: {test_2024['total_trades']}")
    
    # Save
    gene_dict = best_gene.__dict__.copy()
    with open('best_alpha_strategy.json', 'w') as f:
        json.dump(gene_dict, f, indent=2)
    
    print(f"\n✅ Strategy saved to: best_alpha_strategy.json")
    print(f"⏰ Total time: {elapsed:.1f} minutes")
    
    print("\n" + "=" * 80)
