# GG Script - Algorithmic Trading System

A comprehensive algorithmic trading system with genetic algorithm optimization, multi-timeframe analysis, and AI-powered strategies.

## Features

- **Genetic Algorithm Optimization**: Multiple GA implementations for strategy discovery and optimization
- **Multi-Timeframe Analysis**: Top-down analysis across multiple timeframes
- **AI-Powered Trading**: Integration with FinRL for reinforcement learning strategies
- **Multiple Data Providers**: Support for Alpaca and Binance
- **Backtesting Framework**: Extensive backtesting capabilities with performance analysis
- **Strategy Types**:
  - Momentum strategies
  - Reversal strategies
  - Scalping strategies
  - Long-term investment strategies

## Project Structure

- `genetic_algo_*.py` - Various genetic algorithm implementations for strategy optimization
- `ga_*.py` - Multi-timeframe and specialized GA implementations
- `train_*.py` - AI model training scripts
- `test_*.py` - Testing and validation scripts
- `analyze_*.py` - Analysis and comparison tools
- `*_data_provider.py` - Data provider integrations
- `documentation/` - Detailed documentation and guides
- `*.md` - Strategy documentation and research findings

## Key Components

### Genetic Algorithm Variants
- **Robust GA**: Anti-overfitting measures and conservative approach
- **Unrestricted GA**: Maximum flexibility for strategy discovery
- **Multi-Timeframe GA**: Top-down analysis across timeframes
- **Long-term GA**: Optimized for long-term investment horizons
- **Minimal GA**: Simplified strategy with fewer parameters

### Analysis Tools
- Strategy comparison and benchmarking
- Performance metrics and visualization
- Reversal signal analysis
- AI strategy analysis

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API credentials for your chosen data provider (Alpaca/Binance)

3. Run tests to verify setup:
   ```bash
   python test_alpaca_connection.py
   ```

4. Run strategy optimization:
   ```bash
   python genetic_algo_robust.py
   ```

## Documentation

Comprehensive documentation is available in the project:
- `FINRL_SETUP_GUIDE.md` - Setting up FinRL for AI trading
- `ROBUST_GA_QUICK_START.md` - Quick start guide for robust GA
- `MTF_GA_README.md` - Multi-timeframe GA documentation
- `COMPREHENSIVE_TEST_SUITE_README.md` - Testing guide
- Various analysis and results documents

## Results

Best strategy configurations are saved as JSON files:
- `best_robust_strategy.json`
- `best_unrestricted_strategy.json`
- `best_longterm_strategy.json`
- And more...

## License

This project is for educational and research purposes.

## Disclaimer

Trading involves risk. Past performance does not guarantee future results. Always test thoroughly before deploying any trading strategy with real capital.
