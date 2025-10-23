# portfoliolib/manager.py - Versão com Target Volatility

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from mt5se import Trader
from .optimizers import BaseOptimizer
from datetime import datetime

class PortfolioManager:
    """
    Gerencia a alocação de capital entre múltiplos traders e otimiza os pesos do portfólio.
    Suporta target volatility para controlar o risco total do portfólio.
    """
    def __init__(self,
                 traders: List[Trader],
                 optimizer: BaseOptimizer,
                 initial_equity: float,
                 initial_weights: Dict[str, float] = None,
                 target_volatility: Optional[float] = None,
                 max_leverage: float = 1.0,
                 volatility_floor: float = 0.001):
        """
        Args:
            traders: Lista de traders para o portfólio
            optimizer: Estratégia de otimização de pesos
            initial_equity: Capital inicial
            initial_weights: Pesos iniciais (opcional)
            target_volatility: Volatilidade anual alvo (ex: 0.10 para 10%). None desativa o controle
            max_leverage: Alavancagem máxima permitida (ex: 1.5 para 150% de exposição)
            volatility_floor: Volatilidade mínima para evitar divisão por zero (padrão 0.1% anual)
        """
        
        if not traders:
            raise ValueError("A lista de traders não pode estar vazia.")

        self.traders = traders
        self.optimizer = optimizer
        self.initial_equity = initial_equity
        self.total_equity = initial_equity
        
        # Parâmetros de target volatility
        self.target_volatility = target_volatility
        self.max_leverage = max(max_leverage, 0.1)  # Mínimo 10% para evitar problemas
        self.volatility_floor = max(volatility_floor, 0.0001)  # Mínimo 0.01% anual
        self.current_leverage = 1.0
        self.realized_volatility = None
        
        # Histórico para cálculo de volatilidade
        self.historical_equity_curves = None
        
        # Cria mapa de traders com nomes únicos
        self.trader_map: Dict[str, Trader] = {}
        for i, trader in enumerate(traders):
            # Usa nome do trader se disponível, senão cria um nome padrão
            if hasattr(trader, 'name'):
                name = trader.name
            else:
                name = f"{trader.__class__.__name__}_{i}"
            
            # Garante nomes únicos
            base_name = name
            counter = 1
            while name in self.trader_map:
                name = f"{base_name}_{counter}"
                counter += 1
            
            self.trader_map[name] = trader
        
        # Inicializa pesos
        if initial_weights:
            # Valida pesos iniciais
            if not np.isclose(sum(initial_weights.values()), 1.0, rtol=1e-5):
                # Normaliza automaticamente se a soma não for 1
                total = sum(initial_weights.values())
                initial_weights = {k: v/total for k, v in initial_weights.items()}
                print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Pesos iniciais normalizados")
                
            if set(initial_weights.keys()) != set(self.trader_map.keys()):
                # Adiciona traders faltantes com peso zero
                missing = set(self.trader_map.keys()) - set(initial_weights.keys())
                for trader in missing:
                    initial_weights[trader] = 0.0
                # Remove traders extras
                extra = set(initial_weights.keys()) - set(self.trader_map.keys())
                for trader in extra:
                    del initial_weights[trader]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Pesos ajustados para corresponder aos traders")
                
            self.current_weights = initial_weights
        else:
            # Pesos iguais por padrão
            num_traders = len(self.trader_map)
            self.current_weights = {name: 1.0 / num_traders 
                                   for name in self.trader_map.keys()}

        self.capital_allocation: Dict[str, float] = {}
        
        # Log inicial
        print(f"[{datetime.now().strftime('%H:%M:%S')}] PortfolioManager iniciado")
        print(f"   - Traders: {list(self.trader_map.keys())}")
        print(f"   - Capital inicial: ${initial_equity:,.2f}")
        print(f"   - Target volatility: {f'{target_volatility:.1%}' if target_volatility else 'Desativado'}")
        print(f"   - Max leverage: {max_leverage:.1f}x")
        print(f"   - Pesos iniciais: {self.current_weights}")

    def _calculate_portfolio_volatility(self, equity_curves: pd.DataFrame) -> float:
        """
        Calcula a volatilidade anualizada do portfólio baseada nos pesos atuais.
        
        Args:
            equity_curves: DataFrame com curvas de equity históricas dos traders
            
        Returns:
            Volatilidade anualizada (0.10 = 10%)
        """
        if equity_curves.empty or len(equity_curves) < 2:
            return self.volatility_floor
        
        try:
            # Calcula retornos de cada trader
            returns = equity_curves.pct_change().dropna()
            
            if returns.empty:
                return self.volatility_floor
            
            # Cria série de pesos alinhada com as colunas de retornos
            weights_series = pd.Series(index=returns.columns, dtype=float)
            for col in returns.columns:
                weights_series[col] = self.current_weights.get(col, 0.0)
            
            # Normaliza pesos se necessário
            weight_sum = weights_series.sum()
            if weight_sum > 0:
                weights_series = weights_series / weight_sum
            else:
                return self.volatility_floor
            
            # Calcula retorno do portfólio ponderado
            portfolio_returns = (returns * weights_series).sum(axis=1)
            
            # Calcula volatilidade
            daily_vol = portfolio_returns.std()
            
            # Anualiza (assumindo 252 dias de trading)
            annual_vol = daily_vol * np.sqrt(252)
            
            # Aplica floor para evitar divisão por zero
            return max(annual_vol, self.volatility_floor)
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao calcular volatilidade: {e}")
            return self.volatility_floor

    def _calculate_leverage_factor(self, realized_vol: float) -> float:
        """
        Calcula o fator de alavancagem para atingir a volatilidade alvo.
        
        Args:
            realized_vol: Volatilidade realizada do portfólio
            
        Returns:
            Fator de alavancagem (1.0 = 100% do capital)
        """
        if self.target_volatility is None or realized_vol <= 0:
            return 1.0
        
        # Calcula leverage ideal
        ideal_leverage = self.target_volatility / realized_vol
        
        # Aplica limites
        return min(ideal_leverage, self.max_leverage)

    def calculate_var_5pct(self, equity_series: pd.Series) -> float:
        """
        Calcula o VaR 5% simples usando a série de equity do backtest.
        
        Args:
            equity_series: Série de equity do portfólio
            
        Returns:
            VaR 5% em valor absoluto ($)
        """
        if len(equity_series) < 2:
            return 0.0
        
        # Calcula retornos diários
        returns = equity_series.pct_change().dropna()
        
        if len(returns) < 10:  # Mínimo 10 observações
            return 0.0
        
        # Calcula o percentil 5% dos retornos
        var_5pct_return = np.percentile(returns, 5)
        
        # Converte para valor absoluto usando o valor atual do portfólio
        var_5pct_percentage = var_5pct_return
        
        return var_5pct_percentage

    def update_weights(self, historical_equity_curves: pd.DataFrame):
        """
        Atualiza os pesos do portfólio baseado em curvas de equity históricas.
        Se target_volatility estiver ativo, também ajusta a alavancagem.
        
        Args:
            historical_equity_curves: DataFrame com curvas de equity dos traders
        """
        try:
            # Armazena curvas históricas para cálculo de volatilidade
            self.historical_equity_curves = historical_equity_curves.copy()
            
            # Garante que temos dados para todos os traders
            available_traders = set(historical_equity_curves.columns)
            expected_traders = set(self.trader_map.keys())
            
            if not available_traders:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Sem dados de equity para atualizar pesos")
                return
            
            # Log de traders faltantes
            if available_traders != expected_traders:
                missing = expected_traders - available_traders
                extra = available_traders - expected_traders
                if missing:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Traders sem dados: {missing}")
                if extra:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Dados extras ignorados: {extra}")
            
            # Calcula novos pesos apenas para traders com dados
            new_weights = self.optimizer.calculate_weights(historical_equity_curves)
            
            if new_weights:
                # Valida pesos retornados pelo optimizer
                if not all(0 <= w <= 1 for w in new_weights.values()):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Optimizer retornou pesos inválidos, mantendo anteriores")
                    return
                
                # Atualiza apenas os pesos dos traders com dados
                for trader_name, weight in new_weights.items():
                    if trader_name in self.trader_map:
                        self.current_weights[trader_name] = weight
                
                # Renormaliza pesos se necessário
                total_weight = sum(self.current_weights.values())
                if not np.isclose(total_weight, 1.0, rtol=1e-5) and total_weight > 0:
                    for name in self.current_weights:
                        self.current_weights[name] /= total_weight
                
                # Calcula volatilidade e ajusta leverage se target_volatility estiver ativo
                if self.target_volatility is not None:
                    self.realized_volatility = self._calculate_portfolio_volatility(historical_equity_curves)
                    old_leverage = self.current_leverage
                    self.current_leverage = self._calculate_leverage_factor(self.realized_volatility)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Volatilidade e Alavancagem:")
                    print(f"   - Volatilidade realizada: {self.realized_volatility:.1%}")
                    print(f"   - Volatilidade alvo: {self.target_volatility:.1%}")
                    print(f"   - Alavancagem: {old_leverage:.2f}x → {self.current_leverage:.2f}x")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Pesos atualizados:")
                for name, weight in self.current_weights.items():
                    print(f"   - {name}: {weight:.4f} ({weight*100:.2f}%)")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Otimizador não retornou novos pesos")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao atualizar pesos: {e}")
            print(f"   - Mantendo pesos e alavancagem atuais")

    def allocate_capital(self) -> Dict[str, float]:
        """
        Aloca capital entre traders baseado nos pesos atuais e alavancagem.
        
        Returns:
            Dicionário com alocação de capital por trader
        """
        self.capital_allocation = {}
        
        # Capital efetivo considerando alavancagem
        effective_capital = self.total_equity * self.current_leverage
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Alocando capital:")
        print(f"   - Capital base: ${self.total_equity:,.2f}")
        if self.target_volatility is not None:
            print(f"   - Alavancagem: {self.current_leverage:.2f}x")
            print(f"   - Capital efetivo: ${effective_capital:,.2f}")
        
        for trader_name, weight in self.current_weights.items():
            allocated_amount = effective_capital * weight
            self.capital_allocation[trader_name] = allocated_amount
            
            # Atualiza capital no trader se ele tiver esse atributo
            trader_object = self.trader_map.get(trader_name)
            if trader_object and hasattr(trader_object, 'capital'):
                trader_object.capital = allocated_amount
            
            print(f"   - {trader_name}: ${allocated_amount:,.2f} ({weight*100:.2f}%)")
        
        return self.capital_allocation

    def get_portfolio_status(self) -> Dict:
        """
        Retorna status atual do portfólio incluindo informações de volatilidade.
        
        Returns:
            Dicionário com informações completas do portfólio
        """
        status = {
            'total_equity': self.total_equity,
            'num_traders': len(self.trader_map),
            'traders': list(self.trader_map.keys()),
            'current_weights': self.current_weights.copy(),
            'capital_allocation': self.capital_allocation.copy(),
            'optimizer': str(self.optimizer),
            'risk_management': {
                'target_volatility': self.target_volatility,
                'realized_volatility': self.realized_volatility,
                'current_leverage': self.current_leverage,
                'max_leverage': self.max_leverage,
                'effective_capital': self.total_equity * self.current_leverage
            }
        }
        return status

    def set_target_volatility(self, target_vol: Optional[float]):
        """
        Atualiza a volatilidade alvo dinamicamente.
        
        Args:
            target_vol: Nova volatilidade alvo (None para desativar)
        """
        old_target = self.target_volatility
        self.target_volatility = target_vol
        
        # Recalcula leverage se temos dados históricos
        if self.historical_equity_curves is not None and self.target_volatility is not None:
            self.realized_volatility = self._calculate_portfolio_volatility(self.historical_equity_curves)
            self.current_leverage = self._calculate_leverage_factor(self.realized_volatility)
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Target volatility atualizado:")
        print(f"   - Anterior: {f'{old_target:.1%}' if old_target else 'Desativado'}")
        print(f"   - Novo: {f'{target_vol:.1%}' if target_vol else 'Desativado'}")
        if self.target_volatility:
            print(f"   - Nova alavancagem: {self.current_leverage:.2f}x")

    def rebalance_weights(self, target_weights: Dict[str, float]):
        """
        Rebalanceia manualmente os pesos do portfólio.
        
        Args:
            target_weights: Novos pesos desejados
        """
        # Valida e normaliza novos pesos
        total = sum(target_weights.values())
        if not np.isclose(total, 1.0, rtol=1e-5):
            target_weights = {k: v/total for k, v in target_weights.items()}
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pesos normalizados automaticamente")
        
        if set(target_weights.keys()) != set(self.trader_map.keys()):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] AVISO: Ajustando traders nos novos pesos")
            # Adiciona traders faltantes com peso zero
            for trader in self.trader_map.keys():
                if trader not in target_weights:
                    target_weights[trader] = 0.0
            # Remove traders extras
            target_weights = {k: v for k, v in target_weights.items() if k in self.trader_map}
        
        self.current_weights = target_weights
        
        # Recalcula volatilidade e leverage se aplicável
        if self.target_volatility is not None and self.historical_equity_curves is not None:
            self.realized_volatility = self._calculate_portfolio_volatility(self.historical_equity_curves)
            self.current_leverage = self._calculate_leverage_factor(self.realized_volatility)
        
        self.allocate_capital()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Pesos rebalanceados manualmente")