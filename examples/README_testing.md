# PortfolioLib Backtester Testing

This directory contains comprehensive test scripts for the portfoliolib backtester system.

## Test Scripts Overview

### 1. `test_rsi_backtest.py` - Full RSI Backtest
**Purpose**: Complete backtest with two RSI traders and Sharpe optimization

**Features**:
- Two RSI traders with different thresholds:
  - **Conservative**: RSI > 50 (buy), RSI < 40 (sell)
  - **Aggressive**: RSI > 55 (buy), RSI < 45 (sell)
- Sharpe ratio optimization
- Daily rebalancing with 3-month lookback
- INTRADAY trading frequency (1-minute bars)
- Target volatility control (15%)
- Full performance analysis

**Usage**:
```bash
python test_rsi_backtest.py
```

### 2. `debug_backtester.py` - Component Debugging
**Purpose**: Debug individual components of the backtester

**Features**:
- Tests WeightToOrderAdapter functionality
- Tests MT5SE backtest integration
- Tests PortfolioManager components
- Step-by-step debugging with detailed logging

**Usage**:
```bash
python debug_backtester.py
```

### 3. `run_tests.py` - Test Runner
**Purpose**: Easy way to run different test scenarios

**Options**:
1. Debug tests (component testing)
2. Full RSI backtest
3. Individual trader tests
4. Run all tests

**Usage**:
```bash
python run_tests.py [1|2|3|4]
```

## Prerequisites

1. **MetaTrader 5**: Must be running and connected to a broker
2. **MT5SE Package**: Installed and working
3. **PortfolioLib**: All components properly installed
4. **Python Dependencies**: pandas, numpy, scipy

## Expected Output

### Successful Backtest Output:
```
📊 PERFORMANCE SUMMARY:
   - Initial equity: $100,000.00
   - Final equity: $105,234.56
   - Total return: 5.23%
   - Annualized return: 5.23%
   - Volatility: 12.45%
   - Sharpe ratio: 0.420
   - Max drawdown: -3.21%
   - Trading days: 252
```

### Debug Output:
```
[RSI_Conservative] Trade #1: RSI=52.3, Position=0.0, HasPos=False
[RSI_Conservative] → BUY signal (RSI=52.3 > 50)
[RSI_Aggressive] Trade #1: RSI=52.3, Position=0.0, HasPos=False
```

## Troubleshooting

### Common Issues:

1. **MT5 Connection Failed**:
   ```
   ❌ Failed to connect to MetaTrader 5
   ```
   **Solution**: Ensure MT5 is running and connected to a broker

2. **No NVDA Data**:
   ```
   [Trader] Trade #1: No NVDA data
   ```
   **Solution**: Check if NVDA symbol is available in your broker

3. **Insufficient Data**:
   ```
   [Trader] Trade #1: Insufficient data (5 bars)
   ```
   **Solution**: Increase the prestart period or check data availability

4. **Empty Backtest Results**:
   ```
   ❌ Backtest returned empty results
   ```
   **Solution**: Check date ranges and data availability

### Debug Mode:
Run with debug output to see detailed trading decisions:
```bash
python debug_backtester.py
```

## Customization

### Modify RSI Thresholds:
```python
# In test_rsi_backtest.py
trader1 = RSITrader(
    name="RSI_Conservative",
    threshold_high=50,  # Change this
    threshold_low=40,   # Change this
    rsi_period=14
)
```

### Change Rebalancing Frequency:
```python
# In test_rsi_backtest.py
rebalance_frequency = 'W'  # Weekly instead of daily
```

### Modify Target Volatility:
```python
# In test_rsi_backtest.py
target_volatility=0.20  # 20% instead of 15%
```

## Performance Analysis

The test scripts provide comprehensive performance metrics:

- **Total Return**: Overall portfolio performance
- **Annualized Return**: Return adjusted for time period
- **Volatility**: Risk measure (standard deviation)
- **Sharpe Ratio**: Risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Trading Days**: Number of active trading days

## File Outputs

- `rsi_traders_backtest_results.csv`: Complete equity curve and drawdown data
- Console output: Real-time trading decisions and performance metrics

## Next Steps

After running the tests successfully:

1. **Analyze Results**: Review the performance metrics and equity curve
2. **Optimize Parameters**: Adjust RSI thresholds, rebalancing frequency, etc.
3. **Add More Traders**: Extend the system with additional trading strategies
4. **Live Trading**: Use the PortfolioAgent for live trading (separate from backtesting)

## Support

If you encounter issues:

1. Run the debug script first: `python debug_backtester.py`
2. Check MT5 connection and data availability
3. Review the console output for specific error messages
4. Ensure all dependencies are properly installed

