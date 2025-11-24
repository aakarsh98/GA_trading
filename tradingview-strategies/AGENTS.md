# TradingView Strategy Development Configuration for AI Agents

## Project Overview
- **Project Name**: TradingView Strategy Development
- **Purpose**: Algorithmic strategy development, backtesting, and optimization
- **Primary Markets**: Forex (EURUSD, GBPUSD), Indices (SPY, QQQ), Crypto (BTCUSD, ETHUSD)
- **Trading Style**: Multi-timeframe (scalping, day trading, swing trading)
- **Risk Tolerance**: Conservative (max 2% risk per trade)

## TradingView & Pine Script Configuration

### Pine Script Version
- **Current Version**: Pine Script v6
- **Always Use**: `//@version=6` at top of all scripts
- **Compatibility**: Focus on modern features, backward compatibility not critical

### License & Distribution
- **Open Source**: All strategies open source with proper attribution
- **Community Sharing**: Consider sharing on TradingView Community Scripts
- **Documentation**: Include comprehensive comments for educational purposes

## Strategy Development Standards

### Strategy Declaration Pattern
```pinescript
//@version=6
strategy("StrategyName", overlay=true, 
         initial_capital=10000,
         default_qty_type=strategy.percent_of_equity,
         default_qty_value=10,
         commission_value=0.1,
         slippage=2)
```

### Required Strategy Elements
- Clear entry and exit conditions
- Risk management (stop loss and take profit)
- Position sizing based on account equity
- Performance metrics tracking
- Visual indicators for manual verification

### Naming Conventions
- **Strategy Files**: `Strategy_DescriptiveName_v6.pinescript`
- **Indicator Files**: `Indicator_DescriptiveName_v6.pinescript`
- **Utility Scripts**: `Utility_FunctionName_v6.pinescript`
- **Variables**: snake_case `moving_average_fast`, `entry_condition`
- **Functions**: camelCase `calculatePositionSize`, `checkEntrySignal`

## Trading Methodologies Allowed

### Technical Analysis Focus
- **Trend Following**: Moving averages, ADX, trend lines
- **Mean Reversion**: Bollinger Bands, RSI, Stochastic
- **Momentum**: MACD, Rate of Change, Momentum oscillator
- **Volatility**: ATR, VIX, Standard Deviation
- **Volume Analysis**: Volume profile, On-Balance Volume, VWAP

### Multi-Timeframe Analysis
- **Primary Timeframes**: M5, M15, M30, H1, H4, D1
- **Trend Confirmation**: Higher timeframe for trend direction
- **Entry/Exit Timing**: Lower timeframe for precise entries
- **Regime Detection**: Multiple timeframe volatility analysis

### Risk Management Rules
- **Maximum Risk**: Never exceed 2% of account equity per trade
- **Stop Loss**: ATR-based or percentage-based stops
- **Take Profit**: Risk-to-reward minimum 1:1.5, preferably 1:2+
- **Position Sizing**: Dynamic based on volatility and account size
- **Maximum Drawdown**: Strategy should not exceed 15% peak-to-trough in backtests

## Quality Standards for Strategies

### Backtesting Requirements
- **Minimum Data**: 1,000 trades or 3 years of data (whichever is greater)
- **Profit Factor**: Minimum 1.5, preferably 2.0+
- **Maximum Drawdown**: <20% of account equity
- **Win Rate**: 35-65% (avoid unrealistic high win rates)
- **Sharpe Ratio**: Minimum 0.8, preferably 1.2+
- **Calmar Ratio**: Minimum 0.5 for long-term strategies

### Realistic Assumptions
- **Commission**: 0.1% per trade (adjust for specific instruments)
- **Slippage**: 1-2 pips in forex, 0.1-0.2% in stocks
- **Execution Delay**: 1-2 bars for realistic trade simulation
- **Market Hours**: Respect actual market session times
- **Liquidity**: Consider volume constraints for position sizes

### Performance Metrics to Track
- Net Profit and Gross Profit/Loss
- Number of trades and average trade duration
- Maximum consecutive wins/losses
- Average win/loss ratio
- Monthly and yearly returns consistency
- Market condition performance (trending vs ranging)

## Code Quality Standards

