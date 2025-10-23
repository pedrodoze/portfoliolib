import mt5se as se
import pandas as pd
from datetime import datetime, timedelta
import time
import schedule
import json
import math
from .manager import PortfolioManager
from typing import Optional

class PortfolioAgent:
    """
    Motor de execução para operação de portfólio ao vivo.
    """
    def __init__(self, 
                 manager: PortfolioManager,
                 prestart_dt: datetime,
                 lookback_period: pd.DateOffset,
                 rebalance_frequency: str = 'D',  # 'D', 'W', 'M', 'Q', 'Y', '1H', '30T'
                 trade_interval_seconds: int = 60,
                 state_file: str = "portfolio_state.json"):
        
        self.manager = manager
        self.prestart_dt = prestart_dt
        self.lookback_period = lookback_period
        self.rebalance_frequency = rebalance_frequency
        self.trade_interval = trade_interval_seconds
        self.state_file = state_file
        self.all_assets = self._get_all_assets()
        self.last_rebalance_time = None
        self.trader_frequencies = {}
        self.trader_magic_numbers = {}  # Mapeia trader_name → magic number único
        
        # Atribui magic number único para cada trader
        for idx, (trader_name, trader) in enumerate(self.manager.trader_map.items()):
            self.trader_frequencies[trader_name] = getattr(trader, 'frequency', se.DAILY)
            # Magic number único: 10000 + índice do trader
            self.trader_magic_numbers[trader_name] = 10000 + idx
        
        # CORREÇÃO: Adiciona flag para controlar execução de estratégias
        self.enable_strategy_trading = False  # Desabilita trading de estratégias por padrão
        self.min_rebalance_interval = timedelta(minutes=5)  # Intervalo mínimo entre rebalances
        
    def _get_all_assets(self):
        """Extrai todos os ativos únicos de todos os traders."""
        all_assets = set()
        for trader in self.manager.traders:
            if hasattr(trader, 'assets_universe'):
                all_assets.update(trader.assets_universe)
            elif hasattr(trader, 'assets'):
                all_assets.update(trader.assets)
        return list(all_assets)
    
    def _get_trader_positions(self, trader_name):
        """
        Obtém posições específicas de um trader baseado em seu magic number.
        
        Returns:
            dict: {asset: {'shares': float, 'price': float, 'value': float}}
        """
        import MetaTrader5 as mt5
        
        magic = self.trader_magic_numbers.get(trader_name)
        if magic is None:
            return {}
        
        # Obtém todas as posições com este magic number
        all_positions = mt5.positions_get()
        if not all_positions:
            return {}
        
        # Filtra por magic number e agrega por símbolo
        trader_positions = {}
        
        for pos in all_positions:
            if pos.magic == magic:
                symbol = pos.symbol
                
                if symbol not in trader_positions:
                    trader_positions[symbol] = {
                        'shares': 0.0,
                        'price': pos.price_current,
                        'value': 0.0
                    }
                
                # Agrega posições (BUY = +, SELL = -)
                if pos.type == 0:  # BUY
                    trader_positions[symbol]['shares'] += pos.volume
                else:  # SELL
                    trader_positions[symbol]['shares'] -= pos.volume
                
                # Atualiza preço e valor
                trader_positions[symbol]['price'] = pos.price_current
        
        # Calcula valores finais
        for symbol in trader_positions:
            shares = trader_positions[symbol]['shares']
            price = trader_positions[symbol]['price']
            trader_positions[symbol]['value'] = shares * price
        
        return trader_positions
    
    def _close_all_positions(self):
        """Fecha todas as posições existentes no MT5 para começar com cash puro."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando posições existentes no MT5...")
        
        # CRÍTICO: Garante que estamos em modo LIVE, não backtest
        se.inbacktest = False
        se.bts = None
        print(f"   - Modo LIVE ativado (inbacktest={se.inbacktest})")
        
        closed_count = 0
        failed_count = 0
        total_value_closed = 0.0
        
        try:
            # Obtém todos os símbolos com posições
            import MetaTrader5 as mt5
            all_positions = mt5.positions_get()
            
            if not all_positions:
                print(f"   - Nenhuma posição encontrada")
                print(f"   - Conta já está 100% em cash\n")
                return True
            
            # Identifica símbolos únicos (de TODAS as posições, não só self.all_assets)
            symbols_with_positions = set()
            for pos in all_positions:
                symbols_with_positions.add(pos.symbol)
            
            print(f"   - Encontrados {len(symbols_with_positions)} ativos com posições ({len(all_positions)} tickets)")
            
            if len(all_positions) > 20:
                print(f"   ⚠️ AVISO: Muitas posições abertas ({len(all_positions)})!")
                print(f"   - Isso pode indicar posições de testes anteriores não fechadas")
            
            # Fecha CADA position ticket individualmente (não apenas net)
            print(f"   - Fechando {len(all_positions)} position tickets individuais...")
            
            for i, pos in enumerate(all_positions, 1):
                try:
                    symbol = pos.symbol
                    volume = pos.volume
                    ticket = pos.ticket
                    magic = pos.magic
                    
                    # Determina tipo de fechamento (oposto da posição)
                    if pos.type == 0:  # BUY position
                        close_type = mt5.ORDER_TYPE_SELL
                        tick = mt5.symbol_info_tick(symbol)
                        price = tick.bid if tick else 0
                    else:  # SELL position
                        close_type = mt5.ORDER_TYPE_BUY
                        tick = mt5.symbol_info_tick(symbol)
                        price = tick.ask if tick else 0
                    
                    if price <= 0:
                        print(f"     {i:3d}. {symbol}: ❌ Sem preço")
                        failed_count += 1
                        continue
                    
                    # Tenta diferentes filling modes
                    closed_this = False
                    for filling in [mt5.ORDER_FILLING_RETURN, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK]:
                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": volume,
                            "type": close_type,
                            "position": ticket,  # Fecha este ticket específico
                            "price": price,
                            "deviation": 20,
                            "magic": 0,
                            "comment": "Cleanup all",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": filling,
                        }
                        
                        result = mt5.order_send(request)
                        
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            if i <= 10 or i % 20 == 0:  # Log primeiros 10 e depois a cada 20
                                print(f"     {i:3d}. {symbol} ticket={ticket} ✅")
                            closed_count += 1
                            total_value_closed += volume * price
                            closed_this = True
                            break
                        elif result.retcode != 10030:  # Not unsupported filling
                            break
                    
                    if not closed_this:
                        if i <= 10:
                            print(f"     {i:3d}. {symbol} ticket={ticket} ❌ Falhou")
                        failed_count += 1
                    
                    if i % 10 == 0:
                        time.sleep(0.5)  # Pausa a cada 10
                    
                except Exception as e:
                    print(f"     {i:3d}. Erro: {e}")
                    failed_count += 1
            
            # Resumo
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Resumo do cleanup:")
            print(f"   - Posições fechadas: {closed_count}")
            print(f"   - Falhas: {failed_count}")
            print(f"   - Valor convertido em cash: ${total_value_closed:,.2f}")
            
            # Aguarda execução
            if closed_count > 0:
                print(f"   - Aguardando execução das ordens...")
                time.sleep(2)
            
            # Verifica resultado final
            print(f"\n   - Verificação final:")
            all_closed = True
            for symbol in sorted(symbols_with_positions):
                net_after = se.get_shares(symbol)
                if abs(net_after) >= 0.01:
                    print(f"     ⚠️ {symbol}: {net_after:+.1f} (ainda aberto)")
                    all_closed = False
                else:
                    print(f"     ✅ {symbol}: 0.0 (fechado)")
            
            if all_closed:
                print(f"\n   ✅ Conta agora está 100% em cash\n")
            else:
                print(f"\n   ⚠️ Algumas posições podem ainda existir - verifique MT5 terminal\n")
                
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao fechar posições: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _save_state(self):
        """Salva o estado atual do portfólio."""
        try:
            estado = {
                "weights": self.manager.current_weights,
                "last_rebalance": self.last_rebalance_time.isoformat() if self.last_rebalance_time else None,
                "total_equity": self.manager.total_equity,
                "current_leverage": getattr(self.manager, 'current_leverage', 1.0),
                "realized_volatility": getattr(self.manager, 'realized_volatility', None)
            }
            with open(self.state_file, 'w') as f:
                json.dump(estado, f, indent=4)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao salvar estado: {e}")

    def _load_state(self):
        """Carrega o estado do portfólio."""
        try:
            with open(self.state_file, 'r') as f:
                estado = json.load(f)
                self.manager.current_weights = estado.get("weights", self.manager.current_weights)
                self.manager.total_equity = estado.get("total_equity", self.manager.total_equity)
                last_rebalance_str = estado.get("last_rebalance")
                if last_rebalance_str:
                    self.last_rebalance_time = datetime.fromisoformat(last_rebalance_str)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Estado carregado de {self.state_file}.")
        except FileNotFoundError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Arquivo de estado não encontrado, usando configuração inicial.")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao carregar estado: {e}")
        
        # Atualiza equity da conta
        self._update_equity_from_account()

    def _update_equity_from_account(self):
        """Atualiza o equity total a partir da conta."""
        try:
            acc_info = se.account_info()
            if acc_info is not None:
                if hasattr(acc_info, 'equity'):
                    self.manager.total_equity = float(acc_info.equity)
                elif hasattr(acc_info, '_asdict'):
                    info_dict = acc_info._asdict()
                    self.manager.total_equity = float(info_dict.get('equity', self.manager.total_equity))
                self.manager.allocate_capital()
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro ao obter informações da conta: {e}")

    def _should_rebalance(self, current_time: datetime) -> bool:
        """Verifica se deve rebalancear baseado na frequência."""
        if self.last_rebalance_time is None:
            return True
        
        # CORREÇÃO: Adiciona intervalo mínimo para evitar rebalances muito frequentes
        if current_time < self.last_rebalance_time + self.min_rebalance_interval:
            return False
        
        # Converte frequência em timedelta aproximado
        freq_map = {
            'T': timedelta(minutes=1),
            'min': timedelta(minutes=1),
            '5T': timedelta(minutes=5),
            '5min': timedelta(minutes=5),
            '10T': timedelta(minutes=10),
            '10min': timedelta(minutes=10),
            '15T': timedelta(minutes=15),
            '15min': timedelta(minutes=15),
            '30T': timedelta(minutes=30),
            '30min': timedelta(minutes=30),
            'H': timedelta(hours=1),
            '2H': timedelta(hours=2),
            '4H': timedelta(hours=4),
            'D': timedelta(days=1),
            'W': timedelta(weeks=1),
            'M': timedelta(days=30),
            'Q': timedelta(days=90),
            'Y': timedelta(days=365)
        }
        
        if self.rebalance_frequency in freq_map:
            delta = freq_map[self.rebalance_frequency]
            return current_time >= self.last_rebalance_time + delta
        
        # Se não reconhecer a frequência, usa pandas
        try:
            next_rebalance = pd.date_range(
                start=self.last_rebalance_time,
                periods=2,
                freq=self.rebalance_frequency
            )[1]
            return current_time >= next_rebalance
        except:
            return False

    def _execute_traders(self):
        """
        Executa traders e ajusta posições baseado nas alocações retornadas.
        
        Fluxo:
        1. Cada trader retorna seus pesos desejados (dict com weights)
        2. Agent calcula targets em valor absoluto ($)
        3. Agent agrega targets de todos os traders
        4. Agent ajusta posições do portfolio para match targets
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Executando traders e ajustando posições...")
        
        try:
            # Garante modo LIVE
            se.inbacktest = False
            
            # Atualiza equity
            self._update_equity_from_account()
            
            # Aloca capital entre traders
            capital_allocations = self.manager.allocate_capital()
            
            print(f"   - Equity total da conta: ${self.manager.total_equity:,.2f}")
            
            # PASSO 1: Coleta alocações desejadas de cada trader
            print(f"\n   PASSO 1: Coletando alocações desejadas dos traders")
            print(f"   " + "-" * 65)
            
            # Obtém dados de mercado
            dbars = se.get_multi_bars(self.all_assets, 100, type=se.DAILY)
            
            # Executa cada trader individualmente (não agrega)
            for trader_name, allocated_capital in capital_allocations.items():
                trader = self.manager.trader_map[trader_name]
                
                if allocated_capital <= 0:
                    print(f"   - {trader_name}: Sem capital alocado, pulando")
                    continue
                
                # Obtém lista de ativos
                trader_assets = []
                if hasattr(trader, 'assets_universe'):
                    trader_assets = trader.assets_universe
                elif hasattr(trader, 'assets'):
                    trader_assets = trader.assets
                
                if not trader_assets:
                    print(f"   - {trader_name}: Sem ativos definidos")
                    continue
                
                # Filtra dbars para este trader
                trader_dbars = {asset: dbars[asset] for asset in trader_assets if asset in dbars}
                
                # NOVO: Obtém posições específicas deste trader (via magic number)
                my_positions = self._get_trader_positions(trader_name)
                
                # Chama trader.trade() para obter pesos desejados
                # Passa my_positions como parâmetro opcional
                try:
                    # Tenta chamar com my_positions primeiro
                    import inspect
                    sig = inspect.signature(trader.trade)
                    if 'my_positions' in sig.parameters or len(sig.parameters) > 1:
                        allocation = trader.trade(trader_dbars, my_positions=my_positions)
                    else:
                        allocation = trader.trade(trader_dbars)
                    
                    # Se retornar None ou lista vazia, assume cash 100%
                    if allocation is None or (isinstance(allocation, list) and len(allocation) == 0):
                        allocation = {'cash': 1.0}
                    
                    # Valida que é um dict
                    if not isinstance(allocation, dict):
                        print(f"   - {trader_name}: ⚠️ Retornou formato inválido (esperado dict), usando cash 100%")
                        allocation = {'cash': 1.0}
                    
                    # Normaliza pesos se não somam 1.0
                    total_weight = sum(w for k, w in allocation.items() if k != 'cash')
                    cash_weight = allocation.get('cash', 0.0)
                    
                    if abs(total_weight + cash_weight - 1.0) > 0.01:
                        print(f"   - {trader_name}: ⚠️ Pesos não somam 1.0, normalizando")
                        if total_weight + cash_weight > 0:
                            factor = 1.0 / (total_weight + cash_weight)
                            allocation = {k: v * factor for k, v in allocation.items()}
                    
                    print(f"   - {trader_name} (capital: ${allocated_capital:,.2f}, magic: {self.trader_magic_numbers[trader_name]}):")
                    
                    # Converte pesos em valores absolutos
                    trader_targets = {}
                    for asset, weight in allocation.items():
                        if asset == 'cash':
                            cash_amount = allocated_capital * weight
                            print(f"     - Cash: {weight*100:.1f}% (${cash_amount:,.2f})")
                            continue
                        
                        target_value = allocated_capital * weight
                        trader_targets[asset] = target_value
                        print(f"     - {asset}: {weight*100:.1f}% (${target_value:,.2f})")
                    
                    # Ajusta posições DESTE trader especificamente
                    if trader_targets:
                        self._adjust_trader_positions(trader_name, trader_targets)
                        
                except Exception as e:
                    print(f"   - {trader_name}: ❌ Erro ao executar trade(): {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                        
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro na execução: {e}")
            import traceback
            traceback.print_exc()
    
    def _adjust_trader_positions(self, trader_name, targets):
        """
        Ajusta posições de um trader específico para match seus targets.
        Usa magic number para identificar posições deste trader.
        
        Args:
            trader_name: Nome do trader
            targets: {asset: target_value_in_dollars}
        """
        if not targets:
            return
        
        magic = self.trader_magic_numbers[trader_name]
        
        # Ajusta cada ativo deste trader
        for asset, target_value in targets.items():
            try:
                # Obtém posição ATUAL deste trader (via magic number)
                trader_pos = self._get_trader_positions(trader_name)
                current_shares = trader_pos.get(asset, {}).get('shares', 0.0)
                
                # Obtém preço atual
                bars = se.get_bars(asset, 2)
                if bars is None or bars.empty:
                    print(f"       {asset}: ❌ Sem dados de preço")
                    continue
                
                price = se.get_last(bars)
                if price <= 0:
                    print(f"       {asset}: ❌ Preço inválido: {price}")
                    continue
                
                # Calcula valor atual
                current_value = current_shares * price
                
                # Calcula diferença
                value_diff = target_value - current_value
                shares_diff = value_diff / price
                
                # Step size
                step = se.get_volume_step(asset)
                if step <= 0:
                    step = 1.0
                
                # Arredonda para step
                shares_diff = math.floor(shares_diff / step) * step
                
                # Tolerância
                min_trade = step * 2
                if abs(shares_diff) < min_trade:
                    print(f"       {asset}: ✅ OK (atual: ${current_value:,.2f}, alvo: ${target_value:,.2f})")
                    continue
                
                # Executa ordem COM MAGIC NUMBER deste trader
                if shares_diff > 0:
                    order = se.buyOrder(asset, shares_diff)
                    action = "COMPRA"
                else:
                    order = se.sellOrder(asset, abs(shares_diff))
                    action = "VENDA"
                
                if order:
                    # CRUCIAL: Define magic number do trader
                    order['magic'] = magic
                    
                    if se.checkOrder(order):
                        if se.sendOrder(order):
                            print(f"       {asset}: ✅ {action} {abs(shares_diff):.1f} shares @ ${price:.2f} (${abs(shares_diff) * price:,.2f}) [magic={magic}]")
                        else:
                            print(f"       {asset}: ❌ Falha ao enviar ordem")
                    else:
                        print(f"       {asset}: ❌ Ordem inválida")
                else:
                    print(f"       {asset}: ❌ Falha ao criar ordem")
                    
            except Exception as e:
                print(f"       {asset}: ❌ Erro: {e}")
                        
    def _rebalance(self):
        """Rotina de rebalanceamento."""
        current_time = datetime.now()
        
        if not self._should_rebalance(current_time):
            return
        
        print(f"\n[{current_time.strftime('%H:%M:%S')}] === INICIANDO REBALANCEAMENTO ===")
        
        try:
            # Define período de lookback
            lookback_end = current_time
            
            # Converte lookback_period para timedelta se for DateOffset
            if hasattr(self.lookback_period, 'delta'):
                lookback_delta = self.lookback_period.delta
            else:
                # Para DateOffset(minutes=10), converte manualmente
                try:
                    lookback_delta = pd.Timestamp(lookback_end) - (pd.Timestamp(lookback_end) - self.lookback_period)
                    lookback_start = lookback_end - lookback_delta
                except:
                    # Fallback: usa o método original
                    lookback_start = (pd.Timestamp(lookback_end) - self.lookback_period).to_pydatetime()
            
            prestart_date = self.prestart_dt
            
            print(f"   - Lookback: {lookback_start.date()} a {lookback_end.date()}")
            print(f"   - Prestart: {prestart_date.date()}")
            
            # Coleta dados históricos para cada trader
            lookback_curves = pd.DataFrame()
            successful_backtests = 0
            
            for trader_name, trader in self.manager.trader_map.items():
                # Obtém lista de ativos
                assets_list = []
                if hasattr(trader, 'assets_universe'):
                    assets_list = trader.assets_universe
                elif hasattr(trader, 'assets'):
                    assets_list = trader.assets
                    
                if not assets_list:
                    continue
                
                # Define período do backtest
                period = getattr(trader, 'frequency', se.DAILY)
                
                try:
                    # Configura e roda backtest
                    bts = se.backtest.set(
                        assets=assets_list,
                        prestart=prestart_date,
                        start=lookback_start,
                        end=lookback_end,
                        period=period,
                        capital=100000.0,
                        file=f'temp_backtest_{trader_name}',
                        verbose=False
                    )
                    
                    if bts is None:
                        continue
                    
                    # Executa backtest usando adapter para suportar weights
                    print(f"   - Executando backtest para {trader_name}...")
                    from .backtester import WeightToOrderAdapter
                    adapted_trader = WeightToOrderAdapter(trader, allocated_capital=100000.0)
                    results = se.backtest.run(adapted_trader, bts)
                    
                    if results is not None and not results.empty:
                        results['date'] = pd.to_datetime(results['date'])
                        lookback_curves[trader_name] = results.set_index('date')['equity']
                        successful_backtests += 1
                        print(f"     - {trader_name}: {len(results)} pontos coletados")
                    else:
                        print(f"     - {trader_name}: Backtest retornou dados vazios")
                        
                except Exception as e:
                    print(f"   - Erro no backtest de {trader_name}: {e}")
                    continue

            # CRÍTICO: Desativa modo backtest e volta para modo LIVE
            print(f"   - Desativando modo backtest e voltando para modo LIVE...")
            se.inbacktest = False  # CRUCIAL: Volta para modo live trading
            se.bts = None  # Limpa configuração de backtest
            time.sleep(0.5)  # Pequena pausa para garantir mudança de estado

            # CORREÇÃO: Só rebalanceia se tiver dados suficientes
            if successful_backtests >= 2 and not lookback_curves.empty:
                print(f"   - Atualizando pesos com {len(lookback_curves.columns)} traders")
                self.manager.update_weights(lookback_curves)
                
                # Executa traders e ajusta posições
                self._execute_traders()
                
                # Salva estado
                self.last_rebalance_time = current_time
                self._save_state()
                
                print(f"[{current_time.strftime('%H:%M:%S')}] === REBALANCEAMENTO CONCLUÍDO ===\n")
            else:
                print(f"   - AVISO: Dados insuficientes para rebalanceamento ({successful_backtests} backtests válidos)")
                print(f"[{current_time.strftime('%H:%M:%S')}] === REBALANCEAMENTO CANCELADO ===\n")
            
        except Exception as e:
            print(f"[{current_time.strftime('%H:%M:%S')}] Erro no rebalanceamento: {e}")

    def _trade_cycle(self):
        """Executa um ciclo de trading - VERSÃO CORRIGIDA."""
        try:
            # Verifica se mercado está aberto
            if not self.all_assets or not se.is_market_open(self.all_assets[0]):
                return
            
            # CORREÇÃO: Só executa rebalanceamento, não trading de estratégias
            self._rebalance()
            
            # NOVA ARQUITETURA: Trading de estratégias usando weights
            if self.enable_strategy_trading:
                # Executa traders (eles retornam weights, agent ajusta posições)
                self._execute_traders()
                        
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro no ciclo de trading: {e}")

    def run(self):
        """Loop principal de execução."""
        # Conecta ao MT5
        if not se.connect():
            print("Erro ao conectar ao MetaTrader 5")
            return
        
        print("=" * 60)
        print("PortfolioAgent INICIADO (VERSÃO CORRIGIDA)")
        print(f"Rebalanceamento: frequência {self.rebalance_frequency}")
        print(f"Trading: a cada {self.trade_interval} segundos")
        print(f"Ativos: {len(self.all_assets)}")
        print(f"Trading de estratégias: {'HABILITADO' if self.enable_strategy_trading else 'DESABILITADO'}")
        print("Pressione Ctrl+C para parar")
        print("=" * 60)
        
        # PASSO 1: Fecha todas as posições existentes (clean slate)
        print("\n>>> PASSO 1: LIMPEZA INICIAL <<<")
        if not self._close_all_positions():
            print("⚠️ Aviso: Falha ao fechar posições, continuando mesmo assim...")
        
        # Carrega estado
        self._load_state()
        
        # Execução inicial dos traders (usa pesos iniciais se fornecidos)
        print("\n>>> PASSO 2: EXECUÇÃO INICIAL DOS TRADERS <<<")
        print(f"   - Usando pesos iniciais: {self.manager.current_weights}")
        self._execute_traders()
        
        # Marca como se já tivesse feito rebalanceamento
        self.last_rebalance_time = datetime.now()
        
        # Loop principal
        last_trade_time = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Executa ciclo de trading
                if current_time - last_trade_time >= self.trade_interval:
                    self._trade_cycle()
                    last_trade_time = current_time
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n" + "=" * 60)
                print("Encerrando o agente...")
                print("=" * 60)
                break
            except Exception as e:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Erro: {e}")
                time.sleep(30)