"""Regenera os indicadores, as figuras e o artigo HTML autônomo."""

import argparse
from base64 import b64encode
from html import escape
import json
from pathlib import Path
import re

import pandas as pd

from . import analise, figuras
from .etl import PRODUCTS, REGIONS, ROOT, load_panel, write_json

TEMPLATES = ROOT / "src" / "templates"
VENDOR = ROOT / "src" / "vendor"
ANP_ROOT = (
    "https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/"
    "precos/precos-revenda-e-de-distribuicao-combustiveis"
)
ANP_SERIE = ANP_ROOT + "/serie-historica-do-levantamento-de-precos"
ANP_BOLETIM = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/publicacoes/boletins-anp/"
    "btpvc-1/2022/boletim-trimestral-sdc-15-3t22.pdf"
)
MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)
MONTH_ABBR = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")
LEVELS = {"Brasil": "Mês × Brasil", "Região": "Mês × região", "UF": "Mês × UF"}

EXCERPT = """from src.etl import load_panel
from src.analise import serie_nacional, comparacoes

painel = load_panel()
nacional = serie_nacional(painel)  # Índice mensal mantém lacunas no calendário
media_movel = nacional.rolling(12, min_periods=12).mean()
variacoes_pct = nacional.pct_change(fill_method=None).mul(100)

pares = comparacoes(painel)
razao = pares["etanol_hidratado"].div(pares["gasolina_comum"])
"""


def local_number(value, precision=2):
    return f"{value:,.{precision}f}".translate(str.maketrans(",.-", ".,−"))


def reais(value):
    return f"R$ {local_number(value)}"


def percent(value, precision=2):
    return local_number(value, precision) + "%"


def month_long(value):
    year, month = value.split("-")
    return f"{MONTHS[int(month) - 1]} de {year}"


