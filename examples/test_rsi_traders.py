"""
Test RSI-based traders with Sharpe optimization

Two RSI traders:
- Aggressive: Buy if RSI > 70, Close if RSI < 30
- Conservative: Buy if RSI > 60, Close if RSI < 40
"""
import mt5se as se
from datetime import datetime
import pandas as pd
from portfoliolib import PortfolioManager, PortfolioAgent, SharpeOptimizer

def calculate_rsi(bars, period=14):
    """Calculate RSI from bars"""
    if bars is None or len(bars) < period + 1:
        return 50.0  # Neutral if not enough data
    
    closes = bars['close'].values
    deltas = pd.Series(closes).diff()
    
    gain = deltas.clip(lower=0).rolling(window=period).mean()
    loss = -deltas.clip(upper=0).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0


class RSIAggressiveTrader(se.Trader):
    """Aggressive RSI Trader: Buy RSI > 70, Close RSI < 30"""
    def __init__(self, name, asset):
        super().__init__()
        self.name = name
        self.assets_universe = [asset]
        self.frequency = se.INTRADAY
        self.asset = asset
    
    def trade(self, dbars, my_positions=None):
        """
        Returns weights based on RSI and current position.
        
        Args:
            dbars: Market data
            my_positions: {'NVDA': {'shares': 226, 'price': 182, 'value': 41000}} or {}
        """
        if self.asset not in dbars:
            return {'cash': 1.0}
        
        # DEBUG: Check how many bars we have
        bars = dbars[self.asset]
        if bars is None or len(bars) < 15:
            # Not enough data for RSI, stay in cash
            print(f"[{self.name}] Insufficient bars ({len(bars) if bars is not None else 0}), staying in cash")
            return {'cash': 1.0}
        
        # Calculate RSI
        rsi = calculate_rsi(bars)
        
        # Check if we have position
        has_position = my_positions and self.asset in my_positions and my_positions[self.asset]['shares'] > 0
        
        # print(f"      [{self.name}] RSI={rsi:.1f}, Position={'YES' if has_position else 'NO'}")
        
        # Trading logic
        if has_position:
            if rsi < 40:
                # print(f"      → CLOSE (RSI < 30)")
                return {'cash': 1.0}  # Close position
            else:
                # Position size based on RSI: 0.85 * (RSI/100)
                position_size = 0.85 * (rsi / 100.0)
                position_size = min(position_size, 0.85)  # Cap at 85%
                cash_size = 1.0 - position_size
                # print(f"      → HOLD (position size: {position_size*100:.1f}%)")
                return {self.asset: position_size, 'cash': cash_size}
        else:
            if rsi > 55:
                # Position size based on RSI: 0.85 * (RSI/100)
                position_size = 0.85 * (rsi / 100.0)
                position_size = min(position_size, 0.85)  # Cap at 85%
                cash_size = 1.0 - position_size
                # print(f"      → OPEN (RSI > 70, position size: {position_size*100:.1f}%)")
                return {self.asset: position_size, 'cash': cash_size}
            else:
                # print(f"      → WAIT (no signal)")
                return {'cash': 1.0}  # Stay in cash


