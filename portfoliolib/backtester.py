# portfoliolib/backtester.py (versão final com simulação dia a dia)

import pandas as pd
from datetime import datetime
import mt5se as se
from .manager import PortfolioManager
import math


class WeightToOrderAdapter(se.Trader):
    """
    Adapter que converte traders baseados em weights para o formato de orders esperado pelo MT5SE backtest.
    
    Uso:
        weight_trader = MyWeightBasedTrader()
        adapted_trader = WeightToOrderAdapter(weight_trader, allocated_capital=100000.0)
        se.backtest.run(adapted_trader, bts)  # Funciona!
    """
    def __init__(self, weight_trader, allocated_capital=100000.0):
        super().__init__()
        self.weight_trader = weight_trader
        self.allocated_capital = allocated_capital
        self.name = getattr(weight_trader, 'name', 'AdaptedTrader')
        self.frequency = getattr(weight_trader, 'frequency', se.DAILY)
        
        # Copia atributos importantes
        if hasattr(weight_trader, 'assets_universe'):
            self.assets_universe = weight_trader.assets_universe
        elif hasattr(weight_trader, 'assets'):
            self.assets = weight_trader.assets
    
    def setup(self, dbars):
        """Propaga setup para o trader original"""
        if hasattr(self.weight_trader, 'setup'):
            self.weight_trader.setup(dbars)
    
    def trade(self, dbars):
        """
        Converte weights retornados pelo trader em orders para backtest.
        
        Fluxo:
        1. Chama weight_trader.trade() → recebe {'NVDA': 0.6, 'cash': 0.4}
        2. Calcula targets em $ → $60,000 NVDA, $40,000 cash
        3. Obtém posições atuais do backtest
        4. Calcula diferença
        5. Retorna orders para ajustar posições
        """
        # NOVO: Constrói my_positions para traders que precisam
        my_positions = {}
        
        # Obtém assets do trader
        trader_assets = []
        if hasattr(self.weight_trader, 'assets_universe'):
            trader_assets = self.weight_trader.assets_universe
        elif hasattr(self.weight_trader, 'assets'):
            trader_assets = self.weight_trader.assets
        
        # Para cada asset, obtém posição atual do backtest
        for asset in trader_assets:
            shares = se.get_shares(asset)
            if shares != 0 and asset in dbars and dbars[asset] is not None and not dbars[asset].empty:
                price = se.get_last(dbars[asset])
                my_positions[asset] = {
                    'shares': shares,
                    'price': price,
                    'value': shares * price
                }
        
        # Chama o trader original, passando my_positions se aceitar
        import inspect
        try:
            sig = inspect.signature(self.weight_trader.trade)
            if 'my_positions' in sig.parameters or len(sig.parameters) > 1:
                weights = self.weight_trader.trade(dbars, my_positions=my_positions)
            else:
                weights = self.weight_trader.trade(dbars)
        except Exception as e:
            # DEBUG: Mostra erro se trader.trade() falhar
            print(f"[DEBUG Adapter] Erro ao chamar trader.trade(): {e}")
            weights = self.weight_trader.trade(dbars)
        
        # Se retornar None, lista vazia, ou não for dict → sem trades
        if weights is None:
            return []
        
        if isinstance(weights, list):
            # Se já retornar orders, passa direto (backwards compatibility)
            return weights
        
        if not isinstance(weights, dict):
            return []
        orders = []
        
        for asset, weight in weights.items():
            if asset == 'cash':
                continue  # Cash não gera ordem
            
            # Calcula target em $
            target_value = self.allocated_capital * weight
            
            # Obtém preço atual
            if asset not in dbars or dbars[asset] is None or dbars[asset].empty:
                continue
            
            price = se.get_last(dbars[asset])
            if price <= 0:
                continue
            
            # Obtém posição atual (do backtest)
            current_shares = se.get_shares(asset)
            current_value = current_shares * price
            
            # Calcula diferença
            value_diff = target_value - current_value
            shares_diff = value_diff / price
            
            # Arredonda para step size
            step = se.get_volume_step(asset)
            if step > 0:
                shares_diff = math.floor(shares_diff / step) * step
            else:
                shares_diff = math.floor(shares_diff)
            
            # Cria ordem se diferença for significativa
            min_shares = step * 2 if step > 0 else 2
            
            if shares_diff >= min_shares:
                # Precisa comprar
                order = se.buyOrder(asset, shares_diff)
                if order:
                    orders.append(order)
            elif shares_diff <= -min_shares:
                # Precisa vender
                order = se.sellOrder(asset, abs(shares_diff))
                if order:
                    orders.append(order)
        
        return orders
    
    def ending(self, dbars):
        """Propaga ending para o trader original"""
        if hasattr(self.weight_trader, 'ending'):
            self.weight_trader.ending(dbars)

