"""Linhas do mês anterior que aguardavam contrato e agora têm contrato (Q-Q, D67).

A Helena (09:47): "Quando o comercial confirmar, a taxa vale desde o começo (10/09) e eu faturo setembro junto
com outubro. Então sim, outubro precisa puxar as linhas da Atlas de setembro que ficaram pendentes."

Com `--pendencias-anteriores` e `--orbe-anterior`: cada pendência SEM_CONTRATO_VIGENTE do mês anterior cujo EC
agora tem contrato na aba vigente traz de volta as transações dela (os ids estão no `ref_origem`, D55) do
relatório da Orbe do mês anterior. Elas entram na comissão do lojista neste mês, pela taxa contratada vigente na
data de cada uma, com rastro para o arquivo do mês anterior; a nota do mês cita que inclui essas linhas; a
pendência anterior sai em `pendencias_resolvidas.csv`. Sem `--orbe-anterior`, ou com transação faltando no
arquivo, nada é puxado e fica um aviso (nunca fatura em parte).
"""

from __future__ import annotations

from decimal import Decimal

from tarvo.cadastro import Cadastro
from tarvo.calculos.comissoes import id_comissao
from tarvo.calculos.notas import competencia_texto
from tarvo.formatos import fmt_dinheiro
from tarvo.leitores.orbe import LeituraOrbe
from tarvo.modelo import Aviso, TransacaoOrbe
from tarvo.regras import valor_da_regra

PREFIXO = "PEN-SEM_CONTRATO_VIGENTE-EC"


def retomar_sem_contrato(pendencias_anteriores: list[dict] | None, orbe_anterior: LeituraOrbe | None,
                         cadastro: Cadastro) -> tuple[list[tuple[dict, list[TransacaoOrbe]]], list[Aviso]]:
    """(pendência anterior, transações dela) para cada EC que agora tem contrato; e os avisos."""
    retomadas, avisos = [], []
    for p in pendencias_anteriores or []:
        if p.get("tipo") != "SEM_CONTRATO_VIGENTE" or not p.get("id_saida", "").startswith(PREFIXO):
            continue
        ec = p["id_saida"][len(PREFIXO):]
        if ec not in cadastro.por_ec:
            continue  # continua sem contrato: a pendência deste mês já cobre
        if orbe_anterior is None:
            avisos.append(Aviso("--pendencias-anteriores", p["id_saida"],
                                f"EC {ec} agora tem contrato: rode com --orbe-anterior para faturar as linhas do mês anterior (Q-Q)"))
            continue
        refs = p["ref_origem"].split("|")
        por_ref = {t.ref_origem: t for t in orbe_anterior.transacoes if t.cod_estabelecimento == ec}
        faltam = [r for r in refs if r not in por_ref]
        if faltam:
            avisos.append(Aviso(orbe_anterior.arquivo, p["id_saida"],
                                f"{len(faltam)} transações da pendência não estão no arquivo (ex.: {faltam[:3]}): nada puxado"))
            continue
        retomadas.append((p, [por_ref[r] for r in refs]))
    return retomadas, avisos


def _mes(ts: list[TransacaoOrbe]) -> tuple[int, int]:
    d = min(t.data_movimento for t in ts)
    return d.year, d.month


def marcar_retomadas(rastro: list[dict], retomadas: list[tuple[dict, list[TransacaoOrbe]]],
                     competencia: tuple[int, int]) -> None:
    """Anota no rastro da comissão que a linha é do mês anterior e de qual pendência veio."""
    origem = {(t.arquivo_origem, t.ref_origem): (p, ts) for p, ts in retomadas for t in ts}
    for l in rastro:
        achado = origem.get((l["arquivo_origem"], l["ref_origem"]))
        if achado:
            p, ts = achado
            l["nota"] = (f"linha de {competencia_texto(_mes(ts))} que aguardava contrato ({p['id_saida']}), faturada em "
                         f"{competencia_texto(competencia)} (Q-Q); " + (l.get("nota") or ""))


def complementar_discriminacao(notas: list[dict], retomadas: list[tuple[dict, list[TransacaoOrbe]]],
                               cadastro: Cadastro, regras: dict) -> None:
    complemento = valor_da_regra(regras, "notas.discriminacao")["CHECKOUT_COMPLEMENTO_ANTERIOR"]
    for p, ts in retomadas:
        cnpj = cadastro.por_ec[ts[0].cod_estabelecimento]
        for n in notas:
            if n["linha_negocio"] == "CHECKOUT" and n["tomador_cnpj"] == cnpj:
                n["discriminacao"] += complemento.format(n=len(ts), competencia=competencia_texto(_mes(ts)))


def resolvidas_sem_contrato(retomadas: list[tuple[dict, list[TransacaoOrbe]]], cadastro: Cadastro,
                            competencia: tuple[int, int]) -> list[dict]:
    linhas = []
    for p, ts in retomadas:
        cnpj = cadastro.por_ec[ts[0].cod_estabelecimento]
        linhas.append({
            "id_pendencia_anterior": p["id_saida"], "tipo": p["tipo"], "ref_origem": p["ref_origem"],
            "valor_brl": Decimal(p["valor_brl"]) if p.get("valor_brl") else None,
            "resolvida_por": id_comissao(cnpj),
            "motivo": (f"pendência de {competencia_texto(_mes(ts))} resolvida: {cadastro.lojistas[cnpj].nome} tem contrato na "
                       f"aba vigente; as {len(ts)} transações entram na comissão e na nota de {competencia_texto(competencia)} "
                       f"pela taxa contratada na data de cada uma (Q-Q). valor_brl = taxa que a Orbe cobrou "
                       f"({fmt_dinheiro(Decimal(p['valor_brl']))}), informativo"),
        })
    return linhas
