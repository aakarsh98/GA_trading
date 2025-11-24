# Backtest Analysis Template

## Strategy Information
**Strategy Name**: [Strategy Name]
**Asset**: [Asset Symbol]
**Timeframe**: [Primary Timeframe]
**Backtest Period**: [Start Date] to [End Date]
**Number of Trades**: [Total Trades]

## Performance Metrics

### Core Metrics
| Metric | Value | Interpretation |
|--------|-------|----------------|
| Net Profit | $[Amount] | [Good/Bad/Average - Target: Positive with reasonable risk] |
| Gross Profit | $[Amount] | Total profit from winning trades |
| Gross Loss | $[Amount] | Total loss from losing trades |
| Profit Factor | [Ratio] | [Target: >1.5, Excellent: >2.0] |
| Max Drawdown | [Percentage]% | [Target: <20%, Excellent: <15%] |
| Sharpe Ratio | [Ratio] | [Target: >0.8, Excellent: >1.2] |

### Trade Statistics
| Metric | Value | Target |
|--------|-------|--------|
| Total Trades | [Number] | 500-2000 (good sample size) |
| Winning Trades | [Number] | |
| Losing Trades | [Number] | |
| Win Rate | [Percentage]% | 35-65% (avoid unrealistic high rates) |
| Average Win | $[Amount] | |
| Average Loss | $[Amount] | |
| Largest Win | $[Amount] | |
| Largest Loss | $[Amount] | |
| Avg Trade Duration | [Bars/Time] | |
| Consecutive Wins | [Number] | |
| Consecutive Losses | [Number] | Should be manageable |

### Risk Metrics
| Metric | Value | Assessment |
|--------|-------|-----------|
| Risk of Ruin | [Percentage]% | Should be <5% |
| Calmar Ratio | [Ratio] | [Target: >0.5] |
| Sortino Ratio | [Ratio] | Focus on downside risk |
| Recovery Factor | [Ratio] | Profit vs max drawdown |

## Market Condition Analysis

### Trending Markets
**Performance**: [Profit/Loss]%  
**Analysis**: [How strategy performed in trending conditions]

### Ranging/Sideways Markets
**Performance**: [Profit/Loss]%
**Analysis**: [How strategy performed in ranging conditions]

### High Volatility Periods
**Performance**: [Profit/Loss]%
**Analysis**: [Strategy behavior during volatility spikes]

### Low Volatility Periods
**Performance**: [Profit/Loss]%
**Analysis**: [Strategy performance in calm markets]

## Parameter Sensitivity

### Optimized Parameters
| Parameter | Optimized Value | Range Tested | Sensitivity |
|-----------|----------------|--------------|-------------|
| [Parameter 1] | [Value] | [Range] | [High/Medium/Low] |
| [Parameter 2] | [Value] | [Range] | [High/Medium/Low] |
| [Parameter 3] | [Value] | [Range] | [High/Medium/Low] |

### Critical Parameters
1. **Most Important**: [Parameter name] - [Reason for importance]
2. **Second Most**: [Parameter name] - [Reason for importance]
3. **Least Important**: [Parameter name] - [Reason]

## Walk-Forward Testing Results

### Training Period: [Period]
- Net Profit: $[Amount]
- Win Rate: [Percentage]%
- Drawdown: [Percentage]%

### Testing Period: [Period]
- Net Profit: $[Amount]
- Win Rate: [Percentage]%
- Drawdown: [Percentage]%

### Degradation Analysis
- Performance Degradation: [Percentage]%
- **Assessment**: [Acceptable/Concerning/Excellent]

## Cross-Asset Testing

### Forex Pairs
| Pair | Net Profit | Win Rate | Drawdown | Assessment |
|------|-----------|----------|----------|------------|
| EURUSD | $[Amount] | [%]% | [%]% | [Rating] |
| GBPUSD | $[Amount] | [%]% | [%]% | [Rating] |
| USDJPY | $[Amount] | [%]% | [%]% | [Rating] |

