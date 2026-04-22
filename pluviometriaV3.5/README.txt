README - FUNÇÕES PRINCIPAIS DO PROJETO PLUVIOMETRIA

1. VISÃO GERAL

Este projeto executa um fluxo de pluviometria distribuído com duas camadas principais:

- lado cliente/Raspberry:
  - coleta de medições;
  - armazenamento local em SQLite;
  - fila de pendências;
  - sincronização em lote com o PC;
  - manutenção local opcional para remoção de registros antigos já enviados;

- lado PC/servidor:
  - recebimento dos lotes enviados pelo cliente;
  - persistência bruta no banco central SQLite;
  - análise automática da janela recente;
  - persistência analítica em tabela separada;
  - geração e gestão do ciclo de vida dos alertas;
  - monitor gráfico rudimentar em tempo real.

No estado atual do desenvolvimento, o modo principal de uso no PC é:
MODO_EXECUCAO = "simulado"

Esse valor deve estar configurado em:
app/config.py

==================================================
2. ARQUIVOS PRINCIPAIS
==================================================

main.py
Inicia a execução contínua do sistema no lado cliente.

pc/servidor_recepcao.py
Sobe o servidor do PC, recebe os lotes enviados pelo cliente e executa a persistência central.

pc/persistencia_central.py
Coordena a persistência bruta no PC e dispara a camada analítica após o recebimento dos lotes.

pc/processador_analitico.py
Coordena segmentação da janela, análise, persistência analítica e gestão do ciclo de vida dos alertas.

pc/analisador_evento.py
Executa a análise consolidada de uma janela recente de medições.

pc/features_chuva.py
Extrai as features analíticas a partir de uma sequência de medições.

pc/classificador_chuva.py
Classifica a chuva, a severidade operacional, o pré-alerta e o score de confiança.

pc/segmentador_janela_analitica.py
Seleciona o trecho recente contínuo e coerente antes da análise.

pc/gerador_alertas.py
Traduz o resultado analítico em um alerta operacional inicial.

pc/gestor_alertas.py
Decide se um alerta deve ser aberto, atualizado, encerrado ou ignorado.

pc/monitor_tempo_real.py
Renderiza um monitor gráfico rudimentar em tempo real, lendo o banco central do PC.

scripts/healthcheck_ambiente.py
Verifica o estado geral do ambiente, dos bancos e do servidor.

scripts/inspecionar_banco.py
Inspeciona o banco local do cliente.

scripts/inspecionar_banco_central.py
Inspeciona as medições brutas persistidas no banco central do PC.

scripts/inspecionar_analises_central.py
Inspeciona as análises persistidas no banco central do PC.

scripts/inspecionar_alertas_central.py
Inspeciona os alertas com ciclo de vida persistidos no banco central do PC.

scripts/limpar_bases_desenvolvimento.py
Remove bancos locais de desenvolvimento e testes.

scripts/limpar_banco_central.py
Limpa medições brutas, análises e alertas do banco central do PC.

scripts/limpar_medicoes.py
Remove medições do banco local por status.

scripts/limpar_medicoes_antigas.py
Remove medições antigas do banco local, considerando apenas registros ENVIADO.

scripts/executar_manutencao_local.py
Simula ou executa a manutenção local do banco principal.

scripts/monitor_tempo_real.py
Abre o monitor gráfico rudimentar do banco central.

==================================================
3. FLUXO ATUAL DO SISTEMA
==================================================

Fluxo principal atualmente implementado:

1. o cliente coleta medições em intervalos regulares;
2. cada medição é persistida localmente em SQLite;
3. quando a regra de envio é satisfeita, o cliente envia um lote ao PC;
4. o PC valida e persiste o dado bruto no banco central;
5. o PC monta a janela recente válida para análise;
6. o PC executa a análise por regras;
7. o PC persiste o resultado analítico em tabela separada;
8. o PC gera o alerta operacional correspondente;
9. o PC abre, atualiza ou encerra o alerta conforme o estado do evento.

==================================================
4. COMO RODAR O SISTEMA PRINCIPAL
==================================================

PASSO 1 - Subir o servidor do PC

No terminal, na raiz do projeto, rode:

python -m pc.servidor_recepcao

Esse comando inicia o servidor que:
- escuta a porta configurada;
- recebe lotes do cliente;
- persiste as medições brutas;
- tenta executar a análise automática;
- tenta abrir, atualizar ou encerrar alertas;
- responde com os IDs confirmados.

PASSO 2 - Subir o sistema principal

Em outro terminal, também na raiz do projeto, rode:

python main.py

Esse comando inicia:
- coleta contínua;
- persistência local;
- sincronização automática;
- manutenção local automática, se ela estiver habilitada no config.py.

PASSO 3 - Encerrar o sistema

Para encerrar:
- pare o servidor com Ctrl + C
- pare o main com Ctrl + C

==================================================
5. CONFIGURAÇÕES IMPORTANTES
==================================================

Arquivo:
app/config.py

