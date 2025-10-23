# Teste simples para verificar se consegue enviar ordens ao MetaTrader 5

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import mt5se as se
from datetime import datetime

def test_simple_order():
    """
    Teste simples para verificar conexão e envio de ordens.
    """
    print("=" * 60)
    print("TESTE SIMPLES - ENVIO DE ORDEM")
    print("=" * 60)
    
    # Conecta ao MetaTrader 5
    print("Conectando ao MetaTrader 5...")
    if not se.connect():
        print("ERRO: Nao foi possivel conectar ao MetaTrader 5")
        print("   - Verifique se o MT5 esta aberto")
        print("   - Verifique se a conta demo esta ativa")
        print("   - Verifique se o algoritmo trading esta habilitado")
        return False
    
    print("Conectado ao MetaTrader 5")
    
    # Obtem informacoes da conta
    account_info = se.account_info()
    if account_info:
        print(f"   - Conta: {account_info.login}")
        print(f"   - Servidor: {account_info.server}")
        print(f"   - Saldo: ${account_info.balance:.2f}")
        print(f"   - Equity: ${account_info.equity:.2f}")
    
    # Testa com um ativo simples
    test_asset = "AAPL"
    print(f"\nTestando com ativo: {test_asset}")
    
    # Obtem dados do ativo
    bars = se.get_bars(test_asset, 10)
    if bars is None or bars.empty:
        print(f"ERRO: Nao foi possivel obter dados para {test_asset}")
        return False
    
    print(f"Dados obtidos: {len(bars)} barras")
    
    # Obtem preco atual
    price = se.get_last(bars)
    print(f"Preco atual: {price}")
    
    # Calcula quantidade pequena para teste
    test_capital = 1000.0  # $1000
    test_shares = se.get_affor_shares(test_asset, price, test_capital)
    print(f"Quantidade calculada para ${test_capital}: {test_shares}")
    
    # Verifica volume step
    volume_step = se.get_volume_step(test_asset)
    print(f"Volume step: {volume_step}")
    
    # Ajusta para o step se necessario
    if volume_step > 0:
        test_shares = round(test_shares / volume_step) * volume_step
        print(f"Quantidade ajustada para step: {test_shares}")
    
    # Cria ordem de teste
    print(f"\nCriando ordem de teste:")
    print(f"   - Ativo: {test_asset}")
    print(f"   - Quantidade: {test_shares}")
    print(f"   - Preco: {price}")
    
    try:
        # Tenta criar ordem simples primeiro
        order = se.buyOrder(test_asset, test_shares)
        print("Ordem criada com sucesso")
        
        # Verifica ordem
        if se.checkOrder(order):
            print("Ordem validada com sucesso")
            
            # Tenta enviar ordem
            print("Enviando ordem...")
            if se.sendOrder(order):
                print("ORDEM ENVIADA COM SUCESSO!")
                return True
            else:
                print("ERRO: Falha ao enviar ordem")
                return False
        else:
            print("ERRO: Ordem nao passou na validacao")
            return False
            
    except Exception as e:
        print(f"ERRO ao criar ordem: {e}")
        return False
    
    finally:
        # Desconecta
        try:
            se.disconnect()
            print("Desconectado do MetaTrader 5")
        except:
            pass

if __name__ == "__main__":
    success = test_simple_order()
    if success:
        print("\nTESTE CONCLUIDO COM SUCESSO!")
    else:
        print("\nTESTE FALHOU!")
