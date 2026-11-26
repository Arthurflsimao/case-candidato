# Diagnóstico de inconsistências — Case técnico

## 1. Objetivo

Investigar as divergências entre os dados de pagamentos recebidos do tribunal e os registros mantidos pelo sistema, identificando problemas de qualidade dos dados, inconsistências cadastrais, falhas potenciais no processo de integração e erros nas regras de negócio.

A análise considera os arquivos originais fornecidos no case. Nenhum arquivo de origem foi alterado.

## 2. Problemas identificados

### 2.1. Duplicidade de eventos de pagamento

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, eventos `ev-001` e `ev-002`.

O evento `ev-002` aparece duas vezes com exatamente os mesmos dados, incluindo identificador, processo, valor e datas.

O evento `ev-001` também aparece duas vezes, mas com valores diferentes: R$ 15.000,00 no primeiro registro e R$ 15.500,00 no segundo. O segundo registro possui data de atualização posterior.

**Impacto:** a reimportação de eventos pode contabilizar pagamentos mais de uma vez. No caso de `ev-001`, considerar os dois registros como eventos independentes resultaria em duplicidade; considerar apenas um deles sem uma regra de atualização também pode produzir um valor incorreto.

**Relação causal:** o cenário descreve que o operador pode executar novamente o arquivo após uma falha na importação. A ausência de uma restrição de unicidade para `evento_id` no banco aumenta o risco de duplicidade. O comportamento efetivo do importador não pode ser confirmado, pois seu código não foi fornecido.

**Tratamento proposto:** deduplicar registros idênticos e encaminhar eventos com o mesmo identificador e conteúdos diferentes para análise, sem escolher automaticamente um valor.

### 2.2. Formato de valor incompatível com a documentação

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, evento `ev-002`.

O campo `valor` aparece como texto no formato `"2.500,50"`, enquanto `DOCUMENTACAO_TRIBUNAL.md` define esse campo como numérico, com ponto como separador decimal.

**Impacto:** a conversão inadequada pode provocar erros de importação ou interpretação incorreta do valor financeiro.

**Relação causal:** divergência entre o leiaute documentado e o dado recebido, com possível consequência no processamento.

**Tratamento proposto:** aceitar formatos conhecidos e explicitamente identificados, convertendo-os para valores decimais com duas casas. Formatos ambíguos devem ser colocados em análise.

### 2.3. Formato de data incompatível com a documentação

**Gravidade:** Média

**Evidência:** `dados/pagamentos.json`, evento `ev-002`.

A data de pagamento está no formato `10/04/2025`, enquanto a documentação especifica `AAAA-MM-DD`.

**Impacto:** um importador que espere exclusivamente o formato documentado pode rejeitar o registro ou interpretar incorretamente a data.

**Relação causal:** divergência entre o formato recebido e o contrato documentado.

**Tratamento proposto:** normalizar formatos reconhecidos e rejeitar datas inválidas ou ambíguas.

### 2.4. Evento com valor ausente

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, evento `ev-004`.

O campo `valor` está preenchido com `null`.

**Impacto:** não é possível determinar o valor financeiro do evento, impossibilitando sua contabilização confiável.

**Relação causal:** problema de qualidade do dado recebido.

**Tratamento proposto:** separar o evento para análise, sem atribuir valor automaticamente.

### 2.5. Número do processo fora do padrão documentado

**Gravidade:** Média

**Evidência:** `dados/pagamentos.json`, evento `ev-005`.

O processo está registrado como `00234562120208260053`, sem a pontuação do formato CNJ definido na documentação.

**Impacto:** comparações textuais exatas podem impedir a associação do pagamento ao precatório correspondente.

**Relação causal:** falta de padronização dos identificadores, com possível consequência na associação dos registros.

**Tratamento proposto:** validar a quantidade de dígitos e normalizar o processo para uma representação composta por 20 dígitos, preservando o valor original para auditoria.

### 2.6. Estorno exige tratamento específico

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, eventos `ev-006` e `ev-007`.

O processo `0034567-32.2018.8.26.0405` possui um pagamento de R$ 5.000,00 e um estorno de R$ 5.000,00.

**Impacto:** caso o estorno seja somado como um pagamento comum, o total pago será incorreto.

**Relação causal:** risco na regra de contabilização. O esquema do banco permite os tipos `pagamento` e `estorno`, mas não define como o saldo deve ser calculado.

**Tratamento proposto:** definir explicitamente que pagamentos aumentam o total e estornos o reduzem, mantendo os valores armazenados como positivos e utilizando o tipo para determinar o efeito financeiro.

