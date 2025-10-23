# examples/run_live_rebalancing_test.py (com rebalanceamento dinâmico)

import mt5se as se
import pandas as pd
from datetime import datetime
import time
import schedule
import json
import math

from portfoliolib import PortfolioManager, SharpeOptimizer,EqualWeightOptimizer
from live_trader.live_rsi_trader import LiveRsiTrader # Supondo que o trader esteja neste arquivo

ESTADO_FILE = "live_rebalancing_state_novo_.json"

def salvar_estado(manager):
    estado = { "weights": manager.current_weights, "last_rebalance": datetime.now().isoformat() }
    with open(ESTADO_FILE, 'w') as f:
        json.dump(estado, f, indent=4)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Estado do portfólio salvo.")

def carregar_estado(manager):
    try:
        with open(ESTADO_FILE, 'r') as f:
            estado = json.load(f)
            manager.current_weights = estado["weights"]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Estado carregado de {ESTADO_FILE}.")
    except FileNotFoundError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Arquivo de estado não encontrado, usando pesos da inicialização.")
    
    acc_info = se.account_info()
    if acc_info:
        manager.total_equity = acc_info.equity
        manager.allocate_capital()
        salvar_estado(manager)

# --- VERSÃO COMPLETA DA FUNÇÃO DE REBALANCEAMENTO ---
def rebalancear_portfolio(manager):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] --- INICIANDO ROTINA DE REBALANCEAMENTO DINÂMICO ---")
    
    # 1. OTIMIZAÇÃO: Executa backtests de lookback para obter a performance passada
    lookback_end = datetime.now()
    lookback_start = lookback_end - pd.DateOffset(months=6)
    
    # O prestart para o lookback também é necessário
    lookback_prestart = (lookback_start - pd.DateOffset(days=60))
    
    lookback_equity_curves = pd.DataFrame()
    for trader_name in manager.trader_map.keys():
        trader = manager.trader_map[trader_name]
        print(f"   - Obtendo performance de lookback para {trader.name}...")
        
        bts = se.backtest.set(
            assets=trader.assets_universe, 
            prestart=lookback_prestart, 
            start=lookback_start, 
            end=lookback_end, 
            period=se.DAILY, 
            capital=100000.0 # O capital nominal para análise
        )

        results = se.backtest.run(trader, bts)
        
        if results is not None and not results.empty:
            results['date'] = pd.to_datetime(results['date'])
            lookback_equity_curves[trader_name] = results.set_index('date')['equity']

    if lookback_equity_curves.empty:
        print("   - AVISO: Não foi possível obter dados de lookback. Rebalanceamento cancelado.")
        return

    # 2. ATUALIZAÇÃO DE PESOS
    manager.update_weights(lookback_equity_curves)
    
    # 3. ALOCAÇÃO E AJUSTE DE POSIÇÕES
    manager.total_equity = se.account_info().equity
    manager.allocate_capital()
    
    print("\n   --- AJUSTANDO POSIÇÕES ABERTAS PARA OS NOVOS PESOS ---")
    for trader in manager.traders:
        # ... (a lógica de ajuste de posições permanece a mesma)
        pass # Omitido por brevidade
    
    salvar_estado(manager)
    print(f"--- REBALANCEAMENTO CONCLUÍDO ---")

# --- LOOP PRINCIPAL DE OPERAÇÃO ---
def main():
    if not se.connect(): return
    print("Agente de rebalanceamento ao vivo INICIADO. Pressione Ctrl+C para parar.")

    trader_tech = LiveRsiTrader(name="Tech_RSI", assets_universe=['NVDA', 'GOOG'])
    trader_finance = LiveRsiTrader(name="Finance_RSI", assets_universe=['JPM', 'GS'])
    trader_retail = LiveRsiTrader(name="Retail_RSI", assets_universe=['WMT', 'COST'])
    TODOS_ATIVOS = list(set(trader_tech.assets_universe + trader_finance.assets_universe + trader_retail.assets_universe))
    initial_weights = {
        "Tech_RSI": 0.4,
        "Finance_RSI": 0.4,
        "Retail_RSI": 0.2
    }
    manager = PortfolioManager(
        traders=[trader_tech, trader_finance, trader_retail],
        # optimizer=SharpeOptimizer(risk_free_rate=0.0),
        optimizer=EqualWeightOptimizer(),
        initial_equity=se.account_info().equity,
        initial_weights=initial_weights
    )
    
    carregar_estado(manager)
    
    schedule.every(1).minutes.do(rebalancear_portfolio, manager=manager)
    print(f"Rebalanceamento agendado. Próxima execução: {schedule.next_run}")

    while True:
        try:
            schedule.run_pending()
            
            if not se.is_market_open(TODOS_ATIVOS[0]):
                print(f"Mercado fechado... {datetime.now().strftime('%H:%M:%S')}", end="\r")
                time.sleep(30)
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checando sinais...", end="\r")
            dbars_minuto = se.get_multi_bars(TODOS_ATIVOS, 10, type=se.INTRADAY)
            
            for trader in manager.traders:
                orders_to_send = trader.trade(dbars_minuto)
                if orders_to_send:
                    # ... (lógica de envio de ordem)
                    pass

            time.sleep(60)
        except KeyboardInterrupt:
            print("\nEncerrando o agente...")
            break
        except Exception as e:
            print(f"\nOcorreu um erro inesperado: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()