"""
Simple test - single trader backtest to verify adapter works
"""
import mt5se as se
from datetime import datetime, timedelta
from portfoliolib.backtester import WeightToOrderAdapter
import pandas as pd

class SimpleFixedWeightTrader(se.Trader):
    """Returns FIXED weights every time - easy to test"""
    def __init__(self):
        super().__init__()
        self.name = "SimpleTrader"
        self.assets_universe = ["NVDA"]
        self.frequency = se.DAILY
        self.call_count = 0
    
    def trade(self, dbars, my_positions=None):
        self.call_count += 1
        
        # Always return 80% NVDA, 20% cash
        weights = {'NVDA': 0.8, 'cash': 0.2}
        
        # Print every 10 calls to see progress
        if self.call_count % 10 == 0:
            print(f"      [Call #{self.call_count}] Weights: {weights}, Positions: {my_positions}")
        
        return weights

def main():
    print("=" * 70)
    print("TEST: Simple Backtest - Fixed 80% NVDA")
    print("=" * 70)
    
    if not se.connect():
        return
    
    trader = SimpleFixedWeightTrader()
    adapted = WeightToOrderAdapter(trader, allocated_capital=100000.0)
    
    # Run short backtest
    print("\n🧪 Running backtest (last 30 days)...")
    
    bts = se.backtest.set(
        assets=["NVDA"],
        prestart=datetime.now() - timedelta(days=60),
        start=datetime.now() - timedelta(days=30),
        end=datetime.now() - timedelta(days=1),
        period=se.DAILY,
        capital=100000.0,
        file='test_simple_backtest',
        verbose=False
    )
    
    if bts:
        results = se.backtest.run(adapted, bts)
        
        # Clean up
        se.inbacktest = False
        se.bts = None
        
        print(f"\n📊 RESULTADOS:")
        if results is not None and not results.empty:
            print(f"   Total calls to trade(): {trader.call_count}")
            print(f"   Bars simulated: {len(results)}")
            print(f"   Equity inicial: ${results['equity'].iloc[0]:,.2f}")
            print(f"   Equity final: ${results['equity'].iloc[-1]:,.2f}")
            
            ret = (results['equity'].iloc[-1] / results['equity'].iloc[0] - 1) * 100
            print(f"   Retorno: {ret:.2f}%")
            
            if ret != 0:
                print(f"\n   ✅ TRADES ACONTECERAM! Equity mudou!")
            else:
                print(f"\n   ❌ NENHUM TRADE! Equity não mudou!")
                print(f"   Provável causa: Adapter não está convertendo weights corretamente")
        else:
            print(f"   ❌ Backtest retornou vazio")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
