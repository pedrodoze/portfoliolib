# examples/run_debug_comparison.py (com lógica RSI 60/40)

import mt5se as se
import pandas as pd

from portfoliolib import PortfolioManager, PortfolioBacktester, EqualWeightOptimizer
from mt5se.sampleTraders import MultiAssetTrader

# --- 1. Definição da Estratégia com a Lógica Ajustada ---
class Rsi6040Trader(MultiAssetTrader):
    """
    Trader que implementa a estratégia RSI 60/40.
    - Compra se RSI >= 60 e não há posição.
    - Vende para zerar se RSI <= 40 e há posição.
    """
    def trade(self, dbars):
        orders = []
        assets = list(dbars.keys())
        if not assets: return []
        
        capital_per_asset = se.get_balance() / len(assets)

        for asset in assets:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue
            
            bars = dbars[asset]
            rsi = se.tech.rsi(bars) # RSI padrão de 14 períodos
            current_shares = se.get_shares(asset)
            
            # --- LÓGICA DE TRADING AJUSTADA ---
            if rsi >= 60:
                # Só compra se não tiver uma posição aberta
                if current_shares == 0:
                    price = se.get_last(bars)
                    shares_to_buy = se.get_affor_shares(asset, price, capital_per_asset)
                    if shares_to_buy > 0:
                        print(f"   - [SINAL] COMPRA para {asset} (RSI={rsi:.2f})")
                        orders.append(se.buyOrder(asset, shares_to_buy))
            elif rsi <= 40:
                # Só vende se tiver uma posição comprada para zerar
                if current_shares > 0:
                    print(f"   - [SINAL] VENDA (Zerar) para {asset} (RSI={rsi:.2f})")
                    orders.append(se.sellOrder(asset, current_shares))
            # --- FIM DO AJUSTE ---

        return orders

def run_debug():
    if not se.connect():
        print("FATAL: Não foi possível conectar ao Metatrader 5.")
        return

    # --- 2. Configurações do Teste ---
    ASSET_LIST = ['NVDA']
    START_DATE = se.date(2021, 7, 1)
    END_DATE = se.date(2021, 12, 31)
    CAPITAL = 100000.0
    PRESTART_OFFSET = pd.DateOffset(days=60)
    PRESTART_DATE = (START_DATE - PRESTART_OFFSET).to_pydatetime()

    # --- 3. Execução Direta com mt5se (Nossa Referência) ---
    print("="*50)
    print("Executando backtest de referência com mt5se (RSI 60/40)...")
    print("="*50)
    
    trader_mt5se = Rsi6040Trader()
    trader_mt5se.assets_universe = ASSET_LIST
    
    bts_mt5se = se.backtest.set(
        assets=ASSET_LIST,
        prestart=PRESTART_DATE,
        start=START_DATE,
        end=END_DATE,
        period=se.DAILY,
        capital=CAPITAL
    )
    results_mt5se = se.backtest.run(trader_mt5se, bts_mt5se)

    print("\n--- Resultado do Backtest Direto (mt5se) ---")
    if isinstance(results_mt5se, pd.DataFrame) and not results_mt5se.empty:
        equity_mt5se = results_mt5se.set_index('date')['equity']
        print(f"Performance: {(equity_mt5se.iloc[-1] / equity_mt5se.iloc[0] - 1):.2%}")
    else:
        print("O backtest direto não retornou dados ou trades.")

    # --- 4. Execução com PortfolioBacktester ---
    print("\n" + "="*50)
    print("Executando backtest com PortfolioBacktester (RSI 60/40)...")
    print("="*50)
    
    trader_portfolio = Rsi6040Trader()
    trader_portfolio.name = "agressivo_model"
    trader_portfolio.assets_universe = ASSET_LIST
    
    manager = PortfolioManager(
        traders=[trader_portfolio],
        optimizer=EqualWeightOptimizer(),
        initial_equity=CAPITAL,
        prestart_offset=PRESTART_OFFSET
    )

    backtester = PortfolioBacktester(
        manager=manager,
        start_date=START_DATE,
        end_date=END_DATE,
        lookback_period=pd.DateOffset(months=12),
        rebalance_frequency='24MS'
    )
    
    equity_portfolio = backtester.run()
    
    print("\n--- Resultado do Backtest com PortfolioLib ---")
    if equity_portfolio is not None and not equity_portfolio.empty:
        print(f"Performance: {(equity_portfolio.iloc[-1] / equity_portfolio.iloc[0] - 1):.2%}")
    else:
        print("O backtest do portfólio não retornou resultados.")

if __name__ == "__main__":
    run_debug()