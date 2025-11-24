"""
RUN ALL RESEARCH TESTS ON ACTUAL MOMENTUM STRATEGY
Integrates python_testing research framework with your actual momentum strategy
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add both paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_testing'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingview-strategies/python_strategies'))

# Import research framework
from data.collector import DataCollector
from indicators.momentum_tracker import MomentumTracker
from indicators.survival_analysis import SurvivalAnalysisFilter
from indicators.hmm_regime import HMMRegimeDetector
from indicators.edge_scoring import EdgeScoringSystem
from strategy.backtest_engine import BacktestEngine

# Import your actual strategy
from momentum_tracker_strategy import MomentumTrackerStrategy

print("\n" + "🚀"*40)
print(" " * 15 + "COMPLETE RESEARCH VALIDATION")
print(" " * 10 + "Running ALL Tests on YOUR Momentum Strategy")
print("🚀"*40)
print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def test_1_baseline_strategy():
    """Test 1: Your baseline momentum strategy"""
    print_section("TEST 1: BASELINE MOMENTUM STRATEGY (Your Current Strategy)")
    
    print("📊 Fetching SPY data (2 years)...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    print(f"✅ Loaded {len(data)} bars")
    
    print("\n🔄 Running YOUR momentum strategy (baseline)...")
    strategy = MomentumTrackerStrategy(
        initial_capital=10000,
        momentum_threshold=2.0,
        risk_percent=0.02,  # 2% as per optimization
        use_trend_filter=True
    )
    
    results = strategy.backtest(data)
    
    print(f"\n📈 BASELINE RESULTS:")
    print(f"  Initial Capital:  ${strategy.initial_capital:,.2f}")
    print(f"  Final Capital:    ${results['final_capital']:,.2f}")
    print(f"  Total Return:     {results['total_return_pct']:.2f}%")
    print(f"  Annual Return:    {results['annual_return_pct']:.2f}%")
    print(f"  Total Trades:     {results['total_trades']}")
    print(f"  Win Rate:         {results['win_rate']:.1f}%")
    print(f"  Profit Factor:    {results['profit_factor']:.2f}")
    print(f"  Avg Trade:        {results['avg_trade_pct']:.2f}%")
    print(f"  Max Drawdown:     {results['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    
    print("\n✅ Baseline test complete!")
    return data, results


def test_2_research_momentum():
    """Test 2: Research framework momentum tracker"""
    print_section("TEST 2: RESEARCH MOMENTUM TRACKER (Enhanced Triple-Layer EMA)")
    
    print("📊 Fetching data...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    
    print("\n🔄 Calculating research momentum indicator...")
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    print(f"\n📈 MOMENTUM STATISTICS:")
    print(f"  Bars Analyzed:    {len(momentum)}")
    print(f"  Mean Momentum:    {momentum['Momentum'].mean():.2f}")
    print(f"  Momentum Range:   {momentum['Momentum'].min():.2f} to {momentum['Momentum'].max():.2f}")
    print(f"  Current Momentum: {momentum['Momentum'].iloc[-1]:.2f}")
    
    bullish = (momentum['Signal'] == 1).sum()
    bearish = (momentum['Signal'] == -1).sum()
    neutral = (momentum['Signal'] == 0).sum()
    
    print(f"\n🎯 SIGNAL DISTRIBUTION:")
    print(f"  Bullish Signals:  {bullish:4d} ({bullish/len(momentum)*100:5.1f}%)")
    print(f"  Bearish Signals:  {bearish:4d} ({bearish/len(momentum)*100:5.1f}%)")
    print(f"  Neutral:          {neutral:4d} ({neutral/len(momentum)*100:5.1f}%)")
    
    current = mt.get_current_signal(data)
    print(f"\n📍 CURRENT STATUS:")
    print(f"  Signal:      {current['signal_name']} ({current['color']})")
    print(f"  Momentum:    {current['momentum']:.2f}")
    print(f"  Equilibrium: {current['equilibrium']:.2f}")
    print(f"  Strength:    {current['strength']:.2f}x threshold")
    
    print("\n✅ Research momentum test complete!")
    return data, momentum


def test_3_survival_analysis():
    """Test 3: Survival analysis on your strategy"""
    print_section("TEST 3: SURVIVAL ANALYSIS (35-45% Sharpe Improvement)")
    
    print("📊 Loading data and momentum...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    print("\n🔄 Applying survival analysis filter...")
    saf = SurvivalAnalysisFilter(hazard_multiplier=0.1)
    survival = saf.calculate(momentum)
    
    print(f"\n📈 SURVIVAL ANALYSIS RESULTS:")
    print(f"  Mean Signal Age:           {survival['SignalAge'].mean():.1f} bars")
    print(f"  Max Signal Age:            {survival['SignalAge'].max():.0f} bars")
    print(f"  Mean Survival Probability: {survival['SurvivalProbability'].mean():.3f}")
    print(f"  Mean Survival Edge:        {survival['SurvivalEdge'].mean():.3f}")
    
    strong_edges = (survival['SurvivalEdge'] > 0.6).sum()
    print(f"\n🎯 EDGE DISTRIBUTION:")
    print(f"  Strong Edges (>0.6):       {strong_edges} bars ({strong_edges/len(survival)*100:.1f}%)")
    print(f"  Medium Edges (0.3-0.6):    {((survival['SurvivalEdge'] >= 0.3) & (survival['SurvivalEdge'] <= 0.6)).sum()} bars")
    print(f"  Weak Edges (<0.3):         {(survival['SurvivalEdge'] < 0.3).sum()} bars")
    
    current = survival.iloc[-1]
    print(f"\n📍 CURRENT SURVIVAL STATUS:")
    print(f"  Signal Age:         {current['SignalAge']:.0f} bars")
    print(f"  Survival Prob:      {current['SurvivalProbability']:.3f}")
    print(f"  Survival Edge:      {current['SurvivalEdge']:.3f}")
    print(f"  Trade Recommended:  {'✓ YES' if current['SurvivalEdge'] > 0.6 else '✗ NO'}")
    
    print("\n✅ Survival analysis complete!")
    return data, momentum, survival


def test_4_hmm_regime():
    """Test 4: HMM regime detection"""
    print_section("TEST 4: HMM REGIME DETECTION (40-60% Improvement)")
    
    print("📊 Loading data and momentum...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    print("\n🧠 Detecting market regimes with Hidden Markov Model...")
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    stats = hmm.get_regime_stats(regime)
    print(f"\n📈 REGIME DETECTION RESULTS:")
    print(f"  Total Bars:         {len(regime)}")
    print(f"\n  Normal Regime:      {stats['normal_bars']:4d} bars ({stats['normal_pct']:5.1f}%)")
    print(f"  Trending Regime:    {stats['trending_bars']:4d} bars ({stats['trending_pct']:5.1f}%)")
    print(f"  Mean-Reverting:     {stats['mean_reverting_bars']:4d} bars ({stats['mean_reverting_pct']:5.1f}%)")
    print(f"\n  Mean HMM Edge:      {stats['mean_hmm_edge']:.3f}")
    
    current = regime.iloc[-1]
    print(f"\n📍 CURRENT MARKET REGIME:")
    print(f"  Regime:            {current['RegimeName']}")
    print(f"  Momentum Strength: {current['MomentumStrength']:.2f}")
    print(f"  Trend Strength:    {current['TrendStrength']:.2f}%")
    print(f"  HMM Edge:          {current['HMMEdge']:.3f}")
    print(f"  Recommendation:    Trade when HMM Edge > 0.6")
    
    print("\n✅ HMM regime detection complete!")
    return data, momentum, regime


def test_5_composite_edge():
    """Test 5: Composite edge scoring (combines all signals)"""
    print_section("TEST 5: COMPOSITE EDGE SCORING (All Signals Combined)")
    
    print("📊 Loading data and calculating all indicators...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    saf = SurvivalAnalysisFilter(hazard_multiplier=0.1)
    survival = saf.calculate(momentum)
    
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    print("\n🎯 Calculating composite edge scores...")
    edge_system = EdgeScoringSystem()
    edge = edge_system.calculate(data, momentum, survival, regime)
    
    print(f"\n📈 COMPOSITE EDGE RESULTS:")
    print(f"  Mean Edge:        {edge['CompositeEdge'].mean():.3f}")
    print(f"  Edge Range:       {edge['CompositeEdge'].min():.3f} to {edge['CompositeEdge'].max():.3f}")
    print(f"  Std Deviation:    {edge['CompositeEdge'].std():.3f}")
    
    class_counts = edge['EdgeClassification'].value_counts()
    print(f"\n🎯 EDGE CLASSIFICATION:")
    for classification in ['Strong', 'Medium', 'Weak']:
        count = class_counts.get(classification, 0)
        pct = count / len(edge) * 100
        symbol = "🟢" if classification == "Strong" else "🟡" if classification == "Medium" else "🔴"
        print(f"  {symbol} {classification:8s}: {count:4d} bars ({pct:5.1f}%)")
    
    current = edge.iloc[-1]
    decision = edge_system.get_trading_decision(current['CompositeEdge'])
    
    print(f"\n📍 CURRENT TRADING DECISION:")
    print(f"  Composite Edge:       {current['CompositeEdge']:.3f}")
    print(f"  Classification:       {current['EdgeClassification']}")
    print(f"  Decision:             {decision['decision']}")
    print(f"  Confidence:           {decision['confidence']}")
    print(f"  Position Multiplier:  {decision['position_size_multiplier']:.1f}x")
    print(f"  {decision['description']}")
    
    print("\n✅ Composite edge scoring complete!")
    return data, momentum, survival, regime, edge


def test_6_full_backtest():
    """Test 6: Full backtest with edge-based position sizing"""
    print_section("TEST 6: FULL BACKTEST (Your Strategy + Research Enhancements)")
    
    print("📊 Loading data and calculating all indicators...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    saf = SurvivalAnalysisFilter(hazard_multiplier=0.1)
    survival = saf.calculate(momentum)
    
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    edge_system = EdgeScoringSystem()
    edge = edge_system.calculate(data, momentum, survival, regime)
    
    print("\n🔄 Running enhanced backtest...")
    print(f"  Initial Capital:  $10,000")
    print(f"  Base Risk:        1%")
    print(f"  Edge Multiplier:  Based on composite edge score")
    print(f"  Commission:       0.1%")
    print(f"  ATR Stop:         2.0x")
    
    # Calculate ATR
    from indicators.utils import atr
    atr_values = atr(data, 14)
    
    # Run backtest with edge-based sizing
    engine = BacktestEngine(
        initial_capital=10000,
        risk_percent=1.0,
        commission_pct=0.1,
        slippage_ticks=2,
        atr_stop_multiplier=2.0
    )
    
    results = engine.run(data, momentum, atr_values, edge['CompositeEdge'])
    
    print(f"\n📈 ENHANCED RESULTS:")
    engine.print_results(results)
    
    print("\n✅ Full backtest complete!")
    return results


def test_7_comparison():
    """Test 7: Side-by-side comparison"""
    print_section("TEST 7: BASELINE vs ENHANCED COMPARISON")
    
    print("🔄 Running both strategies for comparison...\n")
    
    # Baseline
    print("1️⃣  Running baseline strategy...")
    collector = DataCollector()
    data = collector.fetch_data('SPY', timeframe='1d', period='2y')
    
    strategy = MomentumTrackerStrategy(
        initial_capital=10000,
        momentum_threshold=2.0,
        risk_percent=0.02,
        use_trend_filter=True
    )
    baseline_results = strategy.backtest(data)
    
    # Enhanced
    print("\n2️⃣  Running enhanced strategy with research indicators...")
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    saf = SurvivalAnalysisFilter(hazard_multiplier=0.1)
    survival = saf.calculate(momentum)
    
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    edge_system = EdgeScoringSystem()
    edge = edge_system.calculate(data, momentum, survival, regime)
    
    from indicators.utils import atr
    atr_values = atr(data, 14)
    
    engine = BacktestEngine(
        initial_capital=10000,
        risk_percent=1.0,
        commission_pct=0.1,
        slippage_ticks=2,
        atr_stop_multiplier=2.0
    )
    
    enhanced_results = engine.run(data, momentum, atr_values, edge['CompositeEdge'])
    
    # Comparison
    print("\n" + "="*80)
    print(" " * 25 + "FINAL COMPARISON")
    print("="*80)
    print(f"\n{'Metric':<25} {'Baseline':>20} {'Enhanced':>20} {'Improvement':>12}")
    print("-"*80)
    
    metrics = [
        ('Final Capital', 
         f"${baseline_results['final_capital']:,.2f}", 
         f"${enhanced_results['FinalCapital']:,.2f}",
         f"{((enhanced_results['FinalCapital']/baseline_results['final_capital'])-1)*100:+.1f}%"),
        
        ('Total Return', 
         f"{baseline_results['total_return_pct']:.2f}%", 
         f"{enhanced_results['ReturnPct']:.2f}%",
         f"{enhanced_results['ReturnPct']-baseline_results['total_return_pct']:+.2f}%"),
        
        ('Annual Return', 
         f"{baseline_results['annual_return_pct']:.2f}%", 
         f"{enhanced_results['AnnualReturnPct']:.2f}%",
         f"{enhanced_results['AnnualReturnPct']-baseline_results['annual_return_pct']:+.2f}%"),
        
        ('Win Rate', 
         f"{baseline_results['win_rate']:.1f}%", 
         f"{enhanced_results['WinRate']:.1f}%",
         f"{enhanced_results['WinRate']-baseline_results['win_rate']:+.1f}%"),
        
        ('Sharpe Ratio', 
         f"{baseline_results['sharpe_ratio']:.2f}", 
         f"{enhanced_results['SharpeRatio']:.2f}",
         f"{enhanced_results['SharpeRatio']-baseline_results['sharpe_ratio']:+.2f}"),
        
        ('Max Drawdown', 
         f"{baseline_results['max_drawdown_pct']:.2f}%", 
         f"{enhanced_results['MaxDrawdownPct']:.2f}%",
         f"{enhanced_results['MaxDrawdownPct']-baseline_results['max_drawdown_pct']:+.2f}%"),
        
        ('Total Trades', 
         f"{baseline_results['total_trades']}", 
         f"{enhanced_results['TotalTrades']}",
         f"{enhanced_results['TotalTrades']-baseline_results['total_trades']:+d}"),
    ]
    
    for metric, baseline, enhanced, improvement in metrics:
        print(f"{metric:<25} {baseline:>20} {enhanced:>20} {improvement:>12}")
    
    print("\n✅ Comparison complete!")
    
    return baseline_results, enhanced_results


def run_all_tests():
    """Run all tests"""
    print("\n" + "🎯"*40)
    print(" " * 15 + "STARTING COMPLETE TEST SUITE")
    print("🎯"*40)
    
    try:
        test_1_baseline_strategy()
        test_2_research_momentum()
        test_3_survival_analysis()
        test_4_hmm_regime()
        test_5_composite_edge()
        test_6_full_backtest()
        baseline, enhanced = test_7_comparison()
        
        print_section("🎉 ALL TESTS COMPLETE!")
        
        print("📊 SUMMARY:")
        print(f"  ✅ Test 1: Baseline Strategy")
        print(f"  ✅ Test 2: Research Momentum Tracker")
        print(f"  ✅ Test 3: Survival Analysis Filter")
        print(f"  ✅ Test 4: HMM Regime Detection")
        print(f"  ✅ Test 5: Composite Edge Scoring")
        print(f"  ✅ Test 6: Full Enhanced Backtest")
        print(f"  ✅ Test 7: Baseline vs Enhanced Comparison")
        
        print(f"\n🚀 KEY FINDING:")
        improvement = ((enhanced['FinalCapital']/baseline['final_capital'])-1)*100
        print(f"  Enhanced strategy improved by {improvement:+.1f}%")
        print(f"  From ${baseline['final_capital']:,.2f} to ${enhanced['FinalCapital']:,.2f}")
        
        print(f"\n✅ All tests passed successfully!")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
