# examples/run_multi_asset_portfolio.py

import mt5se as se
import pandas as pd
import matplotlib.pyplot as plt

# Importe os componentes da sua biblioteca e os traders do mt5se
from portfoliolib import PortfolioManager, PortfolioBacktester, SharpeOptimizer
from mt5se.sampleTraders import MultiAssetTrader

def run_multi_asset_backtest():
    """
    Executa um backtest de um portfólio onde cada estratégia (Trader)
    opera em múltiplos ativos ('NVDA' e 'GOOG').
    """
    if not se.connect():
        print("FATAL: Não foi possível conectar ao Metatrader 5.")
        return

    # --- Passo 1: Definir as Estratégias (Traders) ---
    # Cada trader será um "modelo" que opera o mesmo universo de ativos.
    # Poderíamos ter modelos diferentes operando universos diferentes.
    ASSET_LIST = ['NVDA', 'GOOG']
    START_DATE = se.date(2021, 1, 1)
    END_DATE = se.date(2023, 1, 1)
    CAPITAL = 200000.0
    PRESTART_OFFSET = pd.DateOffset(days=10)
    PRESTART_DATE = (START_DATE - PRESTART_OFFSET).to_pydatetime()

    trader_mt5se = MultiAssetTrader()
    bts_mt5se = se.backtest.set(assets=ASSET_LIST, prestart=PRESTART_DATE, start=START_DATE, end=END_DATE, period=se.DAILY, capital=CAPITAL, verbose=False)
    results_mt5se = se.backtest.run(trader_mt5se, bts_mt5se)

    if not isinstance(results_mt5se, pd.DataFrame) or results_mt5se.empty:
        return
        
    results_mt5se['date'] = pd.to_datetime(results_mt5se['date'])
    equity_mt5se = results_mt5se.set_index('date')['equity']
    print(f"Backtest mt5se concluído. Resultado Final: ${equity_mt5se.iloc[-1]:,.2f}")

    # Modelo 1: Um MultiAssetTrader com a lógica padrão de RSI.
    trader_rsi_padrao = MultiAssetTrader()
    trader_rsi_padrao.name = "RSI_Padrao_MultiAsset"
    trader_rsi_padrao.assets_universe = ['NVDA', 'GOOG']

    # Modelo 2: Para demonstrar a flexibilidade, vamos criar um segundo trader
    # que é mais conservador, comprando apenas em RSI > 80.


    # class ConservativeRSITrader(MultiAssetTrader):
    #     def trade(self, dbars):
    #         # A lógica é a mesma do MultiAssetTrader, mas com um limiar de compra diferente.
    #         assets=dbars.keys()
    #         orders=[]
    #         for asset in assets:
    #             bars=dbars[asset]
    #             curr_shares=se.get_shares(asset)
    #             # A divisão do capital é feita pelo override do backtester,
    #             # então a chamada a se.get_balance() será sobrescrita.
    #             money=se.get_balance()/len(assets)
    #             price=se.get_last(bars)
    #             free_shares=se.get_affor_shares(asset,price,money)
    #             rsi=se.tech.rsi(bars)
                
    #             # Lógica mais conservadora
    #             if rsi >= 80 and free_shares > 0: 
    #                 order = se.buyOrder(asset, free_shares)
    #             elif rsi < 70 and curr_shares > 0:
    #                 order = se.sellOrder(asset, curr_shares)
    #             else:
    #                 order = None
                
    #             if order is not None:
    #                 orders.append(order)
    #         return orders

    # trader_rsi_conservador = ConservativeRSITrader()
    # trader_rsi_conservador.name = "RSI_Conservador_MultiAsset"
    # trader_rsi_conservador.assets_universe = ['NVDA', 'GOOG']

    # --- Passo 2: Configurar o Gestor de Portfólio (nível superior) ---
    
    # O otimizador decidirá quanto capital alocar para a estratégia PADRÃO
    # e quanto para a CONSERVADORA.
    portfolio_optimizer = SharpeOptimizer(risk_free_rate=0.02)
    
    manager = PortfolioManager(
        # traders=[trader_rsi_padrao, trader_rsi_conservador],
        traders=[trader_rsi_padrao],
        optimizer=portfolio_optimizer,
        initial_equity=200000.0
        # Usará pesos iniciais iguais por padrão
    )

    # --- Passo 3: Configurar e Executar o Backtester ---
    
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=se.date(2021, 1, 1),
        end_date=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency='6MS', # Rebalanceamento a cada 6 meses, no início do mês
        prestart_offset=pd.DateOffset(days=10) # Prestart para aquecer o RSI
    )
    
    equity_portfolio = backtester.run()
    
    if equity_portfolio is None or equity_portfolio.empty:
        print("O backtest do portfólio não retornou resultados.")
        return

    # --- Passo 4: Visualizar os Resultados ---
    print("\n" + "="*50)
    print("Backtest do Portfólio Multi-Ativo por Trader concluído.")
    print(f"Resultado Final: ${equity_portfolio.iloc[-1]:,.2f}")
    
    plt.figure(figsize=(14, 8))
    equity_portfolio.plot(label="Portfólio de Estratégias Multi-Ativo", lw=2)
    equity_mt5se.plot(label="Resultado Direto (mt5se)", lw=2, ls='--')
    plt.title("Backtest: Portfólio de Estratégias Multi-Ativo")
    plt.ylabel("Patrimônio ($)")
    plt.xlabel("Data")
    plt.legend()
    plt.grid(True)
    plt.show()
    
    print("\nGráfico de comparação salvo em 'backtest_multi_asset_portfolio.png'.")

if __name__ == "__main__":
    run_multi_asset_backtest()