### Stocks/ETFs
| Symbol | Net Profit | Win Rate | Drawdown | Assessment |
|--------|-----------|----------|----------|------------|
| SPY | $[Amount] | [%]% | [%]% | [Rating] |
| QQQ | $[Amount] | [%]% | [%]% | [Rating] |

### Cryptocurrencies
| Crypto | Net Profit | Win Rate | Drawdown | Assessment |
|--------|-----------|----------|----------|------------|
| BTCUSD | $[Amount] | [%]% | [%]% | [Rating] |
| ETHUSD | $[Amount] | [%]% | [%]% | [Rating] |

## Risk Management Analysis

### Position Sizing
- **Method Used**: [Fixed % / Volatility-based / Other]
- **Risk per Trade**: [Percentage]%
- **Max Position Size**: [Percentage]%
- **Assessment**: [Appropriate/Too conservative/Too aggressive]

### Stop Loss Performance
- **Stop Loss Type**: [ATR-based / Percentage / Other]
- **Average Stop Distance**: [Pips/Percent]
- **Stop Hit Rate**: [Percentage]%
- **Assessment**: [Effective/Too tight/Too wide]

### Portfolio Risk
- **Max Simultaneous Positions**: [Number]
- **Correlation Impact**: [Minimal/Medium/High]
- **Portfolio Drawdown**: [Percentage]%
- **Monthly Volatility**: [Percentage]%

## Strategy Strengths

### What Works Well
1. **[Strength 1]** - [Explanation with data]
2. **[Strength 2]** - [Explanation with data]
3. **[Strength 3]** - [Explanation with data]

### Best Market Conditions
- **Optimal Environment**: [Trending/Ranging/Volatile/etc.]
- **Best Timeframes**: [Timeframes that work best]
- **Best Asset Classes**: [Asset types where strategy excels]

## Strategy Weaknesses

### Areas of Concern
1. **[Weakness 1]** - [Explanation with data]
2. **[Weakness 2]** - [Explanation with data]
3. **[Weakness 3]** - [Explanation with data]

### Risk Periods
- **Worst Conditions**: [Markets/conditions where strategy fails]
- **Failure Triggers**: [What causes poor performance]
- **Recovery Time**: [How long to recover from drawdowns]

## Improvement Recommendations

### Immediate Improvements
1. **[Recommendation 1]** - [Expected impact and implementation difficulty]
2. **[Recommendation 2]** - [Expected impact and implementation difficulty]

### Long-term Enhancements
1. **[Enhancement 1]** - [Potential benefits]
2. **[Enhancement 2]** - [Potential benefits]

### Additional Testing Needed
- **[Test 1]** - [Purpose of test]
- **[Test 2]** - [Purpose of test]

## Real-World Considerations

### Implementation Challenges
- **Slippage Impact**: [How slippage affects results]
- **Commission Costs**: [Cost impact on performance]
- **Execution Issues**: [Potential problems in live trading]

### Psychological Factors
- **Trade Frequency**: [Too high/too low for comfort]
- **Drawdown Tolerance**: [Can traders handle the drawdowns?]
- **Discipline Requirements**: [Strategy complexity and discipline needed]

## Conclusion

### Overall Assessment
**Rating**: [Excellent/Good/Average/Poor]

**Summary**: [Brief overall assessment of strategy performance and viability]

### Recommendations
- **Proceed to Live Trading**: [Yes/No/Maybe with conditions]
- **Required Modifications**: [Changes needed before live trading]
- **Ongoing Monitoring**: [What to monitor in live trading]

### Next Steps
1. **[Next Step 1]** - [Timeline and责任人]
2. **[Next Step 2]** - [Timeline and责任人]
3. **[Next Step 3]** - [Timeline and责任人]

---

## Analysis Notes
[Additional observations, concerns, or insights discovered during analysis]

## Data Sources
- **Backtest Platform**: TradingView Strategy Tester
- **Historical Data Period**: [Period and data quality notes]
- **Assumptions Made**: [Any assumptions about costs, timing, etc.]

## Analyst Information
- **Analyst**: [Your name]
- **Analysis Date**: [Date]
- **Experience Level**: [Beginner/Intermediate/Expert]
- **Contact**: [Contact information for follow-up]
