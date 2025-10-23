"""
Test that setting se.inbacktest = False actually enables live trading
"""
import mt5se as se

def main():
    print("=" * 70)
    print("TEST: Verificando fix do modo LIVE")
    print("=" * 70)
    
    if not se.connect():
        print("❌ Falha ao conectar")
        return
    
    print(f"\n📊 Estado INICIAL:")
    print(f"   se.inbacktest: {se.inbacktest}")
    
    # Simulate what happens after backtest
    print(f"\n🔄 Simulando backtest (seta inbacktest=True)...")
    se.inbacktest = True
    print(f"   se.inbacktest: {se.inbacktest}")
    
    # Now apply our fix
    print(f"\n🔧 Aplicando FIX (seta inbacktest=False)...")
    se.inbacktest = False
    se.bts = None
    print(f"   se.inbacktest: {se.inbacktest}")
    
    # Try to create and send an order
    print(f"\n🧪 TESTE: Tentando vender 1 NVDA em modo LIVE...")
    
    nvda_shares = se.get_shares("NVDA")
    print(f"   Posição atual: {nvda_shares} shares")
    
    if nvda_shares > 0:
        # Create order
        order = se.sellOrder("NVDA", 1.0)
        print(f"   Ordem criada: {order is not None}")
        
        if order:
            # Check order
            check = se.checkOrder(order)
            print(f"   Ordem válida: {check}")
            
            if check:
                # Send order
                print(f"   Enviando ordem em modo LIVE...")
                result = se.sendOrder(order)
                print(f"   Resultado sendOrder: {result}")
                
                # Get last order result
                last_result = se.getLastOrderResult()
                print(f"   Last order result: {last_result}")
                
                # Wait and check position
                import time
                time.sleep(2)
                
                nvda_after = se.get_shares("NVDA")
                print(f"   Posição após: {nvda_after} shares")
                
                if nvda_after < nvda_shares:
                    print(f"\n   ✅ SUCESSO! Ordem executou em modo LIVE!")
                    print(f"   ✅ Posição diminuiu de {nvda_shares} para {nvda_after}")
                else:
                    print(f"\n   ❌ FALHA! Posição não mudou")
                    print(f"   ⚠️ Pode ser cache - verifique MT5 terminal")
            else:
                print(f"   ❌ Ordem inválida")
        else:
            print(f"   ❌ Falha ao criar ordem")
    else:
        print(f"   ⚠️ Sem posição NVDA para testar")
    
    print(f"\n" + "=" * 70)
    print(f"FIM DO TESTE")
    print(f"=" * 70)

if __name__ == "__main__":
    main()


