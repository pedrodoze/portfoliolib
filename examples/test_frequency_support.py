# test_frequency_support.py
import pandas as pd
from datetime import datetime
import sys
import os
import mt5se as se

# Adiciona o diretório pai ao path para importar portfoliolib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from portfoliolib.manager import PortfolioManager
from portfoliolib.optimizers import EqualWeightOptimizer
from portfoliolib.backtester import PortfolioBacktester
from portfoliolib import PortfolioAgent
from live_trader.live_rsi_trader import GuaranteedSignalTrader, LiveRsiTrader, AlwaysBuyTrader

# Mock do mt5se para simular frequências
# from guaranteed_signal_trader import GuaranteedSignalTrader

trader_test = GuaranteedSignalTrader(
    name="Test_Trader",
    assets_universe=["NVDA"],
    frequency=se.DAILY
)
trader_test = AlwaysBuyTrader(
    name="TestBuy",
    assets_universe=["NVDA"],
    frequency=se.DAILY
)
se.connect()
# Trader intraday
trader_tech = LiveRsiTrader(name="Tech_RSI", assets_universe=['NVDA', 'GOOG'], frequency=se.H1, rsi_window=15, rsi_oversold=30)
trader_finance = LiveRsiTrader(name="Finance_RSI", assets_universe=['JPM', 'GS'], frequency=se.DAILY, rsi_window=10, rsi_oversold=25)
trader_retail = LiveRsiTrader(name="Retail_RSI", assets_universe=['WMT', 'COST'], frequency=se.DAILY, rsi_window=14, rsi_oversold=30)

def test_backtest_with_mixed_frequencies():
    print("=== Teste: Suporte a Frequências Mistas (Intraday + Daily) ===\n")
    START_DATE = se.date(2023, 1, 1)
    END_DATE = se.date(2025, 1, 1)
    PRESTART_DATE = se.date(2021, 1, 1)
    
    manager = PortfolioManager(
        # traders=[trader_tech, trader_finance, trader_retail],
        traders=[trader_tech],
        optimizer=EqualWeightOptimizer(),
        initial_equity=100000.0, # Este valor é atualizado para o da conta
        target_volatility=0.10,  # 10% anual
        max_leverage=3.0
        
    )
    bts_mt5se = se.backtest.set(assets=['NVDA', 'GOOG'], prestart=PRESTART_DATE, start=START_DATE, end=END_DATE, period=se.H1, capital=100000.0, verbose=False)
    results_mt5se = se.backtest.run(trader_tech, bts_mt5se)
    print(f"Backtest mt5se concluído. Resultado Final: ${results_mt5se['equity'].iloc[-1]:,.2f}")
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=START_DATE,
        end_date=END_DATE,
        prestart_dt=PRESTART_DATE,
        lookback_period=pd.DateOffset(months=12),
        rebalance_frequency='MS' # A cada 6 meses, no início do mês
    )
    backtester.run()
    # agent.run()
if __name__ == "__main__":
    test_backtest_with_mixed_frequencies()
    se.connect()
    print(se.account_info())  # Deve retornar dados reais
    se.connect()
    price = se.get_last(se.get_bars("NVDA", 1))
    shares = se.get_affor_shares("NVDA", price, 10000)
    print("Shares calculados:", shares)  # Deve ser > 0