"""
META-REINFORCEMENT LEARNING & FIRM-SPECIFIC MOMENTUM TEST
Tests adaptive parameter optimization and firm vs systematic momentum decomposition

Sources:
- "An adaptive quantitative trading strategy optimization framework" (2024)
- "Firm-specific versus systematic momentum" (SSRN, 2024)

✅ NOW USING YOUR ACTUAL MOMENTUM TRACKER

Expected: 49-51% annual returns (Meta-RL), improved edge detection (Firm-specific)
"""
import sys
import os
sys.path.append(os.path.dirname(__file__) + '/utils')

# Import YOUR actual momentum tracker
from actual_momentum_tracker import calculate_momentum_indicator as calc_momentum_full, backtest_baseline


import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("\n" + "🧠"*40)
print(" "*5 + "META-RL & FIRM-SPECIFIC MOMENTUM TEST")
print(" "*10 + "Adaptive Optimization + Momentum Decomposition")
print("🧠"*40)


def calculate_momentum_indicator(df):
    """Calculate momentum using YOUR exact algorithm"""
    result = calc_momentum_full(df, length=7, threshold=2.0)
    return result['momentum']


def calculate_firm_specific_momentum(asset_data, market_data):
    """
    Decompose momentum into firm-specific and systematic components
    
    Args:
        asset_data: Individual asset data
        market_data: Market index data (e.g., SPY)
    
    Returns:
        DataFrame with momentum decomposition
    """
    print(f"\n📊 Calculating firm-specific momentum decomposition...")
    
    # Calculate returns
    asset_returns = asset_data['close'].pct_change()
    market_returns = market_data['close'].pct_change()
    
    results = []
    window = 20
    
    for i in range(window, len(asset_returns)):
        # Systematic component (market-driven)
        systematic_momentum = market_returns.iloc[i]
        
        # Firm-specific component (idiosyncratic)
        firm_momentum = asset_returns.iloc[i] - systematic_momentum
        
        # Calculate rolling correlations
        asset_window = asset_returns.iloc[i-window:i]
        market_window = market_returns.iloc[i-window:i]
        
        beta = np.cov(asset_window, market_window)[0, 1] / np.var(market_window) if np.var(market_window) > 0 else 1.0
        
        # Firm dominance: firm momentum >> systematic momentum
        firm_dominance = abs(firm_momentum) > abs(systematic_momentum) * 2.0
        
        # Edge confidence based on firm-specific strength
        atr_estimate = abs(asset_returns.iloc[i-window:i]).mean()
        edge_confidence = min(abs(firm_momentum) / atr_estimate, 2.0) if atr_estimate > 0 else 0
        
        results.append({
            'SystematicMomentum': systematic_momentum,
            'FirmMomentum': firm_momentum,
            'Beta': beta,
            'FirmDominance': firm_dominance,
            'EdgeConfidence': edge_confidence,
            'FirmSpecificEdge': firm_dominance and abs(firm_momentum) > 0.01
        })
    
    return pd.DataFrame(results)


class MetaReinforcementLearning:
    """
    Meta-Reinforcement Learning for adaptive parameter optimization
    
    Tracks strategy performance and adapts parameters dynamically
    """
    
    def __init__(self, initial_risk=0.02, adaptation_rate=0.1):
        self.risk_percent = initial_risk
        self.adaptation_rate = adaptation_rate
        self.performance_history = []
        self.risk_history = [initial_risk]
        self.confidence_level = 1.0
        
    def update(self, recent_pnl, recent_trades, market_volatility):
        """
        Update meta-learning parameters based on recent performance
        
        Args:
            recent_pnl: Recent P&L
            recent_trades: Number of recent trades
            market_volatility: Current market volatility
        
        Returns:
            Updated risk multiplier
        """
        self.performance_history.append(recent_pnl)
        
        # Meta-learning: Analyze recent performance
        if len(self.performance_history) >= 20:
            recent_performance = sum(self.performance_history[-20:])
            baseline_performance = sum(self.performance_history[-40:-20]) if len(self.performance_history) >= 40 else 0
            
            # Performance improvement
            if baseline_performance != 0:
                performance_ratio = recent_performance / baseline_performance
            else:
                performance_ratio = 1.0
            
            # Increase confidence if performing well
            if performance_ratio > 1.1:  # 10% better
                confidence_change = min((performance_ratio - 1.0), 0.5)
                self.confidence_level = min(self.confidence_level + confidence_change * self.adaptation_rate, 2.0)
            # Decrease confidence if underperforming
            elif performance_ratio < 0.9:  # 10% worse
                confidence_degradation = max(performance_ratio - 1.0, -0.3)
                self.confidence_level = max(self.confidence_level + confidence_degradation * self.adaptation_rate, 0.5)
        
        # Adapt to volatility
        volatility_adjustment = 1.0 / (1.0 + market_volatility) if market_volatility > 0 else 1.0
        
        # Calculate risk multiplier
        risk_multiplier = self.confidence_level * volatility_adjustment
        self.risk_history.append(self.risk_percent * risk_multiplier)
        
        return risk_multiplier
    
    def get_adapted_risk(self):
        """Get current adapted risk level"""
        return self.risk_history[-1]
    
    def get_stats(self):
        """Get meta-learning statistics"""
        return {
            'confidence_level': self.confidence_level,
            'current_risk': self.risk_history[-1],
            'mean_risk': np.mean(self.risk_history),
            'performance_trend': np.mean(self.performance_history[-10:]) if len(self.performance_history) >= 10 else 0
        }


