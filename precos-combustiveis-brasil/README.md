# Trabalho para G2

**Tema** · Preços de Combustíveis no Brasil

![Python 3.12](https://img.shields.io/badge/Python-3.12-136557) ![Dados mensais](https://img.shields.io/badge/Recorte-jul%2F2001%20a%20jan%2F2023-136557) ![Licença MIT](https://img.shields.io/badge/C%C3%B3digo-MIT-136557)

**Autoria** · Gabriel de Moraes Ferreira Campos  
**Professor** · Alexandre Neves Louzada  
**Curso** · Bacharelado em Sistemas de Informação, 8º período  
**Disciplina** · Linguagens de programação

O projeto analisa preços mensais de revenda em três escalas geográficas. A gasolina comum atingiu R$ 7,28/L na média nacional em maio de 2022. Entre as UFs, a distância entre as médias anuais extremas de 2022 chegou a R$ 1,03/L. No mesmo ano, o preço médio do etanol ficou em até 70% do preço da gasolina comum em 5 de 12 meses no Centro-Oeste e em 3 de 12 no Sudeste.

**Palavras-chave** · Preços de combustíveis, gasolina comum, etanol hidratado, séries temporais, ciência aberta.

## Fonte e recorte

O ponto de partida são os três CSV do `archive.zip` fornecido para a disciplina. As cópias em `data/raw/` preservam os bytes originais. Os arquivos cobrem julho de 2001 a janeiro de 2023. Setembro de 2020 está ausente. A janela corresponde a 259 meses de calendário e 258 referências observadas. As unidades territoriais são Brasil, cinco regiões e 27 UFs.

A publicação oficial da ANP fornece a referência para a série mensal. O boletim da agência permite conferir os valores nacionais de gasolina comum de junho a setembro de 2022. O ZIP fornecido não traz identificação de sua versão de origem, produtor do empacotamento ou licença própria. [Série histórica mensal da ANP](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/precos-revenda-e-de-distribuicao-combustiveis/serie-historica-do-levantamento-de-precos) · [Boletim da ANP do terceiro trimestre de 2022](https://www.gov.br/anp/pt-br/centrais-de-conteudo/publicacoes/boletins-anp/btpvc-1/2022/boletim-trimestral-sdc-15-3t22.pdf)

## Perguntas de pesquisa

1. Como evoluiu a média nacional da gasolina comum e quais variações mensais se destacaram?
2. Quanto variou a média anual da gasolina comum entre regiões e UFs em 2022?
3. Em quantos meses de 2022 a razão entre os preços de etanol e gasolina comum ficou em até 70% em cada região?

## Estrutura

| Caminho | Conteúdo |
| --- | --- |
| `projeto.json` | Identificação acadêmica e endereço do repositório para o cabeçalho |
| `data/raw/` | Três arquivos CSV tal como fornecidos |
| `data/data_dictionary.md` | Esquemas, unidades de medida, metadados e regras de transformação |
| `data/processed/` | Painel mensal comprimido, relatório de qualidade, quarentena e tabelas da análise |
| `src/etl.py` | Leitura, validação e transformação para o formato longo |
| `src/analise.py` e `src/figuras.py` | Métricas descritivas e figuras |
| `src/artigo.py` | Geração do artigo e exportação de tabelas e indicadores |
| `src/templates/` e `src/vendor/` | Fontes HTML, CSS e JavaScript e versão local do Plotly.js |
| `notebooks/analise_exploratoria.ipynb` | Exploração, verificação das três escalas e reprodução dos resultados |
| `docs/index.html` | Artigo completo com figuras e dados dos gráficos incorporados |
| `docs/assets/` | Figuras estáticas exportadas |
| `LICENSE` e `LICENCAS.md` | Licença do código e condições de atribuição de conteúdo e dados |

## Reproduzir

Extraia o pacote e abra um terminal na pasta que contém o `README.md`. Para um repositório já publicado, use `git clone URL_REAL_DO_REPOSITORIO` e entre na pasta clonada. O pipeline foi executado em Python 3.12, com as versões listadas em `requirements.txt`.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.etl
.\.venv\Scripts\python.exe -m src.artigo
```

### Linux ou macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.etl
python -m src.artigo
```

Abra [docs/index.html](docs/index.html) no navegador. Os gráficos usam dados e código incorporados. A execução local do pipeline lê os arquivos do projeto. Para explorar o notebook, abra `notebooks/analise_exploratoria.ipynb` em um ambiente Jupyter ou no VS Code e selecione um kernel Python com as dependências do projeto instaladas.

## Como interpretar e auditar

- O ETL retém os preços mínimo, médio e máximo de sete produtos. As lacunas de cobertura continuam vazias. As 16 linhas estaduais sem chaves foram preservadas em um arquivo de quarentena sem imputação de mês ou UF.
- Os agregados de cada escala vêm de seu respectivo CSV. Uma média anual no gráfico corresponde à média aritmética de 12 preços médios mensais da mesma localidade.
- A correlação usa variações da gasolina e do etanol entre meses consecutivos. Os limites de Tukey sinalizam variações extremas sem excluí-las.
- Preços são nominais. Os 70% são uma referência de comparação de preços do etanol e da gasolina. O custo relativo por quilômetro depende da eficiência do veículo com cada combustível.
- Os hashes SHA-256 e os totais por arquivo estão em `data/processed/qualidade.json`. Cada linha do painel tem nome do CSV e número da linha de origem.

## Publicar no GitHub Pages

1. Confira os dados acadêmicos em `projeto.json`. O campo `repositorio_github` contém o endereço do projeto.
2. Execute novamente `python -m src.artigo` com o Python do ambiente do projeto. O cabeçalho do HTML passa a mostrar o link do repositório informado.
3. Envie o conteúdo da pasta do projeto à branch `main` do repositório. Inclua o `docs/index.html` e os arquivos de dados, código e documentação do projeto.
4. No repositório, selecione **Settings → Pages → Build and deployment → Deploy from a branch**. Escolha **main** e **/docs**, salve e, após a publicação, abra o endereço exibido nessa tela. [Configuração da fonte de publicação no GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## FAIR e licenças

**Localizável** · O README, os nomes dos arquivos, o dicionário e os metadados HTML identificam o recorte e a fonte de referência.  
**Acessível** · O pipeline pode usar os dados incluídos localmente. O repositório público e o GitHub Pages são as etapas de divulgação previstas para a entrega.  
**Interoperável** · Os brutos e o painel processado usam CSV UTF-8. O painel é disponibilizado em Gzip.  
**Reutilizável** · O ambiente Python tem versões fixadas. O código tem licença MIT e o conteúdo textual e as figuras originais são licenciados em CC BY 4.0. A procedência e as condições de uso de dados de terceiros são descritas à parte. [Princípios FAIR](https://doi.org/10.1038/sdata.2016.18) · [Licenças do projeto](LICENCAS.md)
