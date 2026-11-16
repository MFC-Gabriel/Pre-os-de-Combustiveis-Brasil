# Dicionário de dados

## Identificação da base

| Metadado | Descrição |
| --- | --- |
| Título | Preços mensais de revenda de combustíveis no Brasil, por região e UF |
| Entrada | `archive.zip`, fornecido para a disciplina |
| Fonte oficial de referência | [Série histórica mensal do levantamento de preços da ANP](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/precos-revenda-e-de-distribuicao-combustiveis/serie-historica-do-levantamento-de-precos) |
| Período | Julho de 2001 a janeiro de 2023, com setembro de 2020 ausente |
| Abrangência | Brasil, cinco regiões e 27 unidades federativas |
| Moeda | Real brasileiro, preços nominais |
| Proveniência | O ZIP não declara versão, autor do empacotamento ou licença. O boletim da ANP do 3º trimestre de 2022 corrobora os valores nacionais de gasolina comum de junho a setembro de 2022. |
| Integridade | Hashes SHA-256 dos três arquivos, armazenados em `processed/qualidade.json` |

## CSV brutos

Os arquivos são codificados em UTF-8, com separador vírgula e casas decimais separadas por ponto. A linha 1 traz o cabeçalho. Um campo de preço vazio indica que a estatística não está disponível para o mês, o produto e o território.

| Arquivo | Grão da linha | Chave esperada | Linhas brutas | Linhas válidas |
| --- | --- | --- | ---: | ---: |
| `combustiveis-brasil.csv` | Brasil em um mês | `referencia` | 258 | 258 |
| `combustiveis-regioes.csv` | Uma região em um mês | `referencia`, `regiao` | 1.290 | 1.290 |
| `combustiveis-estados.csv` | Uma UF em um mês | `referencia`, `estado` | 6.966 | 6.950 |

| Variável | Tipo | Formato ou domínio | Descrição |
| --- | --- | --- | --- |
| `referencia` | Texto | `AAAA-MM` | Mês de referência dos preços |
| `ano` | Inteiro | `AAAA` | Ano de referência |
| `mes` | Inteiro | `01` a `12` no CSV bruto | Mês do ano |
| `regiao` | Texto | `CENTRO OESTE`, `NORDESTE`, `NORTE`, `SUDESTE`, `SUL` | Região do agregado regional ou da UF, presente nos arquivos regional e estadual |
| `estado` | Texto | Nome da UF em caixa alta sem acentos | UF da observação, presente no arquivo estadual. Inclui o Distrito Federal. |

Os 21 campos abaixo são números decimais de ponto flutuante, com vazios permitidos. O sufixo `avg` indica o preço médio de revenda, `min` o menor preço de revenda e `max` o maior preço de revenda no agregado mensal de origem.

| Combustível | Unidade | Média | Mínimo | Máximo |
| --- | --- | --- | --- | --- |
| Gasolina comum | R$/L | `gasolina_comum_preco_revenda_avg` | `gasolina_comum_preco_revenda_min` | `gasolina_comum_preco_revenda_max` |
| Gasolina aditivada | R$/L | `gasolina_aditivada_preco_revenda_avg` | `gasolina_aditivada_preco_revenda_min` | `gasolina_aditivada_preco_revenda_max` |
| Etanol hidratado | R$/L | `etanol_hidratado_preco_revenda_avg` | `etanol_hidratado_preco_revenda_min` | `etanol_hidratado_preco_revenda_max` |
| Óleo diesel | R$/L | `oleo_diesel_preco_revenda_avg` | `oleo_diesel_preco_revenda_min` | `oleo_diesel_preco_revenda_max` |
| Óleo diesel S10 | R$/L | `oleo_diesel_s10_preco_revenda_avg` | `oleo_diesel_s10_preco_revenda_min` | `oleo_diesel_s10_preco_revenda_max` |
| GLP P13 | R$/botijão de 13 kg | `gas_cozinha_glp_preco_revenda_avg` | `gas_cozinha_glp_preco_revenda_min` | `gas_cozinha_glp_preco_revenda_max` |
| Gás natural veicular | R$/m³ | `gas_natural_veicular_gnv_preco_revenda_avg` | `gas_natural_veicular_gnv_preco_revenda_min` | `gas_natural_veicular_gnv_preco_revenda_max` |

## Painel mensal processado

O arquivo `processed/precos_mensais.csv.gz` é CSV UTF-8 comprimido. Cada linha representa um mês, um território e um combustível. A chave é `referencia`, `nivel`, `localidade` e `combustivel`. Foram geradas 59.486 linhas e os preços ausentes estão vazios no CSV. A granularidade preserva a linha e a abrangência de origem.