def backtest_with_meta_rl_firm(asset_data, market_data, initial_capital=10000):
    """Backtest with meta-RL and firm-specific momentum"""
    print(f"\n🔄 Running backtest with Meta-RL and firm-specific momentum...")
    
    momentum = calculate_momentum_indicator(asset_data)
    firm_specific = calculate_firm_specific_momentum(asset_data, market_data)
    
    # Initialize meta-RL
    meta_rl = MetaReinforcementLearning(initial_risk=0.02, adaptation_rate=0.1)
    
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(100, len(asset_data)):
        # Align firm-specific data
        firm_idx = i - 20
        if firm_idx >= len(firm_specific):
            break
        
        # Get firm-specific signals
        firm_edge = firm_specific.iloc[firm_idx]['FirmSpecificEdge']
        firm_dominance = firm_specific.iloc[firm_idx]['FirmDominance']
        edge_confidence = firm_specific.iloc[firm_idx]['EdgeConfidence']
        
        # Momentum signal
        momentum_bullish = momentum[i] > momentum[i-1]
        
        # Calculate market volatility (ATR)
        high_slice = asset_data['high'].iloc[max(0, i-14):i]
        low_slice = asset_data['low'].iloc[max(0, i-14):i]
        close_slice = asset_data['close'].iloc[max(0, i-14):i]
        
        tr1 = high_slice - low_slice
        tr2 = abs(high_slice - close_slice.shift(1))
        tr3 = abs(low_slice - close_slice.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()
        market_volatility = atr / asset_data['close'].iloc[i] * 100
        
        # Update meta-RL
        recent_pnl = sum([t['pnl'] for t in trades[-5:] if 'pnl' in t]) if len(trades) >= 5 else 0
        recent_trade_count = len([t for t in trades[-20:] if t['type'] == 'EXIT'])
        risk_multiplier = meta_rl.update(recent_pnl, recent_trade_count, market_volatility)
        
        current_price = asset_data['close'].iloc[i]
        
        # Entry: Combine firm-specific edge with meta-RL adaptation
        if position == 0 and momentum_bullish and firm_edge:
            # Adaptive risk based on meta-RL
            adapted_risk = meta_rl.get_adapted_risk()
            
            # Further adjust by edge confidence
            position_multiplier = 1.0 + (edge_confidence * 0.3)
            risk_amount = capital * adapted_risk * position_multiplier
            
            position_size = risk_amount / (atr * 2.0)
            position = position_size
            entry_price = current_price
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
            
            trades.append({
                'entry_bar': i,
                'entry_price': entry_price,
                'adapted_risk': adapted_risk,
                'risk_multiplier': risk_multiplier,
                'edge_confidence': edge_confidence,
                'type': 'ENTRY'
            })
        
        # Exit
        elif position > 0:
            if current_price <= stop_loss:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'STOP', 'type': 'EXIT'})
                position = 0
            elif current_price >= take_profit:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'TARGET', 'type': 'EXIT'})
                position = 0
            elif not firm_edge or not momentum_bullish:
                pnl = (current_price - entry_price) * position
                capital += pnl
                trades.append({'exit_bar': i, 'pnl': pnl, 'exit_reason': 'SIGNAL', 'type': 'EXIT'})
                position = 0
        
        equity_curve.append(capital)
    
    return {
        'final_capital': capital,
        'trades': trades,
        'equity_curve': equity_curve,
        'meta_rl_stats': meta_rl.get_stats()
    }


