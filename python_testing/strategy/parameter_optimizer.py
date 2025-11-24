"""
Parameter Sensitivity Analysis and Optimization
Tests strategy across parameter ranges to find optimal settings
Research shows this prevents overfitting through robustness testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable
import matplotlib.pyplot as plt
from itertools import product


class ParameterOptimizer:
    """
    Performs parameter optimization and sensitivity analysis.
    
    Features:
    - Grid search optimization
    - Sensitivity analysis
    - Robustness testing
    - 3D visualization of parameter space
    """
    
    def __init__(self):
        self.results = []
    
    def grid_search(self, 
                   backtest_func: Callable,
                   param_grid: Dict[str, List],
                   metric: str = 'SharpeRatio') -> Dict:
        """
        Perform grid search over parameter space.
        
        Args:
            backtest_func: Function that runs backtest and returns results dict
            param_grid: Dictionary mapping parameter names to list of values
            metric: Metric to optimize (default: SharpeRatio)
            
        Returns:
            Dictionary with optimization results
        """
        print(f"\n🔍 Running grid search optimization...")
        print(f"  Parameters: {list(param_grid.keys())}")
        print(f"  Optimization metric: {metric}")
        
        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        print(f"  Total combinations: {len(combinations)}")
        
        results = []
        best_score = -float('inf')
        best_params = None
        
        for i, combo in enumerate(combinations):
            if i % 10 == 0:
                print(f"  Testing combination {i+1}/{len(combinations)}...")
            
            # Create parameter dict
            params = dict(zip(param_names, combo))
            
            try:
                # Run backtest with these parameters
                result = backtest_func(**params)
                
                score = result.get(metric, -float('inf'))
                
                results.append({
                    'params': params,
                    'score': score,
                    'result': result
                })
                
                # Track best
                if score > best_score:
                    best_score = score
                    best_params = params
                    
            except Exception as e:
                print(f"  Failed for {params}: {e}")
                continue
        
        print(f"✅ Grid search complete!")
        print(f"  Best {metric}: {best_score:.2f}")
        print(f"  Best params: {best_params}")
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results,
            'param_names': param_names,
            'metric': metric
        }
    
    def sensitivity_analysis(self,
                            backtest_func: Callable,
                            base_params: Dict,
                            param_ranges: Dict[str, List],
                            metric: str = 'SharpeRatio') -> Dict:
        """
        Analyze sensitivity of results to individual parameters.
        
        Args:
            backtest_func: Function that runs backtest
            base_params: Baseline parameter values
            param_ranges: Dictionary of parameters to test with value ranges
            metric: Metric to analyze
            
        Returns:
            Dictionary with sensitivity results
        """
        print(f"\n🔬 Running sensitivity analysis...")
        
        sensitivity_results = {}
        
        for param_name, param_values in param_ranges.items():
            print(f"  Analyzing {param_name}...")
            
            scores = []
            returns = []
            drawdowns = []
            
            for value in param_values:
                # Create test parameters
                test_params = base_params.copy()
                test_params[param_name] = value
                
                try:
                    result = backtest_func(**test_params)
                    scores.append(result.get(metric, 0))
                    returns.append(result.get('ReturnPct', 0))
                    drawdowns.append(result.get('MaxDrawdownPct', 0))
                except:
                    scores.append(0)
                    returns.append(0)
                    drawdowns.append(0)
            
            sensitivity_results[param_name] = {
                'values': param_values,
                'scores': scores,
                'returns': returns,
                'drawdowns': drawdowns,
                'best_value': param_values[np.argmax(scores)],
                'best_score': max(scores),
                'sensitivity': np.std(scores) / (np.mean(scores) + 1e-10)  # Coefficient of variation
            }
        
        print(f"✅ Sensitivity analysis complete!")
        
        return sensitivity_results
    
    def robustness_test(self,
                       grid_results: Dict,
                       threshold_percentile: float = 75) -> Dict:
        """
        Test robustness by finding parameters that perform well across conditions.
        
        Args:
            grid_results: Results from grid_search
            threshold_percentile: Percentile threshold for "good" performance
            
        Returns:
            Dictionary with robustness analysis
        """
        print(f"\n🛡️  Running robustness test...")
        
        all_scores = [r['score'] for r in grid_results['all_results']]
        threshold = np.percentile(all_scores, threshold_percentile)
        
        print(f"  Performance threshold ({threshold_percentile}th percentile): {threshold:.2f}")
        
        # Find robust parameters (perform well consistently)
        robust_params = []
        for result in grid_results['all_results']:
            if result['score'] >= threshold:
                robust_params.append(result['params'])
        
        print(f"  Robust parameter sets: {len(robust_params)}/{len(grid_results['all_results'])}")
        
        # Analyze parameter distributions among robust sets
        if robust_params:
            param_distributions = {}
            for param_name in grid_results['param_names']:
                values = [p[param_name] for p in robust_params]
                param_distributions[param_name] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
        else:
            param_distributions = {}
        
        return {
            'threshold': threshold,
            'n_robust': len(robust_params),
            'robust_params': robust_params,
            'param_distributions': param_distributions,
            'robustness_ratio': len(robust_params) / len(grid_results['all_results'])
        }
    
    def plot_sensitivity(self, sensitivity_results: Dict):
        """Plot sensitivity analysis results."""
        n_params = len(sensitivity_results)
        fig, axes = plt.subplots(n_params, 1, figsize=(12, 4*n_params))
        
        if n_params == 1:
            axes = [axes]
        
        for ax, (param_name, results) in zip(axes, sensitivity_results.items()):
            values = results['values']
            scores = results['scores']
            
            ax.plot(values, scores, 'o-', linewidth=2, markersize=8)
            ax.axvline(x=results['best_value'], color='red', linestyle='--', 
                      alpha=0.5, label=f"Best: {results['best_value']}")
            ax.set_xlabel(param_name)
            ax.set_ylabel('Score')
            ax.set_title(f'Sensitivity: {param_name} (Sensitivity={results["sensitivity"]:.3f})')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, axes
    
    def plot_heatmap(self, grid_results: Dict):
        """Plot 2D heatmap of parameter space (for 2-parameter optimization)."""
        param_names = grid_results['param_names']
        
        if len(param_names) != 2:
            print("Heatmap requires exactly 2 parameters")
            return None
        
        # Extract unique parameter values
        param1_values = sorted(set(r['params'][param_names[0]] for r in grid_results['all_results']))
        param2_values = sorted(set(r['params'][param_names[1]] for r in grid_results['all_results']))
        
        # Create score matrix
        score_matrix = np.zeros((len(param2_values), len(param1_values)))
        
        for result in grid_results['all_results']:
            i = param2_values.index(result['params'][param_names[1]])
            j = param1_values.index(result['params'][param_names[0]])
            score_matrix[i, j] = result['score']
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(score_matrix, cmap='RdYlGn', aspect='auto')
        
        ax.set_xticks(range(len(param1_values)))
        ax.set_yticks(range(len(param2_values)))
        ax.set_xticklabels([f'{v:.2f}' for v in param1_values])
        ax.set_yticklabels([f'{v:.2f}' for v in param2_values])
        
        ax.set_xlabel(param_names[0])
        ax.set_ylabel(param_names[1])
        ax.set_title(f'Parameter Space Heatmap ({grid_results["metric"]})')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(grid_results['metric'])
        
        # Mark best point
        best_params = grid_results['best_params']
        best_i = param2_values.index(best_params[param_names[1]])
        best_j = param1_values.index(best_params[param_names[0]])
        ax.plot(best_j, best_i, 'r*', markersize=20, label='Best')
        ax.legend()
        
        plt.tight_layout()
        return fig, ax
    
    def print_results(self, grid_results: Dict):
        """Print optimization results."""
        print("\n" + "="*60)
        print(" PARAMETER OPTIMIZATION RESULTS")
        print("="*60)
        
        print(f"\n🎯 OPTIMIZATION METRIC: {grid_results['metric']}")
        
        print(f"\n🏆 BEST PARAMETERS:")
        for param, value in grid_results['best_params'].items():
            print(f"  {param}: {value}")
        print(f"  Score: {grid_results['best_score']:.2f}")
        
        # Show top 5 parameter sets
        sorted_results = sorted(grid_results['all_results'], 
                              key=lambda x: x['score'], reverse=True)
        
        print(f"\n📊 TOP 5 PARAMETER SETS:")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"\n  #{i}: Score = {result['score']:.2f}")
            for param, value in result['params'].items():
                print(f"    {param}: {value}")
        
        print("\n" + "="*60)


def main():
    """Demo parameter optimizer."""
    print("=== Parameter Optimizer Demo ===\n")
    print("This module requires a backtest function to optimize.")
    print("Run the advanced testing script to see it in action!")


if __name__ == '__main__':
    main()
