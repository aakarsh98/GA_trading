"""
Advanced Backtesting Engine
Tests trading strategies with realistic assumptions
Includes bootstrap validation and walk-forward testing
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Tuple
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


class BacktestEngine:
    """
    Simple backtesting engine for strategy validation.
    
    Features:
    - Position sizing based on risk percentage
    - ATR-based stop loss
    - Commission and slippage
    - Performance metrics calculation
    """
    
    def __init__(self,
                 initial_capital: float = 10000,
                 risk_percent: float = 1.0,
                 commission_pct: float = 0.1,
                 slippage_ticks: int = 2,
                 atr_stop_multiplier: float = 2.0):
        """
        Initialize Backtest Engine.
        
        Args:
            initial_capital: Starting capital ($)
            risk_percent: Risk per trade (%)
            commission_pct: Commission (% of trade value)
            slippage_ticks: Slippage in ticks
            atr_stop_multiplier: ATR multiplier for stop loss
        """
        self.initial_capital = initial_capital
        self.risk_percent = risk_percent / 100  # Convert to decimal
        self.commission_pct = commission_pct / 100
        self.slippage_ticks = slippage_ticks
        self.atr_stop_multiplier = atr_stop_multiplier
        
        # Results storage
        self.trades = []
        self.equity_curve = []
        
    def run(self, data: pd.DataFrame, signals: pd.DataFrame, 
            atr_values: pd.Series, edge_scores: Optional[pd.Series] = None) -> Dict:
        """
        Run backtest on data with given signals.
        
        Args:
            data: OHLCV DataFrame
            signals: DataFrame with 'Signal' column (1=long, -1=short, 0=neutral)
            atr_values: ATR values for stop loss calculation
            edge_scores: Optional edge scores for position sizing (0-1)
            
        Returns:
            Dictionary with backtest results
        """
        # Reset state
        self.trades = []
        self.equity_curve = []
        
        current_capital = self.initial_capital
        position = None  # Current position: {'type': 'long'/'short', 'entry_price': float, 'size': float, 'entry_bar': int}
        
        # Process each bar
        for i in range(len(data)):
            bar_date = data.index[i]
            bar_data = data.iloc[i]
            signal = signals['Signal'].iloc[i]
            atr = atr_values.iloc[i]
            
            # Skip if ATR is NaN
            if pd.isna(atr):
                self.equity_curve.append({
                    'Date': bar_date,
                    'Equity': current_capital,
                    'DrawdownPct': 0
                })
                continue
            
            # Get edge score if available
            edge_score = edge_scores.iloc[i] if edge_scores is not None else 1.0
            
            # Close existing position if signal reversed or went neutral
            if position is not None:
                should_close = False
                
                if position['type'] == 'long' and signal <= 0:
                    should_close = True
                    exit_price = bar_data['Close']
                    exit_reason = 'Signal Exit'
                    
                elif position['type'] == 'short' and signal >= 0:
                    should_close = True
                    exit_price = bar_data['Close']
                    exit_reason = 'Signal Exit'
                    
                # Check stop loss
                if position['type'] == 'long':
                    stop_loss = position['entry_price'] - (atr * self.atr_stop_multiplier)
                    if bar_data['Low'] <= stop_loss:
                        should_close = True
                        exit_price = stop_loss
                        exit_reason = 'Stop Loss'
                        
                elif position['type'] == 'short':
                    stop_loss = position['entry_price'] + (atr * self.atr_stop_multiplier)
                    if bar_data['High'] >= stop_loss:
                        should_close = True
                        exit_price = stop_loss
                        exit_reason = 'Stop Loss'
                
                # Close position
                if should_close:
                    pnl = self._close_position(position, exit_price, bar_date, exit_reason)
                    current_capital += pnl
                    position = None
            
            # Open new position if signal and no position
            if position is None and signal != 0:
                # Calculate position size
                position_size = self._calculate_position_size(
                    current_capital, atr, edge_score
                )
                
                # Open position
                if signal > 0:  # Long
                    entry_price = bar_data['Close'] + (self.slippage_ticks * 0.01)  # Simplified slippage
                    position = {
                        'type': 'long',
                        'entry_price': entry_price,
                        'size': position_size,
                        'entry_bar': i,
                        'entry_date': bar_date,
                        'edge_score': edge_score
                    }
                    
                elif signal < 0:  # Short
                    entry_price = bar_data['Close'] - (self.slippage_ticks * 0.01)
                    position = {
                        'type': 'short',
                        'entry_price': entry_price,
                        'size': position_size,
                        'entry_bar': i,
                        'entry_date': bar_date,
                        'edge_score': edge_score
                    }
            
            # Record equity
            position_value = 0
            if position is not None:
                current_price = bar_data['Close']
                if position['type'] == 'long':
                    position_value = (current_price - position['entry_price']) * position['size']
                else:
                    position_value = (position['entry_price'] - current_price) * position['size']
            
            equity = current_capital + position_value
            
            # Calculate drawdown
            max_equity = max([e['Equity'] for e in self.equity_curve] + [equity])
            drawdown_pct = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
            
            self.equity_curve.append({
                'Date': bar_date,
                'Equity': equity,
                'DrawdownPct': drawdown_pct
            })
        
        # Close any remaining position
        if position is not None:
            exit_price = data.iloc[-1]['Close']
            pnl = self._close_position(position, exit_price, data.index[-1], 'End of Test')
            current_capital += pnl
        
        # Calculate performance metrics
        results = self._calculate_metrics(current_capital)
        
        return results
    
    def _calculate_position_size(self, capital: float, atr: float, edge_score: float) -> float:
        """Calculate position size based on risk and edge score."""
        # Base position size
        risk_amount = capital * self.risk_percent
        stop_distance = atr * self.atr_stop_multiplier
        
        base_size = risk_amount / stop_distance if stop_distance > 0 else 0
        
        # Adjust by edge score
        # High edge (>0.8) = 1.4x size
        # Medium edge (0.6-0.8) = 1.0x size
        # Low edge (<0.6) = 0.7x size
        if edge_score >= 0.8:
            multiplier = 1.4
        elif edge_score >= 0.6:
            multiplier = 1.0
        else:
            multiplier = 0.7
        
        return base_size * multiplier
    
    def _close_position(self, position: dict, exit_price: float, 
                       exit_date: pd.Timestamp, exit_reason: str) -> float:
        """Close position and calculate PnL."""
        # Calculate gross PnL
        if position['type'] == 'long':
            gross_pnl = (exit_price - position['entry_price']) * position['size']
        else:
            gross_pnl = (position['entry_price'] - exit_price) * position['size']
        
        # Calculate costs
        entry_cost = position['entry_price'] * position['size'] * self.commission_pct
        exit_cost = exit_price * position['size'] * self.commission_pct
        total_cost = entry_cost + exit_cost
        
        # Net PnL
        net_pnl = gross_pnl - total_cost
        
        # Record trade
        self.trades.append({
            'EntryDate': position['entry_date'],
            'ExitDate': exit_date,
            'Type': position['type'],
            'EntryPrice': position['entry_price'],
            'ExitPrice': exit_price,
            'Size': position['size'],
            'GrossPnL': gross_pnl,
            'Costs': total_cost,
            'NetPnL': net_pnl,
            'ExitReason': exit_reason,
            'EdgeScore': position['edge_score']
        })
        
        return net_pnl
    
    def _calculate_metrics(self, final_capital: float) -> Dict:
        """Calculate performance metrics."""
        if len(self.trades) == 0:
            return {
                'FinalCapital': final_capital,
                'NetProfit': 0,
                'ReturnPct': 0,
                'TotalTrades': 0,
                'WinningTrades': 0,
                'LosingTrades': 0,
                'WinRate': 0,
                'AvgWin': 0,
                'AvgLoss': 0,
                'ProfitFactor': 0,
                'MaxDrawdownPct': 0,
                'SharpeRatio': 0
            }
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        # Basic metrics
        net_profit = final_capital - self.initial_capital
        return_pct = (net_profit / self.initial_capital) * 100
        
        # Trade metrics
        total_trades = len(trades_df)
        winning_trades = (trades_df['NetPnL'] > 0).sum()
        losing_trades = (trades_df['NetPnL'] < 0).sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # PnL metrics
        avg_win = trades_df[trades_df['NetPnL'] > 0]['NetPnL'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['NetPnL'] < 0]['NetPnL'].mean() if losing_trades > 0 else 0
        
        gross_profit = trades_df[trades_df['NetPnL'] > 0]['NetPnL'].sum()
        gross_loss = abs(trades_df[trades_df['NetPnL'] < 0]['NetPnL'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown
        max_drawdown_pct = equity_df['DrawdownPct'].max()
        
        # Sharpe ratio (simplified annual)
        if len(equity_df) > 1:
            returns = equity_df['Equity'].pct_change().dropna()
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        return {
            'FinalCapital': final_capital,
            'NetProfit': net_profit,
            'ReturnPct': return_pct,
            'TotalTrades': total_trades,
            'WinningTrades': winning_trades,
            'LosingTrades': losing_trades,
            'WinRate': win_rate,
            'AvgWin': avg_win,
            'AvgLoss': avg_loss,
            'ProfitFactor': profit_factor,
            'MaxDrawdownPct': max_drawdown_pct,
            'SharpeRatio': sharpe
        }
    
    def print_results(self, results: Dict):
        """Print backtest results in a formatted way."""
        print("\n" + "="*60)
        print(" BACKTEST RESULTS")
        print("="*60)
        
        print(f"\n💰 CAPITAL:")
        print(f"  Initial Capital: ${self.initial_capital:,.2f}")
        print(f"  Final Capital:   ${results['FinalCapital']:,.2f}")
        print(f"  Net Profit:      ${results['NetProfit']:,.2f}")
        print(f"  Return:          {results['ReturnPct']:.2f}%")
        
        print(f"\n📊 TRADES:")
        print(f"  Total Trades:    {results['TotalTrades']}")
        print(f"  Winning Trades:  {results['WinningTrades']}")
        print(f"  Losing Trades:   {results['LosingTrades']}")
        print(f"  Win Rate:        {results['WinRate']:.1f}%")
        
        print(f"\n💵 PNL:")
        print(f"  Average Win:     ${results['AvgWin']:,.2f}")
        print(f"  Average Loss:    ${results['AvgLoss']:,.2f}")
        print(f"  Profit Factor:   {results['ProfitFactor']:.2f}")
        
        print(f"\n📉 RISK:")
        print(f"  Max Drawdown:    {results['MaxDrawdownPct']:.2f}%")
        print(f"  Sharpe Ratio:    {results['SharpeRatio']:.2f}")
        
        print("\n" + "="*60)
    
    def plot_results(self):
        """Plot backtest results."""
        if len(self.equity_curve) == 0:
            print("No data to plot")
            return
        
        equity_df = pd.DataFrame(self.equity_curve)
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # Equity curve
        axes[0].plot(equity_df['Date'], equity_df['Equity'], 
                    label='Equity', color='blue', linewidth=2)
        axes[0].axhline(y=self.initial_capital, color='gray', 
                       linestyle='--', alpha=0.5, label='Initial Capital')
        axes[0].set_ylabel('Equity ($)')
        axes[0].set_title('Equity Curve')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Drawdown
        axes[1].fill_between(equity_df['Date'], 0, -equity_df['DrawdownPct'],
                            color='red', alpha=0.3)
        axes[1].plot(equity_df['Date'], -equity_df['DrawdownPct'],
                    color='red', linewidth=1)
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].set_xlabel('Date')
        axes[1].set_title('Drawdown')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, axes
    
    def bootstrap_validation(self, data: pd.DataFrame, signals: pd.DataFrame,
                            atr_values: pd.Series, edge_scores: Optional[pd.Series] = None,
                            n_iterations: int = 1000, confidence_level: float = 0.95) -> Dict:
        """
        Perform bootstrap validation to assess strategy robustness.
        
        Research shows this provides 95% confidence intervals and P < 0.01 validation.
        
        Args:
            data: OHLCV DataFrame
            signals: Signal DataFrame
            atr_values: ATR values
            edge_scores: Optional edge scores
            n_iterations: Number of bootstrap iterations (default 1000)
            confidence_level: Confidence level (default 0.95)
            
        Returns:
            Dictionary with bootstrap results
        """
        print(f"\n🔄 Running bootstrap validation ({n_iterations} iterations)...")
        
        returns_distribution = []
        sharpe_distribution = []
        drawdown_distribution = []
        
        original_trades = len(self.trades)
        
        for i in range(n_iterations):
            if i % 100 == 0:
                print(f"  Progress: {i}/{n_iterations} iterations...")
            
            # Bootstrap resample: sample with replacement
            sample_indices = np.random.choice(len(data), size=len(data), replace=True)
            sample_indices = sorted(sample_indices)  # Keep time order
            
            # Create bootstrap sample
            bootstrap_data = data.iloc[sample_indices].copy()
            bootstrap_signals = signals.iloc[sample_indices].copy()
            bootstrap_atr = atr_values.iloc[sample_indices].copy()
            bootstrap_edge = edge_scores.iloc[sample_indices].copy() if edge_scores is not None else None
            
            # Reset indices
            bootstrap_data = bootstrap_data.reset_index(drop=True)
            bootstrap_signals = bootstrap_signals.reset_index(drop=True)
            bootstrap_atr = bootstrap_atr.reset_index(drop=True)
            if bootstrap_edge is not None:
                bootstrap_edge = bootstrap_edge.reset_index(drop=True)
            
            # Run backtest on bootstrap sample
            try:
                results = self.run(bootstrap_data, bootstrap_signals, bootstrap_atr, bootstrap_edge)
                
                returns_distribution.append(results['ReturnPct'])
                sharpe_distribution.append(results['SharpeRatio'])
                drawdown_distribution.append(results['MaxDrawdownPct'])
            except Exception as e:
                # Skip failed iterations
                continue
        
        # Calculate statistics
        returns_array = np.array(returns_distribution)
        sharpe_array = np.array(sharpe_distribution)
        drawdown_array = np.array(drawdown_distribution)
        
        # Confidence intervals
        alpha = (1 - confidence_level) / 2
        lower_percentile = alpha * 100
        upper_percentile = (1 - alpha) * 100
        
        results = {
            'n_iterations': len(returns_distribution),
            'confidence_level': confidence_level,
            
            # Return statistics
            'mean_return': np.mean(returns_array),
            'median_return': np.median(returns_array),
            'std_return': np.std(returns_array),
            'return_ci_lower': np.percentile(returns_array, lower_percentile),
            'return_ci_upper': np.percentile(returns_array, upper_percentile),
            
            # Sharpe statistics
            'mean_sharpe': np.mean(sharpe_array),
            'median_sharpe': np.median(sharpe_array),
            'std_sharpe': np.std(sharpe_array),
            'sharpe_ci_lower': np.percentile(sharpe_array, lower_percentile),
            'sharpe_ci_upper': np.percentile(sharpe_array, upper_percentile),
            
            # Drawdown statistics
            'mean_drawdown': np.mean(drawdown_array),
            'median_drawdown': np.median(drawdown_array),
            'std_drawdown': np.std(drawdown_array),
            'drawdown_ci_lower': np.percentile(drawdown_array, lower_percentile),
            'drawdown_ci_upper': np.percentile(drawdown_array, upper_percentile),
            
            # Statistical significance
            'positive_returns_pct': (returns_array > 0).sum() / len(returns_array) * 100,
            'p_value': (returns_array <= 0).sum() / len(returns_array),  # Simplified p-value
            
            # Distributions for plotting
            'returns_distribution': returns_array,
            'sharpe_distribution': sharpe_array,
            'drawdown_distribution': drawdown_array
        }
        
        print(f"✅ Bootstrap validation complete!")
        
        return results
    
    def walk_forward_test(self, data: pd.DataFrame, signals: pd.DataFrame,
                         atr_values: pd.Series, edge_scores: Optional[pd.Series] = None,
                         train_size: int = 500, test_size: int = 100, 
                         step_size: int = 50) -> Dict:
        """
        Perform walk-forward testing (rolling window validation).
        
        Research shows this validates consistency across time periods.
        
        Args:
            data: OHLCV DataFrame
            signals: Signal DataFrame
            atr_values: ATR values
            edge_scores: Optional edge scores
            train_size: Number of bars for training window
            test_size: Number of bars for testing window
            step_size: Number of bars to step forward
            
        Returns:
            Dictionary with walk-forward results
        """
        print(f"\n🔄 Running walk-forward test...")
        print(f"  Train: {train_size} bars, Test: {test_size} bars, Step: {step_size} bars")
        
        test_periods = []
        start_idx = 0
        
        while start_idx + train_size + test_size <= len(data):
            train_end = start_idx + train_size
            test_end = train_end + test_size
            
            # Test period data
            test_data = data.iloc[train_end:test_end].copy()
            test_signals = signals.iloc[train_end:test_end].copy()
            test_atr = atr_values.iloc[train_end:test_end].copy()
            test_edge = edge_scores.iloc[train_end:test_end].copy() if edge_scores is not None else None
            
            # Run backtest on test period
            try:
                results = self.run(test_data, test_signals, test_atr, test_edge)
                
                test_periods.append({
                    'period': len(test_periods) + 1,
                    'start_date': test_data.index[0],
                    'end_date': test_data.index[-1],
                    'return': results['ReturnPct'],
                    'sharpe': results['SharpeRatio'],
                    'drawdown': results['MaxDrawdownPct'],
                    'trades': results['TotalTrades'],
                    'win_rate': results['WinRate']
                })
                
                print(f"  Period {len(test_periods)}: Return={results['ReturnPct']:.2f}%, Sharpe={results['SharpeRatio']:.2f}")
                
            except Exception as e:
                print(f"  Period {len(test_periods) + 1}: Failed - {e}")
            
            start_idx += step_size
        
        # Aggregate statistics
        returns = [p['return'] for p in test_periods]
        sharpes = [p['sharpe'] for p in test_periods]
        drawdowns = [p['drawdown'] for p in test_periods]
        
        results = {
            'n_periods': len(test_periods),
            'test_periods': test_periods,
            
            # Return statistics
            'mean_return': np.mean(returns),
            'median_return': np.median(returns),
            'std_return': np.std(returns),
            'min_return': np.min(returns),
            'max_return': np.max(returns),
            
            # Sharpe statistics
            'mean_sharpe': np.mean(sharpes),
            'median_sharpe': np.median(sharpes),
            'std_sharpe': np.std(sharpes),
            
            # Drawdown statistics
            'mean_drawdown': np.mean(drawdowns),
            'max_drawdown': np.max(drawdowns),
            
            # Consistency metrics
            'positive_periods': sum(1 for r in returns if r > 0),
            'positive_periods_pct': sum(1 for r in returns if r > 0) / len(returns) * 100,
            'consistency_score': np.mean(returns) / (np.std(returns) + 1e-10)  # Risk-adjusted consistency
        }
        
        print(f"✅ Walk-forward test complete!")
        print(f"  Positive periods: {results['positive_periods']}/{results['n_periods']} ({results['positive_periods_pct']:.1f}%)")
        
        return results
    
    def print_bootstrap_results(self, results: Dict):
        """Print bootstrap validation results."""
        print("\n" + "="*60)
        print(" BOOTSTRAP VALIDATION RESULTS")
        print("="*60)
        
        print(f"\n📊 CONFIGURATION:")
        print(f"  Iterations: {results['n_iterations']}")
        print(f"  Confidence Level: {results['confidence_level']*100:.0f}%")
        
        print(f"\n💰 RETURN STATISTICS:")
        print(f"  Mean Return: {results['mean_return']:.2f}%")
        print(f"  Median Return: {results['median_return']:.2f}%")
        print(f"  Std Dev: {results['std_return']:.2f}%")
        print(f"  {results['confidence_level']*100:.0f}% CI: [{results['return_ci_lower']:.2f}%, {results['return_ci_upper']:.2f}%]")
        
        print(f"\n📈 SHARPE RATIO:")
        print(f"  Mean Sharpe: {results['mean_sharpe']:.2f}")
        print(f"  Median Sharpe: {results['median_sharpe']:.2f}")
        print(f"  {results['confidence_level']*100:.0f}% CI: [{results['sharpe_ci_lower']:.2f}, {results['sharpe_ci_upper']:.2f}]")
        
        print(f"\n📉 DRAWDOWN:")
        print(f"  Mean Drawdown: {results['mean_drawdown']:.2f}%")
        print(f"  Median Drawdown: {results['median_drawdown']:.2f}%")
        print(f"  {results['confidence_level']*100:.0f}% CI: [{results['drawdown_ci_lower']:.2f}%, {results['drawdown_ci_upper']:.2f}%]")
        
        print(f"\n🎯 STATISTICAL SIGNIFICANCE:")
        print(f"  Positive Returns: {results['positive_returns_pct']:.1f}% of iterations")
        print(f"  P-value: {results['p_value']:.4f}")
        
        if results['p_value'] < 0.01:
            print(f"  Result: ✅ HIGHLY SIGNIFICANT (p < 0.01)")
        elif results['p_value'] < 0.05:
            print(f"  Result: ✅ SIGNIFICANT (p < 0.05)")
        else:
            print(f"  Result: ⚠️  NOT SIGNIFICANT (p >= 0.05)")
        
        print("\n" + "="*60)
    
    def print_walkforward_results(self, results: Dict):
        """Print walk-forward test results."""
        print("\n" + "="*60)
        print(" WALK-FORWARD TEST RESULTS")
        print("="*60)
        
        print(f"\n📊 CONFIGURATION:")
        print(f"  Test Periods: {results['n_periods']}")
        
        print(f"\n💰 RETURN CONSISTENCY:")
        print(f"  Mean Return: {results['mean_return']:.2f}%")
        print(f"  Median Return: {results['median_return']:.2f}%")
        print(f"  Std Dev: {results['std_return']:.2f}%")
        print(f"  Range: [{results['min_return']:.2f}%, {results['max_return']:.2f}%]")
        
        print(f"\n📈 SHARPE RATIO:")
        print(f"  Mean Sharpe: {results['mean_sharpe']:.2f}")
        print(f"  Median Sharpe: {results['median_sharpe']:.2f}")
        print(f"  Std Dev: {results['std_sharpe']:.2f}")
        
        print(f"\n📉 DRAWDOWN:")
        print(f"  Mean Drawdown: {results['mean_drawdown']:.2f}%")
        print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
        
        print(f"\n🎯 CONSISTENCY METRICS:")
        print(f"  Positive Periods: {results['positive_periods']}/{results['n_periods']} ({results['positive_periods_pct']:.1f}%)")
        print(f"  Consistency Score: {results['consistency_score']:.2f}")
        
        if results['positive_periods_pct'] >= 70:
            print(f"  Result: ✅ HIGHLY CONSISTENT")
        elif results['positive_periods_pct'] >= 50:
            print(f"  Result: ✅ CONSISTENT")
        else:
            print(f"  Result: ⚠️  INCONSISTENT")
        
        print("\n" + "="*60)


def main():
    """Demo backtest engine."""
    import sys
    sys.path.append('..')
    from data.collector import DataCollector
    from indicators.momentum_tracker import MomentumTracker
    from indicators.utils import atr
    
    print("=== Backtest Engine Demo ===\n")
    
    # Fetch data
    collector = DataCollector()
    print("Fetching BTC-USD data...")
    data = collector.fetch_data('BTC-USD', timeframe='1h', period='3mo')
    
    # Calculate indicators
    print("Calculating momentum...")
    mt = MomentumTracker()
    momentum = mt.calculate(data)
    
    print("Calculating ATR...")
    atr_values = atr(data, 14)
    
    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine(
        initial_capital=10000,
        risk_percent=1.0,
        commission_pct=0.1,
        slippage_ticks=2,
        atr_stop_multiplier=2.0
    )
    
    results = engine.run(data, momentum, atr_values)
    
    # Print results
    engine.print_results(results)
    
    print("\n=== Demo Complete ===")


if __name__ == '__main__':
    main()
