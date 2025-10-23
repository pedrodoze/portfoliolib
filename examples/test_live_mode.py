"""
Test how to activate MT5SE live trading mode
"""
import mt5se as se

def main():
    print("=" * 70)
    print("TEST: Ativando modo LIVE do MT5SE")
    print("=" * 70)
    
    # Connect
    if not se.connect():
        print("❌ Falha ao conectar")
        return
    
    print(f"\n📊 Estado ANTES:")
    print(f"   se.is_live(): {se.is_live()}")
    print(f"   se.inbacktest: {se.inbacktest}")
    
    # Try to activate live mode
    print(f"\n🔧 Tentando ativar modo LIVE...")
    
    # Method 1: Check if there's a set_live() function
    if hasattr(se, 'set_live'):
        print(f"   Tentando se.set_live()...")
        se.set_live()
    
    # Method 2: Check if there's a live() function
    if hasattr(se, 'live'):
        print(f"   Tentando se.live()...")
        try:
            se.live()
        except Exception as e:
            print(f"   Erro: {e}")
    
    # Method 3: Set inbacktest to False
    if hasattr(se, 'inbacktest'):
        print(f"   Tentando se.inbacktest = False...")
        se.inbacktest = False
    
    print(f"\n📊 Estado DEPOIS:")
    print(f"   se.is_live(): {se.is_live()}")
    print(f"   se.inbacktest: {se.inbacktest}")
    
    # Now try to send an order
    print(f"\n🧪 TESTE: Tentando vender 1 NVDA em modo LIVE...")
    
    nvda_shares = se.get_shares("NVDA")
    print(f"   Posição atual: {nvda_shares} shares")
    
    if nvda_shares > 0:
        order = se.sellOrder("NVDA", 1.0)
        print(f"   Ordem criada: {order}")
        
        if order:
            check = se.checkOrder(order)
            print(f"   Ordem válida? {check}")
            
            if check:
                print(f"   Enviando ordem...")
                result = se.sendOrder(order)
                print(f"   Resultado: {result}")
                
                # Check if position changed
                import time
                time.sleep(1)
                nvda_after = se.get_shares("NVDA")
                print(f"   Posição após: {nvda_after} shares")
                
                if nvda_after < nvda_shares:
                    print(f"   ✅ SUCESSO! Posição diminuiu!")
                else:
                    print(f"   ❌ FALHA! Posição não mudou!")
    
    # List all functions that might help
    print(f"\n📋 Funções relacionadas a live/backtest:")
    for attr in dir(se):
        if any(word in attr.lower() for word in ['live', 'backtest', 'mode', 'set']):
            val = getattr(se, attr, None)
            if callable(val) or isinstance(val, bool):
                print(f"   - {attr}: {type(val).__name__}")

if __name__ == "__main__":
    main()