### 2.7. Pagamento com valor negativo

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, evento `ev-009`.

O evento está identificado como `pagamento`, mas possui valor de -R$ 200,00.

**Impacto:** o registro pode ser rejeitado pela restrição `CHECK (valor > 0)` do banco ou reduzir indevidamente o total pago caso seja aceito sem validação.

**Relação causal:** inconsistência do dado recebido, incompatível com o modelo atual do banco e com a semântica do tipo informado.

**Tratamento proposto:** colocar o registro em análise. Não convertê-lo automaticamente em estorno, pois isso exigiria confirmação do tribunal.

### 2.8. Evento sem número de processo

**Gravidade:** Alta

**Evidência:** `dados/pagamentos.json`, evento `ev-010`.

O campo `processo` está vazio.

**Impacto:** não é possível associar o pagamento a um precatório de forma confiável.

**Relação causal:** problema de qualidade do dado recebido.

**Tratamento proposto:** separar o evento para análise, preservando todos os campos originais.

### 2.9. Divergência no valor de face do precatório

**Gravidade:** Alta

**Evidência:** `dados/tribunal.csv` e `dados/hub.csv`, processo `0023456-21.2020.8.26.0053`.

O tribunal informa valor de face de R$ 30.000,00, enquanto o Hub registra R$ 31.000,00.

**Impacto:** o sistema apresenta um valor de face R$ 1.000,00 superior ao informado pelo tribunal, comprometendo a confiabilidade dos dados financeiros e dos relatórios da carteira.

**Relação causal:** divergência cadastral entre as bases. Não é possível determinar, apenas com os arquivos disponíveis, qual operação originou a diferença.

**Tratamento proposto:** apresentar a divergência em relatório e solicitar confirmação antes de atualizar o cadastro automaticamente.

### 2.10. Processo presente somente no Hub

**Gravidade:** Alta

**Evidência:** `dados/hub.csv`, processo `0056789-54.2017.4.03.6100`, ausente de `dados/tribunal.csv`.

O Hub possui um precatório com valor de face de R$ 22.000,00 que não aparece na relação recebida do tribunal.

O processo também possui o evento `ev-009`, que apresenta valor negativo.

**Impacto:** a carteira interna pode conter um registro desatualizado ou não contemplado na relação recebida. Não se deve excluir o precatório sem confirmar sua situação.

**Relação causal:** divergência entre as bases cadastrais. A ausência no arquivo recebido não comprova, isoladamente, que o cadastro interno esteja incorreto.

**Tratamento proposto:** encaminhar para conferência com o tribunal e a operação.

### 2.11. Processo presente somente no tribunal

**Gravidade:** Alta

**Evidência:** `dados/tribunal.csv`, processo `0067890-65.2016.8.26.0053`, ausente de `dados/hub.csv`.

O tribunal informa valor de face de R$ 7.000,00, mas o processo não consta na exportação do Hub. Entretanto, existe um pagamento de R$ 4.000,00 associado a ele no evento `ev-011`.

**Impacto:** o sistema pode não conseguir associar corretamente o pagamento a um precatório cadastrado, comprometendo o acompanhamento financeiro.

**Relação causal:** divergência de sincronização ou cadastro entre as bases.

**Tratamento proposto:** verificar a existência do precatório e sua ausência no Hub antes de importar ou contabilizar o pagamento.

### 2.12. Divergência no ente devedor

**Gravidade:** Alta

**Evidência:** `dados/tribunal.csv` e `dados/hub.csv`, processo `0045678-43.2021.5.02.0011`.

O tribunal informa o ente devedor como União, enquanto o Hub registra Município de Santos. Os valores de face são iguais: R$ 9.800,00.

**Impacto:** a associação do precatório ao ente devedor incorreto pode comprometer relatórios, classificações e decisões operacionais.

**Relação causal:** inconsistência cadastral. Não se trata de uma simples diferença de acentuação ou capitalização, mas de entidades distintas.

**Tratamento proposto:** não realizar substituição automática. Solicitar validação do cadastro com base na fonte oficial.

### 2.13. Incompatibilidade entre o leiaute documentado e o CSV recebido

**Gravidade:** Alta

**Evidência:** `DOCUMENTACAO_TRIBUNAL.md` e `dados/tribunal.csv`.

A documentação especifica um arquivo UTF-8, separado por vírgulas e com valores numéricos utilizando ponto como separador decimal.

O arquivo recebido apresenta:

- Ponto e vírgula como delimitador.
- Valores no formato brasileiro, como `45.000,00`.
- Caracteres acentuados representados por bytes compatíveis com Windows-1252.

A codificação foi investigada por meio da leitura dos bytes do arquivo.

