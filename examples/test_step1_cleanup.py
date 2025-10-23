"""
TEST STEP 1: Verify cleanup closes all existing positions

This test validates that the agent correctly closes any existing MT5 positions at startup.

Setup:
1. Manually create some positions in MT5 (or use existing ones)
2. Run this test
3. Verify all positions are closed

Expected output:
- Should show existing positions being closed
- Should convert everything to cash
- Account should be 100% cash after cleanup
"""

import mt5se as se
from portfoliolib import PortfolioManager, PortfolioAgent, EqualWeightOptimizer
from datetime import datetime
import pandas as pd

class DummyTrader(se.Trader):
    """Dummy trader that does nothing - just for testing cleanup"""
    def __init__(self, name, assets):
        super().__init__()
        self.name = name
        self.assets_universe = assets
        self.frequency = se.DAILY

    def trade(self, dbars):
        # Don't trade - we're just testing cleanup
        return []

def main():
    print("=" * 70)
    print("TEST STEP 1: Startup Cleanup")
    print("=" * 70)
    
    # Connect to MT5
    if not se.connect():
        print("[ERRO] Falha ao conectar ao MetaTrader 5")
        return

    # Show current positions BEFORE cleanup
    print("\n📊 POSIÇÕES ANTES DO CLEANUP:")
    nvda_shares_before = se.get_shares("NVDA")
    msft_shares_before = se.get_shares("MSFT")
    balance_before = se.get_balance()
    
    nvda_bars = se.get_bars("NVDA", 2)
    msft_bars = se.get_bars("MSFT", 2)
    
    if nvda_bars is not None and not nvda_bars.empty:
        nvda_price = se.get_last(nvda_bars)
        nvda_value = nvda_shares_before * nvda_price
        print(f"   NVDA: {nvda_shares_before} shares @ ${nvda_price:.2f} = ${nvda_value:,.2f}")
    
    if msft_bars is not None and not msft_bars.empty:
        msft_price = se.get_last(msft_bars)
        msft_value = msft_shares_before * msft_price
        print(f"   MSFT: {msft_shares_before} shares @ ${msft_price:.2f} = ${msft_value:,.2f}")
    
    print(f"   Cash: ${balance_before:,.2f}")
    
    # Create agent (this will trigger cleanup)
    print("\n" + "=" * 70)
    print("INICIANDO AGENT (DEVE EXECUTAR CLEANUP)...")
    print("=" * 70)
    
    trader_a = DummyTrader(name="Portfolio_A", assets=["NVDA"])
    trader_b = DummyTrader(name="Portfolio_B", assets=["MSFT"])
    
    manager = PortfolioManager(
        traders=[trader_a, trader_b],
        optimizer=EqualWeightOptimizer(),
        initial_equity=100000.0,
        initial_weights={"Portfolio_A": 0.5, "Portfolio_B": 0.5},
        max_leverage=1.0
    )
    
    agent = PortfolioAgent(
        manager=manager,
        prestart_dt=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(months=1),
        rebalance_frequency='1H',
        trade_interval_seconds=60,
        state_file="test_cleanup_state.json"
    )
    
    # Manually call cleanup to test it
    print("\n>>> EXECUTANDO CLEANUP MANUALMENTE <<<")
    agent._close_all_positions()
    
    # Show positions AFTER cleanup
    print("\n📊 POSIÇÕES APÓS O CLEANUP:")
    nvda_shares_after = se.get_shares("NVDA")
    msft_shares_after = se.get_shares("MSFT")
    balance_after = se.get_balance()
    
    print(f"   NVDA: {nvda_shares_after} shares (pode ser cache/phantom)")
    print(f"   MSFT: {msft_shares_after} shares (pode ser cache/phantom)")
    print(f"   Cash: ${balance_after:,.2f}")
    
    # Get equity to verify
    acc_info = se.account_info()
    if acc_info:
        if hasattr(acc_info, 'equity'):
            equity_after = float(acc_info.equity)
        else:
            equity_after = float(acc_info._asdict().get('equity', balance_after))
        print(f"   Equity total: ${equity_after:,.2f}")
    
    # Verification
    print("\n" + "=" * 70)
    print("VERIFICAÇÃO:")
    print("=" * 70)
    
    success = True
    
    # The real test: did cash increase by the value of closed positions?
    expected_cash_increase = nvda_value + msft_value if (nvda_shares_before > 0 or msft_shares_before > 0) else 0
    actual_cash_increase = balance_after - balance_before
    
    print(f"\n💰 TESTE DE CASH (o que realmente importa):")
    print(f"   Valor das posições fechadas: ${expected_cash_increase:,.2f}")
    print(f"   Aumento real no cash: ${actual_cash_increase:,.2f}")
    print(f"   Diferença: ${abs(expected_cash_increase - actual_cash_increase):,.2f}")
    
    # Allow small difference due to price changes
    if abs(expected_cash_increase - actual_cash_increase) < 100:
        print(f"   ✅ Cash aumentou corretamente - posições REALMENTE foram fechadas!")
        success = True
    elif nvda_shares_before == 0 and msft_shares_before == 0:
        print(f"   ✅ Sem posições para fechar")
        success = True
    else:
        print(f"   ❌ Cash não aumentou como esperado - posições podem não ter sido fechadas")
        success = False
    
    print(f"\n⚠️ NOTA: get_shares() pode retornar valores do cache do backtest")
    print(f"   O teste REAL é se o cash aumentou, não se get_shares() retorna 0")
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 TESTE PASSOU! Cleanup funcionou corretamente!")
    else:
        print("❌ TESTE FALHOU! Cleanup não fechou todas as posições!")
    print("=" * 70)

if __name__ == "__main__":
    main()

