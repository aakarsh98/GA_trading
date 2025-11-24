"""
PROPER IV/IVP Calculation - Using Real Options Data
Two approaches: Free (limited) and Paid (complete)
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def method_1_current_iv_snapshot():
    """
    METHOD 1: Get CURRENT IV for stocks (FREE)
    Limitation: Only gets today's IV, no history
    """
    print("=" * 80)
    print("📊 METHOD 1: CURRENT IV SNAPSHOT (Free - yfinance)")
    print("=" * 80)
    
    tickers = ['SPY', 'AAPL', 'TSLA', 'NVDA', 'QQQ']
    
    print("\n⚠️  LIMITATION: Can only get TODAY's IV, not historical\n")
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            
            # Get current option chain
            expiration = stock.options[0]  # Nearest expiration
            chain = stock.option_chain(expiration)
            
            # Get ATM options
            current_price = stock.history(period='1d')['Close'].iloc[-1]
            
            # Find ATM call
            calls = chain.calls
            calls['diff'] = abs(calls['strike'] - current_price)
            atm_call = calls.loc[calls['diff'].idxmin()]
            
            iv = atm_call['impliedVolatility']
            
            print(f"{ticker:6s} | Price: ${current_price:7.2f} | IV: {iv*100:5.1f}%")
            
        except Exception as e:
            print(f"{ticker:6s} | Error: {str(e)[:50]}")
    
    print(f"\n💡 This gives us TODAY's IV, but not historical IVP!")
    print(f"   To calculate IVP, we need past 252 days of IV")
    print(f"   This is NOT available for free!\n")


def method_2_implied_volatility_proxy():
    """
    METHOD 2: Use Historical Volatility as IV Proxy (FREE but inaccurate)
    Limitation: HV ≠ IV (can differ significantly)
    """
    print("\n" + "=" * 80)
    print("📊 METHOD 2: HISTORICAL VOL AS PROXY (Free but inaccurate)")
    print("=" * 80)
    
    print("\n⚠️  LIMITATION: Historical Vol ≠ Implied Vol\n")
    
    ticker = 'AAPL'
    print(f"Example: {ticker}")
    
    # Download price data
    data = yf.download(ticker, period='2y', progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0].lower() for col in data.columns]
    else:
        data.columns = data.columns.str.lower()
    
    # Calculate historical volatility (20-day)
    returns = data['close'].pct_change()
    data['hv_20d'] = returns.rolling(20).std() * np.sqrt(252) * 100
    
    # Calculate "HVP" (HV percentile - proxy for IVP)
    lookback = 252
    hvp = []
    
    for i in range(len(data)):
        if i < lookback:
            hvp.append(np.nan)
        else:
            current = data.iloc[i]['hv_20d']
            historical = data.iloc[i-lookback:i]['hv_20d']
            if not np.isnan(current):
                percentile = (historical < current).sum() / len(historical.dropna()) * 100
                hvp.append(percentile)
            else:
                hvp.append(np.nan)
    
    data['hvp'] = hvp
    
    # Show recent data
    recent = data[['close', 'hv_20d', 'hvp']].tail(10).dropna()
    
    if len(recent) > 0:
        print(f"\n📈 Recent {ticker} Data:")
        print("-" * 60)
        print(f"{'Date':12s} | {'Price':>8s} | {'HV':>6s} | {'HVP':>6s}")
        print("-" * 60)
        
        for idx, row in recent.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            print(f"{date_str} | ${row['close']:7.2f} | {row['hv_20d']:5.1f}% | {row['hvp']:5.1f}%")
    
    print(f"\n⚠️  PROBLEM:")
    print(f"   • HV measures PAST volatility")
    print(f"   • IV measures EXPECTED future volatility")
    print(f"   • They can differ by 50%+ during events!")
    print(f"   • Example: Before earnings, IV spikes but HV is calm\n")


def method_3_vix_as_market_proxy():
    """
    METHOD 3: Use VIX as general market IV (FREE - what I did)
    Limitation: VIX ≠ individual stock IV
    """
    print("\n" + "=" * 80)
    print("📊 METHOD 3: VIX AS MARKET PROXY (What I did)")
    print("=" * 80)
    
    print("\n⚠️  LIMITATION: VIX is S&P 500 IV, not individual stocks\n")
    
    # Download VIX
    vix = yf.download('^VIX', period='1y', progress=False)
    
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = [col[0].lower() for col in vix.columns]
    else:
        vix.columns = vix.columns.str.lower()
    
    # Calculate IVP
    lookback = 252
    current_vix = vix['close'].iloc[-1]
    historical_vix = vix['close'].iloc[-lookback:-1]
    
    if len(historical_vix) > 0:
        ivp = (historical_vix < current_vix).sum() / len(historical_vix) * 100
        
        print(f"Current VIX: {current_vix:.2f}")
        print(f"VIX IVP: {ivp:.1f}%")
        
        print(f"\n✅ PROS:")
        print(f"   • Free and easy to get")
        print(f"   • Good for MARKET sentiment")
        print(f"   • Works for SPY, QQQ (index ETFs)")
        
        print(f"\n❌ CONS:")
        print(f"   • NOT accurate for individual stocks")
        print(f"   • AAPL IV ≠ VIX")
        print(f"   • TSLA IV ≠ VIX")
        print(f"   • Each stock has unique IV behavior")


def method_4_paid_data_sources():
    """
    METHOD 4: Proper Implementation (PAID data required)
    """
    print("\n" + "=" * 80)
    print("📊 METHOD 4: PROPER IMPLEMENTATION (Paid Data)")
    print("=" * 80)
    
    print("""
