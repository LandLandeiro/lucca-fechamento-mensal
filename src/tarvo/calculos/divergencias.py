"""Divergências entre taxa contratada e taxa aplicada, transação por transação.

Responsabilidade: comparar o que a Orbe cobrou (`valor_taxa`) com a comissão pela taxa
contratada (a mesma calculada em `comissoes.py`, com a mesma taxa e fonte) e listar só a
diferença real. `id_saida`: `DIV-<id_transacao>`.

CHECKOUT (regras usadas, todas de `regras.yaml`):
- divergencias.tratamento (CONFIRMADO 20:05): divergência listada com transação e valor;
  nunca devolução automática; decisão da Helena;
- divergencias.estorno_de_venda_divergente (ASSUMO, D10): a divergência de uma venda é
  líquida com os estornos dela (`id_referencia`) no mesmo arquivo; só lista se o líquido
  ≠ 0. Estorno de venda que não está no arquivo (mês anterior) é avaliado sozinho;
- divergencias.tolerancia_checkout (ASSUMO, D09): 0 (mesmo truncamento da Orbe);
- divergencias.reversao_liquida_com_antecipacao (ASSUMO, D17): a REVERSAO ANTECIPACAO é
  líquida com a antecipação que ela anula, do mesmo jeito.

Transações em pendência (ex.: Atlas, sem contrato) não entram: não há taxa contratada
para comparar.

REMESSA (divergencias_remessa): ver a docstring da função; usa a classificação de
`calculos/remessa.py` (elegíveis acima da tolerância + todos os spreads negativos).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal

from tarvo.cadastro import Cadastro, linha_vigente
from tarvo.calculos.comissoes import ComissaoTransacao, ResultadoCheckout
from tarvo.calculos.remessa import ClassificacaoRemessa, participacao
from tarvo.formatos import CENTAVO, fmt_pct
from tarvo.modelo import ItemRastro, OperacaoPonte, Pendencia
from tarvo.regras import valor_da_regra

LINHA = "CHECKOUT"


@dataclass
class ResultadoDivergencias:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    grupos_zerados: int = 0  # vendas divergentes cujo estorno zerou a diferença (não listadas)


def id_divergencia(ref: str) -> str:
    return f"DIV-{ref}"


def diferenca(c: ComissaoTransacao) -> Decimal:
    """valor_taxa cobrado pela Orbe − comissão pela taxa contratada (ambos truncados no centavo)."""
    return c.transacao.valor_taxa - c.comissao


def divergencias_checkout(checkout: ResultadoCheckout, cadastro: Cadastro, regras: dict) -> ResultadoDivergencias:
    """Divergências de MDR e antecipação na Orbe."""
    decisao = "Helena"
    valor_da_regra(regras, "divergencias.tratamento")
    valor_da_regra(regras, "divergencias.estorno_de_venda_divergente")
    tolerancia = Decimal(str(valor_da_regra(regras, "divergencias.tolerancia_checkout")))
    ligados = ("ESTORNO", "REVERSAO ANTECIPACAO") if valor_da_regra(
        regras, "divergencias.reversao_liquida_com_antecipacao") else ("ESTORNO",)

    grupos: dict[str, list[ComissaoTransacao]] = {}
    for c in sorted(checkout.por_transacao.values(), key=lambda x: x.transacao.linha_arquivo):
        t = c.transacao
        if t.tipo_lancamento in ligados and t.id_referencia in checkout.por_transacao:
            grupos.setdefault(t.id_referencia, []).append(c)
        else:
            grupos.setdefault(t.ref_origem, []).insert(0, c)  # a venda (cabeça) vai primeiro

    res = ResultadoDivergencias()
    for cabeca_id, itens in grupos.items():
        cabeca = itens[0]
        if cabeca.transacao.ref_origem != cabeca_id:  # grupo sem a venda (não deveria acontecer)
            raise AssertionError(f"grupo de divergência {cabeca_id} sem a transação de origem")
        difs = [diferenca(c) for c in itens]
        liquido = sum(difs, Decimal("0"))
        if abs(liquido) <= tolerancia:
            if any(d != 0 for d in difs):
                res.grupos_zerados += 1
            continue

        t = cabeca.transacao
        aplicada = t.taxa_aplicada_pct / 100
        ligados = [c.transacao.ref_origem for c in itens[1:]]
        motivo = f"Orbe aplicou {fmt_pct(aplicada)}%; contratada {fmt_pct(cabeca.taxa_contratada)}% ({cabeca.fonte_taxa})"
        if t.tipo_lancamento == "ESTORNO":
            motivo += f"; estorno de venda de {t.data_venda_original.isoformat()} que não está no arquivo"
        if ligados:
            motivo += f"; líquida com {', '.join(ligados)} (parcial)"
        res.linhas.append({
            "id_saida": id_divergencia(cabeca_id),
            "cnpj": cabeca.cnpj,
            "linha_negocio": LINHA,
            "ref_origem": cabeca_id,
            "taxa_contratada_pct": cabeca.taxa_contratada,
            "taxa_aplicada_pct": aplicada,
            "diferenca_brl": liquido,
            "lojista": cadastro.lojistas[cabeca.cnpj].nome,
            "data": t.data_movimento,
            "tipo_lancamento": t.tipo_lancamento,
            "valor_bruto": sum((c.transacao.valor_bruto for c in itens), Decimal("0")),
            "comissao_contratada": sum((c.comissao for c in itens), Decimal("0")),
            "valor_taxa_orbe": sum((c.transacao.valor_taxa for c in itens), Decimal("0")),
            "direcao": "COBROU_A_MAIS" if liquido > 0 else "COBROU_A_MENOS",
            "liquida_com": ", ".join(ligados),
            "motivo": motivo,
            "decisao": decisao,
        })
        for c, d in zip(itens, difs):
            item = ItemRastro(id_divergencia(cabeca_id), c.transacao.arquivo_origem, c.transacao.ref_origem, d)
            res.rastro.append({
                "id_saida": item.id_saida,
                "arquivo_origem": item.arquivo_origem,
                "ref_origem": item.ref_origem,
                "valor": item.valor,
                "linha_arquivo": c.transacao.linha_arquivo,
                "tipo_lancamento": c.transacao.tipo_lancamento,
                "valor_bruto": c.transacao.valor_bruto,
                "taxa_contratada_pct": c.taxa_contratada,
                "nota": f"valor_taxa Orbe {c.transacao.valor_taxa} − comissão contratada {c.comissao}",
            })

    res.linhas.sort(key=lambda l: (-l["diferenca_brl"], l["cnpj"], l["ref_origem"]))
    return res


@dataclass
class ResultadoDivergenciasRemessa:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    total_pela_coluna_spread_pct: dict[str, Decimal] = field(default_factory=dict)  # cnpj → mesma conta com o "Spread %" do relatório


def divergencias_remessa(cls: ClassificacaoRemessa, cadastro: Cadastro, regras: dict) -> ResultadoDivergenciasRemessa:
    """Divergências de spread na Ponte (elegíveis acima da tolerância + todos os spreads negativos).

    Regras: remessa.formula_divergencia e remessa.divergencia_spread (valor cheio),
    remessa.spread_padrao (branco/"padrão" = 1,5% sobre a PTAX), ponte.tolerancia_spread_pct,
    ponte.formula_spread_pct, remessa.arredondamento_divergencia, remessa.motivo_spread_negativo.
    """
    valor_da_regra(regras, "remessa.formula_divergencia")
    valor_da_regra(regras, "remessa.divergencia_spread")
    if valor_da_regra(regras, "remessa.arredondamento_divergencia") != "ROUND_HALF_EVEN_POR_OPERACAO":
        raise ValueError("remessa.arredondamento_divergencia não suportado")
    padrao = valor_da_regra(regras, "remessa.spread_padrao")
    if str(padrao.get("base")).upper() != "PTAX":
        raise ValueError("remessa.spread_padrao com base diferente de PTAX não suportado")
    spread_padrao = Decimal(str(padrao["spread_pct"]))
    tolerancia = Decimal(str(valor_da_regra(regras, "ponte.tolerancia_spread_pct")))
    motivo_negativo = valor_da_regra(regras, "remessa.motivo_spread_negativo")
    valor_da_regra(regras, "remessa.divergencia_spread_negativo")
    fracao = Decimal(str(valor_da_regra(regras, "ponte.participacao_tarvo")))
    coluna = valor_da_regra(regras, "taxas.coluna_por_produto")["REMESSA"]

    res = ResultadoDivergenciasRemessa()
    candidatas = [(op, cnpj, False) for op, cnpj in cls.elegiveis] + [(op, cnpj, True) for op, cnpj in cls.negativos]
    for op, cnpj, negativo in sorted(candidatas, key=lambda x: x[0].linha_planilha):
        linha, motivo_linha = linha_vigente(cadastro, cnpj, op.data_contratacao)
        bruto = linha.taxas.get(coluna) if linha is not None else None
        if linha is None:
            res.pendencias.append(_pend(op, "REMESSA_SPREAD_INDEFINIDO", f"spread contratado: {motivo_linha}"))
            continue
        if isinstance(bruto, Decimal):
            contratado, fonte = bruto, f"planilha R{linha.linha_planilha} col. {coluna!r}"
        elif bruto is None or bruto.strip().lower() == "padrão":
            contratado = spread_padrao
            fonte = f"planilha R{linha.linha_planilha} col. {coluna!r} {'vazia' if bruto is None else repr(bruto)} → padrão (remessa.spread_padrao)"
        else:
            res.pendencias.append(_pend(op, "REMESSA_SPREAD_INDEFINIDO", f"spread contratado em texto: {bruto!r} (R{linha.linha_planilha})"))
            continue

        aplicado = (op.taxa_cliente - op.ptax_ref) / op.ptax_ref  # ponte.formula_spread_pct (tolerância e exibição)
        if not negativo and abs(aplicado - contratado) <= tolerancia:
            continue
        # D22: Spread R$ do relatório (mesma base da comissão) − contratado × PTAX × Valor ME; D20: meio → par
        dif = (op.spread_brl - contratado * op.ptax_ref * op.valor_me).quantize(CENTAVO, rounding=ROUND_HALF_EVEN)
        pela_coluna = ((op.spread_pct - contratado) * op.ptax_ref * op.valor_me).quantize(CENTAVO, rounding=ROUND_HALF_EVEN)
        res.total_pela_coluna_spread_pct[cnpj] = res.total_pela_coluna_spread_pct.get(cnpj, Decimal("0")) + pela_coluna

        aplicado_6 = aplicado.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        motivo = f"Ponte aplicou {fmt_pct(aplicado_6)}% sobre a PTAX; contratado {fmt_pct(contratado)}% ({fonte})"
        if negativo:
            motivo = f"spread negativo: {motivo_negativo}; {motivo}; fora da comissão e da nota"
        idd = id_divergencia(op.ref_origem)
        res.linhas.append({
            "id_saida": idd,
            "cnpj": cnpj,
            "linha_negocio": "REMESSA",
            "ref_origem": op.ref_origem,
            "taxa_contratada_pct": contratado,
            "taxa_aplicada_pct": aplicado_6,
            "diferenca_brl": dif,
            "lojista": cadastro.lojistas[cnpj].nome,
            "data": op.data_contratacao,
            "tipo_lancamento": "REMESSA",
            "moeda": op.moeda,
            "valor_me": op.valor_me,
            "ptax_ref": str(op.ptax_ref),
            "taxa_cliente": str(op.taxa_cliente),
            "spread_brl": op.spread_brl,
            "impacto_repasse_tarvo": participacao(op.spread_brl, fracao) if negativo else None,  # D21
            "direcao": "COBROU_A_MAIS" if dif > 0 else "COBROU_A_MENOS",
            "motivo": motivo,
            "decisao": "Helena",
        })
        res.rastro.append({
            "id_saida": idd,
            "arquivo_origem": op.arquivo_origem,
            "ref_origem": op.ref_origem,
            "valor": dif,
            "linha_arquivo": op.linha_planilha,
            "tipo_lancamento": "REMESSA",
            "spread_brl": op.spread_brl,
            "nota": f"({fmt_pct(aplicado_6)}% − {fmt_pct(contratado)}%) × PTAX {op.ptax_ref} × {op.valor_me} {op.moeda}",
        })
    res.linhas.sort(key=lambda l: (-l["diferenca_brl"], l["cnpj"], l["ref_origem"]))
    return res


def _pend(op: OperacaoPonte, tipo: str, motivo: str) -> Pendencia:
    return Pendencia(f"PEN-{tipo}-{op.ref_origem}", tipo, op.ref_origem, None, motivo, "financeiro (Helena)")
