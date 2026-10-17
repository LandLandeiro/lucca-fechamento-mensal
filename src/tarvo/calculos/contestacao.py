"""Contestação com a Ponte: o que a Helena manda para a Ponte, por motivo, com as operações.

Responsabilidade: montar uma pendência CONTESTACAO_PONTE por motivo (Q-L, Helena 22:34) e a
lista de operações de cada uma (`contestacao_ponte.csv`, extra). `id_saida`:
`PEN-CONTESTACAO_PONTE-<motivo>[-<cnpj>]`. São pendências derivadas: reapontam linhas do anexo
que já têm destino (DIV-…, EXC-…), então ficam fora da cobertura "uma vez" do validador.

Motivos (regras `remessa.contestacao_ponte` e `remessa.valor_contestado`):
- SPREAD_ACIMA_DO_CONTRATADO-<cnpj>: divergências COBROU_A_MAIS de spread não negativo,
  uma pendência por lojista; valor = Σ divergência (valor cheio, Helena 20:58);
- SPREAD_NEGATIVO: spreads negativos (trava de 2h vencida); valor = Σ Spread R$ do relatório;
- DUPLICATA: linhas repetidas do relatório que o fechamento conta uma vez; valor = Σ Spread R$
  das cópias que ficaram fora (a Ponte corrige o relatório).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.calculos.remessa import ClassificacaoRemessa
from tarvo.formatos import fmt_dinheiro, fmt_pct
from tarvo.modelo import OperacaoPonte, Pendencia
from tarvo.regras import valor_da_regra

ZERO = Decimal("0")
TIPO = "CONTESTACAO_PONTE"


@dataclass
class ResultadoContestacao:
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    linhas: list[dict] = field(default_factory=list)  # contestacao_ponte.csv


def _linha(pid: str, motivo: str, op: OperacaoPonte, cnpj: str | None, lojista: str | None,
           div: dict | None, valor: Decimal, obs: str) -> dict:
    return {
        "id_pendencia": pid,
        "motivo": motivo,
        "ref_origem": op.ref_origem,
        "linha_anexo": op.linha_planilha,
        "cnpj": cnpj,
        "lojista": lojista or op.cliente,
        "data_contratacao": op.data_contratacao,
        "moeda": op.moeda,
        "valor_me": op.valor_me,
        "ptax_ref": str(op.ptax_ref),
        "taxa_cliente": str(op.taxa_cliente),
        "spread_aplicado_pct": op.spread_pct,
        "spread_contratado_pct": div["taxa_contratada_pct"] if div else None,
        "spread_brl": op.spread_brl,
        "diferenca_contrato_brl": div["diferenca_brl"] if div else None,
        "valor_contestado_brl": valor,
        "observacao": obs,
    }


def contestacao_ponte(cls: ClassificacaoRemessa, divergencias_remessa: list[dict], regras: dict) -> ResultadoContestacao:
    """Pendências CONTESTACAO_PONTE (uma por motivo) + linhas por operação para a Ponte."""
    valor_da_regra(regras, "remessa.contestacao_ponte")
    valor_da_regra(regras, "remessa.valor_contestado")
    quem = "Helena"
    div_por_ref = {d["ref_origem"]: d for d in divergencias_remessa}
    ops = {op.ref_origem: (op, cnpj) for op, cnpj in cls.elegiveis + cls.negativos}
    res = ResultadoContestacao()

    def registrar(pid: str, motivo: str, itens: list[tuple[OperacaoPonte, str | None, str | None, dict | None, Decimal, str]],
                  ref: str, texto: str) -> None:
        total = sum((v for *_, v, _ in itens), ZERO)
        res.pendencias.append(Pendencia(pid, TIPO, ref, total, texto, quem))
        for op, cnpj, lojista, div, v, obs in itens:
            res.linhas.append(_linha(pid, motivo, op, cnpj, lojista, div, v, obs))
            res.rastro.append({
                "id_saida": pid, "arquivo_origem": op.arquivo_origem, "ref_origem": op.ref_origem, "valor": v,
                "linha_arquivo": op.linha_planilha, "tipo_lancamento": "REMESSA", "spread_brl": op.spread_brl,
                "nota": f"contestação com a Ponte ({motivo.lower()}): {obs}",
            })

    # (a) spread acima do contratado, por lojista
    acima: dict[str, list[dict]] = {}
    for d in divergencias_remessa:
        if d["spread_brl"] >= 0 and d["diferenca_brl"] > 0:
            acima.setdefault(d["cnpj"], []).append(d)
    for cnpj, ds in sorted(acima.items()):
        ds = sorted(ds, key=lambda d: ops[d["ref_origem"]][0].linha_planilha)
        contratados = sorted({fmt_pct(d["taxa_contratada_pct"]) for d in ds})
        itens = [(ops[d["ref_origem"]][0], cnpj, d["lojista"], d, d["diferenca_brl"],
                  f"aplicado {fmt_pct(d['taxa_aplicada_pct'])}% × contratado {fmt_pct(d['taxa_contratada_pct'])}% sobre a PTAX")
                 for d in ds]
        total = sum((d["diferenca_brl"] for d in ds), ZERO)
        registrar(
            f"PEN-{TIPO}-SPREAD_ACIMA_DO_CONTRATADO-{cnpj}", "SPREAD_ACIMA_DO_CONTRATADO", itens,
            f"{len(ds)} operações (contestacao_ponte.csv)",
            f"{ds[0]['lojista']}: a Ponte aplicou spread acima do contratado ({'/'.join(contratados)}%) em {len(ds)} "
            f"operações; o lojista pagou {fmt_dinheiro(total)} a mais (valor cheio). Contestar com a Ponte; "
            f"lista de operações em contestacao_ponte.csv (Helena 20:58 e 22:34)",
        )

    # (b) spreads negativos
    negativos = sorted(cls.negativos, key=lambda x: x[0].linha_planilha)
    if negativos:
        # D80 (Q-AA 3): o valor contestado é a diferença até o spread do contrato (o que pedir à Ponte); o Spread R$
        # do relatório (o que aconteceu) fica ao lado, rotulado
        itens = []
        for op, cnpj in negativos:
            div = div_por_ref.get(op.ref_origem)
            pedir = div["diferenca_brl"] if div else op.spread_brl
            itens.append((op, cnpj, div["lojista"] if div else None, div, pedir,
                          f"spread negativo do relatório (o que aconteceu) {fmt_dinheiro(op.spread_brl)}; diferença até o "
                          f"spread do contrato (o que pedir à Ponte) {fmt_dinheiro(pedir)}; {op.observacao or 'sem observação'}"))
        pedir = sum((i[4] for i in itens), ZERO)
        aconteceu = sum((op.spread_brl for op, _ in negativos), ZERO)
        registrar(
            f"PEN-{TIPO}-SPREAD_NEGATIVO", "SPREAD_NEGATIVO", itens,
            ", ".join(op.ref_origem for op, _ in negativos),
            f"{len(negativos)} operações com spread negativo (trava de 2 horas vencida). Spread negativo do relatório "
            f"(o que aconteceu): {fmt_dinheiro(aconteceu)}. Diferença até o spread do contrato (o que pedir à Ponte, "
            f"valor desta pendência): {fmt_dinheiro(pedir)}. Fora da comissão e da nota (Helena 20:48, 22:34; "
            f"Q-AA 3: 'Coloquem os dois na pendência, deixando claro qual é qual')",
        )

    # (c) duplicatas: conta uma vez no fechamento e entra na lista para a Ponte corrigir o relatório
    duplicatas = sorted([(op, nota) for op, motivo, nota in cls.excluidas if motivo == "DUPLICATA"],
                        key=lambda x: x[0].linha_planilha)
    if duplicatas:
        itens = []
        for op, nota in duplicatas:
            fica = ops.get(op.ref_origem)
            itens.append((op, fica[1] if fica else None, None, None, op.spread_brl,
                          f"repetida no relatório (conta uma vez: R{fica[0].linha_planilha})" if fica else nota))
        total = sum((op.spread_brl for op, _ in duplicatas), ZERO)
        refs = ", ".join(f"{op.ref_origem} (R{op.linha_planilha})" for op, _ in duplicatas)
        registrar(
            f"PEN-{TIPO}-DUPLICATA", "DUPLICATA", itens, refs,
            f"Operação repetida no relatório da Ponte: {refs}, Spread R$ {fmt_dinheiro(total)}. O fechamento conta "
            f"uma vez; a Ponte corrige o relatório (Helena 22:34)",
        )
    return res
