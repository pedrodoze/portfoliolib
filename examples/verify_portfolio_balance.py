"""
Simple script to verify if your portfolio is balanced at 50%/50%
Run this while your live trading system is running to check allocation
"""
import mt5se as se

def verify_portfolio_balance():
    """Verifica se o portfolio está balanceado em 50%/50%"""
    
    if not se.connect():
        print("❌ Erro ao conectar ao MetaTrader 5")
        return
    
    print("=" * 60)
    print("VERIFICAÇÃO DE BALANÇO DO PORTFÓLIO")
    print("=" * 60)
    
    # Define os ativos
    nvda_symbol = "NVDA"
    msft_symbol = "MSFT"
    
    # Obtém posições atuais
    nvda_shares = se.get_shares(nvda_symbol)
    msft_shares = se.get_shares(msft_symbol)
    
    # Obtém preços atuais
    nvda_bars = se.get_bars(nvda_symbol, 2)
    msft_bars = se.get_bars(msft_symbol, 2)
    
    if nvda_bars is None or nvda_bars.empty:
        print(f"❌ Não foi possível obter preço de {nvda_symbol}")
        return
    
    if msft_bars is None or msft_bars.empty:
        print(f"❌ Não foi possível obter preço de {msft_symbol}")
        return
    
    nvda_price = se.get_last(nvda_bars)
    msft_price = se.get_last(msft_bars)
    
    # Obtém cash disponível
    cash = se.get_balance()
    
    # Calcula valores
    nvda_value = nvda_shares * nvda_price
    msft_value = msft_shares * msft_price
    total_portfolio = nvda_value + msft_value + cash
    
    # Calcula percentuais
    nvda_pct = (nvda_value / total_portfolio * 100) if total_portfolio > 0 else 0
    msft_pct = (msft_value / total_portfolio * 100) if total_portfolio > 0 else 0
    cash_pct = (cash / total_portfolio * 100) if total_portfolio > 0 else 0
    
    # Exibe informações
    print(f"\n📊 POSIÇÕES ATUAIS:")
    print(f"   {nvda_symbol}: {nvda_shares} shares @ ${nvda_price:.2f} = ${nvda_value:,.2f}")
    print(f"   {msft_symbol}: {msft_shares} shares @ ${msft_price:.2f} = ${msft_value:,.2f}")
    print(f"   Cash: ${cash:,.2f}")
    print(f"   ─────────────────────────────────────")
    print(f"   TOTAL: ${total_portfolio:,.2f}")
    
    print(f"\n📈 ALOCAÇÃO PERCENTUAL:")
    print(f"   Portfolio_A ({nvda_symbol}): {nvda_pct:.2f}%")
    print(f"   Portfolio_B ({msft_symbol}): {msft_pct:.2f}%")
    print(f"   Cash não alocado: {cash_pct:.2f}%")
    print(f"   ─────────────────────────────────────")
    print(f"   TOTAL: {nvda_pct + msft_pct + cash_pct:.2f}%")
    
    # Verifica balanço
    print(f"\n🎯 VERIFICAÇÃO DE BALANÇO (Target: 50%/50%):")
    
    # Define tolerâncias
    perfect_threshold = 1.0  # Dentro de 1% = perfeito
    good_threshold = 2.0     # Dentro de 2% = bom
    
    nvda_diff = abs(nvda_pct - 50.0)
    msft_diff = abs(msft_pct - 50.0)
    max_diff = max(nvda_diff, msft_diff)
    
    if max_diff < perfect_threshold:
        status = "✅ PERFEITO"
        color = "green"
    elif max_diff < good_threshold:
        status = "✔️ BOM"
        color = "yellow"
    else:
        status = "⚠️ DESBALANCEADO"
        color = "red"
    
    print(f"   Portfolio_A: {nvda_pct:.2f}% (target: 50.00%, diff: {nvda_diff:+.2f}%)")
    print(f"   Portfolio_B: {msft_pct:.2f}% (target: 50.00%, diff: {msft_diff:+.2f}%)")
    print(f"\n   Status: {status}")
    
    if max_diff >= good_threshold:
        print(f"\n   ⚠️ Portfolio está desbalanceado em {max_diff:.2f}%")
        print(f"   ℹ️ O próximo rebalanceamento deve corrigir isso")
    
    # Mostra quanto falta para 50/50
    if total_portfolio > 0:
        target_nvda = total_portfolio * 0.5
        target_msft = total_portfolio * 0.5
        
        nvda_diff_value = target_nvda - nvda_value
        msft_diff_value = target_msft - msft_value
        
        print(f"\n💰 PARA ALCANÇAR 50%/50%:")
        if abs(nvda_diff_value) > 100:  # Só mostra se diferença > $100
            action = "COMPRAR" if nvda_diff_value > 0 else "VENDER"
            shares_needed = abs(nvda_diff_value / nvda_price)
            print(f"   {nvda_symbol}: {action} ${abs(nvda_diff_value):,.2f} (~{shares_needed:.0f} shares)")
        else:
            print(f"   {nvda_symbol}: ✅ Já está no target")
            
        if abs(msft_diff_value) > 100:
            action = "COMPRAR" if msft_diff_value > 0 else "VENDER"
            shares_needed = abs(msft_diff_value / msft_price)
            print(f"   {msft_symbol}: {action} ${abs(msft_diff_value):,.2f} (~{shares_needed:.0f} shares)")
        else:
            print(f"   {msft_symbol}: ✅ Já está no target")
    
    print("\n" + "=" * 60)
    
    return {
        'nvda_pct': nvda_pct,
        'msft_pct': msft_pct,
        'cash_pct': cash_pct,
        'is_balanced': max_diff < good_threshold,
        'max_deviation': max_diff
    }

if __name__ == "__main__":
    verify_portfolio_balance()