def run_meta_rl_test():
    """Main test function"""
    
    print("\n📥 Downloading data...")
    qqq = yf.download('QQQ', start='2022-01-01', progress=False)
    spy = yf.download('SPY', start='2022-01-01', progress=False)
    
    for df in [qqq, spy]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() for col in df.columns]
        else:
            df.columns = df.columns.str.lower()
    
    print(f"✅ QQQ: {len(qqq)} bars")
    print(f"✅ SPY: {len(spy)} bars")
    
    # Calculate firm-specific momentum
    firm_results = calculate_firm_specific_momentum(qqq, spy)
    
    print(f"\n📈 FIRM-SPECIFIC MOMENTUM RESULTS:")
    print(f"  Mean Systematic:        {firm_results['SystematicMomentum'].mean()*100:.4f}%")
    print(f"  Mean Firm-Specific:     {firm_results['FirmMomentum'].mean()*100:.4f}%")
    print(f"  Mean Beta:              {firm_results['Beta'].mean():.3f}")
    print(f"  Firm Dominance:         {firm_results['FirmDominance'].sum()} bars "
          f"({firm_results['FirmDominance'].sum()/len(firm_results)*100:.1f}%)")
    print(f"  Firm-Specific Edges:    {firm_results['FirmSpecificEdge'].sum()} bars "
          f"({firm_results['FirmSpecificEdge'].sum()/len(firm_results)*100:.1f}%)")
    print(f"  Mean Edge Confidence:   {firm_results['EdgeConfidence'].mean():.3f}")
    
    # Run backtests
    print("\n" + "="*80)
    print("  BASELINE BACKTEST")
    print("="*80)
    baseline = backtest_baseline_test(qqq)
    print(f"\n  Final Capital:  ${baseline['final_capital']:,.2f}")
    print(f"  Total Return:   {(baseline['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:   {len(baseline.get('trades', []))}")
    
    print("\n" + "="*80)
    print("  ENHANCED BACKTEST (Meta-RL + Firm-Specific)")
    print("="*80)
    enhanced = backtest_with_meta_rl_firm(qqq, spy)
    print(f"\n  Final Capital:  ${enhanced['final_capital']:,.2f}")
    print(f"  Total Return:   {(enhanced['final_capital']/10000-1)*100:.2f}%")
    print(f"  Total Trades:   {len(enhanced.get('trades', []))}")
    
    print(f"\n  Meta-RL Statistics:")
    print(f"    Confidence Level:   {enhanced['meta_rl_stats']['confidence_level']:.3f}")
    print(f"    Current Risk:       {enhanced['meta_rl_stats']['current_risk']*100:.2f}%")
    print(f"    Mean Risk:          {enhanced['meta_rl_stats']['mean_risk']*100:.2f}%")
    print(f"    Performance Trend:  ${enhanced['meta_rl_stats']['performance_trend']:.2f}")
    
    # Comparison
    baseline_ret = (baseline['final_capital']/10000-1)*100
    enhanced_ret = (enhanced['final_capital']/10000-1)*100
    improvement = enhanced_ret - baseline_ret
    
    print(f"\n" + "="*80)
    print("  COMPARISON")
    print("="*80)
    print(f"  Baseline Return:     {baseline_ret:.2f}%")
    print(f"  Enhanced Return:     {enhanced_ret:.2f}%")
    print(f"  Improvement:         {improvement:+.2f}%")
    
    # Annualized returns
    years = len(qqq) / 252
    baseline_annual = ((baseline['final_capital']/10000)**(1/years) - 1) * 100
    enhanced_annual = ((enhanced['final_capital']/10000)**(1/years) - 1) * 100
    
    print(f"\n  Baseline Annual:     {baseline_annual:.2f}%")
    print(f"  Enhanced Annual:     {enhanced_annual:.2f}%")
    print(f"  Expected from research: 49-51% annual returns")
    
    baseline_returns = np.diff(baseline['equity_curve']) / baseline['equity_curve'][:-1]
    enhanced_returns = np.diff(enhanced['equity_curve']) / enhanced['equity_curve'][:-1]
    
    baseline_sharpe = np.mean(baseline_returns) / np.std(baseline_returns) * np.sqrt(252) if np.std(baseline_returns) > 0 else 0
    enhanced_sharpe = np.mean(enhanced_returns) / np.std(enhanced_returns) * np.sqrt(252) if np.std(enhanced_returns) > 0 else 0
    
    print(f"\n  Baseline Sharpe:     {baseline_sharpe:.2f}")
    print(f"  Enhanced Sharpe:     {enhanced_sharpe:.2f}")
    if baseline_sharpe > 0:
        print(f"  Sharpe Improvement:  {(enhanced_sharpe/baseline_sharpe-1)*100:+.1f}%")
    
    print(f"\n✅ Test complete!")
    
    return {'firm_specific': firm_results, 'baseline': baseline, 'enhanced': enhanced}


def backtest_baseline_test(data, initial_capital=10000, risk_pct=2.0):
    """Baseline backtest using YOUR actual momentum tracker"""
    result = backtest_baseline(data, initial_capital=initial_capital, 
                               risk_pct=risk_pct, long_only=True)
    return result


if __name__ == '__main__':
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = run_meta_rl_test()
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
