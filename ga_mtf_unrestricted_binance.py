"""
UNRESTRICTED MULTI-TIMEFRAME GA - BINANCE VERSION
Uses Binance data via ccxt (NO API KEYS NEEDED)
All anti-overfitting features included
"""
import sys
sys.path.insert(0, '/Users/aakarshraj/GG_ Script')

# Use Binance data provider instead of Alpaca
from binance_data_provider import BinanceDataProvider as DataProvider

# Import everything else from robust version
from ga_mtf_unrestricted_robust import (
    run_robust_mtf_ga,
    calculate_robust_fitness,
    MTFUnrestrictedGene,
    backtest_mtf_strategy,
    create_random_mtf_gene,
    mutate_mtf_gene,
    crossover_mtf_genes
)

import json
from datetime import datetime, timedelta

print("=" * 80)
print("  🛡️  ROBUST UNRESTRICTED GA - BINANCE DATA")
print("  💰 NO API KEYS NEEDED")
print("  ✅ All Anti-Overfitting Features")
print("  📊 Crypto: BTC, ETH, SOL, XRP, etc.")
print("=" * 80)

if __name__ == '__main__':
    # Configuration - PRODUCTION PARAMETERS
    SYMBOL = 'BTC/USDT'  # Change to 'ETH/USDT', 'SOL/USDT', etc.
    LOOKBACK_DAYS = 90   # 3 months for better pattern discovery
    POPULATION_SIZE = 100  # Large population for thorough search
    GENERATIONS = 100      # Many generations for convergence
    
    print(f"\n📊 Configuration:")
    print(f"   Symbol: {SYMBOL}")
    print(f"   Lookback: {LOOKBACK_DAYS} days")
    print(f"   Population: {POPULATION_SIZE}")
    print(f"   Generations: {GENERATIONS}")
    
    # Download data
    provider = DataProvider()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    
    print(f"\n📥 Downloading data...")
    mtf_data = provider.download_multi_timeframe(SYMBOL, start_date, end_date)
    
    # Keep timeframes with sufficient data
    # Skip 1-minute (too noisy) and keep meaningful timeframes
    useful_tfs = ['5m', '15m', '1h', '4h', '1d']
    mtf_data = {k: v for k, v in mtf_data.items() if k in useful_tfs and len(v) > 200}
    
    if len(mtf_data) < 3:
        print(f"❌ Need at least 3 timeframes (got {len(mtf_data)})")
        sys.exit(1)
    
    print(f"\n✅ Using {len(mtf_data)} timeframes")
    
    # Print data summary
    print(f"\n📊 Data Summary:")
    for tf, df in mtf_data.items():
        print(f"   {tf:>4}: {len(df):>5} bars | {df['timestamp'].iloc[0].date()} to {df['timestamp'].iloc[-1].date()}")
        print(f"        Price: ${df['close'].min():.0f} - ${df['close'].max():.0f}")
    
    print(f"\n🧬 Starting Production GA...")
    print(f"   This will take approximately 2-3 hours")
    print(f"   Progress will be shown every generation")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run GA
    _, best_gene, best_results, validation_metrics = run_robust_mtf_ga(
        mtf_data,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        elite_size=10,  # Keep more elite for large population
        complexity_weight=0.3,
        use_validation_split=True,
        validation_ratio=0.2
    )
    
    # Save results
    print(f"\n💾 Saving results...")
    
    result_dict = {
        'symbol': SYMBOL,
        'performance': {
            'train': best_results,
            'validation': validation_metrics
        },
        'gene': {
            'primary_timeframe': best_gene.primary_timeframe,
            'confirm_timeframe': best_gene.confirm_timeframe,
            'entry_logic': best_gene.entry_logic,
            'stop_loss_pct': best_gene.stop_loss_pct,
            'take_profit_pct': best_gene.take_profit_pct,
        },
        'robustness': {
            'complexity': validation_metrics.get('complexity', 0),
            'overfitting_gap': validation_metrics.get('overfitting_gap', 0),
            'monte_carlo_robust': validation_metrics.get('monte_carlo', {}).get('is_robust', False),
            'parameter_robust': validation_metrics.get('sensitivity', {}).get('is_robust', False),
        },
        'timestamp': datetime.now().isoformat(),
        'data_source': 'Binance via ccxt (free)'
    }
    
    filename = f"best_{SYMBOL.replace('/', '_')}_strategy.json"
    with open(filename, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    print(f"✅ Saved to: {filename}")
    
    print(f"\n{'='*80}")
    print("✅ COMPLETE!")
    print(f"{'='*80}")
