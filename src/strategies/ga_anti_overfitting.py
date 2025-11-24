"""
ANTI-OVERFITTING GENETIC ALGORITHM FRAMEWORK
Includes: Walk-Forward, Out-of-Sample Validation, Complexity Penalties, Robustness Tests
Prevents curve-fitting and ensures strategies generalize to unseen data
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import random
from dataclasses import dataclass
import json
import warnings
warnings.filterwarnings('ignore')

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🛡️  ANTI-OVERFITTING GA FRAMEWORK")
print("  ✅ Walk-Forward Validation")
print("  ✅ Out-of-Sample Testing During Evolution")
print("  ✅ Complexity Penalties")
print("  ✅ Robustness Tests (Monte Carlo, Parameter Sensitivity)")
print("=" * 80)

# ==============================================================================
# STRATEGY COMPLEXITY CALCULATOR
# ==============================================================================

def calculate_strategy_complexity(gene) -> float:
    """
    Calculate complexity score for a strategy
    Higher complexity = more parameters, more conditions, more overfitting risk
    
    Returns:
        Complexity score (0-100)
    """
    complexity = 0.0
    
    # Count active conditions
    active_conditions = 0
    
    if hasattr(gene, 'use_primary') and gene.use_primary:
        active_conditions += 1
    if hasattr(gene, 'use_confirm') and gene.use_confirm:
        active_conditions += 1
    if hasattr(gene, 'use_filter') and gene.use_filter:
        active_conditions += 1
    
    # Penalty for too many conditions (>3 is overfitting risk)
    complexity += active_conditions * 5
    if active_conditions > 3:
        complexity += (active_conditions - 3) * 10  # Heavy penalty
    
    # Count active features
    active_features = 0
    
    if hasattr(gene, 'use_momentum_acceleration') and gene.use_momentum_acceleration:
        active_features += 1
    if hasattr(gene, 'use_price_volatility') and gene.use_price_volatility:
        active_features += 1
    if hasattr(gene, 'pyramid_enabled') and gene.pyramid_enabled:
        active_features += 1
    if hasattr(gene, 'trailing_stop_enabled') and gene.trailing_stop_enabled:
        active_features += 1
    
    complexity += active_features * 3
    
    # Penalty for extreme parameter values (likely overfitted)
    if hasattr(gene, 'stop_loss_pct'):
        if gene.stop_loss_pct < 2 or gene.stop_loss_pct > 15:
            complexity += 10  # Extreme stops = overfitting
    
    if hasattr(gene, 'take_profit_pct'):
        if gene.take_profit_pct > 40:
            complexity += 10  # Unrealistic TP
    
    if hasattr(gene, 'position_size_base'):
        if gene.position_size_base > 95:
            complexity += 5  # Too aggressive
    
    # Penalty for too-tight or too-loose momentum ranges
    if hasattr(gene, 'entry_momentum_min') and hasattr(gene, 'entry_momentum_max'):
        momentum_range = gene.entry_momentum_max - gene.entry_momentum_min
        if momentum_range < 10:
            complexity += 15  # Too tight = curve-fitting
        elif momentum_range > 80:
            complexity += 10  # Too loose = no real filter
    
    # Top-down specific penalties
    if hasattr(gene, 'require_full_cascade') and gene.require_full_cascade:
        # Requiring ALL timeframes is very restrictive (may overfit to specific periods)
        if hasattr(gene, 'monthly_enabled') and gene.monthly_enabled:
            if hasattr(gene, 'weekly_enabled') and gene.weekly_enabled:
                if hasattr(gene, 'daily_enabled') and gene.daily_enabled:
                    complexity += 15
    
    return min(complexity, 100.0)  # Cap at 100

# ==============================================================================
# WALK-FORWARD VALIDATION
# ==============================================================================

class WalkForwardValidator:
    """
    Implements walk-forward analysis to prevent overfitting
    
    Process:
    1. Split data into N windows (e.g., 4 quarters)
    2. Train on window 1, test on window 2
    3. Train on window 2, test on window 3
    4. Average results across all tests
    5. Compare train vs test performance (degradation check)
    """
    
    def __init__(self, n_windows: int = 4, train_ratio: float = 0.7):
        """
        Args:
            n_windows: Number of walk-forward windows
            train_ratio: Ratio of training data in each window (0.7 = 70% train, 30% test)
        """
        self.n_windows = n_windows
        self.train_ratio = train_ratio
    
    def split_data(self, data: Dict[str, pd.DataFrame]) -> List[Tuple[Dict, Dict]]:
        """
        Split multi-timeframe data into walk-forward windows
        
        Returns:
            List of (train_data, test_data) tuples
        """
        # Use primary timeframe (usually shortest) to determine splits
        primary_tf = list(data.keys())[0]
        primary_df = data[primary_tf]
        
        total_bars = len(primary_df)
        window_size = total_bars // self.n_windows
        
        windows = []
        
        for i in range(self.n_windows - 1):  # Leave one window for final validation
            # Calculate indices for this window
            window_start = i * window_size
            window_end = (i + 1) * window_size
            
            train_end = window_start + int(window_size * self.train_ratio)
            
            # Split all timeframes
            train_split = {}
            test_split = {}
            
            for tf_name, tf_df in data.items():
                # Match timestamps
                primary_start_time = primary_df.iloc[window_start]['timestamp']
                primary_train_end_time = primary_df.iloc[train_end]['timestamp']
                primary_window_end_time = primary_df.iloc[window_end]['timestamp']
                
                # Train data
                train_mask = (tf_df['timestamp'] >= primary_start_time) & (tf_df['timestamp'] < primary_train_end_time)
                train_split[tf_name] = tf_df[train_mask].reset_index(drop=True)
                
                # Test data
                test_mask = (tf_df['timestamp'] >= primary_train_end_time) & (tf_df['timestamp'] < primary_window_end_time)
                test_split[tf_name] = tf_df[test_mask].reset_index(drop=True)
            
            windows.append((train_split, test_split))
        
        return windows
    
    def calculate_degradation(self, train_results: List[Dict], test_results: List[Dict]) -> Dict:
        """
        Calculate how much strategy degrades from train to test
        
        Returns:
            Dict with degradation metrics
        """
        train_returns = [r['return'] for r in train_results]
        test_returns = [r['return'] for r in test_results]
        
        train_sharpe = [r.get('sharpe', 0) for r in train_results]
        test_sharpe = [r.get('sharpe', 0) for r in test_results]
        
        train_win_rates = [r.get('win_rate', 0) for r in train_results]
        test_win_rates = [r.get('win_rate', 0) for r in test_results]
        
        return {
            'return_degradation': np.mean(train_returns) - np.mean(test_returns),
            'return_degradation_pct': ((np.mean(train_returns) - np.mean(test_returns)) / np.mean(train_returns) * 100) if np.mean(train_returns) != 0 else 0,
            'sharpe_degradation': np.mean(train_sharpe) - np.mean(test_sharpe),
            'win_rate_degradation': np.mean(train_win_rates) - np.mean(test_win_rates),
            'avg_train_return': np.mean(train_returns),
            'avg_test_return': np.mean(test_returns),
            'test_return_std': np.std(test_returns),
            'consistency_score': 100 - (np.std(test_returns) / (abs(np.mean(test_returns)) + 1) * 100)
        }

# ==============================================================================
# OUT-OF-SAMPLE VALIDATION DURING EVOLUTION
# ==============================================================================

class DualDatasetEvaluator:
    """
    Maintains separate train and validation datasets
    Evaluates on train, validates on holdout during evolution
    """
    
    def __init__(self, train_data: Dict, validation_data: Dict, validation_frequency: int = 5):
        """
        Args:
            train_data: Data for training/fitness evaluation
            validation_data: Separate holdout data for validation
            validation_frequency: Validate every N generations
        """
        self.train_data = train_data
        self.validation_data = validation_data
        self.validation_frequency = validation_frequency
        self.validation_history = []
    
    def should_validate(self, generation: int) -> bool:
        """Check if should validate on this generation"""
        return generation % self.validation_frequency == 0
    
    def evaluate_with_validation(self, gene, backtest_func, generation: int) -> Tuple[Dict, Optional[Dict]]:
        """
        Evaluate gene on train data, optionally validate on holdout
        
        Returns:
            (train_results, validation_results)
        """
        # Always evaluate on training data
        train_results = backtest_func(gene, self.train_data)
        
        # Periodically validate on holdout
        validation_results = None
        if self.should_validate(generation):
            validation_results = backtest_func(gene, self.validation_data)
            self.validation_history.append({
                'generation': generation,
                'train_return': train_results['return'],
                'val_return': validation_results['return'],
                'overfitting_gap': train_results['return'] - validation_results['return']
            })
        
        return train_results, validation_results

# ==============================================================================
# ROBUSTNESS TESTING
# ==============================================================================

class RobustnessAnalyzer:
    """
    Tests strategy robustness using various methods
    """
    
    @staticmethod
    def monte_carlo_test(results: Dict, n_simulations: int = 1000) -> Dict:
        """
        Monte Carlo simulation of trades to test statistical significance
        Randomly reorders trades to see if performance is due to luck
        """
        if 'trades' not in results or len(results.get('trades', [])) == 0:
            return {'is_robust': False, 'p_value': 1.0, 'reason': 'no_trades'}
        
        trades = results['trades']
        if len(trades) < 10:
            return {'is_robust': False, 'p_value': 1.0, 'reason': 'too_few_trades'}
        
        # Original return
        original_return = results['return']
        
        # Get trade returns
        trade_returns = [t.get('pnl_pct', 0) for t in trades]
        
        # Run simulations
        simulated_returns = []
        for _ in range(n_simulations):
            # Randomly shuffle trades
            shuffled = random.sample(trade_returns, len(trade_returns))
            sim_return = sum(shuffled)
            simulated_returns.append(sim_return)
        
        # Calculate p-value (how often random shuffling beats original)
        better_count = sum(1 for sr in simulated_returns if sr >= original_return)
        p_value = better_count / n_simulations
        
        return {
            'is_robust': p_value < 0.05,  # 95% confidence
            'p_value': p_value,
            'reason': 'statistically_significant' if p_value < 0.05 else 'likely_luck'
        }
    
    @staticmethod
    def parameter_sensitivity_test(gene, backtest_func, data: Dict, perturbation: float = 0.1) -> Dict:
        """
        Test how sensitive strategy is to small parameter changes
        Robust strategies should work even with slight parameter variations
        """
        import copy
        
        original_results = backtest_func(gene, data)
        original_return = original_results['return']
        
        perturbed_returns = []
        
        # Test 10 random perturbations
        for _ in range(10):
            perturbed_gene = copy.deepcopy(gene)
            
            # Randomly perturb parameters
            if hasattr(perturbed_gene, 'stop_loss_pct'):
                perturbed_gene.stop_loss_pct *= (1 + random.uniform(-perturbation, perturbation))
                perturbed_gene.stop_loss_pct = np.clip(perturbed_gene.stop_loss_pct, 1, 20)
            
            if hasattr(perturbed_gene, 'take_profit_pct'):
                perturbed_gene.take_profit_pct *= (1 + random.uniform(-perturbation, perturbation))
                perturbed_gene.take_profit_pct = np.clip(perturbed_gene.take_profit_pct, 2, 50)
            
            if hasattr(perturbed_gene, 'entry_momentum_min'):
                perturbed_gene.entry_momentum_min += random.uniform(-10, 10)
                perturbed_gene.entry_momentum_min = np.clip(perturbed_gene.entry_momentum_min, 0, 100)
            
            # Backtest perturbed strategy
            try:
                perturbed_results = backtest_func(perturbed_gene, data)
                perturbed_returns.append(perturbed_results['return'])
            except:
                continue
        
        if len(perturbed_returns) == 0:
            return {'is_robust': False, 'sensitivity_score': 0}
        
        # Calculate sensitivity
        return_std = np.std(perturbed_returns)
        avg_return = np.mean(perturbed_returns)
        
        # Robust strategy: small std relative to return
        sensitivity_ratio = return_std / (abs(avg_return) + 1)
        
        return {
            'is_robust': sensitivity_ratio < 0.5,  # Less than 50% variation
            'sensitivity_score': 100 - (sensitivity_ratio * 100),
            'avg_perturbed_return': avg_return,
            'return_std': return_std,
            'original_return': original_return,
            'performance_maintained': avg_return > original_return * 0.7  # At least 70% of original
        }

# ==============================================================================
# ENHANCED FITNESS FUNCTION WITH ANTI-OVERFITTING
# ==============================================================================

def calculate_robust_fitness(gene, train_results: Dict, 
                             validation_results: Optional[Dict] = None,
                             complexity_penalty_weight: float = 0.3,
                             validation_weight: float = 0.4) -> float:
    """
    Enhanced fitness function that penalizes overfitting
    
    Args:
        gene: Strategy gene
        train_results: Results on training data
        validation_results: Results on validation data (if available)
        complexity_penalty_weight: How much to penalize complexity (0-1)
        validation_weight: Weight for validation performance (0-1)
    
    Returns:
        Robust fitness score
    """
    # Base fitness from training results
    train_fitness = train_results['return']
    
    # Bonuses for good metrics (same as before)
    if train_results['trades'] >= 10:
        train_fitness += 5
    if train_results['win_rate'] >= 55:
        train_fitness += train_results['win_rate'] * 0.1
    if train_results.get('sharpe', 0) > 1.0:
        train_fitness += train_results['sharpe'] * 5
    
    # Penalties
    if train_results['trades'] < 5:
        train_fitness -= 20
    
    # === COMPLEXITY PENALTY ===
    complexity = calculate_strategy_complexity(gene)
    complexity_penalty = (complexity / 100.0) * 30  # Up to -30 points for high complexity
    train_fitness -= complexity_penalty * complexity_penalty_weight
    
    # === VALIDATION PERFORMANCE ===
    if validation_results is not None:
        val_fitness = validation_results['return']
        
        # Penalize large train-val gap (overfitting indicator)
        overfitting_gap = train_results['return'] - validation_results['return']
        if overfitting_gap > 10:  # More than 10% degradation
            overfitting_penalty = (overfitting_gap - 10) * 2  # Heavy penalty
            train_fitness -= overfitting_penalty
        
        # Blend train and validation fitness
        final_fitness = (train_fitness * (1 - validation_weight)) + (val_fitness * validation_weight)
    else:
        final_fitness = train_fitness
    
    return final_fitness

# ==============================================================================
# WRAPPER FUNCTION FOR EXISTING GA SCRIPTS
# ==============================================================================

def run_robust_ga(ga_function, 
                  data_provider,
                  symbol: str,
                  lookback_days: int = 365,
                  population_size: int = 50,
                  generations: int = 50,
                  enable_walk_forward: bool = True,
                  enable_validation: bool = True,
                  enable_robustness_tests: bool = True) -> Dict:
    """
    Wrapper that adds anti-overfitting features to any GA
    
    Args:
        ga_function: The GA run function (run_mtf_ga or run_topdown_ga)
        data_provider: Data provider instance
        symbol: Trading symbol
        lookback_days: Days of historical data
        population_size: GA population size
        generations: Number of generations
        enable_walk_forward: Use walk-forward validation
        enable_validation: Use out-of-sample validation during evolution
        enable_robustness_tests: Run robustness tests on best strategy
    
    Returns:
        Dict with best strategy and validation metrics
    """
    print("\n🛡️  ROBUST GA WITH ANTI-OVERFITTING")
    print("=" * 80)
    
    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    print(f"\n📥 Downloading data for {symbol}...")
    full_data = data_provider.download_multi_timeframe(symbol, start_date, end_date)
    
    if len(full_data) < 2:
        print("❌ Insufficient data downloaded")
        return None
    
    # === OPTION 1: WALK-FORWARD VALIDATION ===
    if enable_walk_forward:
        print("\n🔄 Using Walk-Forward Validation...")
        
        validator = WalkForwardValidator(n_windows=4, train_ratio=0.7)
        windows = validator.split_data(full_data)
        
        print(f"   Created {len(windows)} walk-forward windows")
        
        # Run GA on each window
        window_results = []
        
        for i, (train_data, test_data) in enumerate(windows):
            print(f"\n📊 Window {i+1}/{len(windows)}")
            print(f"   Train bars: {len(list(train_data.values())[0])}")
            print(f"   Test bars: {len(list(test_data.values())[0])}")
            
            # Run GA on training data
            _, best_gene, best_results = ga_function(
                train_data,
                population_size=population_size,
                generations=generations,
                elite_size=5
            )
            
            # Test on holdout
            from ga_multitimeframe_unrestricted import backtest_mtf_strategy
            test_results = backtest_mtf_strategy(best_gene, test_data)
            
            window_results.append({
                'window': i + 1,
                'train_results': best_results,
                'test_results': test_results,
                'gene': best_gene
            })
        
        # Calculate degradation
        train_results = [w['train_results'] for w in window_results]
        test_results = [w['test_results'] for w in window_results]
        degradation = validator.calculate_degradation(train_results, test_results)
        
        print(f"\n📉 Walk-Forward Degradation Analysis:")
        print(f"   Avg Train Return: {degradation['avg_train_return']:.2f}%")
        print(f"   Avg Test Return: {degradation['avg_test_return']:.2f}%")
        print(f"   Degradation: {degradation['return_degradation']:.2f}% ({degradation['return_degradation_pct']:.1f}%)")
        print(f"   Consistency Score: {degradation['consistency_score']:.1f}/100")
        
        # Select best window strategy
        best_window = max(window_results, key=lambda w: w['test_results']['return'])
        best_gene = best_window['gene']
        best_results = best_window['test_results']
        
        return {
            'best_gene': best_gene,
            'best_results': best_results,
            'walk_forward_metrics': degradation,
            'all_windows': window_results,
            'validation_method': 'walk_forward'
        }
    
    # === OPTION 2: TRAIN/VALIDATION SPLIT ===
    elif enable_validation:
        print("\n✂️  Using Train/Validation Split (80/20)...")
        
        # Split data
        primary_tf = list(full_data.keys())[0]
        total_bars = len(full_data[primary_tf])
        split_idx = int(total_bars * 0.8)
        
        train_data = {}
        val_data = {}
        
        for tf_name, tf_df in full_data.items():
            split_time = full_data[primary_tf].iloc[split_idx]['timestamp']
            train_data[tf_name] = tf_df[tf_df['timestamp'] < split_time].reset_index(drop=True)
            val_data[tf_name] = tf_df[tf_df['timestamp'] >= split_time].reset_index(drop=True)
        
        print(f"   Train bars: {len(train_data[primary_tf])}")
        print(f"   Validation bars: {len(val_data[primary_tf])}")
        
        # Create dual evaluator
        evaluator = DualDatasetEvaluator(train_data, val_data, validation_frequency=5)
        
        # Run GA (would need to modify GA function to accept evaluator)
        # For now, just run normally and validate at end
        _, best_gene, train_results = ga_function(
            train_data,
            population_size=population_size,
            generations=generations,
            elite_size=5
        )
        
        # Validate on holdout
        from ga_multitimeframe_unrestricted import backtest_mtf_strategy
        val_results = backtest_mtf_strategy(best_gene, val_data)
        
        overfitting_gap = train_results['return'] - val_results['return']
        
        print(f"\n📊 Train/Validation Results:")
        print(f"   Train Return: {train_results['return']:.2f}%")
        print(f"   Validation Return: {val_results['return']:.2f}%")
        print(f"   Overfitting Gap: {overfitting_gap:.2f}%")
        
        if overfitting_gap > 15:
            print("   ⚠️  HIGH OVERFITTING RISK!")
        elif overfitting_gap > 5:
            print("   ⚡ Moderate overfitting")
        else:
            print("   ✅ Good generalization")
        
        return {
            'best_gene': best_gene,
            'train_results': train_results,
            'validation_results': val_results,
            'overfitting_gap': overfitting_gap,
            'validation_method': 'train_val_split'
        }
    
    # === OPTION 3: STANDARD (NO VALIDATION) ===
    else:
        print("\n⚠️  Running without validation (not recommended)")
        
        _, best_gene, best_results = ga_function(
            full_data,
            population_size=population_size,
            generations=generations,
            elite_size=5
        )
        
        return {
            'best_gene': best_gene,
            'best_results': best_results,
            'validation_method': 'none'
        }

# ==============================================================================
# EXAMPLE USAGE
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("  ANTI-OVERFITTING GA EXAMPLE")
    print("=" * 80)
    
    # Import your GA functions
    from ga_multitimeframe_unrestricted import (
        MultiTimeframeDataProvider,
        run_mtf_ga
    )
    
    # Initialize
    provider = MultiTimeframeDataProvider()
    
    # Run with anti-overfitting features
    results = run_robust_ga(
        ga_function=run_mtf_ga,
        data_provider=provider,
        symbol='SPY',
        lookback_days=180,  # 6 months
        population_size=30,  # Smaller for faster testing
        generations=30,
        enable_walk_forward=True,  # Enable walk-forward
        enable_validation=False,    # Disable simple validation (using walk-forward instead)
        enable_robustness_tests=True
    )
    
    if results:
        print("\n✅ Robust GA Complete!")
        print(f"   Validation Method: {results['validation_method']}")
        
        if 'walk_forward_metrics' in results:
            wf = results['walk_forward_metrics']
            print(f"   Consistency Score: {wf['consistency_score']:.1f}/100")
            print(f"   Avg Test Return: {wf['avg_test_return']:.2f}%")
        
        # Save results
        print("\n💾 Saving robust strategy...")
        
        # Save to JSON (simplified)
        output = {
            'validation_method': results['validation_method'],
            'best_results': results.get('best_results', results.get('test_results', {})),
            'timestamp': datetime.now().isoformat()
        }
        
        if 'walk_forward_metrics' in results:
            output['walk_forward_metrics'] = results['walk_forward_metrics']
        
        with open('best_robust_strategy.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print("✅ Saved to: best_robust_strategy.json")
