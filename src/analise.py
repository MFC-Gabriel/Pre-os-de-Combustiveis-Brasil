"""Calcula indicadores e tabelas para as três perguntas de pesquisa."""

import numpy as np
import pandas as pd

GASOLINA = "gasolina_comum"
ETANOL = "etanol_hidratado"
LIMIAR = 0.70


def serie_nacional(panel):
    return (
        panel.loc[panel["nivel"].eq("Brasil")]
        .pivot(index="referencia", columns="combustivel", values="preco_medio")
        .sort_index()
        .asfreq("MS")
    )


def variacoes_nacionais(series):
    return series[[GASOLINA, ETANOL]].pct_change(fill_method=None).mul(100)


def diagnostico_variacoes(changes):
    gasoline = changes[GASOLINA].dropna()
    q1, q3 = gasoline.quantile([0.25, 0.75])
    iqr = q3 - q1
    inferior, superior = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = gasoline.lt(inferior) | gasoline.gt(superior)
    return pd.DataFrame({
        "gasolina_var_pct": gasoline,
        "etanol_var_pct": changes[ETANOL].reindex(gasoline.index),
        "limite_inferior_pct": inferior,
        "limite_superior_pct": superior,
        "fora_dos_limites_iqr": outliers,
    })


def comparacoes(panel):
    gasolina_etanol = panel.loc[panel["combustivel"].isin([GASOLINA, ETANOL])].copy()
    gasolina_etanol["uf"] = gasolina_etanol["uf"].fillna("")
    gasolina_etanol["regiao"] = gasolina_etanol["regiao"].fillna("")
    pares = (
        gasolina_etanol.pivot(
            index=["nivel", "localidade", "regiao", "uf", "ano", "mes", "referencia"],
            columns="combustivel", values="preco_medio",
        )
        .reset_index()
    )
    pares["razao_etanol_gasolina"] = pares[ETANOL].div(pares[GASOLINA])
    return pares


def medias_anuais(pares):
    medias = (
        pares.groupby(["ano", "nivel", "localidade", "regiao", "uf"], sort=True)[GASOLINA]
        .agg(preco_medio_anual="mean", meses="count")
        .reset_index()
    )
    return medias.loc[medias["meses"].eq(12)].sort_values(
        ["ano", "nivel", "preco_medio_anual", "localidade"],
        ascending=[True, True, False, True],
        ignore_index=True,
    )


def frequencia_limiar(pares):
    observed = pares.dropna(subset=["razao_etanol_gasolina"]).copy()
    observed["ate_limiar"] = observed["razao_etanol_gasolina"].round(12).le(LIMIAR)
    return (
        observed.groupby(["ano", "nivel", "localidade", "regiao", "uf"], sort=True)
        .agg(
            meses_validos=("razao_etanol_gasolina", "size"),
            meses_ate_70_pct=("ate_limiar", "sum"),
            razao_media=("razao_etanol_gasolina", "mean"),
        )
        .reset_index()
    )


