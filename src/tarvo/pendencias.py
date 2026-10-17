"""Pendências: tudo que exige uma pessoa, com motivo e quem decide.

Responsabilidade: reunir as pendências geradas por leitura, cadastro, cálculos e
classificação (lojista sem chave, regra vazia, duplicidade, spread negativo, lançamento
sem classificação segura etc.) num formato único, sem repetir.
`id_saida`: `PEN-<tipo>-<ref_origem>`.

`ref_origem` (D55): só ids puros das linhas de origem (id_transacao, Nº Operação, L<n>, FITID),
lista completa separada por "|", sem prosa; o texto explicativo fica no `motivo`. Pendência com
rastro: os ids são exatamente os do rastro dela (`refs_das_pendencias`).
"""

from __future__ import annotations

import csv
from dataclasses import replace
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


def refs_das_pendencias(pendencias: list[Pendencia], rastro: list[dict]) -> list[Pendencia]:
    """`ref_origem` de cada pendência com rastro = os ids das linhas de origem do rastro dela, sem repetir,
    na ordem do rastro, separados por "|" (D55). Pendência sem rastro (ex.: linha ilegível) fica como está."""
    refs: dict[str, list[str]] = {}
    for l in rastro:
        lista = refs.setdefault(l["id_saida"], [])
        if l["ref_origem"] not in lista:
            lista.append(l["ref_origem"])
    return [replace(p, ref_origem="|".join(refs[p.id_saida])) if p.id_saida in refs else p for p in pendencias]


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


def pendencia_provisao(competencia: tuple[int, int], lancamentos: list[dict], regras: dict) -> Pendencia:
    """D72 (Q-R 3, `contabil.provisao_do_mes`): a provisão de folha e impostos do mês é sempre feita no fechamento,
    mas os valores não vêm no pacote. Pendência para a Helena, sem valor (nada é estimado). ref_origem = os pagamentos
    das obrigações do mês anterior no extrato, que mostram o que se repete (e que no mês seguinte baixam a provisão)."""
    from tarvo.formatos import nome_mes
    from tarvo.regras import valor_da_regra
    cfg = valor_da_regra(regras, "contabil.provisao_do_mes")
    refs = [l["ref_origem"] for l in lancamentos if l["regra_aplicada"] in cfg["referencia"]]
    ano, mes = competencia
    return Pendencia(
        f"PEN-PROVISAO_DO_MES-{ano}-{mes:02d}", "PROVISAO_DO_MES", "|".join(refs), None,
        f"provisão de folha e impostos de {nome_mes(mes)}: valores fora do pacote. Helena 09:48 (Q-R 3): 'Sempre. Todo mês "
        f"a folha e os impostos do mês ficam provisionados no fechamento, e o pagamento no mês seguinte baixa a provisão.' "
        f"Nenhum valor estimado. ref_origem = os {len(refs)} pagamentos das obrigações do mês anterior neste extrato "
        f"(o mesmo conjunto que a provisão de {nome_mes(mes)} deve cobrir)",
        "Helena",
    )
