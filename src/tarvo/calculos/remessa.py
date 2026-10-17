"""Remessa: elegibilidade de cada operação da Ponte e comissão por lojista.

Responsabilidade: decidir, linha a linha do anexo, onde cada operação termina e calcular
a comissão REMESSA (`COM-<cnpj>-REMESSA`). Regras usadas (todas de `regras.yaml`):
- remessa.liquidacao_no_mes_seguinte (CONFIRMADO 20:48): competência pela data de contratação;
- remessa.operacao_duplicada (CONFIRMADO 20:48): Nº de operação é único, conta uma vez
  (fica a linha que não é "reprocessada"); cópias com conteúdo diferente → pendência;
- remessa.status_aprovado_com_ressalva (CONFIRMADO 20:48): não muda nada;
- remessa.spread_negativo (CONFIRMADO 20:48): fora da comissão e da nota → divergência;
- ponte.participacao_tarvo + ponte.base_participacao (CONFIRMADO 20:48): 50% do Spread R$;
- remessa.arredondamento_participacao (CONFIRMADO 21:13, Q-H d): arredondamento comum por
  operação (meio para longe do zero), depois soma.

Destino de cada linha (o validador confere que cada uma aparece exatamente uma vez):
COM-<cnpj>-REMESSA (elegível) · EXC-REMESSA-<motivo> (exclusão anotada, valor = Spread R$) ·
PEN-… (pendência). O spread negativo também gera DIV-<Nº Operação> (divergencias.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.cadastro import Cadastro
from tarvo.calculos.comissoes import id_comissao, ordem_comissao
from tarvo.formatos import centavos, cnpj_valido, modo_arredondamento, normalizar_cnpj
from tarvo.modelo import OperacaoPonte, Pendencia
from tarvo.regras import valor_da_regra

LINHA = "REMESSA"
CAMPOS_FINANCEIROS = (
    "data_contratacao", "data_liquidacao", "cnpj_cliente_bruto", "moeda", "valor_me",
    "taxa_cliente", "ptax_ref", "valor_brl", "spread_brl", "iof_brl",
)


@dataclass
class ClassificacaoRemessa:
    elegiveis: list[tuple[OperacaoPonte, str]] = field(default_factory=list)  # (op, cnpj)
    negativos: list[tuple[OperacaoPonte, str]] = field(default_factory=list)
    excluidas: list[tuple[OperacaoPonte, str, str]] = field(default_factory=list)  # (op, motivo, nota)
    pendentes: list[tuple[OperacaoPonte, str, str]] = field(default_factory=list)  # (op, tipo, motivo)


@dataclass
class ResultadoRemessa:
    comissoes: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    por_operacao: dict[tuple[str, int], Decimal] = field(default_factory=dict)  # (Nº, linha) → comissão
    comparacao_arredondamento: list[dict] = field(default_factory=list)


def id_exclusao(motivo: str) -> str:
    return f"EXC-{LINHA}-{motivo}"


def participacao(spread: Decimal, fracao: Decimal, modo: str) -> Decimal:
    """Participação × Spread R$, arredondada no centavo com o modo de remessa.arredondamento_participacao."""
    return centavos(spread * fracao, modo)


def modo_participacao(regras: dict) -> str:
    return modo_arredondamento(valor_da_regra(regras, "remessa.arredondamento_participacao"))


def classificar_remessa(
    operacoes: list[OperacaoPonte], competencia: tuple[int, int] | None, cadastro: Cadastro, regras: dict
) -> ClassificacaoRemessa:
    """Decide o destino de cada linha do anexo."""
    valor_da_regra(regras, "remessa.liquidacao_no_mes_seguinte")
    valor_da_regra(regras, "remessa.operacao_duplicada")
    valor_da_regra(regras, "remessa.status_aprovado_com_ressalva")
    valor_da_regra(regras, "remessa.spread_negativo")
    cls = ClassificacaoRemessa()
    if competencia is None:
        for op in operacoes:
            cls.pendentes.append((op, "COMPETENCIA_DESCONHECIDA", "relatório sem 'Competência: MM/AAAA' no cabeçalho"))
        return cls

    no_mes: list[OperacaoPonte] = []
    for op in operacoes:
        if (op.data_contratacao.year, op.data_contratacao.month) != competencia:
            cls.excluidas.append((op, "FORA_COMPETENCIA",
                                  f"contratada em {op.data_contratacao.isoformat()}, fora da competência "
                                  f"{competencia[1]:02d}/{competencia[0]} (competência = data de contratação, Helena 20:48)"))
        else:
            no_mes.append(op)

    por_numero: dict[str, list[OperacaoPonte]] = {}
    for op in no_mes:
        por_numero.setdefault(op.ref_origem, []).append(op)

    unicas: list[OperacaoPonte] = []
    for numero, copias in por_numero.items():
        if len(copias) == 1:
            unicas.append(copias[0])
            continue
        assinaturas = {tuple(getattr(c, f) for f in CAMPOS_FINANCEIROS) for c in copias}
        if len(assinaturas) > 1:
            for c in copias:
                cls.pendentes.append((c, "REMESSA_DUPLICATA_DIVERGENTE",
                                      f"Nº {numero} aparece {len(copias)}× com valores diferentes "
                                      f"(R{', R'.join(str(x.linha_planilha) for x in copias)}): não dá para saber qual vale"))
            continue
        nao_reprocessadas = [c for c in copias if (c.observacao or "").strip().lower() != "reprocessada"]
        fica = (nao_reprocessadas or copias)[0]
        unicas.append(fica)
        for c in copias:
            if c is not fica:
                cls.excluidas.append((c, "DUPLICATA",
                                      f"Nº {numero} repetido; conta uma vez (R{fica.linha_planilha}); "
                                      f"obs {c.observacao!r} (Helena 20:48: número da operação é único)"))

    for op in unicas:
        cnpj = normalizar_cnpj(op.cnpj_cliente_bruto)
        if cnpj is None or not cnpj_valido(cnpj):
            cls.pendentes.append((op, "REMESSA_CNPJ_INVALIDO", f"CNPJ Cliente ilegível ou com DV inválido: {op.cnpj_cliente_bruto!r}"))
            continue
        if cnpj not in cadastro.lojistas:
            cls.pendentes.append((op, "REMESSA_SEM_CADASTRO", f"CNPJ {cnpj} ({op.cliente}) não está na planilha de taxas"))
            continue
        if op.spread_brl < 0:
            cls.negativos.append((op, cnpj))
            cls.excluidas.append((op, "SPREAD_NEGATIVO", valor_da_regra(regras, "remessa.motivo_spread_negativo")))
            continue
        cls.elegiveis.append((op, cnpj))
    return cls


def comissao_remessa(cls: ClassificacaoRemessa, cadastro: Cadastro, regras: dict) -> ResultadoRemessa:
    """Comissão REMESSA por lojista, com rastro, exclusões anotadas e pendências."""
    if valor_da_regra(regras, "ponte.base_participacao") != "SPREAD_REALIZADO":
        raise ValueError("ponte.base_participacao diferente de SPREAD_REALIZADO não suportado")
    modo = modo_participacao(regras)
    fracao = Decimal(str(valor_da_regra(regras, "ponte.participacao_tarvo")))

    res = ResultadoRemessa()
    totais: dict[str, Decimal] = {}
    spreads: dict[str, Decimal] = {}
    qtd: dict[str, int] = {}
    for op, cnpj in cls.elegiveis:
        com = participacao(op.spread_brl, fracao, modo)
        res.por_operacao[(op.ref_origem, op.linha_planilha)] = com
        totais[cnpj] = totais.get(cnpj, Decimal("0")) + com
        spreads[cnpj] = spreads.get(cnpj, Decimal("0")) + op.spread_brl
        qtd[cnpj] = qtd.get(cnpj, 0) + 1
        nota = f"{fracao * 100:.0f}% de Spread R$ {op.spread_brl}; status {op.status_compliance}"
        if op.data_liquidacao.month != op.data_contratacao.month:
            nota += f"; liquidada em {op.data_liquidacao.isoformat()} (competência pela contratação)"
        res.rastro.append(_linha_rastro(id_comissao(cnpj, LINHA), op, com, nota))

    for cnpj in totais:
        res.comissoes.append({
            "id_saida": id_comissao(cnpj, LINHA),
            "cnpj": cnpj,
            "lojista": cadastro.lojistas[cnpj].nome,
            "linha_negocio": LINHA,
            "comissao_brl": totais[cnpj],
            "qtd_transacoes": qtd[cnpj],
        })
        uma_vez = participacao(spreads[cnpj], fracao, modo)
        res.comparacao_arredondamento.append({
            "cnpj": cnpj, "por_operacao": totais[cnpj], "total_uma_vez": uma_vez, "diferenca": totais[cnpj] - uma_vez,
        })
    res.comissoes.sort(key=ordem_comissao)

    for op, motivo, nota in cls.excluidas:
        res.rastro.append(_linha_rastro(id_exclusao(motivo), op, op.spread_brl, f"exclusão anotada (valor = Spread R$): {nota}"))

    grupos: dict[str, list] = {}
    for op, tipo, motivo in cls.pendentes:
        pid = f"PEN-{tipo}-{op.ref_origem}"
        grupos.setdefault(pid, [tipo, op.ref_origem, motivo, []])[3].append(op)
    for pid, (tipo, ref, motivo, ops) in grupos.items():
        valor = sum((o.spread_brl for o in ops), Decimal("0"))
        res.pendencias.append(Pendencia(pid, tipo, ref, valor, f"{motivo}. valor_brl = Spread R$ (informativo)", "financeiro (Helena)"))
        for o in ops:
            res.rastro.append(_linha_rastro(pid, o, o.spread_brl, "Spread R$ da operação em pendência"))
    return res


def _linha_rastro(id_saida: str, op: OperacaoPonte, valor: Decimal, nota: str) -> dict:
    return {
        "id_saida": id_saida,
        "arquivo_origem": op.arquivo_origem,
        "ref_origem": op.ref_origem,
        "valor": valor,
        "linha_arquivo": op.linha_planilha,
        "tipo_lancamento": LINHA,
        "spread_brl": op.spread_brl,
        "nota": nota,
    }
