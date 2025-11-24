"""
DIRECTED TOP-DOWN MULTI-TIMEFRAME GENETIC ALGORITHM
Linear hierarchy: Monthly → Weekly → Daily → 4-Hour → 1-Hour → 15min
Top-down approach: Higher timeframes filter/confirm lower timeframes
GA discovers: Best thresholds and combinations within this structure
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import random
from dataclasses import dataclass
import json

# Alpaca for ALL timeframes (including intraday)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🧬 TOP-DOWN MULTI-TIMEFRAME GA")
print("  🎯 Linear Hierarchy: Monthly → Weekly → Daily → 4H → 1H → 15min")
print("  📊 Higher TF Filters → Lower TF Executes")
print("  💰 Using Alpaca FREE data for all timeframes")
print("=" * 80)

# ==============================================================================
# DATA PROVIDER - TOP-DOWN TIMEFRAMES
# ==============================================================================

class TopDownDataProvider:
    """Download data in top-down hierarchy using Alpaca"""
    
    def __init__(self):
        self.alpaca_client = StockHistoricalDataClient()
    
    def download_topdown_data(self, symbol: str, start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
        """
        Download data for top-down analysis
        Uses Alpaca for ALL timeframes including intraday
        
        Note: For longer timeframes (weekly/monthly), we aggregate from daily data
        """
        print(f"\n📥 Downloading top-down data for {symbol}...")
        print(f"   Period: {start.date()} to {end.date()}")
        
        data = {}
        
        # Define timeframes in top-down order with Alpaca timeframes
        timeframes = {
            '1d': ('Daily', AlpacaTimeFrame.Day),
            '4h': ('4-Hour', AlpacaTimeFrame(4, AlpacaTimeFrame.Hour)),
            '1h': ('Hourly', AlpacaTimeFrame.Hour),
            '15m': ('15-minute', AlpacaTimeFrame(15, AlpacaTimeFrame.Minute)),
        }
        
        for tf_code, (tf_name, alpaca_tf) in timeframes.items():
            try:
                # Download data from Alpaca
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=alpaca_tf,
                    start=start,
                    end=end
                )
                
                bars = self.alpaca_client.get_stock_bars(request)
                df = bars.df
                
                # Reset index to get timestamp as column
                if isinstance(df.index, pd.MultiIndex):
                    df = df.reset_index(level=0, drop=True)
                
                df = df.reset_index()
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']
                
                # Keep only OHLCV
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
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
                
                # MA alignment (trend strength)
                df['ma_aligned_bull'] = (df['ma_20'] > df['ma_50']) & (df['ma_50'] > df['ma_200'])
                df['ma_aligned_bear'] = (df['ma_20'] < df['ma_50']) & (df['ma_50'] < df['ma_200'])
                
                # Momentum trend
                df['momentum_rising'] = df['momentum'].diff() > 0
                df['momentum_falling'] = df['momentum'].diff() < 0
                
                # Price trend
                df['price_rising'] = df['close'].diff() > 0
                
                # Drop NaN
                df = df.dropna().reset_index(drop=True)
                
                data[tf_code] = df
                print(f"   ✓ {tf_name}: {len(df)} bars")
                
            except Exception as e:
                print(f"   ✗ {tf_name}: {e}")
                continue
        
        # Create weekly and monthly from daily data (if daily exists)
        if '1d' in data:
            print("   📊 Aggregating to weekly and monthly...")
            daily_df = data['1d'].copy()
            
            # Weekly aggregation
            try:
                weekly_df = daily_df.set_index('timestamp')
                weekly_df = weekly_df.resample('W').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).reset_index()
                
                # Recalculate indicators for weekly
                momentum_result = calculate_momentum_indicator(weekly_df, length=7, threshold=2.0)
                weekly_df['momentum'] = momentum_result['momentum']
                weekly_df['equilibrium'] = momentum_result['equilibrium']
                weekly_df['momentum_distance'] = weekly_df['momentum'] - weekly_df['equilibrium']
                
                weekly_df['ma_20'] = weekly_df['close'].rolling(20).mean()
                weekly_df['ma_50'] = weekly_df['close'].rolling(50).mean()
                weekly_df['ma_200'] = weekly_df['close'].rolling(200).mean()
                
                weekly_df['price_vs_ma20'] = ((weekly_df['close'] / weekly_df['ma_20']) - 1) * 100
                weekly_df['price_vs_ma50'] = ((weekly_df['close'] / weekly_df['ma_50']) - 1) * 100
                weekly_df['price_vs_ma200'] = ((weekly_df['close'] / weekly_df['ma_200']) - 1) * 100
                
                weekly_df['ma_aligned_bull'] = (weekly_df['ma_20'] > weekly_df['ma_50']) & (weekly_df['ma_50'] > weekly_df['ma_200'])
                weekly_df['ma_aligned_bear'] = (weekly_df['ma_20'] < weekly_df['ma_50']) & (weekly_df['ma_50'] < weekly_df['ma_200'])
                
                weekly_df['momentum_rising'] = weekly_df['momentum'].diff() > 0
                weekly_df['momentum_falling'] = weekly_df['momentum'].diff() < 0
                weekly_df['price_rising'] = weekly_df['close'].diff() > 0
                
                weekly_df = weekly_df.dropna().reset_index(drop=True)
                data['1wk'] = weekly_df
                print(f"   ✓ Weekly: {len(weekly_df)} bars")
            except Exception as e:
                print(f"   ✗ Weekly aggregation: {e}")
            
            # Monthly aggregation
            try:
                monthly_df = daily_df.set_index('timestamp')
                monthly_df = monthly_df.resample('M').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).reset_index()
                
                # Recalculate indicators for monthly
                momentum_result = calculate_momentum_indicator(monthly_df, length=7, threshold=2.0)
                monthly_df['momentum'] = momentum_result['momentum']
                monthly_df['equilibrium'] = momentum_result['equilibrium']
                monthly_df['momentum_distance'] = monthly_df['momentum'] - monthly_df['equilibrium']
                
                monthly_df['ma_20'] = monthly_df['close'].rolling(20).mean()
                monthly_df['ma_50'] = monthly_df['close'].rolling(50).mean()
                monthly_df['ma_200'] = monthly_df['close'].rolling(200).mean()
                
                monthly_df['price_vs_ma20'] = ((monthly_df['close'] / monthly_df['ma_20']) - 1) * 100
                monthly_df['price_vs_ma50'] = ((monthly_df['close'] / monthly_df['ma_50']) - 1) * 100
                monthly_df['price_vs_ma200'] = ((monthly_df['close'] / monthly_df['ma_200']) - 1) * 100
                
                monthly_df['ma_aligned_bull'] = (monthly_df['ma_20'] > monthly_df['ma_50']) & (monthly_df['ma_50'] > monthly_df['ma_200'])
                monthly_df['ma_aligned_bear'] = (monthly_df['ma_20'] < monthly_df['ma_50']) & (monthly_df['ma_50'] < monthly_df['ma_200'])
                
                monthly_df['momentum_rising'] = monthly_df['momentum'].diff() > 0
                monthly_df['momentum_falling'] = monthly_df['momentum'].diff() < 0
                monthly_df['price_rising'] = monthly_df['close'].diff() > 0
                
                monthly_df = monthly_df.dropna().reset_index(drop=True)
                data['1mo'] = monthly_df
                print(f"   ✓ Monthly: {len(monthly_df)} bars")
            except Exception as e:
                print(f"   ✗ Monthly aggregation: {e}")
        
        return data

# ==============================================================================
# TOP-DOWN GENE STRUCTURE
# ==============================================================================

@dataclass
class TopDownGene:
    """
    Directed top-down gene structure
    Each level has its own conditions that filter down
    """
    # === MONTHLY LEVEL (Highest - Long-term trend) ===
    monthly_enabled: bool
    monthly_filter_type: str        # 'ma_alignment', 'momentum_level', 'price_vs_ma'
    monthly_ma_period: str          # 'ma_20', 'ma_50', 'ma_200'
    monthly_momentum_min: float     # Minimum momentum to allow trades (0-100)
    monthly_momentum_max: float     # Maximum momentum
    monthly_require_bull_alignment: bool
    
    # === WEEKLY LEVEL (Medium-term trend) ===
    weekly_enabled: bool
    weekly_filter_type: str
    weekly_ma_period: str
    weekly_momentum_min: float
    weekly_momentum_max: float
    weekly_require_bull_alignment: bool
    weekly_confirm_monthly: bool    # Require agreement with monthly
    
    # === DAILY LEVEL (Short-term trend) ===
    daily_enabled: bool
    daily_filter_type: str
    daily_ma_period: str
    daily_momentum_min: float
    daily_momentum_max: float
    daily_require_bull_alignment: bool
    daily_confirm_weekly: bool
    
    # === HOURLY LEVEL (Intraday trend) ===
    hourly_enabled: bool
    hourly_filter_type: str
    hourly_ma_period: str
    hourly_momentum_min: float
    hourly_momentum_max: float
    hourly_require_bull_alignment: bool
    hourly_confirm_daily: bool
    
    # === 15-MINUTE LEVEL (Execution timeframe) ===
    execution_momentum_min: float   # Entry momentum range on 15min
    execution_momentum_max: float
    execution_require_momentum_rising: bool
    execution_require_price_above_ma: bool
    execution_ma_period: str
    
    # === FILTER CASCADE LOGIC ===
    cascade_type: str               # 'strict' (all must pass), 'majority' (2+ must pass), 'any' (1+ must pass)
    weight_higher_timeframes: bool  # Give more weight to higher TFs
    
    # === ENTRY TRIGGER ===
    entry_on_momentum_cross: bool   # Enter when momentum crosses threshold
    entry_momentum_threshold: float # Threshold to cross
    entry_momentum_direction: str   # 'above', 'below'
    
    entry_on_ma_cross: bool         # Enter on MA crossover
    entry_ma_fast: str              # 'ma_20', 'ma_50'
    entry_ma_slow: str              # 'ma_50', 'ma_200'
    
    entry_on_price_reversal: bool   # Enter on price reversal after pullback
    entry_pullback_pct: float       # Size of pullback (2-10%)
    
    # === EXIT STRATEGY ===
    exit_on_htf_reversal: bool      # Exit if higher TF reverses
    exit_htf_level: str             # Which TF to monitor ('1wk', '1d', '1h')
    
    exit_on_momentum_extreme: bool  # Exit at momentum extremes
    exit_momentum_overbought: float # Exit above this (70-95)
    exit_momentum_oversold: float   # Exit below this (5-30)
    
    exit_on_ma_cross: bool          # Exit on MA cross
    exit_ma_fast: str
    exit_ma_slow: str
    
    # === POSITION MANAGEMENT ===
    position_size_base: float       # Base position size (10-100%)
    scale_size_by_alignment: bool   # Increase size when all TFs align
    alignment_size_boost: float     # Additional size when aligned (0-50%)
    
    # === RISK MANAGEMENT ===
    stop_loss_pct: float            # Fixed stop loss (2-15%)
    stop_loss_based_on_htf_ma: bool # Use higher TF MA as stop
    stop_loss_htf_level: str        # Which TF MA to use
    stop_loss_htf_ma: str           # Which MA
    
    take_profit_pct: float          # Fixed take profit (5-40%)
    take_profit_scaled: bool        # Scale TP based on trend strength
    
    trailing_stop_enabled: bool
    trailing_stop_activation: float # Activate after X% profit
    trailing_stop_distance: float   # Trail by X%
    
    # === TIME MANAGEMENT ===
    min_hold_bars: int              # Minimum hold (in execution TF bars)
    max_hold_bars: int              # Maximum hold
    
    # === DIRECTION ===
    allow_long: bool
    allow_short: bool
    
    # === ADVANCED TOP-DOWN FEATURES ===
    require_full_cascade: bool      # Require all enabled TFs to agree
    allow_counter_trend_daily: bool # Allow daily counter-trend if weekly/monthly bullish
    
    reentry_on_pullback: bool       # Re-enter on pullbacks in strong trends
    reentry_pullback_min: float     # Minimum pullback size (2-8%)
    reentry_max_attempts: int       # Max re-entries (1-3)

# ==============================================================================
# TOP-DOWN FILTER EVALUATION
# ==============================================================================

def evaluate_topdown_filter(filter_type: str, df: pd.DataFrame, idx: int,
                             ma_period: str, momentum_min: float, momentum_max: float,
                             require_bull_alignment: bool) -> bool:
    """
    Evaluate if a timeframe passes its filter
    
    Returns:
        True if timeframe conditions are met (allows trading)
        False if conditions not met (blocks trading)
    """
    if idx >= len(df) or idx < 0:
        return False
    
    row = df.iloc[idx]
    
    # Check momentum range
    if not (momentum_min <= row['momentum'] <= momentum_max):
        return False
    
    # Check MA alignment requirement
    if require_bull_alignment:
        if not row['ma_aligned_bull']:
            return False
    
    # Check specific filter type
    if filter_type == 'ma_alignment':
        # Already checked above
        pass
    
    elif filter_type == 'momentum_level':
        # Momentum must be in upper range (bullish)
        if row['momentum'] < 60:
            return False
    
    elif filter_type == 'price_vs_ma':
        # Price must be above specified MA
        if ma_period == 'ma_20':
            if row['close'] < row['ma_20']:
                return False
        elif ma_period == 'ma_50':
            if row['close'] < row['ma_50']:
                return False
        elif ma_period == 'ma_200':
            if row['close'] < row['ma_200']:
                return False
    
    elif filter_type == 'momentum_rising':
        if not row['momentum_rising']:
            return False
    
    return True

def get_timeframe_index(timestamp: pd.Timestamp, df: pd.DataFrame) -> int:
    """Get the index in df corresponding to timestamp (or closest before)"""
    matching = df['timestamp'] <= timestamp
    if matching.sum() == 0:
        return -1
    return matching.sum() - 1

# ==============================================================================
# TOP-DOWN BACKTESTER
# ==============================================================================

def backtest_topdown_strategy(gene: TopDownGene,
                               topdown_data: Dict[str, pd.DataFrame],
                               initial_capital: float = 10000) -> Dict:
    """
    Backtest top-down strategy
    
    Process:
    1. Check monthly filter → if pass, continue
    2. Check weekly filter → if pass, continue
    3. Check daily filter → if pass, continue
    4. Check hourly filter → if pass, continue
    5. Look for entry on 15min → execute
    """
    # Execution timeframe is 15min (or hourly if 15min not available)
    if '15m' in topdown_data:
        exec_tf = '15m'
        exec_df = topdown_data['15m']
    elif '1h' in topdown_data:
        exec_tf = '1h'
        exec_df = topdown_data['1h']
    else:
        return {'return': -100, 'trades': 0, 'win_rate': 0}
    
    # Trading state
    capital = initial_capital
    position = 0
    position_side = None
    entry_price = 0
    entry_idx = 0
    
    trades = []
    equity_curve = [initial_capital]
    
    # Iterate through execution timeframe
    for i in range(100, len(exec_df)):
        current_price = exec_df.iloc[i]['close']
        current_time = exec_df.iloc[i]['timestamp']
        
        # === CASCADE FILTER CHECK (TOP-DOWN) ===
        filters_passed = []
        
        # MONTHLY FILTER
        if gene.monthly_enabled and '1mo' in topdown_data:
            monthly_df = topdown_data['1mo']
            monthly_idx = get_timeframe_index(current_time, monthly_df)
            monthly_pass = evaluate_topdown_filter(
                gene.monthly_filter_type,
                monthly_df,
                monthly_idx,
                gene.monthly_ma_period,
                gene.monthly_momentum_min,
                gene.monthly_momentum_max,
                gene.monthly_require_bull_alignment
            )
            filters_passed.append(('monthly', monthly_pass))
        
        # WEEKLY FILTER
        if gene.weekly_enabled and '1wk' in topdown_data:
            weekly_df = topdown_data['1wk']
            weekly_idx = get_timeframe_index(current_time, weekly_df)
            weekly_pass = evaluate_topdown_filter(
                gene.weekly_filter_type,
                weekly_df,
                weekly_idx,
                gene.weekly_ma_period,
                gene.weekly_momentum_min,
                gene.weekly_momentum_max,
                gene.weekly_require_bull_alignment
            )
            filters_passed.append(('weekly', weekly_pass))
            
            # Confirm with monthly if required
            if gene.weekly_confirm_monthly and len(filters_passed) > 1:
                if not filters_passed[0][1]:  # Monthly didn't pass
                    weekly_pass = False
        
        # DAILY FILTER
        if gene.daily_enabled and '1d' in topdown_data:
            daily_df = topdown_data['1d']
            daily_idx = get_timeframe_index(current_time, daily_df)
            daily_pass = evaluate_topdown_filter(
                gene.daily_filter_type,
                daily_df,
                daily_idx,
                gene.daily_ma_period,
                gene.daily_momentum_min,
                gene.daily_momentum_max,
                gene.daily_require_bull_alignment
            )
            filters_passed.append(('daily', daily_pass))
            
            # Confirm with weekly if required
            if gene.daily_confirm_weekly:
                weekly_result = [f for f in filters_passed if f[0] == 'weekly']
                if weekly_result and not weekly_result[0][1]:
                    daily_pass = False
        
        # HOURLY FILTER
        if gene.hourly_enabled and '1h' in topdown_data:
            hourly_df = topdown_data['1h']
            hourly_idx = get_timeframe_index(current_time, hourly_df)
            hourly_pass = evaluate_topdown_filter(
                gene.hourly_filter_type,
                hourly_df,
                hourly_idx,
                gene.hourly_ma_period,
                gene.hourly_momentum_min,
                gene.hourly_momentum_max,
                gene.hourly_require_bull_alignment
            )
            filters_passed.append(('hourly', hourly_pass))
            
            # Confirm with daily if required
            if gene.hourly_confirm_daily:
                daily_result = [f for f in filters_passed if f[0] == 'daily']
                if daily_result and not daily_result[0][1]:
                    hourly_pass = False
        
        # === DETERMINE IF TRADING ALLOWED (CASCADE LOGIC) ===
        trading_allowed = False
        
        if gene.cascade_type == 'strict':
            # All enabled timeframes must pass
            if len(filters_passed) > 0:
                trading_allowed = all(f[1] for f in filters_passed)
            else:
                trading_allowed = True  # No filters, allow trading
        
        elif gene.cascade_type == 'majority':
            # At least half must pass
            if len(filters_passed) > 0:
                passed_count = sum(1 for f in filters_passed if f[1])
                trading_allowed = passed_count >= len(filters_passed) / 2
            else:
                trading_allowed = True
        
        elif gene.cascade_type == 'any':
            # At least one must pass
            if len(filters_passed) > 0:
                trading_allowed = any(f[1] for f in filters_passed)
            else:
                trading_allowed = True
        
        # === CHECK EXECUTION TIMEFRAME CONDITIONS ===
        if position == 0 and trading_allowed:
            exec_momentum = exec_df.iloc[i]['momentum']
            
            # Check execution momentum range
            if not (gene.execution_momentum_min <= exec_momentum <= gene.execution_momentum_max):
                continue
            
            # Check if momentum is rising (if required)
            if gene.execution_require_momentum_rising:
                if not exec_df.iloc[i]['momentum_rising']:
                    continue
            
            # Check if price above MA (if required)
            if gene.execution_require_price_above_ma:
                ma_col = gene.execution_ma_period
                if exec_df.iloc[i]['close'] < exec_df.iloc[i][ma_col]:
                    continue
            
            # === ENTRY TRIGGERS ===
            entry_signal = False
            
            # Momentum cross trigger
            if gene.entry_on_momentum_cross:
                if i > 0:
                    prev_momentum = exec_df.iloc[i-1]['momentum']
                    if gene.entry_momentum_direction == 'above':
                        if prev_momentum < gene.entry_momentum_threshold and exec_momentum >= gene.entry_momentum_threshold:
                            entry_signal = True
                    elif gene.entry_momentum_direction == 'below':
                        if prev_momentum > gene.entry_momentum_threshold and exec_momentum <= gene.entry_momentum_threshold:
                            entry_signal = True
            
            # MA cross trigger
            if gene.entry_on_ma_cross:
                if i > 0:
                    fast_ma = exec_df.iloc[i][gene.entry_ma_fast]
                    slow_ma = exec_df.iloc[i][gene.entry_ma_slow]
                    prev_fast = exec_df.iloc[i-1][gene.entry_ma_fast]
                    prev_slow = exec_df.iloc[i-1][gene.entry_ma_slow]
                    
                    # Bullish cross
                    if prev_fast < prev_slow and fast_ma >= slow_ma:
                        entry_signal = True
            
            # Price reversal trigger
            if gene.entry_on_price_reversal:
                # Check for pullback followed by reversal
                if i > 10:
                    recent_high = exec_df.iloc[i-10:i]['close'].max()
                    pullback_pct = (recent_high - current_price) / recent_high * 100
                    if pullback_pct >= gene.entry_pullback_pct:
                        # Check if price is now rising
                        if exec_df.iloc[i]['price_rising']:
                            entry_signal = True
            
            # ENTER POSITION
            if entry_signal and gene.allow_long:
                # Calculate position size
                base_size = gene.position_size_base / 100.0
                
                # Boost size if all timeframes aligned
                if gene.scale_size_by_alignment:
                    if all(f[1] for f in filters_passed):
                        boost = gene.alignment_size_boost / 100.0
                        base_size += boost
                        base_size = min(base_size, 1.0)  # Cap at 100%
                
                shares = int((capital * base_size) / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_idx = i
                    position_side = 'long'
                    
                    cost = shares * current_price * 1.001
                    capital -= cost
        
        # === EXIT LOGIC ===
        elif position > 0:
            bars_held = i - entry_idx
            unrealized_pnl_pct = (current_price / entry_price - 1) * 100
            
            exit_signal = False
            exit_reason = ""
            
            # Time-based exit
            if bars_held >= gene.max_hold_bars:
                exit_signal = True
                exit_reason = "max_hold"
            elif bars_held < gene.min_hold_bars:
                pass  # Don't exit yet
            else:
                # Stop loss
                if unrealized_pnl_pct <= -gene.stop_loss_pct:
                    exit_signal = True
                    exit_reason = "stop_loss"
                
                # Take profit
                if unrealized_pnl_pct >= gene.take_profit_pct:
                    exit_signal = True
                    exit_reason = "take_profit"
                
                # Exit on HTF reversal
                if gene.exit_on_htf_reversal:
                    htf = gene.exit_htf_level
                    if htf in topdown_data:
                        htf_df = topdown_data[htf]
                        htf_idx = get_timeframe_index(current_time, htf_df)
                        if htf_idx >= 0 and htf_idx < len(htf_df):
                            # Check if HTF momentum turned bearish
                            if htf_df.iloc[htf_idx]['momentum'] < 40:
                                exit_signal = True
                                exit_reason = "htf_reversal"
                
                # Exit on momentum extreme
                if gene.exit_on_momentum_extreme:
                    exec_momentum = exec_df.iloc[i]['momentum']
                    if exec_momentum >= gene.exit_momentum_overbought:
                        exit_signal = True
                        exit_reason = "overbought"
                    elif exec_momentum <= gene.exit_momentum_oversold:
                        exit_signal = True
                        exit_reason = "oversold"
                
                # Exit on MA cross
                if gene.exit_on_ma_cross and i > 0:
                    fast_ma = exec_df.iloc[i][gene.exit_ma_fast]
                    slow_ma = exec_df.iloc[i][gene.exit_ma_slow]
                    prev_fast = exec_df.iloc[i-1][gene.exit_ma_fast]
                    prev_slow = exec_df.iloc[i-1][gene.exit_ma_slow]
                    
                    # Bearish cross
                    if prev_fast > prev_slow and fast_ma <= slow_ma:
                        exit_signal = True
                        exit_reason = "ma_cross"
            
            # EXIT POSITION
            if exit_signal:
                proceeds = position * current_price * 0.999
                capital += proceeds
                
                pnl = proceeds - (position * entry_price)
                pnl_pct = (pnl / (position * entry_price)) * 100
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'reason': exit_reason
                })
                
                position = 0
                position_side = None
        
        # Track equity
        if position > 0:
            equity_curve.append(capital + position * current_price)
        else:
            equity_curve.append(capital)
    
    # Close any remaining position
    if position > 0:
        final_price = exec_df.iloc[-1]['close']
        proceeds = position * final_price * 0.999
        capital += proceeds
        pnl = proceeds - (position * entry_price)
        pnl_pct = (pnl / (position * entry_price)) * 100
        trades.append({
            'entry_price': entry_price,
            'exit_price': final_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'bars_held': len(exec_df) - entry_idx,
            'reason': 'end_of_data'
        })
    
    # Calculate metrics
    final_capital = capital
    total_return = (final_capital / initial_capital - 1) * 100
    
    if len(trades) == 0:
        return {
            'return': -10,
            'trades': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'sharpe': 0,
            'max_drawdown': 0
        }
    
    winning_trades = [t for t in trades if t['pnl'] > 0]
    losing_trades = [t for t in trades if t['pnl'] <= 0]
    
    win_rate = len(winning_trades) / len(trades) * 100
    avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
    
    returns = pd.Series(equity_curve).pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    return {
        'return': total_return,
        'trades': len(trades),
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'final_capital': final_capital
    }

# ==============================================================================
# GA FUNCTIONS
# ==============================================================================

def create_random_topdown_gene() -> TopDownGene:
    """Create random top-down gene"""
    
    filter_types = ['ma_alignment', 'momentum_level', 'price_vs_ma', 'momentum_rising']
    ma_periods = ['ma_20', 'ma_50', 'ma_200']
    cascade_types = ['strict', 'majority', 'any']
    
    return TopDownGene(
        # Monthly
        monthly_enabled=random.choice([True, True, False]),
        monthly_filter_type=random.choice(filter_types),
        monthly_ma_period=random.choice(ma_periods),
        monthly_momentum_min=random.uniform(20, 40),
        monthly_momentum_max=random.uniform(60, 80),
        monthly_require_bull_alignment=random.choice([True, False]),
        
        # Weekly
        weekly_enabled=random.choice([True, True, True, False]),
        weekly_filter_type=random.choice(filter_types),
        weekly_ma_period=random.choice(ma_periods),
        weekly_momentum_min=random.uniform(25, 45),
        weekly_momentum_max=random.uniform(55, 75),
        weekly_require_bull_alignment=random.choice([True, False]),
        weekly_confirm_monthly=random.choice([True, False]),
        
        # Daily
        daily_enabled=random.choice([True, True, True, True, False]),
        daily_filter_type=random.choice(filter_types),
        daily_ma_period=random.choice(ma_periods),
        daily_momentum_min=random.uniform(30, 50),
        daily_momentum_max=random.uniform(50, 70),
        daily_require_bull_alignment=random.choice([True, False]),
        daily_confirm_weekly=random.choice([True, False]),
        
        # Hourly
        hourly_enabled=random.choice([True, True, False]),
        hourly_filter_type=random.choice(filter_types),
        hourly_ma_period=random.choice(ma_periods),
        hourly_momentum_min=random.uniform(35, 55),
        hourly_momentum_max=random.uniform(45, 65),
        hourly_require_bull_alignment=random.choice([True, False]),
        hourly_confirm_daily=random.choice([True, False]),
        
        # Execution (15min)
        execution_momentum_min=random.uniform(40, 60),
        execution_momentum_max=random.uniform(50, 70),
        execution_require_momentum_rising=random.choice([True, False]),
        execution_require_price_above_ma=random.choice([True, False]),
        execution_ma_period=random.choice(ma_periods),
        
        # Cascade
        cascade_type=random.choice(cascade_types),
        weight_higher_timeframes=random.choice([True, False]),
        
        # Entry triggers
        entry_on_momentum_cross=random.choice([True, False]),
        entry_momentum_threshold=random.uniform(45, 65),
        entry_momentum_direction=random.choice(['above', 'below']),
        
        entry_on_ma_cross=random.choice([True, False]),
        entry_ma_fast='ma_20',
        entry_ma_slow=random.choice(['ma_50', 'ma_200']),
        
        entry_on_price_reversal=random.choice([True, False]),
        entry_pullback_pct=random.uniform(2, 8),
        
        # Exit
        exit_on_htf_reversal=random.choice([True, False]),
        exit_htf_level=random.choice(['1wk', '1d', '1h']),
        
        exit_on_momentum_extreme=random.choice([True, False]),
        exit_momentum_overbought=random.uniform(75, 95),
        exit_momentum_oversold=random.uniform(5, 25),
        
        exit_on_ma_cross=random.choice([True, False]),
        exit_ma_fast='ma_20',
        exit_ma_slow='ma_50',
        
        # Position sizing
        position_size_base=random.uniform(50, 95),
        scale_size_by_alignment=random.choice([True, False]),
        alignment_size_boost=random.uniform(5, 30),
        
        # Risk
        stop_loss_pct=random.uniform(3, 12),
        stop_loss_based_on_htf_ma=random.choice([True, False]),
        stop_loss_htf_level=random.choice(['1d', '1h']),
        stop_loss_htf_ma='ma_50',
        
        take_profit_pct=random.uniform(8, 30),
        take_profit_scaled=random.choice([True, False]),
        
        trailing_stop_enabled=random.choice([True, False]),
        trailing_stop_activation=random.uniform(5, 15),
        trailing_stop_distance=random.uniform(3, 8),
        
        # Time
        min_hold_bars=random.randint(1, 5),
        max_hold_bars=random.randint(20, 100),
        
        # Direction
        allow_long=random.choice([True, True, True, False]),
        allow_short=random.choice([True, False, False, False]),
        
        # Advanced
        require_full_cascade=random.choice([True, False]),
        allow_counter_trend_daily=random.choice([True, False]),
        
        reentry_on_pullback=random.choice([True, False]),
        reentry_pullback_min=random.uniform(2, 6),
        reentry_max_attempts=random.randint(1, 3),
    )

def mutate_topdown_gene(gene: TopDownGene, mutation_rate: float = 0.15) -> TopDownGene:
    """Mutate top-down gene"""
    import copy
    new_gene = copy.deepcopy(gene)
    
    # Mutate each field with probability
    if random.random() < mutation_rate:
        new_gene.monthly_momentum_min += random.uniform(-10, 10)
        new_gene.monthly_momentum_min = np.clip(new_gene.monthly_momentum_min, 0, 50)
    
    if random.random() < mutation_rate:
        new_gene.weekly_momentum_max += random.uniform(-10, 10)
        new_gene.weekly_momentum_max = np.clip(new_gene.weekly_momentum_max, 50, 100)
    
    if random.random() < mutation_rate:
        new_gene.execution_momentum_min += random.uniform(-10, 10)
        new_gene.execution_momentum_min = np.clip(new_gene.execution_momentum_min, 0, 100)
    
    if random.random() < mutation_rate:
        new_gene.stop_loss_pct += random.uniform(-3, 3)
        new_gene.stop_loss_pct = np.clip(new_gene.stop_loss_pct, 1, 20)
    
    if random.random() < mutation_rate:
        new_gene.take_profit_pct += random.uniform(-5, 5)
        new_gene.take_profit_pct = np.clip(new_gene.take_profit_pct, 5, 50)
    
    if random.random() < mutation_rate:
        new_gene.cascade_type = random.choice(['strict', 'majority', 'any'])
    
    return new_gene

def crossover_topdown_genes(parent1: TopDownGene, parent2: TopDownGene) -> TopDownGene:
    """Crossover two top-down genes"""
    import copy
    
    child = copy.deepcopy(parent1)
    
    # Randomly inherit from either parent
    if random.random() < 0.5:
        child.monthly_enabled = parent2.monthly_enabled
        child.monthly_filter_type = parent2.monthly_filter_type
    
    if random.random() < 0.5:
        child.weekly_filter_type = parent2.weekly_filter_type
        child.weekly_confirm_monthly = parent2.weekly_confirm_monthly
    
    if random.random() < 0.5:
        child.daily_filter_type = parent2.daily_filter_type
    
    if random.random() < 0.5:
        child.cascade_type = parent2.cascade_type
    
    if random.random() < 0.5:
        child.stop_loss_pct = parent2.stop_loss_pct
        child.take_profit_pct = parent2.take_profit_pct
    
    return child

def run_topdown_ga(topdown_data: Dict[str, pd.DataFrame],
                   population_size: int = 50,
                   generations: int = 100,
                   elite_size: int = 5) -> Tuple:
    """Run GA for top-down strategies"""
    
    print(f"\n🧬 Starting Top-Down GA: {population_size} population, {generations} generations")
    
    # Create initial population
    population = [create_random_topdown_gene() for _ in range(population_size)]
    
    best_ever_fitness = -float('inf')
    best_ever_gene = None
    best_ever_results = None
    
    generation_best = []
    
    for gen in range(generations):
        print(f"\n{'='*80}")
        print(f"Generation {gen+1}/{generations}")
        print(f"{'='*80}")
        
        # Evaluate fitness
        fitness_scores = []
        
        for idx, gene in enumerate(population):
            results = backtest_topdown_strategy(gene, topdown_data)
            
            # Fitness function
            fitness = results['return']
            
            if results['trades'] >= 10:
                fitness += 5
            if results['win_rate'] >= 55:
                fitness += results['win_rate'] * 0.1
            if results['trades'] < 5:
                fitness -= 20
            if results['sharpe'] > 1.0:
                fitness += results['sharpe'] * 5
            
            fitness_scores.append((gene, fitness, results))
            
            if idx % 10 == 0:
                print(f"  Evaluated {idx+1}/{population_size}...")
        
        # Sort by fitness
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Track best
        current_best = fitness_scores[0]
        generation_best.append(current_best)
        
        if current_best[1] > best_ever_fitness:
            best_ever_fitness = current_best[1]
            best_ever_gene = current_best[0]
            best_ever_results = current_best[2]
            print(f"\n🎉 NEW BEST! Fitness: {best_ever_fitness:.2f}")
            print(f"   Return: {best_ever_results['return']:.2f}%")
            print(f"   Trades: {best_ever_results['trades']}")
            print(f"   Win Rate: {best_ever_results['win_rate']:.1f}%")
        
        # Print stats
        print(f"\n📊 Generation {gen+1} Stats:")
        print(f"   Best Fitness: {current_best[1]:.2f}")
        print(f"   Best Return: {current_best[2]['return']:.2f}%")
        print(f"   Avg Fitness: {np.mean([f[1] for f in fitness_scores]):.2f}")
        
        # Selection and reproduction
        new_population = [gene for gene, _, _ in fitness_scores[:elite_size]]
        
        while len(new_population) < population_size:
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent1 = max(tournament, key=lambda x: x[1])[0]
            
            tournament = random.sample(fitness_scores[:population_size//2], 5)
            parent2 = max(tournament, key=lambda x: x[1])[0]
            
            child = crossover_topdown_genes(parent1, parent2)
            child = mutate_topdown_gene(child, 0.15)
            
            new_population.append(child)
        
        population = new_population
    
    print(f"\n{'='*80}")
    print("🏆 TOP-DOWN GA COMPLETE!")
    print(f"{'='*80}")
    
    return generation_best, best_ever_gene, best_ever_results

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    print("\n📥 Downloading top-down multi-timeframe data...")
    
    provider = TopDownDataProvider()
    
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year (Alpaca free tier limit for intraday)
    
    print(f"   Symbol: {symbol}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    
    topdown_data = provider.download_topdown_data(symbol, start_date, end_date)
    
    if len(topdown_data) < 3:
        print("❌ Not enough timeframes downloaded. Exiting.")
        sys.exit(1)
    
    print(f"\n✅ Downloaded {len(topdown_data)} timeframes")
    
    # Run GA
    generation_best, best_gene, best_results = run_topdown_ga(
        topdown_data,
        population_size=50,
        generations=50,
        elite_size=5
    )
    
    # Print best strategy
    print(f"\n{'='*80}")
    print("🎯 BEST TOP-DOWN STRATEGY DISCOVERED")
    print(f"{'='*80}")
    print(f"\n📊 Performance:")
    print(f"   Total Return: {best_results['return']:.2f}%")
    print(f"   Total Trades: {best_results['trades']}")
    print(f"   Win Rate: {best_results['win_rate']:.1f}%")
    print(f"   Sharpe Ratio: {best_results['sharpe']:.2f}")
    print(f"   Max Drawdown: {best_results['max_drawdown']:.2f}%")
    
    print(f"\n🔧 Top-Down Configuration:")
    print(f"   Monthly Filter: {'ENABLED' if best_gene.monthly_enabled else 'DISABLED'}")
    if best_gene.monthly_enabled:
        print(f"      Type: {best_gene.monthly_filter_type}")
        print(f"      Momentum: {best_gene.monthly_momentum_min:.1f} - {best_gene.monthly_momentum_max:.1f}")
    
    print(f"\n   Weekly Filter: {'ENABLED' if best_gene.weekly_enabled else 'DISABLED'}")
    if best_gene.weekly_enabled:
        print(f"      Type: {best_gene.weekly_filter_type}")
        print(f"      Confirm Monthly: {best_gene.weekly_confirm_monthly}")
    
    print(f"\n   Daily Filter: {'ENABLED' if best_gene.daily_enabled else 'DISABLED'}")
    if best_gene.daily_enabled:
        print(f"      Type: {best_gene.daily_filter_type}")
        print(f"      Confirm Weekly: {best_gene.daily_confirm_weekly}")
    
    print(f"\n   Cascade Logic: {best_gene.cascade_type.upper()}")
    print(f"   Position Size: {best_gene.position_size_base:.1f}%")
    print(f"   Stop Loss: {best_gene.stop_loss_pct:.1f}%")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}%")
    
    # Save strategy
    strategy_dict = {
        'performance': best_results,
        'gene': {
            'monthly_enabled': best_gene.monthly_enabled,
            'monthly_filter_type': best_gene.monthly_filter_type,
            'monthly_momentum_min': best_gene.monthly_momentum_min,
            'monthly_momentum_max': best_gene.monthly_momentum_max,
            'weekly_enabled': best_gene.weekly_enabled,
            'weekly_filter_type': best_gene.weekly_filter_type,
            'weekly_confirm_monthly': best_gene.weekly_confirm_monthly,
            'daily_enabled': best_gene.daily_enabled,
            'daily_filter_type': best_gene.daily_filter_type,
            'daily_confirm_weekly': best_gene.daily_confirm_weekly,
            'cascade_type': best_gene.cascade_type,
            'execution_momentum_min': best_gene.execution_momentum_min,
            'execution_momentum_max': best_gene.execution_momentum_max,
            'position_size_base': best_gene.position_size_base,
            'stop_loss_pct': best_gene.stop_loss_pct,
            'take_profit_pct': best_gene.take_profit_pct,
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('best_mtf_topdown_strategy.json', 'w') as f:
        json.dump(strategy_dict, f, indent=2)
    
    print("\n✅ Strategy saved to: best_mtf_topdown_strategy.json")
    print(f"\n{'='*80}")
    print("✅ TOP-DOWN GA COMPLETE!")
    print(f"{'='*80}")
