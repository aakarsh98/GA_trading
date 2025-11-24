"""
UNRESTRICTED MULTI-TIMEFRAME GENETIC ALGORITHM
Complete autonomy to discover best multi-timeframe conditions
Uses: Momentum Tracker + Moving Averages across multiple timeframes
GA discovers: Which timeframes matter, how to combine them, when to trade
"""
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import random
from dataclasses import dataclass, field
import json

# Alpaca for intraday data
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame as AlpacaTimeFrame

sys.path.append('tradingview-strategies/python_strategies/utils')
from actual_momentum_tracker import calculate_momentum_indicator

print("=" * 80)
print("  🧬 UNRESTRICTED MULTI-TIMEFRAME GA")
print("  🎯 Complete Freedom to Discover Timeframe Relationships")
print("  📊 Momentum + MA across 1min, 5min, 15min, 1h, 4h, 1d")
print("=" * 80)

# ==============================================================================
# DATA PROVIDER - MULTI-TIMEFRAME
# ==============================================================================

class MultiTimeframeDataProvider:
    """Download multi-timeframe data"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        """
        Initialize data provider
        
        Args:
            api_key: Alpaca API key (optional, will use dummy for historical)
            secret_key: Alpaca secret key (optional, will use dummy for historical)
        
        Note: Alpaca now requires keys even for historical data
        Get free keys at: https://alpaca.markets (paper trading account)
        """
        # Use provided keys or dummy keys (Alpaca requires something)
        if api_key is None:
            # Try environment variables
            import os
            api_key = os.getenv('ALPACA_API_KEY', 'DUMMY_KEY')
            secret_key = os.getenv('ALPACA_SECRET_KEY', 'DUMMY_SECRET')
        
        try:
            self.alpaca_client = StockHistoricalDataClient(api_key, secret_key)
        except Exception as e:
            print(f"\n⚠️  Alpaca API requires authentication now.")
            print(f"   Error: {e}")
            print(f"\n📝 To fix:")
            print(f"   1. Sign up for free at: https://alpaca.markets")
            print(f"   2. Get paper trading API keys")
            print(f"   3. Set environment variables:")
            print(f"      export ALPACA_API_KEY='your_key'")
            print(f"      export ALPACA_SECRET_KEY='your_secret'")
            print(f"\n   Or use yfinance fallback (daily data only)...")
            raise
    
    def download_multi_timeframe(self, symbol: str, start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple timeframes
        Returns dict of {timeframe: dataframe}
        """
        timeframes = {
            '1min': AlpacaTimeFrame.Minute,
            '5min': AlpacaTimeFrame(5, AlpacaTimeFrame.Minute),
            '15min': AlpacaTimeFrame(15, AlpacaTimeFrame.Minute),
            '1hour': AlpacaTimeFrame.Hour,
            '4hour': AlpacaTimeFrame(4, AlpacaTimeFrame.Hour),
            '1day': AlpacaTimeFrame.Day,
        }
        
        data = {}
        
        for name, tf in timeframes.items():
            try:
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=tf,
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
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                # Calculate momentum for this timeframe
                momentum_result = calculate_momentum_indicator(df, length=7, threshold=2.0)
                df['momentum'] = momentum_result['momentum']
                df['equilibrium'] = momentum_result['equilibrium']
                
                # Calculate MAs
                df['ma_20'] = df['close'].rolling(20).mean()
                df['ma_50'] = df['close'].rolling(50).mean()
                df['ma_200'] = df['close'].rolling(200).mean()
                
                # Price position vs MAs
                df['price_vs_ma20'] = ((df['close'] / df['ma_20']) - 1) * 100
                df['price_vs_ma50'] = ((df['close'] / df['ma_50']) - 1) * 100
                df['price_vs_ma200'] = ((df['close'] / df['ma_200']) - 1) * 100
                
                # MA alignment
                df['ma_aligned_bull'] = (df['ma_20'] > df['ma_50']) & (df['ma_50'] > df['ma_200'])
                df['ma_aligned_bear'] = (df['ma_20'] < df['ma_50']) & (df['ma_50'] < df['ma_200'])
                
                # Drop NaN
                df = df.dropna().reset_index(drop=True)
                
                data[name] = df
                print(f"  ✓ {name}: {len(df)} bars")
                
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                continue
        
        return data

# ==============================================================================
# UNRESTRICTED MULTI-TIMEFRAME GENE
# ==============================================================================

