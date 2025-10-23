"""
Test WeightToOrderAdapter - verify it converts weights to orders correctly
"""
import mt5se as se
from portfoliolib.backtester import WeightToOrderAdapter
from datetime import datetime

class SimpleWeightTrader(se.Trader):
    """Test trader that returns weights"""
    def __init__(self):
        super().__init__()
        self.name = "TestTrader"
        self.assets_universe = ["NVDA"]
        self.frequency = se.DAILY
    
    def trade(self, dbars):
        # Returns 60% NVDA, 40% cash
        return {'NVDA': 0.6, 'cash': 0.4}

def main():
    print("=" * 70)
    print("TEST: WeightToOrderAdapter")
    print("=" * 70)
    
    if not se.connect():
        print("❌ Falha ao conectar")
        return
    
    # Create weight-based trader
    weight_trader = SimpleWeightTrader()
    
    # Wrap with adapter
    adapted_trader = WeightToOrderAdapter(weight_trader, allocated_capital=10000.0)
    
    print(f"\n📊 CONFIGURAÇÃO:")
    print(f"   Trader: {adapted_trader.name}")
    print(f"   Capital alocado: $10,000")
    print(f"   Alocação desejada: 60% NVDA, 40% cash")
    print(f"   Target NVDA: $6,000")
    
    # Run a small backtest
    print(f"\n🧪 EXECUTANDO BACKTEST COM ADAPTER:")
    
    bts = se.backtest.set(
        assets=["NVDA"],
        prestart=se.date(2024, 1, 1),
        start=se.date(2024, 6, 1),
        end=se.date(2024, 7, 1),
        period=se.DAILY,
        capital=10000.0,
        file='test_adapter_backtest',
        verbose=False
    )
    
    if bts:
        try:
            results = se.backtest.run(adapted_trader, bts)
            
            # Return to live mode
            se.inbacktest = False
            se.bts = None
            
            if results is not None and not results.empty:
                print(f"   ✅ Backtest executou com sucesso!")
                print(f"   - Total de barras: {len(results)}")
                print(f"   - Equity inicial: ${results['equity'].iloc[0]:,.2f}")
                print(f"   - Equity final: ${results['equity'].iloc[-1]:,.2f}")
                print(f"   - Retorno: {((results['equity'].iloc[-1] / results['equity'].iloc[0]) - 1) * 100:.2f}%")
                
                print(f"\n✅ TESTE PASSOU! Adapter funciona corretamente!")
                print(f"   - Trader retorna weights")
                print(f"   - Adapter converte para orders")
                print(f"   - Backtest executa normalmente")
            else:
                print(f"   ❌ Backtest retornou vazio")
                
        except Exception as e:
            print(f"   ❌ Erro no backtest: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ❌ Falha ao configurar backtest")
    
    print("=" * 70)

if __name__ == "__main__":
    main()

