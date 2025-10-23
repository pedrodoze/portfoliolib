#!/usr/bin/env python3
"""
Simple test to isolate the backtest issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mt5se as se
from portfoliolib.backtester import WeightToOrderAdapter

class SimpleTestTrader(se.Trader):
    """Very simple trader for testing."""
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.frequency = se.INTRADAY
        self.assets_universe = ['NVDA']
        
    def setup(self, dbars):
        print(f"[{self.name}] Setup called")
        
    def trade(self, dbars, my_positions=None):
        """Always return cash (no trading)."""
        return {'cash': 1.0}
    
    def ending(self, dbars):
        print(f"[{self.name}] Ending called")

def test_simple_backtest():
    """Test a very simple backtest to isolate the issue."""
    
    print("🧪 SIMPLE BACKTEST TEST")
    print("=" * 40)
    
    # Connect to MT5
    if not se.connect():
        print("❌ Failed to connect to MetaTrader 5")
        return False
    
    print("✅ Connected to MetaTrader 5")
    
    # Use a very short date range first
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)  # Only 2 days
    prestart_date = start_date - timedelta(days=1)  # 1 day before
    
    print(f"\n📅 Short date range:")
    print(f"   - Start: {start_date.date()}")
    print(f"   - End: {end_date.date()}")
    print(f"   - Prestart: {prestart_date.date()}")
    
    # Create simple trader
    trader = SimpleTestTrader("TestTrader")
    
    # Test 1: Direct MT5SE backtest
    print(f"\n🔍 Test 1: Direct MT5SE backtest...")
    try:
        assets = trader.assets_universe
        period = trader.frequency
        
        bts = se.backtest.set(assets, prestart_date, start_date, end_date, period, 100000.0)
        
        if bts is None:
            print(f"   ❌ Backtest setup failed")
            return False
        
        print(f"   ✅ Backtest setup successful")
        
        # Run backtest
        results = se.backtest.run(trader, bts)
        
        if results is not None and not results.empty:
            print(f"   ✅ Direct backtest successful")
            print(f"   - Results shape: {results.shape}")
            print(f"   - Final equity: ${results['equity'].iloc[-1]:,.2f}")
        else:
            print(f"   ❌ Direct backtest failed - no results")
            
    except Exception as e:
        print(f"   ❌ Direct backtest error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: With WeightToOrderAdapter
    print(f"\n🔍 Test 2: With WeightToOrderAdapter...")
    try:
        adapted_trader = WeightToOrderAdapter(trader, allocated_capital=100000.0)
        
        bts2 = se.backtest.set(assets, prestart_date, start_date, end_date, period, 100000.0)
        results2 = se.backtest.run(adapted_trader, bts2)
        
        if results2 is not None and not results2.empty:
            print(f"   ✅ Adapter backtest successful")
            print(f"   - Results shape: {results2.shape}")
            print(f"   - Final equity: ${results2['equity'].iloc[-1]:,.2f}")
        else:
            print(f"   ❌ Adapter backtest failed - no results")
            
    except Exception as e:
        print(f"   ❌ Adapter backtest error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Longer date range (like in the original test)
    print(f"\n🔍 Test 3: Longer date range (1 week)...")
    try:
        end_date_long = datetime.now()
        start_date_long = end_date_long - timedelta(days=7)  # 1 week
        prestart_date_long = start_date_long - timedelta(days=7)  # 1 week before
        
        print(f"   - Start: {start_date_long.date()}")
        print(f"   - End: {end_date_long.date()}")
        print(f"   - Prestart: {prestart_date_long.date()}")
        
        bts3 = se.backtest.set(assets, prestart_date_long, start_date_long, end_date_long, period, 100000.0)
        
        if bts3 is None:
            print(f"   ❌ Long backtest setup failed")
            return False
        
        print(f"   ✅ Long backtest setup successful")
        
        results3 = se.backtest.run(adapted_trader, bts3)
        
        if results3 is not None and not results3.empty:
            print(f"   ✅ Long backtest successful")
            print(f"   - Results shape: {results3.shape}")
            print(f"   - Final equity: ${results3['equity'].iloc[-1]:,.2f}")
        else:
            print(f"   ❌ Long backtest failed - no results")
            
    except Exception as e:
        print(f"   ❌ Long backtest error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ All simple tests passed!")
    return True

if __name__ == "__main__":
    test_simple_backtest()

