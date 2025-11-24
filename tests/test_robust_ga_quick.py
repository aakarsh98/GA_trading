"""
Quick test of robust GA with minimal parameters
Fast execution for testing (5-10 minutes)
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

from ga_mtf_unrestricted_robust import (
    MultiTimeframeDataProvider,
    run_robust_mtf_ga
)

print("=" * 80)
print("  🧪 QUICK TEST - ROBUST UNRESTRICTED GA")
print("  ⚡ Reduced parameters for fast testing")
print("=" * 80)

# Download data
provider = MultiTimeframeDataProvider()

symbol = 'SPY'
end_date = datetime.now()
start_date = end_date - timedelta(days=60)  # Only 2 months

print(f"\n📥 Downloading data for {symbol}...")
print(f"   Period: {start_date.date()} to {end_date.date()}")
print(f"   Timeframes: 15min, 1h, 4h, 1d only (skipping 1min, 5min for speed)")

# Download only key timeframes
mtf_data = {}
for tf in ['15min', '1hour', '4hour', '1day']:
    try:
        data = provider.download_multi_timeframe(symbol, start_date, end_date)
        # Keep only these timeframes
        if tf in data:
            mtf_data[tf] = data[tf]
    except:
        pass

# Use first download that worked
if not mtf_data:
    mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)

if len(mtf_data) < 2:
    print("❌ Insufficient data. Exiting.")
    sys.exit(1)

print(f"\n✅ Downloaded {len(mtf_data)} timeframes")
for tf_name, tf_df in mtf_data.items():
    print(f"   {tf_name}: {len(tf_df)} bars")

# Run with minimal parameters for speed
print("\n🧬 Running GA with reduced parameters...")
print("   Population: 20 (instead of 50)")
print("   Generations: 20 (instead of 50)")
print("   Expected time: 5-10 minutes")

_, best_gene, best_results, validation_metrics = run_robust_mtf_ga(
    mtf_data,
    population_size=20,      # Small for quick test
    generations=20,          # Few generations
    elite_size=3,
    complexity_weight=0.3,
    use_walk_forward=False,
    use_validation_split=True,
    validation_ratio=0.2
)

print(f"\n{'='*80}")
print("✅ QUICK TEST COMPLETE!")
print(f"{'='*80}")
print(f"\nTrain Return: {best_results['return']:.2f}%")
print(f"Validation Gap: {validation_metrics.get('overfitting_gap', 0):.2f}%")
print(f"Complexity: {validation_metrics.get('complexity', 0):.1f}/100")
print(f"Monte Carlo Robust: {validation_metrics.get('monte_carlo', {}).get('is_robust', False)}")

print("\n💾 Results saved to: best_mtf_unrestricted_robust.json")
print("\n✅ System is working! Ready for full run.")
