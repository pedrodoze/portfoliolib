# examples/run_multi_asset_portfolio.py

import mt5se as se
import pandas as pd
import matplotlib.pyplot as plt

# Importe os componentes da sua biblioteca e os traders do mt5se
from portfoliolib import PortfolioManager, PortfolioBacktester, SharpeOptimizer, EqualWeightOptimizer
from mt5se.sampleTraders import MultiAssetTrader

def run_multi_asset_backtest():
    """
    Executa um backtest de um portfólio onde cada estratégia (Trader)
    opera em múltiplos ativos ('NVDA' e 'GOOG').
    """
    if not se.connect():
        print("FATAL: Não foi possível conectar ao Metatrader 5.")
        return

    class ConservativeRSITrader(MultiAssetTrader):
        def trade(self, dbars):
            # A lógica é a mesma do MultiAssetTrader, mas com um limiar de compra diferente.
            assets=dbars.keys()
            orders=[]
            for asset in assets:
                bars=dbars[asset]
                curr_shares=se.get_shares(asset)
                money=se.get_balance()/len(assets)
                price=se.get_last(bars)
                free_shares=se.get_affor_shares(asset,price,money)
                rsi=se.tech.rsi(bars)
                
                # Lógica mais conservadora
                if rsi >= 80 and free_shares > 0: 
                    order = se.buyOrder(asset, free_shares)
                elif rsi < 70 and curr_shares > 0:
                    order = se.sellOrder(asset, curr_shares)
                else:
                    order = None
                
                if order is not None:
                    orders.append(order)
            return orders

    ASSET_LIST = ['NVDA', 'GOOG']
    START_DATE = se.date(2021, 1, 1)
    END_DATE = se.date(2023, 1, 1)
    CAPITAL = float(200000.0)
    PRESTART_OFFSET = pd.DateOffset(days=10)
    PRESTART_DATE = (START_DATE - PRESTART_OFFSET).to_pydatetime()

    multi_trader_mt5se = MultiAssetTrader()
    ConservativeRSITrader_mt5se = ConservativeRSITrader()
    bts_mt5se_1 = se.backtest.set(assets=ASSET_LIST, prestart=PRESTART_DATE, start=START_DATE, end=END_DATE, period=se.DAILY, capital=CAPITAL, verbose=False)
    bts_mt5se_2 = se.backtest.set(assets=ASSET_LIST, prestart=PRESTART_DATE, start=START_DATE, end=END_DATE, period=se.DAILY, capital=CAPITAL, verbose=False)
    results_multi_mt5se = se.backtest.run(multi_trader_mt5se, bts_mt5se_1)
    results_conservative_mt5se = se.backtest.run(ConservativeRSITrader_mt5se, bts_mt5se_2)

    if not isinstance(results_multi_mt5se, pd.DataFrame) or results_multi_mt5se.empty:
        return

    results_multi_mt5se['date'] = pd.to_datetime(results_multi_mt5se['date'])
    equity_mt5se_multi = results_multi_mt5se.set_index('date')['equity']
    equity_mt5se_multi.to_excel("C:\\Users\\pedro.borges\\Desktop\\codigo_tcc\\Resultados\\equity_multi_asset_trader.xlsx")
    if not isinstance(results_conservative_mt5se, pd.DataFrame) or results_conservative_mt5se.empty:
        return
    results_conservative_mt5se['date'] = pd.to_datetime(results_conservative_mt5se['date'])
    equity_mt5se_conservative = results_conservative_mt5se.set_index('date')['equity']
    equity_mt5se_conservative.to_excel("C:\\Users\\pedro.borges\\Desktop\\codigo_tcc\\Resultados\\equity_conservative_rsi_trader.xlsx")
    
    # Modelo 1: Um MultiAssetTrader com a lógica padrão de RSI.
    trader_rsi_padrao = MultiAssetTrader()
    trader_rsi_padrao.name = "RSI_Padrao_MultiAsset"
    trader_rsi_padrao.assets_universe = ['NVDA', 'GOOG']

    trader_conservador = ConservativeRSITrader()
    trader_conservador.name = "RSI_Conservador_MultiAsset"
    trader_conservador.assets_universe = ['NVDA', 'GOOG']


    # --- Passo 2: Configurar o Gestor de Portfólio (nível superior) ---
    
    # O otimizador decidirá quanto capital alocar para a estratégia PADRÃO
    # e quanto para a CONSERVADORA.
    portfolio_optimizer = SharpeOptimizer(risk_free_rate=0.02)
    # portfolio_optimizer = EqualWeightOptimizer()
    
    manager = PortfolioManager(
        traders=[trader_rsi_padrao, trader_conservador],
        optimizer=portfolio_optimizer,
        initial_equity=200000.0,
        initial_weights={"RSI_Padrao_MultiAsset": 0, "RSI_Conservador_MultiAsset": 1}
    )

    # --- Passo 3: Configurar e Executar o Backtester ---
    
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=se.date(2021, 1, 1),
        end_date=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency='6MS',
        prestart_offset=pd.DateOffset(days=10)
    )
    
    equity_portfolio = backtester.run()
    
    if equity_portfolio is None or equity_portfolio.empty:
        print("O backtest do portfólio não retornou resultados.")
        return

    print("\n" + "="*50)
    print("Backtest do Portfólio Multi-Ativo por Trader concluído.")
    print(f"Resultado Final: ${equity_portfolio.iloc[-1]:,.2f}")
    equity_portfolio.to_excel("C:\\Users\\pedro.borges\\Desktop\\codigo_tcc\\Resultados\\equity_portfolio_multi_asset.xlsx")

if __name__ == "__main__":
    run_multi_asset_backtest()