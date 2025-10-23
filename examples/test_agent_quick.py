# Teste rápido do agente sem rebalancing inicial

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

class QuickPortfolioAgent(PortfolioAgent):
    """
    Versão do PortfolioAgent que pula o rebalancing inicial para teste rápido.
    """
    def run(self):
        """Loop principal de execução sem rebalancing inicial."""
        # Conecta ao MT5
        if not se.connect():
            print("Erro ao conectar ao MetaTrader 5")
            return
        
        print("=" * 60)
        print("QuickPortfolioAgent INICIADO")
        print(f"Rebalanceamento: frequência {self.rebalance_frequency}")
        print(f"Trading: a cada {self.trade_interval} segundos")
        print(f"Ativos: {len(self.all_assets)}")
        print("Pressione Ctrl+C para parar")
        print("=" * 60)
        
        # Carrega estado
        self._load_state()
        
        # PULA rebalanceamento inicial para teste rápido
        print("Pulando rebalanceamento inicial - indo direto para trading...")
        
        # Loop principal
        last_trade_time = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Executa ciclo de trading
                if current_time - last_trade_time >= self.trade_interval:
                    self._trade_cycle_quick()
                    last_trade_time = current_time
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n" + "=" * 60)
                print("Encerrando o agente...")
                print("=" * 60)
                break
            except Exception as e:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Erro: {e}")

    def _trade_cycle_quick(self):
        """Executa um ciclo de trading sem rebalancing."""
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === CICLO DE TRADING RAPIDO ===")
            
            for trader_name, trader in self.manager.trader_map.items():
                try:
                    print(f"   Executando {trader_name}...")
                    
                    # Filtra ativos do trader
                    trader_assets = []
                    if hasattr(trader, 'assets_universe'):
                        trader_assets = trader.assets_universe
                    elif hasattr(trader, 'assets'):
                        trader_assets = trader.assets
                    
                    if not trader_assets:
                        print(f"   - {trader_name}: Sem ativos definidos")
                        continue
                    
                    # Obtém dados com frequência específica do trader
                    frequency = self.trader_frequencies[trader_name]
                    bars_count = 100 if frequency == se.DAILY else 500
                    
                    trader_dbars = {}
                    for asset in trader_assets:
                        bars = se.get_bars(asset, bars_count, type=frequency)
                        if bars is not None and not bars.empty:
                            trader_dbars[asset] = bars
                            print(f"     - {asset}: {len(bars)} barras")
                    
                    if trader_dbars:
                        # Executa estratégia
                        orders = trader.trade(trader_dbars)
                        
                        if orders:
                            print(f"     {len(orders)} ordens geradas:")
                            for i, order in enumerate(orders):
                                print(f"       {i+1}. {order['symbol']} - {order['volume']} shares")
                                
                                # Tenta enviar ordem
                                if se.checkOrder(order):
                                    if se.sendOrder(order):
                                        print(f"         ORDEM ENVIADA COM SUCESSO!")
                                    else:
                                        print(f"         FALHA ao enviar ordem")
                                else:
                                    print(f"         Ordem nao passou na validacao")
                        else:
                            print(f"     Nenhuma ordem gerada")
                    else:
                        print(f"     Sem dados de mercado")
                                        
                except Exception as e:
                    print(f"   Erro no trader {trader_name}: {e}")
                    continue
                    
            print(f"[{datetime.now().strftime('%H:%M:%S')}] === CICLO CONCLUIDO ===")
                                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro no ciclo de trading: {e}")

def create_traders():
    """Cria traders para teste."""
    traders = []
    
    # Trader 1: RSI Conservador
    trader_conservative = EqualWeightVolatilityTrader(
        name="RSI_Conservative",
        assets_universe=["EURUSD", "GBPUSD", "USDJPY"],
        rsi_buy_threshold=65,
        rsi_sell_threshold=35,
        risk_per_trade=0.03,
        timeframe=se.DAILY
    )
    traders.append(trader_conservative)
    
    # Trader 2: RSI Balanceado
    trader_balanced = EqualWeightVolatilityTrader(
        name="RSI_Balanced", 
        assets_universe=["AAPL", "MSFT", "GOOGL"],
        rsi_buy_threshold=60,
        rsi_sell_threshold=40,
        risk_per_trade=0.05,
        timeframe=se.DAILY
    )
    traders.append(trader_balanced)
    
    # Trader 3: RSI Agressivo
    trader_aggressive = EqualWeightVolatilityTrader(
        name="RSI_Aggressive",
        assets_universe=["AAPL", "MSFT", "TSLA"],
        rsi_buy_threshold=55,
        rsi_sell_threshold=45,
        risk_per_trade=0.07,
        timeframe=se.DAILY
    )
    traders.append(trader_aggressive)
    
    return traders

def test_quick_agent():
    """Testa o agente rápido."""
    print("=" * 80)
    print("TESTE AGENTE RAPIDO - SEM REBALANCING INICIAL")
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
    
    # Cria traders
    print("\nCriando traders...")
    traders = create_traders()
    
    for trader in traders:
        print(f"   - {trader.name}: {len(trader.assets_universe)} ativos")
    
    # Configura o otimizador e manager
    optimizer = EqualWeightOptimizer()
    manager = PortfolioManager(
        traders=traders,
        optimizer=optimizer,
        initial_equity=float(account_info.equity) if account_info else 10000.0,
        target_volatility=0.10,
        max_leverage=3.0
    )
    
    # Define datas
    current_date = datetime.now()
    prestart_date = current_date - timedelta(days=210)
    lookback_period = pd.DateOffset(months=6)
    
    # Configura o agente rápido
    print("\nConfigurando QuickPortfolioAgent...")
    agent = QuickPortfolioAgent(
        manager=manager,
        prestart_dt=prestart_date,
        lookback_period=lookback_period,
        rebalance_frequency='W',
        trade_interval_seconds=30,  # 30 segundos para teste rápido
        state_file="quick_test_state.json"
    )
    
    print("   - Rebalanceamento: Semanal")
    print("   - Intervalo de trading: 30 segundos")
    print("   - SEM rebalancing inicial")
    
    # Inicia o trading
    print("\nINICIANDO TESTE RAPIDO...")
    print("   Pressione Ctrl+C para parar")
    print("=" * 80)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Teste interrompido pelo usuario")
        print("=" * 80)
    except Exception as e:
        print(f"\nERRO durante o teste: {e}")
        print("=" * 80)
    finally:
        try:
            se.disconnect()
            print("Desconectado do MetaTrader 5")
        except:
            pass

if __name__ == "__main__":
    test_quick_agent()

