"""Escritor dos CSVs de `saida/`.

Formato fixo (docs/case.md): separador `;`, ponto decimal, datas AAAA-MM-DD, CNPJ só
números (14 dígitos), `linha_negocio` CHECKOUT|REMESSA, `banco` AURORA|MERIDIANO,
`metodo` REGRA|IA|HUMANO. A formatação acontece só aqui; as contas chegam em Decimal.

Colunas obrigatórias primeiro, na ordem do case; colunas extras (bem-vindas pelo case)
depois. Colunas terminadas em `_pct` saem como percentual (3.59); outros Decimal como
dinheiro com 2 casas. Só escreve os arquivos pedidos: entregável ainda não implementado
não vira CSV vazio (que pareceria "nada a reportar").
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from tarvo.formatos import fmt_dinheiro, fmt_pct

COLUNAS = {
    "comissoes_por_lojista.csv": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "divergencias_taxa.csv": [
        "id_saida", "cnpj", "linha_negocio", "ref_origem",
        "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl",
    ],
    "notas_a_emitir.csv": [
        "id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao",
    ],
    "lancamentos_classificados.csv": [
        "id_saida", "banco", "ref_origem", "data", "descricao", "valor",
        "conta_codigo", "metodo", "confianca",
    ],
    "pendencias.csv": ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"],
    "rastro.csv": ["id_saida", "arquivo_origem", "ref_origem", "valor"],
}
# extras (fora dos 6 do case): só colunas próprias, sem obrigatórias do case
EXTRAS = {
    "contestacao_ponte.csv": ["id_pendencia", "motivo", "ref_origem", "linha_anexo", "valor_contestado_brl"],
    "sugestoes_regra.csv": ["id_sugestao", "tipo", "banco", "padrao_ou_nome", "conta_codigo", "status"],
}


def formatar(coluna: str, valor: object) -> str:
    if valor is None:
        return ""
    if isinstance(valor, Decimal):
        return fmt_pct(valor) if coluna.endswith("_pct") else fmt_dinheiro(valor)
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, float):
        raise TypeError(f"float na saída (coluna {coluna}): use Decimal")
    return str(valor)


def escrever_csv(caminho: Path, linhas: list[dict]) -> Path:
    """Escreve um CSV do case: obrigatórias na ordem do case + extras na ordem em que aparecem."""
    obrigatorias = {**COLUNAS, **EXTRAS}[caminho.name]
    extras: list[str] = []
    for linha in linhas:
        faltando = [c for c in obrigatorias if c not in linha]
        if faltando:
            raise ValueError(f"{caminho.name}: linha sem colunas obrigatórias {faltando}: {linha}")
        extras.extend(c for c in linha if c not in obrigatorias and c not in extras)
    colunas = obrigatorias + extras
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(colunas)
        for linha in linhas:
            w.writerow([formatar(c, linha.get(c)) for c in colunas])
    return caminho


def escrever_saida(arquivos: dict[str, list[dict]], pasta: Path) -> list[Path]:
    """Escreve os CSVs pedidos ({nome_arquivo: linhas}) e devolve os caminhos."""
    desconhecidos = set(arquivos) - set(COLUNAS) - set(EXTRAS)
    if desconhecidos:
        raise ValueError(f"arquivos de saída fora do case: {sorted(desconhecidos)}")
    return [escrever_csv(pasta / nome, linhas) for nome, linhas in arquivos.items()]
