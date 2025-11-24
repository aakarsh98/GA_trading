"""
Test YOUR Momentum Tracker Strategy with Real Market Data
This tests ONLY your strategy, not the research strategies
"""
import sys
sys.path.append('.')

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from momentum_tracker_strategy import MomentumTrackerStrategy


def download_data(symbol='SPY', days=730):
    """Download real market data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"📥 Downloading {symbol} data from {start_date.date()} to {end_date.date()}...")
    data = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False)
    
    # Standardize column names
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    print(f"✅ Downloaded {len(data)} bars\n")
    return data


def test_momentum_strategy(data, symbol='SPY', show_details=True):
    """Test YOUR momentum tracker strategy"""
    print("=" * 80)
    print(f"🎯 Testing YOUR Momentum Tracker Strategy on {symbol}")
    print("=" * 80)
    
    print(f"\n📊 Data Info:")
    print(f"   Bars: {len(data)}")
    print(f"   Period: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"   Price Range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
    
    # Create strategy
    strategy = MomentumTrackerStrategy(
        initial_capital=10000,
        momentum_threshold=2.0,       # From your Pine Script
        trend_length=20,              # From your Pine Script
        risk_percent=0.01,            # 1% risk per trade
        atr_multiplier=2.0,           # From your Pine Script
        atr_length=14,                # From your Pine Script
        use_trend_filter=True,        # From your Pine Script
        use_take_profit=True,         # From your Pine Script
        take_profit_ratio=2.0         # From your Pine Script
    )
    
    print(f"\n⚙️  Strategy Parameters:")
    print(f"   Momentum Threshold: {strategy.momentum_threshold}")
    print(f"   Trend MA Length: {strategy.trend_length}")
    print(f"   Risk Per Trade: {strategy.risk_percent * 100}%")
    print(f"   ATR Multiplier: {strategy.atr_multiplier}")
    print(f"   Take Profit Ratio: {strategy.take_profit_ratio}:1")
    
    # Run backtest
    print(f"\n🔄 Running backtest...")
    results = strategy.backtest(data)
    
    # Display results
    print(f"\n" + "=" * 80)
    print("📈 BACKTEST RESULTS - YOUR MOMENTUM TRACKER STRATEGY")
    print("=" * 80)
    
    print(f"\n💰 Performance Metrics:")
    print(f"   Initial Capital:     ${strategy.initial_capital:,.2f}")
    print(f"   Final Capital:       ${results['final_capital']:,.2f}")
    print(f"   Net Profit:          ${results['net_profit']:,.2f}")
    print(f"   Return:              {results['return_pct']:.2f}%")
    
    print(f"\n📊 Trade Statistics:")
    print(f"   Total Trades:        {results['total_trades']}")
    print(f"   Winning Trades:      {results['winning_trades']}")
    print(f"   Losing Trades:       {results['losing_trades']}")
    print(f"   Win Rate:            {results['win_rate']:.2f}%")
    
    print(f"\n💵 Profit/Loss Analysis:")
    print(f"   Average Win:         ${results['avg_win']:.2f}")
    print(f"   Average Loss:        ${results['avg_loss']:.2f}")
    print(f"   Win/Loss Ratio:      {abs(results['avg_win'] / results['avg_loss']):.2f}:1" if results['avg_loss'] != 0 else "   Win/Loss Ratio:      N/A")
    
    print(f"\n📉 Risk Metrics:")
    print(f"   Sharpe Ratio:        {results['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown:        ${results['max_drawdown']:.2f}")
    print(f"   Max Drawdown %:      {results['max_drawdown_pct']:.2f}%")
    
    # Show some example trades
    if show_details and results['total_trades'] > 0:
        print(f"\n" + "=" * 80)
        print("📝 Sample Trades (First 10):")
        print("=" * 80)
        
        completed_trades = [t for t in strategy.trades if t.exit_time is not None]
        
        for i, trade in enumerate(completed_trades[:10]):
            profit_loss = "PROFIT" if trade.pnl > 0 else "LOSS"
            print(f"\n   Trade #{i+1} ({trade.position_type}):")
            print(f"      Entry:  {trade.entry_time.date()} @ ${trade.entry_price:.2f}")
            print(f"      Exit:   {trade.exit_time.date()} @ ${trade.exit_price:.2f}")
            print(f"      P&L:    ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%) - {profit_loss}")
    
    print("\n" + "=" * 80)
    
    return results


def test_multiple_assets():
    """Test YOUR strategy on multiple assets"""
    print("\n" + "=" * 80)
    print("🌐 Testing YOUR Momentum Tracker on Multiple Assets")
    print("=" * 80)
    
    assets = {
        'SPY': 'S&P 500',
        'QQQ': 'Nasdaq 100',
        'AAPL': 'Apple',
        'TSLA': 'Tesla'
    }
    
    results_summary = []
    
    for symbol, name in assets.items():
        try:
            print(f"\n{'─' * 80}")
            data = download_data(symbol, days=730)
            results = test_momentum_strategy(data, symbol, show_details=False)
            
            results_summary.append({
                'Asset': f"{symbol} ({name})",
                'Trades': results['total_trades'],
                'Win Rate': f"{results['win_rate']:.1f}%",
                'Return': f"{results['return_pct']:.2f}%",
                'Sharpe': f"{results['sharpe_ratio']:.2f}",
                'Max DD': f"{results['max_drawdown_pct']:.2f}%"
            })
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
    
    # Summary table
    print("\n" + "=" * 80)
    print("📊 SUMMARY - YOUR MOMENTUM TRACKER ACROSS ASSETS")
    print("=" * 80)
    
    import pandas as pd
    df = pd.DataFrame(results_summary)
    print("\n" + df.to_string(index=False))
    
    print("\n" + "=" * 80)


def main():
    """Main test function"""
    print("\n" + "🎯" * 40)
    print(" " * 20 + "YOUR MOMENTUM TRACKER STRATEGY TEST")
    print("🎯" * 40)
    
    # Test on SPY first
    print("\n📍 Test 1: Detailed test on SPY")
    spy_data = download_data('SPY', days=730)
    spy_results = test_momentum_strategy(spy_data, 'SPY', show_details=True)
    
    # Ask if want to test more
    print("\n" + "─" * 80)
    test_more = input("\n❓ Test on more assets? (y/n): ").strip().lower()
    
    if test_more == 'y':
        test_multiple_assets()
    
    print("\n" + "=" * 80)
    print("✅ Testing Complete!")
    print("=" * 80)
    
    print("\n💡 Key Takeaways:")
    print(f"   • Strategy traded {spy_results['total_trades']} times on SPY")
    print(f"   • Win rate: {spy_results['win_rate']:.1f}%")
    print(f"   • Total return: {spy_results['return_pct']:.2f}%")
    print(f"   • Sharpe ratio: {spy_results['sharpe_ratio']:.2f}")
    
    if spy_results['sharpe_ratio'] > 1.0:
        print("\n   ✅ Good risk-adjusted returns!")
    elif spy_results['sharpe_ratio'] > 0:
        print("\n   ⚠️  Positive but could be improved")
    else:
        print("\n   ❌ Strategy needs optimization")
    
    print("\n📁 Your strategy code: momentum_tracker_strategy.py")
    print("📁 This test script: test_your_momentum_strategy.py")
    print("\n")


if __name__ == "__main__":
    main()
