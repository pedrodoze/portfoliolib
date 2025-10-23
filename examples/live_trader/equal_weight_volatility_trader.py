# examples/live_trader/equal_weight_volatility_trader.py

import mt5se as se
from mt5se import Trader
from datetime import datetime
import pandas as pd
import numpy as np

class EqualWeightVolatilityTrader(Trader):
    """
    Trader que opera com pesos iguais entre ativos e foca em volatilidade controlada.
    
    Características:
    - Distribui capital igualmente entre todos os ativos
    - Usa RSI para sinais de entrada/saída
    - Gerencia risco por posição
    - Suporta diferentes timeframes
    """
    
    def __init__(self, name: str, assets_universe: list, 
                 rsi_buy_threshold: float = 60, rsi_sell_threshold: float = 40,
                 risk_per_trade: float = 0.05, timeframe: str = se.DAILY):
        super().__init__()
        self.name = name
        self.assets_universe = assets_universe
        self.rsi_buy_threshold = rsi_buy_threshold
        self.rsi_sell_threshold = rsi_sell_threshold
        self.risk_per_trade = risk_per_trade  # 5% do capital por trade
        self.frequency = timeframe
        self.capital = 0.0

    def trade(self, dbars: dict):
        """
        Executa trades baseado em RSI com gestão de risco.
        """
        orders = []
        
        if not dbars:
            return orders
            
        # Calcula capital efetivo disponível
        effective_capital = self.capital if hasattr(self, 'capital') and self.capital > 0 else se.get_balance()
        
        if effective_capital <= 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: Sem capital disponível")
            return orders
        
        # Capital por ativo (peso igual)
        capital_per_asset = effective_capital / len(self.assets_universe)
        
        # Capital para este trade (gerenciamento de risco)
        trade_capital = capital_per_asset * self.risk_per_trade
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name}: Capital=${effective_capital:.2f}, "
              f"Por ativo=${capital_per_asset:.2f}, Trade=${trade_capital:.2f}")
        
        for asset in self.assets_universe:
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue
                
            try:
                bars = dbars[asset]
                curr_shares = se.get_shares(asset)
                price = se.get_last(bars)
                
                if price <= 0:
                    continue
                
                # Calcula RSI
                rsi = se.tech.rsi(bars)
                
                if pd.isna(rsi):
                    continue
                
                # Calcula quantidade de ações para este trade
                target_shares = se.get_affor_shares(asset, price, trade_capital)
                
                # Garante volume mínimo
                if target_shares < 1:
                    target_shares = 0
                
                order = None
                
                # Lógica de trading baseada em RSI
                if rsi >= self.rsi_buy_threshold and target_shares > 0:
                    # Sinal de compra
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name} {asset}: "
                          f"COMPRA - RSI={rsi:.2f}, Qty={target_shares}")
                    order = se.buyOrder(asset, target_shares)
                    
                elif rsi <= self.rsi_sell_threshold and curr_shares > 0:
                    # Sinal de venda
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name} {asset}: "
                          f"VENDA - RSI={rsi:.2f}, Qty={curr_shares}")
                    order = se.sellOrder(asset, curr_shares)
                
                if order:
                    orders.append(order)
                    
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.name} {asset}: Erro - {e}")
                continue
        
        return orders

    def get_volatility_estimate(self, dbars: dict, lookback_days: int = 30) -> float:
        """
        Estima a volatilidade histórica do trader baseada nos retornos.
        """
        try:
            if not dbars:
                return 0.0
            
            # Coleta dados de todos os ativos
            all_returns = []
            
            for asset in self.assets_universe:
                if asset in dbars and dbars[asset] is not None and not dbars[asset].empty:
                    bars = dbars[asset]
                    returns = bars['close'].pct_change().dropna()
                    if len(returns) >= lookback_days:
                        all_returns.extend(returns.tail(lookback_days).tolist())
            
            if len(all_returns) < 10:  # Mínimo de dados
                return 0.0
            
            # Calcula volatilidade anualizada
            daily_vol = np.std(all_returns)
            annual_vol = daily_vol * np.sqrt(252)
            
            return annual_vol
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao calcular volatilidade: {e}")
            return 0.0

