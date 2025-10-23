#!/usr/bin/env python3
"""
Test script for portfoliolib backtester with two RSI traders and Sharpe optimization.

Features:
- Two RSI traders: one for NVDA, one for MSFT
- RSI thresholds: buy > 65, sell < 30
- Sharpe ratio optimization
- Daily rebalancing with 1-week lookback
- DAILY trading frequency
- 1-month backtest period
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mt5se as se
from portfoliolib import PortfolioManager, PortfolioBacktester, SharpeOptimizer
from portfoliolib.backtester import WeightToOrderAdapter

class RSITrader(se.Trader):
    """
    RSI-based trader that opens/closes positions based on RSI thresholds.
    
    Logic:
    - Opens position when RSI > threshold_high and no position exists
    - Closes position when RSI < threshold_low and position exists
    - Trades a single specified asset
    """
    
    def __init__(self, name, asset, threshold_high=65, threshold_low=30, rsi_period=14):
        super().__init__()
        self.name = name
        self.asset = asset
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
        self.rsi_period = rsi_period
        self.frequency = se.DAILY  # Daily bars
        self.assets_universe = [asset]
        
        # State tracking
        self.current_position = 0.0  # Current shares held
        self.last_rsi = None
        
    def setup(self, dbars):
        """Initialize the trader with historical data."""
        print(f"[{self.name}] Setup: RSI thresholds {self.threshold_high}/{self.threshold_low} for {self.asset}")
        
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return None
            
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100.0
            
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        
        for i in range(period, len(deltas)):
            delta = deltas[i]
            if delta > 0:
                upval = delta
                downval = 0.0
            else:
                upval = 0.0
                downval = -delta
                
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            if down == 0:
                rsi = 100.0
            else:
                rs = up / down
                rsi = 100 - (100 / (1 + rs))
                
        return rsi
    
    def trade(self, dbars, my_positions=None):
        """
        Main trading logic based on RSI.
        
        Returns:
            dict: Portfolio weights {asset: weight, 'cash': weight}
        """
        if self.asset not in dbars or dbars[self.asset] is None or dbars[self.asset].empty:
            return {'cash': 1.0}
        
        asset_bars = dbars[self.asset]
        if len(asset_bars) < self.rsi_period + 1:
            return {'cash': 1.0}
        
        # Calculate RSI
        close_prices = asset_bars['close'].values
        rsi = self.calculate_rsi(close_prices, self.rsi_period)
        
        if rsi is None:
            return {'cash': 1.0}
        
        self.last_rsi = rsi
        
        # Get current position
        current_shares = 0.0
        if my_positions and self.asset in my_positions:
            current_shares = my_positions[self.asset].get('shares', 0.0)
        
        # Trading logic
        has_position = abs(current_shares) > 0.01
        
        if not has_position and rsi > self.threshold_high:
            # Open long position
            print(f"[{self.name}] RSI={rsi:.1f} > {self.threshold_high} → BUY {self.asset}")
            return {self.asset: 1.0, 'cash': 0.0}
            
        elif has_position and rsi < self.threshold_low:
            # Close position
            print(f"[{self.name}] RSI={rsi:.1f} < {self.threshold_low} → CLOSE position")
            return {self.asset: 0.0, 'cash': 1.0}
        
        # No action needed
        if has_position:
            return {self.asset: 1.0, 'cash': 0.0}
        else:
            return {self.asset: 0.0, 'cash': 1.0}
    
    def ending(self, dbars):
        """Cleanup when backtest ends."""
        rsi_str = f"{self.last_rsi:.1f}" if self.last_rsi is not None else "N/A"
        print(f"[{self.name}] Ending: Final RSI = {rsi_str}")

def create_test_traders():
    """Create the two RSI traders for NVDA and MSFT."""
    
    # Trader 1: NVDA RSI (65/30)
    trader1 = RSITrader(
        name="RSI_NVDA",
        asset="NVDA",
        threshold_high=65,
        threshold_low=30,
        rsi_period=14
    )
    
    # Trader 2: MSFT RSI (65/30)
    trader2 = RSITrader(
        name="RSI_MSFT", 
        asset="MSFT",
        threshold_high=65,
        threshold_low=30,
        rsi_period=14
    )
    
    return [trader1, trader2]

def run_backtest():
    """Run the complete backtest with RSI traders and Sharpe optimization."""
    
    print("=" * 80)
    print("RSI TRADERS BACKTEST WITH SHARPE OPTIMIZATION")
    print("=" * 80)
    
    # 1. Create traders
    print("\n1. Creating RSI traders...")
    traders = create_test_traders()
    
    for trader in traders:
        print(f"   - {trader.name}: {trader.asset} RSI thresholds {trader.threshold_high}/{trader.threshold_low}")
    
    # 2. Setup dates (10 years of data for comprehensive backtest)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=252*10)  # 10 years of trading days
    prestart_date = start_date - timedelta(days=252*1)  # 1 year before for lookback
    
    print(f"\n2. Setting up date ranges:")
    print(f"   - Start date: {start_date.date()}")
    print(f"   - End date: {end_date.date()}")
    print(f"   - Prestart date: {prestart_date.date()}")
    
    # 3. Create optimizer and manager
    print(f"\n3. Setting up portfolio management...")
    optimizer = SharpeOptimizer(risk_free_rate=0.02)  # 2% risk-free rate
    
    initial_equity = 100000.0
    initial_weights = {
        "RSI_NVDA": 0.5,  # Start with equal weights
        "RSI_MSFT": 0.5
    }
    
    manager = PortfolioManager(
        traders=traders,
        optimizer=optimizer,
        initial_equity=initial_equity,
        initial_weights=initial_weights,
        target_volatility=0.15,  # 15% target volatility
        max_leverage=1.5  # Max 150% exposure
    )
    
    # 4. Setup backtest parameters
    print(f"\n4. Configuring backtest parameters...")
    lookback_period = pd.DateOffset(days=60)  # 60-day lookback for optimization
    rebalance_frequency = 'D'  # Daily rebalancing
    
    print(f"   - Lookback period: 60 days")
    print(f"   - Rebalance frequency: Daily")
    print(f"   - Trading frequency: DAILY")
    print(f"   - Target volatility: 15%")
    print(f"   - Max leverage: 1.5x")
    
    # 5. Create and run backtester
    print(f"\n5. Running backtest...")
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=start_date,
        end_date=end_date,
        lookback_period=lookback_period,
        rebalance_frequency=rebalance_frequency,
        prestart_dt=prestart_date
    )
    
    # Run the backtest
    equity_curve = backtester.run()
    
    # 6. Analyze results
    print(f"\n6. Analyzing results...")
    if equity_curve.empty:
        print("   ❌ Backtest failed - no results generated")
        return None
    
    # Calculate performance metrics
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    annualized_return = (1 + total_return) ** (252 / len(equity_curve)) - 1
    volatility = equity_curve.pct_change().std() * np.sqrt(252)
    sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
    
    # Drawdown analysis
    rolling_max = equity_curve.expanding().max()
    drawdown = (equity_curve - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    print(f"\n📊 PERFORMANCE SUMMARY:")
    print(f"   - Initial equity: ${initial_equity:,.2f}")
    print(f"   - Final equity: ${equity_curve.iloc[-1]:,.2f}")
    print(f"   - Total return: {total_return:.2%}")
    print(f"   - Annualized return: {annualized_return:.2%}")
    print(f"   - Volatility: {volatility:.2%}")
    print(f"   - Sharpe ratio: {sharpe_ratio:.3f}")
    print(f"   - Max drawdown: {max_drawdown:.2%}")
    print(f"   - Trading days: {len(equity_curve)}")
    
    # 7. Save results
    print(f"\n7. Saving results...")
    results_df = pd.DataFrame({
        'date': equity_curve.index,
        'equity': equity_curve.values,
        'drawdown': drawdown.values
    })
    
    output_file = "rsi_traders_backtest_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"   - Results saved to: {output_file}")
    
    # 8. Show final portfolio status
    print(f"\n8. Final portfolio status:")
    status = manager.get_portfolio_status()
    print(f"   - Current weights: {status['current_weights']}")
    print(f"   - Capital allocation: {status['capital_allocation']}")
    print(f"   - Risk management: {status['risk_management']}")
    
    print(f"\n✅ Backtest completed successfully!")
    return equity_curve

def test_individual_traders():
    """Test individual traders separately for comparison."""
    
    print("\n" + "=" * 80)
    print("INDIVIDUAL TRADER TESTING")
    print("=" * 80)
    
    traders = create_test_traders()
    
    # Test each trader individually
    for trader in traders:
        print(f"\n--- Testing {trader.name} ---")
        
        # Simple backtest for individual trader
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        prestart_date = start_date - timedelta(days=30)
        
        assets = trader.assets_universe
        period = trader.frequency
        
        print(f"   - Assets: {assets}")
        print(f"   - Period: {period}")
        print(f"   - Date range: {start_date.date()} to {end_date.date()}")
        
        try:
            # Setup backtest
            bts = se.backtest.set(assets, prestart_date, start_date, end_date, period, 100000.0)
            
            if bts is None:
                print(f"   ❌ Failed to setup backtest for {trader.name}")
                continue
            
            # Run backtest with adapter
            adapted_trader = WeightToOrderAdapter(trader, allocated_capital=100000.0)
            results = se.backtest.run(adapted_trader, bts)
            
            if results is not None and not results.empty:
                final_equity = results['equity'].iloc[-1]
                total_return = (final_equity / 100000.0) - 1
                print(f"   ✅ {trader.name}: Final equity ${final_equity:,.2f} ({total_return:.2%})")
            else:
                print(f"   ❌ {trader.name}: No results generated")
                
        except Exception as e:
            print(f"   ❌ {trader.name}: Error - {e}")

if __name__ == "__main__":
    try:
        # Connect to MT5 (required for backtest)
        if not se.connect():
            print("❌ Failed to connect to MetaTrader 5")
            print("   Make sure MT5 is running and connected to a broker")
            sys.exit(1)
        
        print("✅ Connected to MetaTrader 5")
        
        # Test individual traders first
        test_individual_traders()
        
        # Run main backtest
        equity_curve = run_backtest()
        
        if equity_curve is not None:
            print(f"\n🎉 All tests completed successfully!")
        else:
            print(f"\n❌ Backtest failed - check the logs above for errors")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n👋 Test script finished")
