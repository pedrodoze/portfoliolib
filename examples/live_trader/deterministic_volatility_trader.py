# deterministic_volatility_trader.py
import mt5se as se
from mt5se import Trader
import numpy as np

class DeterministicVolatilityTrader(Trader):
    """
    Trader determinístico para teste de target volatility.
    
    Comportamento:
    - No primeiro dia do backtest/live: compra uma quantidade fixa de ativo
    - Mantém a posição até o fim (nunca vende)
    - Gera uma equity curve com volatilidade previsível
    
    Ideal para validar:
    - Cálculo de realized_volatility
    - Ajuste de alavancagem com target_volatility
    """
    def __init__(self, name: str, assets_universe: list, shares_to_buy: int = 10):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.shares_to_buy = shares_to_buy  # Quantidade fixa para comprar
        self._has_traded = False

    def trade(self, dbars: dict):
        if self._has_traded:
            return []  # Nunca altera a posição após a primeira compra

        orders = []
        asset = self.assets_universe[0]  # Usa apenas o primeiro ativo
        if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
            return []

        # Verifica se já tem posição (evita duplicação)
        current_shares = se.get_shares(asset)
        if current_shares != 0:
            self._has_traded = True
            return []

        # Compra quantidade fixa no primeiro sinal
        orders.append(se.buyOrder(asset, self.shares_to_buy))
        self._has_traded = True
        print(f"[DeterministicTrader] COMPRA {self.shares_to_buy} de {asset}")
        return orders