**Impacto:** um importador que siga estritamente a documentação poderá interpretar incorretamente as colunas, falhar na decodificação ou converter valores financeiros de maneira inadequada.

**Relação causal:** divergência entre o contrato de integração documentado e o arquivo efetivamente recebido.

**Tratamento proposto:** formalizar o leiaute esperado com o tribunal e implementar validação explícita de delimitador, codificação e formato numérico.

### 2.14. Prazo de pagamento calculado incorretamente

**Gravidade:** Alta

**Evidência:** `dados/apresentacoes.json` e `dados/hub.csv`, processo `0012345-10.2019.8.26.0053`.

A data de apresentação é 02/04/2025. Conforme a regra descrita no enunciado, o prazo esperado é 31/12/2026. Entretanto, o Hub registra 31/12/2027.

**Impacto:** o sistema pode apresentar uma prioridade incorreta para a carteira, prejudicando o planejamento e o acompanhamento dos precatórios.

**Relação causal:** possível erro na implementação da regra de cálculo ou na atualização do prazo. O código responsável pelo cálculo não foi fornecido.

**Tratamento proposto:** recalcular os prazos a partir da data de apresentação validada, com testes automatizados para os dias anteriores, iguais e posteriores a 2 de abril.

### 2.15. Ambiguidade de fuso horário nas datas de apresentação

**Gravidade:** Alta

**Evidência:** `dados/apresentacoes.json`, processos `0045678-43.2021.5.02.0011` e `0056789-54.2017.4.03.6100`.

Os registros apresentam datas com horário e indicação de fuso:

- Processo `0045678`: `2025-04-02T23:30:00-03:00`.
- Processo `0056789`: `2025-04-03T01:00:00Z`.

Esses horários correspondem, respectivamente, a 03/04/2025 às 02:30 UTC e 02/04/2025 às 22:00 no fuso UTC-3.

**Impacto:** a conversão entre fusos pode alterar o dia considerado para a regra de corte de 2 de abril, resultando em prazos diferentes.

**Relação causal:** ausência de definição explícita sobre o fuso horário aplicável à data de apresentação.

**Tratamento proposto:** confirmar com o tribunal qual fuso determina a data juridicamente válida e aplicar a mesma regra em todo o sistema.

### 2.16. Tamanho incompatível da coluna de número do processo

**Gravidade:** Média

**Evidência:** `schema.sql`, coluna `precatorio.numero_processo`.

A coluna foi definida como `VARCHAR(20)`, mas o número CNJ pontuado possui 25 caracteres. O mesmo número contém 20 dígitos quando removidos os separadores.

**Impacto:** armazenar diretamente o formato pontuado pode causar falha de inserção ou incompatibilidade com o tamanho da coluna.

**Relação causal:** limitação de modelagem do banco relacionada à ausência de uma estratégia explícita de padronização do identificador.

**Tratamento proposto:** adotar uma representação única. Uma alternativa é utilizar `VARCHAR(25)` e armazenar o número no formato CNJ pontuado. Caso a opção seja armazenar somente os 20 dígitos, a normalização deve ser aplicada consistentemente em todas as integrações.

### 2.17. Ausência de unicidade para o identificador do evento

**Gravidade:** Alta

**Evidência:** `schema.sql`, tabela `pagamento`, coluna `evento_id`.

O identificador do evento é obrigatório, mas não possui restrição `UNIQUE`.

**Impacto:** o banco não impede a inserção de eventos repetidos, aumentando o risco de contabilização duplicada quando um arquivo é processado novamente.

**Relação causal:** limitação do modelo de dados que contribui para o risco de falta de idempotência na importação.

**Tratamento proposto:** estabelecer uma chave de unicidade para o identificador do evento, considerando também a origem do evento caso existam múltiplos tribunais.

### 2.18. Ausência de tratamento operacional para falhas de importação

**Gravidade:** Alta

**Evidência:** `ENUNCIADO.md`, seção "O fluxo Operacional".

O processo descrito informa que eventos que não podem ser importados são ignorados e que ninguém é avisado.

Além disso, quando ocorre uma falha no meio da importação, o operador executa novamente o mesmo arquivo.

**Impacto:** erros podem permanecer sem conhecimento da equipe, enquanto a reexecução pode duplicar eventos já processados.

**Relação causal:** problema de processo operacional e de desenho da integração. A ausência de alertas e de mecanismos de idempotência pode agravar as divergências financeiras.

**Tratamento proposto:** implementar processamento transacional, idempotência, registro de erros, relatório de rejeições e alertas para a operação.

## 3. Limitações da investigação