class RSIConservativeTrader(se.Trader):
    """Conservative RSI Trader: Buy RSI > 60, Close RSI < 40"""
    def __init__(self, name, asset):
        super().__init__()
        self.name = name
        self.assets_universe = [asset]
        self.frequency = se.INTRADAY
        self.asset = asset
    
    def trade(self, dbars, my_positions=None):
        """
        Returns weights based on RSI and current position.
        
        Args:
            dbars: Market data
            my_positions: {'MSFT': {'shares': 79, 'price': 515, 'value': 40685}} or {}
        """
        if self.asset not in dbars:
            return {'cash': 1.0}
        
        # DEBUG: Check how many bars we have
        bars = dbars[self.asset]
        if bars is None or len(bars) < 15:
            # Not enough data for RSI, stay in cash
            print(f"[{self.name}] Insufficient bars ({len(bars) if bars is not None else 0}), staying in cash")
            return {'cash': 1.0}
        
        # Calculate RSI
        rsi = calculate_rsi(bars)
        
        # Check if we have position
        has_position = my_positions and self.asset in my_positions and my_positions[self.asset]['shares'] > 0
        
        # print(f"      [{self.name}] RSI={rsi:.1f}, Position={'YES' if has_position else 'NO'}")
        
        # Trading logic
        if has_position:
            if rsi < 45:
                # print(f"      → CLOSE (RSI < 40)")
                return {'cash': 1.0}  # Close position
            else:
                # Position size based on RSI: 0.85 * (RSI/100)
                position_size = 0.85 * (rsi / 100.0)
                position_size = min(position_size, 0.85)  # Cap at 85%
                cash_size = 1.0 - position_size
                # print(f"      → HOLD (position size: {position_size*100:.1f}%)")
                return {self.asset: position_size, 'cash': cash_size}
        else:
            if rsi > 50:
                # Position size based on RSI: 0.85 * (RSI/100)
                position_size = 0.85 * (rsi / 100.0)
                position_size = min(position_size, 0.85)  # Cap at 85%
                cash_size = 1.0 - position_size
                # print(f"      → OPEN (RSI > 60, position size: {position_size*100:.1f}%)")
                return {self.asset: position_size, 'cash': cash_size}
            else:
                # print(f"      → WAIT (no signal)")
                return {'cash': 1.0}  # Stay in cash


def main():
    print("=" * 70)
    print("TEST: RSI Traders com Sharpe Optimization")
    print("=" * 70)
    
    if not se.connect():
        print("[ERRO] Falha ao conectar ao MetaTrader 5")
        return
    
    # Create RSI traders - BOTH trading NVDA to test per-trader tracking
    trader_aggressive = RSIAggressiveTrader(name="RSI_Aggressive", asset="NVDA")
    trader_conservative = RSIConservativeTrader(name="RSI_Conservative", asset="NVDA")
    
    # Initial weights (equal)
    initial_weights = {
        "RSI_Aggressive": 0.5,
        "RSI_Conservative": 0.5
    }
    
    # Create manager with Sharpe optimizer
    manager = PortfolioManager(
        traders=[trader_aggressive, trader_conservative],
        optimizer=SharpeOptimizer(risk_free_rate=0.02),  # 2% risk-free rate
        initial_equity=100000.0,
        initial_weights=initial_weights,
        max_leverage=1.0,
        target_volatility=None
    )
    
    # Configure agent
    agent = PortfolioAgent(
        manager=manager,
        prestart_dt=se.date(2023, 1, 1),
        lookback_period=pd.DateOffset(minutes=60),  # 10 minutes lookback
        rebalance_frequency='5T',  # Rebalance every 60 minutes
        trade_interval_seconds=10,  # Trade every 10 seconds
        state_file="test_rsi_state.json"
    )
    
    agent.enable_strategy_trading = True
    
    print("\n[OK] Configuração RSI Traders:")
    print(f"   - Aggressive (NVDA): Buy RSI>70, Close RSI<30, Magic=10000")
    print(f"   - Conservative (NVDA): Buy RSI>60, Close RSI<40, Magic=10001")
    print(f"   - AMBOS traders operam NVDA (testa tracking independente)")
    print(f"   - Lookback: 10 minutos")
    print(f"   - Rebalanceamento: a cada 10 minutos")
    print(f"   - Trading: a cada 10 segundos")
    print(f"   - Position size: 0.85 * (RSI/100), capped at 85%\n")
    print(f"   EXEMPLO:")
    print(f"      RSI=70 → 59.5% position")
    print(f"      RSI=80 → 68.0% position")
    print(f"      RSI=100 → 85.0% position (max)\n")
    
    # Run
    agent.run()

if __name__ == "__main__":
    main()

