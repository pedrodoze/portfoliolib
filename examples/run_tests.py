#!/usr/bin/env python3
"""
Test runner for portfoliolib backtester.

This script provides an easy way to run different test scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_debug_tests():
    """Run debug tests to check individual components."""
    print("🔧 Running debug tests...")
    from debug_backtester import main as debug_main
    return debug_main()

def run_full_backtest():
    """Run the full RSI traders backtest."""
    print("📊 Running full RSI backtest...")
    from test_rsi_backtest import run_backtest
    return run_backtest()

def run_individual_trader_tests():
    """Run individual trader tests."""
    print("🎯 Running individual trader tests...")
    from test_rsi_backtest import test_individual_traders
    test_individual_traders()
    return True

def main():
    """Main test runner."""
    
    print("🚀 PORTFOLIOLIB TEST RUNNER")
    print("=" * 50)
    print("Available tests:")
    print("1. Debug tests (component testing)")
    print("2. Full RSI backtest")
    print("3. Individual trader tests")
    print("4. Run all tests")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter your choice (1-4): ").strip()
    
    success = False
    
    if choice == "1":
        success = run_debug_tests()
    elif choice == "2":
        equity_curve = run_full_backtest()
        success = equity_curve is not None
    elif choice == "3":
        success = run_individual_trader_tests()
    elif choice == "4":
        print("🔄 Running all tests...")
        success = True
        
        print("\n" + "="*50)
        print("STEP 1: Debug Tests")
        print("="*50)
        if not run_debug_tests():
            print("❌ Debug tests failed")
            success = False
        
        print("\n" + "="*50)
        print("STEP 2: Individual Trader Tests")
        print("="*50)
        if not run_individual_trader_tests():
            print("❌ Individual trader tests failed")
            success = False
        
        print("\n" + "="*50)
        print("STEP 3: Full Backtest")
        print("="*50)
        equity_curve = run_full_backtest()
        if equity_curve is None:
            print("❌ Full backtest failed")
            success = False
    else:
        print("❌ Invalid choice. Please run with 1, 2, 3, or 4")
        return False
    
    if success:
        print(f"\n✅ All selected tests completed successfully!")
    else:
        print(f"\n❌ Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

