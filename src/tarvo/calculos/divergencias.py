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
  líquida com a antecipação que ela anula, do mesmo jeito;
- divergencias.pendencia_por_lojista (ASSUMO, D53): uma pendência DIVERGENCIA_CHECKOUT por lojista,
  com o total e o rastro das transações (mesmo padrão da contestação com a Ponte). Se a taxa
  contratada veio de uma condição especial (ex.: Casa), quem decide é o da condição e o texto cita a
  fonte dela; senão, a Helena (20:05).

Transações em pendência (ex.: Atlas, sem contrato) não entram: não há taxa contratada.

Identidade do checkout: Σ valor_taxa (Orbe) = Σ comissão + Σ divergência + resíduo, em que
o resíduo de cada linha é o efeito do truncamento da Orbe contra o arredondamento comum.

REMESSA (divergencias_remessa): ver a docstring da função.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tarvo.cadastro import Cadastro, condicao_especial, linha_vigente
from tarvo.calculos.comissoes import ComissaoTransacao, ResultadoCheckout
from tarvo.calculos.remessa import ClassificacaoRemessa, modo_participacao, participacao
from tarvo.formatos import centavos, fmt_dinheiro, fmt_pct, modo_arredondamento, nome_mes
from tarvo.modelo import OperacaoPonte, Pendencia
from tarvo.regras import valor_da_regra

LINHA = "CHECKOUT"
ZERO = Decimal("0")


@dataclass
class ResultadoDivergencias:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)  # DIVERGENCIA_CHECKOUT, uma por lojista (D53)
    rastro_pendencias: list[dict] = field(default_factory=list)
    itens_por_div: dict[str, list[ComissaoTransacao]] = field(default_factory=dict)  # DIV-… → transações do grupo
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
    valor_da_regra(regras, "divergencias.valor_a_devolver")  # D71
    modo = modo_arredondamento(valor_da_regra(regras, "checkout.arredondamento_comissao_contratada"))
    ligados = ("ESTORNO", "REVERSAO ANTECIPACAO") if valor_da_regra(
        regras, "divergencias.reversao_liquida_com_antecipacao") else ("ESTORNO",)

    res = ResultadoDivergencias()
    condicoes: dict[str, dict | None] = {}  # id DIV → condição especial que deu a taxa contratada
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
        if liquido == 0 and any(d != 0 for d in difs):
            res.grupos_zerados += 1  # D77: listadas mesmo assim, cada uma com o seu sinal; o líquido é 0
        # D77 (Q-AB 3): transação por transação; o estorno de uma venda com taxa errada entra com valor negativo
        for c, d in zip(itens, difs):
            if d == 0:
                continue
            t = c.transacao
            aplicada = t.taxa_aplicada_pct / 100
            outros = [x.transacao.ref_origem for x in itens if x is not c]
            if c.condicao is not None:  # condicao_nao_informada: a Orbe cobrou o contratado com ela, não se acusa a Orbe
                motivo = (f"Isenção comercial da Tarvo, não registrada na Orbe: a Orbe aplicou {fmt_pct(aplicada)}% "
                          f"(o contrato dela), o lojista tem {fmt_pct(c.taxa_contratada)}% contratado ({c.fonte_taxa}). "
                          f"A Orbe cobrou o contratado com ela (Q-AA 1). A devolução é custo da Tarvo (Q-AE 1)")
            else:
                motivo = f"Orbe aplicou {fmt_pct(aplicada)}%; contratada {fmt_pct(c.taxa_contratada)}% ({c.fonte_taxa})"
            estorno_de_acima = (t.tipo_lancamento in ("ESTORNO", "REVERSAO ANTECIPACAO") and c is not cabeca
                                and difs[0] > 0 and d < 0)
            if estorno_de_acima:  # D86: não é "a Orbe cobrou a menos" (Q-N 7), é o estorno de uma venda cobrada a mais
                motivo = (f"estorno de venda cobrada acima do contrato ({cabeca_id}): " + motivo)
            elif t.tipo_lancamento in ("ESTORNO", "REVERSAO ANTECIPACAO") and c is not cabeca:
                motivo += f"; {t.tipo_lancamento.lower()} de {cabeca_id}"
            elif t.tipo_lancamento == "ESTORNO":
                motivo += f"; estorno de venda de {t.data_venda_original.isoformat()} que não está no arquivo"
            if outros:
                motivo += (f"; com {', '.join(outros)} o líquido é 0: não entra em cobrança nem devolução (Q-N 3)"
                           if liquido == 0 else f"; líquida com {', '.join(outros)} (parcial)")
            ida = id_divergencia(t.ref_origem)
            condicoes[ida] = c.condicao
            res.linhas.append({
                "id_saida": ida,
                "cnpj": c.cnpj,
                "linha_negocio": LINHA,
                "ref_origem": t.ref_origem,
                "taxa_contratada_pct": c.taxa_contratada,
                "taxa_aplicada_pct": aplicada,
                "diferenca_brl": d,
                "lojista": cadastro.lojistas[c.cnpj].nome,
                "data": t.data_movimento,
                "tipo_lancamento": t.tipo_lancamento,
                "valor_bruto": t.valor_bruto,
                "comissao_contratada": c.comissao,
                "valor_taxa_orbe": t.valor_taxa,
                # D71: o que o lojista perdeu de fato (a Orbe liquida o líquido, Q-U 4): valor cobrado − comissão contratada
                "valor_a_devolver_brl": t.valor_taxa - c.comissao,
                "direcao": ("ESTORNO_DE_VENDA_ACIMA_DO_CONTRATO" if estorno_de_acima
                            else "COBROU_A_MAIS" if d > 0 else "COBROU_A_MENOS"),
                "liquida_com": ", ".join(outros),
                "natureza": _natureza_checkout(c, aplicada, cadastro),
                "motivo": motivo,
                # D85: a devolução da Casa (concessão comercial) decide Helena + comercial, não só a Helena
                "decisao": (c.condicao or {}).get("quem_decide_divergencia") or decisao,
            })
            res.itens_por_div[ida] = [c]
            res.rastro.append({
                "id_saida": ida,
                "arquivo_origem": t.arquivo_origem,
                "ref_origem": t.ref_origem,
                "valor": d,
                "linha_arquivo": t.linha_arquivo,
                "tipo_lancamento": t.tipo_lancamento,
                "valor_bruto": t.valor_bruto,
                "taxa_contratada_pct": c.taxa_contratada,
                "nota": f"round({t.valor_bruto} × ({fmt_pct(aplicada)}% − {fmt_pct(c.taxa_contratada)}%))",
            })

    res.linhas.sort(key=lambda l: (-l["diferenca_brl"], l["cnpj"], l["ref_origem"]))
    _pendencias_por_lojista(res, condicoes, regras)
    return res