### Pine Script Best Practices
- Use built-in functions when available (`ta.ema()`, `ta.atr()`, etc.)
- Implement proper security functions (`request.security()`)
- Use color.new() for all plotting functions
- Implement proper error handling and edge cases
- Include comprehensive comments explaining logic

### Documentation Requirements
- Brief description at top of each script
- Parameters explanation in input() descriptions
- Logic explanation for complex sections
- Performance expectations and limitations
- Usage examples and recommended settings

### Code Organization
```pinescript
//@version=6
strategy("StrategyName", overlay=true)

//=== USER INPUTS =============================================================================
// All strategy parameters here

//=== INDICATORS ==========================================================================
// Calculate all technical indicators

//=== STRATEGY LOGIC ======================================================================
// Entry and exit conditions

//=== RISK MANAGEMENT =====================================================================
// Position sizing and stop/take profit

//=== EXECUTION ===========================================================================
// Strategy.entry() and strategy.close calls

//=== VISUALIZATION =======================================================================
// Plotting and visual feedback
```

## Testing & Validation Procedures

### Initial Development Testing
1. **Visual Backtest**: Apply to chart and verify signals match expectations
2. **Manual Verification**: Check 50-100 trades manually
3. **Different Timeframes**: Test strategy on multiple timeframes
4. **Market Conditions**: Test in trending, ranging, volatile markets

### Automated Backtesting Workflow
1. **Strategy Tester**: Run complete backtest with realistic assumptions
2. **Performance Analysis**: Review all key metrics and drawdowns
3. **Parameter Optimization**: Test parameter ranges for robustness
4. **Walk-Forward Testing**: Train on 70% of data, test on remaining 30%

### Cross-Market Validation
- **Currency Pairs**: Test on EURUSD, GBPUSD, USDJPY
- **Indices**: Test on SPY, QQQ, DIA
- **Commodities**: Test on Gold (XAUUSD), Oil (USOIL)
- **Crypto**: Test on Bitcoin (BTCUSD), Ethereum (ETHUSD)

## Risk Management & Position Sizing

### Position Sizing Formula
```pinescript
// Risk-based position sizing
risk_percent = input.float(2.0, "Risk %", 0.1, 10.0, 0.1) / 100
atrv = ta.atr(14) * 2  // ATR-based stop distance
position_size = (strategy.netprofit + strategy.initial_capital) * risk_percent / atrv
```

### Stop Loss Methods
- **ATR-based**: `entryPrice - atr_multiplier * atr_value`
- **Percentage**: `entryPrice * (1 - stop_percent)`
- **Recent High/Low**: Based on recent swing points
- **Volatility-adjusted**: Based on current market volatility

### Portfolio Risk Management
- **Maximum Positions**: No more than 5 simultaneous positions
- **Correlation Management**: Avoid highly correlated instruments
- **Market Exposure**: Risk exposure should not exceed 8% of account total

## Script Categories & Templates

### Trend Following Template
```pinescript
// Template structure for trend-following strategies
strategy("Trend Template", overlay=true)

// Trend indicators (MA, ADX, etc.)
// Entry on trend continuation
// Exit on trend reversal
// Visual trend direction indicators
```

### Mean Reversion Template
```pinescript
// Template structure for mean reversion strategies
strategy("Mean Reversion Template", overlay=true)

// Oscillators (RSI, Stochastic, etc.)
// Entry in overbought/oversold conditions
// Exit when returning to mean
// Range trading visual elements
```

### Multi-Timeframe Template
```pinescript
// Template structure for multi-timeframe strategies
strategy("MTF Template", overlay=true)

// Higher timeframe trend analysis
// Lower timeframe entry timing
// Confirmation signals across timeframes
// Visual trend alignment indicators
```

## Market-Specific Considerations

### Forex Market
- **Trading Hours**: 24-hour market, respect session overlaps
- **Spread Impact**: Include realistic spread costs (1-3 pips)
- **Currency Pairs**: Major pairs for better liquidity
- **Seasonal Patterns**: Consider holiday effects on volatility

### Stock Market
- **Market Hours**: Respect exchange trading hours only
- **Gap Risk**: Consider overnight gap risk
- **Earnings Impact**: Avoid trading around earnings announcements
- **Sector Rotation**: Consider sector-specific trends

### Cryptocurrency Market
- **24/7 Trading**: No market hour restrictions
- **High Volatility**: Wider stop losses required
- **Correlation Events**: All crypto often moves together
- **Market Cycles**: Consider bull/bear market phases

