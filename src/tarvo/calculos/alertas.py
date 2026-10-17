"""Alertas que não mudam número nenhum: só avisam quem precisa saber.

Alerta de antecipação (Q-N 6, regra `checkout.alerta_antecipacao`, D66): a antecipação é sobre o que o
lojista já vendeu, e não há trava. Para lojista SEM histórico (sem vigência na planilha antes do mês e sem
nenhuma linha com `data_venda_original` anterior ao mês), a antecipação acumulada no mês não pode passar das
vendas acumuladas até a data. Exposição por data (D73) = antecipações − reversões − (vendas − estornos),
acumulados até a data; com pico > 0, uma pendência ALERTA_ANTECIPACAO para "Helena + comercial": valor = a
exposição no pico, com a data; rastro = as antecipações e reversões (bruto, com sinal) e as vendas e estornos
(− bruto) até a data do pico, então a soma do rastro é o valor. Para lojista com histórico a
antecipação cobre recebíveis de meses anteriores, que não estão nos dados: o alerta seria alarme falso.
`id_saida`: `PEN-ALERTA_ANTECIPACAO-<cnpj ou EC<n>>`. Não muda comissão, nota nem divergência.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from tarvo.cadastro import Cadastro
from tarvo.formatos import fmt_dinheiro
from tarvo.modelo import Pendencia, TransacaoOrbe
from tarvo.regras import valor_da_regra

ZERO = Decimal("0")
ANTECIPACOES = ("ANTECIPACAO", "REVERSAO ANTECIPACAO")
VENDAS = ("VENDA", "ESTORNO")


@dataclass
class ResultadoAlertas:
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)


def _sem_historico(ident: str, ts: list[TransacaoOrbe], cadastro: Cadastro, inicio_mes: date) -> bool:
    if any(t.data_venda_original and t.data_venda_original < inicio_mes for t in ts):
        return False
    for _, vig in cadastro.linhas_por_cnpj.get(ident, []):
        if vig is None or vig.inicio is None or vig.inicio < inicio_mes:
            return False
    return True


def alerta_antecipacao(transacoes: list[TransacaoOrbe], cadastro: Cadastro, competencia: tuple[int, int],
                       regras: dict) -> ResultadoAlertas:
    cfg = valor_da_regra(regras, "checkout.alerta_antecipacao")
    inicio_mes = date(competencia[0], competencia[1], 1)
    por_lojista: dict[str, list[TransacaoOrbe]] = {}
    for t in transacoes:
        ident = cadastro.por_ec.get(t.cod_estabelecimento) or f"EC{t.cod_estabelecimento}"
        por_lojista.setdefault(ident, []).append(t)
    res = ResultadoAlertas()
    for ident, ts in sorted(por_lojista.items()):
        if not any(t.tipo_lancamento == "ANTECIPACAO" for t in ts) or not _sem_historico(ident, ts, cadastro, inicio_mes):
            continue
        ts = sorted(ts, key=lambda t: (t.data_movimento, t.linha_arquivo))
        # D73: exposição por data = antecipações − reversões − (vendas − estornos), acumulados até a data; vale o pico
        exposicao, serie = ZERO, []
        for d in sorted({t.data_movimento for t in ts}):
            exposicao += sum((t.valor_bruto if t.tipo_lancamento in ANTECIPACOES else -t.valor_bruto
                              for t in ts if t.data_movimento == d and t.tipo_lancamento in ANTECIPACOES + VENDAS), ZERO)
            serie.append((d, exposicao))
        d, pico = max(serie, key=lambda x: (x[1], -x[0].toordinal()))  # o maior; no empate, a primeira data
        if pico <= 0:
            continue
        antecipado = sum((t.valor_bruto for t in ts if t.data_movimento <= d and t.tipo_lancamento == "ANTECIPACAO"), ZERO)
        revertido = -sum((t.valor_bruto for t in ts if t.data_movimento <= d and t.tipo_lancamento == "REVERSAO ANTECIPACAO"), ZERO)
        vendido = sum((t.valor_bruto for t in ts if t.data_movimento <= d and t.tipo_lancamento in VENDAS), ZERO)
        reversoes = [f"{t.id_referencia} revertida em {t.data_movimento.strftime('%d/%m')} ({t.ref_origem})"
                     for t in ts if t.tipo_lancamento == "REVERSAO ANTECIPACAO"]
        ate = [t for t in ts if t.data_movimento <= d and t.tipo_lancamento in ANTECIPACOES + VENDAS]
        nome = cadastro.lojistas[ident].nome if ident in cadastro.lojistas else ts[0].nome_estabelecimento
        pid = f"PEN-ALERTA_ANTECIPACAO-{ident}"
        res.pendencias.append(Pendencia(
            pid, "ALERTA_ANTECIPACAO", "|".join(t.ref_origem for t in ate), pico,
            f"{nome} ({ident}): exposição máxima no mês de {fmt_dinheiro(pico)} em {d.isoformat()} (antecipado "
            f"{fmt_dinheiro(antecipado)} − revertido {fmt_dinheiro(revertido)} − vendido líquido de estornos "
            f"{fmt_dinheiro(vendido)}, acumulados até a data; lojista sem histórico antes do mês). Reversões no mês: "
            f"{', '.join(reversoes) or 'nenhuma'}; no fim do mês a exposição é {fmt_dinheiro(serie[-1][1])}. Alerta, não "
            f"muda nenhum valor. {cfg['citacao_fonte']}: '{cfg['citacao']}' valor_brl = exposição no pico",
            cfg["quem_decide"],
        ))
        for t in ate:
            sinal = 1 if t.tipo_lancamento in ANTECIPACOES else -1
            res.rastro.append({
                "id_saida": pid, "arquivo_origem": t.arquivo_origem, "ref_origem": t.ref_origem,
                "valor": sinal * t.valor_bruto, "linha_arquivo": t.linha_arquivo, "tipo_lancamento": t.tipo_lancamento,
                "valor_bruto": t.valor_bruto,
                "nota": {"ANTECIPACAO": "antecipação (+ bruto)", "REVERSAO ANTECIPACAO": "reversão (bruto negativo)"}.get(
                    t.tipo_lancamento, "venda/estorno até a data do pico (− bruto)"),
            })
    return res