def metrics(series, changes, iqr_report, annual, fractions, latest_year):
    gasoline = series[GASOLINA].dropna()
    peak = gasoline.idxmax()
    year = gasoline.loc[str(latest_year)]
    trough = year.idxmin()
    december = year.iloc[-1]
    extrema = iqr_report["gasolina_var_pct"]
    max_change, min_change = extrema.idxmax(), extrema.idxmin()

    last_annual = annual.loc[annual["ano"].eq(latest_year)]
    areas = last_annual.loc[last_annual["nivel"].eq("Região")]
    states = last_annual.loc[last_annual["nivel"].eq("UF")]
    state_prices = states["preco_medio_anual"]
    counts = fractions.loc[fractions["ano"].eq(latest_year)]
    national_count = counts.loc[counts["nivel"].eq("Brasil")].iloc[0]
    region_counts = counts.loc[counts["nivel"].eq("Região")]
    state_counts = counts.loc[counts["nivel"].eq("UF")]
    national_row = last_annual.loc[last_annual["nivel"].eq("Brasil")].iloc[0]
    comparable_pairs = changes.dropna()
    return {
        "ultimo_ano_completo": latest_year,
        "gasolina_brasil": {
            "inicio": gasolina_ponto(gasoline, gasoline.index[0]),
            "pico": gasolina_ponto(gasoline, peak),
            "menor_no_ultimo_ano": gasolina_ponto(gasoline, trough),
            "dezembro": gasolina_ponto(gasoline, year.index[-1]),
            "fim": gasolina_ponto(gasoline, gasoline.index[-1]),
            "variacao_pico_dezembro_pct": float((december / gasoline.loc[peak] - 1) * 100),
            "media_ultimo_ano": float(national_row["preco_medio_anual"]),
            "maior_alta": gasolina_ponto(extrema, max_change),
            "maior_queda": gasolina_ponto(extrema, min_change),
            "limite_inferior_iqr_pct": float(iqr_report["limite_inferior_pct"].iloc[0]),
            "limite_superior_iqr_pct": float(iqr_report["limite_superior_pct"].iloc[0]),
            "outliers_iqr": int(iqr_report["fora_dos_limites_iqr"].sum()),
            "variacoes_validas": len(iqr_report),
            "correlacao_etanol_gasolina": float(
                comparable_pairs[GASOLINA].corr(comparable_pairs[ETANOL])
            ),
            "pares_para_correlacao": len(comparable_pairs),
        },
        "geografia": {
            "regioes": len(areas),
            "ufs": len(states),
            "regiao_maior": area_ponto(areas.iloc[0]),
            "regiao_menor": area_ponto(areas.iloc[-1]),
            "amplitude_regional": float(
                areas["preco_medio_anual"].iloc[0] - areas["preco_medio_anual"].iloc[-1]
            ),
            "uf_maior": area_ponto(states.iloc[0]),
            "uf_menor": area_ponto(states.iloc[-1]),
            "amplitude_ufs": float(state_prices.max() - state_prices.min()),
            "mediana_ufs": float(state_prices.median()),
            "desvio_padrao_amostral_ufs": float(state_prices.std(ddof=1)),
            "iqr_ufs": float(state_prices.quantile(0.75) - state_prices.quantile(0.25)),
        },
        "razao_etanol_gasolina": {
            "limiar": LIMIAR,
            "brasil": frequencia_ponto(national_count),
            "regioes": [frequencia_ponto(row) for _, row in region_counts.iterrows()],
            "ufs_com_algum_mes_no_limiar": int((state_counts["meses_ate_70_pct"] > 0).sum()),
            "pares_uf_mes_ate_limiar": int(state_counts["meses_ate_70_pct"].sum()),
            "pares_uf_mes_validos": int(state_counts["meses_validos"].sum()),
        },
    }


def gasolina_ponto(series, timestamp):
    return {"referencia": timestamp.strftime("%Y-%m"), "valor": float(series.loc[timestamp])}


def area_ponto(row):
    return {"localidade": row["localidade"], "valor": float(row["preco_medio_anual"])}


def frequencia_ponto(row):
    return {
        "localidade": row["localidade"],
        "meses_validos": int(row["meses_validos"]),
        "meses_ate_70_pct": int(row["meses_ate_70_pct"]),
        "razao_media_pct": float(100 * row["razao_media"]),
    }


def payload(series, pairs, annual, complete_years):
    from .etl import PRODUCTS

    rolling = series.rolling(window=12, min_periods=12).mean()

    def array(values):
        return [float(value) if np.isfinite(value) else None for value in values]

    by_year = {}
    for year in complete_years:
        prices = annual.loc[annual["ano"].eq(year)]
        regional = prices.loc[prices["nivel"].eq("Região")]
        states = prices.loc[prices["nivel"].eq("UF")]
        ratios = pairs.loc[pairs["ano"].eq(year) & pairs["nivel"].ne("UF")]
        ratios = ratios.pivot(index="mes", columns="localidade", values="razao_etanol_gasolina")
        by_year[str(year)] = {
            "media_brasil": float(prices.loc[prices["nivel"].eq("Brasil"), "preco_medio_anual"].iloc[0]),
            "regioes": regional[["localidade", "preco_medio_anual"]].to_dict("records"),
            "ufs": states[["localidade", "uf", "regiao", "preco_medio_anual"]].to_dict("records"),
            "razoes": {name: array(ratios[name].mul(100)) for name in ratios.columns},
        }

    return {
        "referencias": series.index.strftime("%Y-%m-%d").tolist(),
        "nacional": {
            product: {
                "rotulo": name,
                "unidade": unit,
                "mensal": array(series[product]),
                "movel": array(rolling[product]),
            }
            for product, (name, unit) in PRODUCTS.items()
        },
        "anos": by_year,
        "limiar_pct": 100 * LIMIAR,
    }
