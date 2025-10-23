# Exemplo simplificado de trading ao vivo sem rebalancing complexo

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mt5se as se
import pandas as pd
from datetime import datetime, timedelta
import time

# Importa componentes do portfoliolib
from portfoliolib import PortfolioManager, EqualWeightOptimizer
from portfoliolib.agent import PortfolioAgent

# Importa o trader customizado
from live_trader.equal_weight_volatility_trader import EqualWeightVolatilityTrader

def create_simple_trader():
    """
    Cria um trader simples para teste.
    """
    trader = EqualWeightVolatilityTrader(
        name="Simple_RSI",
        assets_universe=["AAPL", "MSFT", "GOOGL"],  # Stocks simples
        rsi_buy_threshold=60,  # Padrão
        rsi_sell_threshold=40,
        risk_per_trade=0.05,   # 5% por trade
        timeframe=se.DAILY
    )
    return trader

def simple_live_trading():
    """
    Trading ao vivo simplificado sem rebalancing complexo.
    """
    print("=" * 80)
    print("TRADING AO VIVO SIMPLIFICADO")
    print("=" * 80)
    
    # Conecta ao MetaTrader 5
    if not se.connect():
        print("ERRO: Nao foi possivel conectar ao MetaTrader 5")
        return
    
    print("Conectado ao MetaTrader 5")
    
    # Obtem informacoes da conta
    account_info = se.account_info()
    if account_info:
        print(f"   - Conta: {account_info.login}")
        print(f"   - Servidor: {account_info.server}")
        print(f"   - Saldo: ${account_info.balance:.2f}")
        print(f"   - Equity: ${account_info.equity:.2f}")
    
    # Cria trader simples
    print("\nCriando trader simples...")
    trader = create_simple_trader()
    print(f"   - {trader.name}: {len(trader.assets_universe)} ativos")
    
    # Loop de trading simples
    print("\nINICIANDO TRADING SIMPLES...")
    print("Pressione Ctrl+C para parar")
    print("=" * 80)
    
    trade_count = 0
    
    try:
        while True:
            try:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === CICLO DE TRADING #{trade_count + 1} ===")
                
                # Obtem dados para todos os ativos
                trader_dbars = {}
                for asset in trader.assets_universe:
                    bars = se.get_bars(asset, 100)
                    if bars is not None and not bars.empty:
                        trader_dbars[asset] = bars
                        print(f"   - {asset}: {len(bars)} barras obtidas")
                
                if trader_dbars:
                    # Executa estrategia do trader
                    print(f"   Executando estrategia {trader.name}...")
                    orders = trader.trade(trader_dbars)
                    
                    if orders:
                        print(f"   {len(orders)} ordens geradas:")
                        for i, order in enumerate(orders):
                            print(f"     {i+1}. {order['symbol']} - {order['volume']} shares")
                            
                            # Tenta enviar ordem
                            if se.checkOrder(order):
                                if se.sendOrder(order):
                                    print(f"       ORDEM ENVIADA COM SUCESSO!")
                                    trade_count += 1
                                else:
                                    print(f"       FALHA ao enviar ordem")
                            else:
                                print(f"       Ordem nao passou na validacao")
                    else:
                        print("   Nenhuma ordem gerada")
                else:
                    print("   Nenhum dado de mercado disponivel")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] === CICLO CONCLUIDO ===")
                
                # Aguarda 60 segundos antes do proximo ciclo
                print("Aguardando 60 segundos...")
                time.sleep(60)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erro no ciclo de trading: {e}")
                time.sleep(10)  # Aguarda 10 segundos em caso de erro
                
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Trading interrompido pelo usuario")
        print(f"Total de trades executados: {trade_count}")
        print("=" * 80)
    finally:
        # Desconecta do MetaTrader
        try:
            se.disconnect()
            print("Desconectado do MetaTrader 5")
        except:
            pass

if __name__ == "__main__":
    simple_live_trading()