@dataclass
class MTFUnrestrictedGene:
    """
    Completely unrestricted multi-timeframe gene
    GA decides which timeframes to use and how
    """
    # === TIMEFRAME SELECTION (GA chooses which timeframes matter) ===
    primary_timeframe: str  # '1min', '5min', '15min', '1hour', '4hour', '1day'
    confirm_timeframe: str  # Second timeframe for confirmation
    filter_timeframe: str   # Third timeframe for filtering
    
    use_primary: bool       # Whether to use primary timeframe
    use_confirm: bool       # Whether to use confirmation timeframe
    use_filter: bool        # Whether to use filter timeframe
    
    # === PRIMARY TIMEFRAME RULES ===
    primary_rule_type: str          # 'momentum_level', 'momentum_vs_eq', 'price_vs_ma', 'ma_alignment'
    primary_rule_value: float       # Threshold
    primary_rule_operator: str      # '<', '>', '<=', '>='
    primary_rule_ma_period: str     # 'ma_20', 'ma_50', 'ma_200'
    
    # === CONFIRMATION TIMEFRAME RULES ===
    confirm_rule_type: str
    confirm_rule_value: float
    confirm_rule_operator: str
    confirm_rule_ma_period: str
    
    # === FILTER TIMEFRAME RULES ===
    filter_rule_type: str
    filter_rule_value: float
    filter_rule_operator: str
    filter_rule_ma_period: str
    
    # === LOGIC COMBINATION ===
    entry_logic: str        # 'ALL', 'ANY', 'PRIMARY_AND_CONFIRM', 'PRIMARY_ONLY', etc.
    exit_logic: str
    
    # === ENTRY CONDITIONS ===
    entry_momentum_min: float       # Minimum momentum to enter (0-100)
    entry_momentum_max: float       # Maximum momentum to enter (0-100)
    entry_requires_ma_alignment: bool  # Require MA alignment on any timeframe
    entry_ma_alignment_timeframe: str  # Which timeframe must have MA alignment
    
    # === EXIT CONDITIONS ===
    exit_on_opposite_signal: bool   # Exit when opposite signal appears
    exit_on_momentum_threshold: bool
    exit_momentum_value: float      # Exit when momentum crosses this
    exit_momentum_direction: str    # 'below', 'above'
    
    # === POSITION SIZING ===
    position_size_type: str         # 'fixed', 'momentum_scaled', 'volatility_adjusted'
    position_size_base: float       # Base position size (10-100%)
    position_scale_factor: float    # How much to scale based on signal strength
    
    # === RISK MANAGEMENT ===
    stop_loss_type: str             # 'fixed', 'trailing', 'ma_based', 'momentum_based'
    stop_loss_pct: float            # Stop loss percentage (1-20%)
    stop_loss_ma_period: str        # 'ma_20', 'ma_50', 'ma_200' if MA-based
    
    take_profit_enabled: bool
    take_profit_pct: float          # Take profit percentage (2-50%)
    
    trailing_stop_enabled: bool
    trailing_stop_activation: float # Profit % to activate trailing stop
    trailing_stop_distance: float   # Trailing distance %
    
    # === TIME MANAGEMENT ===
    min_hold_bars: int              # Minimum hold (primary timeframe bars)
    max_hold_bars: int              # Maximum hold
    time_based_exit: bool
    
    # === DIRECTION ===
    allow_long: bool
    allow_short: bool
    
    # === ADVANCED MULTI-TIMEFRAME FEATURES ===
    require_timeframe_agreement: bool  # All selected timeframes must agree
    disagreement_action: str           # 'skip', 'reduce_size', 'use_primary_only'
    
    momentum_cascade_required: bool    # Require momentum trending across timeframes
    cascade_direction: str             # 'higher_tf_to_lower', 'lower_tf_to_higher', 'any'
    
    use_htf_trend_filter: bool        # Use higher timeframe as trend filter
    htf_filter_timeframe: str         # Which timeframe for trend filter
    htf_filter_type: str              # 'ma_alignment', 'momentum_direction', 'price_vs_ma'
    
    # === PYRAMID/SCALING ===
    pyramid_enabled: bool
    pyramid_on_timeframe: str         # Which timeframe triggers pyramid
    pyramid_max_adds: int             # Max additional entries (1-3)
    pyramid_size_mult: float          # Size multiplier for adds (0.25-1.0)

# ==============================================================================
# RULE EVALUATION FOR MULTI-TIMEFRAME
# ==============================================================================