NATUREZAS = ("contrato_orbe", "condicao_nao_informada", "spread_acima_contrato", "spread_abaixo_contrato", "spread_negativo")


def _natureza_checkout(c: ComissaoTransacao, aplicada: Decimal, cadastro: Cadastro) -> str:
    """D63, corrigida pela D76 (`divergencias.natureza`): `condicao_nao_informada` só quando a taxa contratada veio
    de uma condição especial do comercial, fora do contrato (Casa: "Quem abriu mão da receita fomos nós", Q-AA 1);
    toda outra divergência é `contrato_orbe`, com ou sem aviso à Orbe ("O que decide é o contrato, não o aviso")."""
    return "condicao_nao_informada" if c.condicao is not None else "contrato_orbe"


def _pendencias_por_lojista(res: ResultadoDivergencias, condicoes: dict[str, dict | None], regras: dict) -> None:
    """D53: o que a Helena decide vira pendência, uma por lojista, com valor e as transações (rastro)."""
    cfg = valor_da_regra(regras, "divergencias.pendencia_por_lojista")
    por_cnpj: dict[str, list[dict]] = {}
    for l in res.linhas:
        por_cnpj.setdefault(l["cnpj"], []).append(l)
    nat = valor_da_regra(regras, "divergencias.natureza")
    grupos: dict[tuple[str, str], list[dict]] = {}
    for cnpj, divs in por_cnpj.items():
        for d in divs:
            grupos.setdefault((cnpj, d["natureza"]), []).append(d)
    for (cnpj, natureza), divs in sorted(grupos.items()):
        total = sum((d["valor_a_devolver_brl"] for d in divs), ZERO)  # D71: valor a devolver, não a diferença da Q-H c
        cond = next((condicoes[d["id_saida"]] for d in divs if condicoes.get(d["id_saida"])), None)
        nome, n = divs[0]["lojista"], len(divs)
        datas = sorted(d["data"] for d in divs)
        sentido = "a mais" if total > 0 else "a menos"
        if natureza == "condicao_nao_informada":
            quem = cond.get("quem_decide_divergencia") or nat["condicao_nao_informada"]["quem_decide"]
            vig = cond["vigencia"]
            texto = (f"{nome}: o contrato tem condição especial ({cond.get('descricao', 'regras.yaml')}, {vig['inicio']} a "
                     f"{vig['fim']}) e a Orbe cobrou {fmt_dinheiro(total)} em {n} transações. "
                     f"{cond.get('citacao_fonte', 'regras.yaml')}: '{cond.get('citacao', '')}'. "
                     f"{nat['condicao_nao_informada']['citacao_fonte']}: '{nat['condicao_nao_informada']['citacao']}'. "
                     f"Devolver {fmt_dinheiro(abs(total))} ao lojista (a Orbe liquida o líquido: o lojista já recebeu a "
                     f"menos, {cfg['liquido_fonte']}); nada a recuperar da Orbe e sem rascunho para ela: custo da Tarvo")
        else:
            quem = cfg["quem_decide"]
            texto = (f"{nome}: a Orbe descontou {fmt_dinheiro(abs(total))} {sentido} que o contrato em {n} transações. "
                     f"Devolver {fmt_dinheiro(abs(total))} ao lojista (a Orbe liquida o líquido: o lojista já recebeu a "
                     f"menos, {cfg['liquido_fonte']}) e recuperar o mesmo valor da Orbe (rascunho em rascunhos/; o valor "
                     f"não soma duas vezes). {cfg['citacao_fonte']}: '{cfg['citacao']}'")
        texto += ". Detalhe por transação em divergencias_taxa.csv (DIV-<id_transacao>)"
        # D85 (Q-N 1 "Deixem separado"): a devolução por concessão comercial tem tipo próprio, fora das divergências
        tipo = "DEVOLUCAO_CONCESSAO_COMERCIAL" if natureza == "condicao_nao_informada" else "DIVERGENCIA_CHECKOUT"
        pid = f"PEN-{tipo}-{cnpj}"
        if len({k for (c, k) in grupos if c == cnpj}) > 1 and tipo == "DIVERGENCIA_CHECKOUT":
            pid += f"-{natureza.upper()}"
        texto = texto.replace(".'.", ".'")
        res.pendencias.append(Pendencia(pid, tipo, "|".join(d["ref_origem"] for d in divs), total,
                                        " ".join(texto.split()), quem))
        for d in divs:
            for c in res.itens_por_div[d["id_saida"]]:
                res.rastro_pendencias.append({
                    "id_saida": pid, "arquivo_origem": c.transacao.arquivo_origem, "ref_origem": c.transacao.ref_origem,
                    "valor": c.transacao.valor_taxa - c.comissao, "linha_arquivo": c.transacao.linha_arquivo,
                    "tipo_lancamento": c.transacao.tipo_lancamento, "valor_bruto": c.transacao.valor_bruto,
                    "taxa_contratada_pct": c.taxa_contratada,
                    "nota": f"a devolver: valor cobrado pela Orbe {c.transacao.valor_taxa} − comissão contratada {c.comissao}",
                })


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
    remessa.divergencia_spread_negativo (participacao_tarvo_no_spread, informativa: D38) e
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
        especial = condicao_especial(regras, cnpj, "REMESSA", op.data_contratacao)  # D61: antes da planilha
        linha, motivo_linha = linha_vigente(cadastro, cnpj, op.data_contratacao)
        bruto = linha.taxas.get(coluna) if linha is not None else None
        if especial is not None:
            if especial.taxa is None:
                res.pendencias.append(_pend(op, "REMESSA_SPREAD_INDEFINIDO", f"spread contratado: {especial.fonte}"))
                continue
            contratado, fonte = especial.taxa, especial.fonte
        elif linha is None:
            res.pendencias.append(_pend(op, "REMESSA_SPREAD_INDEFINIDO", f"spread contratado: {motivo_linha}"))
            continue
        elif isinstance(bruto, Decimal):
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
            "participacao_tarvo_no_spread": participacao(op.spread_brl, fracao, modo_part) if negativo else None,  # D38: informativa
            "direcao": "COBROU_A_MAIS" if dif > 0 else "COBROU_A_MENOS",
            # D63 (Q-O): no spread negativo o lojista não pagou a mais; o prejuízo é da Tarvo com a Ponte
            "natureza": "spread_negativo" if negativo else ("spread_acima_contrato" if dif > 0 else "spread_abaixo_contrato"),
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
        # Q-H (b)/(d): metade de cada operação, arredondada, depois soma (D45)
        partes = [(op, participacao(d, fracao, modo_part)) for op, d in itens]
        metade = sum((v for _, v in partes), ZERO)
        pid = f"PEN-EXCESSO_REMESSA-{cnpj}"
        res.pendencias_derivadas.append(Pendencia(
            pid, "EXCESSO_REMESSA", ", ".join(id_divergencia(o.ref_origem) for o, _ in itens[:3])
            + (f" e mais {len(itens) - 3}" if len(itens) > 3 else ""), metade,
            f"{cadastro.lojistas[cnpj].nome}: a Ponte cobrou {fmt_dinheiro(total_div)} a mais em {len(itens)} operações. "
            f"A nota de {nome_mes(itens[0][0].data_contratacao.month)} sai pelo realizado (Helena 21:45); "
            f"a nossa metade ({fmt_dinheiro(metade)}) sai no mês "
            f"em que a Ponte devolver a diferença ao lojista",
            "Helena",
        ))
        for op, v in partes:
            res.rastro_pendencias.append({
                "id_saida": pid, "arquivo_origem": op.arquivo_origem, "ref_origem": op.ref_origem, "valor": v,
                "linha_arquivo": op.linha_planilha, "tipo_lancamento": "REMESSA", "spread_brl": op.spread_brl,
                "nota": "nossa metade da divergência da operação",
            })
    return res


def _pend(op: OperacaoPonte, tipo: str, motivo: str) -> Pendencia:
    return Pendencia(f"PEN-{tipo}-{op.ref_origem}", tipo, op.ref_origem, None, motivo, "financeiro (Helena)")
