"""Comissão por lojista e linha de negócio (CHECKOUT e REMESSA).

Responsabilidade: compor a comissão segundo as regras confirmadas e gerar o rastro por
linha de origem. `id_saida`: `COM-<cnpj>-<CHECKOUT|REMESSA>`.

CHECKOUT (regras usadas, todas de `regras.yaml`):
- checkout.base_comissao (CONFIRMADO 20:05): bruto × taxa contratada, por transação;
- checkout.arredondamento_comissao_contratada (ASSUMO, D09): truncar no centavo por
  transação, depois somar;
- checkout.composicao_comissao (CONFIRMADO 20:47): VENDA, ESTORNO, ANTECIPACAO entram;
  REVERSAO ANTECIPACAO só anula a antecipação referenciada (id_referencia);
- checkout.estorno (CONFIRMADO 20:06): estorno pela taxa contratada vigente na data da
  venda original;
- cadastro.lojista_sem_contrato_vigente (CONFIRMADO 20:24): não fatura → pendência;
- cadastro.condicao_especial_casa_do_estudante (CONFIRMADO 20:49): via cadastro.taxa_contratada.

Toda linha da Orbe termina em exatamente um lugar: no rastro de uma comissão (COM-…) ou
no rastro de uma pendência (PEN-…). O validador confere isso.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal

from tarvo.cadastro import Cadastro, coluna_do_produto, taxa_contratada
from tarvo.formatos import CENTAVO
from tarvo.modelo import ItemRastro, OperacaoPonte, Pendencia, TransacaoOrbe
from tarvo.regras import valor_da_regra

LINHA = "CHECKOUT"
QUEM_DECIDE_FINANCEIRO = "financeiro (Helena)"


@dataclass(frozen=True)
class ComissaoTransacao:
    transacao: TransacaoOrbe
    cnpj: str
    taxa_contratada: Decimal
    comissao: Decimal
    nota: str
    fonte_taxa: str = ""  # de onde veio a taxa contratada (linha da planilha ou regra)


@dataclass
class ResultadoCheckout:
    comissoes: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)  # ItemRastro + colunas extras
    pendencias: list[Pendencia] = field(default_factory=list)
    por_transacao: dict[str, ComissaoTransacao] = field(default_factory=dict)
    em_pendencia: dict[str, str] = field(default_factory=dict)  # id_transacao → id_saida da pendência


def id_comissao(cnpj: str, linha: str = LINHA) -> str:
    return f"COM-{cnpj}-{linha}"


def truncar(valor: Decimal) -> Decimal:
    """Trunca no centavo em direção a zero (D09: igual à Orbe)."""
    return valor.quantize(CENTAVO, rounding=ROUND_DOWN)


def comissao_checkout(transacoes: list[TransacaoOrbe], cadastro: Cadastro, regras: dict) -> ResultadoCheckout:
    """Comissão CHECKOUT por lojista, com rastro e pendências."""
    valor_da_regra(regras, "checkout.base_comissao")
    valor_da_regra(regras, "checkout.estorno")
    arred = valor_da_regra(regras, "checkout.arredondamento_comissao_contratada")
    if arred != "TRUNCAR_POR_TRANSACAO":
        raise ValueError(f"checkout.arredondamento_comissao_contratada = {arred!r} não suportado")
    tipos = set(valor_da_regra(regras, "checkout.composicao_comissao"))
    sem_contrato = {str(k): v for k, v in valor_da_regra(regras, "cadastro.lojista_sem_contrato_vigente").items()}
    mapa_colunas = valor_da_regra(regras, "taxas.coluna_por_produto")

    res = ResultadoCheckout()
    grupos: dict[str, dict] = {}  # pendências agrupadas por lojista/EC

    def pendente_grupo(t: TransacaoOrbe, tipo: str, ref: str, motivo: str, quem: str) -> None:
        pid = f"PEN-{tipo}-{ref}"
        g = grupos.setdefault(pid, {"tipo": tipo, "ref": ref, "motivo": motivo, "quem": quem, "itens": []})
        g["itens"].append(t)
        res.em_pendencia[t.ref_origem] = pid

    def pendente_transacao(t: TransacaoOrbe, tipo: str, motivo: str) -> None:
        pendente_grupo(t, tipo, t.ref_origem, motivo, QUEM_DECIDE_FINANCEIRO)

    def cnpj_da(t: TransacaoOrbe) -> str | None:
        ec = t.cod_estabelecimento
        if ec in sem_contrato:
            pendente_grupo(t, "SEM_CONTRATO_VIGENTE", f"EC{ec}",
                           f"EC {ec} sem contrato na aba vigente; 'Não fatura a Atlas até o comercial confirmar' "
                           f"(Helena 20:24). valor_brl = taxa cobrada pela Orbe, informativo",
                           "comercial")
            return None
        cnpj = cadastro.por_ec.get(ec)
        if cnpj is None:
            pendente_grupo(t, "EC_SEM_CADASTRO", f"EC{ec}",
                           f"EC {ec} ({t.nome_estabelecimento}) sem vínculo com CNPJ na planilha nem em "
                           f"cadastro.mapeamento_ec_confirmado. valor_brl = taxa cobrada pela Orbe, informativo",
                           QUEM_DECIDE_FINANCEIRO)
        return cnpj

    reversoes: list[TransacaoOrbe] = []
    for t in transacoes:
        if t.tipo_lancamento not in tipos:
            pendente_transacao(t, "TIPO_NAO_PREVISTO", f"tipo_lancamento {t.tipo_lancamento!r} fora de checkout.composicao_comissao")
            continue
        if t.tipo_lancamento == "REVERSAO ANTECIPACAO":
            reversoes.append(t)  # depende da antecipação referenciada: segunda passada
            continue
        cnpj = cnpj_da(t)
        if cnpj is None:
            continue
        if t.tipo_lancamento == "ESTORNO":
            if t.data_venda_original is None:
                pendente_transacao(t, "ESTORNO_SEM_DATA_ORIGINAL", "estorno sem data_venda_original: não há como achar a taxa vigente")
                continue
            data_ref = t.data_venda_original
            nota = f"estorno de {t.id_referencia} (venda de {data_ref.isoformat()})"
        else:
            data_ref = t.data_movimento
            nota = ""
        coluna = coluna_do_produto(t.tipo_lancamento, t.modalidade, t.qtd_parcelas, mapa_colunas)
        if coluna is None:
            pendente_transacao(t, "PRODUTO_SEM_COLUNA",
                               f"modalidade {t.modalidade!r} / {t.qtd_parcelas} parcelas sem coluna em taxas.coluna_por_produto")
            continue
        enc = taxa_contratada(cadastro, cnpj, coluna, data_ref, regras)
        if enc.taxa is None:
            pendente_transacao(t, "TAXA_CONTRATADA_INDEFINIDA", f"{coluna}: {enc.fonte}")
            continue
        com = truncar(t.valor_bruto * enc.taxa)
        nota = "; ".join(x for x in (nota, enc.fonte) if x)
        res.por_transacao[t.ref_origem] = ComissaoTransacao(t, cnpj, enc.taxa, com, nota, enc.fonte)

    por_id = {t.ref_origem: t for t in transacoes}
    for t in reversoes:
        ref = t.id_referencia
        original = por_id.get(ref) if ref else None
        if original is None or original.tipo_lancamento != "ANTECIPACAO":
            pendente_transacao(t, "REVERSAO_SEM_ANTECIPACAO", f"id_referencia {ref!r} não é uma ANTECIPACAO deste arquivo")
            continue
        if original.cod_estabelecimento != t.cod_estabelecimento:
            pendente_transacao(t, "REVERSAO_OUTRO_EC", f"reverte {ref} de outro EC ({original.cod_estabelecimento})")
            continue
        if ref in res.em_pendencia:  # a antecipação está em pendência: a reversão vai junto
            g = grupos[res.em_pendencia[ref]]
            g["itens"].append(t)
            res.em_pendencia[t.ref_origem] = res.em_pendencia[ref]
            continue
        base = res.por_transacao[ref]
        res.por_transacao[t.ref_origem] = ComissaoTransacao(
            t, base.cnpj, base.taxa_contratada, -base.comissao, f"anula a antecipação {ref}", base.fonte_taxa
        )

    _marcar_estornadas(res)
    _agregar(res, cadastro)
    for pid, g in grupos.items():
        valor = sum((x.valor_taxa for x in g["itens"]), Decimal("0"))
        refs = ", ".join(x.ref_origem for x in g["itens"]) if len(g["itens"]) <= 3 else f"{len(g['itens'])} transações"
        res.pendencias.append(Pendencia(pid, g["tipo"], g["ref"], valor, f"{g['motivo']} ({refs})", g["quem"]))
        for x in g["itens"]:
            res.rastro.append(_linha_rastro(pid, x, x.valor_taxa, None, "taxa cobrada pela Orbe (valor_taxa)"))
    return res


def _marcar_estornadas(res: ResultadoCheckout) -> None:
    estornos = [c for c in res.por_transacao.values() if c.transacao.tipo_lancamento == "ESTORNO"]
    for e in estornos:
        venda = res.por_transacao.get(e.transacao.id_referencia or "")
        if venda is not None:
            marca = f"estornada em {e.transacao.data_movimento.isoformat()} por {e.transacao.ref_origem}"
            res.por_transacao[venda.transacao.ref_origem] = ComissaoTransacao(
                venda.transacao, venda.cnpj, venda.taxa_contratada, venda.comissao,
                "; ".join(x for x in (venda.nota, marca) if x), venda.fonte_taxa,
            )


def _agregar(res: ResultadoCheckout, cadastro: Cadastro) -> None:
    totais: dict[str, Decimal] = {}
    qtd: dict[str, int] = {}
    for c in res.por_transacao.values():
        totais[c.cnpj] = totais.get(c.cnpj, Decimal("0")) + c.comissao
        qtd[c.cnpj] = qtd.get(c.cnpj, 0) + 1
        res.rastro.append(_linha_rastro(id_comissao(c.cnpj), c.transacao, c.comissao, c.taxa_contratada, c.nota))
    for cnpj in sorted(totais):
        res.comissoes.append({
            "id_saida": id_comissao(cnpj),
            "cnpj": cnpj,
            "lojista": cadastro.lojistas[cnpj].nome,
            "linha_negocio": LINHA,
            "comissao_brl": totais[cnpj],
            "qtd_transacoes": qtd[cnpj],
        })
    res.comissoes.sort(key=ordem_comissao)


def ordem_comissao(linha: dict) -> tuple:
    """Ordem determinística da saída: comissão decrescente, depois CNPJ."""
    return (-linha["comissao_brl"], linha["cnpj"])


def _linha_rastro(id_saida: str, t: TransacaoOrbe, valor: Decimal, taxa: Decimal | None, nota: str) -> dict:
    item = ItemRastro(id_saida, t.arquivo_origem, t.ref_origem, valor)
    return {
        "id_saida": item.id_saida,
        "arquivo_origem": item.arquivo_origem,
        "ref_origem": item.ref_origem,
        "valor": item.valor,
        "linha_arquivo": t.linha_arquivo,
        "tipo_lancamento": t.tipo_lancamento,
        "valor_bruto": t.valor_bruto,
        "taxa_contratada_pct": taxa,
        "nota": nota,
    }


def comissao_remessa(
    operacoes: list[OperacaoPonte], cadastro: dict, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Comissão REMESSA por lojista, com rastro."""
    raise NotImplementedError
