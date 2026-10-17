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


PREFIXOS_COBERTURA = ("COM-", "PEN-")  # onde cada linha de origem tem que aparecer exatamente uma vez


def validar_saida(
    pasta: Path,
    refs_esperadas: dict[str, set[str]] | None = None,
    valor_taxa_orbe: dict[str, dict[str, Decimal]] | None = None,
) -> list[str]:
    """Devolve a lista de erros encontrados (vazia = saída válida).

    - `refs_esperadas` {arquivo: refs}: cada ref aparece exatamente uma vez no rastro de um
      número COM-… ou PEN-… (DIV-… reaponta as mesmas linhas e não conta).
    - `valor_taxa_orbe` {arquivo: {ref: valor_taxa}}, lido da fonte: conservação do checkout,
      Σ valor_taxa das linhas em COM-…-CHECKOUT = Σ comissão CHECKOUT + Σ divergências CHECKOUT;
      e toda divergência aponta só linhas que estão numa comissão.
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
        erros.append(f"rastro.csv: id_saida {ids} não existe em nenhum arquivo de saída")

    if valor_taxa_orbe:
        erros.extend(_conservacao_checkout(dados, valor_taxa_orbe))

    if refs_esperadas:
        for arquivo, esperadas in refs_esperadas.items():
            vistas = Counter(
                l["ref_origem"] for l in dados["rastro.csv"]
                if l.get("arquivo_origem") == arquivo and l["id_saida"].startswith(PREFIXOS_COBERTURA)
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


def _conservacao_checkout(dados: dict[str, list[dict]], valor_taxa_orbe: dict[str, dict[str, Decimal]]) -> list[str]:
    erros: list[str] = []
    rastro = dados["rastro.csv"]
    com_ids = {l["id_saida"] for l in dados.get("comissoes_por_lojista.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    div_ids = {l["id_saida"] for l in dados.get("divergencias_taxa.csv", []) if l["linha_negocio"] == "CHECKOUT"}
    soma_com = sum((Decimal(l["comissao_brl"]) for l in dados.get("comissoes_por_lojista.csv", [])
                    if l["id_saida"] in com_ids), Decimal("0"))
    soma_div = sum((Decimal(l["diferenca_brl"]) for l in dados.get("divergencias_taxa.csv", [])
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
