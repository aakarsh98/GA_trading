"""
Main entry point for running strategy backtests
"""
import sys
import os
import argparse

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from utils.data_generator import load_sample_data
from tests.test_strategies import StrategyTester, run_comprehensive_tests


def run_single_strategy(strategy_name: str, data_type: str = 'mixed', n_bars: int = 2000):
    """Run a single strategy test"""
    from strategies.survival_analysis_filter import SurvivalAnalysisFilter
    from strategies.lead_lag_detection import LeadLagDetection
    from strategies.multi_timeframe_attention import MultiTimeframeAttention
    from strategies.hidden_markov_regime import HiddenMarkovRegime
    from strategies.statistical_arbitrage import StatisticalArbitrage
    from strategies.edge_scoring import EdgeScoring
    from strategies.meta_reinforcement_learning import MetaReinforcementLearning
    from strategies.cross_asset_momentum import CrossAssetMomentum
    from strategies.llm_inspired_features import LLMInspiredFeatures
    
    strategies = {
        'survival': (SurvivalAnalysisFilter, "Survival Analysis Filter"),
        'leadlag': (LeadLagDetection, "Lead-Lag Detection"),
        'attention': (MultiTimeframeAttention, "Multi-Timeframe Attention"),
        'hmm': (HiddenMarkovRegime, "Hidden Markov Models"),
        'arbitrage': (StatisticalArbitrage, "Statistical Arbitrage"),
        'edge': (EdgeScoring, "Real-Time Edge Scoring"),
        'meta': (MetaReinforcementLearning, "Meta-Reinforcement Learning"),
        'crossasset': (CrossAssetMomentum, "Cross-Asset Momentum"),
        'llm': (LLMInspiredFeatures, "LLM-Inspired Features"),
    }
    
    if strategy_name not in strategies:
        print(f"Unknown strategy: {strategy_name}")
        print(f"Available strategies: {', '.join(strategies.keys())}")
        return
    
    # Load data
    print(f"Loading {data_type} market data ({n_bars} bars)...")
    data = load_sample_data(data_type, n_bars)
    
    # Run test
    tester = StrategyTester()
    strategy_class, name = strategies[strategy_name]
    result = tester.test_strategy(strategy_class, data, name)
    
    return result


def run_quick_test():
    """Run a quick test on all strategies with limited data"""
    print("\nRunning Quick Test (500 bars, mixed market)...")
    data = load_sample_data('mixed', 500)
    
    tester = StrategyTester()
    results = tester.test_all_strategies(data)
    tester.generate_report(results)
    
    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Trading Strategy Backtesting Framework')
    parser.add_argument('--mode', choices=['quick', 'full', 'single'], default='quick',
                       help='Test mode: quick (fast), full (comprehensive), single (one strategy)')
    parser.add_argument('--strategy', type=str, help='Strategy name for single mode')
    parser.add_argument('--data', choices=['mixed', 'trending', 'volatile', 'regime_switching'], 
                       default='mixed', help='Market data type')
    parser.add_argument('--bars', type=int, default=2000, help='Number of bars to test')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("TRADING STRATEGY BACKTESTING FRAMEWORK")
    print("Research-Based Strategy Implementation (2024-2025)")
    print("="*80)
    
    if args.mode == 'quick':
        results = run_quick_test()
        
    elif args.mode == 'full':
        results = run_comprehensive_tests()
        
    elif args.mode == 'single':
        if not args.strategy:
            print("Error: --strategy required for single mode")
            print("Available: survival, leadlag, attention, hmm, arbitrage, edge, meta, crossasset, llm")
            return
        results = run_single_strategy(args.strategy, args.data, args.bars)
    
    print("\n" + "="*80)
    print("BACKTESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    # If no arguments provided, run quick test
    if len(sys.argv) == 1:
        print("\nNo arguments provided. Running quick test...")
        print("Use --help for more options")
        run_quick_test()
    else:
        main()
