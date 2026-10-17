"""Conferências entre fontes, sem mudar a conta de nenhum lançamento (`classificacao_extratos.conferencias`).

1. Transferência entre contas: cada saída Aurora→Meridiano (regra transferencia_meridiano)
   casa com uma entrada de mesma titularidade (regra mesma_titularidade) de mesmo valor em
   até 1 dia útil. Sem par → pendência "em trânsito". Entrada sem saída no mês → pendência, a não
   ser que case com uma pendência "em trânsito" do mês anterior (`--pendencias-anteriores`, D50):
   aí sai como pendência anterior resolvida, não como pendência nova.
2. Aportes da remessa: por lojista, Σ PIX RECEB no Meridiano × Σ (Valor R$ + IOF) das
   operações únicas da Ponte (a duplicata conta uma vez). Sobra igual a um aporte → pendência
   desse aporte; outra sobra ≠ 0 → pendência do lojista. Lojista sem nenhum aporte identificado,
   havendo PIX RECEB sem regra, fica "não conferido" (sem pendência: seria alarme falso).
3. Aplicação × resgate (FIFO): resgate acima do saldo aplicado no mês é sempre reportado. Com
   `resgate_acima_do_aplicado` = SALDO_APLICADO_ANTERIOR_SE_HA_RENDIMENTO (D49, refina a D36), o excesso
   só é saldo aplicado anterior se o extrato do mês tem linha própria de rendimento (regra
   rendimento_aplicacao); sem ela, vira pendência para a Helena. PENDENCIA e SALDO_APLICADO_ANTERIOR
   forçam um dos dois. A linha nunca é dividida.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from datetime import date, timedelta
from decimal import Decimal

from tarvo.formatos import fmt_dinheiro, mes_seguinte, nome_mes
from tarvo.modelo import LancamentoBancario, OperacaoPonte, Pendencia

ZERO = Decimal("0")


@dataclass
class ResultadoConferencias:
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro_pendencias: list[dict] = field(default_factory=list)
    transferencias: list[tuple[LancamentoBancario, LancamentoBancario | None]] = field(default_factory=list)
    resolvidas: list[dict] = field(default_factory=list)  # pendências do mês anterior resolvidas neste mês (D50)
    aportes: list[dict] = field(default_factory=list)
    resgates: list[dict] = field(default_factory=list)


def dias_uteis_entre(a: date, b: date, feriados: frozenset[date] = frozenset()) -> int:
    """Dias úteis (seg–sex fora de `feriados`, regra `calendario.feriados_nacionais`, D59) de a até b, sem contar a."""
    if b < a:
        return -dias_uteis_entre(b, a, feriados)
    n, d = 0, a
    while d < b:
        d += timedelta(days=1)
        n += d.weekday() < 5 and d not in feriados
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
    resgate_acima: str = "PENDENCIA",
    pendencias_anteriores: list[dict] | None = None,
    feriados: frozenset[date] = frozenset(),
    aporte_sem_operacao: dict | None = None,
) -> ResultadoConferencias:
    """Roda as três conferências. `regra_por_lancamento` (banco, ref) → nome da regra aplicada;
    `feriados` = datas que não são dia útil (`calendario.feriados_nacionais`)."""
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
        par = next((e for e in entradas
                    if e.valor == -saida.valor and 0 <= dias_uteis_entre(saida.data, e.data, feriados) <= 1), None)
        res.transferencias.append((saida, par))
        if par is not None:
            entradas.remove(par)
            continue
        pid = f"PEN-TRANSFERENCIA_EM_TRANSITO-{saida.banco}-{saida.ref_origem}"
        proximo = nome_mes(mes_seguinte(saida.data)[1])  # D48: mês derivado da data, nunca fixo
        res.pendencias.append(Pendencia(
            pid, "TRANSFERENCIA_EM_TRANSITO", saida.ref_origem, saida.valor,
            f"transferência de {fmt_dinheiro(-saida.valor)} saiu do Aurora em {saida.data.isoformat()} e não tem TED de "
            f"mesma titularidade no Meridiano em até 1 dia útil: em trânsito, cai no Meridiano no dia útil seguinte "
            f"(Q-F 4c); conferir no extrato de {proximo}", f"analista (conferir em {proximo})",
        ))
        res.rastro_pendencias.append(_rastro(pid, saida, saida.valor, linha(saida), "transferência sem par no Meridiano"))
    em_transito = [p for p in (pendencias_anteriores or []) if p.get("tipo") == "TRANSFERENCIA_EM_TRANSITO"]
    for e in entradas:  # entrada de mesma titularidade sem saída no Aurora
        anterior = _transito_anterior(e, em_transito, feriados)
        if anterior is not None:  # D50: a transferência em trânsito do mês anterior caiu agora
            em_transito.remove(anterior)
            m = _RE_DATA_SAIDA.search(anterior.get("motivo", ""))
            mes_ant = nome_mes(date.fromisoformat(m.group(1)).month) if m else "mês anterior"
            res.resolvidas.append({
                "id_pendencia_anterior": anterior["id_saida"], "tipo": anterior["tipo"], "ref_origem": anterior["ref_origem"],
                "valor_brl": Decimal(anterior["valor_brl"]), "resolvida_por": f"LAN-{e.banco}-{e.ref_origem}",
                "data_resolucao": e.data,
                "motivo": f"pendência de {mes_ant} resolvida: a transferência de {fmt_dinheiro(-Decimal(anterior['valor_brl']))}"
                          f" que saiu do Aurora em {m.group(1) if m else '?'} caiu no Meridiano em {e.data.isoformat()} ({e.ref_origem})",
            })
            continue
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
            # D87 (Q-N 5): é dinheiro de remessa que ainda não foi feita; vira acompanhamento, com próximo passo
            cfg = aporte_sem_operacao or {}
            proximo = nome_mes(mes_seguinte(lan.data)[1])
            pid = f"PEN-ACOMPANHAMENTO_APORTE-{lan.banco}-{lan.ref_origem}"
            res.pendencias.append(Pendencia(
                pid, "ACOMPANHAMENTO_APORTE", lan.ref_origem, lan.valor,
                f"Acompanhamento: {nomes.get(cnpj, cnpj)}: aportes no Meridiano somam {fmt_dinheiro(recebido)} e as "
                f"operações da Ponte (Valor R$ + IOF) {fmt_dinheiro(devido.get(cnpj, ZERO))}; a sobra é exatamente o PIX de "
                f"{lan.data.isoformat()} ({fmt_dinheiro(lan.valor)}), recurso do lojista para remessa que ainda não foi feita, "
                f"em 2.1.02.001. {cfg.get('citacao_fonte', '')}: '{cfg.get('citacao', '')}' Próximo passo: "
                f"{cfg.get('proximo_passo', 'conferir no mês seguinte')} ({proximo})", f"analista (conferir em {proximo})",
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
        if falta > 0 and _resgate_vira_pendencia(resgate_acima, por_regra):
            pid = f"PEN-RESGATE_ACIMA_DO_APLICADO-{lan.banco}-{lan.ref_origem}"
            orig = ", ".join(f"{a.ref_origem} ({fmt_dinheiro(u)})" for a, u in consumidas) or "nenhuma"
            res.pendencias.append(Pendencia(
                pid, "RESGATE_ACIMA_DO_APLICADO", lan.ref_origem, falta,
                f"resgate de {fmt_dinheiro(lan.valor)} em {lan.data.isoformat()} excede em {fmt_dinheiro(falta)} o saldo aplicado "
                f"no mês (FIFO: {orig}). A linha ficou inteira em 1.1.02.001. O extrato do mês não tem linha própria de "
                f"rendimento: o excesso pode ser rendimento (3.2.01) ou saldo aplicado antes de "
                f"{lan.data.replace(day=1).isoformat()}, que o extrato não mostra. Não dividi a linha", "Helena",
            ))
            res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha(lan), "resgate"))
            for a, u in consumidas:
                res.rastro_pendencias.append(_rastro(pid, a, -u, linha(a), "aplicação consumida (FIFO)"))
    return res


_RE_DATA_SAIDA = re.compile(r"saiu do Aurora em (\d{4}-\d{2}-\d{2})")


def _transito_anterior(e: LancamentoBancario, em_transito: list[dict], feriados: frozenset[date] = frozenset()) -> dict | None:
    """Pendência "em trânsito" do mês anterior com o mesmo valor (sinal oposto) e saída até 1 dia útil antes."""
    for p in em_transito:
        try:
            valor = Decimal(p["valor_brl"])
        except Exception:  # noqa: BLE001 — linha ilegível do arquivo anterior: não casa
            continue
        m = _RE_DATA_SAIDA.search(p.get("motivo", ""))
        if valor == -e.valor and m and 0 <= dias_uteis_entre(date.fromisoformat(m.group(1)), e.data, feriados) <= 1:
            return p
    return None


def _resgate_vira_pendencia(modo: str, por_regra: dict) -> bool:
    """D49: com SALDO_APLICADO_ANTERIOR_SE_HA_RENDIMENTO, o excesso só é saldo anterior se o extrato do mês
    tem linha própria de rendimento (a evidência da D36 em setembro)."""
    if modo == "SALDO_APLICADO_ANTERIOR_SE_HA_RENDIMENTO":
        return not por_regra.get("meridiano.rendimento_aplicacao")
    if modo in ("PENDENCIA", "SALDO_APLICADO_ANTERIOR"):
        return modo == "PENDENCIA"
    raise ValueError(f"resgate_acima_do_aplicado desconhecido: {modo!r}")
