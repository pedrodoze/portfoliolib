# Teste minimal do script original
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mt5se as se
import pandas as pd
from datetime import datetime, timedelta

# Importa componentes do portfoliolib
from portfoliolib import PortfolioManager, EqualWeightOptimizer
from portfoliolib.agent import PortfolioAgent

# Importa o trader customizado
from live_trader.equal_weight_volatility_trader import EqualWeightVolatilityTrader

def test_minimal():
    """Teste minimal para verificar se tudo funciona."""
    print("=" * 60)
    print("TESTE MINIMAL DO SCRIPT ORIGINAL")
    print("=" * 60)
    
    # Teste 1: Conexão
    print("1. Testando conexão com MetaTrader 5...")
    if not se.connect():
        print("   ERRO: Falha na conexão")
        return False
    print("   OK: Conectado ao MetaTrader 5")
    
    # Teste 2: Informações da conta
    print("2. Testando informações da conta...")
    account_info = se.account_info()
    if account_info:
        print(f"   OK: Conta {account_info.login}, Equity: ${account_info.equity:.2f}")
    else:
        print("   ERRO: Não conseguiu obter informações da conta")
        return False
    
    # Teste 3: Criação de traders
    print("3. Testando criação de traders...")
    try:
        trader = EqualWeightVolatilityTrader(
            name="Test_Trader",
            assets_universe=["AAPL", "MSFT"],
            rsi_buy_threshold=60,
            rsi_sell_threshold=40,
            risk_per_trade=0.05,
            timeframe=se.DAILY
        )
        print("   OK: Trader criado com sucesso")
    except Exception as e:
        print(f"   ERRO: Falha ao criar trader: {e}")
        return False
    
    # Teste 4: PortfolioManager
    print("4. Testando PortfolioManager...")
    try:
        traders = [trader]
        optimizer = EqualWeightOptimizer()
        manager = PortfolioManager(
            traders=traders,
            optimizer=optimizer,
            initial_equity=10000.0,
            target_volatility=0.10,
            max_leverage=3.0
        )
        print("   OK: PortfolioManager criado com sucesso")
    except Exception as e:
        print(f"   ERRO: Falha ao criar PortfolioManager: {e}")
        return False
    
    # Teste 5: PortfolioAgent
    print("5. Testando PortfolioAgent...")
    try:
        current_date = datetime.now()
        prestart_date = current_date - timedelta(days=30)
        lookback_period = pd.DateOffset(days=7)  # Período menor para teste
        
        agent = PortfolioAgent(
            manager=manager,
            prestart_dt=prestart_date,
            lookback_period=lookback_period,
            rebalance_frequency='D',
            trade_interval_seconds=60,
            state_file="test_state.json"
        )
        print("   OK: PortfolioAgent criado com sucesso")
    except Exception as e:
        print(f"   ERRO: Falha ao criar PortfolioAgent: {e}")
        return False
    
    # Teste 6: Dados de mercado
    print("6. Testando obtenção de dados de mercado...")
    try:
        bars = se.get_bars("AAPL", 10)
        if bars is not None and not bars.empty:
            print(f"   OK: Obtidos {len(bars)} barras para AAPL")
        else:
            print("   ERRO: Não conseguiu obter dados de mercado")
            return False
    except Exception as e:
        print(f"   ERRO: Falha ao obter dados: {e}")
        return False
    
    # Teste 7: Estratégia do trader
    print("7. Testando estratégia do trader...")
    try:
        trader_dbars = {"AAPL": bars}
        orders = trader.trade(trader_dbars)
        print(f"   OK: Estratégia executada, {len(orders)} ordens geradas")
    except Exception as e:
        print(f"   ERRO: Falha na estratégia: {e}")
        return False
    
    print("=" * 60)
    print("TODOS OS TESTES PASSARAM!")
    print("O script original deve funcionar corretamente.")
    print("=" * 60)
    
    try:
        se.disconnect()
        print("Desconectado do MetaTrader 5")
    except:
        pass
    
    return True

if __name__ == "__main__":
    success = test_minimal()
    if success:
        print("\nRESULTADO: SCRIPT ORIGINAL DEVE FUNCIONAR")
    else:
        print("\nRESULTADO: SCRIPT ORIGINAL TEM PROBLEMAS")

