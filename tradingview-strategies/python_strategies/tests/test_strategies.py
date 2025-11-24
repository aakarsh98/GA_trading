"""Comprehensive testing framework for all strategies"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from typing import Dict, List
import json
from datetime import datetime

from strategies.survival_analysis_filter import SurvivalAnalysisFilter
from strategies.lead_lag_detection import LeadLagDetection
from strategies.multi_timeframe_attention import MultiTimeframeAttention
from strategies.hidden_markov_regime import HiddenMarkovRegime
from strategies.statistical_arbitrage import StatisticalArbitrage
from strategies.edge_scoring import EdgeScoring
from strategies.meta_reinforcement_learning import MetaReinforcementLearning
from strategies.cross_asset_momentum import CrossAssetMomentum
from strategies.llm_inspired_features import LLMInspiredFeatures
from utils.data_generator import load_sample_data


class StrategyTester:
    """Comprehensive strategy testing framework"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.results = {}
        
    def test_strategy(self, strategy_class, data: pd.DataFrame, strategy_name: str = None, **kwargs) -> Dict:
        """Test a single strategy"""
        print(f"\n{'='*60}")
        print(f"Testing: {strategy_name or strategy_class.__name__}")
        print(f"{'='*60}")
        
        try:
            strategy = strategy_class(initial_capital=self.initial_capital, **kwargs)
            results = strategy.backtest(data)
            
            print(f"Results:")
            print(f"  Total Trades: {results['total_trades']}")
            print(f"  Win Rate: {results['win_rate']:.2f}%")
            print(f"  Net Profit: ${results['net_profit']:.2f} ({results['net_profit_pct']:.2f}%)")
            print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
            print(f"  Final Capital: ${results['final_capital']:.2f}")
            
            return results
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'strategy_name': strategy_name or strategy_class.__name__,
                'error': str(e),
                'total_trades': 0
            }
    
    def test_all_strategies(self, data: pd.DataFrame) -> Dict:
        """Test all implemented strategies"""
        print("\n" + "="*80)
        print("COMPREHENSIVE STRATEGY TESTING")
        print("="*80)
        print(f"Data: {len(data)} bars from {data.index[0]} to {data.index[-1]}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print("="*80)
        
        strategies_to_test = [
            (SurvivalAnalysisFilter, "Phase 1.1: Survival Analysis Filter"),
            (LeadLagDetection, "Phase 1.2: Lead-Lag Detection"),
            (MultiTimeframeAttention, "Phase 1.3: Multi-Timeframe Attention"),
            (HiddenMarkovRegime, "Phase 2.1: Hidden Markov Models"),
            (StatisticalArbitrage, "Phase 2.2: Statistical Arbitrage"),
            (EdgeScoring, "Phase 2.3: Real-Time Edge Scoring"),
            (MetaReinforcementLearning, "Phase 3.1: Meta-Reinforcement Learning"),
            (CrossAssetMomentum, "Phase 3.2: Cross-Asset Momentum Analysis"),
            (LLMInspiredFeatures, "Phase 3.3: LLM-Inspired Features"),
        ]
        
        results = {}
        
        for strategy_class, name in strategies_to_test:
            result = self.test_strategy(strategy_class, data.copy(), name)
            results[name] = result
        
        return results
    
    def compare_strategies(self, results: Dict) -> pd.DataFrame:
        """Compare all strategies performance"""
        comparison_data = []
        
        for name, result in results.items():
            if 'error' in result:
                continue
                
            comparison_data.append({
                'Strategy': result['strategy_name'],
                'Total Trades': result['total_trades'],
                'Win Rate (%)': round(result['win_rate'], 2),
                'Net Return (%)': round(result['net_profit_pct'], 2),
                'Sharpe Ratio': round(result['sharpe_ratio'], 2),
                'Max DD (%)': round(result['max_drawdown_pct'], 2),
                'Final Capital ($)': round(result['final_capital'], 2),
                'Avg Win ($)': round(result['avg_win'], 2),
                'Avg Loss ($)': round(result['avg_loss'], 2)
            })
        
        df = pd.DataFrame(comparison_data)
        
        if len(df) > 0:
            df = df.sort_values('Sharpe Ratio', ascending=False)
        
        return df
    
    def generate_report(self, results: Dict, output_file: str = None):
        """Generate comprehensive testing report"""
        print("\n" + "="*80)
        print("STRATEGY PERFORMANCE COMPARISON")
        print("="*80)
        
        comparison_df = self.compare_strategies(results)
        print("\n" + comparison_df.to_string(index=False))
        
        # Calculate aggregate statistics
        print("\n" + "="*80)
        print("AGGREGATE STATISTICS")
        print("="*80)
        
        valid_results = [r for r in results.values() if 'error' not in r and r['total_trades'] > 0]
        
        if valid_results:
            avg_win_rate = np.mean([r['win_rate'] for r in valid_results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in valid_results])
            avg_return = np.mean([r['net_profit_pct'] for r in valid_results])
            max_return = max([r['net_profit_pct'] for r in valid_results])
            best_strategy = max(valid_results, key=lambda x: x['sharpe_ratio'])
            
            print(f"Average Win Rate: {avg_win_rate:.2f}%")
            print(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
            print(f"Average Return: {avg_return:.2f}%")
            print(f"Maximum Return: {max_return:.2f}%")
            print(f"Best Strategy (by Sharpe): {best_strategy['strategy_name']}")
            print(f"  - Sharpe Ratio: {best_strategy['sharpe_ratio']:.2f}")
            print(f"  - Return: {best_strategy['net_profit_pct']:.2f}%")
            print(f"  - Win Rate: {best_strategy['win_rate']:.2f}%")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write("STRATEGY TESTING REPORT\n")
                f.write("="*80 + "\n\n")
                f.write(f"Test Date: {datetime.now()}\n")
                f.write(f"Initial Capital: ${self.initial_capital:,.2f}\n\n")
                f.write("\nPERFORMANCE COMPARISON\n")
                f.write("="*80 + "\n")
                f.write(comparison_df.to_string(index=False))
                f.write("\n\n")
                
                if valid_results:
                    f.write("AGGREGATE STATISTICS\n")
                    f.write("="*80 + "\n")
                    f.write(f"Average Win Rate: {avg_win_rate:.2f}%\n")
                    f.write(f"Average Sharpe Ratio: {avg_sharpe:.2f}\n")
                    f.write(f"Average Return: {avg_return:.2f}%\n")
                    f.write(f"Best Strategy: {best_strategy['strategy_name']}\n")
            
            print(f"\nReport saved to: {output_file}")
        
        return comparison_df


def run_comprehensive_tests():
    """Run comprehensive tests on all strategies"""
    print("\n" + "#"*80)
    print("STARTING COMPREHENSIVE STRATEGY TESTING")
    print("#"*80)
    
    # Initialize tester
    tester = StrategyTester(initial_capital=10000)
    
    # Test on different market conditions
    market_conditions = {
        'Mixed Markets': load_sample_data('mixed', 2000),
        'Trending Markets': load_sample_data('trending', 2000),
        'High Volatility': load_sample_data('volatile', 2000),
        'Regime Switching': load_sample_data('regime_switching', 2000),
    }
    
    all_results = {}
    
    for condition_name, data in market_conditions.items():
        print("\n" + "#"*80)
        print(f"TESTING IN: {condition_name}")
        print("#"*80)
        
        results = tester.test_all_strategies(data)
        all_results[condition_name] = results
        
        # Generate report for this condition
        report_file = f"/Users/aakarshraj/GG_ Script/tradingview-strategies/python_strategies/tests/report_{condition_name.replace(' ', '_').lower()}.txt"
        tester.generate_report(results, report_file)
    
    # Generate summary report
    print("\n" + "#"*80)
    print("CROSS-CONDITION PERFORMANCE SUMMARY")
    print("#"*80)
    
    for condition_name, results in all_results.items():
        print(f"\n{condition_name}:")
        valid_results = [r for r in results.values() if 'error' not in r and r['total_trades'] > 0]
        if valid_results:
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in valid_results])
            avg_return = np.mean([r['net_profit_pct'] for r in valid_results])
            print(f"  Average Sharpe: {avg_sharpe:.2f}")
            print(f"  Average Return: {avg_return:.2f}%")
    
    print("\n" + "#"*80)
    print("TESTING COMPLETE")
    print("#"*80)
    
    return all_results


if __name__ == "__main__":
    results = run_comprehensive_tests()