| Variável | Tipo | Formato ou domínio | Descrição |
| --- | --- | --- | --- |
| `referencia` | Data mensal | `AAAA-MM` no disco, primeiro dia do mês em memória | Mês de referência |
| `ano` | Inteiro | `AAAA` | Ano conferido contra a referência |
| `mes` | Inteiro | 1 a 12 | Mês conferido contra a referência |
| `nivel` | Texto | `Brasil`, `Região`, `UF` | Escala do agregado de origem |
| `localidade` | Texto | `Brasil` ou nome de região/UF | Rótulo padronizado com acentos |
| `regiao` | Texto, anulável | Nome padronizado da região | Preenchido nos níveis Região e UF |
| `uf` | Texto, anulável | Sigla de duas letras | Preenchido no nível UF |
| `combustivel` | Texto | Prefixo do campo de preço bruto | Código de um dos sete produtos |
| `unidade` | Texto | `R$/L`, `R$/botijão de 13 kg` ou `R$/m³` | Unidade monetária do produto |
| `preco_medio` | Decimal, anulável | Pontuação decimal com ponto | Preço médio de revenda da fonte |
| `preco_minimo` | Decimal, anulável | Pontuação decimal com ponto | Menor preço de revenda da fonte |
| `preco_maximo` | Decimal, anulável | Pontuação decimal com ponto | Maior preço de revenda da fonte |
| `arquivo_origem` | Texto | Nome do CSV bruto | Referência ao arquivo de entrada |
| `linha_csv` | Inteiro | A partir de 2 | Posição no arquivo bruto contando o cabeçalho como linha 1 |

## Arquivos de auditoria

- `linhas_em_quarentena.csv` preserva todos os campos originais das linhas sem chave, acompanhados de `arquivo` (texto), `linha_csv` (inteiro) e `motivo` (texto). Nenhum preço é reaproveitado sem a identificação temporal e territorial.
- `qualidade.json` contém, para cada escala, `arquivo` (texto), `sha256` (hexadecimal de 64 caracteres), `linhas_brutas`, `linhas_validas`, `linhas_quarentena`, `territorios` e `meses_observados` (inteiros). `primeira_referencia` e `ultima_referencia` usam `AAAA-MM`. A lista `meses_ausentes` mostra as lacunas de calendário em toda a escala. Em UF, `meses_ausentes_por_uf` informa lacunas adicionais, entre os meses presentes na escala. Em `cobertura`, cada produto tem contagens inteiras de preços médios observados e ausentes e primeira e última referências observadas em `AAAA-MM`.
- O Amapá possui 16 lacunas adicionais. A posição ou o preço de uma linha sem identificação não confirma sua origem. O pipeline mantém esses registros em quarentena.

## Tabelas derivadas

As tabelas anuais reaproveitam `ano`, `nivel`, `localidade`, `regiao` e `uf` como dimensões. Os demais campos são os seguintes.

| Arquivo | Variável | Tipo e significado |
| --- | --- | --- |
| `variacoes_mensais.csv` | `referencia` | Mês, `AAAA-MM` |
| `variacoes_mensais.csv` | `gasolina_var_pct` | Decimal em % · 100 × (média do mês / média do mês anterior − 1) |
| `variacoes_mensais.csv` | `etanol_var_pct` | Decimal em % · mesma fórmula aplicada ao etanol |
| `variacoes_mensais.csv` | `limite_inferior_pct`, `limite_superior_pct` | Decimais em % · Q1 − 1,5 × IQR e Q3 + 1,5 × IQR |
| `variacoes_mensais.csv` | `fora_dos_limites_iqr` | Booleano · marca variação estritamente fora dos limites |
| `medias_anuais_gasolina.csv` | `preco_medio_anual` | Decimal em R$/L · média aritmética dos preços médios mensais da gasolina comum |
| `medias_anuais_gasolina.csv` | `meses` | Inteiro · são incluídos apenas territórios com 12 meses no respectivo ano |
| `frequencia_etanol_gasolina.csv` | `meses_validos` | Inteiro · meses com ambos os preços disponíveis |
| `frequencia_etanol_gasolina.csv` | `meses_ate_70_pct` | Inteiro · quantidade de razões etanol/gasolina ≤ 0,70. Arredondamento a 12 casas decimais na comparação para evitar efeito de representação binária no limite. |
| `frequencia_etanol_gasolina.csv` | `razao_media` | Decimal adimensional · média das razões mensais em que ambos os preços existem |
| `indicadores.json` | Resumos por pergunta | Preços em R$/L, variações cujo nome termina em `_pct` em porcentagem, com sinal, contagens inteiras e correlação de Pearson adimensional |

A média móvel do artigo usa 12 meses de calendário e aparece apenas quando os 12 preços estão disponíveis. As variações mensais também respeitam o calendário, com lacunas preservadas. As razões mostradas em porcentagem multiplicam a razão adimensional por 100. Os preços permanecem em moeda nominal ao longo de toda a análise.
