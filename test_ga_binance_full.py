"""
FULL TEST - Robust GA with Binance Data
60 days of data, all timeframes, proper generation count
Expected: 15-20 minutes
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

from binance_data_provider import BinanceDataProvider
from ga_mtf_unrestricted_robust import run_robust_mtf_ga

print("=" * 80)
print("  🚀 FULL TEST - ROBUST GA WITH BINANCE")
print("  💰 NO API KEYS NEEDED")
print("  📊 60 Days + All Timeframes")
print("=" * 80)

# Download Binance data
provider = BinanceDataProvider()

symbol = 'BTC/USDT'
end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # 2 months of data

print(f"\n📊 Symbol: {symbol}")
print(f"   Period: {start_date.date()} to {end_date.date()}")
print(f"   Duration: 60 days")

mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)

# Keep timeframes with sufficient data
min_bars = 100
mtf_data = {k: v for k, v in mtf_data.items() if len(v) > min_bars}

if len(mtf_data) < 3:
    print(f"❌ Insufficient timeframes (need 3+, got {len(mtf_data)})")
    sys.exit(1)

print(f"\n✅ Using {len(mtf_data)} timeframes:")
for tf, df in mtf_data.items():
    print(f"   {tf}: {len(df)} bars")
    print(f"      Date: {df['timestamp'].iloc[0].date()} to {df['timestamp'].iloc[-1].date()}")
    print(f"      Price: ${df['close'].min():.0f} - ${df['close'].max():.0f}")

# Run GA with proper parameters
print("\n🧬 Running Robust GA...")
print("   Population: 30")
print("   Generations: 30")
print("   Complexity penalty: 0.3")
print("   Train/Val split: 80/20")
print("   Expected time: 15-20 minutes")
print("\n⏰ Starting now...\n")

try:
    _, best_gene, best_results, validation_metrics = run_robust_mtf_ga(
        mtf_data,
        population_size=30,
        generations=30,
        elite_size=5,
        complexity_weight=0.3,
        use_walk_forward=False,
        use_validation_split=True,
        validation_ratio=0.2
    )
    
    print(f"\n{'='*80}")
    print("✅ FULL TEST COMPLETE!")
    print(f"{'='*80}")
    
    print(f"\n📊 Performance:")
    print(f"   Train Return: {best_results['return']:.2f}%")
    print(f"   Train Trades: {best_results['trades']}")
    print(f"   Win Rate: {best_results.get('win_rate', 0):.1f}%")
    
    if 'val_return' in validation_metrics:
        print(f"\n📉 Validation:")
        print(f"   Val Return: {validation_metrics['val_return']:.2f}%")
        print(f"   Overfitting Gap: {validation_metrics.get('overfitting_gap', 0):.2f}%")
        gap_pct = validation_metrics.get('overfitting_pct', 0)
        if gap_pct < 25:
            print(f"   Status: ✅ Good generalization")
        elif gap_pct < 40:
            print(f"   Status: ⚠️  Moderate overfitting")
        else:
            print(f"   Status: 🚨 High overfitting")
    
    print(f"\n🧪 Robustness:")
    print(f"   Complexity: {validation_metrics.get('complexity', 0):.1f}/100")
    mc = validation_metrics.get('monte_carlo', {})
    print(f"   Monte Carlo: {'✅ Robust' if mc.get('is_robust') else '🚨 May be luck'}")
    sens = validation_metrics.get('sensitivity', {})
    print(f"   Sensitivity: {'✅ Robust' if sens.get('is_robust') else '🚨 Fragile'}")
    
    print(f"\n💾 Results saved to: best_mtf_unrestricted_robust.json")
    
    # Strategy details
    print(f"\n🎯 Strategy Details:")
    print(f"   Primary TF: {best_gene.primary_timeframe}")
    print(f"   Confirm TF: {best_gene.confirm_timeframe} ({'Used' if best_gene.use_confirm else 'Not used'})")
    print(f"   Filter TF: {best_gene.filter_timeframe} ({'Used' if best_gene.use_filter else 'Not used'})")
    print(f"   Entry Logic: {best_gene.entry_logic}")
    print(f"   Stop Loss: {best_gene.stop_loss_pct:.1f}%")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}%")
    
    print(f"\n🎉 Binance data works perfectly!")
    print(f"   Symbol: {symbol}")
    print(f"   Ready for production runs")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
