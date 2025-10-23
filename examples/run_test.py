# examples/run_test.py

import pandas as pd
import numpy as np
from datetime import datetime

# Importa as classes da sua biblioteca recém-instalada
from portfoliolib import (
    PortfolioManager, 
    PortfolioBacktester, 
    EqualWeightOptimizer, 
    SharpeOptimizer
)
from mt5se import Trader

# --- Simulação do Ambiente MT5SE (para rodar sem conexão real) ---

# b. Criar classes FakeTrader
class FakeTrader(Trader):
    """Um trader falso que negocia um único ativo e gera retornos aleatórios."""
    def __init__(self, asset_name: str):
        self.asset = asset_name
        self.capital = 0

    def trade(self, dbars):
        # A lógica de negociação não é necessária para este teste
        return []

# Função que simula (mock) o `se.backtest.run`
def mock_backtest_runner(trader_name: str, start: datetime, end: datetime) -> pd.Series:
    """
    Esta função substitui a chamada real ao `se.backtest.run`.
    Ela gera uma série de retornos diários aleatórios para um trader,
    simulando o resultado de um backtest.
    """
    print(f"      (MOCK) Simulando backtest para '{trader_name}' de {start.date()} a {end.date()}")
    date_range = pd.date_range(start, end, freq='B') # 'B' para dias úteis
    # Gera retornos aleatórios com uma pequena tendência positiva
    random_returns = np.random.normal(loc=0.0005, scale=0.015, size=len(date_range))
    return pd.Series(random_returns, index=date_range)

# --- Configuração e Execução do Backtest do Portfólio ---

if __name__ == "__main__":
    # a. Instanciar traders falsos
    trader1 = FakeTrader(asset_name="CPB")
    trader2 = FakeTrader(asset_name="YUMC")
    trader3 = FakeTrader(asset_name="ABEV")

    # b. Instanciar um otimizador
    # optimizer = EqualWeightOptimizer()
    optimizer = SharpeOptimizer(risk_free_rate=0.02)
    
    # c. Instanciar o PortfolioManager
    manager = PortfolioManager(
        traders=[trader1, trader2, trader3],
        optimizer=optimizer,
        initial_equity=100000.0
    )

    # d. Instanciar o PortfolioBacktester
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=datetime(2022, 1, 1),
        end_date=datetime(2023, 12, 31),
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency=pd.DateOffset(months=1)
    )

    # e. Executar o backtest, passando nossa função MOCK
    final_equity_curve = backtester.run(backtest_runner=mock_backtest_runner)

    print("\n--- Curva de Capital Final do Portfólio ---")
    print(final_equity_curve.tail())