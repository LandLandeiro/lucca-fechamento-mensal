"""Comissão por lojista e linha de negócio (CHECKOUT e REMESSA).

Responsabilidade: compor a comissão segundo as regras confirmadas e gerar o rastro por
linha de origem. `id_saida`: `COM-<cnpj>-<CHECKOUT|REMESSA>`.

CHECKOUT (regras usadas, todas de `regras.yaml`):
- checkout.base_comissao (CONFIRMADO 20:05): bruto × taxa contratada, por transação;
- checkout.arredondamento_comissao_contratada (CONFIRMADO 21:13, Q-H): arredondamento comum
  no centavo (meio para longe do zero) por transação, depois somar (substitui o truncamento da D09);
- checkout.composicao_comissao (CONFIRMADO 20:47): VENDA, ESTORNO, ANTECIPACAO entram;
  REVERSAO ANTECIPACAO só anula a antecipação referenciada (id_referencia);
- checkout.estorno (CONFIRMADO 20:06): estorno pela taxa contratada vigente na data da
  venda original;
- cadastro.lojista_sem_contrato_vigente (CONFIRMADO 20:24): não fatura → pendência, até a aba vigente trazer
  contrato para o EC (o comercial confirmou, Q-Q/Q-S): aí vale a planilha, com aviso (D67);
- cadastro.condicoes_especiais (CONFIRMADO 20:49, Casa; lista, D61): via cadastro.taxa_contratada.

Toda linha da Orbe termina em exatamente um lugar: no rastro de uma comissão (COM-…) ou
no rastro de uma pendência (PEN-…). O validador confere isso.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from tarvo.cadastro import Cadastro, coluna_do_produto, taxa_contratada
from tarvo.formatos import centavos, modo_arredondamento
from tarvo.modelo import Aviso, ItemRastro, Pendencia, TransacaoOrbe
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
    condicao: dict | None = None  # condição especial (regras.yaml) que deu a taxa contratada, se houver
    coluna: str = ""  # coluna da planilha da transação (taxas.coluna_por_produto)
    data_ref: date | None = None  # data em que a taxa contratada foi procurada (a da venda original, no estorno)


@dataclass
class ResultadoCheckout:
    comissoes: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)  # ItemRastro + colunas extras
    pendencias: list[Pendencia] = field(default_factory=list)
    por_transacao: dict[str, ComissaoTransacao] = field(default_factory=dict)
    em_pendencia: dict[str, str] = field(default_factory=dict)  # id_transacao → id_saida da pendência
    # CNPJ → pendências de transações dele (taxa indefinida etc.): a nota do mês não sai com valor parcial (D57)
    pendencias_por_cnpj: dict[str, list[str]] = field(default_factory=dict)
    avisos: list = field(default_factory=list)


def id_comissao(cnpj: str, linha: str = LINHA) -> str:
    return f"COM-{cnpj}-{linha}"


@dataclass
class JuncaoOrbe:
    transacoes: list[TransacaoOrbe]
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)


def juntar_relatorios_orbe(leituras: list) -> JuncaoOrbe:
    """D75 (`orbe.ajustes_tardios`): o relatório da Orbe do mês e os ajustes tardios (06, opcional) formam um só conjunto de
    transações; cada linha leva o seu arquivo no rastro. `id_transacao` repetido entre arquivos (uma correção?)
    não conta em lugar nenhum: as linhas vão para uma pendência ID_REPETIDO_ORBE para a Helena (ASSUMO,
    `orbe.id_repetido_entre_arquivos`; pergunta do Lucca 13:19 sem resposta)."""
    por_id: dict[str, list[TransacaoOrbe]] = {}
    for leitura in leituras:
        for t in leitura.transacoes:
            por_id.setdefault(t.ref_origem, []).append(t)
    res = JuncaoOrbe([t for ts in por_id.values() if len({x.arquivo_origem for x in ts}) == 1 for t in ts])
    for ref, ts in sorted(por_id.items()):
        if len({x.arquivo_origem for x in ts}) == 1:
            continue
        pid = f"PEN-ID_REPETIDO_ORBE-{ref}"
        onde = ", ".join(f"{x.arquivo_origem} linha {x.linha_arquivo}" for x in ts)
        res.pendencias.append(Pendencia(
            pid, "ID_REPETIDO_ORBE", ref, sum((x.valor_taxa for x in ts), Decimal("0")),
            f"id_transacao {ref} aparece em mais de um arquivo da Orbe ({onde}): pode ser correção de uma linha. "
            f"Nenhuma das linhas entra na comissão até a Helena dizer qual vale. valor_brl = taxa cobrada, informativo",
            "Helena",
        ))
        res.rastro.extend(_linha_rastro(pid, x, x.valor_taxa, None, "id repetido entre arquivos da Orbe") for x in ts)
    return res


@dataclass
class SeparacaoCompetencia:
    competencia: tuple[int, int]
    dentro: list[TransacaoOrbe]
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    do_mes_anterior: list[TransacaoOrbe] = field(default_factory=list)  # D91: ajuste tardio de mês já aprovado


class CompetenciaAmbigua(ValueError):
    """O relatório da Orbe não tem um mês predominante (empate ou vazio)."""


def separar_competencia(transacoes: list[TransacaoOrbe],
                        ajustes_de_mes_aprovado: frozenset[str] = frozenset()) -> SeparacaoCompetencia:
    """D62: competência do checkout = o mês de `data_movimento` da maioria das linhas da Orbe. Linha de outro
    mês não aborta o fechamento: fica fora da comissão e vira pendência ORBE_FORA_COMPETENCIA (uma por linha,
    valor = taxa cobrada, informativo). Sem linhas ou com empate entre meses → CompetenciaAmbigua.

    D91 (Q-AJ 1): `ajustes_de_mes_aprovado` = ids do arquivo de ajustes tardios quando o fechamento do mês anterior
    já foi aprovado; a linha desses ids com movimento no mês anterior entra nesta competência."""
    contagem: dict[tuple[int, int], int] = {}
    for t in transacoes:
        mes = (t.data_movimento.year, t.data_movimento.month)
        contagem[mes] = contagem.get(mes, 0) + 1
    if not contagem:
        raise CompetenciaAmbigua("relatório da Orbe sem linhas: não há competência")
    ordem = sorted(contagem.items(), key=lambda kv: -kv[1])
    if len(ordem) > 1 and ordem[0][1] == ordem[1][1]:
        raise CompetenciaAmbigua(f"relatório da Orbe com meses empatados {sorted(contagem)}: competência do checkout ambígua")
    competencia = ordem[0][0]
    anterior = (competencia[0] - 1, 12) if competencia[1] == 1 else (competencia[0], competencia[1] - 1)

    def entra(t: TransacaoOrbe) -> bool:
        mes = (t.data_movimento.year, t.data_movimento.month)
        return mes == competencia or (mes == anterior and t.ref_origem in ajustes_de_mes_aprovado)

    res = SeparacaoCompetencia(competencia, [t for t in transacoes if entra(t)])
    res.do_mes_anterior = [t for t in res.dentro if (t.data_movimento.year, t.data_movimento.month) == anterior]
    for t in transacoes:
        if entra(t):
            continue
        pid = f"PEN-ORBE_FORA_COMPETENCIA-{t.ref_origem}"
        res.pendencias.append(Pendencia(
            pid, "ORBE_FORA_COMPETENCIA", t.ref_origem, t.valor_taxa,
            f"linha {t.linha_arquivo} da Orbe ({t.tipo_lancamento}, {t.nome_estabelecimento}) com data_movimento "
            f"{t.data_movimento.isoformat()}, fora da competência {competencia[1]:02d}/{competencia[0]}: fora da comissão "
            f"do mês. valor_brl = taxa cobrada pela Orbe, informativo", "analista (conferir com a Orbe)",
        ))
        res.rastro.append(_linha_rastro(pid, t, t.valor_taxa, None, "linha fora da competência"))
    return res


def comissao_checkout(transacoes: list[TransacaoOrbe], cadastro: Cadastro, regras: dict) -> ResultadoCheckout:
    """Comissão CHECKOUT por lojista, com rastro e pendências."""
    valor_da_regra(regras, "checkout.base_comissao")
    valor_da_regra(regras, "checkout.estorno")
    modo = modo_arredondamento(valor_da_regra(regras, "checkout.arredondamento_comissao_contratada"))
    tipos = set(valor_da_regra(regras, "checkout.composicao_comissao"))
    sem_contrato = {str(k): v for k, v in valor_da_regra(regras, "cadastro.lojista_sem_contrato_vigente").items()
                    if str(k) not in cadastro.por_ec}  # D67: com contrato na aba vigente, vale a planilha
    mapa_colunas = valor_da_regra(regras, "taxas.coluna_por_produto")
    identificacao = {str(k): v for k, v in (valor_da_regra(regras, "cadastro.identificacao_sem_contrato")
                                           if "cadastro.identificacao_sem_contrato" in regras else {}).items()}

    res = ResultadoCheckout()
    for ec in sorted(str(k) for k in valor_da_regra(regras, "cadastro.lojista_sem_contrato_vigente")):
        if ec in cadastro.por_ec:
            res.avisos.append(Aviso("regras.yaml", "cadastro.lojista_sem_contrato_vigente",
                                    f"EC {ec} tem contrato na aba vigente ({cadastro.lojistas[cadastro.por_ec[ec]].nome}): "
                                    f"vale a planilha; tire o EC da regra (D67)"))
    grupos: dict[str, dict] = {}  # pendências agrupadas por lojista/EC

    def pendente_grupo(t: TransacaoOrbe, tipo: str, ref: str, motivo: str, quem: str) -> None:
        pid = f"PEN-{tipo}-{ref}"
        g = grupos.setdefault(pid, {"tipo": tipo, "ref": ref, "motivo": motivo, "quem": quem, "itens": []})
        g["itens"].append(t)
        res.em_pendencia[t.ref_origem] = pid

    def pendente_transacao(t: TransacaoOrbe, tipo: str, motivo: str) -> None:
        pendente_grupo(t, tipo, t.ref_origem, motivo, QUEM_DECIDE_FINANCEIRO)
        cnpj = cadastro.por_ec.get(t.cod_estabelecimento)
        if cnpj and t.cod_estabelecimento not in sem_contrato:
            lista = res.pendencias_por_cnpj.setdefault(cnpj, [])
            if f"PEN-{tipo}-{t.ref_origem}" not in lista:
                lista.append(f"PEN-{tipo}-{t.ref_origem}")

    def cnpj_da(t: TransacaoOrbe) -> str | None:
        ec = t.cod_estabelecimento
        if ec in sem_contrato:
            ident = identificacao.get(ec)  # D82: identidade da aba antiga (a taxa de lá não vale, Q-AC 1)
            quem_e = (f"{ident['nome']}, CNPJ {ident['cnpj']} (identificação: {ident['origem']}; só a identidade, a taxa "
                      f"daquela aba não vale)" if ident else t.nome_estabelecimento)
            pendente_grupo(t, "SEM_CONTRATO_VIGENTE", f"EC{ec}",
                           f"EC {ec}, {quem_e}: sem contrato na aba vigente; 'Não fatura a Atlas até o comercial confirmar' "
                           f"(Helena 20:24). Fora de comissoes_por_lojista.csv e de notas, com as transações aqui (Q-AC 2). "
                           f"valor_brl = taxa cobrada pela Orbe, informativo",
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
        com = centavos(t.valor_bruto * enc.taxa, modo)
        nota = "; ".join(x for x in (nota, enc.fonte) if x)
        res.por_transacao[t.ref_origem] = ComissaoTransacao(t, cnpj, enc.taxa, com, nota, enc.fonte, enc.condicao,
                                                            coluna, data_ref)

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
        res.por_transacao[t.ref_origem] = replace(base, transacao=t, comissao=-base.comissao, nota=f"anula a antecipação {ref}")

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
            res.por_transacao[venda.transacao.ref_origem] = replace(venda, nota="; ".join(x for x in (venda.nota, marca) if x))


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
    """Ordem determinística da saída: linha de negócio, comissão decrescente, CNPJ."""
    return (linha["linha_negocio"], -linha["comissao_brl"], linha["cnpj"])


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

# Comissão REMESSA: tarvo.calculos.remessa
