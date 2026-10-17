"""Notas fiscais a emitir: tomador, linha de negócio, valor e discriminação.

Responsabilidade: transformar as comissões em notas segundo as regras de faturamento e
gerar as pendências que dependem delas. `id_saida`: `NF-<cnpj_tomador>-<CHECKOUT|REMESSA>`.
O rastro de cada nota reaponta as mesmas linhas de origem da comissão.

Regras usadas (todas de `regras.yaml`):
- notas.estrutura_nf_checkout (CONFIRMADO 20:47): 1 nota por lojista por mês = comissão do
  mês; zero não emite; negativo não emite e vira pendência para a Helena;
- ponte.tomador_nf_remessa (CONFIRMADO 20:47): 1 nota só, tomadora Ponte Câmbio, total da
  participação do mês;
- notas.discriminacao (ASSUMO Lucca): textos com {competencia};
- notas.conferencia_repasse (CONFIRMADO 22:33, Q-K): conferir o TED da Ponte quando cair, sem
  prever desconto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.calculos.remessa import ClassificacaoRemessa
from tarvo.formatos import fmt_dinheiro
from tarvo.modelo import Pendencia
from tarvo.regras import valor_da_regra

ZERO = Decimal("0")
_RE_DATA_CREDITO = re.compile(r"creditad[oa]\s+em\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
# o que o total do relatório da Ponte inclui e o fechamento não conta: motivo → (singular, plural)
_ROTULOS_RELATORIO = {
    "SPREAD_NEGATIVO": ("o spread negativo", "spreads negativos"),
    "DUPLICATA": ("a duplicata", "duplicatas"),
    "FORA_COMPETENCIA": ("a operação fora da competência", "operações fora da competência"),
    "PENDENCIA": ("a operação em pendência", "operações em pendência"),
}
_EM_CONTESTACAO = {"SPREAD_NEGATIVO", "DUPLICATA"}  # Q-L: entram na contestação com a Ponte


@dataclass
class ResultadoNotas:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro_pendencias: list[dict] = field(default_factory=list)


def id_nota(cnpj: str, linha: str) -> str:
    return f"NF-{cnpj}-{linha}"


def competencia_texto(competencia: tuple[int, int]) -> str:
    ano, mes = competencia
    return f"{mes:02d}/{ano}"


def notas_a_emitir(
    comissoes: list[dict],
    rastro_comissoes: list[dict],
    regras: dict,
    competencia_checkout: tuple[int, int],
    competencia_remessa: tuple[int, int] | None,
) -> ResultadoNotas:
    """Notas a emitir (CHECKOUT por lojista; REMESSA para a Ponte) e pendências de nota negativa."""
    valor_da_regra(regras, "notas.estrutura_nf_checkout")
    textos = valor_da_regra(regras, "notas.discriminacao")
    tomador_remessa = valor_da_regra(regras, "ponte.tomador_nf_remessa")
    por_id: dict[str, list[dict]] = {}
    for l in rastro_comissoes:
        por_id.setdefault(l["id_saida"], []).append(l)

    res = ResultadoNotas()
    for c in comissoes:
        if c["linha_negocio"] != "CHECKOUT":
            continue
        linhas = por_id.get(c["id_saida"], [])
        if c["comissao_brl"] > 0:
            nid = id_nota(c["cnpj"], "CHECKOUT")
            res.linhas.append({
                "id_saida": nid,
                "tomador_cnpj": c["cnpj"],
                "tomador": c["lojista"],
                "linha_negocio": "CHECKOUT",
                "valor_brl": c["comissao_brl"],
                "discriminacao": textos["CHECKOUT"].format(competencia=competencia_texto(competencia_checkout)),
                "competencia": competencia_texto(competencia_checkout),
                "id_comissao": c["id_saida"],
                "qtd_linhas_origem": len(linhas),
            })
            res.rastro.extend({**l, "id_saida": nid} for l in linhas)
        elif c["comissao_brl"] < 0:
            nao_nulas = [l for l in linhas if l["valor"] != 0]
            detalhe = "; ".join(f"{l['ref_origem']} (L{l['linha_arquivo']}) {fmt_dinheiro(l['valor'])}: {l['nota']}"
                                for l in nao_nulas[:3])
            if len(nao_nulas) > 3:
                detalhe += f"; e mais {len(nao_nulas) - 3} linhas"
            pid = f"PEN-NF_NEGATIVA-{c['cnpj']}"
            res.pendencias.append(Pendencia(
                pid, "NF_NEGATIVA", c["id_saida"], c["comissao_brl"],
                f"comissão CHECKOUT do mês negativa ({fmt_dinheiro(c['comissao_brl'])}): não emite nota e não passa "
                f"para o mês seguinte automaticamente (Helena 20:47). Linhas não nulas: {detalhe}",
                "Helena",
            ))
            res.rastro_pendencias.extend({**l, "id_saida": pid} for l in linhas)
        # zero: não emite e não há o que decidir

    remessa = [c for c in comissoes if c["linha_negocio"] == "REMESSA"]
    total_remessa = sum((c["comissao_brl"] for c in remessa), ZERO)
    if remessa and total_remessa > 0:
        if competencia_remessa is None:
            raise ValueError("competência da remessa desconhecida: não há como montar a discriminação da nota")
        nid = id_nota(str(tomador_remessa["cnpj"]), "REMESSA")
        linhas = [l for c in remessa for l in por_id.get(c["id_saida"], [])]
        res.linhas.append({
            "id_saida": nid,
            "tomador_cnpj": str(tomador_remessa["cnpj"]),
            "tomador": tomador_remessa["nome"],
            "linha_negocio": "REMESSA",
            "valor_brl": total_remessa,
            "discriminacao": textos["REMESSA"].format(competencia=competencia_texto(competencia_remessa)),
            "competencia": competencia_texto(competencia_remessa),
            "id_comissao": ", ".join(c["id_saida"] for c in remessa),
            "qtd_linhas_origem": len(linhas),
        })
        res.rastro.extend({**l, "id_saida": nid} for l in linhas)
    return res


def conferencia_repasse(
    nota_remessa: Decimal,
    rastro_nota: list[dict],
    spread_declarado: Decimal | None,
    cls: ClassificacaoRemessa,
    corpo_email: str,
    regras: dict,
) -> tuple[list[Pendencia], list[dict]]:
    """Pendência para a Helena conferir o TED da Ponte quando cair (Q-K, Helena 22:33).

    Não prevê desconto nem diferença: a Ponte ainda não disse como vai pagar ("Não conte que ela
    vai descontar nada do repasse"). Informa o faturado (valor da pendência, rastro = linhas da
    nota REMESSA) e o total do relatório da Ponte com o que ele inclui e o fechamento não conta.
    """
    valor_da_regra(regras, "notas.conferencia_repasse")
    if nota_remessa <= 0:
        return [], []
    m = _RE_DATA_CREDITO.search(corpo_email or "")
    quando = f"previsto {m.group(1)[:5]}" if m else "data não informada no e-mail da Ponte"
    texto = f"Conferir o TED da Ponte quando cair ({quando}). Faturado: {fmt_dinheiro(nota_remessa)}."
    if spread_declarado is not None:
        grupos: dict[str, list] = {}
        for op, motivo, _ in cls.excluidas:
            grupos.setdefault(motivo, []).append(op)
        for op, _, _ in cls.pendentes:
            grupos.setdefault("PENDENCIA", []).append(op)
        partes, em_contestacao = [], 0
        for motivo, (um, varios) in _ROTULOS_RELATORIO.items():
            ops = grupos.get(motivo)
            if not ops:
                continue
            soma = fmt_dinheiro(sum((o.spread_brl for o in ops), ZERO))
            if len(ops) == 1:
                partes.append(f"{um} {ops[0].ref_origem} ({soma})")
            else:
                partes.append(f"{len(ops)} {varios} ({soma})")
            em_contestacao += motivo in _EM_CONTESTACAO
        texto += f" Total do relatório da Ponte: {fmt_dinheiro(spread_declarado)}"
        if partes:
            texto += ", que inclui " + (" e ".join([", ".join(partes[:-1]), partes[-1]]) if len(partes) > 1 else partes[0])
            if em_contestacao == len(partes):
                texto += ", ambos em contestação" if len(partes) == 2 else ", em contestação"
        texto += "."
    pid = "PEN-CONFERENCIA_REPASSE-REMESSA"
    ref = rastro_nota[0]["id_saida"] if rastro_nota else "nota REMESSA"
    pend = Pendencia(pid, "CONFERENCIA_REPASSE", ref, nota_remessa, texto, "Helena")
    return [pend], [{**l, "id_saida": pid} for l in rastro_nota]
