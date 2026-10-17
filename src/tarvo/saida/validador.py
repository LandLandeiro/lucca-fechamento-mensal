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
PREFIXOS_DERIVADOS = ("PEN-NF_NEGATIVA-", "PEN-CONFERENCIA_REPASSE-")


def _d(texto: str | None) -> Decimal:
    """Número da saída para as checagens de soma; fora do formato conta 0 (o erro de formato já é reportado)."""
    return Decimal(texto) if _RE_DINHEIRO.match(texto or "") else Decimal("0")


def _destino(id_saida: str) -> bool:
    return id_saida.startswith(PREFIXOS_COBERTURA) and not id_saida.startswith(PREFIXOS_DERIVADOS)


def validar_saida(
    pasta: Path,
    refs_esperadas: dict[str, set[tuple[str, int]]] | None = None,
    valor_taxa_orbe: dict[str, dict[str, Decimal]] | None = None,
    spread_ponte: dict[str, dict[tuple[str, int], Decimal]] | None = None,
    spread_declarado: Decimal | None = None,
) -> list[str]:
    """Devolve a lista de erros encontrados (vazia = saída válida).

    - `refs_esperadas` {arquivo: {(ref_origem, linha)}}: cada linha de origem aparece
      exatamente uma vez no rastro de um COM-…, PEN-… ou EXC-… (a linha distingue cópias
      com o mesmo Nº de operação).
    - `valor_taxa_orbe` {arquivo: {ref: valor_taxa}}, lido da fonte: conservação do checkout,
      Σ valor_taxa das linhas em COM-…-CHECKOUT = Σ comissão CHECKOUT + Σ divergências CHECKOUT;
      e toda divergência de checkout aponta só linhas que estão numa comissão.
    - `spread_ponte` {arquivo: {(Nº, linha): Spread R$}}: conservação da remessa (ver
      `_conservacao_remessa`); `spread_declarado` = "Spread total R$" do próprio relatório.
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

    if "notas_a_emitir.csv" in dados:
        erros.extend(_notas(dados))
    if valor_taxa_orbe:
        erros.extend(_conservacao_checkout(dados, valor_taxa_orbe))
    if spread_ponte:
        erros.extend(_conservacao_remessa(dados, spread_ponte, spread_declarado))

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


def _notas(dados: dict[str, list[dict]]) -> list[str]:
    """Σ notas CHECKOUT = Σ comissões CHECKOUT positivas (e cada nota = a comissão do lojista);
    nota REMESSA = Σ comissão REMESSA; nenhuma nota ≤ 0."""
    erros: list[str] = []
    notas = dados["notas_a_emitir.csv"]
    comissoes = dados.get("comissoes_por_lojista.csv", [])
    com = {(l["cnpj"], l["linha_negocio"]): _d(l["comissao_brl"]) for l in comissoes}
    for n in notas:
        if _d(n["valor_brl"]) <= 0:
            erros.append(f"{n['id_saida']}: nota com valor {n['valor_brl']} ≤ 0")
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


def _conservacao_checkout(dados: dict[str, list[dict]], valor_taxa_orbe: dict[str, dict[str, Decimal]]) -> list[str]:
    erros: list[str] = []
    rastro = dados["rastro.csv"]
    com_ids = {l["id_saida"] for l in dados.get("comissoes_por_lojista.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    div_ids = {l["id_saida"] for l in dados.get("divergencias_taxa.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    soma_com = sum((_d(l["comissao_brl"]) for l in dados.get("comissoes_por_lojista.csv", [])
                    if l["id_saida"] in com_ids), Decimal("0"))
    soma_div = sum((_d(l["diferenca_brl"]) for l in dados.get("divergencias_taxa.csv", [])
                    if l["id_saida"] in div_ids), Decimal("0"))
    soma_fonte = Decimal("0")
    refs_com: set[tuple[str, str]] = set()
    for l in rastro:
        if l["id_saida"] in com_ids:
            fonte = valor_taxa_orbe.get(l["arquivo_origem"], {})
            if l["ref_origem"] not in fonte:
                erros.append(f"conservação: {l['ref_origem']} no rastro de {l['id_saida']} não existe na fonte")
                continue
            soma_fonte += fonte[l["ref_origem"]]
            refs_com.add((l["arquivo_origem"], l["ref_origem"]))
    for l in rastro:
        if l["id_saida"] in div_ids and (l["arquivo_origem"], l["ref_origem"]) not in refs_com:
            erros.append(f"{l['id_saida']}: aponta {l['ref_origem']}, que não está em nenhuma comissão (pendência?)")
    if soma_fonte != soma_com + soma_div:
        erros.append(
            f"conservação CHECKOUT: Σ valor_taxa Orbe {soma_fonte} ≠ Σ comissão {soma_com} + Σ divergências {soma_div}"
            f" (diferença {soma_fonte - soma_com - soma_div})"
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
