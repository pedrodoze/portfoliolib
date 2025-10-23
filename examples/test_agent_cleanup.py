"""
Test that the agent's _close_all_positions() works correctly
"""
import mt5se as se
import MetaTrader5 as mt5
from portfoliolib import PortfolioManager, PortfolioAgent, EqualWeightOptimizer
from datetime import datetime
import pandas as pd

class DummyTrader(se.Trader):
    """Dummy trader - doesn't trade, just for testing"""
    def __init__(self, name, assets):
        super().__init__()
        self.name = name
        self.assets_universe = assets
        self.frequency = se.DAILY

    def trade(self, dbars):
        return []

def get_real_positions():
    """Get real positions from MT5"""
    positions = mt5.positions_get()
    if not positions:
        return {}
    
    result = {}
    for pos in positions:
        if pos.symbol not in result:
            result[pos.symbol] = 0.0
        
        if pos.type == 0:  # BUY
            result[pos.symbol] += pos.volume
        else:  # SELL
            result[pos.symbol] -= pos.volume
    
    return result

def main():
    print("=" * 70)
    print("TEST: Agent Cleanup (_close_all_positions)")
    print("=" * 70)
    
    if not se.connect():
        print("❌ Falha ao conectar")
        return
    
    # Show positions BEFORE
    print(f"\n📊 POSIÇÕES ANTES DO CLEANUP:")
    positions_before = get_real_positions()
    
    if not positions_before:
        print("   ✅ Nenhuma posição (conta já limpa)")
    else:
        for symbol, net in sorted(positions_before.items()):
            print(f"   {symbol}: {net:+.1f}")
    
    # Create agent
    print(f"\n" + "=" * 70)
    print("CRIANDO AGENT (vai executar cleanup no startup)...")
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
        state_file="test_agent_cleanup_state.json"
    )
    
    # Manually call cleanup (normally called in run())
    print(f"\n>>> EXECUTANDO CLEANUP DO AGENT <<<")
    print("=" * 70)
    
    success = agent._close_all_positions()
    
    # Show positions AFTER
    print(f"\n" + "=" * 70)
    print(f"📊 POSIÇÕES DEPOIS DO CLEANUP:")
    print("=" * 70)
    
    positions_after = get_real_positions()
    
    if not positions_after:
        print("   ✅ Nenhuma posição (tudo fechado!)")
    else:
        for symbol, net in sorted(positions_after.items()):
            if abs(net) < 0.01:
                print(f"   {symbol}: 0.0 ✅")
            else:
                print(f"   {symbol}: {net:+.1f} ❌")
    
    # Verification
    print(f"\n" + "=" * 70)
    print("VERIFICAÇÃO FINAL:")
    print("=" * 70)
    
    all_zero = all(abs(net) < 0.01 for net in positions_after.values()) if positions_after else True
    
    if all_zero and len(positions_after) == 0:
        print("🎉 TESTE PASSOU! Agent cleanup funcionou perfeitamente!")
        print("   ✅ Todas as posições foram fechadas")
        print("   ✅ Conta está 100% em cash")
    elif all_zero:
        print("✅ TESTE PASSOU! Todas as posições estão em zero")
    else:
        print("❌ TESTE FALHOU! Ainda existem posições abertas")
        print("   Verifique o MT5 terminal")
    
    print("=" * 70)

if __name__ == "__main__":
    main()