def evaluate_mtf_rule(rule_type: str, rule_value: float, rule_operator: str,
                      df: pd.DataFrame, idx: int, ma_period: str) -> bool:
    """
    Evaluate a rule on a specific timeframe
    
    Args:
        rule_type: Type of rule
        rule_value: Threshold value
        rule_operator: Comparison operator
        df: DataFrame for this timeframe
        idx: Current index
        ma_period: MA period to use ('ma_20', 'ma_50', 'ma_200')
    
    Returns:
        bool: Whether rule is satisfied
    """
    if idx >= len(df):
        return False
    
    row = df.iloc[idx]
    
    # Get indicator value based on rule type
    if rule_type == 'momentum_level':
        indicator = row['momentum']
    
    elif rule_type == 'momentum_vs_eq':
        indicator = row['momentum'] - row['equilibrium']
    
    elif rule_type == 'price_vs_ma':
        if ma_period == 'ma_20':
            indicator = row['price_vs_ma20']
        elif ma_period == 'ma_50':
            indicator = row['price_vs_ma50']
        elif ma_period == 'ma_200':
            indicator = row['price_vs_ma200']
        else:
            return False
    
    elif rule_type == 'ma_alignment':
        # For boolean rules, use value as threshold (0.5 = must be true)
        indicator = 1.0 if row['ma_aligned_bull'] else 0.0
        rule_value = 0.5  # Threshold for "true"
    
    elif rule_type == 'momentum_direction':
        # Check if momentum is rising
        if idx > 0:
            prev_momentum = df.iloc[idx-1]['momentum']
            indicator = 1.0 if row['momentum'] > prev_momentum else 0.0
        else:
            indicator = 0.5
        rule_value = 0.5
    
    elif rule_type == 'price_above_ma':
        if ma_period == 'ma_20':
            indicator = 1.0 if row['close'] > row['ma_20'] else 0.0
        elif ma_period == 'ma_50':
            indicator = 1.0 if row['close'] > row['ma_50'] else 0.0
        elif ma_period == 'ma_200':
            indicator = 1.0 if row['close'] > row['ma_200'] else 0.0
        else:
            return False
        rule_value = 0.5
    
    else:
        return False
    
    # Apply operator
    if rule_operator == '<':
        return indicator < rule_value
    elif rule_operator == '>':
        return indicator > rule_value
    elif rule_operator == '<=':
        return indicator <= rule_value
    elif rule_operator == '>=':
        return indicator >= rule_value
    else:
        return False

def check_ma_alignment(df: pd.DataFrame, idx: int, direction: str = 'bull') -> bool:
    """Check if MAs are aligned on this timeframe"""
    if idx >= len(df):
        return False
    
    row = df.iloc[idx]
    
    if direction == 'bull':
        return row['ma_aligned_bull']
    else:
        return row['ma_aligned_bear']

# ==============================================================================
# BACKTESTER FOR MULTI-TIMEFRAME STRATEGY
# ==============================================================================

