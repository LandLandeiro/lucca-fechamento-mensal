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
- D17: a REVERSAO ANTECIPACAO é líquida com a antecipação que ela anula, do mesmo jeito.

Transações em pendência (ex.: Atlas, sem contrato) não entram: não há taxa contratada
para comparar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.cadastro import Cadastro
from tarvo.calculos.comissoes import ComissaoTransacao, ResultadoCheckout
from tarvo.formatos import fmt_pct
from tarvo.modelo import ItemRastro, OperacaoPonte
from tarvo.regras import valor_da_regra

LINHA = "CHECKOUT"
LIGADOS_POR_REFERENCIA = ("ESTORNO", "REVERSAO ANTECIPACAO")


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

    grupos: dict[str, list[ComissaoTransacao]] = {}
    for c in sorted(checkout.por_transacao.values(), key=lambda x: x.transacao.linha_arquivo):
        t = c.transacao
        if t.tipo_lancamento in LIGADOS_POR_REFERENCIA and t.id_referencia in checkout.por_transacao:
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


def divergencias_remessa(
    operacoes: list[OperacaoPonte], cadastro: dict, taxas: list, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Divergências de spread na Ponte."""
    raise NotImplementedError
