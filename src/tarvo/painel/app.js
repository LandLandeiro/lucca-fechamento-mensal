(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var D = JSON.parse(document.getElementById("dados").textContent);
  var TELAS = ["visao", "decisoes", "contratado", "notas"];

  // ---- navegação por âncora: #tela ou #notas?id=<ID>
  function lerHash() {
    var h = decodeURIComponent(location.hash.replace(/^#/, ""));
    var partes = h.split("?id=");
    var tela = TELAS.indexOf(partes[0]) >= 0 ? partes[0] : "visao";
    return { tela: tela, id: partes[1] || "" };
  }
  function mostrar() {
    var h = lerHash();
    TELAS.forEach(function (t) {
      var s = document.getElementById(t);
      s.classList.toggle("ativa", t === h.tela);
    });
    document.querySelectorAll(".lateral a").forEach(function (a) {
      if (a.getAttribute("data-tela") === h.tela) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    if (h.id) { document.getElementById("q").value = h.id; buscar(h.id); }
    window.scrollTo(0, 0);
    // o navegador rola até a âncora depois do script: volta ao topo da tela
    window.requestAnimationFrame(function () { window.scrollTo(0, 0); });
  }
  window.addEventListener("load", function () { window.scrollTo(0, 0); });
  window.addEventListener("hashchange", mostrar);

  // ---- Contratado × cobrado: linha de negócio (Checkout/Remessa) e abas que filtram as linhas de verdade
  var linhaAtual = "checkout", filtroAtual = "todos";
  function aplicarFiltro() {
    var tab = document.getElementById(linhaAtual === "remessa" ? "tabela-remessa" : "tabela-lojistas");
    ["tabela-lojistas", "tabela-remessa"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.hidden = el !== tab;
    });
    document.querySelectorAll(".nota-residuo").forEach(function (el) { el.hidden = linhaAtual !== "checkout"; });
    document.querySelectorAll(".nota-remessa").forEach(function (el) { el.hidden = linhaAtual !== "remessa"; });
    tab.querySelectorAll("tbody tr").forEach(function (tr) {
      tr.hidden = !(filtroAtual === "todos" || tr.getAttribute("data-situacao") === filtroAtual);
    });
    document.querySelectorAll(".aba").forEach(function (o) {
      o.setAttribute("aria-selected", o.getAttribute("data-filtro") === filtroAtual ? "true" : "false");
      o.setAttribute("aria-controls", tab.id);
      var q = o.querySelector(".qtd");
      q.textContent = q.getAttribute("data-qtd-" + linhaAtual);
    });
    document.querySelectorAll(".aba-linha").forEach(function (o) {
      o.setAttribute("aria-pressed", o.getAttribute("data-linha") === linhaAtual ? "true" : "false");
    });
  }
  document.querySelectorAll(".aba").forEach(function (b) {
    b.addEventListener("click", function () { filtroAtual = b.getAttribute("data-filtro"); aplicarFiltro(); });
  });
  document.querySelectorAll(".aba-linha").forEach(function (b) {
    b.addEventListener("click", function () { linhaAtual = b.getAttribute("data-linha"); aplicarFiltro(); });
  });

  // ---- rastro
  var COLS = D.rastro.cols, ROWS = D.rastro.rows, C = {};
  COLS.forEach(function (c, i) { C[c] = i; });
  var porSaida = null, porRef = null, porRegra = null;
  function indexar() {
    if (porSaida) return;
    porSaida = {}; porRef = {}; porRegra = {};
    ROWS.forEach(function (r, i) {
      (porSaida[r[C.id_saida]] = porSaida[r[C.id_saida]] || []).push(i);
      var ref = r[C.ref_origem].toUpperCase();
      (porRef[ref] = porRef[ref] || []).push(i);
    });
    Object.keys(D.saidas).forEach(function (id) {
      var k = D.saidas[id].regra;
      if (k) (porRegra[k] = porRegra[k] || []).push(id);
    });
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  // dinheiro sem float: formata a string decimal da saída (ponto) em pt-BR
  function brl(v) {
    if (v === "" || v === null || v === undefined) return "—";
    var s = String(v), neg = s.charAt(0) === "-";
    if (neg) s = s.slice(1);
    var p = s.split("."), int = p[0], dec = ((p[1] || "") + "00").slice(0, 2);
    int = int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (neg ? "−" : "") + "R$ " + int + "," + dec;
  }
  function pct(v) { return v === "" ? "" : String(v).replace(".", ",") + "%"; }
  function badge(status) {
    var cls = { SEI: "st-sei", ASSUMO: "st-assumo", CONFIRMADO: "st-confirmado", PENDENTE: "st-pendente" }[status] || "";
    return status ? '<span class="badge ' + cls + '">' + esc(status) + "</span>" : "";
  }
  function botaoId(id) { return '<button type="button" class="btn-sec" data-ir="' + esc(id) + '">' + esc(id) + "</button>"; }

  function regraDaLinha(r) {
    var m = /regras\.yaml ([a-z_]+(?:\.[a-z_]+)+)/.exec(r[C.nota] || "");
    if (m && D.regras[m[1]]) return m[1];
    return (D.saidas[r[C.id_saida]] || {}).regra || "";
  }

  function cadeia(i) {
    var r = ROWS[i], id = r[C.id_saida], s = D.saidas[id] || {};
    var arq = r[C.arquivo_origem], linha = r[C.linha_arquivo];
    var origem = '<code>' + esc(arq) + (linha ? ":" + esc(linha) : "") + "</code>";
    var detOrig = [r[C.ref_origem], r[C.tipo_lancamento]].filter(Boolean).map(esc).join(" · ");
    if (r[C.valor_bruto]) detOrig += " · bruto " + brl(r[C.valor_bruto]);
    var k = regraDaLinha(r), rg = D.regras[k];
    var regra = k ? "<code>" + esc(k) + "</code> " + badge(rg.status) : '<span class="p-det">sem regra mapeada</span>';
    var detRegra = rg ? esc(rg.fonte) : "";
    var nota = r[C.nota] || "";
    var formula = /round\(|% de Spread/.test(nota);
    // a nota do rastro é a fórmula (divergência, remessa) ou a origem da taxa (planilha, regras.yaml)
    if (nota && !formula && !/^regras\.yaml/.test(nota)) detRegra = esc(nota) + (detRegra ? "<br>" + detRegra : "");
    var calc;
    if (formula) {
      calc = esc(nota) + " = <strong>" + brl(r[C.valor]) + "</strong>";
    } else if (r[C.valor_bruto] && r[C.taxa_contratada_pct] !== undefined && r[C.taxa_contratada_pct] !== "") {
      calc = brl(r[C.valor_bruto]) + " × " + pct(r[C.taxa_contratada_pct]) + " = <strong>" + brl(r[C.valor]) + "</strong>" +
        '<span class="p-det">arredondado no centavo, linha por linha</span>';
    } else {
      calc = "valor da linha: <strong>" + brl(r[C.valor]) + "</strong>" + (nota && !/^regras\.yaml/.test(nota) ? '<span class="p-det">' + esc(nota) + "</span>" : "");
    }
    var fecha = s.confere === null || s.confere === undefined ? "" : (s.confere ? ' <span class="ok">Σ confere</span>' : ' <span class="erro">Σ não confere</span>');
    var destino = botaoId(id) + '<span class="p-det">' + esc(s.arquivo || "") + " · total " + brl(s.reportado !== "" && s.reportado !== undefined ? s.reportado : s.soma) + " em " + (s.linhas || 0) + " linhas" + fecha + "</span>";
    return '<ol class="cadeia">' +
      '<li><span class="p-rot">Origem</span><span class="p-val">' + origem + '</span><span class="p-det">' + detOrig + "</span></li>" +
      '<li><span class="p-rot">Regra</span><span class="p-val">' + regra + '</span><span class="p-det">' + detRegra + "</span></li>" +
      '<li><span class="p-rot">Cálculo</span><span class="p-val">' + calc + "</span></li>" +
      '<li><span class="p-rot">Destino</span><span class="p-val">' + destino + "</span></li></ol>";
  }

  var LIMITE = 25;
  function listarLinhas(idx, todas) {
    var n = todas ? idx.length : Math.min(idx.length, LIMITE);
    var html = idx.slice(0, n).map(cadeia).join("");
    if (idx.length > n) html += '<p><button type="button" class="btn-sec" data-mais="1">Mostrar as ' + idx.length + " linhas</button></p>";
    return html;
  }

  var ultimo = { q: "", idx: [] , cab: "" };
  function buscar(q) {
    indexar();
    q = String(q || "").trim();
    var out = document.getElementById("resultado"), Q = q.toUpperCase(), html = "", idx = [];
    if (!q) { out.innerHTML = ""; return; }
    var idSaida = Object.prototype.hasOwnProperty.call(D.saidas, q) ? q : (Object.prototype.hasOwnProperty.call(D.saidas, Q) ? Q : "");
    if (idSaida) {
      var s = D.saidas[idSaida], p = D.pendencias[idSaida];
      idx = porSaida[idSaida] || [];
      var conf = s.confere === null ? "" : (s.confere ? '<span class="ok">a soma das linhas confere com o número reportado</span>' : '<span class="erro">a soma das linhas não confere</span>');
      var rg = D.regras[s.regra];
      html = '<div class="res-cab"><p><code>' + esc(idSaida) + "</code>" + (p ? " · " + esc(p.titulo) : "") + "</p>" +
        "<p>" + esc(s.arquivo) + ": reportado <strong class=\"num\">" + brl(s.reportado) + "</strong> · Σ de " + s.linhas + " linhas de rastro <strong class=\"num\">" + brl(s.soma) + "</strong> " + conf + "</p>" +
        (rg ? '<p class="meta"><code>' + esc(s.regra) + "</code> " + badge(rg.status) + " " + esc(rg.fonte) + "</p>" : "") +
        (p && !p.soma ? '<p class="meta">não entra no total da decisão</p>' : "") + "</div>";
    } else if (porRef[Q]) {
      idx = porRef[Q];
      html = '<div class="res-cab"><p><code>' + esc(q) + "</code> aparece em " + idx.length + " " + (idx.length === 1 ? "número" : "números") + " da saída</p></div>";
    } else if (porRegra[q]) {
      html = '<div class="res-cab"><p><code>' + esc(q) + "</code> " + badge(D.regras[q].status) + " decide " + porRegra[q].length + " números da saída</p>" +
        '<p class="meta">' + esc(D.regras[q].fonte) + '</p><div class="lista-ids">' + porRegra[q].slice(0, 200).map(botaoId).join("") + "</div></div>";
    } else {
      var sug = Object.keys(D.saidas).concat(Object.keys(porRef)).filter(function (k) { return k.toUpperCase().indexOf(Q) >= 0; }).slice(0, 20);
      html = '<div class="res-cab"><p>Nenhum ID exato para <code>' + esc(q) + "</code>.</p>" +
        (sug.length ? '<p class="meta">Parecidos:</p><div class="lista-ids">' + sug.map(botaoId).join("") + "</div>" : "") + "</div>";
    }
    ultimo = { q: q, idx: idx, cab: html };
    out.innerHTML = html + listarLinhas(idx, false);
  }

  document.getElementById("busca").addEventListener("submit", function (e) {
    e.preventDefault();
    var q = document.getElementById("q").value.trim();
    history.replaceState(null, "", "#notas" + (q ? "?id=" + encodeURIComponent(q) : ""));
    buscar(q);
  });
  document.getElementById("notas").addEventListener("click", function (e) {
    var b = e.target.closest("[data-ir],[data-mais]");
    if (!b) return;
    if (b.hasAttribute("data-mais")) {
      document.getElementById("resultado").innerHTML = ultimo.cab + listarLinhas(ultimo.idx, true);
      return;
    }
    var id = b.getAttribute("data-ir");
    document.getElementById("q").value = id;
    history.replaceState(null, "", "#notas?id=" + encodeURIComponent(id));
    buscar(id);
  });

  // exemplos tirados do próprio rastro (um por tipo de ID)
  (function () {
    var vistos = {}, ex = [];
    function tipoId(s) {
      var m = /^([A-Z]+-?)/.exec(s);
      return m ? m[1] : s;
    }
    ROWS.forEach(function (r) {
      [r[C.id_saida], r[C.ref_origem]].forEach(function (v) {
        var t = tipoId(v);
        if (!vistos[t] && ex.length < 8) { vistos[t] = 1; ex.push(v); }
      });
    });
    document.getElementById("exemplos").innerHTML = ex.length ? "Exemplos: " + ex.map(botaoId).join("") : "";
  })();

  mostrar();
})();
