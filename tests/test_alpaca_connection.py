"""
Test Alpaca API connection
"""
import os
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

print("🔍 Testing Alpaca API Connection...")
print("=" * 80)

# Check environment variables
api_key = os.getenv('ALPACA_API_KEY')
secret_key = os.getenv('ALPACA_SECRET_KEY')

if not api_key or not secret_key:
    print("❌ API keys not found in environment variables")
    print("\n📝 Set them with:")
    print("   export ALPACA_API_KEY='your_key'")
    print("   export ALPACA_SECRET_KEY='your_secret'")
    exit(1)

print(f"✅ Found API key: {api_key[:10]}...")
print(f"✅ Found secret key: {secret_key[:10]}...")

# Test connection
try:
    client = StockHistoricalDataClient(api_key, secret_key)
    
    # Try downloading small amount of data
    print("\n📥 Testing data download...")
    
    request = StockBarsRequest(
        symbol_or_symbols="SPY",
        timeframe=TimeFrame.Day,
        start=datetime.now() - timedelta(days=30),
        end=datetime.now()
    )
    
    bars = client.get_stock_bars(request)
    df = bars.df
    
    print(f"✅ Successfully downloaded {len(df)} bars of SPY daily data")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")
    print("\n🎉 Connection successful! You're ready to use the GA scripts.")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n📝 Make sure:")
    print("   1. Keys are correct")
    print("   2. Keys are from paper trading account")
    print("   3. You have internet connection")
