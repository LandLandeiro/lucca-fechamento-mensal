"""Conferências entre fontes, sem mudar a conta de nenhum lançamento (`classificacao_extratos.conferencias`).

1. Transferência entre contas: cada saída Aurora→Meridiano (regra transferencia_meridiano)
   casa com uma entrada de mesma titularidade (regra mesma_titularidade) de mesmo valor em
   até 1 dia útil. Sem par → pendência "em trânsito".
2. Aportes da remessa: por lojista, Σ PIX RECEB no Meridiano × Σ (Valor R$ + IOF) das
   operações únicas da Ponte (a duplicata conta uma vez). Sobra igual a um aporte → pendência
   desse aporte; outra sobra ≠ 0 → pendência do lojista. Lojista sem nenhum aporte identificado,
   havendo PIX RECEB sem regra, fica "não conferido" (sem pendência: seria alarme falso).
3. Aplicação × resgate (FIFO): resgate acima do saldo aplicado no mês → pendência com
   proposta (o excesso seria rendimento 3.2.01); a linha não é dividida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from tarvo.formatos import fmt_dinheiro
from tarvo.modelo import LancamentoBancario, OperacaoPonte, Pendencia

ZERO = Decimal("0")


@dataclass
class ResultadoConferencias:
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro_pendencias: list[dict] = field(default_factory=list)
    transferencias: list[tuple[LancamentoBancario, LancamentoBancario | None]] = field(default_factory=list)
    aportes: list[dict] = field(default_factory=list)
    resgates: list[dict] = field(default_factory=list)


def dias_uteis_entre(a: date, b: date) -> int:
    """Dias úteis (seg–sex) de a até b, sem contar a; feriados não são considerados."""
    if b < a:
        return -dias_uteis_entre(b, a)
    n, d = 0, a
    while d < b:
        d += timedelta(days=1)
        n += d.weekday() < 5
    return n


def _rastro(pid: str, lan: LancamentoBancario, valor: Decimal, linha: int, nota: str) -> dict:
    return {"id_saida": pid, "arquivo_origem": lan.arquivo_origem, "ref_origem": lan.ref_origem, "valor": valor,
            "linha_arquivo": linha, "tipo_lancamento": f"EXTRATO {lan.banco}", "nota": nota}


def conferir(
    regra_por_lancamento: dict[tuple[str, str], str],
    lancamentos: list[LancamentoBancario],
    linhas_arquivo: dict[tuple[str, str], int],
    lojista_por_lancamento: dict[tuple[str, str], str],
    operacoes_unicas: list[tuple[OperacaoPonte, str]],
    nomes: dict[str, str],
    aportes_nao_identificados: list[LancamentoBancario] | None = None,
) -> ResultadoConferencias:
    """Roda as três conferências. `regra_por_lancamento` (banco, ref) → nome da regra aplicada."""
    res = ResultadoConferencias()
    por_regra: dict[str, list[LancamentoBancario]] = {}
    for lan in sorted(lancamentos, key=lambda l: (l.data, l.banco, l.ref_origem)):
        regra = regra_por_lancamento.get((lan.banco, lan.ref_origem), "")
        por_regra.setdefault(regra, []).append(lan)

    def linha(lan):
        return linhas_arquivo.get((lan.banco, lan.ref_origem), 0)

    # 1) transferências entre contas próprias
    entradas = list(por_regra.get("meridiano.mesma_titularidade", []))
    for saida in por_regra.get("aurora.transferencia_meridiano", []):
        par = next((e for e in entradas if e.valor == -saida.valor and 0 <= dias_uteis_entre(saida.data, e.data) <= 1), None)
        res.transferencias.append((saida, par))
        if par is not None:
            entradas.remove(par)
            continue
        pid = f"PEN-TRANSFERENCIA_EM_TRANSITO-{saida.banco}-{saida.ref_origem}"
        res.pendencias.append(Pendencia(
            pid, "TRANSFERENCIA_EM_TRANSITO", saida.ref_origem, saida.valor,
            f"transferência de {fmt_dinheiro(-saida.valor)} saiu do Aurora em {saida.data.isoformat()} e não tem TED de "
            f"mesma titularidade no Meridiano em até 1 dia útil: em trânsito, cai no Meridiano em 01/10 "
            f"(Helena 20:49, Q-F 4c); conferir no extrato de outubro", "analista (conferir em outubro)",
        ))
        res.rastro_pendencias.append(_rastro(pid, saida, saida.valor, linha(saida), "transferência sem par no Meridiano"))
    for e in entradas:  # entrada de mesma titularidade sem saída no Aurora
        pid = f"PEN-TRANSFERENCIA_SEM_ORIGEM-{e.banco}-{e.ref_origem}"
        res.pendencias.append(Pendencia(pid, "TRANSFERENCIA_SEM_ORIGEM", e.ref_origem, e.valor,
                                        f"TED de mesma titularidade de {fmt_dinheiro(e.valor)} em {e.data.isoformat()} "
                                        f"sem transferência correspondente no Aurora", "analista"))
        res.rastro_pendencias.append(_rastro(pid, e, e.valor, linha(e), "entrada sem saída no Aurora"))

    # 2) aportes PIX × operações da Ponte, por lojista
    aportes: dict[str, list[LancamentoBancario]] = {}
    for lan in por_regra.get("meridiano.aporte_lojista", []):
        cnpj = lojista_por_lancamento.get((lan.banco, lan.ref_origem))
        if cnpj:
            aportes.setdefault(cnpj, []).append(lan)
    devido: dict[str, Decimal] = {}
    for op, cnpj in operacoes_unicas:
        devido[cnpj] = devido.get(cnpj, ZERO) + op.valor_brl + op.iof_brl
    for cnpj in sorted(set(aportes) | set(devido)):
        recebido = sum((l.valor for l in aportes.get(cnpj, [])), ZERO)
        sobra = recebido - devido.get(cnpj, ZERO)
        nao_conferido = not aportes.get(cnpj) and bool(aportes_nao_identificados)
        res.aportes.append({"cnpj": cnpj, "lojista": nomes.get(cnpj, cnpj), "aportes": recebido,
                            "operacoes": devido.get(cnpj, ZERO), "sobra": sobra, "nao_conferido": nao_conferido})
        if sobra == 0 or nao_conferido:
            # nenhum aporte identificado e há PIX RECEB sem regra: a conferência depende da identificação
            # (alarme falso se acusar agora); fica registrada como não conferida
            continue
        candidatos = [l for l in aportes.get(cnpj, []) if l.valor == sobra]
        if len(candidatos) == 1:
            lan = candidatos[0]
            pid = f"PEN-APORTE_SEM_OPERACAO-{lan.banco}-{lan.ref_origem}"
            res.pendencias.append(Pendencia(
                pid, "APORTE_SEM_OPERACAO", lan.ref_origem, lan.valor,
                f"{nomes.get(cnpj, cnpj)}: aportes no Meridiano somam {fmt_dinheiro(recebido)} e as operações da Ponte "
                f"(Valor R$ + IOF) {fmt_dinheiro(devido.get(cnpj, ZERO))}; a sobra é exatamente o PIX de "
                f"{lan.data.isoformat()} ({fmt_dinheiro(lan.valor)}): recurso do lojista sem operação de câmbio", "Helena",
            ))
            res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha(lan), "aporte sem operação na Ponte"))
        else:
            pid = f"PEN-APORTE_DIVERGENTE-{cnpj}"
            res.pendencias.append(Pendencia(
                pid, "APORTE_DIVERGENTE", cnpj, sobra,
                f"{nomes.get(cnpj, cnpj)}: aportes {fmt_dinheiro(recebido)} × operações {fmt_dinheiro(devido.get(cnpj, ZERO))}; "
                f"diferença {fmt_dinheiro(sobra)} não corresponde a um aporte só", "Helena",
            ))
            # rastro: + cada aporte, − cada operação (Valor R$ + IOF) → soma = a diferença reportada
            for lan in aportes.get(cnpj, []):
                res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha(lan), "aporte do lojista"))
            for op, c in operacoes_unicas:
                if c == cnpj:
                    res.rastro_pendencias.append({
                        "id_saida": pid, "arquivo_origem": op.arquivo_origem, "ref_origem": op.ref_origem,
                        "valor": -(op.valor_brl + op.iof_brl), "linha_arquivo": op.linha_planilha,
                        "tipo_lancamento": "REMESSA", "nota": "operação da Ponte (Valor R$ + IOF)",
                    })

    # 3) aplicação × resgate (FIFO)
    eventos = sorted(por_regra.get("meridiano.aplicacao_automatica", []) + por_regra.get("meridiano.resgate_automatico", []),
                     key=lambda l: (l.data, l.ref_origem))
    fila: list[list] = []  # [lançamento de aplicação, saldo restante]
    for lan in eventos:
        if lan.valor < 0:
            fila.append([lan, -lan.valor])
            continue
        falta, consumidas = lan.valor, []
        while falta > 0 and fila:
            ap = fila[0]
            usado = min(ap[1], falta)
            ap[1] -= usado
            falta -= usado
            consumidas.append((ap[0], usado))
            if ap[1] == 0:
                fila.pop(0)
        res.resgates.append({"resgate": lan, "consumidas": consumidas, "excesso": falta})
        if falta > 0:
            pid = f"PEN-RESGATE_ACIMA_DO_APLICADO-{lan.banco}-{lan.ref_origem}"
            orig = ", ".join(f"{a.ref_origem} ({fmt_dinheiro(u)})" for a, u in consumidas) or "nenhuma"
            res.pendencias.append(Pendencia(
                pid, "RESGATE_ACIMA_DO_APLICADO", lan.ref_origem, falta,
                f"resgate de {fmt_dinheiro(lan.valor)} em {lan.data.isoformat()} excede em {fmt_dinheiro(falta)} o saldo aplicado "
                f"no mês (FIFO: {orig}). A linha ficou inteira em 1.1.02.001. Proposta: o excesso é rendimento "
                f"(3.2.01) — ou havia saldo aplicado antes de 01/09, que o extrato não mostra. Não dividi a linha", "Lucca",
            ))
            res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha(lan), "resgate"))
            for a, u in consumidas:
                res.rastro_pendencias.append(_rastro(pid, a, -u, linha(a), "aplicação consumida (FIFO)"))
    return res
