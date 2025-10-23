import mt5se as se
from mt5se import Trader
from datetime import datetime

class LiveRsiTrader(Trader):

    def __init__(
        self, 
        name: str, 
        assets_universe: list, 
        frequency: str,
        rsi_window: int = 14,
        rsi_oversold: float = 30.0
    ):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.frequency = frequency
        self.rsi_window = rsi_window          # ← Janela explícita do RSI
        self.rsi_oversold = rsi_oversold      # ← Limite configurável
        self.capital = 0.0  # Será definido pelo PortfolioManager

    def trade(self, dbars: dict):
        if hasattr(self, 'capital') and self.capital > 0:
        # Modo LIVE: usa capital alocado pelo PortfolioManager
            total_capital = self.capital
        else:
            # Modo BACKTEST: usa o saldo da simulação do MT5SE
            total_capital = se.get_balance()
            if total_capital <= 0:
                return []

        orders = []
        capital_per_asset = total_capital / len(self.assets_universe)

        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue

            bars = dbars[asset]
            if len(bars) < self.rsi_window:
                continue  # Não há dados suficientes

            # Pega as últimas N barras, MAS mantém o índice original
            bars = bars.tail(self.rsi_window)
            price = se.get_last(bars)
            rsi = se.tech.rsi(bars)
            
            if rsi is None:
                continue

            current_shares = se.get_shares(asset)

            # LÓGICA DE SAÍDA: vende se RSI > 70 (sobrecomprado)
            if current_shares > 0 and rsi >= 70.0:
                orders.append(se.sellOrder(asset, current_shares))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: Sinal de VENDA para {asset} (RSI={rsi:.2f})")

            # LÓGICA DE ENTRADA: compra se RSI <= oversold E sem posição
            elif current_shares == 0 and rsi <= self.rsi_oversold:
                shares_to_buy = se.get_affor_shares(asset, price, capital_per_asset)
                if shares_to_buy > 0:
                    orders.append(se.buyOrder(asset, shares_to_buy))
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: Sinal de COMPRA para {asset} (RSI={rsi:.2f})")

        return orders


# guaranteed_signal_trader.py
import mt5se as se
from mt5se import Trader
from datetime import datetime

class GuaranteedSignalTrader(Trader):
    """
    Trader de teste que gera sinais garantidos:
    - Compra no primeiro dia do período de backtest
    - Vende no último dia do período de backtest
    Útil para validar a integração do pipeline de backtest e live.
    """
    def __init__(self, name: str, assets_universe: list, frequency: str = se.DAILY):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.frequency = frequency
        self.capital = 0.0
        self._first_trade_done = False
        self._last_trade_done = False
        self._backtest_start = None
        self._backtest_end = None

    def _detect_backtest_period(self, dbars: dict):
        """Detecta o período do backtest com base nos dados recebidos."""
        if self._backtest_start is not None and self._backtest_end is not None:
            return
        
        all_dates = []
        for bars in dbars.values():
            if bars is not None and not bars.empty:
                all_dates.extend(bars.index.tolist())
        
        if all_dates:
            self._backtest_start = min(all_dates)
            self._backtest_end = max(all_dates)

    def trade(self, dbars: dict):
        if not dbars or self.capital <= 0:
            return []

        # Detecta o período do backtest (só funciona em backtest ou live com histórico)
        self._detect_backtest_period(dbars)

        orders = []
        current_time = None

        # Tenta obter a data atual dos dados
        for bars in dbars.values():
            if bars is not None and not bars.empty:
                current_time = bars.index[-1]
                break

        if current_time is None:
            return []

        capital_per_asset = self.capital / len(self.assets_universe)

        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue

            bars = dbars[asset]
            price = se.get_last(bars)
            current_shares = se.get_shares(asset)

            # SINAL DE COMPRA: no primeiro dia
            if not self._first_trade_done and self._backtest_start is not None:
                if abs((current_time - self._backtest_start).days) <= 1:
                    shares_to_buy = se.get_affor_shares(asset, price, capital_per_asset)
                    if shares_to_buy > 0:
                        orders.append(se.buyOrder(asset, shares_to_buy))
                        self._first_trade_done = True
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: COMPRA garantida em {asset} no início do período")

            # SINAL DE VENDA: no último dia
            elif not self._last_trade_done and self._backtest_end is not None:
                if abs((current_time - self._backtest_end).days) <= 1 and current_shares > 0:
                    orders.append(se.sellOrder(asset, current_shares))
                    self._last_trade_done = True
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: VENDA garantida em {asset} no fim do período")

        return orders
    
    
    
    # simple_always_buy_trader.py
import mt5se as se
from mt5se import Trader
from datetime import datetime

class AlwaysBuyTrader(Trader):
    def __init__(self, name: str, assets_universe: list, frequency: str = se.DAILY):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.frequency = frequency
        self.capital = 0.0
        self._has_traded = False  # Evita spam de ordens

    def trade(self, dbars: dict):
        if hasattr(self, 'capital') and self.capital > 0:
        # Modo LIVE: usa capital alocado pelo PortfolioManager
            total_capital = self.capital
        else:
            # Modo BACKTEST: usa o saldo da simulação do MT5SE
            total_capital = se.get_balance()
            if total_capital <= 0:
                return []
        
        orders = []
        capital_per_asset = total_capital / len(self.assets_universe)
        
        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue
            
            bars = dbars[asset]
            price = se.get_last(bars)
            shares = se.get_affor_shares(asset, price, capital_per_asset)
            
            if shares > 0:
                orders.append(se.buyOrder(asset, shares))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: COMPRA FORÇADA de {shares} {asset}")
                self._has_traded = True  # Só compra uma vez
        
        return orders
























