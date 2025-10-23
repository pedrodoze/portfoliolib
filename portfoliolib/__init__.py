# portfoliolib/__init__.py

# Torna as classes principais facilmente acessíveis ao importar o pacote
from .optimizers import BaseOptimizer, EqualWeightOptimizer, SharpeOptimizer
from .manager import PortfolioManager
from .backtester import PortfolioBacktester, WeightToOrderAdapter
from .agent import PortfolioAgent

print("Pacote portfoliolib carregado.")