class PortfolioBacktester:
    def __init__(self, manager: PortfolioManager, start_date: datetime, end_date: datetime,
                 lookback_period: pd.DateOffset, rebalance_frequency: str,
                 prestart_dt: datetime):
        self.manager = manager
        self.start_date = start_date
        self.end_date = end_date
        self.lookback_period = lookback_period
        self.rebalance_frequency = rebalance_frequency
        self.prestart_dt = prestart_dt

    def _get_trader_returns(self, trader_name: str) -> pd.Series:
        """
        Executa um backtest completo e fiel ao mt5se para um trader e retorna seus retornos diários.
        Agora suporta traders baseados em weights através do WeightToOrderAdapter.
        """
        trader_object = self.manager.trader_map[trader_name]
        assets = getattr(trader_object, 'assets_universe', [])
        
        # Usa as datas de início e prestart globais para garantir consistência
        start_dt = self.start_date
        end_dt = self.end_date
        period = getattr(trader_object, 'frequency', se.DAILY)
        
        # CRÍTICO: Ajusta prestart para garantir bars suficientes para indicadores
        # MT5SE usa rolling window: prestart→start define tamanho da janela
        # Para indicadores como RSI (precisa 15+ bars), precisamos janela maior
        from datetime import timedelta
        
        if period == se.DAILY:
            # DAILY: precisa ~30 dias de história mínima para indicadores
            min_history_days = 30
            prestart_dt = start_dt - timedelta(days=min_history_days)
        else:
            # INTRADAY: precisa ~100 bars (depende do período)
            # Estimativa: 100 minutos = ~2 horas de mercado
            min_history_days = 5  # 5 dias de intraday deve dar 100+ bars
            prestart_dt = start_dt - timedelta(days=min_history_days)
        
        # Usa o mais antigo entre prestart calculado e self.prestart_dt
        if self.prestart_dt < prestart_dt:
            prestart_dt = self.prestart_dt
        
        print(f"    - Rodando simulação base para {trader_name} de {start_dt.date()} a {end_dt.date()} (Prestart: {prestart_dt.date()})")
        
        bts = se.backtest.set(assets, prestart_dt, start_dt, end_dt, period, 100000.0)
        
        # Wrap com adapter para suportar weights
        adapted_trader = WeightToOrderAdapter(trader_object, allocated_capital=100000.0)
        
        results_df = se.backtest.run(adapted_trader, bts)

        if results_df is None or not isinstance(results_df, pd.DataFrame) or results_df.empty:
            return pd.Series(dtype=float)

        results_df['date'] = pd.to_datetime(results_df['date'])
        equity_curve = results_df.set_index('date')['equity']
        
        # DEBUG: Check equity
        print(f"       Equity: first=${equity_curve.iloc[0]:,.2f}, last=${equity_curve.iloc[-1]:,.2f}, bars={len(equity_curve)}")
        
        # Calculate returns
        returns = equity_curve.pct_change().fillna(0)
        
        # DEBUG: Check if returns are all zero
        non_zero_returns = (returns != 0).sum()
        print(f"       Returns: {len(returns)} dias, {non_zero_returns} com retorno não-zero")
        
        return returns

    def run(self) -> pd.Series:
        print("Iniciando backtest com simulação precisa dia a dia...")
        
        # 1. PRÉ-CÁLCULO DOS RETORNOS PUROS
        full_returns_df = pd.DataFrame()
        for trader_name in self.manager.trader_map.keys():
            returns_series = self._get_trader_returns(trader_name)
            full_returns_df[trader_name] = returns_series
            
            # DEBUG: Show what we got
            print(f"\n    Returns para {trader_name}:")
            print(f"       Total pontos: {len(returns_series)}")
            print(f"       Date range: {returns_series.index[0]} to {returns_series.index[-1]}")
            print(f"       Non-zero returns: {(returns_series != 0).sum()}")
            print(f"       Mean return: {returns_series.mean():.6f}")
        
        if full_returns_df.empty:
            print("ERRO FATAL: Nenhum dado de retorno foi pré-calculado.")
            return pd.Series(dtype=float)

        # 2. SIMULAÇÃO DIA A DIA
        rebalance_dates = pd.date_range(self.start_date, self.end_date, freq=self.rebalance_frequency)
        current_weights = pd.Series(self.manager.current_weights)
        
        # Cria um índice com todos os dias de negociação reais
        trading_days = full_returns_df.loc[self.start_date:self.end_date].index
        if trading_days.empty:
            print("AVISO: Nenhum dia de negociação encontrado no período especificado.")
            return pd.Series(dtype=float)
        
        equity = pd.Series(index=trading_days, dtype=float)
        equity.iloc[0] = self.manager.total_equity
        next_rebalance_idx = 0

        for i in range(1, len(trading_days)):
            today = trading_days[i]
            yesterday = trading_days[i-1]

            if next_rebalance_idx < len(rebalance_dates) and today >= rebalance_dates[next_rebalance_idx]:
                lookback_start = today - self.lookback_period
                print(f"\n--- Checando Rebalanceamento em {today.date()} ---")
                
                # Verifica se temos dados suficientes no lookback
                lookback_end = today - pd.DateOffset(days=1)
                
                # Tenta pegar dados de lookback
                try:
                    lookback_returns = full_returns_df.loc[lookback_start:lookback_end]
                    
                    if len(lookback_returns) >= 5:  # Mínimo 5 pontos de dados
                        lookback_equity = (1 + lookback_returns).cumprod()
                        
                        if not lookback_equity.empty:
                            self.manager.update_weights(lookback_equity.ffill())
                            current_weights = pd.Series(self.manager.current_weights)
                            print(f"   - Pesos atualizados com {len(lookback_returns)} pontos")
                        else:
                            print(f"   - Lookback equity vazio. Pesos mantidos.")
                    else:
                        print(f"   - Lookback insuficiente ({len(lookback_returns)} pontos < 5). Pesos mantidos.")
                except Exception as e:
                    print(f"   - Erro no lookback: {e}. Pesos mantidos.")
                    
                next_rebalance_idx += 1

            # Calcula o retorno do dia e compõe o capital
            daily_returns = full_returns_df.loc[today]
            portfolio_return = (daily_returns * current_weights).sum()
            equity.iloc[i] = equity.loc[yesterday] * (1 + portfolio_return)
            
            # DEBUG: Log progress periodically
            if i % 5 == 0 or i < 3:
                print(f"   Day {i}: {today.date()}, Returns: {daily_returns.values}, Portfolio Return: {portfolio_return:.4f}, Equity: ${equity.iloc[i]:,.2f}")

        print("\nBacktest walk-forward concluído!")
        return equity.ffill()