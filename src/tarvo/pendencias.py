"""Pendências: tudo que exige uma pessoa, com motivo e quem decide.

Responsabilidade: reunir as pendências geradas por leitura, cadastro, cálculos e
classificação (lojista sem chave, regra vazia, duplicidade, spread negativo, lançamento
sem classificação segura etc.) num formato único, sem repetir.
`id_saida`: `PEN-<tipo>-<ref_origem>`.
"""

from __future__ import annotations

import csv
from pathlib import Path

from tarvo.modelo import Pendencia


def consolidar_pendencias(*listas: list[Pendencia]) -> list[Pendencia]:
    """Junta as pendências de todas as etapas, sem repetição. Mesmo id com conteúdo diferente = erro."""
    vistas: dict[str, Pendencia] = {}
    for lista in listas:
        for p in lista:
            atual = vistas.get(p.id_saida)
            if atual is not None and atual != p:
                raise ValueError(f"pendência {p.id_saida} gerada duas vezes com conteúdo diferente")
            vistas[p.id_saida] = p
    return sorted(vistas.values(), key=lambda p: (p.tipo, p.id_saida))


def pendencia_para_linha(p: Pendencia) -> dict:
    """Pendencia → linha do pendencias.csv."""
    return {
        "id_saida": p.id_saida,
        "tipo": p.tipo,
        "ref_origem": p.ref_origem,
        "valor_brl": p.valor_brl,
        "motivo": p.motivo,
        "quem_decide": p.quem_decide,
    }


def ler_pendencias_anteriores(caminho: Path) -> list[dict]:
    """`pendencias.csv` do mês anterior (formato desta saída): uma linha por pendência (D50)."""
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    faltando = [c for c in ("id_saida", "tipo", "ref_origem", "valor_brl", "motivo") if linhas and c not in linhas[0]]
    if faltando:
        raise ValueError(f"{caminho}: não parece um pendencias.csv (faltam {faltando})")
    return linhas
