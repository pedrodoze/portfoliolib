# examples/test_live_setup.py
"""
Script de teste para validar a configuração antes de executar o trading ao vivo.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mt5se as se
import pandas as pd
from datetime import datetime, timedelta

def test_mt5_connection():
    """Testa a conexão com o MetaTrader 5."""
    print("🔌 Testando conexão com MetaTrader 5...")
    
    if not se.connect():
        print("❌ Falha ao conectar ao MT5")
        print("   - Verifique se o MT5 está aberto")
        print("   - Verifique se a conta demo está ativa")
        print("   - Verifique se o algoritmo trading está habilitado")
        return False
    
    print("✅ Conectado ao MetaTrader 5")
    
    # Obtém informações da conta
    account_info = se.account_info()
    if account_info:
        print(f"   - Conta: {account_info.login}")
        print(f"   - Servidor: {account_info.server}")
        print(f"   - Saldo: ${account_info.balance:.2f}")
        print(f"   - Equity: ${account_info.equity:.2f}")
        print(f"   - Leverage: 1:{account_info.leverage}")
    
    return True

def test_assets_availability():
    """Testa a disponibilidade dos ativos."""
    print("\n📊 Testando disponibilidade dos ativos...")
    
    # Lista de ativos que serão usados
    test_assets = {
        "Forex": ["EURUSD", "GBPUSD", "USDJPY"],
        "Stocks": ["AAPL", "MSFT", "GOOGL"],
        "Crypto": ["BTCUSD", "ETHUSD", "XRPUSD"]
    }
    
    available_assets = {}
    
    for category, assets in test_assets.items():
        print(f"   {category}:")
        available_assets[category] = []
        
        for asset in assets:
            try:
                # Testa se o ativo existe
                symbol_info = se.symbol_info(asset)
                if symbol_info is None:
                    print(f"     ❌ {asset}: Não disponível")
                    continue
                
                # Testa se consegue obter dados
                bars = se.get_bars(asset, 10)
                if bars is None or bars.empty:
                    print(f"     ❌ {asset}: Sem dados")
                    continue
                
                # Obtém preço atual
                price = se.get_last(bars)
                if price <= 0:
                    print(f"     ❌ {asset}: Preço inválido")
                    continue
                
                print(f"     ✅ {asset}: ${price:.5f}")
                available_assets[category].append(asset)
                
            except Exception as e:
                print(f"     ❌ {asset}: Erro - {e}")
    
    return available_assets

def test_market_hours():
    """Testa se o mercado está aberto."""
    print("\n🕐 Testando horários de mercado...")
    
    test_assets = ["EURUSD", "AAPL", "BTCUSD"]
    
    for asset in test_assets:
        try:
            is_open = se.is_market_open(asset)
            status = "🟢 ABERTO" if is_open else "🔴 FECHADO"
            print(f"   {asset}: {status}")
        except Exception as e:
            print(f"   {asset}: ❌ Erro - {e}")

def test_trading_functions():
    """Testa as funções de trading básicas."""
    print("\n💹 Testando funções de trading...")
    
    test_asset = "EURUSD"  # Usar forex que está sempre disponível
    
    try:
        # Testa obtenção de posição atual
        current_shares = se.get_shares(test_asset)
        print(f"   Posição atual em {test_asset}: {current_shares}")
        
        # Testa obtenção de saldo
        balance = se.get_balance()
        print(f"   Saldo disponível: ${balance:.2f}")
        
        # Testa cálculo de ações que pode comprar
        bars = se.get_bars(test_asset, 2)
        if bars is not None and not bars.empty:
            price = se.get_last(bars)
            test_capital = 1000.0  # $1000 para teste
            affordable_shares = se.get_affor_shares(test_asset, price, test_capital)
            print(f"   Com ${test_capital} pode comprar {affordable_shares} de {test_asset} @ ${price:.5f}")
        
        # Testa criação de ordem (sem enviar)
        if affordable_shares > 0:
            test_order = se.buyOrder(test_asset, 1)  # Apenas 1 unidade para teste
            if se.checkOrder(test_order):
                print(f"   ✅ Ordem de teste válida")
            else:
                print(f"   ❌ Ordem de teste inválida")
        
        print("   ✅ Funções de trading funcionando")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nas funções de trading: {e}")
        return False

def test_portfoliolib_imports():
    """Testa se consegue importar os componentes do portfoliolib."""
    print("\n📦 Testando imports do portfoliolib...")
    
    try:
        from portfoliolib import PortfolioManager, EqualWeightOptimizer
        print("   ✅ PortfolioManager importado")
        print("   ✅ EqualWeightOptimizer importado")
        
        from portfoliolib.agent_improved import ImprovedPortfolioAgent
        print("   ✅ ImprovedPortfolioAgent importado")
        
        from live_trader.equal_weight_volatility_trader import EqualWeightVolatilityTrader
        print("   ✅ EqualWeightVolatilityTrader importado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao importar: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("🧪 EXECUTANDO TESTES DE CONFIGURAÇÃO")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 5
    
    # Teste 1: Conexão MT5
    if test_mt5_connection():
        tests_passed += 1
    
    # Teste 2: Ativos disponíveis
    available_assets = test_assets_availability()
    if any(assets for assets in available_assets.values()):
        tests_passed += 1
        print(f"\n   📋 Ativos disponíveis por categoria:")
        for category, assets in available_assets.items():
            if assets:
                print(f"     {category}: {', '.join(assets)}")
    
    # Teste 3: Horários de mercado
    test_market_hours()
    tests_passed += 1  # Sempre passa, apenas informativo
    
    # Teste 4: Funções de trading
    if test_trading_functions():
        tests_passed += 1
    
    # Teste 5: Imports
    if test_portfoliolib_imports():
        tests_passed += 1
    
    # Resultado final
    print("\n" + "=" * 50)
    print(f"🎯 RESULTADO DOS TESTES: {tests_passed}/{total_tests} passaram")
    
    if tests_passed == total_tests:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("   O sistema está pronto para trading ao vivo.")
    elif tests_passed >= 3:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("   O sistema pode funcionar, mas verifique os problemas.")
    else:
        print("❌ MUITOS TESTES FALHARAM")
        print("   Corrija os problemas antes de executar o trading ao vivo.")
    
    print("=" * 50)
    
    return tests_passed >= 3

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🚀 Para executar o trading ao vivo, rode:")
        print("   python run_live_equal_weight_volatility.py")
    else:
        print("\n🛠️ Corrija os problemas antes de continuar.")

