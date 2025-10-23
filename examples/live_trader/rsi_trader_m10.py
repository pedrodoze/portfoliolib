# examples/traders/rsi_trader_m10.py (com gerenciamento de risco)

import mt5se as se
from mt5se import Trader
from datetime import datetime

class RsiM10Trader(Trader):
    """
    Este trader opera em um timeframe de 1 minuto, mas baseia suas decisões
    no RSI calculado sobre as últimas 10 barras de 1 minuto.

    - Entra na posição (compra) se RSI(10) >= 60.
    - Sai da posição (vende) se RSI(10) <= 40.
    - **NOVO:** Usa no máximo 5% do capital alocado por trade.
    """
    def __init__(self, name: str, assets_universe: list):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.capital = 0.0 

    def trade(self, dbars: dict):
        orders = []
        
        effective_capital = self.capital if hasattr(self, 'capital') and self.capital > 0 else se.get_balance()
        capital_per_asset = effective_capital / len(self.assets_universe)

        # --- NOVA LÓGICA DE GERENCIAMENTO DE RISCO ---
        # Define que cada novo trade usará no máximo 5% do capital alocado para o ativo.
        capital_for_this_trade = capital_per_asset * 0.05

        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue
            
            bars = dbars[asset]
            curr_shares = se.get_shares(asset)
            price = se.get_last(bars)
            
            # Calcula as ações que pode comprar com o capital LIMITADO para este trade
            free_shares = se.get_affor_shares(asset, price, capital_for_this_trade)
            
            # Garante que o volume seja pelo menos o mínimo negociável (geralmente 1)
            if free_shares < 1:
                free_shares = 0

            rsi = se.tech.rsi(bars)
            
            order = None
            if rsi >= 60 and free_shares > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {asset}: Sinal de COMPRA (RSI={rsi:.2f})")
                order = se.buyOrder(asset, free_shares)
            elif rsi <= 40 and curr_shares > 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {asset}: Sinal de VENDA (RSI={rsi:.2f})")
                # Ao sair, vende a posição inteira
                order = se.sellOrder(asset, curr_shares)
            
            if order:
                orders.append(order)
                
        return orders