def backtest_mtf_strategy(gene: MTFUnrestrictedGene, 
                          mtf_data: Dict[str, pd.DataFrame],
                          initial_capital: float = 10000) -> Dict:
    """
    Backtest multi-timeframe strategy
    
    Uses primary timeframe for execution timing
    Other timeframes for confirmation/filtering
    """
    # Get primary timeframe data
    if gene.primary_timeframe not in mtf_data:
        return {'return': -100, 'trades': 0, 'win_rate': 0}
    
    primary_df = mtf_data[gene.primary_timeframe]
    
    # Trading state
    capital = initial_capital
    position = 0
    position_side = None  # 'long' or 'short'
    entry_price = 0
    entry_idx = 0
    
    trades = []
    equity_curve = [initial_capital]
    
    # Iterate through primary timeframe
    for i in range(100, len(primary_df)):  # Start after enough history
        current_price = primary_df.iloc[i]['close']
        current_time = primary_df.iloc[i]['timestamp']
        
        # === FIND CORRESPONDING INDICES IN OTHER TIMEFRAMES ===
        # Match by timestamp (get closest bar)
        confirm_idx = None
        filter_idx = None
        
        if gene.use_confirm and gene.confirm_timeframe in mtf_data:
            confirm_df = mtf_data[gene.confirm_timeframe]
            confirm_idx = (confirm_df['timestamp'] <= current_time).sum() - 1
            if confirm_idx < 0 or confirm_idx >= len(confirm_df):
                confirm_idx = None
        
        if gene.use_filter and gene.filter_timeframe in mtf_data:
            filter_df = mtf_data[gene.filter_timeframe]
            filter_idx = (filter_df['timestamp'] <= current_time).sum() - 1
            if filter_idx < 0 or filter_idx >= len(filter_df):
                filter_idx = None
        
        # === EVALUATE ENTRY CONDITIONS ===
        if position == 0:
            # Evaluate primary timeframe rule
            primary_signal = False
            if gene.use_primary:
                primary_signal = evaluate_mtf_rule(
                    gene.primary_rule_type,
                    gene.primary_rule_value,
                    gene.primary_rule_operator,
                    primary_df,
                    i,
                    gene.primary_rule_ma_period
                )
            
            # Evaluate confirmation timeframe rule
            confirm_signal = True  # Default to true if not used
            if gene.use_confirm and confirm_idx is not None:
                confirm_signal = evaluate_mtf_rule(
                    gene.confirm_rule_type,
                    gene.confirm_rule_value,
                    gene.confirm_rule_operator,
                    mtf_data[gene.confirm_timeframe],
                    confirm_idx,
                    gene.confirm_rule_ma_period
                )
            
            # Evaluate filter timeframe rule
            filter_signal = True  # Default to true if not used
            if gene.use_filter and filter_idx is not None:
                filter_signal = evaluate_mtf_rule(
                    gene.filter_rule_type,
                    gene.filter_rule_value,
                    gene.filter_rule_operator,
                    mtf_data[gene.filter_timeframe],
                    filter_idx,
                    gene.filter_rule_ma_period
                )
            
            # Combine signals based on entry logic
            entry_signal = False
            
            if gene.entry_logic == 'ALL':
                entry_signal = primary_signal and confirm_signal and filter_signal
            elif gene.entry_logic == 'ANY':
                entry_signal = primary_signal or confirm_signal or filter_signal
            elif gene.entry_logic == 'PRIMARY_AND_CONFIRM':
                entry_signal = primary_signal and confirm_signal
            elif gene.entry_logic == 'PRIMARY_ONLY':
                entry_signal = primary_signal
            elif gene.entry_logic == 'PRIMARY_OR_CONFIRM':
                entry_signal = primary_signal or confirm_signal
            
            # Additional entry filters
            current_momentum = primary_df.iloc[i]['momentum']
            
            if entry_signal:
                # Check momentum range
                if not (gene.entry_momentum_min <= current_momentum <= gene.entry_momentum_max):
                    entry_signal = False
                
                # Check MA alignment requirement
                if gene.entry_requires_ma_alignment:
                    alignment_tf = gene.entry_ma_alignment_timeframe
                    if alignment_tf in mtf_data:
                        alignment_df = mtf_data[alignment_tf]
                        alignment_idx = (alignment_df['timestamp'] <= current_time).sum() - 1
                        if alignment_idx >= 0 and alignment_idx < len(alignment_df):
                            if not check_ma_alignment(alignment_df, alignment_idx, 'bull'):
                                entry_signal = False
                
                # Check HTF trend filter
                if gene.use_htf_trend_filter:
                    htf = gene.htf_filter_timeframe
                    if htf in mtf_data:
                        htf_df = mtf_data[htf]
                        htf_idx = (htf_df['timestamp'] <= current_time).sum() - 1
                        if htf_idx >= 0 and htf_idx < len(htf_df):
                            if gene.htf_filter_type == 'ma_alignment':
                                if not check_ma_alignment(htf_df, htf_idx, 'bull'):
                                    entry_signal = False
            
            # ENTER POSITION
            if entry_signal and (gene.allow_long or gene.allow_short):
                # Determine position size
                base_size = gene.position_size_base / 100.0
                
                if gene.position_size_type == 'momentum_scaled':
                    # Scale based on momentum strength
                    momentum_strength = abs(current_momentum - 50) / 50.0
                    size_mult = 1.0 + (momentum_strength * gene.position_scale_factor)
                    base_size *= size_mult
                
                # Calculate shares
                shares = int((capital * base_size) / current_price)
                
                if shares > 0:
                    position = shares
                    entry_price = current_price
                    entry_idx = i
                    
                    # Determine direction (for now, assume long when momentum > 50)
                    position_side = 'long' if current_momentum > 50 else 'short'
                    
                    # Deduct capital
                    cost = shares * current_price * 1.001  # 0.1% commission
                    capital -= cost
        
        # === EVALUATE EXIT CONDITIONS ===
        elif position > 0:
            current_momentum = primary_df.iloc[i]['momentum']
            bars_held = i - entry_idx
            
            # Calculate unrealized P&L
            if position_side == 'long':
                unrealized_pnl_pct = (current_price / entry_price - 1) * 100
            else:  # short
                unrealized_pnl_pct = (entry_price / current_price - 1) * 100
            
            exit_signal = False
            exit_reason = ""
            
            # Time-based exit
            if gene.time_based_exit:
                if bars_held < gene.min_hold_bars:
                    pass  # Don't exit yet
                elif bars_held >= gene.max_hold_bars:
                    exit_signal = True
                    exit_reason = "max_hold"
            
            # Stop loss
            if unrealized_pnl_pct <= -gene.stop_loss_pct:
                exit_signal = True
                exit_reason = "stop_loss"
            
            # Take profit
            if gene.take_profit_enabled and unrealized_pnl_pct >= gene.take_profit_pct:
                exit_signal = True
                exit_reason = "take_profit"
            
            # Exit on momentum threshold
            if gene.exit_on_momentum_threshold:
                if gene.exit_momentum_direction == 'below' and current_momentum < gene.exit_momentum_value:
                    exit_signal = True
                    exit_reason = "momentum_threshold"
                elif gene.exit_momentum_direction == 'above' and current_momentum > gene.exit_momentum_value:
                    exit_signal = True
                    exit_reason = "momentum_threshold"
            
            # Exit on opposite signal
            if gene.exit_on_opposite_signal:
                # Evaluate exit rules (similar to entry)
                primary_exit = evaluate_mtf_rule(
                    gene.primary_rule_type,
                    gene.primary_rule_value,
                    gene.primary_rule_operator,
                    primary_df,
                    i,
                    gene.primary_rule_ma_period
                )
                
                # If signal is opposite to position side
                if (position_side == 'long' and not primary_exit) or \
                   (position_side == 'short' and primary_exit):
                    exit_signal = True
                    exit_reason = "opposite_signal"
            
            # EXIT POSITION
            if exit_signal:
                proceeds = position * current_price * 0.999  # 0.1% commission
                capital += proceeds
                
                pnl = proceeds - (position * entry_price)
                pnl_pct = (pnl / (position * entry_price)) * 100
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'bars_held': bars_held,
                    'side': position_side,
                    'reason': exit_reason
                })
                
                position = 0
                position_side = None
                entry_price = 0
        
        # Track equity
        if position > 0:
            if position_side == 'long':
                current_value = capital + position * current_price
            else:
                current_value = capital + position * (2 * entry_price - current_price)
            equity_curve.append(current_value)
        else:
            equity_curve.append(capital)
    
    # Close any remaining position
    if position > 0:
        final_price = primary_df.iloc[-1]['close']
        proceeds = position * final_price * 0.999
        capital += proceeds
        pnl = proceeds - (position * entry_price)
        pnl_pct = (pnl / (position * entry_price)) * 100
        trades.append({
            'entry_price': entry_price,
            'exit_price': final_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'bars_held': len(primary_df) - entry_idx,
            'side': position_side,
            'reason': 'end_of_data'
        })
    
    # Calculate metrics
    final_capital = capital
    total_return = (final_capital / initial_capital - 1) * 100
    
    if len(trades) == 0:
        return {
            'return': -10,  # Penalty for no trades
            'trades': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'sharpe': 0,
            'max_drawdown': 0
        }
    
    winning_trades = [t for t in trades if t['pnl'] > 0]
    losing_trades = [t for t in trades if t['pnl'] <= 0]
    
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
    
    # Calculate Sharpe ratio
    returns = pd.Series(equity_curve).pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    
    # Calculate max drawdown
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
# GENETIC ALGORITHM ENGINE
# ==============================================================================

