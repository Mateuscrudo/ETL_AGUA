> **Cópia preparada com dados fictícios.** As planilhas em ENTRADA são exemplos inventados, gerados por `gerar_demo.py`; nenhum dado operacional foi copiado. Consulte [origem dos dados](docs/DADOS_FICTICIOS.md) e [validação desta cópia](VALIDACAO.md). O projeto interno permanece separado.

## Executar os exemplos incluídos

As entradas sintéticas já estão incluídas. Instale `requirements.txt` e execute `python -X utf8 main.py` na raiz. Para Água e Obra, use `$env:EXECUCAO_AGENTE = "1"` antes de executar para dispensar interação. `gerar_demo.py` documenta e reproduz a criação das entradas, mas recusa sobrescrevê-las; use uma cópia vazia para regenerar.

# ETL Água — consolidação BASE_AG e AppDeep

Consolida duas fontes Excel em uma base cadastral de água, com uma linha por matrícula, e reúne links de fotos para consulta pelo aplicativo interno. Gera Excel, SQLite e log de auditoria. As entradas são lidas; o pipeline não grava alterações nelas.

Esta documentação descreve o código local revisado em 13/10/2026. Não representa uma nova validação das bases de produção. Para portfólio, use uma cópia independente com dados sintéticos.

## Estrutura e configuração

```text
ETL_AGUA/
├── config_central.py              # configuração local independente
├── main.py
├── gerar_demo.py
├── requirements.txt
├── ETL/                           # leitura, consolidação e exportações
├── tests/test_demo.py
├── ENTRADA/                       # duas planilhas fictícias incluídas
└── SAIDA_AGUA/                     # gerada ao executar
```

`main.py`, `ler_bases.py` e `gerar_sql.py` importam `ETLS` de `config_central.py`, localizado na raiz deste repositório. Entrada e saída são relativas a essa raiz. Esta é a única adaptação de configuração do pipeline nesta cópia; a instalação interna original continua usando a configuração compartilhada na pasta superior.

O pipeline gera arquivos na saída configurada. Não copia bancos para `APP+CONFIG_AGUA/Bases`, não faz commit/push e não atualiza sozinho o aplicativo.

## Fontes e contrato de entrada

Na entrada configurada, deve existir exatamente um Excel com `BASE_AG` no nome e um com `EXPORTACAO`. A busca ignora diferenças de maiúsculas no nome e considera `.xlsx`, `.xlsm` e `.xls`. Nenhum ou vários candidatos causam erro. Os dados cadastrais são lidos da primeira aba, com cabeçalho na primeira linha, pelo comportamento padrão de `pd.read_excel`.

| Fonte | Colunas obrigatórias validadas |
| --- | --- |
| BASE_AG | `Matrícula`, `Data Adesão`, `Qtd. Tentat.`, `Endereço`, `Comunidade`, `Status Adesão` |
| EXPORTACAO / AppDeep | `Matricula`, `Data do registro`, `Situação Campo`, `Endereço `, `Bairro` |

**O cabeçalho `Endereço ` do AppDeep contém um espaço final.** Os nomes são usados literalmente. O campo opcional `Nome do agente ` também contém espaço final.

Outros campos opcionais incluem `Nome Cliente`, `Telefone`, `Latitude`, `Longitude`, `Equipe Exec.`, `Situação Backoffice`, `Link Backoffice` e `Code Deep`. Ausência de campo opcional não significa preenchimento automático.

Valores preenchidos não numéricos em `Qtd. Tentat.` interrompem a leitura com erro. Valores vazios podem permanecer ausentes; essa validação não impõe inteiro ou valor não negativo.

Matrícula é identificador textual: preserve zeros à esquerda nos arquivos. A preparação remove espaços externos e descarta matrícula vazia. A conversão para maiúsculas ocorre somente na saída cadastral; a comparação entre fontes e a associação das fotos são sensíveis à caixa antes dessa etapa. Não há normalização de identificadores numéricos como `123` versus `123.0`.

## Regras de consolidação

1. Dentro de cada fonte, selecionar uma linha por matrícula: data mais recente, depois prioridade para `Status Adesão = ADESÃO EXECUTADA` quando essa coluna existir, depois última ocorrência no arquivo. No layout obrigatório do AppDeep, `Situação Campo` não participa desse desempate de status.
2. Datas são convertidas com dia primeiro; valores inválidos viram data ausente e perdem para datas válidas.
3. Entre as fontes, vence a data mais recente. AppDeep vence em empate ou quando ambas as datas estão ausentes.
4. Endereço, bairro, status, nome e telefone usam a fonte vencedora; quando o campo está vazio, procuram o correspondente na outra fonte. Latitude e longitude usam a fonte vencedora e fallback quando o valor é ausente.
5. Bairro corresponde a `Comunidade` na BASE_AG e a `Bairro` no AppDeep. Status corresponde a `Status Adesão` e `Situação Campo`, respectivamente.
6. `Data Adesão` e `Equipe Exec.` vêm da BASE_AG; `Data do Registro`, `Situação Backoffice` e `Agente` vêm do registro selecionado do AppDeep, independentemente da fonte vencedora.
7. `Quantidade de Visitas`: quando existe BASE_AG, usar `Qtd. Tentat.` do registro selecionado dessa fonte, inclusive quando ausente. Somente para matrícula exclusiva do AppDeep, contar suas ocorrências antes da seleção de uma linha. Não somar visitas entre as fontes.
8. Não existe exclusão específica por `Tipo Registro Visita = duplicado` neste ETL. As ocorrências AppDeep entram na contagem e na coleta de fotos antes da seleção cadastral.
9. `Origem dos Dados` indica presença nas fontes: `AMBOS`, `BASE PRINCIPAL` ou `BASE ATUALIZADA`.
10. `origem_adesao` identifica a fonte efetiva do status, inclusive fallback; `data_origem_adesao` guarda a data dessa fonte. `link_appdeep` e `registro_appdeep` são preenchidos quando o status provém do AppDeep. O link precisa estar em `Link Backoffice`, com esquema HTTP/HTTPS e hostname; não é construído por matrícula.

