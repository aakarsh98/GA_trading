# GA Trading - Genetic Algorithm Strategy Optimizer

A clean, production-ready algorithmic trading system using genetic algorithms to discover and optimize trading strategies.

## Core Features

- **Genetic Algorithm Optimization**: Multiple GA implementations for strategy discovery
- **Multi-Timeframe Analysis**: Top-down analysis across different timeframes
- **AI Integration**: FinRL support for reinforcement learning strategies
- **Data Providers**: Alpaca and Binance support
- **Backtesting Engine**: Comprehensive backtesting with performance metrics
- **Advanced Testing Suite**: Research-grade testing framework

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Set up your data provider credentials (Alpaca or Binance) in environment variables or config files.

### 3. Run Your First Strategy Optimization

```bash
# Quick test with robust genetic algorithm
python test_robust_ga_quick.py

# Full genetic algorithm optimization
python genetic_algo_robust.py

# Long-term strategy optimization
python genetic_algo_longterm.py
```

## Project Structure

```
.
├── genetic_algo_*.py          # Various GA implementations
├── ga_*.py                    # Multi-timeframe GA variants
├── test_*.py                  # Testing scripts
├── *_data_provider.py         # Data provider integrations
├── python_testing/            # Advanced testing framework
│   ├── indicators/           # Custom indicators
│   ├── strategy/             # Strategy engine
│   └── data/                 # Data collection utilities
└── requirements.txt
```

## Available GA Implementations

- **`genetic_algo_robust.py`** - Conservative, anti-overfitting approach
- **`genetic_algo_unrestricted.py`** - Maximum flexibility for discovery
- **`genetic_algo_longterm.py`** - Optimized for long-term horizons
- **`genetic_algo_minimal.py`** - Simplified strategy with fewer parameters
- **`ga_multitimeframe_*.py`** - Multi-timeframe analysis variants
- **`genetic_algo_ultra_robust.py`** - Maximum robustness measures

## Testing

```bash
# Test data connection
python test_alpaca_connection.py

# Quick GA test
python test_robust_ga_quick.py

# Comprehensive testing
python run_all_research_tests.py
```

## Advanced Features

### Python Testing Framework

Located in `python_testing/`, includes:
- Edge scoring indicators
- Hidden Markov Model regime detection
- Survival analysis filters
- Cross-asset momentum tracking
- Advanced backtesting engine

### AI Training

```bash
# Train momentum-based AI agent
python train_momentum_ai.py
```

## Configuration

Results are saved as JSON files:
- Strategy parameters
- Performance metrics
- Optimization history

## Best Practices

1. Start with `test_robust_ga_quick.py` for rapid iteration
2. Use robust GA variants to avoid overfitting
3. Always backtest on out-of-sample data
4. Monitor Sharpe ratio and maximum drawdown
5. Test across multiple market conditions

## Requirements

- Python 3.9+
- See `requirements.txt` for package dependencies

## License

This project is for educational and research purposes.

## Disclaimer

⚠️ **Trading involves significant risk of loss. Past performance does not guarantee future results. Always test thoroughly before deploying with real capital.**

## Contributing

This is a research project. Feel free to experiment with new GA variants and strategy ideas.

## Getting Help

Check the test files for usage examples and the python_testing framework for advanced features.
