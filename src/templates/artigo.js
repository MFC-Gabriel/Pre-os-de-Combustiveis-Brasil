"use strict";

const byId = (id) => document.getElementById(id);
const dados = JSON.parse(byId("dados-artigo").textContent);
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const valor = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
const pct = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
const meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const regioes = {
  "Centro-Oeste": "#167567",
  Nordeste: "#a44f32",
  Norte: "#496f92",
  Sudeste: "#755293",
  Sul: "#62634a",
};
const plotConfig = { displayModeBar: false, responsive: true, scrollZoom: false };
const grid = "#e0e8e3";

function mesAno(data) {
  return `${data.slice(5, 7)}/${data.slice(0, 4)}`;
}

function formata(x, formatter, suffix = "") {
  return x === null || x === undefined ? "—" : formatter.format(x) + suffix;
}

function linha(cells, colsNumericas) {
  const tr = document.createElement("tr");
  for (const [i, value] of cells.entries()) {
    const cell = document.createElement(i === 0 ? "th" : "td");
    if (i === 0) {
      cell.scope = "row";
    }
    if (i >= colsNumericas) {
      cell.className = "num";
    }
    cell.textContent = value;
    tr.append(cell);
  }
  return tr;
}

function preencheTabela(id, linhas) {
  const fragment = document.createDocumentFragment();
  for (const cells of linhas) {
    fragment.append(linha(cells, 1));
  }
  byId(id).replaceChildren(fragment);
}

function chartLayout(height, margin) {
  return {
    height,
    margin,
    font: { family: "Roboto, Arial, sans-serif", size: 12, color: "#314743" },
    paper_bgcolor: "#ffffff",
    plot_bgcolor: "#ffffff",
    separators: ",.",
    dragmode: false,
    hoverlabel: { bgcolor: "#17342d", font: { color: "#ffffff" }, bordercolor: "#17342d" },
  };
}

function eixo(titulo = "") {
  return {
    title: { text: titulo, font: { size: 12 } },
    gridcolor: grid,
    zeroline: false,
    fixedrange: true,
    tickfont: { size: 11 },
  };
}

async function desenhaSerie() {
  const product = dados.nacional[byId("essencia").value];
  const periodo = byId("serie-periodo").value;
  const datas = [];
  const mensal = [];
  const movel = [];
  for (const [i, data] of dados.referencias.entries()) {
    const ano = Number(data.slice(0, 4));
    if (periodo !== "todos" && (ano < Number(periodo) || ano >= Number(periodo) + 10)) {
      continue;
    }
    datas.push(data);
    mensal.push(product.mensal[i]);
    movel.push(product.movel[i]);
  }

  const pontos = datas
    .map((data, i) => [mesAno(data), formata(mensal[i], valor), formata(movel[i], valor)]);
  preencheTabela("serie-tabela", pontos);
  byId("serie-unidade").textContent = `Preço médio (${product.unidade})`;
  const n = mensal.filter((v) => v !== null).length;
  const status = byId("serie-status");
  status.textContent = `${n} de ${datas.length} meses no recorte com preço disponível.`;
  const el = byId("serie-plot");
  const compact = el.clientWidth < 500;
  const unit = product.unidade.replace(" de 13 kg", "");
  const layout = {
    ...chartLayout(compact ? 280 : 343, { l: compact ? 65 : 78, r: 18, t: 14, b: 43 }),
    xaxis: {
      ...eixo(),
      type: "date",
      tickformat: periodo === "2020" ? "%m/%Y" : "%Y",
      nticks: compact ? 4 : 7,
      showgrid: false,
    },
    yaxis: { ...eixo(unit), rangemode: "tozero", nticks: 6 },
    showlegend: false,
  };
  if (n === 0) {
    Plotly.purge(el);
    el.replaceChildren();
    return;
  }
  const series = [
    { data: mensal, name: "Média mensal", color: "#1b7467", dash: "solid", width: 2.6 },
    { data: movel, name: "Média móvel", color: "#a75432", dash: "dash", width: 2.0 },
  ];
  const traces = series.map(({ data, name, color, dash, width }) => ({
    type: "scatter", mode: "lines",
    x: datas, y: data, name, connectgaps: false,
    line: { color, dash, width },
    customdata: datas.map((date, i) => [mesAno(date), formata(data[i], valor)]),
    hovertemplate: `%{customdata[0]}<br>${name} %{customdata[1]} ${product.unidade}<extra></extra>`,
  }));
  await Plotly.react(el, traces, layout, plotConfig);
}