⭐ CORRECT APPROACH (Requires Paid Data):

1. Subscribe to Options Data Provider:
   
   Option A: Interactive Brokers API (Free with account)
   ─────────────────────────────────────────────────────
   • Cost: Free (need funded account)
   • Data: Historical options (limited)
   • Code:
     from ib_insync import *
     ib = IB()
     ib.connect()
     # Request historical IV data
   
   Option B: ThetaData ($150/month)
   ─────────────────────────────────────────────────────
   • Cost: $150/month (retail)
   • Data: Full options history back to 2003
   • Code:
     from thetadata import ThetaClient
     client = ThetaClient()
     iv_history = client.get_hist_option(
         symbol='AAPL',
         exp_date='2024-12-20',
         strike=180
     )
   
   Option C: CBOE DataShop ($100-500/month)
   ─────────────────────────────────────────────────────
   • Cost: $100-500/month
   • Data: Official CBOE data
   • API available
   
   Option D: Polygon.io ($200/month)
   ─────────────────────────────────────────────────────
   • Cost: $200/month
   • Data: Real-time + historical options
   • Code:
     import requests
     url = "https://api.polygon.io/v3/snapshot/options/AAPL"
     # Get IV history

2. Extract IV from Options Data:
   ─────────────────────────────────────────────────────
   For each day:
     a) Get ATM option (strike ≈ stock price)
     b) Extract implied volatility
     c) Store in database
   
   Result: 
     Date         | Stock | IV
     2024-01-01   | AAPL  | 23.5%
     2024-01-02   | AAPL  | 24.1%
     ...
     2024-11-20   | AAPL  | 28.3%

3. Calculate IVP:
   ─────────────────────────────────────────────────────
   Same formula as before:
     current_iv = 28.3%
     historical_ivs = past 252 days
     ivp = (historical_ivs < current_iv).sum() / 252 * 100

4. Trade Based on Stock's OWN IVP:
   ─────────────────────────────────────────────────────
   If AAPL IVP > 80:
     → Sell AAPL iron condor
   
   If TSLA IVP > 80:
     → Sell TSLA credit spread
   
   Each stock trades on ITS OWN IV cycle!
""")


def workaround_free_alternative():
    """
    WORKAROUND: Free alternative that's somewhat useful
    """
    print("\n" + "=" * 80)
    print("💡 WORKAROUND: Free Alternative (Partial Solution)")
    print("=" * 80)
    
    print("""
🎯 PRACTICAL FREE APPROACH:

1. Use VIX IVP for Market Timing:
   ─────────────────────────────────────────────────────
   • When VIX IVP > 80: Market fear high
   • Sell premium on SPY, QQQ (index products)
   • These correlate well with VIX
   
2. Use Today's IV + Historical Context:
   ─────────────────────────────────────────────────────
   • Get current IV from yfinance (free)
   • Compare to stock's typical range (manual research)
   • Example:
     - AAPL usually: 20-30% IV
     - Current: 45% IV
     - Conclusion: High, probably sell
   
3. Use Earnings as Volatility Events:
   ─────────────────────────────────────────────────────
   • Before earnings: IV always spikes
   • After earnings: IV always crashes
   • Don't need historical IV to know this
   • Strategy: Sell premium day before earnings
   
4. Use External Tools:
   ─────────────────────────────────────────────────────
   Free websites that show IV Rank/Percentile:
   • Barchart.com/options/iv-rank-percentile
   • MarketChameleon.com (limited free)
   • TastyTrade.com (IV rank for free)
   
   Workflow:
   1. Check website for IV rank
   2. If IV rank > 70, sell premium
   3. Use yfinance for backtesting (on indices)

5. Focus on Products with Available Data:
   ─────────────────────────────────────────────────────
   ✅ VIX: Full history available
   ✅ SPY: Can use VIX as proxy
   ✅ QQQ: Can use VIX as proxy
   ❌ AAPL: Need paid data
   ❌ TSLA: Need paid data
   
   Start with SPY/QQQ until you can afford data!
""")


def main():
    """Show all methods and their limitations"""
    print("\n" + "🎯" * 40)
    print(" " * 10 + "PROPER IV/IVP DATA: FREE VS PAID")
    print(" " * 15 + "(What data do we REALLY need?)")
    print("🎯" * 40)
    
    # Show each method
    method_1_current_iv_snapshot()
    method_2_implied_volatility_proxy()
    method_3_vix_as_market_proxy()
    method_4_paid_data_sources()
    workaround_free_alternative()
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 SUMMARY: DATA REQUIREMENTS")
    print("=" * 80)
    
    print("""
🔴 WHAT I DID (Simplified):
   • Used VIX as proxy for market IV
   • Calculated IVP from VIX history
   • ✅ Works for: SPY, QQQ, market timing
   • ❌ Doesn't work for: Individual stocks

🟢 WHAT YOU SHOULD DO (Proper):
   • Subscribe to options data provider
   • Get EACH stock's IV history
   • Calculate IVP for EACH stock separately
   • Trade based on that stock's IVP
   
💰 COST:
   Free approach: Limited to indices (SPY/QQQ)
   Paid approach: $150-500/month for full data
   
🎯 RECOMMENDATION:
   Phase 1 (Learning): Use VIX + SPY/QQQ (free)
   Phase 2 (Scaling): Subscribe to ThetaData ($150/mo)
   Phase 3 (Professional): Full data + automation
""")
    
    print("\n✅ Analysis complete!")
    print("\nYou're RIGHT - I should be using real IV data per stock!")
    print("For now, VIX works as a starting point for indices.\n")


if __name__ == "__main__":
    main()