def create_random_mtf_gene() -> MTFUnrestrictedGene:
    """Create a random multi-timeframe gene (CRYPTO-OPTIMIZED)"""
    
    # CRYPTO FIX: Remove 1min (too noisy), focus on 15m-1d
    timeframes = ['5min', '15min', '1hour', '4hour', '1day']
    
    # CRYPTO FIX: Favor momentum rules over MA rules (crypto moves fast)
    rule_types = [
        'momentum_level', 'momentum_level',      # 40% weight
        'momentum_vs_eq', 'momentum_vs_eq',      # 30% weight  
        'momentum_direction',                     # 10% weight
        'price_vs_ma',                           # 10% weight
        'ma_alignment',                          # 10% weight
    ]
    operators = ['<', '>', '<=', '>=']
    
    # CRYPTO FIX: Remove MA 200 (too slow for crypto)
    ma_periods = ['ma_20', 'ma_50']
    
    return MTFUnrestrictedGene(
        # Timeframe selection
        primary_timeframe=random.choice(timeframes),
        confirm_timeframe=random.choice(timeframes),
        filter_timeframe=random.choice(timeframes),
        
        use_primary=True,  # CRYPTO FIX: Always use primary
        use_confirm=random.choice([True, False]),
        use_filter=random.choice([True, False, False, False]),  # CRYPTO FIX: Rarely use filter
        
        # Primary rules
        primary_rule_type=random.choice(rule_types),
        primary_rule_value=random.uniform(0, 100),
        primary_rule_operator=random.choice(operators),
        primary_rule_ma_period=random.choice(ma_periods),
        
        # Confirm rules
        confirm_rule_type=random.choice(rule_types),
        confirm_rule_value=random.uniform(0, 100),
        confirm_rule_operator=random.choice(operators),
        confirm_rule_ma_period=random.choice(ma_periods),
        
        # Filter rules
        filter_rule_type=random.choice(rule_types),
        filter_rule_value=random.uniform(0, 100),
        filter_rule_operator=random.choice(operators),
        filter_rule_ma_period=random.choice(ma_periods),
        
        # Logic - CRYPTO FIX: Favor simpler logic
        entry_logic=random.choice([
            'PRIMARY_ONLY', 'PRIMARY_ONLY', 'PRIMARY_ONLY',           # 40% weight
            'PRIMARY_OR_CONFIRM', 'PRIMARY_OR_CONFIRM',               # 30% weight
            'PRIMARY_AND_CONFIRM',                                     # 15% weight
            'ANY',                                                     # 10% weight
            'ALL'                                                      # 5% weight
        ]),
        exit_logic=random.choice(['PRIMARY_ONLY', 'PRIMARY_ONLY', 'ANY']),  # Simpler exits
        
        # Entry conditions - CRYPTO FIX: Ensure valid ranges and wider acceptance
        entry_momentum_min=random.uniform(0, 30),      # Oversold zone
        entry_momentum_max=random.uniform(70, 100),    # Overbought zone  
        entry_requires_ma_alignment=random.random() < 0.2,  # CRYPTO FIX: Only 20% use MA alignment
        entry_ma_alignment_timeframe=random.choice(timeframes),
        
        # Exit conditions
        exit_on_opposite_signal=random.choice([True, False]),
        exit_on_momentum_threshold=random.choice([True, False]),
        exit_momentum_value=random.uniform(30, 70),
        exit_momentum_direction=random.choice(['below', 'above']),
        
        # Position sizing
        position_size_type=random.choice(['fixed', 'momentum_scaled', 'volatility_adjusted']),
        position_size_base=random.uniform(50, 95),
        position_scale_factor=random.uniform(0.1, 0.5),
        
        # Risk management
        stop_loss_type=random.choice(['fixed', 'trailing', 'ma_based', 'momentum_based']),
        stop_loss_pct=random.uniform(2, 15),
        stop_loss_ma_period=random.choice(ma_periods),
        
        take_profit_enabled=random.choice([True, False]),
        take_profit_pct=random.uniform(5, 30),
        
        trailing_stop_enabled=random.choice([True, False]),
        trailing_stop_activation=random.uniform(3, 10),
        trailing_stop_distance=random.uniform(2, 8),
        
        # Time management
        min_hold_bars=random.randint(1, 10),
        max_hold_bars=random.randint(20, 200),
        time_based_exit=random.choice([True, False]),
        
        # Direction
        allow_long=random.choice([True, True, True, False]),  # Bias toward long
        allow_short=random.choice([True, False, False, False]),
        
        # Advanced MTF features - CRYPTO FIX: Disable most advanced features (too strict)
        require_timeframe_agreement=random.random() < 0.1,  # Only 10% require agreement
        disagreement_action=random.choice(['use_primary_only', 'reduce_size', 'skip']),
        
        momentum_cascade_required=random.random() < 0.1,  # Only 10% require cascade
        cascade_direction=random.choice(['higher_tf_to_lower', 'lower_tf_to_higher', 'any']),
        
        use_htf_trend_filter=random.random() < 0.2,  # CRYPTO FIX: Only 20% use HTF filter
        htf_filter_timeframe=random.choice(['4hour', '1day']),
        htf_filter_type=random.choice(['momentum_direction', 'price_vs_ma', 'ma_alignment']),
        
        # Pyramid
        pyramid_enabled=random.choice([True, False, False]),
        pyramid_on_timeframe=random.choice(timeframes),
        pyramid_max_adds=random.randint(1, 3),
        pyramid_size_mult=random.uniform(0.25, 0.75),
    )

