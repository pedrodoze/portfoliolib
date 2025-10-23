# test_target_volatility_live.py
import mt5se as se
from datetime import datetime
import pandas as pd
from live_trader.deterministic_volatility_trader import DeterministicVolatilityTrader
from portfoliolib import PortfolioManager, PortfolioAgent, EqualWeightOptimizer

def main():
    if not se.connect():
        print("❌ Falha ao conectar ao MT5")
        return

    # Cria dois traders com comportamento previsível
    trader_a = DeterministicVolatilityTrader(
        name="LowVol_Trader",
        assets_universe=["GOOG"],   # Forex: volatilidade baixa (~5-8% anual)
        shares_to_buy=100           # 0.1 lote
    )
    trader_b = DeterministicVolatilityTrader(
        name="HighVol_Trader",
        assets_universe=["NVDA"],   # Ações: volatilidade alta (~15-25% anual)
        shares_to_buy=10              # 10 ações
    )

    # Pesos iniciais desbalanceados
    initial_weights = {
        "LowVol_Trader": 0.3,
        "HighVol_Trader": 0.7
    }

    manager = PortfolioManager(
        traders=[trader_a, trader_b],
        optimizer=EqualWeightOptimizer(),
        initial_equity=10000.0,
        initial_weights=initial_weights,
        target_volatility=0.1,    # 10% alvo
        max_leverage=5.0          # Permite ajuste
        # volatility_floor=0.001
    )

    agent = PortfolioAgent(
        manager=manager,
        prestart_dt=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(days=60),  # Janela estável
        rebalance_frequency='5T',                # Rebalanceia a cada 5 minutos
        trade_interval_seconds=30,
        state_file="test_vol_state.json"
    )

    print("✅ Iniciando teste de target volatility com traders determinísticos")
    agent.run()

if __name__ == "__main__":
    main()