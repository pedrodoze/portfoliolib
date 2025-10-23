 # hold_forever_trader.py
import mt5se as se
from mt5se import Trader

class HoldForeverTrader(Trader):
    """
    Trader que compra 1 unidade do ativo no primeiro dia e segura para sempre.
    Ideal para validar equity curve e volatilidade.
    """
    def __init__(self, asset: str):
        super().__init__()
        self.asset = asset
        self._bought = False

    def trade(self, dbars):
        if self._bought:
            return []
        if self.asset not in dbars or dbars[self.asset] is None or dbars[self.asset].empty:
            return []
        # Compra exatamente 1 unidade no primeiro sinal
        self._bought = True
        volume = int(100000/se.get_last(dbars[self.asset]))  # 0.01 lote padrão
        return [se.buyOrder(self.asset, volume)]