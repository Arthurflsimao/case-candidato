# Processamento e Conciliação de Precatórios

## 1. Sobre o projeto

Este projeto foi desenvolvido como parte de um case técnico, com o objetivo de automatizar o processamento de pagamentos de precatórios e a conciliação de informações entre os registros internos (Hub) e os arquivos enviados pelo Tribunal.

A solução foi implementada em Python e busca reduzir erros operacionais, evitar a contabilização duplicada de pagamentos e facilitar a identificação de divergências nos dados.

## 2. Funcionalidades

- Leitura de arquivos JSON e CSV.
- Normalização de números de processos no padrão CNJ.
- Validação de identificadores, valores monetários, tipos de evento e datas.
- Identificação de eventos duplicados e conflitos de identificadores.
- Tratamento de pagamentos e estornos.
- Cálculo de saldos por processo.
- Comparação de processos entre Hub e Tribunal.
- Identificação de divergências de valores e entes devedores.
- Conferência de prazos de pagamento.
- Geração de relatórios em CSV e JSON.

## 3. Tecnologias utilizadas

- Python 3.13
- Módulos nativos: `csv`, `json`, `decimal`, `datetime`, `pathlib`, `collections` e `unittest`.

Não são necessárias bibliotecas externas para executar o projeto.

## 4. Estrutura do projeto

```text
case-candidato/
│
├── dados/
│   ├── pagamentos.json
│   ├── apresentacoes.json
│   ├── hub.csv
│   └── tribunal.csv
│
├── src/
│   ├── main.py
│   ├── leitores.py
│   ├── validacoes.py
│   ├── processamento.py
│   └── relatorio.py
│
├── tests/
│   ├── __init__.py
│   ├── test_validacoes.py
│   └── test_processamento.py
│
├── saida/
│
├── DIAGNOSTICO.md
├── DOCUMENTACAO_TRIBUNAL.md
├── ENUNCIADO.md
├── README.md
└── schema.sql
```

## 5. Como executar

### Pré-requisitos

- Python 3.13 ou superior.
- Git (opcional, para controle de versão).

### Executar o processamento

Na pasta raiz do projeto, execute:

```bash
python -m src.main
```

O programa realizará a leitura dos arquivos de entrada, as validações, o processamento dos pagamentos, a conciliação dos dados e a geração dos relatórios.

## 6. Relatórios gerados

Os resultados são armazenados na pasta `saida/`.

| Arquivo | Descrição |
|---|---|
| `pagamentos.csv` | Pagamentos válidos, duplicados, pendentes e descartados. |
| `saldos.csv` | Saldo líquido de pagamentos por processo. |
| `conciliacao.csv` | Comparação entre os dados do Hub e do Tribunal. |
| `prazos.csv` | Conferência dos prazos de pagamento. |
| `relatorio.json` | Consolidação geral dos resultados. |

## 7. Regras e decisões de processamento

### Identificação de duplicidades

Eventos com o mesmo identificador e conteúdo idêntico são contabilizados uma única vez.

Quando um mesmo identificador apresenta conteúdos diferentes, todos os registros envolvidos são encaminhados para análise, sem contabilização automática.

### Valores monetários

Os valores são tratados utilizando `Decimal`, evitando imprecisões comuns em operações financeiras realizadas com números de ponto flutuante.

### Pagamentos e estornos

Pagamentos aumentam o saldo do processo, enquanto estornos reduzem o saldo.

Os valores dos eventos devem ser positivos, sendo o efeito financeiro determinado pelo tipo de evento.

### Normalização de processos

Os números de processos são normalizados para uma representação composta por 20 dígitos, removendo pontuação e caracteres não numéricos.

### Prazos de pagamento

A regra implementada considera:

- Apresentações realizadas até 2 de abril, inclusive: pagamento até 31 de dezembro do ano seguinte.
- Apresentações realizadas após 2 de abril: pagamento até 31 de dezembro do segundo ano seguinte.

Registros com informações de fuso horário ainda não confirmadas são classificados como pendentes.

## 8. Testes automatizados

Os testes foram desenvolvidos utilizando o módulo `unittest`.

Para executar todos os testes:

```bash
python -m unittest discover -v
```

A suíte contempla testes de:

- Normalização de processos.
- Conversão de valores monetários.
- Validação de datas e prazos.
- Validação de pagamentos.
- Identificação de duplicidades e conflitos.
- Cálculo de saldos com estornos.
- Conciliação de valores entre Hub e Tribunal.

## 9. Tratamento de inconsistências

O sistema diferencia registros válidos, duplicados, pendentes e descartados.

As inconsistências identificadas não são corrigidas silenciosamente. Casos que exigem confirmação ou análise operacional são preservados para investigação.

## 10. Limitações e pontos de atenção

- A validação do número CNJ verifica a estrutura de 20 dígitos, mas não realiza a validação oficial do dígito verificador.
- A interpretação de timestamps com fuso horário depende de confirmação da regra adotada pelo Tribunal.
- Conflitos de identificadores e divergências de conciliação exigem análise antes de qualquer correção definitiva.
- O formato real dos arquivos deve ser compatível com as configurações de leitura implementadas.

## 11. Próximas melhorias

- Persistência dos dados em banco de dados relacional.
- Implementação de transações para garantir a integridade das importações.
- Restrição de unicidade para identificadores de eventos.
- Registro histórico das importações e alterações.
- Ampliação da cobertura de testes automatizados.
- Integração com o processo de recebimento dos arquivos do Tribunal.