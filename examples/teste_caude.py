# test_portfolio.py - Script de teste para o portfoliolib (Versão Corrigida)

import mt5se as se
import pandas as pd
from datetime import datetime
from portfoliolib import PortfolioManager, PortfolioBacktester, PortfolioAgent
from portfoliolib import EqualWeightOptimizer, SharpeOptimizer

# --- Nenhuma alteração necessária nos Traders, exceto a adição de uma verificação de segurança ---

class SimpleRSITrader(se.Trader):
    """
    Trader simples baseado em RSI para teste.
    """
    def __init__(self, assets_universe, name="RSITrader"):
        super().__init__()
        self.assets_universe = assets_universe
        self.name = name
        self.capital = 0

    def setup(self, dbars):
        print(f"   {self.name} configurado com {len(self.assets_universe)} ativos.")

    def trade(self, dbars):
        orders = []
        
        ### ALTERAÇÃO 1: Adicionada verificação para evitar divisão por zero ###
        if not hasattr(self, 'capital') or self.capital <= 0 or not self.assets_universe:
            return orders

        capital_per_asset = self.capital / len(self.assets_universe)
        
        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty or len(dbars[asset]) < 14:
                continue
                
            bars = dbars[asset]
            rsi = se.tech.rsi(bars)
            current_shares = se.get_shares(asset)
            price = se.get_last(bars)
            
            if price <= 0: continue
                
            if rsi < 30:
                affordable_shares = se.get_affor_shares(asset, price, capital_per_asset)
                if affordable_shares > 0:
                    orders.append(se.buyOrder(asset, affordable_shares))
            elif rsi > 70 and current_shares > 0:
                orders.append(se.sellOrder(asset, current_shares))
                
        return orders

    def orders_result(self, exec_orders):
        if exec_orders:
            print(f"   {self.name}: {len(exec_orders)} ordens executadas.")

    def ending(self, dbars):
        print(f"   {self.name} finalizado.")

class SimpleTrendTrader(se.Trader):
    """
    Trader simples baseado em tendência para teste.
    """
    def __init__(self, assets_universe, name="TrendTrader"):
        super().__init__()
        self.assets_universe = assets_universe
        self.name = name
        self.capital = 0

    def setup(self, dbars):
        print(f"   {self.name} configurado com {len(self.assets_universe)} ativos.")

    def trade(self, dbars):
        orders = []

        ### ALTERAÇÃO 1 (Repetida): Adicionada verificação para evitar divisão por zero ###
        if not hasattr(self, 'capital') or self.capital <= 0 or not self.assets_universe:
            return orders

        capital_per_asset = self.capital / len(self.assets_universe)
        
        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty or len(dbars[asset]) < 20:
                continue

            bars = dbars[asset]
            trend = se.tech.trend(bars['close'])
            current_shares = se.get_shares(asset)
            price = se.get_last(bars)

            if price <= 0: continue

            if trend > 0:
                affordable_shares = se.get_affor_shares(asset, price, capital_per_asset)
                if affordable_shares > 0:
                    orders.append(se.buyOrder(asset, affordable_shares))
            elif trend < 0 and current_shares > 0:
                orders.append(se.sellOrder(asset, current_shares))
                
        return orders

    def orders_result(self, exec_orders):
        if exec_orders:
            print(f"   {self.name}: {len(exec_orders)} ordens executadas.")

    def ending(self, dbars):
        print(f"   {self.name} finalizado.")

