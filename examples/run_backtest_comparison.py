# examples/run_backtest_comparison.py (versão final)

import mt5se as se
import pandas as pd
import matplotlib.pyplot as plt

from portfoliolib import PortfolioManager, PortfolioBacktester, EqualWeightOptimizer
from mt5se.sampleTraders import SimpleAITrader

def run_comparison():
    if not se.connect():
        return

    # --- Configurações ---
    ASSET_LIST = ['NVDA']
    START_DATE = se.date(2020, 1, 1)
    END_DATE = se.date(2023, 7, 1)
    CAPITAL = 100000.0
    PRESTART_DATE = se.date(2019, 1, 1)

    # --- 1. Execução Direta com mt5se (Nossa Referência) ---
    print("="*50)
    print("Executando backtest diretamente com mt5se...")
    trader_mt5se = SimpleAITrader()
    bts_mt5se = se.backtest.set(assets=ASSET_LIST, prestart=PRESTART_DATE, start=START_DATE, end=END_DATE, period=se.DAILY, capital=CAPITAL, verbose=False)
    results_mt5se = se.backtest.run(trader_mt5se, bts_mt5se)

    if not isinstance(results_mt5se, pd.DataFrame) or results_mt5se.empty:
        return
        
    results_mt5se['date'] = pd.to_datetime(results_mt5se['date'])
    equity_mt5se = results_mt5se.set_index('date')['equity']
    
    print(f"Backtest mt5se concluído. Resultado Final: ${equity_mt5se.iloc[-1]:,.2f}")

    # --- 2. Execução com PortfolioBacktester ---
    print("\n" + "="*50)
    print("Executando backtest com PortfolioBacktester...")
    
    trader_portfolio = SimpleAITrader()
    trader_portfolio.name = "NVDA_AI_Model"
    trader_portfolio.assets_universe = ASSET_LIST
    
    # Usamos 100% de peso inicial, já que é um teste de comparação com um único trader
    initial_weights = {"NVDA_AI_Model": 1.0}
    
    manager = PortfolioManager(
        traders=[trader_portfolio],
        optimizer=EqualWeightOptimizer(),
        initial_equity=CAPITAL,
        initial_weights=initial_weights
    )

    backtester = PortfolioBacktester(
        manager=manager,
        start_date=START_DATE,
        end_date=END_DATE,
        prestart_dt=PRESTART_DATE,
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency='6MS' # A cada 6 meses, no início do mês
    )
    
    equity_portfolio = backtester.run()
    print(equity_portfolio)
    if equity_portfolio is None or equity_portfolio.empty: return

    print(f"Backtest do portfólio concluído. Resultado Final: ${equity_portfolio.iloc[-1]:,.2f}")

    # --- 3. Comparação ---
    plt.figure(figsize=(14, 8))
    equity_mt5se.plot(label="Resultado Direto (mt5se)", lw=2, ls='--')
    equity_portfolio.plot(label="Resultado via PortfolioBacktester", lw=2, ls='-')
    plt.title("Comparação de Backtest: mt5se vs portfoliolib")
    plt.legend()
    plt.grid(True)
    # plt.savefig("backtest_comparison_final.png")
    plt.show()
    print("\nGráfico salvo em 'backtest_comparison_final.png'. As curvas devem ser idênticas.")

if __name__ == "__main__":
    run_comparison() 