def mutate_mtf_gene(gene: MTFUnrestrictedGene, mutation_rate: float = 0.15) -> MTFUnrestrictedGene:
    """Mutate a multi-timeframe gene"""
    import copy
    new_gene = copy.deepcopy(gene)
    
    timeframes = ['1min', '5min', '15min', '1hour', '4hour', '1day']
    rule_types = ['momentum_level', 'momentum_vs_eq', 'price_vs_ma', 'ma_alignment', 
                  'momentum_direction', 'price_above_ma']
    operators = ['<', '>', '<=', '>=']
    ma_periods = ['ma_20', 'ma_50', 'ma_200']
    
    # Mutate each field with probability
    if random.random() < mutation_rate:
        new_gene.primary_timeframe = random.choice(timeframes)
    if random.random() < mutation_rate:
        new_gene.confirm_timeframe = random.choice(timeframes)
    if random.random() < mutation_rate:
        new_gene.filter_timeframe = random.choice(timeframes)
    
    if random.random() < mutation_rate:
        new_gene.use_primary = random.choice([True, False])
    if random.random() < mutation_rate:
        new_gene.use_confirm = random.choice([True, False])
    if random.random() < mutation_rate:
        new_gene.use_filter = random.choice([True, False])
    
    # Mutate rules
    if random.random() < mutation_rate:
        new_gene.primary_rule_type = random.choice(rule_types)
    if random.random() < mutation_rate:
        new_gene.primary_rule_value += random.uniform(-20, 20)
        new_gene.primary_rule_value = np.clip(new_gene.primary_rule_value, 0, 100)
    if random.random() < mutation_rate:
        new_gene.primary_rule_operator = random.choice(operators)
    
    # Mutate position sizing
    if random.random() < mutation_rate:
        new_gene.position_size_base += random.uniform(-20, 20)
        new_gene.position_size_base = np.clip(new_gene.position_size_base, 10, 100)
    
    # Mutate stop loss
    if random.random() < mutation_rate:
        new_gene.stop_loss_pct += random.uniform(-5, 5)
        new_gene.stop_loss_pct = np.clip(new_gene.stop_loss_pct, 1, 20)
    
    # Mutate take profit
    if random.random() < mutation_rate:
        new_gene.take_profit_pct += random.uniform(-10, 10)
        new_gene.take_profit_pct = np.clip(new_gene.take_profit_pct, 2, 50)
    
    # Mutate time limits
    if random.random() < mutation_rate:
        new_gene.min_hold_bars = max(1, new_gene.min_hold_bars + random.randint(-3, 3))
    if random.random() < mutation_rate:
        new_gene.max_hold_bars = max(10, new_gene.max_hold_bars + random.randint(-50, 50))
    
    return new_gene