def test_backtest():
    """
    Função para testar o backtest do portfólio.
    """
    print("\n" + "="*80 + "\nTESTE DE BACKTEST DO PORTFOLIOLIB\n" + "="*80)
    
    if not se.connect():
        print("Erro ao conectar ao MetaTrader 5")
        return
    
    assets_group1 = ['GOOG', 'NVDA', 'GS']
    assets_group2 = ['COST', 'JPM', 'WMT']
    
    trader1 = SimpleRSITrader(assets_group1, "RSI_Trader")
    trader2 = SimpleTrendTrader(assets_group2, "Trend_Trader")
    
    optimizer = SharpeOptimizer(risk_free_rate=0.02)
    
    manager = PortfolioManager(
        traders=[trader1, trader2],
        optimizer=optimizer,
        initial_equity=100000.0,
        prestart_offset=pd.DateOffset(days=10),
        target_volatility=0.15
    )
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    ### ALTERAÇÃO 2: Simplificada a criação do Backtester, removendo o prestart_offset ###
    backtester = PortfolioBacktester(
        manager=manager,
        start_date=start_date,
        end_date=end_date,
        lookback_period=pd.DateOffset(months=6),
        rebalance_frequency='MS'
    )
    
    ### ALTERAÇÃO 3: A chamada a run() agora desempacota a curva de equity e as métricas ###
    equity_curve, metrics = backtester.run()
    
    if not equity_curve.empty:
        results_df = pd.DataFrame({'date': equity_curve.index, 'equity': equity_curve.values})
        results_df.to_csv('portfolio_backtest_results.csv', index=False)
        print("\nResultados do backtest salvos em 'portfolio_backtest_results.csv'")
        
        # As métricas agora são impressas diretamente pela função run()
    else:
        print("\nERRO: Backtest não retornou resultados.")

# --- Nenhuma alteração necessária na função test_live_agent ou main ---
# ... (O resto do seu código de teste_caude.py pode permanecer o mesmo) ...

def test_live_agent():
    """
    Função para testar o agente de operação ao vivo.
    """
    print("\n" + "="*80)
    print("TESTE DO AGENTE AO VIVO DO PORTFOLIOLIB")
    print("="*80)
    
    # Conecta ao MT5
    if not se.connect():
        print("Erro ao conectar ao MetaTrader 5")
        return
    
    # Define universo de ativos
    assets_group1 = ['PETR4', 'VALE3', 'ITUB4']
    assets_group2 = ['BBDC4', 'ABEV3', 'WEGE3']
    
    # Cria traders
    trader1 = SimpleRSITrader(assets_group1, "RSI_Trader")
    trader2 = SimpleTrendTrader(assets_group2, "Trend_Trader")
    
    # Define otimizador
    optimizer = EqualWeightOptimizer()  # Usa pesos iguais para simplicidade
    
    # Obtém capital da conta
    acc_info = se.account_info()
    if acc_info:
        if hasattr(acc_info, 'equity'):
            initial_equity = acc_info.equity
        else:
            initial_equity = 100000.0
    else:
        initial_equity = 100000.0
    
    # Cria o manager do portfólio
    manager = PortfolioManager(
        traders=[trader1, trader2],
        optimizer=optimizer,
        initial_equity=initial_equity,
        prestart_offset=pd.DateOffset(days=365),
        initial_weights=None,
        target_volatility=0.15
    )
    
    # Cria o agente
    agent = PortfolioAgent(
        manager=manager,
        rebalance_interval_minutes=60,  # Rebalanceia a cada hora
        trade_interval_seconds=60,  # Executa trades a cada minuto
        state_file="portfolio_state.json"
    )
    
    # Executa o agente
    print("\nIniciando agente ao vivo...")
    print("Pressione Ctrl+C para parar\n")
    agent.run()

def main():
    """
    Função principal para escolher qual teste executar.
    """
    print("\n" + "="*80)
    print("TESTE DO PORTFOLIOLIB")
    print("="*80)
    print("\nEscolha uma opção:")
    print("1. Testar Backtest")
    print("2. Testar Agente Ao Vivo")
    print("3. Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == "1":
        test_backtest()
    elif choice == "2":
        confirm = input("\nAVISO: Isso executará ordens reais! Continuar? (s/n): ").strip().lower()
        if confirm == 's':
            test_live_agent()
        else:
            print("Operação cancelada")
    elif choice == "3":
        print("Saindo...")
    else:
        print("Opção inválida")

if __name__ == "__main__":
    main()