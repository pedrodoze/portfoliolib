# examples/run_mt5se_backtest.py

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Importa as classes da sua biblioteca
from portfoliolib import (
    PortfolioManager, 
    PortfolioBacktester, 
    SharpeOptimizer,
    EqualWeightOptimizer
)

# Importa os traders de exemplo diretamente da biblioteca mt5se
from mt5se.sampleTraders import MultiAssetTrader, SimpleAITrader
import mt5se as se
from live_trader.live_rsi_trader import LiveRsiTrader 

def main():
    """Função principal para executar o backtest."""
    
    print("Iniciando conexão com o Metatrader 5...")
    if not se.connect():
        print("Falha ao conectar ao Metatrader 5. Verifique se o terminal está em execução.")
        return

    print("Conexão estabelecida com sucesso.")
    
    # trader_rsi = MultiAssetTrader()
    # trader_ai = SimpleAITrader()
    
    trader_tech = LiveRsiTrader(name="Tech_RSI", assets_universe=['NVDA', 'GOOG'], frequency=se.DAILY)
    trader_finance = LiveRsiTrader(name="Finance_RSI", assets_universe=['JPM', 'GS'], frequency=se.INTRADAY)
    trader_retail = LiveRsiTrader(name="Retail_RSI", assets_universe=['WMT', 'COST'], frequency=se.H1)

    traders_list = [trader_tech]
    # assets_list = ['GOOG', 'MSFT']
    optimizer = EqualWeightOptimizer() 
    
    # 4. Instanciar o PortfolioManager
    manager = PortfolioManager(
        traders=traders_list,
        optimizer=optimizer,
        initial_equity=100000.0, # Este valor é atualizado para o da conta
        target_volatility=0.10,  # 10% anual
        max_leverage=3.0
    )

    backtester = PortfolioBacktester(
        manager=manager,
        prestart=pd.Timestamp(2020, 12, 1), # Período de pré-start para o lookback inicial
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2022, 1, 1),
        lookback_period=pd.DateOffset(months=6),      # Janela de 6 meses para otimização
        rebalance_frequency=pd.DateOffset(months=1) # Rebalanceamento mensal
    )
    
    
    try:
        final_equity_curve = backtester.run()

        print("\n--- Curva de Capital Final do Portfólio ---")
        print(final_equity_curve.tail(10))
        plt.figure(figsize=(12, 8))
        final_equity_curve.plot()
        plt.title('Curva de Capital do Portfólio (Walk-Forward Backtest)')
        plt.xlabel('Data')
        plt.ylabel('Patrimônio ($)')
        plt.grid(True)
        plt.savefig(r'C:\\Users\\pedro.borges\\Desktop\\codigo_tcc\\Resultados\\portfolio_equity_curve_equal.png')
        final_equity_curve.to_csv(r'C:\\Users\\pedro.borges\\Desktop\\codigo_tcc\\Resultados\\portfolio_equity_curve_equal.csv')
    except Exception as e:
        print(f"\nOcorreu um erro durante a execução do backtest: {e}")
        print("Verifique se sua instalação do Metatrader 5 possui dados históricos para os ativos e datas solicitadas.")

if __name__ == "__main__":
    main()