Na saída cadastral, campos de texto selecionados são convertidos para maiúsculas e espaços repetidos são compactados. Essa padronização não é aplicada às URLs das fotos, nem a todos os campos indistintamente.

## Fotos

- BASE_AG: procura cabeçalhos `Matrícula` e `Fotos` nas primeiras 20 linhas de cada aba e extrai hyperlinks Excel. Texto solto e fórmula HYPERLINK não são interpretados como hyperlink por esse extrator.
- AppDeep: lê todas as colunas com `foto` no nome; URLs HTTP/HTTPS devem estar separadas por quebra de linha.
- Remove repetição exata de matrícula + URL, ordena por matrícula/data de registro e transforma em uma linha por matrícula: `Matrícula`, `Foto 1`, `Foto 2`, etc.
- A coleta usa registros anteriores também; não fica restrita ao cadastro vencedor. Sem links, a tabela retornada contém apenas a coluna de matrícula.
- O total de colunas de fotos é dinâmico. No SQLite, `Foto 1` até `Foto 10` são renomeadas para `foto_1` até `foto_10`; colunas posteriores mantêm seus nomes. Não há limite de dez links no extrator.
- A tabela final de fotos guarda os links em colunas, sem conservar as colunas intermediárias de origem/tipo/data. O pipeline não baixa imagens nem verifica se os links estão acessíveis.

## Saídas

| Arquivo | Conteúdo |
| --- | --- |
| `SAIDA_AGUA/base_agua_consolidada.xlsx` | Abas `BASE_AGUA` e `FOTOS` |
| `SAIDA_AGUA/base_agua.db` | Tabelas `agua` e `fotos`; índices por `matricula` |
| `SAIDA_AGUA/etl_agua_YYYY-MM-DD.log` | Log diário em modo append |

Os caminhos efetivos seguem `config_central.py`. A base cadastral contém 19 colunas: `Matrícula`, `Endereço`, `Bairro`, `Status Adesão`, `Data Adesão`, `Situação Backoffice`, `Data do Registro`, `Equipe Exec.`, `Agente`, `Latitude`, `Longitude`, `Nome Cliente`, `Telefone`, `Quantidade de Visitas`, `origem_adesao`, `data_origem_adesao`, `link_appdeep`, `registro_appdeep`, `Origem dos Dados`.

O SQLite renomeia os campos cadastrais principais para nomes como `matricula`, `endereco`, `bairro`, `status_adesao`, `data_adesao`, `quantidade_visitas` e `origem_dos_dados`; os quatro campos de rastreabilidade já usam nomes simples.

Excel e tabelas SQLite são substituídos em cada execução. Não há geração em banco temporário, promoção conjunta das saídas ou `integrity_check` no fluxo atual. Uma falha pode deixar saídas parcialmente atualizadas. Preserve a última versão válida antes de reprocessar produção.

## Dependências e execução

Dependências diretas: Python, pandas e openpyxl; para leitura de `.xls`, xlrd. O módulo sqlite3 faz parte do Python. As dependências estão em `requirements.txt`. A cópia foi testada com Python 3.14 e pandas 3.0.5.

Na raiz de `ETL_AGUA`, com `config_central.py` incluído no repositório:

```powershell
python -m pip install -r requirements.txt
python -X utf8 main.py
```

A extração de hyperlinks da BASE_AG usa openpyxl. Portanto, para execução completa com fotos, forneça BASE_AG em `.xlsx` ou `.xlsm`: a descoberta de `.xls` não significa suporte integral a esse formato.

O modo normal pausa após consolidar, antes de exportar, apesar da mensagem `Pressione ENTER para encerrar...`. Para dispensar essa pausa no terminal atual:

```powershell
$env:EXECUCAO_AGENTE = "1"
python -X utf8 main.py
```

Importar `main.py` já pode criar a pasta de saída; o processamento é iniciado por `main()` ou pela execução do arquivo.

## Auditoria e falhas

O log registra entradas, contagens, datas por matrícula presente nas duas fontes, duplicidades internas, origem, duração e `STATUS=SUCESSO` ao final. As auditorias detalhadas acontecem depois das exportações. Algumas mensagens auxiliares usam `print` e não são copiadas para esse log.

Na exceção, o código registra tipo, mensagem e duração, e propaga o erro. Não grava explicitamente `STATUS=FALHA`, não registra traceback completo nesse arquivo e não faz nova tentativa automática. Como o log contém matrículas, deve ser tratado como informação operacional.

## Validação e publicação

A demonstração foi executada somente com dados sintéticos: 3 matrículas em `agua` e 2 linhas em `fotos`. `tests/test_demo.py` reproduz a geração e a execução em pasta temporária e confere visitas, contagens e integridade SQLite. O diagnóstico antigo `ETL/teste_sql.py` não foi incluído.

Configuração independente, manifesto e teste sintético foram adicionados nesta cópia. As únicas entradas incluídas são fictícias e reproduzíveis pelo gerador. Bancos e logs gerados não entram no pacote de publicação. Resultados de produção não foram certificados.
