# examples/test_live_mt5se_direct.py

import mt5se as se
from datetime import datetime
from live_trader.rsi_trader_m10 import RsiM10Trader # Importa o nosso trader

def run_direct_test():
    """
    Testa o RsiM10Trader usando o orquestrador nativo do mt5se.
    """
    if not se.connect():
        print("FATAL: Não foi possível conectar ao Metatrader 5.")
        return

    print("="*50)
    print("INICIANDO TESTE AO VIVO: MT5SE DIreto")
    print("="*50)

    # 1. Defina os ativos para a estratégia
    ASSET_LIST = ['NVDA', 'GOOG']
    
    # 2. Crie uma instância do seu trader
    trader = RsiM10Trader(name="RSI_M10_Direct", assets_universe=ASSET_LIST)

    # 3. Configure a sessão de operação
    # Irá rodar por 5 minutos para o teste
    ops = se.operations.set(
        assets=ASSET_LIST,
        capital=se.account_info().equity,
        endTime=se.now(minOffset=5),
        mem=10, # 'mem' deve ser igual ou maior que o período do RSI
        timeframe=se.INTRADAY, # Timeframe de 1 minuto
        verbose=False,
        delay=60, # Checa a cada 60 segundos
        waitForOpen=True
    )

    # 4. Execute o trader
    print(f"Agente '{trader.name}' iniciado. Operando por 5 minutos... Pressione Ctrl+C para parar.")
    se.operations.run(trader, ops)
    print("\nTeste ao vivo com mt5se direto concluído.")

if __name__ == "__main__":
    run_direct_test()