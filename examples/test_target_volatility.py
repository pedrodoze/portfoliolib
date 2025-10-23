# test_target_volatility.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock simples do Trader (não precisa do MT5)
class MockTrader:
    def __init__(self, name: str):
        self.name = name

# Seus módulos (ajuste o caminho se necessário)
from portfoliolib.optimizers import EqualWeightOptimizer
from portfoliolib.manager import PortfolioManager

def create_synthetic_equity_from_end(num_days: int, annual_vol: float, end_date: pd.Timestamp, seed: int = 42) -> pd.Series:
    np.random.seed(seed)
    daily_vol = annual_vol / np.sqrt(252)
    returns = np.random.normal(0, daily_vol, num_days)
    equity = (1 + returns).cumprod()
    dates = pd.date_range(end=end_date, periods=num_days, freq='D')
    return pd.Series(equity, index=dates, name=f"Trader_{seed}")

def test_target_volatility():
    print("=== Teste: Target Volatility no PortfolioManager ===\n")
    
    # Define um end_date fixo para garantir alinhamento
    end_date = pd.Timestamp.today().normalize()  # ← data de hoje às 00:00:00
    
    traders = [MockTrader("LowVol"), MockTrader("HighVol")]
    
    # Gera curvas com o MESMO índice
    low_vol_curve = create_synthetic_equity_from_end(100, annual_vol=0.20, end_date=end_date, seed=42)
    high_vol_curve = create_synthetic_equity_from_end(100, annual_vol=0.20, end_date=end_date, seed=99)
    
    equity_curves = pd.DataFrame({
        "LowVol": low_vol_curve,
        "HighVol": high_vol_curve
    })
    
    # Agora garanta que não há NaN no início
    equity_curves = equity_curves.dropna()
    
    if equity_curves.empty:
        raise ValueError("Erro: equity_curves está vazio. Verifique a geração de dados sintéticos.")
    
    print(f"Período de dados: {equity_curves.index[0].date()} a {equity_curves.index[-1].date()}")
    print(f"Volatilidade estimada (LowVol): {equity_curves['LowVol'].pct_change().std() * np.sqrt(252):.1%}")
    print(f"Volatilidade estimada (HighVol): {equity_curves['HighVol'].pct_change().std() * np.sqrt(252):.1%}\n")

    # 3. Criar PortfolioManager com target volatility = 10%
    optimizer = EqualWeightOptimizer()
    manager = PortfolioManager(
        traders=traders,
        optimizer=optimizer,
        initial_equity=100_000,
        target_volatility=0.10,  # 10% anual
        max_leverage=3.0
    )
    
    # 4. Atualizar pesos e calcular leverage
    manager.update_weights(equity_curves)
    
    # 5. Verificar resultados
    status = manager.get_portfolio_status()
    risk = status['risk_management']
    
    print(f"Volatilidade realizada do portfólio: {risk['realized_volatility']:.1%}")
    print(f"Volatilidade alvo: {risk['target_volatility']:.1%}")
    print(f"Alavancagem aplicada: {risk['current_leverage']:.2f}x")
    print(f"Capital efetivo: ${risk['effective_capital']:,.2f}")
    
    # 6. Validar lógica
    assert risk['target_volatility'] == 0.10
    assert risk['realized_volatility'] > 0
    assert risk['current_leverage'] > 0
    assert risk['effective_capital'] == 100_000 * risk['current_leverage']
    
    # Exemplo: se vol realizada ~12.5%, leverage deve ser ~0.8x
    expected_leverage = 0.10 / risk['realized_volatility']
    expected_leverage = min(expected_leverage, 3.0)
    assert abs(risk['current_leverage'] - expected_leverage) < 0.01, "Leverage incorreto!"
    
    print("\n✅ Teste concluído com sucesso!")

if __name__ == "__main__":
    test_target_volatility()