"""Validador da saída: recusa total que não fecha.

Responsabilidade: conferir os CSVs escritos (colunas obrigatórias, separador, ponto
decimal, datas ISO, CNPJ com 14 dígitos e DV válido, enums) e que a soma do
`rastro.csv` por `id_saida` bate com o número reportado em cada arquivo. Com
`refs_esperadas`, confere também que cada linha de origem aparece no rastro exatamente
uma vez (nada some, nada conta duas vezes).

Lê o que foi escrito em disco, não os objetos em memória: valida o que vai ser entregue.
Qualquer achado é ERRO (a CLI sai com código 1).
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from tarvo.formatos import cnpj_valido
from tarvo.saida.escritor import COLUNAS

_RE_DINHEIRO = re.compile(r"^-?\d+\.\d{2}$")
_RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COL_DINHEIRO = {"comissao_brl", "diferenca_brl", "valor_brl", "valor"}
_COL_CNPJ = {"cnpj", "tomador_cnpj"}
_ENUMS = {
    "linha_negocio": {"CHECKOUT", "REMESSA"},
    "banco": {"AURORA", "MERIDIANO"},
    "metodo": {"REGRA", "IA", "HUMANO"},
}
# arquivo → coluna com o número que o rastro tem que reproduzir
_TOTAL_POR_ARQUIVO = {
    "comissoes_por_lojista.csv": "comissao_brl",
    "divergencias_taxa.csv": "diferenca_brl",
    "notas_a_emitir.csv": "valor_brl",
    "lancamentos_classificados.csv": "valor",
    "pendencias.csv": "valor_brl",
}


def _ler(caminho: Path, erros: list[str]) -> list[dict] | None:
    with open(caminho, encoding="utf-8", newline="") as f:
        primeira = f.readline()
        if ";" not in primeira:
            erros.append(f"{caminho.name}: cabeçalho sem separador ';'")
            return None
        f.seek(0)
        leitor = csv.DictReader(f, delimiter=";")
        faltando = [c for c in COLUNAS[caminho.name] if c not in (leitor.fieldnames or [])]
        if faltando:
            erros.append(f"{caminho.name}: faltam colunas obrigatórias {faltando}")
            return None
        return list(leitor)


# onde cada linha de origem tem que aparecer exatamente uma vez: comissão, pendência ou
# exclusão anotada (EXC-…, sem número reportado). DIV-… reaponta linhas e não conta.
PREFIXOS_COBERTURA = ("COM-", "PEN-", "EXC-")
PREFIXO_EXCLUSAO = "EXC-"
# pendências derivadas de um número já calculado: reapontam linhas que já têm destino
PREFIXOS_DERIVADOS = ("PEN-NF_NEGATIVA-", "PEN-CONFERENCIA_REPASSE-", "PEN-EXCESSO_REMESSA-", "PEN-APORTE_",
                      "PEN-CONTESTACAO_PONTE-", "PEN-DIVERGENCIA_CHECKOUT-", "PEN-NOTA_BLOQUEADA-",
                      "PEN-ALERTA_ANTECIPACAO-", "PEN-CADASTRO_REMESSA-")


def _d(texto: str | None) -> Decimal:
    """Número da saída para as checagens de soma; fora do formato conta 0 (o erro de formato já é reportado)."""
    return Decimal(texto) if _RE_DINHEIRO.match(texto or "") else Decimal("0")


def _destino(id_saida: str) -> bool:
    return id_saida.startswith(PREFIXOS_COBERTURA) and not id_saida.startswith(PREFIXOS_DERIVADOS)


def validar_saida(
    pasta: Path,
    refs_esperadas: dict[str, set[tuple[str, int]]] | None = None,
    fonte_orbe: dict[str, dict[str, tuple]] | None = None,
    modo_checkout: str | None = None,
    spread_ponte: dict[str, dict[tuple[str, int], Decimal]] | None = None,
    spread_declarado: Decimal | None = None,
    refs_extratos: dict[str, set[tuple[str, int]]] | None = None,
    saldos_extratos: dict[str, tuple[Decimal | None, Decimal | None]] | None = None,
    contas_lancaveis: set[str] | None = None,
    fontes_rastro: dict[str, set[tuple[str, int]]] | None = None,
) -> list[str]:
    """Devolve a lista de erros encontrados (vazia = saída válida).

    - `refs_esperadas` {arquivo: {(ref_origem, linha)}}: cada linha de origem aparece
      exatamente uma vez no rastro de um COM-…, PEN-… ou EXC-… (a linha distingue cópias
      com o mesmo Nº de operação).
    - `fonte_orbe` {arquivo: {ref: (valor_taxa, valor_bruto, taxa_aplicada fração)}} lido da fonte,
      com `modo_checkout` (modo de arredondamento do Decimal): conservação do checkout com resíduo
      de truncamento (ver `_conservacao_checkout`); toda divergência aponta só linhas de comissão.
    - `spread_ponte` {arquivo: {(Nº, linha): Spread R$}}: conservação da remessa (ver
      `_conservacao_remessa`); `spread_declarado` = "Spread total R$" do próprio relatório.
    - `fontes_rastro` {arquivo: {(ref_origem, linha)}} de todas as fontes: TODA linha do rastro (de
      qualquer id_saida, inclusive NF-, DIV- e pendências derivadas) tem que existir na fonte (D45).
    - Sempre: nenhum CSV da pasta tem ';' dentro de campo (D45).
    """
    erros: list[str] = []
    dados: dict[str, list[dict]] = {}
    for nome in COLUNAS:
        caminho = pasta / nome
        if caminho.exists():
            linhas = _ler(caminho, erros)
            if linhas is not None:
                dados[nome] = linhas
    if "rastro.csv" not in dados:
        erros.append("rastro.csv ausente: nenhum número tem rastro")
        return erros
    for caminho in sorted(pasta.glob("*.csv")):
        with open(caminho, encoding="utf-8", newline="") as f:
            for i, linha in enumerate(csv.reader(f, delimiter=";"), start=1):
                for v in linha:
                    if ";" in v:
                        erros.append(f"{caminho.name}:{i}: ';' dentro do campo {v[:60]!r}")
    if fontes_rastro is not None:
        for i, l in enumerate(dados["rastro.csv"], start=2):
            fonte = fontes_rastro.get(l.get("arquivo_origem", ""))
            n = int(l["linha_arquivo"]) if (l.get("linha_arquivo") or "").isdigit() else 0
            if fonte is None:
                erros.append(f"rastro.csv:{i} {l['id_saida']}: arquivo {l.get('arquivo_origem')!r} não é fonte do fechamento")
            elif (l["ref_origem"], n) not in fonte:
                erros.append(f"rastro.csv:{i} {l['id_saida']}: {l['ref_origem']} linha {n} não existe na fonte {l['arquivo_origem']}")

    reportados: dict[str, Decimal] = {}
    for nome, linhas in dados.items():
        for i, linha in enumerate(linhas, start=2):
            local = f"{nome}:{i}"
            for col, valor in linha.items():
                if col in _COL_DINHEIRO and valor != "" and not _RE_DINHEIRO.match(valor or ""):
                    erros.append(f"{local}: {col}={valor!r} fora do formato 0.00")
                if col in _COL_CNPJ and not (re.fullmatch(r"\d{14}", valor or "") and cnpj_valido(valor)):
                    erros.append(f"{local}: {col}={valor!r} não é CNPJ de 14 dígitos válido")
                if col in _ENUMS and valor not in _ENUMS[col]:
                    erros.append(f"{local}: {col}={valor!r} fora de {sorted(_ENUMS[col])}")
                if col == "data" and not _RE_DATA.match(valor or ""):
                    erros.append(f"{local}: data={valor!r} fora de AAAA-MM-DD")
            if nome == "rastro.csv":
                continue
            ids = linha.get("id_saida", "")
            if not ids:
                erros.append(f"{local}: id_saida vazio")
                continue
            if ids in reportados:
                erros.append(f"{local}: id_saida {ids} repetido entre os arquivos de saída")
            col_total = _TOTAL_POR_ARQUIVO[nome]
            if linha.get(col_total, "") != "" and _RE_DINHEIRO.match(linha[col_total]):
                reportados[ids] = Decimal(linha[col_total])

    somas: dict[str, Decimal] = {}
    for linha in dados["rastro.csv"]:
        if _RE_DINHEIRO.match(linha.get("valor") or ""):
            somas[linha["id_saida"]] = somas.get(linha["id_saida"], Decimal("0")) + Decimal(linha["valor"])
    for ids, total in sorted(reportados.items()):
        if ids not in somas:
            erros.append(f"{ids}: número {total} sem nenhuma linha no rastro")
        elif somas[ids] != total:
            erros.append(f"{ids}: reportado {total} ≠ soma do rastro {somas[ids]}")
    for ids in sorted(set(somas) - set(reportados)):
        if not ids.startswith(PREFIXO_EXCLUSAO):  # exclusão anotada: só existe no rastro
            erros.append(f"rastro.csv: id_saida {ids} não existe em nenhum arquivo de saída")
    for ids in reportados:
        if ids.startswith(PREFIXO_EXCLUSAO):
            erros.append(f"{ids}: exclusão anotada não pode ser número de saída")

    if "pendencias.csv" in dados:
        erros.extend(_refs_pendencias(dados))
    for i, l in enumerate(dados.get("divergencias_taxa.csv", []), start=2):  # D63
        nat = l.get("natureza") or ""
        if nat not in _NATUREZA_POR_LINHA.get(l.get("linha_negocio"), ()):
            erros.append(f"divergencias_taxa.csv:{i} {l['id_saida']}: natureza {nat!r} fora de "
                         f"{list(_NATUREZA_POR_LINHA.get(l.get('linha_negocio'), ()))}")
    if "notas_a_emitir.csv" in dados:
        erros.extend(_notas(dados))
    if (pasta / "contestacao_ponte.csv").exists():
        erros.extend(_contestacao(pasta / "contestacao_ponte.csv", dados))
    if (pasta / "rascunhos").is_dir():
        erros.extend(_rascunhos(pasta / "rascunhos", dados))
    if fonte_orbe:
        if modo_checkout is None:
            raise ValueError("fonte_orbe exige modo_checkout")
        erros.extend(_conservacao_checkout(dados, fonte_orbe, modo_checkout))
    if spread_ponte:
        erros.extend(_conservacao_remessa(dados, spread_ponte, spread_declarado))
    if refs_extratos is not None or saldos_extratos is not None or contas_lancaveis is not None:
        erros.extend(_extratos(dados, refs_extratos or {}, saldos_extratos or {}, contas_lancaveis))

    if refs_esperadas:
        for arquivo, esperadas in refs_esperadas.items():
            esperadas = {(r, str(n)) for r, n in esperadas}
            vistas = Counter(
                (l["ref_origem"], l.get("linha_arquivo", "")) for l in dados["rastro.csv"]
                if l.get("arquivo_origem") == arquivo and _destino(l["id_saida"])
            )
            faltando = sorted(esperadas - set(vistas))
            repetidas = sorted(r for r, n in vistas.items() if n > 1)
            estranhas = sorted(set(vistas) - esperadas)
            if faltando:
                erros.append(f"{arquivo}: {len(faltando)} linhas sem rastro nem pendência (ex.: {faltando[:5]})")
            if repetidas:
                erros.append(f"{arquivo}: {len(repetidas)} linhas contadas mais de uma vez (ex.: {repetidas[:5]})")
            if estranhas:
                erros.append(f"{arquivo}: {len(estranhas)} ref_origem no rastro que não existem na fonte (ex.: {estranhas[:5]})")
    return erros


# D63: natureza da divergência, lista fechada por linha de negócio
_NATUREZA_POR_LINHA = {
    "CHECKOUT": ("contrato_orbe", "condicao_nao_informada"),
    "REMESSA": ("spread_acima_contrato", "spread_abaixo_contrato", "spread_negativo"),
}
_RE_ID_PURO = re.compile(r"^[^\s,;()|]+$")


def _refs_pendencias(dados: dict[str, list[dict]]) -> list[str]:
    """D55: `ref_origem` de pendência = ids puros separados por '|', sem prosa nem repetição; com rastro,
    exatamente os ids das linhas de origem do rastro dela (lista completa)."""
    erros: list[str] = []
    do_rastro: dict[str, set[str]] = {}
    for l in dados["rastro.csv"]:
        do_rastro.setdefault(l["id_saida"], set()).add(l["ref_origem"])
    for p in dados["pendencias.csv"]:
        tokens = (p.get("ref_origem") or "").split("|")
        ruins = [t for t in tokens if not _RE_ID_PURO.match(t)]
        if ruins:
            erros.append(f"{p['id_saida']}: ref_origem com algo que não é id puro: {ruins[:3]}")
        elif len(tokens) != len(set(tokens)):
            erros.append(f"{p['id_saida']}: ref_origem com id repetido")
        elif p["id_saida"] in do_rastro and set(tokens) != do_rastro[p["id_saida"]]:
            faltam = sorted(do_rastro[p["id_saida"]] - set(tokens))
            sobram = sorted(set(tokens) - do_rastro[p["id_saida"]])
            erros.append(f"{p['id_saida']}: ref_origem ≠ ids do rastro (faltam {faltam[:3]}, sobram {sobram[:3]})")
    return erros


_RE_TOTAL_RASCUNHO = re.compile(r"total_brl=(-?\d+\.\d{2})")


def _rascunhos(pasta: Path, dados: dict[str, list[dict]]) -> list[str]:
    """D68: cada rascunho `.md` tem o seu `.csv`; `total_brl=` do `.md` = Σ valor_brl do `.csv`; nenhuma linha de
    divergência `condicao_nao_informada` (D63) em rascunho para a Orbe; toda linha existe na fonte do rascunho."""
    erros: list[str] = []
    nao_cobrar = {d["ref_origem"] for d in dados.get("divergencias_taxa.csv", []) if d.get("natureza") == "condicao_nao_informada"}
    cobrar_orbe = {d["ref_origem"] for d in dados.get("divergencias_taxa.csv", []) if d.get("natureza") == "contrato_orbe"}
    for md in sorted(pasta.glob("*.md")):
        lista = md.with_suffix(".csv")
        m = _RE_TOTAL_RASCUNHO.search(md.read_text(encoding="utf-8"))
        if not lista.exists() or m is None:
            erros.append(f"rascunhos/{md.name}: sem {lista.name} ou sem total_brl=")
            continue
        with open(lista, encoding="utf-8", newline="") as f:
            linhas = list(csv.DictReader(f, delimiter=";"))
        soma = sum((_d(l.get("valor_brl")) for l in linhas), Decimal("0"))
        if soma != Decimal(m.group(1)):
            erros.append(f"rascunhos/{md.name}: total {m.group(1)} ≠ Σ {lista.name} {soma}")
        if md.name.startswith("orbe_"):
            for l in linhas:
                if l.get("id_transacao") in nao_cobrar:
                    erros.append(f"rascunhos/{md.name}: {l['id_transacao']} é condicao_nao_informada e não se cobra da Orbe")
                elif l.get("id_transacao") not in cobrar_orbe:
                    erros.append(f"rascunhos/{md.name}: {l.get('id_transacao')} não é divergência contrato_orbe")
    return erros


def _contestacao(caminho: Path, dados: dict[str, list[dict]]) -> list[str]:
    """contestacao_ponte.csv (extra): Σ valor_contestado_brl por id_pendencia = valor da pendência
    CONTESTACAO_PONTE, e toda pendência desse tipo tem a sua lista de operações."""
    erros: list[str] = []
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    somas: dict[str, Decimal] = {}
    for i, l in enumerate(linhas, start=2):
        if not _RE_DINHEIRO.match(l.get("valor_contestado_brl") or ""):
            erros.append(f"{caminho.name}:{i}: valor_contestado_brl={l.get('valor_contestado_brl')!r} fora do formato 0.00")
        somas[l.get("id_pendencia", "")] = somas.get(l.get("id_pendencia", ""), Decimal("0")) + _d(l.get("valor_contestado_brl"))
    pend = {p["id_saida"]: _d(p["valor_brl"]) for p in dados.get("pendencias.csv", []) if p["tipo"] == "CONTESTACAO_PONTE"}
    for pid in sorted(set(pend) | set(somas)):
        if pid not in pend:
            erros.append(f"{caminho.name}: {pid} não é pendência CONTESTACAO_PONTE")
        elif pid not in somas:
            erros.append(f"{pid}: pendência de contestação sem lista de operações em {caminho.name}")
        elif somas[pid] != pend[pid]:
            erros.append(f"{pid}: pendência {pend[pid]} ≠ Σ {caminho.name} {somas[pid]}")
    return erros


def _notas(dados: dict[str, list[dict]]) -> list[str]:
    """Σ notas CHECKOUT = Σ comissões CHECKOUT positivas dos lojistas sem nota bloqueada (e cada nota = a
    comissão do lojista); lojista com NOTA_BLOQUEADA não tem nota (D57); nota REMESSA = Σ comissão REMESSA;
    nenhuma nota ≤ 0."""
    erros: list[str] = []
    notas = dados["notas_a_emitir.csv"]
    comissoes = dados.get("comissoes_por_lojista.csv", [])
    bloqueados = {p["id_saida"].rsplit("-", 1)[1] for p in dados.get("pendencias.csv", []) if p["tipo"] == "NOTA_BLOQUEADA"}
    com = {(l["cnpj"], l["linha_negocio"]): _d(l["comissao_brl"]) for l in comissoes
           if not (l["linha_negocio"] == "CHECKOUT" and l["cnpj"] in bloqueados)}
    for n in notas:
        if _d(n["valor_brl"]) <= 0:
            erros.append(f"{n['id_saida']}: nota com valor {n['valor_brl']} ≤ 0")
        if n["linha_negocio"] == "CHECKOUT" and n["tomador_cnpj"] in bloqueados:
            erros.append(f"{n['id_saida']}: nota emitida para lojista com NOTA_BLOQUEADA (valor parcial)")
        if n["linha_negocio"] == "CHECKOUT" and com.get((n["tomador_cnpj"], "CHECKOUT")) != _d(n["valor_brl"]):
            erros.append(f"{n['id_saida']}: valor {n['valor_brl']} ≠ comissão CHECKOUT do lojista {com.get((n['tomador_cnpj'], 'CHECKOUT'))}")
    positivas = sum((v for (_, ln), v in com.items() if ln == "CHECKOUT" and v > 0), Decimal("0"))
    nf_checkout = sum((_d(n["valor_brl"]) for n in notas if n["linha_negocio"] == "CHECKOUT"), Decimal("0"))
    if nf_checkout != positivas:
        erros.append(f"notas CHECKOUT: Σ {nf_checkout} ≠ Σ comissões CHECKOUT positivas {positivas}")
    remessa = sum((v for (_, ln), v in com.items() if ln == "REMESSA"), Decimal("0"))
    nf_remessa = [n for n in notas if n["linha_negocio"] == "REMESSA"]
    if remessa > 0 and (len(nf_remessa) != 1 or _d(nf_remessa[0]["valor_brl"]) != remessa):
        erros.append(f"notas REMESSA: esperada 1 nota de {remessa}, achei {[(n['id_saida'], n['valor_brl']) for n in nf_remessa]}")
    return erros


def _conservacao_checkout(dados: dict[str, list[dict]], fonte_orbe: dict[str, dict[str, tuple]], modo: str) -> list[str]:
    """Σ valor_taxa (Orbe, linhas em COM-…-CHECKOUT) = Σ comissão + Σ divergência + resíduo de truncamento.

    Para cada linha, recalcula a divergência da fonte (Q-H c): round(bruto × (aplicada − contratada))
    se as taxas diferem, senão 0; a taxa contratada vem do rastro. Exige: Σ divergências recalculadas
    = Σ divergências listadas (pares zerados somam 0); resíduo da linha ≤ 1 centavo onde as taxas são
    iguais (só o truncamento da Orbe) e ≤ 2 centavos onde diferem (truncamento + dois arredondamentos).
    """
    erros: list[str] = []
    rastro = dados["rastro.csv"]
    com_ids = {l["id_saida"] for l in dados.get("comissoes_por_lojista.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    div_ids = {l["id_saida"] for l in dados.get("divergencias_taxa.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    soma_com = sum((_d(l["comissao_brl"]) for l in dados.get("comissoes_por_lojista.csv", [])
                    if l["id_saida"] in com_ids), Decimal("0"))
    soma_div = sum((_d(l["diferenca_brl"]) for l in dados.get("divergencias_taxa.csv", [])
                    if l["id_saida"] in div_ids), Decimal("0"))
    soma_fonte = soma_div_recalc = residuo = Decimal("0")
    centavo = Decimal("0.01")
    refs_com: set[tuple[str, str]] = set()
    for l in rastro:
        if l["id_saida"] not in com_ids:
            continue
        fonte = fonte_orbe.get(l["arquivo_origem"], {})
        if l["ref_origem"] not in fonte:
            erros.append(f"conservação: {l['ref_origem']} no rastro de {l['id_saida']} não existe na fonte")
            continue
        valor_taxa, bruto, aplicada = fonte[l["ref_origem"]]
        try:
            contratada = Decimal(l.get("taxa_contratada_pct") or "x") / 100
        except Exception:  # noqa: BLE001 — coluna ausente ou ilegível
            erros.append(f"conservação: {l['ref_origem']} sem taxa_contratada_pct legível no rastro")
            continue
        dif = Decimal("0") if aplicada == contratada else (bruto * (aplicada - contratada)).quantize(centavo, rounding=modo)
        res_linha = valor_taxa - _d(l["valor"]) - dif
        limite = centavo if aplicada == contratada else 2 * centavo
        if abs(res_linha) > limite:
            erros.append(f"{l['ref_origem']}: resíduo {res_linha} (valor_taxa {valor_taxa} − comissão {l['valor']} − "
                         f"divergência {dif}) acima de {limite}")
        soma_fonte += valor_taxa
        soma_div_recalc += dif
        residuo += res_linha
        refs_com.add((l["arquivo_origem"], l["ref_origem"]))
    for l in rastro:
        if l["id_saida"] in div_ids and (l["arquivo_origem"], l["ref_origem"]) not in refs_com:
            erros.append(f"{l['id_saida']}: aponta {l['ref_origem']}, que não está em nenhuma comissão (pendência?)")
    if soma_div_recalc != soma_div:
        erros.append(f"divergências CHECKOUT: listadas {soma_div} ≠ recalculadas da fonte {soma_div_recalc}")
    if soma_fonte != soma_com + soma_div + residuo:
        erros.append(
            f"conservação CHECKOUT: Σ valor_taxa {soma_fonte} ≠ Σ comissão {soma_com} + Σ divergências {soma_div}"
            f" + resíduo {residuo}"
        )
    return erros


def _conservacao_remessa(
    dados: dict[str, list[dict]], spread_ponte: dict[str, dict[tuple[str, int], Decimal]], declarado: Decimal | None
) -> list[str]:
    """Σ Spread R$ do anexo = Σ spread das elegíveis (COM-…-REMESSA) + Σ exclusões (EXC-…) + Σ pendências.

    Também: comissão de cada operação = metade do spread (±0,01); exclusão anotada com
    valor = Spread R$ da linha; Σ do anexo = total declarado pela Ponte.
    """
    erros: list[str] = []
    com_ids = {l["id_saida"] for l in dados.get("comissoes_por_lojista.csv", []) if l["linha_negocio"] == "REMESSA"}
    pen_ids = {l["id_saida"] for l in dados.get("pendencias.csv", [])}
    partes = {"elegíveis": Decimal("0"), "exclusões": Decimal("0"), "pendências": Decimal("0")}
    for arquivo, fonte in spread_ponte.items():
        total_fonte = sum(fonte.values(), Decimal("0"))
        if declarado is not None and total_fonte != declarado:
            erros.append(f"{arquivo}: Σ Spread R$ das linhas {total_fonte} ≠ total declarado no relatório {declarado}")
        for l in dados["rastro.csv"]:
            if l.get("arquivo_origem") != arquivo:
                continue
            chave = (l["ref_origem"], int(l["linha_arquivo"])) if (l.get("linha_arquivo") or "").isdigit() else None
            ids = l["id_saida"]
            if ids in com_ids or ids.startswith(PREFIXO_EXCLUSAO) or (ids in pen_ids and _destino(ids)):
                if chave not in fonte:
                    erros.append(f"{ids}: {l['ref_origem']} linha {l.get('linha_arquivo')} não existe no anexo")
                    continue
                spread, valor = fonte[chave], _d(l["valor"])
                if ids in com_ids:
                    partes["elegíveis"] += spread
                    if abs(2 * valor - spread) > Decimal("0.01"):
                        erros.append(f"{ids}: comissão {valor} de {l['ref_origem']} não é metade do spread {spread}")
                elif ids.startswith(PREFIXO_EXCLUSAO):
                    partes["exclusões"] += spread
                    if valor != spread:
                        erros.append(f"{ids}: exclusão de {l['ref_origem']} com valor {valor} ≠ Spread R$ {spread}")
                else:
                    partes["pendências"] += spread
        if total_fonte != sum(partes.values()):
            erros.append(
                f"conservação REMESSA: Σ Spread R$ do anexo {total_fonte} ≠ elegíveis {partes['elegíveis']}"
                f" + exclusões {partes['exclusões']} + pendências {partes['pendências']}"
            )
    return erros


def _extratos(
    dados: dict[str, list[dict]],
    refs: dict[str, set[tuple[str, int]]],
    saldos: dict[str, tuple[Decimal | None, Decimal | None]],
    contas: set[str] | None,
) -> list[str]:
    """Lançamentos dos extratos: cada linha exatamente uma vez (LAN-…); Σ valor por banco = saldo
    final − saldo inicial do próprio extrato (quando o extrato traz os dois); conta usada existe e é
    lançável; REGRA/IA com conta; HUMANO com conta só por decisão explícita; confiança sempre preenchida (D54):
    0.00–1.00, REGRA = 1.00, HUMANO com conta = 1.00, HUMANO sem conta = 0.00."""
    erros: list[str] = []
    lan = dados.get("lancamentos_classificados.csv")
    if lan is None:
        return ["lancamentos_classificados.csv ausente"]
    rastro = dados["rastro.csv"]
    for arquivo, esperadas in refs.items():
        esperadas = {(r, str(n)) for r, n in esperadas}
        vistas = Counter((l["ref_origem"], l.get("linha_arquivo", "")) for l in rastro
                         if l.get("arquivo_origem") == arquivo and l["id_saida"].startswith("LAN-"))
        faltando = sorted(esperadas - set(vistas))
        repetidas = sorted(r for r, n in vistas.items() if n > 1)
        estranhas = sorted(set(vistas) - esperadas)
        if faltando:
            erros.append(f"{arquivo}: {len(faltando)} lançamentos sem classificação (ex.: {faltando[:5]})")
        if repetidas:
            erros.append(f"{arquivo}: {len(repetidas)} lançamentos classificados mais de uma vez (ex.: {repetidas[:5]})")
        if estranhas:
            erros.append(f"{arquivo}: {len(estranhas)} ref_origem que não existem no extrato (ex.: {estranhas[:5]})")
    for banco, (inicial, final) in saldos.items():
        soma = sum((_d(l["valor"]) for l in lan if l["banco"] == banco), Decimal("0"))
        if inicial is not None and final is not None and soma != final - inicial:
            erros.append(f"{banco}: Σ lançamentos {soma} ≠ saldo final {final} − saldo inicial {inicial} ({final - inicial})")
    for l in lan:
        conta, metodo = l.get("conta_codigo", ""), l.get("metodo", "")
        if metodo in ("REGRA", "IA") and not conta:
            erros.append(f"{l['id_saida']}: método {metodo} sem conta")
        confianca = l.get("confianca") or ""
        if not (_RE_DINHEIRO.match(confianca) and Decimal("0") <= Decimal(confianca) <= Decimal("1")):
            erros.append(f"{l['id_saida']}: confiança {confianca!r} fora de 0.00–1.00 (nunca vazia, D54)")
        else:
            esperada = {"REGRA": "1.00", "HUMANO": "1.00" if conta else "0.00"}.get(metodo)
            if esperada and confianca != esperada:
                erros.append(f"{l['id_saida']}: método {metodo} {'com' if conta else 'sem'} conta e confiança {confianca}"
                             f" (esperada {esperada}, D54)")
        if metodo == "HUMANO" and conta and not (l.get("regra_aplicada") or "").startswith("decisoes_humanas."):
            erros.append(f"{l['id_saida']}: método HUMANO com conta {conta} sem decisão explícita (decisoes_humanas no regras.yaml)")
        if conta and contas is not None and conta not in contas:
            erros.append(f"{l['id_saida']}: conta {conta} não existe ou não aceita lançamento (ANALITICA e ACEITA_LANCTO=S)")
    return erros

