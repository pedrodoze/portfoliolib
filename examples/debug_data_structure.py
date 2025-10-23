#!/usr/bin/env python3
"""
Debug script to check the data structure returned by MT5SE.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mt5se as se

def debug_mt5se_data():
    """Debug the data structure returned by MT5SE."""
    
    print("🔍 DEBUGGING MT5SE DATA STRUCTURE")
    print("=" * 50)
    
    # Connect to MT5
    if not se.connect():
        print("❌ Failed to connect to MetaTrader 5")
        return False
    
    print("✅ Connected to MetaTrader 5")
    
    # Test data retrieval
    assets = ['NVDA']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    prestart_date = start_date - timedelta(days=7)
    
    print(f"\n📅 Date range:")
    print(f"   - Start: {start_date.date()}")
    print(f"   - End: {end_date.date()}")
    print(f"   - Prestart: {prestart_date.date()}")
    
    # Test get_bars function
    print(f"\n🔍 Testing se.get_bars()...")
    try:
        bars = se.get_bars('NVDA', start_date, end_date, se.INTRADAY)
        
        if bars is not None and not bars.empty:
            print(f"   ✅ Bars retrieved successfully")
            print(f"   - Shape: {bars.shape}")
            print(f"   - Columns: {list(bars.columns)}")
            print(f"   - Index type: {type(bars.index)}")
            print(f"   - First few rows:")
            print(bars.head())
            
            # Check if 'time' column exists
            if 'time' in bars.columns:
                print(f"   ✅ 'time' column exists")
                print(f"   - Time range: {bars['time'].min()} to {bars['time'].max()}")
            else:
                print(f"   ❌ 'time' column missing!")
                print(f"   - Available columns: {list(bars.columns)}")
                
                # Check if time is in index
                if hasattr(bars.index, 'dtype') and 'datetime' in str(bars.index.dtype):
                    print(f"   ℹ️ Time appears to be in index")
                else:
                    print(f"   ❌ Time not found in index either")
        else:
            print(f"   ❌ No bars data retrieved")
            
    except Exception as e:
        print(f"   ❌ Error getting bars: {e}")
        import traceback
        traceback.print_exc()
    
    # Test backtest.set function
    print(f"\n🔍 Testing se.backtest.set()...")
    try:
        bts = se.backtest.set(assets, prestart_date, start_date, end_date, se.INTRADAY, 100000.0)
        
        if bts is not None:
            print(f"   ✅ Backtest setup successful")
            print(f"   - Backtest config keys: {list(bts.keys())}")
            
            # Check if dbars were created
            if 'dbars' in bts:
                print(f"   - dbars keys: {list(bts['dbars'].keys())}")
                for asset in assets:
                    if asset in bts['dbars']:
                        asset_bars = bts['dbars'][asset]
                        print(f"   - {asset} bars shape: {asset_bars.shape}")
                        print(f"   - {asset} bars columns: {list(asset_bars.columns)}")
        else:
            print(f"   ❌ Backtest setup failed")
            
    except Exception as e:
        print(f"   ❌ Error setting up backtest: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    debug_mt5se_data()

