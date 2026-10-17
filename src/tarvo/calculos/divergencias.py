"""Divergências entre taxa contratada e taxa aplicada, transação por transação.

Responsabilidade: listar onde a taxa aplicada difere da contratada, com o valor da
diferença em R$, e só a diferença real. `id_saida`: `DIV-<id_transacao>` / `DIV-<Nº Operação>`.

CHECKOUT (regras usadas, todas de `regras.yaml`):
- divergencias.criterio_checkout (CONFIRMADO 21:13, Q-H c): divergência só quando a taxa
  aplicada ≠ contratada; valor = round(valor_bruto × (aplicada − contratada)) por linha.
  O centavo de truncamento da Orbe não é divergência: vira resíduo (ver `residuo`);
- checkout.arredondamento_comissao_contratada (CONFIRMADO 21:13): o mesmo arredondamento;
- divergencias.tratamento (CONFIRMADO 20:05): listada com transação e valor; nunca devolução
  automática; decisão da Helena;
- divergencias.estorno_de_venda_divergente (ASSUMO, D10): a divergência de uma venda é
  líquida com os estornos dela (`id_referencia`) no mesmo arquivo; só lista se o líquido
  ≠ 0. Estorno de venda que não está no arquivo (mês anterior) é avaliado sozinho;
- divergencias.reversao_liquida_com_antecipacao (ASSUMO, D17): a REVERSAO ANTECIPACAO é
  líquida com a antecipação que ela anula, do mesmo jeito.

Transações em pendência (ex.: Atlas, sem contrato) não entram: não há taxa contratada.

Identidade do checkout: Σ valor_taxa (Orbe) = Σ comissão + Σ divergência + resíduo, em que
o resíduo de cada linha é o efeito do truncamento da Orbe contra o arredondamento comum.

REMESSA (divergencias_remessa): ver a docstring da função.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.cadastro import Cadastro, linha_vigente
from tarvo.calculos.comissoes import ComissaoTransacao, ResultadoCheckout
from tarvo.calculos.remessa import ClassificacaoRemessa, modo_participacao, participacao
from tarvo.formatos import centavos, fmt_dinheiro, fmt_pct, modo_arredondamento
from tarvo.modelo import ItemRastro, OperacaoPonte, Pendencia
from tarvo.regras import valor_da_regra

LINHA = "CHECKOUT"
ZERO = Decimal("0")


@dataclass
class ResultadoDivergencias:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    grupos_zerados: int = 0  # vendas divergentes cujo estorno zerou a diferença (não listadas)
    residuo: Decimal = ZERO  # Σ (valor_taxa − comissão − divergência da linha): truncamento da Orbe
    linhas_com_residuo: int = 0


def id_divergencia(ref: str) -> str:
    return f"DIV-{ref}"


def diferenca(c: ComissaoTransacao, modo: str) -> Decimal:
    """round(valor_bruto × (taxa aplicada − contratada)); 0 quando as taxas são iguais (Q-H c)."""
    aplicada = c.transacao.taxa_aplicada_pct / 100
    if aplicada == c.taxa_contratada:
        return ZERO
    return centavos(c.transacao.valor_bruto * (aplicada - c.taxa_contratada), modo)


def divergencias_checkout(checkout: ResultadoCheckout, cadastro: Cadastro, regras: dict) -> ResultadoDivergencias:
    """Divergências de MDR e antecipação na Orbe."""
    decisao = "Helena"
    valor_da_regra(regras, "divergencias.tratamento")
    valor_da_regra(regras, "divergencias.estorno_de_venda_divergente")
    valor_da_regra(regras, "divergencias.criterio_checkout")
    modo = modo_arredondamento(valor_da_regra(regras, "checkout.arredondamento_comissao_contratada"))
    ligados = ("ESTORNO", "REVERSAO ANTECIPACAO") if valor_da_regra(
        regras, "divergencias.reversao_liquida_com_antecipacao") else ("ESTORNO",)

    res = ResultadoDivergencias()
    grupos: dict[str, list[ComissaoTransacao]] = {}
    for c in sorted(checkout.por_transacao.values(), key=lambda x: x.transacao.linha_arquivo):
        t = c.transacao
        residuo = t.valor_taxa - c.comissao - diferenca(c, modo)
        res.residuo += residuo
        res.linhas_com_residuo += residuo != 0
        if t.tipo_lancamento in ligados and t.id_referencia in checkout.por_transacao:
            grupos.setdefault(t.id_referencia, []).append(c)
        else:
            grupos.setdefault(t.ref_origem, []).insert(0, c)  # a venda (cabeça) vai primeiro

    for cabeca_id, itens in grupos.items():
        cabeca = itens[0]
        if cabeca.transacao.ref_origem != cabeca_id:  # grupo sem a venda (não deveria acontecer)
            raise AssertionError(f"grupo de divergência {cabeca_id} sem a transação de origem")
        difs = [diferenca(c, modo) for c in itens]
        liquido = sum(difs, ZERO)
        if liquido == 0:
            if any(d != 0 for d in difs):
                res.grupos_zerados += 1
            continue

        t = cabeca.transacao
        aplicada = t.taxa_aplicada_pct / 100
        outros = [c.transacao.ref_origem for c in itens[1:]]
        motivo = f"Orbe aplicou {fmt_pct(aplicada)}%; contratada {fmt_pct(cabeca.taxa_contratada)}% ({cabeca.fonte_taxa})"
        if t.tipo_lancamento == "ESTORNO":
            motivo += f"; estorno de venda de {t.data_venda_original.isoformat()} que não está no arquivo"
        if outros:
            motivo += f"; líquida com {', '.join(outros)} (parcial)"
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
            "valor_bruto": sum((c.transacao.valor_bruto for c in itens), ZERO),
            "comissao_contratada": sum((c.comissao for c in itens), ZERO),
            "valor_taxa_orbe": sum((c.transacao.valor_taxa for c in itens), ZERO),
            "direcao": "COBROU_A_MAIS" if liquido > 0 else "COBROU_A_MENOS",
            "liquida_com": ", ".join(outros),
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
                "nota": f"round({c.transacao.valor_bruto} × ({fmt_pct(c.transacao.taxa_aplicada_pct / 100)}% − "
                        f"{fmt_pct(c.taxa_contratada)}%))",
            })

    res.linhas.sort(key=lambda l: (-l["diferenca_brl"], l["cnpj"], l["ref_origem"]))
    return res


@dataclass
class ResultadoDivergenciasRemessa:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    pendencias_derivadas: list[Pendencia] = field(default_factory=list)  # Q-J: nossa metade do excesso
    rastro_pendencias: list[dict] = field(default_factory=list)


def divergencias_remessa(cls: ClassificacaoRemessa, cadastro: Cadastro, regras: dict) -> ResultadoDivergenciasRemessa:
    """Divergências de spread na Ponte (elegíveis acima da tolerância + todos os spreads negativos).

    Regras: remessa.formula_divergencia (D28: round((Spread % do relatório − contratado) ×
    PTAX × Valor ME), valor cheio), remessa.divergencia_spread, remessa.spread_padrao
    (branco/"padrão" = 1,5% sobre a PTAX), ponte.tolerancia_spread_pct (comparada com a coluna
    "Spread %"), remessa.arredondamento_divergencia, remessa.motivo_spread_negativo,
    remessa.divergencia_spread_negativo (impacto_repasse_tarvo) e
    remessa.excesso_cobrado_na_remessa (Q-J: pendência com a nossa metade do excesso).
    """
    valor_da_regra(regras, "remessa.formula_divergencia")
    valor_da_regra(regras, "remessa.divergencia_spread")
    valor_da_regra(regras, "remessa.excesso_cobrado_na_remessa")
    modo = modo_arredondamento(valor_da_regra(regras, "remessa.arredondamento_divergencia"))
    modo_part = modo_participacao(regras)
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
    excesso: dict[str, list[tuple[OperacaoPonte, Decimal]]] = {}
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

        aplicado = op.spread_pct  # coluna "Spread %" do relatório (D28)
        if not negativo and abs(aplicado - contratado) <= tolerancia:
            continue
        dif = centavos((aplicado - contratado) * op.ptax_ref * op.valor_me, modo)

        motivo = f"Ponte aplicou {fmt_pct(aplicado)}% sobre a PTAX; contratado {fmt_pct(contratado)}% ({fonte})"
        if negativo:
            motivo = f"spread negativo: {motivo_negativo}; {motivo}; fora da comissão e da nota"
        elif dif > 0:
            excesso.setdefault(cnpj, []).append((op, dif))
        idd = id_divergencia(op.ref_origem)
        res.linhas.append({
            "id_saida": idd,
            "cnpj": cnpj,
            "linha_negocio": "REMESSA",
            "ref_origem": op.ref_origem,
            "taxa_contratada_pct": contratado,
            "taxa_aplicada_pct": aplicado,
            "diferenca_brl": dif,
            "lojista": cadastro.lojistas[cnpj].nome,
            "data": op.data_contratacao,
            "tipo_lancamento": "REMESSA",
            "moeda": op.moeda,
            "valor_me": op.valor_me,
            "ptax_ref": str(op.ptax_ref),
            "taxa_cliente": str(op.taxa_cliente),
            "spread_brl": op.spread_brl,
            "impacto_repasse_tarvo": participacao(op.spread_brl, fracao, modo_part) if negativo else None,  # D21
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
            "nota": f"round(({fmt_pct(aplicado)}% − {fmt_pct(contratado)}%) × PTAX {op.ptax_ref} × {op.valor_me} {op.moeda})",
        })
    res.linhas.sort(key=lambda l: (-l["diferenca_brl"], l["cnpj"], l["ref_origem"]))

    for cnpj, itens in sorted(excesso.items()):
        total_div = sum((d for _, d in itens), ZERO)
        metade = participacao(total_div, fracao, modo_part)
        pid = f"PEN-EXCESSO_REMESSA-{cnpj}"
        res.pendencias_derivadas.append(Pendencia(
            pid, "EXCESSO_REMESSA", ", ".join(id_divergencia(o.ref_origem) for o, _ in itens[:3])
            + (f" e mais {len(itens) - 3}" if len(itens) > 3 else ""), metade,
            f"{cadastro.lojistas[cnpj].nome}: a Ponte cobrou {fmt_dinheiro(total_div)} a mais em {len(itens)} operações. "
            f"A nota de setembro sai pelo realizado (Helena 21:45); a nossa metade ({fmt_dinheiro(metade)}) sai no mês "
            f"em que a Ponte devolver a diferença ao lojista",
            "Helena",
        ))
        partes = [(op, participacao(d, fracao, modo_part)) for op, d in itens]
        for op, v in partes:
            res.rastro_pendencias.append({
                "id_saida": pid, "arquivo_origem": op.arquivo_origem, "ref_origem": op.ref_origem, "valor": v,
                "linha_arquivo": op.linha_planilha, "tipo_lancamento": "REMESSA", "spread_brl": op.spread_brl,
                "nota": "nossa metade da divergência da operação",
            })
        residuo = metade - sum((v for _, v in partes), ZERO)
        if residuo:
            res.rastro_pendencias.append({
                "id_saida": pid, "arquivo_origem": itens[0][0].arquivo_origem, "ref_origem": "arredondamento",
                "valor": residuo, "linha_arquivo": 0, "tipo_lancamento": "REMESSA",
                "nota": "round(50% × total) − Σ round(50% × divergência por operação)",
            })
    return res


def _pend(op: OperacaoPonte, tipo: str, motivo: str) -> Pendencia:
    return Pendencia(f"PEN-{tipo}-{op.ref_origem}", tipo, op.ref_origem, None, motivo, "financeiro (Helena)")