O código do importador não foi disponibilizado. Portanto, os problemas relacionados à sua implementação foram tratados como riscos decorrentes do fluxo descrito, e não como falhas de código comprovadas.

Também não foi fornecida uma especificação formal sobre a atualização de eventos com o mesmo identificador, o tratamento de estornos ou o fuso horário aplicável às datas de apresentação. Essas regras precisam ser confirmadas antes da implantação de qualquer limpeza automática.

## 4. Proposta de prevenção e correção

### 4.1. Processo operacional

Para reduzir erros durante as importações e conciliações, proponho o seguinte fluxo:

1. Preservar os arquivos originais recebidos do tribunal, sem edição manual.
2. Executar o programa de validação antes de qualquer gravação na base oficial.
3. Classificar os registros em quatro categorias:
   - **Válidos:** registros que passaram pelas validações e podem ser considerados no processamento.
   - **Duplicados:** registros repetidos com conteúdo idêntico, dos quais apenas uma ocorrência deve ser contabilizada.
   - **Pendentes:** registros com conflitos ou informações ambíguas que exigem confirmação antes de qualquer contabilização.
   - **Descartados:** registros inválidos que não podem ser importados automaticamente. Devem permanecer registrados nos relatórios para análise operacional.
4. Identificar e documentar as normalizações realizadas em um relatório específico (`correcoes.csv`), registrando os campos alterados e seus valores originais e normalizados.
5. Gerar relatórios com a quantidade de registros por categoria, as alterações realizadas e os motivos de rejeição ou pendência.
6. Conferir os resultados antes de efetivar a importação.
7. Manter um histórico das execuções para permitir auditoria e identificação de falhas.

A operação deve ser repetível: executar novamente o mesmo arquivo não pode duplicar pagamentos nem alterar indevidamente os valores já registrados.

### 4.2. Melhorias no programa de importação

O programa Python deverá:

- Ler diretamente os arquivos originais JSON e CSV.
- Identificar automaticamente o formato dos arquivos ou rejeitá-los com uma mensagem clara quando não forem compatíveis.
- Normalizar números de processo CNJ para uma representação padronizada, preservando o valor original para auditoria.
- Interpretar valores monetários utilizando precisão decimal, evitando erros de arredondamento.
- Validar campos obrigatórios, datas, valores e tipos de evento.
- Identificar eventos duplicados e conflitos de identificadores.
- Não importar registros com informações inválidas ou ambíguas.
- Gerar relatórios de importação, correção, descarte e pendências.
- Registrar erros com identificação do arquivo, registro e motivo da rejeição.

Os registros com conflitos, como o `ev-001`, devem permanecer pendentes até que exista uma regra confirmada para determinar qual versão é válida.

### 4.3. Melhorias no banco de dados

Proponho as seguintes alterações e controles:

- Definir uma representação única para o número do processo, utilizando os 20 dígitos normalizados ou o formato CNJ completo, de maneira consistente.
- Garantir a unicidade do identificador do evento de pagamento. Caso existam diferentes tribunais como origem, considerar uma chave composta pela origem e pelo identificador.
- Manter os valores de pagamento e estorno positivos no armazenamento, utilizando o campo `tipo` para determinar o efeito de cada lançamento no saldo.
- Registrar a origem do arquivo e informações de auditoria da importação.
- Utilizar transações para garantir que uma falha não deixe uma importação parcialmente gravada.
- Antes de criar restrições de unicidade, identificar e resolver os registros duplicados já existentes.

A importação deve ser idempotente: o mesmo evento não pode produzir mais de um lançamento, mesmo que o arquivo seja processado novamente.

### 4.4. Dúvidas que precisam ser esclarecidas

**Ao tribunal:**

- Qual é a codificação e o delimitador oficial dos arquivos CSV? A documentação informa UTF-8 e vírgula, mas o arquivo recebido apresenta características diferentes.
- O que deve acontecer quando um mesmo `evento_id` aparece novamente com valor diferente?
- Como devem ser relacionados os eventos de estorno aos pagamentos originais? Existe um identificador do evento original?
- Qual fuso horário deve ser utilizado para determinar a data de apresentação e aplicar o limite de 2 de abril?
- Um processo sem pontuação no número CNJ é considerado válido pelo sistema de origem?

**À equipe de operação:**

- Qual deve ser o procedimento para registros que não podem ser corrigidos automaticamente?
- Quem deve aprovar alterações de valor ou de ente devedor?
- Como deve ser feita a conferência e a autorização antes de uma importação definitiva?
- Existe um histórico das importações anteriores que permita identificar quando e por quem um registro foi processado?