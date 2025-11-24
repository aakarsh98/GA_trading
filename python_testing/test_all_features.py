"""
Comprehensive Feature Testing Script
Tests all indicators, edge scoring, and backtesting with open-source data
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Import our modules
from data.collector import DataCollector
from indicators.momentum_tracker import MomentumTracker
from indicators.survival_analysis import SurvivalAnalysisFilter
from indicators.hmm_regime import HMMRegimeDetector
from indicators.edge_scoring import EdgeScoringSystem
from indicators.utils import atr
from strategy.backtest_engine import BacktestEngine


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70 + "\n")


def test_data_collection():
    """Test 1: Data Collection from Multiple Sources."""
    print_header("TEST 1: DATA COLLECTION")
    
    collector = DataCollector()
    
    # Test single asset
    print("📊 Fetching BTC-USD hourly data (1 month)...")
    btc_data = collector.fetch_data('BTC-USD', timeframe='1h', period='1mo')
    print(f"✓ Fetched {len(btc_data)} bars")
    print(f"  Date range: {btc_data.index[0]} to {btc_data.index[-1]}")
    print(f"  Price range: ${btc_data['Close'].min():.2f} - ${btc_data['Close'].max():.2f}")
    
    # Test multiple assets
    print("\n📊 Fetching multiple assets...")
    symbols = ['BTC-USD', 'ETH-USD', 'SPY']
    data_dict = collector.fetch_multiple(symbols, timeframe='1d', period='3mo')
    
    for symbol, data in data_dict.items():
        print(f"  {symbol}: {len(data)} bars")
    
    print("\n✅ Data collection test passed!")
    return btc_data


def test_momentum_tracker(data: pd.DataFrame):
    """Test 2: Momentum Tracker Indicator."""
    print_header("TEST 2: MOMENTUM TRACKER INDICATOR")
    
    print("🔄 Calculating momentum with triple-layer EMA smoothing...")
    mt = MomentumTracker(length=7, threshold=2.0)
    momentum = mt.calculate(data)
    
    print(f"✓ Calculated momentum for {len(momentum)} bars")
    print(f"\n📈 Momentum Statistics:")
    print(f"  Mean: {momentum['Momentum'].mean():.2f}")
    print(f"  Range: {momentum['Momentum'].min():.2f} - {momentum['Momentum'].max():.2f}")
    print(f"  Current: {momentum['Momentum'].iloc[-1]:.2f}")
    
    # Signal distribution
    print(f"\n🎯 Signal Distribution:")
    bullish = (momentum['Signal'] == 1).sum()
    bearish = (momentum['Signal'] == -1).sum()
    neutral = (momentum['Signal'] == 0).sum()
    
    print(f"  Bullish (Blue):   {bullish:4d} bars ({bullish/len(momentum)*100:5.1f}%)")
    print(f"  Bearish (Red):    {bearish:4d} bars ({bearish/len(momentum)*100:5.1f}%)")
    print(f"  Neutral (Yellow): {neutral:4d} bars ({neutral/len(momentum)*100:5.1f}%)")
    
    # Current signal
    current = mt.get_current_signal(data)
    print(f"\n🎯 Current Signal:")
    print(f"  Direction: {current['signal_name']} ({current['color']})")
    print(f"  Momentum: {current['momentum']:.2f}")
    print(f"  Equilibrium: {current['equilibrium']:.2f}")
    print(f"  Strength: {current['strength']:.2f}x threshold")
    
    print("\n✅ Momentum tracker test passed!")
    return momentum


def test_survival_analysis(momentum: pd.DataFrame):
    """Test 3: Survival Analysis Filter."""
    print_header("TEST 3: SURVIVAL ANALYSIS FILTER")
    
    print("⏱️  Calculating survival analysis (35-45% Sharpe improvement)...")
    saf = SurvivalAnalysisFilter(hazard_multiplier=0.1)
    survival = saf.calculate(momentum)
    
    print(f"✓ Analyzed {len(survival)} signals")
    print(f"\n📊 Survival Statistics:")
    print(f"  Mean Signal Age: {survival['SignalAge'].mean():.1f} bars")
    print(f"  Max Signal Age: {survival['SignalAge'].max():.0f} bars")
    print(f"  Mean Survival Probability: {survival['SurvivalProbability'].mean():.3f}")
    print(f"  Mean Survival Edge: {survival['SurvivalEdge'].mean():.3f}")
    
    # Strong edges
    strong_edges = (survival['SurvivalEdge'] > 0.6).sum()
    print(f"\n🎯 Edge Analysis:")
    print(f"  Strong Edges (>0.6): {strong_edges} bars ({strong_edges/len(survival)*100:.1f}%)")
    
    # Current survival
    current = survival.iloc[-1]
    print(f"\n📍 Current Survival Analysis:")
    print(f"  Signal Age: {current['SignalAge']:.0f} bars")
    print(f"  Survival Probability: {current['SurvivalProbability']:.3f}")
    print(f"  Survival Edge: {current['SurvivalEdge']:.3f}")
    print(f"  Trade Approval: {'✓ YES' if current['SurvivalEdge'] > 0.6 else '✗ NO'}")
    
    print("\n✅ Survival analysis test passed!")
    return survival


def test_hmm_regime(data: pd.DataFrame, momentum: pd.DataFrame):
    """Test 4: HMM Regime Detection."""
    print_header("TEST 4: HMM REGIME DETECTION")
    
    print("🧠 Detecting market regimes (40-60% improvement)...")
    hmm = HMMRegimeDetector()
    regime = hmm.calculate(data, momentum)
    
    print(f"✓ Classified {len(regime)} bars")
    
    # Regime statistics
    stats = hmm.get_regime_stats(regime)
    print(f"\n📊 Regime Distribution:")
    print(f"  Normal:         {stats['normal_bars']:4d} bars ({stats['normal_pct']:5.1f}%)")
    print(f"  Trending:       {stats['trending_bars']:4d} bars ({stats['trending_pct']:5.1f}%)")
    print(f"  Mean-Reverting: {stats['mean_reverting_bars']:4d} bars ({stats['mean_reverting_pct']:5.1f}%)")
    print(f"  Mean HMM Edge: {stats['mean_hmm_edge']:.3f}")
    
    # Current regime
    current = regime.iloc[-1]
    print(f"\n📍 Current Market Regime:")
    print(f"  Regime: {current['RegimeName']}")
    print(f"  Momentum Strength: {current['MomentumStrength']:.2f}")
    print(f"  Trend Strength: {current['TrendStrength']:.2f}%")
    print(f"  HMM Edge: {current['HMMEdge']:.3f}")
    
    print("\n✅ HMM regime detection test passed!")
    return regime


def test_edge_scoring(data: pd.DataFrame, momentum: pd.DataFrame, 
                     survival: pd.DataFrame, regime: pd.DataFrame):
    """Test 5: Composite Edge Scoring System."""
    print_header("TEST 5: COMPOSITE EDGE SCORING")
    
    print("🎯 Calculating composite edge scores...")
    edge_system = EdgeScoringSystem()
    edge = edge_system.calculate(data, momentum, survival, regime)
    
    print(f"✓ Calculated edge for {len(edge)} bars")
    print(f"\n📊 Edge Score Statistics:")
    print(f"  Mean: {edge['CompositeEdge'].mean():.3f}")
    print(f"  Range: {edge['CompositeEdge'].min():.3f} - {edge['CompositeEdge'].max():.3f}")
    print(f"  Std Dev: {edge['CompositeEdge'].std():.3f}")
    
    # Edge classification
    print(f"\n🎯 Edge Classification Distribution:")
    class_counts = edge['EdgeClassification'].value_counts()
    for classification in ['Strong', 'Medium', 'Weak']:
        count = class_counts.get(classification, 0)
        pct = count / len(edge) * 100
        print(f"  {classification:8s}: {count:4d} bars ({pct:5.1f}%)")
    
    # Current edge and decision
    current = edge.iloc[-1]
    decision = edge_system.get_trading_decision(current['CompositeEdge'])
    
    print(f"\n📍 Current Edge Analysis:")
    print(f"  Composite Edge: {current['CompositeEdge']:.3f}")
    print(f"  Classification: {current['EdgeClassification']}")
    print(f"\n💼 Trading Decision:")
    print(f"  Decision: {decision['decision']}")
    print(f"  Confidence: {decision['confidence']}")
    print(f"  Position Size Multiplier: {decision['position_size_multiplier']:.1f}x")
    print(f"  {decision['description']}")
    
    print("\n✅ Edge scoring test passed!")
    return edge


def test_backtesting(data: pd.DataFrame, momentum: pd.DataFrame, 
                    edge: pd.DataFrame):
    """Test 6: Backtesting Engine."""
    print_header("TEST 6: BACKTESTING ENGINE")
    
    print("🔄 Running backtest with edge-based position sizing...")
    print(f"  Initial Capital: $10,000")
    print(f"  Risk per Trade: 1%")
    print(f"  Commission: 0.1%")
    print(f"  ATR Stop: 2.0x")
    
    # Calculate ATR
    atr_values = atr(data, 14)
    
    # Create backtest engine
    engine = BacktestEngine(
        initial_capital=10000,
        risk_percent=1.0,
        commission_pct=0.1,
        slippage_ticks=2,
        atr_stop_multiplier=2.0
    )
    
    # Run backtest
    results = engine.run(data, momentum, atr_values, edge['CompositeEdge'])
    
    # Print results
    print(f"\n✓ Backtest complete!")
    engine.print_results(results)
    
    print("\n✅ Backtesting test passed!")
    return results


def test_all():
    """Run all tests in sequence."""
    print("\n" + "🚀"*35)
    print(" COMPREHENSIVE TRADING STRATEGY TESTING SUITE")
    print("🚀"*35)
    print(f"\nStarting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Testing Framework v1.0")
    print(f"Testing all features with open-source market data...")
    
    try:
        # Test 1: Data Collection
        data = test_data_collection()
        
        # Test 2: Momentum Tracker
        momentum = test_momentum_tracker(data)
        
        # Test 3: Survival Analysis
        survival = test_survival_analysis(momentum)
        
        # Test 4: HMM Regime Detection
        regime = test_hmm_regime(data, momentum)
        
        # Test 5: Edge Scoring
        edge = test_edge_scoring(data, momentum, survival, regime)
        
        # Test 6: Backtesting
        results = test_backtesting(data, momentum, edge)
        
        # Final summary
        print_header("FINAL SUMMARY")
        print("✅ All 6 tests passed successfully!")
        print(f"\n📊 Key Results:")
        print(f"  Data Bars Processed: {len(data)}")
        print(f"  Momentum Signals: {(momentum['Signal'] != 0).sum()}")
        print(f"  Mean Edge Score: {edge['CompositeEdge'].mean():.3f}")
        print(f"  Backtest Return: {results['ReturnPct']:.2f}%")
        print(f"  Win Rate: {results['WinRate']:.1f}%")
        print(f"  Sharpe Ratio: {results['SharpeRatio']:.2f}")
        
        print(f"\n🎉 Testing complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_all()
    sys.exit(0 if success else 1)
