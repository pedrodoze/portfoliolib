# Exemplo de Trading Ao Vivo - Equal Weight + Target Volatility

Este exemplo demonstra como usar a biblioteca `portfoliolib` para executar um portfólio de trading ao vivo com 3 traders igualmente ponderados, target volatility de 10% e lookback de 6 meses.

## Características do Exemplo

- **3 Traders Igualmente Ponderados**: Cada trader recebe 33.33% do capital
- **Target Volatility**: 10% anual com ajuste automático de alavancagem
- **Lookback Window**: 6 meses para cálculo de volatilidade
- **Rebalanceamento**: Diário
- **Estratégias RSI**: Cada trader usa RSI com thresholds diferentes
- **Diversificação**: Forex, Ações e Crypto
- **Trading Ao Vivo**: Integração completa com MetaTrader 5

## Arquivos Criados

### 1. `equal_weight_volatility_trader.py`
Trader customizado que:
- Distribui capital igualmente entre ativos
- Usa RSI para sinais de entrada/saída
- Gerencia risco por posição
- Suporta diferentes timeframes

### 2. `run_live_equal_weight_volatility.py`
Script principal que:
- Cria 3 traders com estratégias diferentes
- Configura PortfolioManager com target volatility
- Executa trading ao vivo
- Inclui backtest de validação

### 3. `agent.py` (Melhorado)
Agente original com melhorias implementadas:
- Gestão de frequências diferentes por trader
- Rebalancing mais robusto
- Melhor tratamento de erros
- Validação de posições
- Logging detalhado

### 4. `test_live_setup.py`
Script de teste que valida:
- Conexão com MetaTrader 5
- Disponibilidade de ativos
- Funções de trading
- Imports do portfoliolib

## Configuração dos Traders

### Trader 1: RSI Conservative
- **Ativos**: EURUSD, GBPUSD, USDJPY (Forex)
- **RSI**: Buy ≥ 65, Sell ≤ 35
- **Risk**: 3% por trade
- **Estratégia**: Mais conservadora

### Trader 2: RSI Balanced  
- **Ativos**: AAPL, MSFT, GOOGL (Tech Stocks)
- **RSI**: Buy ≥ 60, Sell ≤ 40
- **Risk**: 5% por trade
- **Estratégia**: Balanceada

### Trader 3: RSI Aggressive
- **Ativos**: BTCUSD, ETHUSD, XRPUSD (Crypto)
- **RSI**: Buy ≥ 55, Sell ≤ 45
- **Risk**: 7% por trade
- **Estratégia**: Mais agressiva

## Como Usar

### 1. Preparação
```bash
# Navegue para o diretório do projeto
cd teste02/portfoliolib_project/examples

# Ative o ambiente virtual (se necessário)
# source venv_MT5SE/Scripts/activate  # Windows
# source venv_MT5SE/bin/activate     # Linux/Mac
```

### 2. Teste a Configuração
```bash
python test_live_setup.py
```

Este script irá:
- Testar conexão com MetaTrader 5
- Verificar disponibilidade dos ativos
- Validar funções de trading
- Testar imports do portfoliolib

### 3. Execute o Trading Ao Vivo
```bash
python run_live_equal_weight_volatility.py
```

O script irá:
- Perguntar se quer executar backtest de validação primeiro
- Conectar ao MetaTrader 5
- Configurar os 3 traders
- Usar o PortfolioAgent melhorado com validação de posições
- Iniciar o trading ao vivo
- Mostrar logs detalhados

### 4. Monitoramento
Durante a execução, você verá:
- Status de conexão com MT5
- Informações da conta
- Rebalanceamentos executados
- Trades executados
- Ajustes de volatilidade e alavancagem

## Configurações Importantes

### MetaTrader 5
- Certifique-se que o MT5 está aberto
- Conta demo deve estar ativa
- Algoritmo trading deve estar habilitado
- Conexão deve estar estável

### Target Volatility
- **Alvo**: 10% anual
- **Max Leverage**: 300% (3.0x)
- **Floor**: 0.1% volatilidade mínima
- **Lookback**: 6 meses para cálculo

### Rebalanceamento
- **Frequência**: Diário
- **Lookback**: 6 meses
- **Prestart**: 7 meses (para dados suficientes)
- **Intervalo Trading**: 5 minutos

## Arquivos de Estado

O sistema salva automaticamente:
- `live_equal_weight_state.json`: Estado do portfólio
- `temp_backtest_*.csv`: Dados temporários de backtest

## Logs e Monitoramento

### Durante Rebalanceamento
```
[14:30:15] === INICIANDO REBALANCEAMENTO ===
   - Lookback: 2024-01-15 a 2024-07-15
   - Executando backtest para RSI_Conservative...
     - RSI_Conservative: 120 pontos coletados
   - Atualizando pesos com 3 traders
   - Volatilidade realizada: 8.5%
   - Alavancagem: 1.2x → 1.18x
   - Ajustando posições...
   - COMPRA: 100 de EURUSD @ $1.08500
```

### Durante Trading
```
[14:35:22] RSI_Conservative EURUSD: COMPRA - RSI=67.45, Qty=50
[14:35:23] RSI_Balanced AAPL: VENDA - RSI=38.20, Qty=10
```

## Troubleshooting

### Problemas Comuns

1. **Falha de Conexão MT5**
   - Verifique se o MT5 está aberto
   - Confirme que a conta demo está ativa
   - Teste com `test_live_setup.py`

2. **Ativos Não Disponíveis**
   - Alguns ativos podem não estar disponíveis na conta
   - O script irá pular ativos indisponíveis
   - Verifique com `test_live_setup.py`

3. **Erro de Rebalanceamento**
   - Dados insuficientes no período de lookback
   - Aumente o período de prestart
   - Verifique conectividade com dados históricos

4. **Orders Falhando**
   - Verifique se algoritmo trading está habilitado
   - Confirme que tem saldo suficiente
   - Verifique horários de mercado

### Logs de Debug
Para mais detalhes, verifique:
- Console output para logs detalhados
- Arquivo de estado JSON
- Logs do MetaTrader 5

## Personalização

### Alterar Ativos
Edite a função `create_traders()` em `run_live_equal_weight_volatility.py`:
```python
assets_universe=["EURUSD", "GBPUSD", "USDJPY"]  # Seus ativos
```

### Alterar Parâmetros RSI
```python
rsi_buy_threshold=65,  # Seu threshold de compra
rsi_sell_threshold=35, # Seu threshold de venda
```

### Alterar Target Volatility
```python
target_volatility=0.15,  # 15% ao invés de 10%
```

### Alterar Lookback
```python
lookback_period=pd.DateOffset(months=3),  # 3 meses ao invés de 6
```

## Segurança

⚠️ **IMPORTANTE**: Este é um exemplo educacional. Para uso em produção:
- Teste extensivamente em conta demo
- Implemente controles de risco adicionais
- Monitore constantemente
- Tenha planos de contingência
- Considere limitações de capital

## Suporte

Para problemas ou dúvidas:
1. Execute `test_live_setup.py` para diagnóstico
2. Verifique logs detalhados
3. Consulte documentação do mt5se
4. Teste com ativos mais líquidos primeiro
