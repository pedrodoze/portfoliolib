# examples/run_live_equal_weight_volatility.py
"""
Exemplo de portfólio com 3 traders igualmente ponderados,
target volatility de 10% e lookback de 6 meses para trading ao vivo.

Características:
- 3 traders com estratégias RSI diferentes
- Pesos iguais (33.33% cada)
- Target volatility: 10% anual
- Lookback window: 6 meses
- Rebalanceamento diário
- Trading ao vivo via MetaTrader 5
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mt5se as se
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Importa componentes do portfoliolib
from portfoliolib import PortfolioManager, EqualWeightOptimizer
from portfoliolib.agent import PortfolioAgent

# Importa o trader customizado
from live_trader.equal_weight_volatility_trader import EqualWeightVolatilityTrader



def create_traders():
    """
    Cria 3 traders com estratégias RSI diferentes para diversificação.
    """
    traders = []
    
    # Trader 1: RSI Conservador (entrada mais restritiva) - Forex
    trader_conservative = EqualWeightVolatilityTrader(
        name="RSI_Conservative",
        assets_universe=["EURUSD"],  # Apenas 1 ativo para evitar conflitos
        rsi_buy_threshold=65,  # Mais conservador
        rsi_sell_threshold=35,
        risk_per_trade=0.03,   # 3% por trade
        timeframe=se.DAILY
    )
    traders.append(trader_conservative)
    
    # Trader 2: RSI Padrão (balanceado) - Tech stocks
    trader_balanced = EqualWeightVolatilityTrader(
        name="RSI_Balanced", 
        assets_universe=["AAPL"],  # Apenas 1 ativo para evitar conflitos
        rsi_buy_threshold=60,  # Padrão
        rsi_sell_threshold=40,
        risk_per_trade=0.05,   # 5% por trade
        timeframe=se.DAILY
    )
    traders.append(trader_balanced)
    
    # Trader 3: RSI Agressivo (entrada mais rápida) - Diferente ativo
    trader_aggressive = EqualWeightVolatilityTrader(
        name="RSI_Aggressive",
        assets_universe=["MSFT"],  # Apenas 1 ativo diferente para evitar conflitos
        rsi_buy_threshold=55,  # Mais agressivo
        rsi_sell_threshold=45,
        risk_per_trade=0.07,   # 7% por trade
        timeframe=se.DAILY
    )
    traders.append(trader_aggressive)
    
    return traders

def run_live_portfolio():
    """
    Executa o portfólio ao vivo com as configurações especificadas.
    Baseado no test_live_rebalance.py que estava funcionando.
    """
    print("=" * 80)
    print("PORTFOLIO AO VIVO - EQUAL WEIGHT + TARGET VOLATILITY")
    print("=" * 80)
    print("Configuracoes:")
    print("- 3 traders igualmente ponderados (33.33% cada)")
    print("- Target volatility: 10% anual")
    print("- Lookback window: 1 mes")
    print("- Rebalanceamento: A cada 1 minuto")
    print("- Trading: Ao vivo via MetaTrader 5")
    print("- Agent: PortfolioAgent (baseado no test_live_rebalance)")
    print("=" * 80)
    
    # Conecta ao MetaTrader 5
    if not se.connect():
        print("ERRO: Nao foi possivel conectar ao MetaTrader 5")
        print("   - Verifique se o MT5 esta aberto")
        print("   - Verifique se a conta demo esta ativa")
        print("   - Verifique se o algoritmo trading esta habilitado")
        return
    
    print("Conectado ao MetaTrader 5")
    
    # Obtem informacoes da conta
    account_info = se.account_info()
    if account_info:
        print(f"   - Conta: {account_info.login}")
        print(f"   - Servidor: {account_info.server}")
        print(f"   - Saldo: ${account_info.balance:.2f}")
        print(f"   - Equity: ${account_info.equity:.2f}")
    
    # Cria os traders (usando ativos diferentes para evitar conflitos)
    print("\nCriando traders...")
    traders = create_traders()
    
    for trader in traders:
        print(f"   - {trader.name}: {len(trader.assets_universe)} ativos, "
              f"RSI {trader.rsi_buy_threshold}/{trader.rsi_sell_threshold}, "
              f"Risk {trader.risk_per_trade:.1%}")
    
    # Configura o otimizador (pesos iguais)
    optimizer = EqualWeightOptimizer()
    
    # Configura o manager do portfólio (seguindo o padrão do test_live_rebalance)
    print("\nConfigurando PortfolioManager...")
    manager = PortfolioManager(
        traders=traders,
        optimizer=optimizer,
        initial_equity=float(account_info.equity) if account_info else 10000.0,
        initial_weights=None,  # Usa pesos iguais automaticamente
        target_volatility=0.10,  # 10% target volatility
        max_leverage=1.0,        # Reduzido para 1.0 (como no test_live_rebalance)
        volatility_floor=0.001   # 0.1% volatilidade mínima
    )
    
    # Define datas (período menor como no test_live_rebalance)
    current_date = datetime.now()
    prestart_date = current_date - timedelta(days=90)  # 3 meses para prestart
    lookback_period = pd.DateOffset(months=1)  # 1 mês de lookback
    
    print(f"   - Data atual: {current_date.strftime('%Y-%m-%d')}")
    print(f"   - Prestart: {prestart_date.strftime('%Y-%m-%d')}")
    print(f"   - Lookback: 1 mes")
    print(f"   - Target volatility: 10%")
    
    # Configura o agente para trading ao vivo (seguindo o padrão do test_live_rebalance)
    print("\nConfigurando PortfolioAgent...")
    agent = PortfolioAgent(
        manager=manager,
        prestart_dt=prestart_date,
        lookback_period=lookback_period,
        rebalance_frequency='1T',  # Rebalanceamento a cada 1 minuto (como no test_live_rebalance)
        trade_interval_seconds=30,  # Verifica trades a cada 30 segundos
        state_file="live_equal_weight_state.json"
    )
    
    print("   - Rebalanceamento: A cada 1 minuto")
    print("   - Intervalo de trading: 30 segundos")
    print("   - Arquivo de estado: live_equal_weight_state.json")
    
    # Mostra status inicial
    print("\nStatus inicial do portfolio:")
    status = manager.get_portfolio_status()
    print(f"   - Total equity: ${status['total_equity']:,.2f}")
    print(f"   - Numero de traders: {status['num_traders']}")
    print(f"   - Target volatility: {status['risk_management']['target_volatility']:.1%}")
    print(f"   - Max leverage: {status['risk_management']['max_leverage']:.1f}x")
    
    print("\nPesos iniciais:")
    for trader_name, weight in status['current_weights'].items():
        print(f"   - {trader_name}: {weight:.4f} ({weight*100:.2f}%)")
    
    # Inicia o trading ao vivo
    print("\nINICIANDO TRADING AO VIVO...")
    print("   Pressione Ctrl+C para parar")
    print("=" * 80)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("Trading interrompido pelo usuario")
        print("=" * 80)
    except Exception as e:
        print(f"\nERRO durante o trading: {e}")
        print("=" * 80)
    finally:
        # Desconecta do MetaTrader
        try:
            se.disconnect()
            print("Desconectado do MetaTrader 5")
        except AttributeError:
            # mt5se pode não ter função disconnect
            print("MetaTrader 5 desconectado")

def test_backtest_first():
    """
    Executa um backtest rápido antes do trading ao vivo para validar a estratégia.
    """
    print("Executando backtest de validacao...")
    
    # Conecta ao MetaTrader 5 para backtest
    if not se.connect():
        print("ERRO: Nao foi possivel conectar ao MetaTrader 5 para backtest")
        print("   - Verifique se o MT5 esta aberto")
        print("   - Verifique se a conta demo esta ativa")
        return False
    
    print("Conectado ao MetaTrader 5 para backtest")
    
    # Cria traders para teste
    traders = create_traders()
    
    # Configura datas de teste (últimos 3 meses)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    prestart_date = start_date - timedelta(days=30)
    
    print(f"   - Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Configura manager
    optimizer = EqualWeightOptimizer()
    manager = PortfolioManager(
        traders=traders,
        optimizer=optimizer,
        initial_equity=100000.0,
        target_volatility=0.10,
        max_leverage=3.0
    )
    
    # Executa backtest rápido
    from portfoliolib import PortfolioBacktester
    
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=start_date,
        end_date=end_date,
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency='W',  # Semanal para teste mais rápido
        prestart_dt=prestart_date
    )
    
    try:
        equity_curve = backtester.run()
        
        if equity_curve is not None and not equity_curve.empty:
            final_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            volatility = equity_curve.pct_change().std() * (252 ** 0.5)
            sharpe = (equity_curve.pct_change().mean() * 252) / (equity_curve.pct_change().std() * (252 ** 0.5))
            
            print(f"   Backtest concluido:")
            print(f"   - Retorno total: {final_return:.2%}")
            print(f"   - Volatilidade: {volatility:.2%}")
            print(f"   - Sharpe ratio: {sharpe:.2f}")
            print(f"   - Valor final: ${equity_curve.iloc[-1]:,.2f}")
            
            return True
        else:
            print("   Backtest falhou - sem dados")
            return False
            
    except Exception as e:
        print(f"   Erro no backtest: {e}")
        return False
    finally:
        # Desconecta do MetaTrader após o backtest
        try:
            se.disconnect()
            print("Desconectado do MetaTrader 5 após backtest")
        except AttributeError:
            # mt5se pode não ter função disconnect
            print("MetaTrader 5 desconectado após backtest")

def main():
    """
    Função principal que executa o exemplo completo.
    """
    print("EXEMPLO: PORTFOLIO EQUAL WEIGHT + TARGET VOLATILITY")
    print("   - 3 traders igualmente ponderados")
    print("   - Target volatility: 10%")
    print("   - Lookback: 6 meses")
    print("   - Trading ao vivo via MetaTrader 5")
    print("   - PortfolioAgent com melhorias de rebalancing")
    print()
    
    # Para debug, pula o backtest e vai direto para trading ao vivo
    print("Pulando backtest - indo direto para trading ao vivo...")
    run_live_portfolio()

if __name__ == "__main__":
    main()