## Optimization Guidelines

### Parameter Ranges
- **Moving Averages**: 5 to 100 periods
- **Risk Percent**: 0.5% to 3.0% per trade
- **ATR Multiples**: 1.0 to 5.0 for stop distances
- **RSI Levels**: 20 to 80 for oversold/overbought

### Overfitting Prevention
- Avoid curve fitting to historical data
- Use walk-forward testing methodology
- Test on out-of-sample data
- Keep strategy logic simple and explainable
- Ensure parameters work across different markets

### Performance Validation
- Must work in at least 3 different market types
- Consistency across different time periods
- Reasonable number of trades (not too few, not too many)
- Profit distribution should not have extreme outliers

## Integration with TradingView Features

### Alerts Configuration
- **Setup Alert Conditions**: Use `alertcondition()` for signal detection
- **Message Formatting**: Clear alert messages with instrument and action
- **Sound Notifications**: Consider different sounds for buy/sell signals
- **Email Notifications**: Setup for backup alert delivery

### Study Publishing
- **Public Scripts**: Consider publishing profitable strategies
- **Attribution**: Credit original sources when using others' ideas
- **Script Description**: Clear description of strategy logic and use cases
- **Performance Summary**: Include backtest results in script comments

### Community Interaction
- **Review Comments**: Monitor community feedback on published scripts
- **Feature Requests**: Consider user suggestions for improvements
- **Bug Reports**: Fix issues reported by community users
- **Updates**: Maintain published scripts with improvements

## File Organization Standards

### Directory Structure
```
tradingview-strategies/
├── AGENTS.md                    # This file
├── README.md                    # Project overview
├── scripts/                     # Pine Script files
│   ├── strategies/              # Complete strategy scripts
│   ├── indicators/              # Custom indicators
│   └── libraries/               # Reusable functions
├── backtests/                   # Backtest results and analysis
├── documentation/               # Strategy documentation
└── utils/                       # Analysis and utility tools
```

### File Naming Convention
- **Strategy Scripts**: `Strategy_MovingAverageCross_v6.pinescript`
- **Indicators**: `Indicator_AwesomeOscillator_v6.pinescript`
- **Libraries**: `Library_RiskManagement_v6.pinescript`
- **Documentation**: `Strategy_MovingAverageCross_Analysis.md`

### Version Control
- Use semantic versioning (v1.0.0, v1.1.0, etc.)
- Keep CHANGELOG.md for major modifications
- Archive old versions in `archive/` folder
- Tag releases with descriptive names

## Special Instructions for AI Agents

### When Creating New Strategies
1. Always start with proper strategy declaration and parameters
2. Implement comprehensive risk management
3. Include visual feedback for manual verification
4. Test across multiple timeframes before finalizing
5. Document all parameters and their implications
6. Consider market regime changes and adaptability

### When Optimizing Existing Strategies
1. First understand the current strategy logic thoroughly
2. Make incremental changes rather than wholesale overhauls
3. Test each optimization independently
4. Compare results with baseline to verify improvements
5. Document changes made and their rationale
6. Backtest on multiple assets to ensure robustness

### When Debugging Strategies
1. Identify if issues are logical or implementation-related
2. Use plot() statements to debug values visually
3. Check for common issues: repainting, future leaks, incorrect calculations
4. Verify risk management is working correctly
5. Test with small position sizes initially
6. Consider edge cases and extreme market conditions

### Performance Analysis Requirements
1. Provide complete performance metrics for all strategies
2. Include analysis of different market conditions
3. Compare against relevant benchmarks (buy and hold, etc.)
4. Highlight strengths and weaknesses of each approach
5. Suggest potential improvements or refinements
6. Consider real-world implementation challenges

## Code Examples and Templates

