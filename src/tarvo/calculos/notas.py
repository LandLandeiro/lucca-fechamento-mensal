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
- notas.conferencia_repasse (ASSUMO Lucca): repasse previsto pela Ponte × nota REMESSA.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.calculos.remessa import ClassificacaoRemessa, modo_participacao, participacao
from tarvo.formatos import fmt_dinheiro
from tarvo.modelo import Pendencia
from tarvo.regras import valor_da_regra

ZERO = Decimal("0")
_RE_DATA_CREDITO = re.compile(r"creditad[oa]\s+em\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)


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
    spread_declarado: Decimal | None,
    cls: ClassificacaoRemessa,
    corpo_email: str,
    arquivo_ponte: str,
    regras: dict,
) -> tuple[list[Pendencia], list[dict]]:
    """Repasse previsto pela Ponte (participação × total declarado) × nota REMESSA → pendência para a Helena.

    A diferença é decomposta, a partir da classificação, em spreads negativos (a Ponte desconta;
    contestar) e duplicata (a Ponte pagaria a mais; avisar). Valores calculados, nunca fixos.
    """
    valor_da_regra(regras, "notas.conferencia_repasse")
    if spread_declarado is None:
        return [], []
    fracao = Decimal(str(valor_da_regra(regras, "ponte.participacao_tarvo")))
    modo = modo_participacao(regras)
    previsto = participacao(spread_declarado, fracao, modo)
    diferenca = nota_remessa - previsto
    if diferenca == 0:
        return [], []

    m = _RE_DATA_CREDITO.search(corpo_email or "")
    quando = f"TED da Ponte previsto para {m.group(1)[:5]}" if m else "data do TED da Ponte não informada no e-mail"
    # cada linha do relatório que não está na nota muda o repasse em −participação(spread)
    rotulos = {
        "SPREAD_NEGATIVO": ("spreads negativos", "contestar"),
        "DUPLICATA": ("duplicata", "a Ponte pagaria a mais; avisar"),
        "FORA_COMPETENCIA": ("fora da competência", "conferir"),
        "PENDENCIA": ("operações em pendência", "decidir a pendência"),
    }
    componentes: dict[str, list] = {}
    for op, motivo, _ in cls.excluidas:
        componentes.setdefault(motivo, []).append((op, -participacao(op.spread_brl, fracao, modo)))
    for op, _, _ in cls.pendentes:
        componentes.setdefault("PENDENCIA", []).append((op, -participacao(op.spread_brl, fracao, modo)))
    soma = sum((v for itens in componentes.values() for _, v in itens), ZERO)
    residuo = diferenca - soma

    partes = []
    for motivo in [m for m in rotulos if m in componentes]:
        itens = componentes[motivo]
        total = sum((v for _, v in itens), ZERO)
        nome, acao = rotulos[motivo]
        sinal = "− " if total < 0 and partes else ("+ " if partes else "")
        valor_txt = fmt_dinheiro(abs(total)) if partes else fmt_dinheiro(total)
        partes.append(f"{sinal}{valor_txt} ({nome} {', '.join(o.ref_origem for o, _ in itens)}, {acao})")
    if residuo:
        partes.append(f"{'+ ' if residuo > 0 else '− '}{fmt_dinheiro(abs(residuo))} "
                      f"(arredondamento por operação contra {fracao * 100:.0f}% do total da Ponte)")
    motivo_txt = (f"{quando}. Pelo total do relatório da Ponte ({fmt_dinheiro(spread_declarado)}) o repasse seria "
                  f"{fmt_dinheiro(previsto)}; faturamos {fmt_dinheiro(nota_remessa)}. Diferença {fmt_dinheiro(diferenca)} = "
                  + " ".join(partes) + ".")
    pid = "PEN-CONFERENCIA_REPASSE-REMESSA"
    pend = Pendencia(pid, "CONFERENCIA_REPASSE", "Spread total R$ (relatório da Ponte)", diferenca, motivo_txt, "Helena")
    rastro = [{
        "id_saida": pid, "arquivo_origem": op.arquivo_origem, "ref_origem": op.ref_origem, "valor": v,
        "linha_arquivo": op.linha_planilha, "tipo_lancamento": "REMESSA", "spread_brl": op.spread_brl,
        "nota": f"−participação de {motivo.lower()}: muda o repasse previsto pela Ponte",
    } for motivo, itens in componentes.items() for op, v in itens]
    if residuo:
        rastro.append({"id_saida": pid, "arquivo_origem": arquivo_ponte, "ref_origem": "Spread total R$:",
                       "valor": residuo, "linha_arquivo": 0, "tipo_lancamento": "REMESSA",
                       "nota": "arredondamento por operação contra a participação do total declarado pela Ponte"})
    return [pend], rastro
