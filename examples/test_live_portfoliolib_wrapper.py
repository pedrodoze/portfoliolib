# examples/test_live_portfoliolib_wrapper.py (versão corrigida)

import mt5se as se
from datetime import datetime
import time

# Importe os componentes da sua biblioteca e o mesmo trader
from portfoliolib import PortfolioManager, EqualWeightOptimizer
# Supondo que o trader esteja em examples/traders/rsi_trader_m10.py
from live_trader.rsi_trader_m10 import RsiM10Trader # Importa o nosso trader

def run_portfolio_test():
    """
    Testa o RsiM10Trader sendo gerenciado pelo PortfolioManager.
    """
    if not se.connect():
        print("FATAL: Não foi possível conectar ao Metatrader 5.")
        return

    print("="*50)
    print("INICIANDO TESTE AO VIVO: PORTFOLIOLIB Wrapper")
    print("="*50)

    # 1. Defina os ativos
    ASSET_LIST = ['NVDA', 'GOOG']

    # 2. Crie uma instância do trader
    trader = RsiM10Trader(name="RSI_M10_Portfolio", assets_universe=ASSET_LIST)
    
    # 3. Configure o PortfolioManager
    manager = PortfolioManager(
        traders=[trader],
        optimizer=EqualWeightOptimizer(),
        initial_equity=se.account_info().equity
    )
    manager.allocate_capital()

    # 4. Crie o loop de operação manual
    endTime = se.now(minOffset=5)
    print(f"Agente '{trader.name}' iniciado via portfoliolib. Operando por 5 minutos... Pressione Ctrl+C para parar.")

    while datetime.now() < endTime:
        try:
            if not se.is_market_open(ASSET_LIST[0]):
                print("Mercado fechado...", end="\r")
                time.sleep(30)
                continue
            
            print(f"Checando sinais... {datetime.now().strftime('%H:%M:%S')}", end="\r")
            
            # --- CORREÇÃO PRINCIPAL AQUI ---
            # O parâmetro para timeframe em get_multi_bars é 'type', não 'timeFrame'.
            dbars_minuto = se.get_multi_bars(ASSET_LIST, 10, type=se.INTRADAY)
            
            # Executa a lógica de trade do nosso único trader
            orders_to_send = manager.traders[0].trade(dbars_minuto)

            if orders_to_send:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Modelo '{trader.name}' gerou ordens:")
                for order in orders_to_send:
                    if se.checkOrder(order) and se.sendOrder(order):
                        print(f"  -> ORDEM ENVIADA: {order}")
                    else:
                        print(f"  -> FALHA AO ENVIAR ORDEM: {se.getLastError()}")

            time.sleep(60) # Espera 1 minuto

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nErro no loop: {e}")
            time.sleep(30)

    print("\nTeste ao vivo com portfoliolib concluído.")

if __name__ == "__main__":
    run_portfolio_test()