async function desenhaGeo() {
  const ano = byId("geo-ano").value;
  const nivel = byId("geo-nivel").value;
  const dadosAno = dados.anos[ano];
  const areas = dadosAno[nivel];
  const nomes = areas.map((area) => nivel === "ufs" ? area.uf : area.localidade);
  const precos = areas.map((area) => area.preco_medio_anual);
  const referencia = dadosAno.media_brasil;
  const min = Math.min(...precos, referencia);
  const max = Math.max(...precos, referencia);
  const padding = Math.max((max - min) * 0.12, 0.035);
  const el = byId("geo-plot");
  const compact = el.clientWidth < 500;
  const trace = {
    type: "scatter", mode: "markers",
    y: nomes, x: precos,
    marker: { color: "#1b7467", size: nivel === "ufs" ? 8 : 12 },
    customdata: areas.map((area) => [area.localidade, formata(area.preco_medio_anual, moeda)]),
    hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]} por litro<extra></extra>",
  };
  const layout = {
    ...chartLayout(nivel === "ufs" ? 70 + areas.length * 23 : 250, { l: 100, r: 19, t: 14, b: 52 }),
    xaxis: { ...eixo("R$/L"), range: [min - padding, max + padding], tickformat: ".2f", nticks: compact ? 4 : 7 },
    yaxis: { ...eixo(), type: "category", categoryorder: "array", categoryarray: nomes, autorange: "reversed" },
    shapes: [{
      type: "line", x0: referencia, x1: referencia, xref: "x", y0: 0, y1: 1, yref: "paper",
      line: { color: "#ac5534", width: 1.4, dash: "dash" }, layer: "below",
    }],
    showlegend: false,
  };
  preencheTabela("geo-tabela", areas.map((a) => [a.localidade, formata(a.preco_medio_anual, moeda)]));
  byId("geo-status").textContent = `Brasil em ${ano} · ${formata(referencia, moeda)} por litro. ${areas.length} territórios com 12 meses.`;
  await Plotly.react(el, [trace], layout, plotConfig);
}

function preencheTabelaRazao(selected, sources) {
  const head = document.createElement("thead");
  const headers = document.createElement("tr");
  for (const value of ["Mês", ...selected]) {
    const col = document.createElement("th");
    col.scope = "col";
    col.textContent = value;
    if (value !== "Mês") {
      col.className = "num";
    }
    headers.append(col);
  }
  head.append(headers);
  const rows = document.createElement("tbody");
  for (const [i, mes] of meses.entries()) {
    rows.append(linha([mes, ...selected.map((nome) => formata(sources[nome][i], pct, "%"))], 1));
  }
  byId("ratio-tabela").replaceChildren(head, rows);
}

async function desenhaRazao() {
  const ano = byId("ratio-ano").value;
  const selected = byId("ratio-territorio").value;
  const nomes = selected === "regioes" ? Object.keys(regioes) : [selected];
  const razoes = dados.anos[ano].razoes;
  const threshold = dados.limiar_pct;
  const el = byId("ratio-plot");
  const compact = el.clientWidth < 500;
  const simbolos = ["circle", "square", "diamond", "triangle-up", "cross"];
  const traces = nomes.map((nome, i) => ({
    type: "scatter",
    mode: "lines+markers",
    x: meses,
    y: razoes[nome],
    name: nome,
    line: { color: regioes[nome] ?? "#245c54", width: 2.1 },
    marker: { symbol: simbolos[i], size: 6 },
    customdata: razoes[nome].map((v) => formata(v, pct, "%")),
    hovertemplate: `<b>${nome}</b><br>%{x}/${ano} · %{customdata}<extra></extra>`,
  }));
  preencheTabelaRazao(nomes, razoes);
  const valores = traces.flatMap((trace) => trace.y).filter((v) => v !== null);
  const low = Math.min(threshold, ...valores) - 3;
  const high = Math.max(threshold, ...valores) + 3;
  const status = byId("ratio-status");
  status.textContent = `Ano selecionado: ${ano}. Referência: 70%.`;
  const layout = {
    ...chartLayout(compact ? 330 : 345, { l: 59, r: 19, t: 12, b: nomes.length > 1 ? 72 : 47 }),
    xaxis: { ...eixo(), type: "category", categoryorder: "array", categoryarray: meses, showgrid: false },
    yaxis: { ...eixo("Razão de preços"), ticksuffix: "%", range: [low, high], nticks: 6 },
    legend: { orientation: "h", y: -0.19, yanchor: "top", font: { size: 10 } },
    showlegend: nomes.length > 1,
    shapes: [{
      type: "line", x0: 0, x1: 1, xref: "paper", y0: threshold, y1: threshold, yref: "y",
      line: { color: "#405955", dash: "dash", width: 1.25 }, layer: "below",
    }],
  };
  if (compact) {
    layout.xaxis.tickvals = meses.filter((_, i) => i % 2 === 0);
  }
  await Plotly.react(el, traces, layout, plotConfig);
}

async function carregaPlotly() {
  const encoded = byId("plotly-fonte").textContent.trim();
  const compressed = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream("gzip"));
  const source = await new Response(stream).text();
  const script = document.createElement("script");
  script.textContent = source;
  document.head.append(script);
  if (!globalThis.Plotly) {
    throw new Error("Biblioteca de gráficos indisponível.");
  }
  byId("plotly-fonte").remove();
}

async function ativaGraficos() {
  const configuracoes = [
    ["serie", ["essencia", "serie-periodo"], desenhaSerie],
    ["geo", ["geo-ano", "geo-nivel"], desenhaGeo],
    ["ratio", ["ratio-ano", "ratio-territorio"], desenhaRazao],
  ];
  const falha = (nome, error) => {
    byId(`${nome}-status`).textContent = "O gráfico não carregou. Os valores estão disponíveis na tabela.";
    console.error(error);
  };
  try {
    await carregaPlotly();
  } catch (error) {
    for (const [nome] of configuracoes) {
      falha(nome, error);
    }
    return;
  }
  for (const [nome, seletores, desenha] of configuracoes) {
    try {
      await desenha();
      byId(`${nome}-controles`).hidden = false;
      if (nome === "serie") {
        byId("serie-legenda").hidden = false;
      }
      byId(`${nome}-status`).setAttribute("aria-live", "polite");
      for (const id of seletores) {
        byId(id).addEventListener("change", () => desenha().catch((error) => falha(nome, error)));
      }
    } catch (error) {
      falha(nome, error);
    }
  }
}

ativaGraficos();
