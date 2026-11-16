"""Valida os três CSV brutos e exporta um painel mensal auditável."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {
    "gasolina_comum": ("Gasolina comum", "R$/L"),
    "gasolina_aditivada": ("Gasolina aditivada", "R$/L"),
    "etanol_hidratado": ("Etanol hidratado", "R$/L"),
    "oleo_diesel": ("Óleo diesel", "R$/L"),
    "oleo_diesel_s10": ("Óleo diesel S10", "R$/L"),
    "gas_cozinha_glp": ("GLP P13", "R$/botijão de 13 kg"),
    "gas_natural_veicular_gnv": ("Gás natural veicular", "R$/m³"),
}
REGIONS = {
    "CENTRO OESTE": "Centro-Oeste",
    "NORDESTE": "Nordeste",
    "NORTE": "Norte",
    "SUDESTE": "Sudeste",
    "SUL": "Sul",
}
STATES = {
    "ACRE": ("AC", "Acre", "NORTE"),
    "ALAGOAS": ("AL", "Alagoas", "NORDESTE"),
    "AMAPA": ("AP", "Amapá", "NORTE"),
    "AMAZONAS": ("AM", "Amazonas", "NORTE"),
    "BAHIA": ("BA", "Bahia", "NORDESTE"),
    "CEARA": ("CE", "Ceará", "NORDESTE"),
    "DISTRITO FEDERAL": ("DF", "Distrito Federal", "CENTRO OESTE"),
    "ESPIRITO SANTO": ("ES", "Espírito Santo", "SUDESTE"),
    "GOIAS": ("GO", "Goiás", "CENTRO OESTE"),
    "MARANHAO": ("MA", "Maranhão", "NORDESTE"),
    "MATO GROSSO": ("MT", "Mato Grosso", "CENTRO OESTE"),
    "MATO GROSSO DO SUL": ("MS", "Mato Grosso do Sul", "CENTRO OESTE"),
    "MINAS GERAIS": ("MG", "Minas Gerais", "SUDESTE"),
    "PARA": ("PA", "Pará", "NORTE"),
    "PARAIBA": ("PB", "Paraíba", "NORDESTE"),
    "PARANA": ("PR", "Paraná", "SUL"),
    "PERNAMBUCO": ("PE", "Pernambuco", "NORDESTE"),
    "PIAUI": ("PI", "Piauí", "NORDESTE"),
    "RIO DE JANEIRO": ("RJ", "Rio de Janeiro", "SUDESTE"),
    "RIO GRANDE DO NORTE": ("RN", "Rio Grande do Norte", "NORDESTE"),
    "RIO GRANDE DO SUL": ("RS", "Rio Grande do Sul", "SUL"),
    "RONDONIA": ("RO", "Rondônia", "NORTE"),
    "RORAIMA": ("RR", "Roraima", "NORTE"),
    "SANTA CATARINA": ("SC", "Santa Catarina", "SUL"),
    "SAO PAULO": ("SP", "São Paulo", "SUDESTE"),
    "SERGIPE": ("SE", "Sergipe", "NORDESTE"),
    "TOCANTINS": ("TO", "Tocantins", "NORTE"),
}
FILES = (
    ("combustiveis-brasil.csv", "Brasil", ()),
    ("combustiveis-regioes.csv", "Região", ("regiao",)),
    ("combustiveis-estados.csv", "UF", ("regiao", "estado")),
)
DATE_COLUMNS = ("referencia", "ano", "mes")
PRICE_FIELDS = {"avg": "preco_medio", "min": "preco_minimo", "max": "preco_maximo"}


def write_json(path, content):
    text = json.dumps(content, ensure_ascii=False, indent=2, allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def require(condition, path, message):
    if not condition:
        raise ValueError(f"{path.name}: {message}")


def read_table(path, level, geography):
    price_columns = [
        f"{product}_preco_revenda_{suffix}"
        for product in PRODUCTS
        for suffix in PRICE_FIELDS
    ]
    keys = [*DATE_COLUMNS, *geography]
    source = pd.read_csv(
        path, encoding="utf-8", sep=",", decimal=".",
        dtype="string", keep_default_na=False,
    )
    require(
        list(source.columns) == keys + price_columns,
        path, "o cabeçalho difere do esquema documentado.",
    )

    dimensions = source[keys].apply(lambda column: column.str.strip())
    invalid = dimensions.eq("").any(axis=1) | dimensions.isna().any(axis=1)
    quarantine = source.loc[invalid].copy()
    quarantine.insert(0, "motivo", "Chave temporal ou geográfica incompleta")
    quarantine.insert(0, "linha_csv", quarantine.index + 2)
    quarantine.insert(0, "arquivo", path.name)

    valid = dimensions.loc[~invalid].copy()
    require(not valid.empty, path, "nenhuma chave utilizável.")
    valid["referencia"] = pd.to_datetime(valid["referencia"], format="%Y-%m", errors="raise")
    year_month = valid[["ano", "mes"]].apply(pd.to_numeric, errors="raise")
    require(
        year_month["ano"].eq(valid["referencia"].dt.year).all()
        and year_month["mes"].eq(valid["referencia"].dt.month).all(),
        path, "há divergência entre referência, ano e mês.",
    )
    valid[["ano", "mes"]] = year_month.astype("int32")
    location_key = {"Brasil": [], "Região": ["regiao"], "UF": ["estado"]}[level]
    require(
        not valid.duplicated(["referencia", *location_key]).any(),
        path, "há chaves de mês e território duplicadas.",
    )

    valid["nivel"] = level
    valid["uf"] = pd.NA
    if level == "UF":
        region_of = {key: value[2] for key, value in STATES.items()}
        require(
            valid["estado"].map(region_of).eq(valid["regiao"]).fillna(False).all(),
            path, "há UF desconhecida ou atribuída a uma região incompatível.",
        )
        valid["uf"] = valid["estado"].map({key: value[0] for key, value in STATES.items()})
        valid["localidade"] = valid["estado"].map(
            {key: value[1] for key, value in STATES.items()}
        )
    elif level == "Região":
        require(valid["regiao"].isin(REGIONS).all(), path, "há região desconhecida.")
        valid["localidade"] = valid["regiao"].map(REGIONS)
    else:
        valid["regiao"] = pd.NA
        valid["localidade"] = "Brasil"
    if level != "Brasil":
        valid["regiao"] = valid["regiao"].map(REGIONS)

    valid["arquivo_origem"] = path.name
    valid["linha_csv"] = valid.index + 2
    price_text = source.loc[valid.index, price_columns]
    prices = price_text.mask(price_text.eq("")).apply(pd.to_numeric, errors="raise")
    active_prices = prices.stack().to_numpy(dtype="float64")
    require(
        np.isfinite(active_prices).all() and (active_prices > 0).all(),
        path, "há preço não positivo ou não finito.",
    )

    dimensions = [
        "referencia", "ano", "mes", "nivel", "localidade", "regiao", "uf",
        "arquivo_origem", "linha_csv",
    ]
    parts = []
    coverage = {}
    for product, (_, unit) in PRODUCTS.items():
        rename = {f"{product}_preco_revenda_{key}": name for key, name in PRICE_FIELDS.items()}
        triplet = prices[list(rename)].rename(columns=rename)
        observed = triplet["preco_medio"].notna()
        valid_prices = triplet.loc[observed]
        require(
            triplet.notna().sum(axis=1).isin([0, 3]).all()
            and valid_prices["preco_minimo"].le(valid_prices["preco_medio"]).all()
            and valid_prices["preco_medio"].le(valid_prices["preco_maximo"]).all(),
            path, f"há um trio mínimo/média/máximo inconsistente para {product}.",
        )
        parts.append(valid[dimensions].join(triplet).assign(combustivel=product, unidade=unit))
        dates = valid.loc[observed, "referencia"].dt.strftime("%Y-%m")
        coverage[product] = {
            "observados": int(observed.sum()),
            "ausentes": int((~observed).sum()),
            "primeira_referencia": dates.min() if len(dates) else None,
            "ultima_referencia": dates.max() if len(dates) else None,
        }

    dates = pd.DatetimeIndex(valid["referencia"].unique()).sort_values()
    full_index = pd.date_range(dates.min(), dates.max(), freq="MS")
    metrics = {
        "arquivo": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "linhas_brutas": len(source),
        "linhas_validas": len(valid),
        "linhas_quarentena": len(quarantine),
        "territorios": int(valid["localidade"].nunique()),
        "primeira_referencia": dates.min().strftime("%Y-%m"),
        "ultima_referencia": dates.max().strftime("%Y-%m"),
        "meses_observados": len(dates),
        "meses_ausentes": full_index.difference(dates).strftime("%Y-%m").tolist(),
        "cobertura": coverage,
    }
    if level == "UF":
        metrics["meses_ausentes_por_uf"] = {
            uf: dates.difference(pd.DatetimeIndex(group["referencia"])).strftime("%Y-%m").tolist()
            for uf, group in valid.groupby("uf", sort=True)
        }
    return pd.concat(parts, ignore_index=True), quarantine, metrics


def run(raw_dir, output_dir):
    tables, quarantines, quality = [], [], {}
    for filename, level, geography in FILES:
        table, quarantine, metrics = read_table(raw_dir / filename, level, geography)
        tables.append(table)
        quarantines.append(quarantine)
        quality[level] = metrics

    panel = pd.concat(tables, ignore_index=True).sort_values(
        ["nivel", "localidade", "referencia", "combustivel"], ignore_index=True,
    )
    panel = panel[[
        "referencia", "ano", "mes", "nivel", "localidade", "regiao", "uf",
        "combustivel", "unidade", "preco_medio", "preco_minimo", "preco_maximo",
        "arquivo_origem", "linha_csv",
    ]]
    # Todas as validações dos três arquivos precedem a escrita.
    output_dir.mkdir(parents=True, exist_ok=True)
    csv = panel.to_csv(index=False, date_format="%Y-%m", lineterminator="\n")
    (output_dir / "precos_mensais.csv.gz").write_bytes(
        gzip.compress(csv.encode("utf-8"), compresslevel=9, mtime=0)
    )
    pd.concat(quarantines, ignore_index=True, sort=False).to_csv(
        output_dir / "linhas_em_quarentena.csv", index=False, lineterminator="\n",
    )
    write_json(output_dir / "qualidade.json", quality)
    return panel, quality


def load_panel(output_dir=ROOT / "data" / "processed"):
    panel = pd.read_csv(output_dir / "precos_mensais.csv.gz", dtype={"uf": "string"})
    panel["referencia"] = pd.to_datetime(panel["referencia"], format="%Y-%m", errors="raise")
    return panel


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args()
    panel, quality = run(args.raw_dir, args.output_dir)
    for level, report in quality.items():
        print(f"{level}: {report['linhas_validas']} válidas, {report['linhas_quarentena']} em quarentena")
    print(f"Painel: {len(panel)} linhas mês × território × combustível")
