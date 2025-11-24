"""
Test GA on multiple cryptocurrencies
BTC, ETH, SOL - find which works best
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

from binance_data_provider import BinanceDataProvider
from ga_mtf_unrestricted_robust import run_robust_mtf_ga

print("=" * 80)
print("  🪙 MULTI-CRYPTO GA TEST")
print("  💰 BTC + ETH + SOL")
print("  ⚡ Quick params (30 min total)")
print("=" * 80)

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
LOOKBACK_DAYS = 30
POP_SIZE = 20
GENERATIONS = 20

provider = BinanceDataProvider()
end_date = datetime.now()
start_date = end_date - timedelta(days=LOOKBACK_DAYS)

results = {}

for symbol in SYMBOLS:
    print(f"\n{'='*80}")
    print(f"  Testing: {symbol}")
    print(f"{'='*80}")
    
    try:
        # Download data
        mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)
        mtf_data = {k: v for k, v in mtf_data.items() if len(v) > 100}
        
        if len(mtf_data) < 3:
            print(f"❌ {symbol}: Insufficient timeframes")
            results[symbol] = {'error': 'insufficient_data'}
            continue
        
        print(f"✅ {len(mtf_data)} timeframes")
        
        # Run GA
        _, best_gene, best_results, val = run_robust_mtf_ga(
            mtf_data,
            population_size=POP_SIZE,
            generations=GENERATIONS,
            complexity_weight=0.3,
            use_validation_split=True
        )
        
        results[symbol] = {
            'train_return': best_results['return'],
            'train_trades': best_results['trades'],
            'val_return': val.get('val_return', 0),
            'overfitting_gap': val.get('overfitting_gap', 0),
            'complexity': val.get('complexity', 0),
            'monte_carlo_robust': val.get('monte_carlo', {}).get('is_robust', False),
            'primary_tf': best_gene.primary_timeframe,
            'confirm_tf': best_gene.confirm_timeframe
        }
        
        print(f"\n✅ {symbol} Results:")
        print(f"   Train: {best_results['return']:.2f}% ({best_results['trades']} trades)")
        print(f"   Val: {val.get('val_return', 0):.2f}%")
        print(f"   Gap: {val.get('overfitting_gap', 0):.2f}%")
        
    except Exception as e:
        print(f"❌ {symbol}: {e}")
        results[symbol] = {'error': str(e)}

# Final comparison
print(f"\n{'='*80}")
print("  📊 FINAL COMPARISON")
print(f"{'='*80}")

for symbol, res in results.items():
    if 'error' in res:
        print(f"\n{symbol}: ❌ {res['error']}")
    else:
        print(f"\n{symbol}:")
        print(f"   Train: {res['train_return']:.2f}% ({res['train_trades']} trades)")
        print(f"   Val: {res['val_return']:.2f}%")
        print(f"   Gap: {res['overfitting_gap']:.2f}%")
        print(f"   Robust: {'✅' if res['monte_carlo_robust'] else '❌'}")

# Determine best
valid_results = {k: v for k, v in results.items() if 'error' not in v}

if valid_results:
    best_symbol = max(valid_results.items(), key=lambda x: x[1]['val_return'])
    print(f"\n🏆 WINNER: {best_symbol[0]}")
    print(f"   Validation Return: {best_symbol[1]['val_return']:.2f}%")
else:
    print(f"\n❌ No successful results")

print(f"\n{'='*80}")
print("✅ MULTI-CRYPTO TEST COMPLETE!")
print(f"{'='*80}")

# Save comparison
import json
with open('multi_crypto_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n💾 Saved to: multi_crypto_comparison.json")
