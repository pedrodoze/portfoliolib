#!/usr/bin/env python3
"""
Debug script for portfoliolib backtester components.

This script helps debug specific issues in the backtester by testing
individual components step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mt5se as se
from portfoliolib import PortfolioManager, SharpeOptimizer
from portfoliolib.backtester import WeightToOrderAdapter

class SimpleRSITrader(se.Trader):
    """Simplified RSI trader for debugging."""
    
    def __init__(self, name, threshold_high=50, threshold_low=40):
        super().__init__()
        self.name = name
        self.threshold_high = threshold_high
        self.threshold_low = threshold_low
        self.frequency = se.INTRADAY
        self.assets_universe = ['NVDA']
        self.trade_count = 0
        
    def setup(self, dbars):
        print(f"[{self.name}] Setup called")
        
    def calculate_rsi(self, prices, period=14):
        """Simple RSI calculation."""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if not enough data
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def trade(self, dbars, my_positions=None):
        """Simplified trading logic."""
        self.trade_count += 1
        
        if 'NVDA' not in dbars or dbars['NVDA'] is None or dbars['NVDA'].empty:
            if self.trade_count <= 5:  # Debug first few calls
                print(f"[{self.name}] Trade #{self.trade_count}: No NVDA data")
            return {'cash': 1.0}
        
        nvda_bars = dbars['NVDA']
        if len(nvda_bars) < 15:
            if self.trade_count <= 5:
                print(f"[{self.name}] Trade #{self.trade_count}: Insufficient data ({len(nvda_bars)} bars)")
            return {'cash': 1.0}
        
        # Calculate RSI
        close_prices = nvda_bars['close'].values
        rsi = self.calculate_rsi(close_prices)
        
        # Get current position
        current_shares = 0.0
        if my_positions and 'NVDA' in my_positions:
            current_shares = my_positions['NVDA'].get('shares', 0.0)
        
        has_position = abs(current_shares) > 0.01
        
        # Debug first few trades
        if self.trade_count <= 10:
            print(f"[{self.name}] Trade #{self.trade_count}: RSI={rsi:.1f}, Position={current_shares:.1f}, HasPos={has_position}")
        
        # Simple logic: buy if RSI > threshold and no position
        if not has_position and rsi > self.threshold_high:
            if self.trade_count <= 10:
                print(f"[{self.name}] → BUY signal (RSI={rsi:.1f} > {self.threshold_high})")
            return {'NVDA': 1.0, 'cash': 0.0}
        elif has_position and rsi < self.threshold_low:
            if self.trade_count <= 10:
                print(f"[{self.name}] → SELL signal (RSI={rsi:.1f} < {self.threshold_low})")
            return {'NVDA': 0.0, 'cash': 1.0}
        
        # Hold current position
        if has_position:
            return {'NVDA': 1.0, 'cash': 0.0}
        else:
            return {'NVDA': 0.0, 'cash': 1.0}
    
    def ending(self, dbars):
        print(f"[{self.name}] Ending: Total trades = {self.trade_count}")

def test_weight_to_order_adapter():
    """Test the WeightToOrderAdapter component."""
    
    print("=" * 60)
    print("TESTING WEIGHT TO ORDER ADAPTER")
    print("=" * 60)
    
    # Create a simple trader
    trader = SimpleRSITrader("DebugTrader", threshold_high=50, threshold_low=40)
    
    # Create adapter
    adapter = WeightToOrderAdapter(trader, allocated_capital=100000.0)
    
    print(f"Adapter created:")
    print(f"  - Name: {adapter.name}")
    print(f"  - Frequency: {adapter.frequency}")
    print(f"  - Assets: {getattr(adapter, 'assets_universe', 'N/A')}")
    print(f"  - Allocated capital: ${adapter.allocated_capital:,.2f}")
    
    # Test with mock data
    print(f"\nTesting with mock data...")
    
    # Create mock bars data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
    mock_bars = pd.DataFrame({
        'time': dates,
        'open': 100 + np.random.randn(100).cumsum() * 0.1,
        'high': 100 + np.random.randn(100).cumsum() * 0.1 + 0.5,
        'low': 100 + np.random.randn(100).cumsum() * 0.1 - 0.5,
        'close': 100 + np.random.randn(100).cumsum() * 0.1,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    dbars = {'NVDA': mock_bars}
    
    # Test setup
    print(f"\n1. Testing setup...")
    adapter.setup(dbars)
    
    # Test trade method
    print(f"\n2. Testing trade method...")
    orders = adapter.trade(dbars)
    
    print(f"   - Orders returned: {len(orders)}")
    if orders:
        for i, order in enumerate(orders):
            print(f"     Order {i+1}: {order.get('symbol', 'N/A')} {order.get('type', 'N/A')} {order.get('volume', 'N/A')}")
    else:
        print(f"     No orders generated")
    
    # Test ending
    print(f"\n3. Testing ending...")
    adapter.ending(dbars)
    
    print(f"\n✅ WeightToOrderAdapter test completed")

def test_mt5se_backtest_integration():
    """Test MT5SE backtest integration."""
    
    print("\n" + "=" * 60)
    print("TESTING MT5SE BACKTEST INTEGRATION")
    print("=" * 60)
    
    # Create trader
    trader = SimpleRSITrader("MT5SETest", threshold_high=50, threshold_low=40)
    
    # Setup dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    prestart_date = start_date - timedelta(days=7)
    
    print(f"Date range:")
    print(f"  - Start: {start_date.date()}")
    print(f"  - End: {end_date.date()}")
    print(f"  - Prestart: {prestart_date.date()}")
    
    # Setup backtest
    print(f"\n1. Setting up MT5SE backtest...")
    assets = trader.assets_universe
    period = trader.frequency
    
    try:
        bts = se.backtest.set(assets, prestart_date, start_date, end_date, period, 100000.0)
        
        if bts is None:
            print(f"   ❌ Failed to setup backtest")
            return False
        
        print(f"   ✅ Backtest setup successful")
        print(f"   - Assets: {assets}")
        print(f"   - Period: {period}")
        print(f"   - Capital: $100,000")
        
    except Exception as e:
        print(f"   ❌ Error setting up backtest: {e}")
        return False
    
    # Test with adapter
    print(f"\n2. Testing with WeightToOrderAdapter...")
    try:
        adapter = WeightToOrderAdapter(trader, allocated_capital=100000.0)
        results = se.backtest.run(adapter, bts)
        
        if results is not None and not results.empty:
            print(f"   ✅ Backtest run successful")
            print(f"   - Results shape: {results.shape}")
            print(f"   - Columns: {list(results.columns)}")
            print(f"   - Date range: {results['date'].min()} to {results['date'].max()}")
            print(f"   - Final equity: ${results['equity'].iloc[-1]:,.2f}")
            print(f"   - Total return: {((results['equity'].iloc[-1] / 100000.0) - 1):.2%}")
            return True
        else:
            print(f"   ❌ Backtest returned empty results")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_manager():
    """Test PortfolioManager component."""
    
    print("\n" + "=" * 60)
    print("TESTING PORTFOLIO MANAGER")
    print("=" * 60)
    
    # Create traders
    trader1 = SimpleRSITrader("Trader1", threshold_high=50, threshold_low=40)
    trader2 = SimpleRSITrader("Trader2", threshold_high=55, threshold_low=45)
    
    # Create optimizer and manager
    optimizer = SharpeOptimizer(risk_free_rate=0.02)
    
    print(f"1. Creating PortfolioManager...")
    try:
        manager = PortfolioManager(
            traders=[trader1, trader2],
            optimizer=optimizer,
            initial_equity=100000.0,
            initial_weights={"Trader1": 0.5, "Trader2": 0.5},
            target_volatility=0.15,
            max_leverage=1.5
        )
        
        print(f"   ✅ PortfolioManager created successfully")
        print(f"   - Traders: {list(manager.trader_map.keys())}")
        print(f"   - Initial weights: {manager.current_weights}")
        print(f"   - Target volatility: {manager.target_volatility}")
        
    except Exception as e:
        print(f"   ❌ Error creating PortfolioManager: {e}")
        return False
    
    # Test capital allocation
    print(f"\n2. Testing capital allocation...")
    try:
        allocations = manager.allocate_capital()
        print(f"   ✅ Capital allocation successful")
        for trader_name, amount in allocations.items():
            print(f"   - {trader_name}: ${amount:,.2f}")
        
    except Exception as e:
        print(f"   ❌ Error in capital allocation: {e}")
        return False
    
    # Test weight update with mock data
    print(f"\n3. Testing weight update...")
    try:
        # Create mock equity curves
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        mock_equity = pd.DataFrame({
            'Trader1': 100000 + np.random.randn(30).cumsum() * 1000,
            'Trader2': 100000 + np.random.randn(30).cumsum() * 1000
        }, index=dates)
        
        manager.update_weights(mock_equity)
        print(f"   ✅ Weight update successful")
        print(f"   - New weights: {manager.current_weights}")
        
    except Exception as e:
        print(f"   ❌ Error updating weights: {e}")
        return False
    
    return True

def main():
    """Run all debug tests."""
    
    print("🔧 PORTFOLIOLIB BACKTESTER DEBUG SCRIPT")
    print("=" * 80)
    
    try:
        # Connect to MT5
        if not se.connect():
            print("❌ Failed to connect to MetaTrader 5")
            print("   Make sure MT5 is running and connected to a broker")
            return False
        
        print("✅ Connected to MetaTrader 5")
        
        # Run tests
        test_weight_to_order_adapter()
        
        if test_mt5se_backtest_integration():
            print(f"\n✅ MT5SE integration test passed")
        else:
            print(f"\n❌ MT5SE integration test failed")
        
        if test_portfolio_manager():
            print(f"\n✅ PortfolioManager test passed")
        else:
            print(f"\n❌ PortfolioManager test failed")
        
        print(f"\n🎉 Debug tests completed!")
        return True
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Debug interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

