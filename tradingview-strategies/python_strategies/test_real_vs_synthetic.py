"""
Compare Strategy Performance: Real Data vs Synthetic Data
Shows why real market data matters
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

import yfinance as yf
import pandas as pd
from strategies.statistical_arbitrage import StatisticalArbitrage
from strategies.multi_timeframe_attention import MultiTimeframeAttention
from utils.data_generator import load_sample_data


def download_real_data(symbol='SPY', days=730):
    """Download real market data"""
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}...")
    data = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False)
    
    # Standardize column names
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    print(f"✅ Downloaded {len(data)} bars of real data")
    return data


def test_strategy(strategy_class, data, data_type):
    """Test a strategy and return results"""
    strategy = strategy_class(initial_capital=10000)
    results = strategy.backtest(data)
    
    print(f"\n  {data_type} Data Results:")
    print(f"    Total Trades: {results['total_trades']}")
    print(f"    Win Rate: {results['win_rate']:.1f}%")
    print(f"    Net Return: {results['net_profit_pct']:.2f}%")
    print(f"    Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"    Max Drawdown: {results['max_drawdown_pct']:.2f}%")
    
    return results


def main():
    print("=" * 70)
    print(" 📊 REAL DATA vs SYNTHETIC DATA COMPARISON")
    print("=" * 70)
    
    # ========================================
    # Load Data
    # ========================================
    print("\n1️⃣  Loading Data...")
    print("-" * 70)
    
    # Synthetic data
    print("\n📉 Synthetic Data (what we used before):")
    synthetic_data = load_sample_data('mixed', 730)
    print(f"   Generated {len(synthetic_data)} synthetic bars")
    
    # Real data
    print("\n📈 Real Market Data (SPY - S&P 500):")
    try:
        real_data = download_real_data('SPY', days=730)
    except Exception as e:
        print(f"❌ Error downloading real data: {e}")
        print("   Make sure you have internet connection")
        return
    
    # ========================================
    # Test Strategy 1: Statistical Arbitrage
    # ========================================
    print("\n2️⃣  Testing Statistical Arbitrage Strategy")
    print("=" * 70)
    
    print("\n🤖 Statistical Arbitrage (Mean Reversion)")
    synthetic_results_1 = test_strategy(StatisticalArbitrage, synthetic_data, "Synthetic")
    real_results_1 = test_strategy(StatisticalArbitrage, real_data, "Real")
    
    # Compare
    print("\n  📊 Comparison:")
    print(f"    Return Difference: {real_results_1['net_profit_pct'] - synthetic_results_1['net_profit_pct']:.2f}%")
    print(f"    Sharpe Difference: {real_results_1['sharpe_ratio'] - synthetic_results_1['sharpe_ratio']:.2f}")
    
    # ========================================
    # Test Strategy 2: Multi-Timeframe Attention
    # ========================================
    print("\n3️⃣  Testing Multi-Timeframe Attention Strategy")
    print("=" * 70)
    
    print("\n🎯 Multi-Timeframe Attention")
    synthetic_results_2 = test_strategy(MultiTimeframeAttention, synthetic_data, "Synthetic")
    real_results_2 = test_strategy(MultiTimeframeAttention, real_data, "Real")
    
    # Compare
    print("\n  📊 Comparison:")
    print(f"    Return Difference: {real_results_2['net_profit_pct'] - synthetic_results_2['net_profit_pct']:.2f}%")
    print(f"    Sharpe Difference: {real_results_2['sharpe_ratio'] - synthetic_results_2['sharpe_ratio']:.2f}")
    
    # ========================================
    # Summary
    # ========================================
    print("\n4️⃣  Summary")
    print("=" * 70)
    
    print("\n📊 Key Findings:")
    print("\n  Statistical Arbitrage:")
    print(f"    Synthetic: {synthetic_results_1['sharpe_ratio']:.2f} Sharpe, {synthetic_results_1['net_profit_pct']:.2f}% return")
    print(f"    Real Data: {real_results_1['sharpe_ratio']:.2f} Sharpe, {real_results_1['net_profit_pct']:.2f}% return")
    
    print("\n  Multi-Timeframe Attention:")
    print(f"    Synthetic: {synthetic_results_2['sharpe_ratio']:.2f} Sharpe, {synthetic_results_2['net_profit_pct']:.2f}% return")
    print(f"    Real Data: {real_results_2['sharpe_ratio']:.2f} Sharpe, {real_results_2['net_profit_pct']:.2f}% return")
    
    print("\n💡 Conclusions:")
    print("  • Real data shows actual market behavior")
    print("  • Results may differ due to market microstructure")
    print("  • Real data is REQUIRED for production validation")
    print("  • Synthetic data is OK for initial testing only")
    
    print("\n" + "=" * 70)
    print("✅ Comparison Complete!")
    print("=" * 70)
    
    print("\n📝 Next Steps:")
    print("  1. Always validate strategies with real data")
    print("  2. Test on multiple assets (not just SPY)")
    print("  3. Include realistic transaction costs")
    print("  4. Test across different time periods")
    print("  5. Monitor performance with real-time data")


if __name__ == "__main__":
    main()
