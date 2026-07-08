# Dashboard de Telemetria - rb_telemetria

Este arquivo (`telemetry_grafana.json`) define um dashboard do Grafana (formato `dashboard.grafana.app/v2`) responsável por exibir em tempo real os dados de telemetria da empilhadeira autônoma do projeto. Ele pode ser importado diretamente no Grafana para recriar o painel de monitoramento.

## Visão geral

- **Título do dashboard:** `rb_telemetria`
- **Fonte de dados:** PostgreSQL/TimescaleDB (datasource `efr0zsd6jbvnke`), dataset `projeto_b`
- **Tabela consultada:** `rb_emp`
- **Intervalo de tempo padrão:** últimos 5 minutos (`now-5m` até `now`)
- **Auto-refresh disponível:** 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d (nenhum intervalo fixo é aplicado por padrão)
- **Fuso horário:** o do navegador

## Painéis

| Painel | Título | Tipo | Coluna de origem | Cálculo/Query | Faixa (min-max) |
|---|---|---|---|---|---|
| panel-1 | Tensão | gauge | `tensao_v` | Média por bucket de 1s | 11 a 12.4 |
| panel-2 | Corrente | gauge | `corrente_ma` | Média por bucket de 1s | 0 a 3 |
| panel-3 | Potência | gauge | `potencia_mw` | Média por bucket de 1s | 0 a 37.2 |
| panel-4 | RPM esquerdo | gauge | `rpm_esq` | Média por bucket de 1s | 0 a 150 |
| panel-5 | RPM direito | gauge | `rpm_dir` | Média por bucket de 1s | 0 a 150 |
| panel-6 | Modo | stat | `tipo` | Última leitura (`ORDER BY created_at DESC LIMIT 1`) | - |
| panel-7 | Falha no Motor de Passo? | stat | `falha_motor_passo` | Última leitura (`ORDER BY created_at DESC LIMIT 1`) | - |

### Painéis 1 a 5 (gauges de séries temporais)

Utilizam `time_bucket('1 second', created_at)` do TimescaleDB para agregar os dados em janelas de 1 segundo e calcular a média (`AVG`) da coluna correspondente dentro do intervalo de tempo selecionado no dashboard (`$__timeFilter(created_at)`). Todos exibem sparkline e usam gradiente de cor contínuo (verde a vermelho), exceto Corrente e RPM direito, que usam limiares em modo percentual (60% amarelo, 80% vermelho).

### Painel 6 - Modo

Mostra o modo de operação atual do sistema, traduzindo o valor numérico da coluna `tipo` para um rótulo textual:

- `0` -> Manual
- `1` -> Autônomo
- `2` -> Procura
- `3` -> Garfo
- Qualquer outro valor -> Desconhecido

### Painel 7 - Falha no Motor de Passo?

Mostra o status mais recente da coluna `falha_motor_passo`, traduzido para texto:

- `0` -> Não
- `1` -> Sim
- Qualquer outro valor -> Desconhecido

## Layout na tela

Os painéis são organizados em um grid de 22 colunas, em três linhas:

1. **Linha 1** (altura 6): Tensão, Corrente e Potência lado a lado.
2. **Linha 2** (altura 6): Falha no Motor de Passo, RPM esquerdo e RPM direito lado a lado.
3. **Linha 3** (altura 4): Modo, ocupando a largura total (22 colunas).

## Requisitos para reutilização

Para que este dashboard funcione em outro ambiente, é necessário:

1. Ter uma instância do Grafana (Cloud ou self-hosted) compatível com o schema `dashboard.grafana.app/v2`.
2. Configurar um datasource do tipo `grafana-postgresql-datasource` apontando para o banco PostgreSQL/TimescaleDB que contém o dataset `projeto_b` e a tabela `rb_emp`.
3. Atualizar o campo `datasource.name` em cada painel (`efr0zsd6jbvnke`) para o UID do datasource configurado no novo ambiente, caso seja diferente.
4. Garantir que a tabela `rb_emp` possua, no mínimo, as colunas: `created_at`, `tensao_v`, `corrente_ma`, `potencia_mw`, `rpm_esq`, `rpm_dir`, `tipo` e `falha_motor_passo`.

## Importação no Grafana

1. No Grafana, acessar **Dashboards > New > Import**.
2. Colar o conteúdo de `telemetry_grafana.json` ou fazer upload do arquivo.
3. Selecionar/ajustar o datasource PostgreSQL correspondente.
4. Confirmar a importação.
