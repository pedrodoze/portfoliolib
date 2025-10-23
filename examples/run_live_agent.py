# run_live_agent.py (O novo script do usuário)

import mt5se as se

# Importa os componentes da biblioteca
from portfoliolib import PortfolioManager, SharpeOptimizer, PortfolioAgent, EqualWeightOptimizer
# Importa as estratégias customizadas do usuário
from live_trader.live_rsi_trader import LiveRsiTrader 
import pandas as pd

def main():
    """
    Configura e executa o agente de portfólio.
    """
    trader_tech = LiveRsiTrader(name="Tech_RSI", assets_universe=['NVDA', 'GOOG'], frequency=se.INTRADAY)
    trader_finance = LiveRsiTrader(name="Finance_RSI", assets_universe=['JPM', 'GS'], frequency=se.INTRADAY)
    trader_retail = LiveRsiTrader(name="Retail_RSI", assets_universe=['WMT', 'COST'], frequency=se.INTRADAY)

    pesos_iniciais = {
        "Tech_RSI": 0.5,
        "Finance_RSI": 0.2,
        "Retail_RSI": 0.3
    }

    manager = PortfolioManager(
        traders=[trader_tech, trader_finance, trader_retail],
        optimizer=EqualWeightOptimizer(),
        initial_equity=100000.0, # Este valor é atualizado para o da conta
        initial_weights=pesos_iniciais,
    )

    agent = PortfolioAgent(
        manager=manager,
        prestart_dt = se.date(2023,1,1),
        lookback_period=pd.DateOffset(days=30),
        trade_interval_seconds=60,
        rebalance_frequency='5T',
    )
    
    agent.run()

if __name__ == "__main__":
    main()