"""
Test DoltHub Free Options Database
Access FREE historical IV data!
"""
import pandas as pd
import subprocess
import os

print("\n" + "🎉" * 40)
print(" " * 10 + "TESTING FREE OPTIONS DATABASE")
print(" " * 15 + "(DoltHub - Completely FREE!)")
print("🎉" * 40)

# Check if doltpy is installed
print("\n📦 Checking dependencies...")
try:
    subprocess.run(['pip', 'show', 'doltpy'], check=True, capture_output=True)
    print("✅ doltpy already installed")
except:
    print("⚠️  Installing doltpy...")
    subprocess.run(['pip', 'install', '-q', 'doltpy'], check=True)
    print("✅ doltpy installed")

try:
    from doltpy.core import Dolt
    from doltpy.core.system_helpers import get_dolt_path
    
    print("\n" + "=" * 80)
    print("📥 ACCESSING DOLTHUB FREE OPTIONS DATABASE")
    print("=" * 80)
    
    print("\n🌐 Connecting to: post-no-preference/options")
    print("   Database: Free historical US options data")
    print("   Includes: IV, Greeks, Volume, OI, Prices")
    print("   Cost: $0 (completely free!)")
    
    # Clone database (downloads to local directory)
    db_path = 'dolthub_options_data'
    
    if not os.path.exists(db_path):
        print(f"\n📥 Downloading database to: {db_path}")
        print("   This may take a few minutes on first run...")
        
        try:
            dolt = Dolt.clone('post-no-preference/options', db_path)
            print("✅ Database cloned successfully!")
        except Exception as e:
            print(f"⚠️  Clone error: {e}")
            print("\nAlternative: Use SQL directly")
            print("Visit: https://www.dolthub.com/repositories/post-no-preference/options")
            exit(1)
    else:
        print(f"✅ Database already exists at: {db_path}")
        dolt = Dolt(db_path)
    
    print("\n" + "=" * 80)
    print("🔍 QUERYING DATA")
    print("=" * 80)
    
    # Query 1: Check what data is available
    print("\n1️⃣  Checking available symbols...")
    
    query = """
    SELECT symbol, COUNT(*) as records
    FROM option_chain
    GROUP BY symbol
    ORDER BY records DESC
    LIMIT 10
    """
    
    try:
        result = dolt.sql(query, result_format='pandas')
        
        print(f"\n📊 Top 10 symbols by record count:")
        print(result.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        print("\nNote: Database might need to be pulled")
        print("Try: cd dolthub_options_data && dolt pull")
    
    # Query 2: Get AAPL IV history
    print("\n2️⃣  Getting AAPL historical IV...")
    
    query = """
    SELECT 
        date,
        AVG(iv) as avg_iv,
        COUNT(*) as num_options,
        AVG(volume) as avg_volume
    FROM option_chain
    WHERE symbol = 'AAPL'
      AND option_type = 'call'
      AND date >= '2024-01-01'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 10
    """
    
    try:
        result = dolt.sql(query, result_format='pandas')
        
        if len(result) > 0:
            print(f"\n✅ Got {len(result)} days of AAPL IV data!")
            print("\n📈 Recent AAPL IV History:")
            print(result.to_string(index=False))
            
            # Calculate simple IVP for most recent
            if len(result) >= 10:
                current_iv = result.iloc[0]['avg_iv']
                historical = result.iloc[1:]['avg_iv']
                ivp = (historical < current_iv).sum() / len(historical) * 100
                
                print(f"\n🎯 Quick IVP Calculation:")
                print(f"   Current IV: {current_iv:.2%}")
                print(f"   IVP (10-day): {ivp:.1f}%")
                
                if ivp > 70:
                    print(f"   📊 HIGH IVP - Consider selling premium!")
                elif ivp < 30:
                    print(f"   📊 LOW IVP - Consider buying options!")
        else:
            print("⚠️  No data returned for AAPL")
            
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    # Query 3: Check date range
    print("\n3️⃣  Checking data date range...")
    
    query = """
    SELECT 
        MIN(date) as first_date,
        MAX(date) as last_date,
        COUNT(DISTINCT date) as total_days
    FROM option_chain
    """
    
    try:
        result = dolt.sql(query, result_format='pandas')
        
        print(f"\n📅 Data Coverage:")
        print(result.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)
    
    print("""
🎉 SUCCESS! You now have access to FREE historical options data!

What you can do:
  1. Query any US stock's historical IV
  2. Calculate IVP (IV Percentile) for free
  3. Analyze volatility cycles
  4. Backtest vol strategies
  5. NO COST!

Database location: dolthub_options_data/
Query language: SQL
Cost: $0

Next steps:
  1. Explore more symbols (SPY, QQQ, TSLA, etc.)
  2. Calculate historical IVP
  3. Build trading strategy
  4. Test with real data!
""")

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nInstall doltpy:")
    print("  pip install doltpy")

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"   Type: {type(e).__name__}")
    
    print("""
📚 Alternative Access Methods:

1. Web Interface:
   https://www.dolthub.com/repositories/post-no-preference/options
   
2. SQL Workbench (online):
   Query directly in browser
   
3. Download CSV:
   Export specific queries to CSV
   
4. Dolt CLI (direct):
   dolt clone post-no-preference/options
   cd options
   dolt sql -q "SELECT * FROM option_chain LIMIT 10"
""")

print("\n")
