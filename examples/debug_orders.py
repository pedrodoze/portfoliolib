#!/usr/bin/env python3
"""
Debug script to check what orders are being returned.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mt5se as se
from portfoliolib.backtester import WeightToOrderAdapter

class DebugTrader(se.Trader):
    """Debug trader to see what's happening."""
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.frequency = se.INTRADAY
        self.assets_universe = ['NVDA']
        
    def setup(self, dbars):
        print(f"[{self.name}] Setup called")
        
    def trade(self, dbars, my_positions=None):
        """Debug what's being passed and returned."""
        print(f"[{self.name}] trade() called")
        print(f"   - dbars type: {type(dbars)}")
        print(f"   - dbars keys: {list(dbars.keys()) if isinstance(dbars, dict) else 'Not a dict'}")
        print(f"   - my_positions: {my_positions}")
        
        # Return empty list (no orders)
        result = []
        print(f"   - Returning: {result} (type: {type(result)})")
        return result
    
    def ending(self, dbars):
        print(f"[{self.name}] Ending called")

def test_debug_orders():
    """Test to see what orders are being returned."""
    
    print("🔍 DEBUG ORDERS TEST")
    print("=" * 30)
    
    # Connect to MT5
    if not se.connect():
        print("❌ Failed to connect to MetaTrader 5")
        return False
    
    print("✅ Connected to MetaTrader 5")
    
    # Short date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    prestart_date = start_date - timedelta(days=1)
    
    print(f"\n📅 Date range:")
    print(f"   - Start: {start_date.date()}")
    print(f"   - End: {end_date.date()}")
    print(f"   - Prestart: {prestart_date.date()}")
    
    # Test 1: Direct trader
    print(f"\n🔍 Test 1: Direct trader...")
    try:
        trader = DebugTrader("DirectTrader")
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
        else:
            print(f"   ❌ Direct backtest failed - no results")
            
    except Exception as e:
        print(f"   ❌ Direct backtest error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: With adapter
    print(f"\n🔍 Test 2: With adapter...")
    try:
        trader2 = DebugTrader("AdapterTrader")
        adapted_trader = WeightToOrderAdapter(trader2, allocated_capital=100000.0)
        
        bts2 = se.backtest.set(assets, prestart_date, start_date, end_date, period, 100000.0)
        results2 = se.backtest.run(adapted_trader, bts2)
        
        if results2 is not None and not results2.empty:
            print(f"   ✅ Adapter backtest successful")
            print(f"   - Results shape: {results2.shape}")
        else:
            print(f"   ❌ Adapter backtest failed - no results")
            
    except Exception as e:
        print(f"   ❌ Adapter backtest error: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    test_debug_orders()

