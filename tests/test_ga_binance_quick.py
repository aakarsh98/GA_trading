"""
QUICK TEST - Robust GA with Binance Data
NO API KEYS NEEDED!
Fast test: 20 pop × 20 gen = 5-10 minutes
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

from binance_data_provider import BinanceDataProvider
from ga_mtf_unrestricted_robust import run_robust_mtf_ga

print("=" * 80)
print("  🧪 QUICK TEST - ROBUST GA WITH BINANCE")
print("  💰 NO API KEYS NEEDED")
print("  ⚡ Fast Parameters (5-10 minutes)")
print("=" * 80)

# Download Binance data
provider = BinanceDataProvider()

symbol = 'BTC/USDT'  # Bitcoin
end_date = datetime.now()
start_date = end_date - timedelta(days=14)  # Last 2 weeks only

print(f"\n📊 Symbol: {symbol}")
print(f"   Period: {start_date.date()} to {end_date.date()}")

mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)

# Keep only key timeframes for speed
keep_tfs = ['15m', '1h', '4h', '1d']
mtf_data = {k: v for k, v in mtf_data.items() if k in keep_tfs and len(v) > 50}

if len(mtf_data) < 2:
    print("❌ Insufficient data")
    sys.exit(1)

print(f"\n✅ Using {len(mtf_data)} timeframes:")
for tf, df in mtf_data.items():
    print(f"   {tf}: {len(df)} bars")

# Run GA with minimal parameters
print("\n🧬 Running Robust GA...")
print("   Population: 20")
print("   Generations: 20")
print("   Expected: 5-10 minutes")

_, best_gene, best_results, validation_metrics = run_robust_mtf_ga(
    mtf_data,
    population_size=20,
    generations=20,
    elite_size=3,
    complexity_weight=0.3,
    use_validation_split=True,
    validation_ratio=0.2
)

print(f"\n{'='*80}")
print("✅ TEST COMPLETE!")
print(f"{'='*80}")
print(f"\nTrain Return: {best_results['return']:.2f}%")
print(f"Validation Return: {validation_metrics.get('val_return', 0):.2f}%")
print(f"Overfitting Gap: {validation_metrics.get('overfitting_gap', 0):.2f}%")
print(f"Complexity: {validation_metrics.get('complexity', 0):.1f}/100")
print(f"Monte Carlo Robust: {validation_metrics.get('monte_carlo', {}).get('is_robust', False)}")
print(f"Parameter Robust: {validation_metrics.get('sensitivity', {}).get('is_robust', False)}")

print("\n💾 Results saved to: best_mtf_unrestricted_robust.json")
print("\n🎉 Binance data works perfectly!")
print("   Ready for full runs on BTC, ETH, SOL, etc.")
