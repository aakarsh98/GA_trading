"""
Binance Data Provider using ccxt
NO API KEYS NEEDED for public historical data
Supports all intraday timeframes: 1m, 5m, 15m, 1h, 4h, 1d
"""
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict
import sys

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

class BinanceDataProvider:
    """
    Download multi-timeframe data from Binance using ccxt
    NO API KEYS NEEDED - public data is free!
    """
    
    def __init__(self):
        """Initialize Binance exchange (no keys needed for historical data)"""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'},  # USDT-M futures
        })
        self.exchange.load_markets()
        print("✅ Binance provider initialized (no API keys needed)")
    
    def download_multi_timeframe(self, symbol: str, start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple timeframes
        
        Args:
            symbol: Symbol like 'BTC/USDT', 'ETH/USDT', 'SOL/USDT'
            start: Start date
            end: End date
        
        Returns:
            Dict of {timeframe: dataframe}
        """
        print(f"\n📥 Downloading multi-timeframe data for {symbol}...")
        print(f"   Period: {start.date()} to {end.date()}")
        print(f"   Source: Binance via ccxt (FREE)")
        
        # Timeframes to download
        timeframes = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
        }
        
        data = {}
        
        for tf_name, tf_code in timeframes.items():
            try:
                # Convert dates to milliseconds
                since = int(start.timestamp() * 1000)
                end_ms = int(end.timestamp() * 1000)
                
                # Fetch OHLCV data
                all_candles = []
                current_since = since
                
                while current_since < end_ms:
                    candles = self.exchange.fetch_ohlcv(
                        symbol, 
                        timeframe=tf_code,
                        since=current_since,
                        limit=1000  # Max per request
                    )
                    
                    if not candles:
                        break
                    
                    all_candles.extend(candles)
                    
                    # Move to next batch
                    current_since = candles[-1][0] + 1
                    
                    # Stop if we've passed end date
                    if candles[-1][0] >= end_ms:
                        break
                
                # Convert to DataFrame
                df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Filter to exact date range
                df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
                
                if len(df) == 0:
                    print(f"   ✗ {tf_name}: No data in range")
                    continue
                
                # Calculate momentum
                momentum_result = calculate_momentum_indicator(df, length=7, threshold=2.0)
                df['momentum'] = momentum_result['momentum']
                df['equilibrium'] = momentum_result['equilibrium']
                df['momentum_distance'] = df['momentum'] - df['equilibrium']
                
                # Calculate MAs
                df['ma_20'] = df['close'].rolling(20).mean()
                df['ma_50'] = df['close'].rolling(50).mean()
                df['ma_200'] = df['close'].rolling(200).mean()
                
                # MA relationships
                df['price_vs_ma20'] = ((df['close'] / df['ma_20']) - 1) * 100
                df['price_vs_ma50'] = ((df['close'] / df['ma_50']) - 1) * 100
                df['price_vs_ma200'] = ((df['close'] / df['ma_200']) - 1) * 100
                
                # MA alignment
                df['ma_aligned_bull'] = (df['ma_20'] > df['ma_50']) & (df['ma_50'] > df['ma_200'])
                df['ma_aligned_bear'] = (df['ma_20'] < df['ma_50']) & (df['ma_50'] < df['ma_200'])
                
                # Momentum trend
                df['momentum_rising'] = df['momentum'].diff() > 0
                df['momentum_falling'] = df['momentum'].diff() < 0
                df['price_rising'] = df['close'].diff() > 0
                
                # Drop NaN
                df = df.dropna().reset_index(drop=True)
                
                data[tf_name] = df
                print(f"   ✓ {tf_name}: {len(df)} bars")
                
            except Exception as e:
                print(f"   ✗ {tf_name}: {e}")
                continue
        
        return data


if __name__ == '__main__':
    """Test the Binance data provider"""
    print("=" * 80)
    print("  🧪 TESTING BINANCE DATA PROVIDER")
    print("  💰 NO API KEYS NEEDED")
    print("=" * 80)
    
    provider = BinanceDataProvider()
    
    # Test with Bitcoin
    symbol = 'BTC/USDT'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last month
    
    data = provider.download_multi_timeframe(symbol, start_date, end_date)
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE!")
    print(f"{'='*80}")
    print(f"\nDownloaded {len(data)} timeframes:")
    for tf_name, df in data.items():
        print(f"  {tf_name}: {len(df)} bars")
        if len(df) > 0:
            print(f"    Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
            print(f"    Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    print("\n💡 Ready to use with GA scripts!")
    print("   Just replace MultiTimeframeDataProvider with BinanceDataProvider")
