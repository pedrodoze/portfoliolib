# portfoliolib/optimizers.py

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import scipy.optimize as sco
from typing import Dict

class BaseOptimizer(ABC):
    """Classe base abstrata para todas as estratégias de otimização de portfólio."""

    @abstractmethod
    def calculate_weights(self, historical_prices: pd.DataFrame) -> Dict[str, float]:
        """Calcula os pesos ótimos para os ativos no portfólio."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

class EqualWeightOptimizer(BaseOptimizer):
    """Atribui um peso igual a cada ativo no portfólio."""

    def calculate_weights(self, historical_prices: pd.DataFrame) -> Dict[str, float]:
        num_assets = len(historical_prices.columns)
        if num_assets == 0:
            return {}
        equal_weight = 1.0 / num_assets
        return {ticker: equal_weight for ticker in historical_prices.columns}

class SharpeOptimizer(BaseOptimizer):
    """Calcula os pesos do portfólio que maximizam o Índice de Sharpe."""

    def __init__(self, risk_free_rate: float = 0.0):
        self.risk_free_rate = risk_free_rate

    def _calculate_portfolio_performance(self, weights, mean_returns, cov_matrix):
        portfolio_return = np.sum(mean_returns * weights) * 252
        portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(252)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std_dev
        return portfolio_return, portfolio_std_dev, sharpe_ratio

    def _negative_sharpe_ratio(self, weights, mean_returns, cov_matrix):
        return -self._calculate_portfolio_performance(weights, mean_returns, cov_matrix)[2]
    
    def calculate_weights(self, historical_prices: pd.DataFrame) -> Dict[str, float]:
        returns = historical_prices.pct_change().dropna()
        if returns.empty or len(returns.columns) == 0:
            return {}
        
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        num_assets = len(returns.columns)
        
        args = (mean_returns, cov_matrix)
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets,]
        
        result = sco.minimize(self._negative_sharpe_ratio, initial_guess, args=args,
                              method='SLSQP', bounds=bounds, constraints=constraints)
        
        return dict(zip(returns.columns, result.x))