# test_live_rebalance.py - VERSÃO CORRIGIDA COM WEIGHTS
"""
TESTE DETERMINÍSTICO DE REBALANCEAMENTO - NOVA ARQUITETURA

Este teste valida o novo sistema onde traders retornam PESOS ao invés de ordens.

NOVA ARQUITETURA:
1. Traders retornam dict de pesos: {'NVDA': 0.8, 'cash': 0.2}
2. Agent calcula targets em $ baseado no capital alocado
3. Agent agrega targets de todos os traders
4. Agent ajusta posições do portfolio para match targets

EXPECTATIVA DE EXECUÇÃO:
1. Cleanup inicial: Fecha todas as posições (começa com 100% cash)
2. Execução inicial: Portfolio aloca 70% Portfolio_A, 30% Portfolio_B (initial_weights)
3. A cada 10 segundos: Traders retornam nova alocação
   - Trade #1: Ambos traders querem 85% em seus ativos (15% buffer)
   - Trade #2: Ambos traders querem 50% ativo, 50% cash
   - Trade #3: Ambos traders querem 80% ativo, 20% cash
   - Trade #4: Ambos traders querem 30% ativo, 70% cash
4. A cada 5 minutos: Rebalanceamento ajusta capital entre traders

EXEMPLO DE EXECUÇÃO (Trade #1 - Initial):
- Total equity: $96,777
- Portfolio_A recebe: $67,744 (70% - initial_weights)
- Portfolio_B recebe: $29,033 (30% - initial_weights)
- Trader A retorna: {'NVDA': 0.85} → Target: $57,582 em NVDA
- Trader B retorna: {'MSFT': 0.85} → Target: $24,678 em MSFT
- Agent compra: ~317 NVDA + ~48 MSFT
- Cash buffer: ~$14,517 (15%)

EXEMPLO DE EXECUÇÃO (Trade #2):
- Trader A retorna: {'NVDA': 0.5, 'cash': 0.5} → Target: $25,000 em NVDA
- Trader B retorna: {'MSFT': 0.5, 'cash': 0.5} → Target: $25,000 em MSFT
- Agent ajusta: Vende metade das posições
"""
import mt5se as se
from datetime import datetime
import pandas as pd

# Importe sua biblioteca
from portfoliolib import PortfolioManager, PortfolioAgent, EqualWeightOptimizer

# Trader simples para teste (sem lógica complexa)
class VolatileTestTrader(se.Trader):
    def __init__(self, name, assets):
        super().__init__()
        self.name = name
        self.assets_universe = assets
        self.frequency = se.DAILY

    def trade(self, dbars):
        """
        Retorna alocação desejada como dicionário de pesos.
        Formato: {'ASSET': weight, 'cash': weight}
        Pesos devem somar 1.0
        """
        # TESTE DETERMINÍSTICO - Sequência previsível de alocações
        if not hasattr(self, 'trade_count'):
            self.trade_count = 0
        
        self.trade_count += 1
        print(f"[{self.name}] Trade #{self.trade_count}")
        
        # Define alocações para cada step
        if "NVDA" in self.assets_universe:
            asset = "NVDA"
        elif "MSFT" in self.assets_universe:
            asset = "MSFT"
        else:
            return {'cash': 1.0}
        
        # STEP 1: 85% no ativo (buffer para slippage e margem)
        if self.trade_count == 1:
            print(f"  -> Alocação: 85% {asset}, 15% cash")
            return {asset: 0.85, 'cash': 0.15}
        
        # STEP 2: 50% ativo, 50% cash
        elif self.trade_count == 2:
            print(f"  -> Alocação: 50% {asset}, 50% cash")
            return {asset: 0.5, 'cash': 0.5}
        
        # STEP 3: 80% ativo, 20% cash
        elif self.trade_count == 3:
            print(f"  -> Alocação: 80% {asset}, 20% cash")
            return {asset: 0.8, 'cash': 0.2}
        
        # STEP 4: 30% ativo, 70% cash  
        elif self.trade_count == 4:
            print(f"  -> Alocação: 30% {asset}, 70% cash")
            return {asset: 0.3, 'cash': 0.7}
        
        # STEP 5+: Mantém 30/70
        else:
            print(f"  -> Mantendo: 30% {asset}, 70% cash")
            return {asset: 0.3, 'cash': 0.7}

def main():
    print("=== Teste de Rebalanceamento ao Vivo (VERSÃO CORRIGIDA) ===")
    
    # Conecta ao MT5
    if not se.connect():
        print("[ERRO] Falha ao conectar ao MetaTrader 5")
        return

    # Cria dois traders com ativos diferentes (evita conflito de ordens)
    trader_a = VolatileTestTrader(name="Portfolio_A", assets=["NVDA"])
    trader_b = VolatileTestTrader(name="Portfolio_B", assets=["MSFT"])

    # Pesos iniciais DESBALANCEADOS (0.7 / 0.3)
    initial_weights = {
        "Portfolio_A": 0.7,
        "Portfolio_B": 0.3
    }

    # Cria o PortfolioManager com EqualWeightOptimizer (alvo = 50%/50%)
    manager = PortfolioManager(
        traders=[trader_a, trader_b],
        optimizer=EqualWeightOptimizer(),
        initial_equity=10000.0,  # Valor simbólico — será substituído pelo saldo real
        initial_weights=initial_weights,  # Usa 70/30 inicialmente, depois rebalanceia para 50/50
        max_leverage=1.0,
        target_volatility=None  # Desativa target volatility para simplificar teste
    )

    # Configura o agente
    agent = PortfolioAgent(
        manager=manager,
        prestart_dt=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(months=12),
        rebalance_frequency='5T',  # Rebalanceia a cada 5 minutos para teste rápido
        trade_interval_seconds=10,  # Verifica a cada 10 segundos para teste rápido
        state_file="test_rebalance_state_fixed.json"
    )

    # Habilita trading de estratégias para testar o cenário
    agent.enable_strategy_trading = True

    print("\n[OK] Configuração concluída - NOVA ARQUITETURA COM WEIGHTS.")
    print(f"   - Pesos iniciais do portfolio: {initial_weights}")
    print(f"   - Objetivo do otimizador: pesos iguais (50%/50%)")
    print(f"   - Rebalanceamento a cada 5 minutos")
    print(f"   - Trading de estratégias: HABILITADO")
    print(f"   - Sequência de alocações:")
    print(f"     1. Traders alocam 85% em ativos, 15% buffer")
    print(f"     2. Traders alocam 50% ativos, 50% cash")
    print(f"     3. Traders alocam 80% ativos, 20% cash")
    print(f"     4. Traders alocam 30% ativos, 70% cash")
    print(f"     5+. Traders mantêm 30% ativos, 70% cash")
    print(f"   - Cada trader decide sua alocação independentemente\n")

    # Executa o agente
    agent.run()

if __name__ == "__main__":
    main()