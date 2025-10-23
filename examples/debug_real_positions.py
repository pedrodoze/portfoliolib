"""
Debug script to understand what's happening with positions
"""
import mt5se as se

def main():
    print("=" * 70)
    print("DEBUG: Verificando posições reais do MT5")
    print("=" * 70)
    
    if not se.connect():
        print("Erro ao conectar")
        return
    
    # Check account info
    acc_info = se.account_info()
    print(f"\n📊 Informações da Conta:")
    if acc_info:
        if hasattr(acc_info, '_asdict'):
            for key, value in acc_info._asdict().items():
                print(f"   {key}: {value}")
        else:
            print(f"   {acc_info}")
    
    # Check positions via MT5 directly
    print(f"\n📊 Posições via se.get_shares():")
    nvda = se.get_shares("NVDA")
    msft = se.get_shares("MSFT")
    print(f"   NVDA: {nvda}")
    print(f"   MSFT: {msft}")
    
    # Check balance
    balance = se.get_balance()
    print(f"\n💰 Balance: ${balance:,.2f}")
    
    # Try to get positions another way
    print(f"\n🔍 Tentando obter posições de outra forma...")
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            positions = mt5.positions_get()
            if positions:
                print(f"   Total de posições abertas: {len(positions)}")
                for pos in positions:
                    print(f"   - {pos.symbol}: {pos.volume} @ {pos.price_open}")
            else:
                print(f"   Nenhuma posição encontrada via MT5 direto")
            mt5.shutdown()
    except Exception as e:
        print(f"   Erro ao acessar MT5 direto: {e}")
    
    # Test selling
    print(f"\n🧪 TESTE: Tentando vender 1 share de NVDA...")
    if nvda > 0:
        order = se.sellOrder("NVDA", 1.0)
        print(f"   Ordem criada: {order}")
        
        check = se.checkOrder(order)
        print(f"   Ordem válida? {check}")
        
        if check:
            result = se.sendOrder(order)
            print(f"   Ordem enviada? {result}")
            
            # Check position after
            nvda_after = se.get_shares("NVDA")
            print(f"   NVDA após venda: {nvda_after}")
            
            if nvda_after == nvda - 1:
                print(f"   ✅ Venda funcionou!")
            else:
                print(f"   ❌ Venda não mudou a posição!")
    else:
        print(f"   Sem posição NVDA para testar")

if __name__ == "__main__":
    main()


