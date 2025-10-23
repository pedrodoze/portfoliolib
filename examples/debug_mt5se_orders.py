"""
Debug why se.sellOrder() returns None
"""
import mt5se as se

def main():
    print("=" * 70)
    print("DEBUG: Investigando por que se.sellOrder() retorna None")
    print("=" * 70)
    
    if not se.connect():
        print("❌ Falha ao conectar")
        return
    
    # Check if we're in live mode
    print(f"\n🔍 Verificando modo de operação:")
    print(f"   se.is_live(): {hasattr(se, 'is_live') and se.is_live()}")
    print(f"   se.backtest: {hasattr(se, 'backtest')}")
    
    # Get current shares
    nvda_shares = se.get_shares("NVDA")
    print(f"\n📊 Posição atual NVDA: {nvda_shares} shares")
    
    if nvda_shares <= 0:
        print("   Sem posição para testar")
        return
    
    # Get price
    bars = se.get_bars("NVDA", 2)
    if bars is None or bars.empty:
        print("   ❌ Não foi possível obter preço")
        return
    
    price = se.get_last(bars)
    print(f"   Preço atual: ${price:.2f}")
    
    # Try different ways to create sell order
    print(f"\n🧪 TESTE 1: se.sellOrder() padrão")
    order1 = se.sellOrder("NVDA", 1.0)
    print(f"   Resultado: {order1}")
    print(f"   Tipo: {type(order1)}")
    
    print(f"\n🧪 TESTE 2: se.sellOrder() com mais parâmetros")
    try:
        order2 = se.sellOrder("NVDA", 1.0, price=price)
        print(f"   Resultado: {order2}")
    except Exception as e:
        print(f"   Erro: {e}")
    
    print(f"\n🧪 TESTE 3: Verificar se há função alternativa")
    print(f"   se.sell: {hasattr(se, 'sell')}")
    print(f"   se.close_position: {hasattr(se, 'close_position')}")
    print(f"   se.close: {hasattr(se, 'close')}")
    
    # Try buyOrder to see if it also returns None
    print(f"\n🧪 TESTE 4: se.buyOrder() para comparação")
    order3 = se.buyOrder("NVDA", 1.0)
    print(f"   Resultado: {order3}")
    print(f"   Tipo: {type(order3)}")
    
    # Check balance
    balance = se.get_balance()
    print(f"\n💰 Balance: ${balance:,.2f}")
    
    # List all se functions related to orders
    print(f"\n📋 Funções disponíveis no se relacionadas a ordens:")
    for attr in dir(se):
        if 'order' in attr.lower() or 'sell' in attr.lower() or 'buy' in attr.lower() or 'close' in attr.lower():
            print(f"   - {attr}")
    
    # Check if there's a mode we need to set
    print(f"\n🔍 Verificando modos disponíveis:")
    for attr in dir(se):
        if 'mode' in attr.lower() or 'live' in attr.lower() or 'backtest' in attr.lower():
            print(f"   - {attr}: {getattr(se, attr, 'N/A')}")

if __name__ == "__main__":
    main()