### Basic Strategy Structure
```pinescript
//@version=6
strategy("Template Strategy", overlay=true, 
         initial_capital=10000,
         default_qty_type=strategy.percent_of_equity,
         default_qty_value=10,
         commission_value=0.1)

//=== USER INPUTS =============================================================================
fastMA_len = input.int(20, title="Fast MA Length")
slowMA_len = input.int(50, title="Slow MA Length")
risk_percent = input.float(1.0, "Risk %", 0.1, 5.0, 0.1) / 100
atr_multiplier = input.float(2.0, "ATR Stop Loss", 1.0, 5.0, 0.1)

//=== INDICATORS ==========================================================================
fast_ma = ta.ema(close, fastMA_len)
slow_ma = ta.ema(close, slowMA_len)
atr_value = ta.atr(14)

//=== STRATEGY LOGIC ======================================================================
long_condition = ta.crossover(fast_ma, slow_ma)
exit_condition = ta.crossunder(fast_ma, slow_ma)

//=== RISK MANAGEMENT =====================================================================
if long_condition and strategy.opentrades == 0
    stop_distance = atr_value * atr_multiplier
    risk_amount = (strategy.netprofit + strategy.initial_capital) * risk_percent
    position_size = risk_amount / stop_distance
    strategy.entry("Long", strategy.long, qty=position_size)

if exit_condition
    strategy.close("Long", comment="Exit on MA crossunder")

//=== VISUALIZATION =======================================================================
plot(fast_ma, color=color.new(color.blue, 0), title="Fast MA")
plot(slow_ma, color=color.new(color.red, 0), title="Slow MA")
```

### Risk Management Template
```pinescript
// Advanced position sizing with volatility adjustment
calculatePositionSize() =>
    risk_percent = input.float(1.0, "Risk %", 0.1, 5.0, 0.1) / 100
    atr_length = input.int(14, "ATR Length")
    atr_multiple = input.float(2.0, "ATR Multiple", 1.0, 5.0, 0.1)
    
    current_atr = ta.atr(atr_length)
    stop_distance = current_atr * atr_multiple
    account_risk_amount = (strategy.netprofit + strategy.initial_capital) * risk_percent
    
    position_size = account_risk_amount / stop_distance
    position_size
```

## Future Development Roadmap

### Planned Enhancements
- **Machine Learning Integration**: Basic ML models for signal generation
- **Portfolio Management**: Multi-strategy combination and optimization
- **Advanced Risk Management**: Dynamic risk sizing based on volatility
- **Market Regime Detection**: Automatic market condition identification
- **Automated Optimization**: Genetic algorithm parameter optimization

### Learning Goals
- Study profitable community strategies and their techniques
- Explore advanced indicators and their mathematical foundations
- Understand market microstructure and its impact on trading
- Implement sophisticated portfolio risk management techniques
- Develop expertise in specific market niches

## Resources and References

### Official Documentation
- Pine Script v5 Manual: TradingView official documentation
- Pine Script Reference: Complete function and keyword reference
- TradingView Community: Scripts and discussions from other traders

### Educational Resources
- Technical Analysis textbooks for foundational knowledge
- Academic papers on market efficiency and trading strategies
- Professional trader interviews and strategy discussions
- Backtesting methodologies and statistical analysis

### Analysis Tools
- Excel/Google Sheets for deeper performance analysis
- Python libraries (pandas, matplotlib) for custom analysis
- Statistical software for advanced validation methods
- Real-world testing with paper trading accounts

---

## Quick Reference for AI Agents

### Before Creating Any Strategy
1. Review existing patterns and strategies in the scripts folder
2. Check AGENTS.md for specific requirements and constraints
3. Determine appropriate risk parameters and position sizing
4. Plan for multi-timeframe testing and validation
5. Consider the target audience (beginner vs advanced traders)

### Strategy Creation Checklist
- [ ] Proper strategy declaration with realistic parameters
- [ ] Clear entry and exit logic with risk management
- [ ] Visual indicators for manual verification
- [ ] Comprehensive comments explaining strategy logic
- [ ] Testing across multiple timeframes and assets
- [ ] Performance metrics analysis and documentation

### Common Pitfalls to Avoid
- Repainting issues (avoid future data leaks)
- Unrealistic assumptions about slippage and commissions
- Over-optimized parameters that only work on historical data
- Missing risk management or position sizing
- Inadequate testing across different market conditions
- Complex logic that cannot be explained or justified

### Performance Validation Standards
- Minimum 1000 trades in backtest
- Drawdown under 20% of account equity
- Profit factor above 1.5
- Consistent performance across different time periods
- Reasonable win rate (35-65%)
- Works in at least 3 different market conditions

This AGENTS.md file serves as the complete guide for AI agents working on TradingView strategy development, ensuring consistent, high-quality, and well-documented trading strategies.