Principais parâmetros do cliente:

MODO_EXECUCAO
Define o modo atual do sistema.
Valor esperado no PC:
simulado

INTERVALO_MEDICAO_SEGUNDOS
Intervalo entre medições.

LIMITE_LOTE_SINCRONIZACAO
Quantidade máxima de registros por lote.

INTERVALO_VERIFICACAO_PENDENCIAS_SEGUNDOS
Intervalo de checagem para decidir quando sincronizar.

TEMPO_MAXIMO_ESPERA_ENVIO_SEGUNDOS
Tempo máximo que um registro pode esperar antes de forçar envio.

MANUTENCAO_LOCAL_HABILITADA
Ativa ou desativa a manutenção local automática no main.

RETENCAO_LOCAL_ENVIADOS_HORAS
Define por quantas horas registros ENVIADO ficam retidos localmente.

INTERVALO_MANUTENCAO_LOCAL_SEGUNDOS
Define de quanto em quanto tempo a manutenção automática roda.

USAR_PULSOS_ALEATORIOS
Define se a simulação usa pulsos aleatórios ou padrão fixo.

PADRAO_PULSOS_SIMULADOS
Define o padrão fixo de pulsos da simulação determinística.

Principais parâmetros da camada analítica no PC:

LIMITE_JANELA_ANALITICA
Quantidade máxima de medições recentes consideradas na análise.

MINIMO_MEDICOES_ANALISE
Quantidade mínima de medições válidas para permitir a análise.

TOLERANCIA_CONTIGUIDADE_MEDICOES_SEGUNDOS
Folga máxima permitida entre medições consecutivas para manter a janela válida.

PERMITIR_REINICIO_ACUMULADO_NA_JANELA
Define se a análise permite misturar medições com reinício de acumulado.

Configurações de rede:

HOST_SERVIDOR_PC
Endereço do servidor do PC.
Durante testes locais normalmente fica em:
127.0.0.1

PORTA_SERVIDOR_PC
Porta usada na comunicação.

TIMEOUT_SOCKET_SEGUNDOS
Tempo limite do socket durante conexão e envio.

==================================================
6. VERIFICAÇÃO DO AMBIENTE
==================================================

Para verificar rapidamente o estado do projeto, rode:

python -m scripts.healthcheck_ambiente

Esse comando mostra:
- modo de execução atual;
- estado do banco local;
- estado do banco central;
- se o servidor do PC está disponível;
- qual serviço respondeu;
- qual persistência o servidor está usando.

Use esse comando antes de testes importantes ou antes de subir o fluxo completo.

==================================================
7. INSPEÇÃO DO BANCO LOCAL
==================================================

Para ver o banco local:

python -m scripts.inspecionar_banco

Para ver apenas pendentes:

python -m scripts.inspecionar_banco --pendentes

Para limitar a quantidade exibida:

python -m scripts.inspecionar_banco --limite 10

Esse comando é útil para verificar:
- quantas medições existem no banco local;
- quantas estão pendentes;
- quantas já foram enviadas;
- detalhes de cada registro.

==================================================
8. INSPEÇÃO DO BANCO CENTRAL DO PC
==================================================

Para ver as medições brutas do banco central:

python -m scripts.inspecionar_banco_central

Para limitar a quantidade exibida:

python -m scripts.inspecionar_banco_central --limite 10

Esse comando mostra:
- total de registros persistidos no banco central;
- id central;
- id de origem;
- data e hora;
- pulsos;
- chuva do intervalo;
- acumulado;
- data de recebimento.

==================================================
9. INSPEÇÃO DAS ANÁLISES CENTRAIS
==================================================

Para ver as análises persistidas no banco central:

python -m scripts.inspecionar_analises_central

Para limitar a quantidade exibida:

python -m scripts.inspecionar_analises_central --limite 10

Esse comando mostra:
- quantidade de análises persistidas;
- classificação da chuva;
- severidade operacional;
- tendência;
- pré-alerta;
- score de confiança;
- momento da análise.

==================================================
10. INSPEÇÃO DOS ALERTAS CENTRAIS
==================================================

Para ver os alertas com ciclo de vida:

python -m scripts.inspecionar_alertas_central

Para limitar a quantidade exibida:

python -m scripts.inspecionar_alertas_central --limite 10

Esse comando mostra:
- total de alertas persistidos;
- status do alerta;
- nível atual;
- nível máximo atingido;
- primeira e última medição associadas;
- quantidade de atualizações;
- datas de abertura, atualização e encerramento.

==================================================
11. LIMPEZA DAS BASES DE DESENVOLVIMENTO
==================================================

Para apagar as bases locais de desenvolvimento e testes:

python -m scripts.limpar_bases_desenvolvimento

Esse comando remove:
- banco local principal;
- bancos locais auxiliares de desenvolvimento e testes.

Use com cuidado.

==================================================
12. LIMPEZA DO BANCO CENTRAL
==================================================

Para apagar toda a base central de desenvolvimento:

python -m scripts.limpar_banco_central

Esse comando remove:
- medições brutas;
- análises;
- alertas com ciclo de vida.

Use com cuidado.

==================================================
13. LIMPEZA DO BANCO LOCAL POR STATUS
==================================================

Para remover apenas registros ENVIADO:

python -m scripts.limpar_medicoes --enviadas

Para remover apenas registros PENDENTE:

python -m scripts.limpar_medicoes --pendentes

Para remover tudo do banco local:

python -m scripts.limpar_medicoes --todas

Esse script opera sobre o banco local principal.

==================================================
14. LIMPEZA DO BANCO LOCAL POR IDADE
==================================================

Para remover registros ENVIADO mais antigos que uma data fixa:

python -m scripts.limpar_medicoes_antigas --antes-de "2026-04-19 03:00:00"

Para remover registros ENVIADO mais antigos que uma quantidade de horas:

python -m scripts.limpar_medicoes_antigas --mais-antigas-que-horas 24

Esse comando:
- remove somente registros ENVIADO;
- não remove pendentes;
- usa o campo enviado_em como referência de antiguidade.

==================================================
15. MANUTENÇÃO LOCAL MANUAL
==================================================

Para apenas simular a manutenção local:

python -m scripts.executar_manutencao_local

Para executar a manutenção de verdade:

python -m scripts.executar_manutencao_local --executar

Para usar outra retenção:

python -m scripts.executar_manutencao_local --retencao-horas 12

ou

python -m scripts.executar_manutencao_local --retencao-horas 12 --executar

Sem a flag --executar, o script só mostra:
- a data limite calculada;
- quantos registros seriam removidos.

==================================================
16. MONITOR GRÁFICO RUDIMENTAR
==================================================

Para abrir o monitor gráfico do banco central:

python -m scripts.monitor_tempo_real

Exemplo com parâmetros:

python -m scripts.monitor_tempo_real --limite-medicoes 30 --limite-analises 20 --limite-alertas 20 --intervalo-ms 2000

O monitor, no estado atual, exibe:
- medições recentes;
- classificação da chuva;
- severidade operacional;
- score de confiança;
- alertas do evento.

Observação:
a primeira versão do monitor é funcional, mas ainda rudimentar. Pode ser necessário evoluir a organização visual dos gráficos em sessões futuras.

==================================================
17. FLUXO RECOMENDADO DE USO
==================================================

Fluxo básico para operar o projeto no PC:

1. verificar ambiente:
python -m scripts.healthcheck_ambiente

2. subir o servidor do PC:
python -m pc.servidor_recepcao

3. subir o sistema principal:
python main.py

4. inspecionar o banco local quando necessário:
python -m scripts.inspecionar_banco

5. inspecionar medições brutas no banco central:
python -m scripts.inspecionar_banco_central

6. inspecionar análises no banco central:
python -m scripts.inspecionar_analises_central

7. inspecionar alertas no banco central:
python -m scripts.inspecionar_alertas_central

8. abrir o monitor gráfico, se desejado:
python -m scripts.monitor_tempo_real

==================================================
18. OBSERVAÇÕES IMPORTANTES
==================================================

1. No PC, usar preferencialmente:
MODO_EXECUCAO = "simulado"

2. O modo gpio está reservado para futura execução real no Raspberry e não deve ser usado no PC comum.

3. Antes de rodar fluxos longos, vale verificar:
- se o servidor está ligado;
- se o banco local está limpo ou em estado conhecido;
- se a manutenção automática está desativada ou configurada corretamente;
- se a simulação está em modo aleatório ou determinístico.

4. Durante testes controlados, pode ser útil ajustar temporariamente:
- USAR_PULSOS_ALEATORIOS
- PADRAO_PULSOS_SIMULADOS
- MANUTENCAO_LOCAL_HABILITADA
- RETENCAO_LOCAL_ENVIADOS_HORAS
- INTERVALO_MANUTENCAO_LOCAL_SEGUNDOS

Depois dos testes, o ideal é voltar para uma configuração segura.

5. A camada analítica atual ainda é baseada em regras heurísticas, sem modelo de ML treinado.

6. O monitor gráfico atual é somente de leitura e não interfere na coleta, na sincronização ou na análise.

==================================================
19. ESTADO ATUAL
==================================================

No estado atual do projeto, já estão funcionando:

- coleta simulada;
- persistência local em SQLite;
- sincronização em lote;
- confirmação por IDs;
- persistência central em SQLite no PC;
- health check;
- inspeção dos bancos;
- limpeza e manutenção local;
- extração de features da chuva;
- classificação por regras;
- score de confiança;
- segmentação da janela analítica;
- persistência analítica;
- geração de alertas;
- ciclo de vida do alerta;
- monitor gráfico rudimentar.

As próximas evoluções naturais do projeto são:
- refinamento do monitor gráfico;
- integração com a base real do projeto;
- evolução futura para ML e IA sobre a camada analítica.
