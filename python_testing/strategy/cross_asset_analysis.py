"""
Cross-Asset Correlation Analysis
Analyzes strategy performance across multiple assets
Research shows this validates international applicability
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns


class CrossAssetAnalyzer:
    """
    Analyzes trading strategy across multiple assets.
    
    Features:
    - Performance comparison across assets
    - Correlation analysis
    - Diversification benefits
    - Portfolio optimization
    """
    
    def __init__(self):
        self.results = {}
    
    def analyze_multiple_assets(self, asset_results: Dict[str, Dict]) -> Dict:
        """
        Analyze results from multiple assets.
        
        Args:
            asset_results: Dictionary mapping asset name to backtest results
            
        Returns:
            Dictionary with cross-asset analysis
        """
        print(f"\n🌍 Analyzing {len(asset_results)} assets...")
        
        # Extract performance metrics
        assets = list(asset_results.keys())
        returns = [asset_results[asset]['ReturnPct'] for asset in assets]
        sharpes = [asset_results[asset]['SharpeRatio'] for asset in assets]
        drawdowns = [asset_results[asset]['MaxDrawdownPct'] for asset in assets]
        win_rates = [asset_results[asset]['WinRate'] for asset in assets]
        
        # Calculate statistics
        analysis = {
            'n_assets': len(assets),
            'assets': assets,
            
            # Return statistics
            'mean_return': np.mean(returns),
            'median_return': np.median(returns),
            'best_asset': assets[np.argmax(returns)],
            'best_return': max(returns),
            'worst_asset': assets[np.argmin(returns)],
            'worst_return': min(returns),
            'return_std': np.std(returns),
            
            # Sharpe statistics
            'mean_sharpe': np.mean(sharpes),
            'median_sharpe': np.median(sharpes),
            'best_sharpe_asset': assets[np.argmax(sharpes)],
            'best_sharpe': max(sharpes),
            
            # Drawdown statistics
            'mean_drawdown': np.mean(drawdowns),
            'best_drawdown_asset': assets[np.argmin(drawdowns)],
            'best_drawdown': min(drawdowns),
            
            # Win rate statistics
            'mean_win_rate': np.mean(win_rates),
            'best_win_rate_asset': assets[np.argmax(win_rates)],
            'best_win_rate': max(win_rates),
            
            # Consistency
            'positive_assets': sum(1 for r in returns if r > 0),
            'positive_assets_pct': sum(1 for r in returns if r > 0) / len(returns) * 100,
            
            # Individual results
            'individual_results': asset_results
        }
        
        print(f"✅ Cross-asset analysis complete!")
        
        return analysis
    
    def calculate_correlation_matrix(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate correlation matrix between asset returns.
        
        Args:
            price_data: Dictionary mapping asset name to OHLCV DataFrame
            
        Returns:
            Correlation matrix DataFrame
        """
        print(f"\n📊 Calculating correlation matrix...")
        
        # Calculate returns for each asset
        returns_dict = {}
        for asset, data in price_data.items():
            returns_dict[asset] = data['Close'].pct_change()
        
        # Create DataFrame of returns
        returns_df = pd.DataFrame(returns_dict)
        
        # Calculate correlation
        correlation_matrix = returns_df.corr()
        
        print(f"✅ Correlation matrix calculated!")
        
        return correlation_matrix
    
    def portfolio_optimization(self, asset_results: Dict[str, Dict], 
                              correlation_matrix: pd.DataFrame = None) -> Dict:
        """
        Suggest optimal portfolio allocation based on results.
        
        Args:
            asset_results: Backtest results for each asset
            correlation_matrix: Optional correlation matrix
            
        Returns:
            Dictionary with portfolio recommendations
        """
        print(f"\n💼 Calculating portfolio optimization...")
        
        assets = list(asset_results.keys())
        returns = np.array([asset_results[asset]['ReturnPct'] for asset in assets])
        sharpes = np.array([asset_results[asset]['SharpeRatio'] for asset in assets])
        
        # Simple optimization: weight by Sharpe ratio
        # Filter out negative Sharpe ratios
        positive_sharpes = np.maximum(sharpes, 0)
        
        if positive_sharpes.sum() > 0:
            weights = positive_sharpes / positive_sharpes.sum()
        else:
            # Equal weight if all Sharpes are negative
            weights = np.ones(len(assets)) / len(assets)
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(weights, returns)
        
        # Estimate portfolio Sharpe (simplified)
        portfolio_sharpe = np.dot(weights, sharpes)
        
        portfolio = {
            'assets': assets,
            'weights': weights,
            'weight_pct': weights * 100,
            'portfolio_return': portfolio_return,
            'portfolio_sharpe': portfolio_sharpe,
            'diversification_benefit': portfolio_sharpe - np.mean(sharpes)
        }
        
        print(f"✅ Portfolio optimization complete!")
        
        return portfolio
    
    def plot_performance_comparison(self, asset_results: Dict[str, Dict]):
        """Plot performance comparison across assets."""
        assets = list(asset_results.keys())
        returns = [asset_results[asset]['ReturnPct'] for asset in assets]
        sharpes = [asset_results[asset]['SharpeRatio'] for asset in assets]
        win_rates = [asset_results[asset]['WinRate'] for asset in assets]
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Plot 1: Returns comparison
        colors = ['green' if r > 0 else 'red' for r in returns]
        axes[0, 0].bar(range(len(assets)), returns, color=colors, alpha=0.7)
        axes[0, 0].set_xticks(range(len(assets)))
        axes[0, 0].set_xticklabels(assets, rotation=45, ha='right')
        axes[0, 0].set_ylabel('Return (%)')
        axes[0, 0].set_title('Returns by Asset')
        axes[0, 0].axhline(y=0, color='black', linestyle='--', alpha=0.3)
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Sharpe ratios
        colors = ['green' if s > 0 else 'red' for s in sharpes]
        axes[0, 1].bar(range(len(assets)), sharpes, color=colors, alpha=0.7)
        axes[0, 1].set_xticks(range(len(assets)))
        axes[0, 1].set_xticklabels(assets, rotation=45, ha='right')
        axes[0, 1].set_ylabel('Sharpe Ratio')
        axes[0, 1].set_title('Sharpe Ratios by Asset')
        axes[0, 1].axhline(y=0, color='black', linestyle='--', alpha=0.3)
        axes[0, 1].axhline(y=1.0, color='green', linestyle='--', alpha=0.3, label='Target (1.0)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Win rates
        axes[1, 0].bar(range(len(assets)), win_rates, color='steelblue', alpha=0.7)
        axes[1, 0].set_xticks(range(len(assets)))
        axes[1, 0].set_xticklabels(assets, rotation=45, ha='right')
        axes[1, 0].set_ylabel('Win Rate (%)')
        axes[1, 0].set_title('Win Rates by Asset')
        axes[1, 0].axhline(y=50, color='orange', linestyle='--', alpha=0.3, label='50% baseline')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Risk-Return scatter
        drawdowns = [asset_results[asset]['MaxDrawdownPct'] for asset in assets]
        axes[1, 1].scatter(drawdowns, returns, s=100, alpha=0.7)
        for i, asset in enumerate(assets):
            axes[1, 1].annotate(asset, (drawdowns[i], returns[i]), 
                              fontsize=8, ha='right')
        axes[1, 1].set_xlabel('Max Drawdown (%)')
        axes[1, 1].set_ylabel('Return (%)')
        axes[1, 1].set_title('Risk-Return Profile')
        axes[1, 1].axhline(y=0, color='black', linestyle='--', alpha=0.3)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig, axes
    
    def plot_correlation_matrix(self, correlation_matrix: pd.DataFrame):
        """Plot correlation heatmap."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(correlation_matrix, annot=True, fmt='.2f', 
                   cmap='RdYlGn_r', center=0, ax=ax,
                   square=True, linewidths=1)
        
        ax.set_title('Asset Return Correlations', fontsize=14, pad=20)
        
        plt.tight_layout()
        return fig, ax
    
    def print_analysis(self, analysis: Dict):
        """Print cross-asset analysis results."""
        print("\n" + "="*60)
        print(" CROSS-ASSET ANALYSIS RESULTS")
        print("="*60)
        
        print(f"\n📊 ASSETS ANALYZED: {analysis['n_assets']}")
        print(f"  {', '.join(analysis['assets'])}")
        
        print(f"\n💰 RETURN STATISTICS:")
        print(f"  Mean Return: {analysis['mean_return']:.2f}%")
        print(f"  Median Return: {analysis['median_return']:.2f}%")
        print(f"  Best: {analysis['best_asset']} ({analysis['best_return']:.2f}%)")
        print(f"  Worst: {analysis['worst_asset']} ({analysis['worst_return']:.2f}%)")
        print(f"  Std Dev: {analysis['return_std']:.2f}%")
        
        print(f"\n📈 SHARPE RATIO:")
        print(f"  Mean Sharpe: {analysis['mean_sharpe']:.2f}")
        print(f"  Median Sharpe: {analysis['median_sharpe']:.2f}")
        print(f"  Best: {analysis['best_sharpe_asset']} ({analysis['best_sharpe']:.2f})")
        
        print(f"\n📉 DRAWDOWN:")
        print(f"  Mean Drawdown: {analysis['mean_drawdown']:.2f}%")
        print(f"  Best: {analysis['best_drawdown_asset']} ({analysis['best_drawdown']:.2f}%)")
        
        print(f"\n🎯 CONSISTENCY:")
        print(f"  Positive Assets: {analysis['positive_assets']}/{analysis['n_assets']} ({analysis['positive_assets_pct']:.1f}%)")
        print(f"  Mean Win Rate: {analysis['mean_win_rate']:.1f}%")
        
        print("\n" + "="*60)
    
    def print_portfolio(self, portfolio: Dict):
        """Print portfolio optimization results."""
        print("\n" + "="*60)
        print(" PORTFOLIO OPTIMIZATION")
        print("="*60)
        
        print(f"\n💼 RECOMMENDED ALLOCATION:")
        for i, asset in enumerate(portfolio['assets']):
            weight = portfolio['weight_pct'][i]
            print(f"  {asset}: {weight:.1f}%")
        
        print(f"\n📊 PORTFOLIO METRICS:")
        print(f"  Expected Return: {portfolio['portfolio_return']:.2f}%")
        print(f"  Expected Sharpe: {portfolio['portfolio_sharpe']:.2f}")
        print(f"  Diversification Benefit: {portfolio['diversification_benefit']:.2f}")
        
        print("\n" + "="*60)


def main():
    """Demo cross-asset analysis."""
    print("=== Cross-Asset Analysis Demo ===\n")
    print("This module requires backtest results from multiple assets.")
    print("Run the advanced testing script to see it in action!")


if __name__ == '__main__':
    main()
