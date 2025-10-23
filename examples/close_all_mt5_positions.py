"""
Emergency script to close ALL MT5 positions using MetaTrader5 library directly
"""
import MetaTrader5 as mt5
import time

def main():
    print("=" * 70)
    print("FECHANDO TODAS AS POSIÇÕES DO MT5 (EMERGÊNCIA)")
    print("=" * 70)
    
    if not mt5.initialize():
        print("❌ Falha ao inicializar MT5")
        return
    
    # Get all positions
    positions = mt5.positions_get()
    
    if not positions:
        print("✅ Nenhuma posição aberta")
        mt5.shutdown()
        return
    
    print(f"\n📊 Encontradas {len(positions)} posições abertas")
    print("\nFechando todas...")
    
    closed_count = 0
    failed_count = 0
    
    for position in positions:
        symbol = position.symbol
        volume = position.volume
        pos_type = position.type
        ticket = position.ticket
        
        # Determine close type (opposite of position type)
        if pos_type == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            action = "VENDA"
        else:
            close_type = mt5.ORDER_TYPE_BUY
            action = "COMPRA"
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"  ❌ Não foi possível obter preço de {symbol}")
            failed_count += 1
            continue
        
        price = tick.ask if close_type == mt5.ORDER_TYPE_BUY else tick.bid
        
        # Create close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 0,
            "comment": "Fechamento manual",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"  ✅ {action} {volume} {symbol} @ {price:.2f} - Fechado!")
            closed_count += 1
        else:
            print(f"  ❌ Falha: {symbol} - {result.comment}")
            failed_count += 1
        
        time.sleep(0.1)  # Small delay between orders
    
    print(f"\n" + "=" * 70)
    print(f"RESUMO:")
    print(f"  ✅ Fechadas: {closed_count}")
    print(f"  ❌ Falharam: {failed_count}")
    print("=" * 70)
    
    # Verify
    positions_after = mt5.positions_get()
    if positions_after:
        print(f"\n⚠️ Ainda existem {len(positions_after)} posições abertas:")
        for pos in positions_after:
            print(f"  - {pos.symbol}: {pos.volume}")
    else:
        print(f"\n🎉 SUCESSO! Todas as posições foram fechadas!")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()