def serialize(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")


def data_uri(path):
    return "data:image/png;base64," + b64encode(path.read_bytes()).decode("ascii")


def option(value, label, selected=False):
    active = " selected" if selected else ""
    return f'<option value="{escape(str(value))}"{active}>{escape(str(label))}</option>'


def cell_values(values):
    return "".join(f'<td class="num">{escape(str(value))}</td>' for value in values)


def row(label, *values):
    return f'<tr><th scope="row">{escape(str(label))}</th>{cell_values(values)}</tr>'


def inventory_table(quality):
    return "".join(
        f'<tr><th scope="row"><code>{report["arquivo"]}</code></th>'
        f'<td>{LEVELS[level]}</td>'
        + cell_values(
            [local_number(report["linhas_brutas"], 0), local_number(report["linhas_validas"], 0)]
        )
        + "</tr>"
        for level, report in quality.items()
    )


def series_table(dados):
    series = dados["nacional"][analise.GASOLINA]
    return "".join(
        row(
            f"{date[5:7]}/{date[:4]}",
            local_number(price, 4) if price is not None else "—",
            local_number(rolling, 4) if rolling is not None else "—",
        )
        for date, price, rolling in zip(dados["referencias"], series["mensal"], series["movel"])
    )


def ratio_table(ratios):
    areas = list(REGIONS.values())
    heads = "".join(f'<th scope="col" class="num">{name}</th>' for name in areas)
    rows = "".join(
        row(month, *(percent(ratios[name][i]) if ratios[name][i] is not None else "—" for name in areas))
        for i, month in enumerate(MONTH_ABBR)
    )
    return f'<thead><tr><th scope="col">Mês</th>{heads}</tr></thead><tbody>{rows}</tbody>'


def academic_metadata(config, quality, repository):
    authors = escape(", ".join(config["autores"]))
    affiliations = ["Bacharelado em Sistemas de Informação", "6º período"]
    if config["instituicao"].strip():
        affiliations.append(config["instituicao"].strip())
    semester = config["semestre_letivo"].strip()
    dataset = quality["Brasil"]
    json_ld = {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "name": f"{config['titulo']} · {config['tema']}",
        "about": {"@type": "Thing", "name": config["tema"]},
        "inLanguage": "pt-BR",
        "author": [{"@type": "Person", "name": name} for name in config["autores"]],
        "temporalCoverage": f'{dataset["primeira_referencia"]}/{dataset["ultima_referencia"]}',
        "keywords": ["preços de combustíveis", "gasolina comum", "etanol", "séries temporais", "ciência aberta"],
    }
    if config["instituicao"].strip():
        for author in json_ld["author"]:
            author["affiliation"] = {"@type": "Organization", "name": config["instituicao"].strip()}
    if repository:
        json_ld["codeRepository"] = repository
    return {
        "autores": authors,
        "professor": escape(config["professor"]),
        "disciplina": escape(config["disciplina"]),
        "titulo_trabalho": escape(config["titulo"]),
        "tema_trabalho": escape(config["tema"]),
        "filiacao": escape(" · ".join(affiliations)),
        "semestre": f'<p class="affiliation">Semestre letivo {escape(semester)}</p>' if semester else "",
        "metadados": serialize(json_ld),
    }


def repository_links(repository):
    if repository:
        href = escape(repository)
        clone = f"git clone {href}.git precos-combustiveis-brasil\ncd precos-combustiveis-brasil"
        return {
            "botao_repo": f'<a class="button" href="{href}">Repositório GitHub <span class="arrow" aria-hidden="true">↗</span></a>',
            "status_publicacao": "O código e os dados estão vinculados ao repositório informado.",
            "comando_clone": f"<pre><code>{clone}</code></pre>",
            "link_dados": f'<a href="{href}">Ver código, notebook e dados no GitHub</a>.',
        }
    return {
        "botao_repo": '<a class="button" href="#fair">Código e dados <span class="arrow" aria-hidden="true">↓</span></a>',
        "status_publicacao": "A publicação no GitHub Pages está pendente.",
        "comando_clone": "",
        "link_dados": "O README inclui as etapas para cadastrar o endereço do repositório e publicar a pasta <code>docs/</code>.",
    }


def render(config, panel, quality, summary, dados, assets):
    country = quality["Brasil"]
    series = summary["gasolina_brasil"]
    geography = summary["geografia"]
    year = summary["ultimo_ano_completo"]
    ratio = summary["razao_etanol_gasolina"]
    geo_year = dados["anos"][str(year)]
    region_counts = {line["localidade"]: line["meses_ate_70_pct"] for line in ratio["regioes"]}
    repository = config["repositorio_github"].strip().rstrip("/").removesuffix(".git")
    if repository and not re.fullmatch(r"https://github\.com/[\w-]+/[\w.-]+", repository, re.ASCII):
        raise ValueError("Informe em projeto.json o URL do repositório GitHub no formato https://github.com/usuario/repositorio.")
    return {
        **academic_metadata(config, quality, repository),
        **repository_links(repository),
        "inicio_extenso": month_long(country["primeira_referencia"]),
        "fim_extenso": month_long(country["ultima_referencia"]),
        "pico_mes": month_long(series["pico"]["referencia"]),
        "pico_preco": reais(series["pico"]["valor"]),
        "primeiro_preco": reais(series["inicio"]["valor"]),
        "ultimo_preco": reais(series["fim"]["valor"]),
        "dez_preco": reais(series["dezembro"]["valor"]),
        "meses": str(country["meses_observados"]),
        "ufs": str(quality["UF"]["territorios"]),
        "produtos": str(len(PRODUCTS)),
        "ano": str(year),
        "painel_linhas": local_number(len(panel), 0),
        "quarentena": str(quality["UF"]["linhas_quarentena"]),
        "ap_lacunas": str(len(quality["UF"]["meses_ausentes_por_uf"]["AP"])),
        "maior_queda_abs": percent(abs(series["maior_queda"]["valor"])),
        "maior_alta": percent(series["maior_alta"]["valor"]),
        "maior_alta_mes": month_long(series["maior_alta"]["referencia"]),
        "pico_dez_queda_abs": percent(abs(series["variacao_pico_dezembro_pct"])),
        "correlacao": local_number(series["correlacao_etanol_gasolina"], 3),
        "pares_correlacao": str(series["pares_para_correlacao"]),
        "variacoes_validas": str(series["variacoes_validas"]),
        "outliers": str(series["outliers_iqr"]),
        "iqr_inferior": percent(series["limite_inferior_iqr_pct"]),
        "iqr_superior": percent(series["limite_superior_iqr_pct"]),
        "media_nacional": reais(series["media_ultimo_ano"]),
        "maior_regiao": geography["regiao_maior"]["localidade"],
        "maior_regiao_preco": reais(geography["regiao_maior"]["valor"]),
        "menor_regiao": geography["regiao_menor"]["localidade"],
        "menor_regiao_preco": reais(geography["regiao_menor"]["valor"]),
        "amplitude_regional": reais(geography["amplitude_regional"]),
        "maior_uf": geography["uf_maior"]["localidade"],
        "maior_uf_preco": reais(geography["uf_maior"]["valor"]),
        "menor_uf": geography["uf_menor"]["localidade"],
        "menor_uf_preco": reais(geography["uf_menor"]["valor"]),
        "amplitude_ufs": reais(geography["amplitude_ufs"]),
        "mediana_uf": reais(geography["mediana_ufs"]),
        "desvio_uf": reais(geography["desvio_padrao_amostral_ufs"]),
        "iqr_uf": reais(geography["iqr_ufs"]),
        "ratio_br": str(ratio["brasil"]["meses_ate_70_pct"]),
        "ratio_co": str(region_counts["Centro-Oeste"]),
        "ratio_se": str(region_counts["Sudeste"]),
        "ratio_uf_qualquer": str(ratio["ufs_com_algum_mes_no_limiar"]),
        "ratio_uf_baixas": str(ratio["pares_uf_mes_ate_limiar"]),
        "ratio_uf_pares": str(ratio["pares_uf_mes_validos"]),
        "trecho_python": escape(EXCERPT),
        "tabela_inventario": inventory_table(quality),
        "tabela_cobertura": "".join(
            row(
                f"{label} · {unit}",
                *(
                    f'{local_number(report["cobertura"][product]["observados"], 0)} / '
                    f'{local_number(report["linhas_validas"], 0)}'
                    for report in quality.values()
                ),
            )
            for product, (label, unit) in PRODUCTS.items()
        ),
        "tabela_serie": series_table(dados),
        "tabela_geo": "".join(
            row(area["localidade"], reais(area["preco_medio_anual"]))
            for area in geo_year["regioes"]
        ),
        "tabela_ratio": ratio_table(geo_year["razoes"]),
        "tabela_ratio_anual": "".join(
            row(
                line["localidade"],
                f'{line["meses_ate_70_pct"]} / {line["meses_validos"]}',
                percent(line["razao_media_pct"]),
            )
            for line in [ratio["brasil"], *ratio["regioes"]]
        ),
        "opcoes_produto": "".join(
            option(code, name, code == analise.GASOLINA) for code, (name, _) in PRODUCTS.items()
        ),
        "opcoes_ano": "".join(
            option(number, number, str(year) == number) for number in reversed(dados["anos"])
        ),
        "opcoes_regiao": "".join(option(name, name) for name in REGIONS.values()),
        "anp_url": ANP_SERIE,
        "anp_metodo_url": ANP_ROOT,
        "anp_boletim_url": ANP_BOLETIM,
        "sparkline": data_uri(assets / "gasolina_2021_2023.png"),
        "histograma": data_uri(assets / "variacoes_mensais_gasolina.png"),
        "css": (TEMPLATES / "artigo.css").read_text(encoding="utf-8"),
        "javascript": (TEMPLATES / "artigo.js").read_text(encoding="utf-8"),
        "dados_json": serialize(dados),
        "plotly_gzip": b64encode((VENDOR / "plotly-2.30.0-cartesiano.js.gz").read_bytes()).decode("ascii"),
        "plotly_licenca": (VENDOR / "Plotly-LICENSE.txt").read_text(encoding="utf-8"),
    }


def run(processed_dir, docs_dir, config_path):
    panel = load_panel(processed_dir)
    quality = json.loads((processed_dir / "qualidade.json").read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    series = analise.serie_nacional(panel)
    changes = analise.variacoes_nacionais(series)
    diagnostic = analise.diagnostico_variacoes(changes)
    pairs = analise.comparacoes(panel)
    annual = analise.medias_anuais(pairs)
    ratios = analise.frequencia_limiar(pairs)
    years = annual.loc[annual["nivel"].eq("Brasil"), "ano"].astype(int).tolist()
    last_year = max(years)
    summary = analise.metrics(series, changes, diagnostic, annual, ratios, last_year)
    dados = analise.payload(series, pairs, annual, years)

    assets = docs_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    figuras.sparkline(series[analise.GASOLINA], assets / "gasolina_2021_2023.png")
    figuras.histograma_variacoes(diagnostic, assets / "variacoes_mensais_gasolina.png")
    context = render(config, panel, quality, summary, dados, assets)
    template = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    html = re.sub(r"\{\{([a-z0-9_]+)\}\}", lambda match: context[match.group(1)], template)
    (docs_dir / "index.html").write_text(html, encoding="utf-8", newline="\n")

    write_json(processed_dir / "indicadores.json", summary)
    diagnostic.to_csv(
        processed_dir / "variacoes_mensais.csv", date_format="%Y-%m", lineterminator="\n",
    )
    annual.to_csv(processed_dir / "medias_anuais_gasolina.csv", index=False, lineterminator="\n")
    ratios.to_csv(processed_dir / "frequencia_etanol_gasolina.csv", index=False, lineterminator="\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--docs-dir", type=Path, default=ROOT / "docs")
    parser.add_argument("--config", type=Path, default=ROOT / "projeto.json")
    args = parser.parse_args()
    run(args.processed_dir, args.docs_dir, args.config)
    print(f"Artigo gerado em {args.docs_dir / 'index.html'}")