def crossover_mtf_genes(parent1: MTFUnrestrictedGene, parent2: MTFUnrestrictedGene) -> MTFUnrestrictedGene:
    """Crossover two multi-timeframe genes"""
    import copy
    
    # Random crossover point
    child = copy.deepcopy(parent1)
    
    # Randomly inherit from either parent
    if random.random() < 0.5:
        child.primary_timeframe = parent2.primary_timeframe
    if random.random() < 0.5:
        child.confirm_timeframe = parent2.confirm_timeframe
    if random.random() < 0.5:
        child.filter_timeframe = parent2.filter_timeframe
    
    if random.random() < 0.5:
        child.primary_rule_type = parent2.primary_rule_type
        child.primary_rule_value = parent2.primary_rule_value
        child.primary_rule_operator = parent2.primary_rule_operator
    
    if random.random() < 0.5:
        child.entry_logic = parent2.entry_logic
    
    if random.random() < 0.5:
        child.position_size_base = parent2.position_size_base
        child.position_size_type = parent2.position_size_type
    
    if random.random() < 0.5:
        child.stop_loss_pct = parent2.stop_loss_pct
        child.take_profit_pct = parent2.take_profit_pct
    
    return child

def run_mtf_ga(mtf_data: Dict[str, pd.DataFrame],
               population_size: int = 50,
               generations: int = 100,
               elite_size: int = 5) -> List[Tuple[MTFUnrestrictedGene, Dict]]:
    """
    Run genetic algorithm to discover best multi-timeframe strategies
    """
    print(f"\n🧬 Starting GA: {population_size} population, {generations} generations")
    
    # Create initial population
    print("\n📊 Creating initial population...")
    population = [create_random_mtf_gene() for _ in range(population_size)]
    
    best_ever_fitness = -float('inf')
    best_ever_gene = None
    best_ever_results = None
    
    generation_best = []
    
    for gen in range(generations):
        print(f"\n{'='*80}")
        print(f"Generation {gen+1}/{generations}")
        print(f"{'='*80}")
        
        # Evaluate fitness for each gene
        fitness_scores = []
        
        for idx, gene in enumerate(population):
            results = backtest_mtf_strategy(gene, mtf_data)
            
            # Fitness function (can be customized)
            fitness = results['return']
            
            # Bonus for more trades (avoid overfitting)
            if results['trades'] >= 10:
                fitness += 5
            
            # Bonus for high win rate
            if results['win_rate'] >= 55:
                fitness += results['win_rate'] * 0.1
            
            # Penalty for too few trades
            if results['trades'] < 5:
                fitness -= 20
            
            # Bonus for good Sharpe
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
            print(f"   Sharpe: {best_ever_results['sharpe']:.2f}")
        
        # Print generation stats
        print(f"\n📊 Generation {gen+1} Stats:")
        print(f"   Best Fitness: {current_best[1]:.2f}")
        print(f"   Best Return: {current_best[2]['return']:.2f}%")
        print(f"   Avg Fitness: {np.mean([f[1] for f in fitness_scores]):.2f}")
        top_5_returns = [f"{f[2]['return']:.1f}%" for f in fitness_scores[:5]]
        print(f"   Top 5 Returns: {top_5_returns}")
        
        # Selection and reproduction
        # Keep elite
        new_population = [gene for gene, _, _ in fitness_scores[:elite_size]]
        
        # Create offspring
        while len(new_population) < population_size:
            # Tournament selection
            tournament_size = 5
            tournament = random.sample(fitness_scores[:population_size//2], tournament_size)
            parent1 = max(tournament, key=lambda x: x[1])[0]
            
            tournament = random.sample(fitness_scores[:population_size//2], tournament_size)
            parent2 = max(tournament, key=lambda x: x[1])[0]
            
            # Crossover
            child = crossover_mtf_genes(parent1, parent2)
            
            # Mutate
            child = mutate_mtf_gene(child, mutation_rate=0.15)
            
            new_population.append(child)
        
        population = new_population
    
    print(f"\n{'='*80}")
    print("🏆 GENETIC ALGORITHM COMPLETE!")
    print(f"{'='*80}")
    print(f"\nBest Ever Fitness: {best_ever_fitness:.2f}")
    print(f"Best Ever Return: {best_ever_results['return']:.2f}%")
    print(f"Best Ever Trades: {best_ever_results['trades']}")
    print(f"Best Ever Win Rate: {best_ever_results['win_rate']:.1f}%")
    print(f"Best Ever Sharpe: {best_ever_results['sharpe']:.2f}")
    
    return generation_best, best_ever_gene, best_ever_results

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == '__main__':
    print("\n📥 Downloading multi-timeframe data...")
    
    provider = MultiTimeframeDataProvider()
    
    # Download data for SPY
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # Last 2 months for intraday
    
    print(f"   Symbol: {symbol}")
    print(f"   Period: {start_date.date()} to {end_date.date()}")
    print(f"   Timeframes: 1min, 5min, 15min, 1h, 4h, 1d\n")
    
    mtf_data = provider.download_multi_timeframe(symbol, start_date, end_date)
    
    if len(mtf_data) < 3:
        print("❌ Not enough timeframe data downloaded. Exiting.")
        sys.exit(1)
    
    print(f"\n✅ Downloaded {len(mtf_data)} timeframes")
    
    # Run GA
    generation_best, best_gene, best_results = run_mtf_ga(
        mtf_data,
        population_size=50,
        generations=50,  # Start with 50, increase to 100 later
        elite_size=5
    )
    
    # Print best strategy details
    print(f"\n{'='*80}")
    print("🎯 BEST STRATEGY DISCOVERED")
    print(f"{'='*80}")
    print(f"\n📊 Performance:")
    print(f"   Total Return: {best_results['return']:.2f}%")
    print(f"   Total Trades: {best_results['trades']}")
    print(f"   Win Rate: {best_results['win_rate']:.1f}%")
    print(f"   Avg Win: {best_results['avg_win']:.2f}%")
    print(f"   Avg Loss: {best_results['avg_loss']:.2f}%")
    print(f"   Sharpe Ratio: {best_results['sharpe']:.2f}")
    print(f"   Max Drawdown: {best_results['max_drawdown']:.2f}%")
    print(f"   Final Capital: ${best_results['final_capital']:,.2f}")
    
    print(f"\n🔧 Strategy Configuration:")
    print(f"   Primary TF: {best_gene.primary_timeframe}")
    print(f"   Confirm TF: {best_gene.confirm_timeframe} (Used: {best_gene.use_confirm})")
    print(f"   Filter TF: {best_gene.filter_timeframe} (Used: {best_gene.use_filter})")
    print(f"\n   Entry Logic: {best_gene.entry_logic}")
    print(f"   Primary Rule: {best_gene.primary_rule_type} {best_gene.primary_rule_operator} {best_gene.primary_rule_value:.1f}")
    print(f"   Momentum Range: {best_gene.entry_momentum_min:.1f} - {best_gene.entry_momentum_max:.1f}")
    print(f"\n   Position Size: {best_gene.position_size_base:.1f}% ({best_gene.position_size_type})")
    print(f"   Stop Loss: {best_gene.stop_loss_pct:.1f}% ({best_gene.stop_loss_type})")
    print(f"   Take Profit: {best_gene.take_profit_pct:.1f}% (Enabled: {best_gene.take_profit_enabled})")
    print(f"\n   Hold Time: {best_gene.min_hold_bars} - {best_gene.max_hold_bars} bars")
    print(f"   Direction: Long={best_gene.allow_long}, Short={best_gene.allow_short}")
    
    print(f"\n   HTF Filter: {best_gene.use_htf_trend_filter}")
    if best_gene.use_htf_trend_filter:
        print(f"      Filter TF: {best_gene.htf_filter_timeframe}")
        print(f"      Filter Type: {best_gene.htf_filter_type}")
    
    # Save best strategy
    print(f"\n💾 Saving best strategy...")
    
    strategy_dict = {
        'performance': best_results,
        'gene': {
            'primary_timeframe': best_gene.primary_timeframe,
            'confirm_timeframe': best_gene.confirm_timeframe,
            'filter_timeframe': best_gene.filter_timeframe,
            'use_primary': best_gene.use_primary,
            'use_confirm': best_gene.use_confirm,
            'use_filter': best_gene.use_filter,
            'primary_rule_type': best_gene.primary_rule_type,
            'primary_rule_value': best_gene.primary_rule_value,
            'primary_rule_operator': best_gene.primary_rule_operator,
            'entry_logic': best_gene.entry_logic,
            'entry_momentum_min': best_gene.entry_momentum_min,
            'entry_momentum_max': best_gene.entry_momentum_max,
            'position_size_base': best_gene.position_size_base,
            'position_size_type': best_gene.position_size_type,
            'stop_loss_pct': best_gene.stop_loss_pct,
            'stop_loss_type': best_gene.stop_loss_type,
            'take_profit_enabled': best_gene.take_profit_enabled,
            'take_profit_pct': best_gene.take_profit_pct,
            'min_hold_bars': best_gene.min_hold_bars,
            'max_hold_bars': best_gene.max_hold_bars,
            'allow_long': best_gene.allow_long,
            'allow_short': best_gene.allow_short,
            'use_htf_trend_filter': best_gene.use_htf_trend_filter,
            'htf_filter_timeframe': best_gene.htf_filter_timeframe,
            'htf_filter_type': best_gene.htf_filter_type,
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('best_mtf_unrestricted_strategy.json', 'w') as f:
        json.dump(strategy_dict, f, indent=2)
    
    print("✅ Strategy saved to: best_mtf_unrestricted_strategy.json")
    
    print(f"\n{'='*80}")
    print("✅ GA COMPLETE!")
    print(f"{'='*80}")
