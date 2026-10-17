"""CLI: `python -m tarvo --dados data --saida saida`.

Implementado: comissão de CHECKOUT (E1+E2) e de REMESSA (E4) por lojista, e divergências de
taxa de checkout (E5a) e de spread de remessa (E4), com rastro e pendências, validados. Os arquivos de entrada são achados pelo prefixo
do nome (o mesmo formato chega todo mês); nada de setembro está fixo no código.
Saída inválida → código 1.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from tarvo.cadastro import adicionar_nomes_orbe, montar_cadastro, normalizar_nome
from tarvo.calculos.comissoes import comissao_checkout, ordem_comissao
from tarvo.calculos.contestacao import contestacao_ponte
from tarvo.calculos.divergencias import divergencias_checkout, divergencias_remessa
from tarvo.calculos.notas import conferencia_repasse, notas_a_emitir
from tarvo.calculos.remessa import classificar_remessa, comissao_remessa
from tarvo.classificacao.conferencias import conferir
from tarvo.classificacao import por_ia
from tarvo.classificacao.decisoes import aplicar_decisoes_humanas
from tarvo.classificacao.por_regra import classificar_por_regra
from tarvo.formatos import fmt_brl, fmt_dinheiro, modo_arredondamento, nome_mes
from tarvo.leitores.extrato_aurora import ler_extrato_aurora
from tarvo.leitores.extrato_meridiano import ler_extrato_meridiano
from tarvo.leitores.orbe import ErroLeitura, ler_orbe
from tarvo.leitores.plano_contas import contas_lancaveis, ler_plano_contas
from tarvo.leitores.ponte_email import ler_email, ler_operacoes
from tarvo.leitores.taxas import ler_taxas_vigentes
from tarvo.modelo import Aviso, Pendencia
from tarvo.pendencias import consolidar_pendencias, ler_pendencias_anteriores, pendencia_para_linha
from tarvo.regras import RegraInvalida, RegraPendente, carregar_regras, valor_da_regra
from tarvo.saida.escritor import escrever_saida
from tarvo.saida.validador import validar_saida

PADRAO_ORBE = "01_orbe_relatorio_comissoes_*.csv"
PADRAO_TAXAS = "02_tabela_taxas_contratadas*.xlsx"
PADRAO_PONTE = "03_email_ponte_cambio_*.eml"
PADRAO_PLANO = "04_plano_de_contas*.csv"
PADRAO_AURORA = "05a_extrato_banco_aurora_*.csv"
PADRAO_MERIDIANO = "05b_extrato_banco_meridiano_*.ofx"
ZERO = Decimal("0")
# regras.yaml da raiz do repositório (src/tarvo/__main__.py → raiz), não da pasta atual (D41)
RAIZ_REPO = Path(__file__).resolve().parents[2]
REGRAS_PADRAO = RAIZ_REPO / "regras.yaml"
CACHE_IA_PADRAO = RAIZ_REPO / "cache_ia"  # respostas da IA, commitadas (reexecução sem custo)
ENV_LOCAL = RAIZ_REPO / ".env.local"  # ANTHROPIC_API_KEY (fora do git)
_PADRAO = object()


class ErroEntrada(RuntimeError):
    pass


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tarvo",
        description="Fechamento mensal da Tarvo: lê o data pack como chega e gera os CSVs de saída.",
    )
    parser.add_argument("--dados", type=Path, default=Path("data"), help="pasta do data pack (padrão: data)")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="pasta dos CSVs gerados (padrão: saida)")
    parser.add_argument("--regras", type=Path, default=REGRAS_PADRAO,
                        help="arquivo de regras (padrão: regras.yaml da raiz do repositório)")
    parser.add_argument("--pendencias-anteriores", type=Path, default=None,
                        help="pendencias.csv do mês anterior: o que foi resolvido neste mês sai como resolvido, não como pendência nova")
    parser.add_argument("--sem-ia", action="store_true",
                        help="não usa IA nem o cache dela: lançamentos sem regra ficam para uma pessoa")
    return parser


def achar_unico(pasta: Path, padrao: str) -> Path:
    achados = sorted(pasta.glob(padrao))
    if len(achados) != 1:
        raise ErroEntrada(f"esperado 1 arquivo {padrao!r} em {pasta}, achei {len(achados)}: {[p.name for p in achados]}")
    return achados[0]


def executar(dados: Path, saida: Path, regras_path: Path, sem_ia: bool = False, cliente_ia=_PADRAO,
             cache_ia: Path = CACHE_IA_PADRAO, pendencias_anteriores: Path | None = None) -> dict:
    """Roda o fechamento e devolve o resumo. Levanta exceção em erro de entrada."""
    regras = carregar_regras(regras_path)
    arq_orbe = achar_unico(dados, PADRAO_ORBE)
    arq_taxas = achar_unico(dados, PADRAO_TAXAS)

    orbe = ler_orbe(arq_orbe)
    colunas = list(valor_da_regra(regras, "taxas.coluna_por_produto").values())
    taxas = ler_taxas_vigentes(
        arq_taxas, valor_da_regra(regras, "taxas.aba_vigente"), colunas, valor_da_regra(regras, "taxas.casas_decimais_taxa")
    )
    cadastro = montar_cadastro(taxas.linhas, regras, arq_taxas.name)
    checkout = comissao_checkout(orbe.transacoes, cadastro, regras)
    divergencias = divergencias_checkout(checkout, cadastro, regras)

    arq_ponte = achar_unico(dados, PADRAO_PONTE)
    mail = ler_email(arq_ponte)
    ponte = ler_operacoes(mail.anexo_xlsx, arq_ponte.name, mail.nome_anexo, valor_da_regra(regras, "ponte.linhas_que_nao_sao_dados"))
    avisos_extra = []
    meses_orbe = {(t.data_movimento.year, t.data_movimento.month) for t in orbe.transacoes}
    if ponte.competencia and meses_orbe and {ponte.competencia} != meses_orbe:
        avisos_extra.append(Aviso(arq_ponte.name, "-", f"competência da Ponte {ponte.competencia} ≠ meses da Orbe {sorted(meses_orbe)}"))
    declarado_qtd = ponte.totais_declarados.get("Total de operações:")
    if declarado_qtd is not None and declarado_qtd != ponte.total_linhas_dados:
        avisos_extra.append(Aviso(arq_ponte.name, "-", f"Total de operações declarado {declarado_qtd} ≠ {ponte.total_linhas_dados} linhas lidas"))
    cls_remessa = classificar_remessa(ponte.operacoes, ponte.competencia, cadastro, regras)
    remessa = comissao_remessa(cls_remessa, cadastro, regras)
    div_remessa = divergencias_remessa(cls_remessa, cadastro, regras)

    pend_leitura = [
        Pendencia(f"PEN-LEITURA_INVALIDA-{li.ref_origem}", "LEITURA_INVALIDA", f"{orbe.arquivo}:L{li.linha_arquivo}",
                  None, f"linha não lida: {li.motivo}", "analista (conferir o arquivo com a Orbe)")
        for li in orbe.linhas_invalidas
    ]
    pend_leitura += [
        Pendencia(f"PEN-LEITURA_INVALIDA-{li.ref_origem}-R{li.linha_arquivo}", "LEITURA_INVALIDA",
                  f"{ponte.arquivo}:R{li.linha_arquivo}", None, f"linha do anexo não lida: {li.motivo}",
                  "analista (conferir o relatório com a Ponte)")
        for li in ponte.linhas_invalidas
    ]
    if len(orbe.transacoes) + len(orbe.linhas_invalidas) != orbe.total_linhas_dados:
        raise AssertionError("linhas da Orbe perdidas entre leitura e cálculo")
    if len(ponte.operacoes) + len(ponte.linhas_invalidas) != ponte.total_linhas_dados:
        raise AssertionError("linhas do anexo da Ponte perdidas entre leitura e cálculo")
    if len(meses_orbe) != 1:
        raise ErroEntrada(f"relatório da Orbe com {len(meses_orbe)} meses ({sorted(meses_orbe)}): competência do checkout ambígua")

    comissoes = sorted(checkout.comissoes + remessa.comissoes, key=ordem_comissao)
    notas = notas_a_emitir(comissoes, checkout.rastro + remessa.rastro, regras, next(iter(meses_orbe)), ponte.competencia)
    nf_remessa = sum((n["valor_brl"] for n in notas.linhas if n["linha_negocio"] == "REMESSA"), ZERO)
    pend_repasse, rastro_repasse = conferencia_repasse(
        nf_remessa, [l for l in notas.rastro if l["id_saida"].endswith("-REMESSA")],
        ponte.totais_declarados.get("Spread total R$:"), cls_remessa, mail.corpo, regras,
    )
    contestacao = contestacao_ponte(cls_remessa, div_remessa.linhas, regras)
    # extratos (E6b): classificação por regra + conferências entre fontes
    competencia = next(iter(meses_orbe))
    plano = contas_lancaveis(ler_plano_contas(achar_unico(dados, PADRAO_PLANO)))
    aurora = ler_extrato_aurora(achar_unico(dados, PADRAO_AURORA))
    meridiano = ler_extrato_meridiano(achar_unico(dados, PADRAO_MERIDIANO))
    for ext in (aurora, meridiano):
        meses = {(l.data.year, l.data.month) for l in ext.lancamentos}
        if meses and meses != {competencia}:
            avisos_extra.append(Aviso(ext.arquivo, "-", f"lançamentos em {sorted(meses)}; competência {competencia}"))
        for li in ext.linhas_invalidas:
            pend_leitura.append(Pendencia(f"PEN-LEITURA_INVALIDA-{ext.banco}-{li.ref_origem}", "LEITURA_INVALIDA",
                                          f"{ext.arquivo}:L{li.linha_arquivo}", None, f"lançamento não lido: {li.motivo}",
                                          "analista (conferir o extrato com o banco)"))
    adicionar_nomes_orbe(cadastro, orbe.transacoes, regras)  # D35: ex.: Atlas
    classif = [classificar_por_regra(ext.lancamentos, ext.linhas_arquivo, plano, regras, cadastro, competencia)
               for ext in (aurora, meridiano)]
    # decisões humanas por linha antes da IA (D44); IA só nas sobras, o código verifica antes de aceitar (D42)
    avisos_extra += [Aviso("regras.yaml", "decisoes_humanas", a)
                     for a in aplicar_decisoes_humanas(classif, regras, competencia)]
    aporte = valor_da_regra(regras, "classificacao_extratos.meridiano.aporte_lojista")
    aportes_por_regra: dict[str, Decimal] = {}
    for c in classif:
        for l in c.linhas:
            cnpj = c.lojista_por_lancamento.get((l["banco"], l["ref_origem"]))
            if l["regra_aplicada"] == "meridiano.aporte_lojista" and cnpj:
                aportes_por_regra[cnpj] = aportes_por_regra.get(cnpj, ZERO) + l["valor"]
    linhas_ext = {(ext.banco, ref): n for ext in (aurora, meridiano) for ref, n in ext.linhas_arquivo.items()}
    if cliente_ia is _PADRAO:
        cliente_ia = None if sem_ia else por_ia.cliente_padrao(ENV_LOCAL, regras)
    prompt_ia = por_ia.carregar_prompt()
    ia = por_ia.classificar_sobras(
        [(lan, motivo, linhas_ext[(lan.banco, lan.ref_origem)]) for c in classif for lan, motivo in c.sem_regra],
        plano, cadastro, regras, competencia, orbe.transacoes, cls_remessa.elegiveis + cls_remessa.negativos,
        aportes_por_regra, cache_ia, cliente_ia, sem_ia=sem_ia, prompt=prompt_ia,
    )
    por_ia.aplicar(ia, classif, prompt_ia.versao)
    avisos_extra += [Aviso("IA", "-", a) for a in ia.avisos]
    regra_por_lanc = {}
    for c in classif:
        for l in c.linhas:
            chave = (l["banco"], l["ref_origem"])
            regra_por_lanc[chave] = l["regra_aplicada"]
            # aporte verificado pela IA entra na conferência de aportes como aporte (D42)
            if (l["metodo"] == "IA" and l["banco"] == "MERIDIANO" and l["conta_codigo"] == aporte["conta"]
                    and chave in c.lojista_por_lancamento):
                regra_por_lanc[chave] = "meridiano.aporte_lojista"
    linhas_por_lanc = {(ext.banco, ref): n for ext in (aurora, meridiano) for ref, n in ext.linhas_arquivo.items()}
    conf = conferir(
        regra_por_lanc, aurora.lancamentos + meridiano.lancamentos, linhas_por_lanc,
        {k: v for c in classif for k, v in c.lojista_por_lancamento.items()},
        cls_remessa.elegiveis + cls_remessa.negativos,
        {cnpj: lj.nome for cnpj, lj in cadastro.lojistas.items()},
        [lan for c in classif for lan, _ in c.sem_regra if normalizar_nome(lan.descricao).startswith("PIX RECEB ")],
        valor_da_regra(regras, "classificacao_extratos.conferencias")["resgate_acima_do_aplicado"],
        ler_pendencias_anteriores(pendencias_anteriores) if pendencias_anteriores else None,
    )
    lancamentos = [l for c in classif for l in c.linhas]

    pendencias = consolidar_pendencias(
        checkout.pendencias, divergencias.pendencias, remessa.pendencias, div_remessa.pendencias, pend_leitura,
        notas.pendencias, pend_repasse,
        div_remessa.pendencias_derivadas, contestacao.pendencias, *[c.pendencias for c in classif], conf.pendencias,
    )
    divs = divergencias.linhas + div_remessa.linhas
    rastro = sorted(
        checkout.rastro + divergencias.rastro + divergencias.rastro_pendencias + remessa.rastro + div_remessa.rastro
        + notas.rastro + notas.rastro_pendencias + rastro_repasse + div_remessa.rastro_pendencias + contestacao.rastro
        + [l for c in classif for l in c.rastro + c.rastro_pendencias] + conf.rastro_pendencias,
        key=lambda l: (l["id_saida"], l["linha_arquivo"], l["ref_origem"]),
    )
    escrever_saida(
        {
            "comissoes_por_lojista.csv": comissoes,
            "divergencias_taxa.csv": divs,
            "notas_a_emitir.csv": notas.linhas,
            "lancamentos_classificados.csv": lancamentos,
            "pendencias.csv": [pendencia_para_linha(p) for p in pendencias],
            "rastro.csv": rastro,
            "contestacao_ponte.csv": contestacao.linhas,  # extra (Q-L): o que a Helena manda para a Ponte
            "sugestoes_regra.csv": ia.sugestoes_regra,  # extra (E6b parte 2): propostas de regra para o mês seguinte
            **({"pendencias_resolvidas.csv": conf.resolvidas} if pendencias_anteriores else {}),  # extra (D50)
        },
        saida,
    )
    refs_esperadas = {
        orbe.arquivo: {(t.ref_origem, t.linha_arquivo) for t in orbe.transacoes},
        ponte.arquivo: {(o.ref_origem, o.linha_planilha) for o in ponte.operacoes},
    }
    refs_extratos = {ext.arquivo: {(l.ref_origem, ext.linhas_arquivo[l.ref_origem]) for l in ext.lancamentos}
                     for ext in (aurora, meridiano)}
    fontes_rastro = {**refs_esperadas, **refs_extratos}
    erros = validar_saida(
        saida,
        refs_esperadas=refs_esperadas,
        fonte_orbe={orbe.arquivo: {t.ref_origem: (t.valor_taxa, t.valor_bruto, t.taxa_aplicada_pct / 100) for t in orbe.transacoes}},
        modo_checkout=modo_arredondamento(valor_da_regra(regras, "checkout.arredondamento_comissao_contratada")),
        spread_ponte={ponte.arquivo: {(o.ref_origem, o.linha_planilha): o.spread_brl for o in ponte.operacoes}},
        spread_declarado=ponte.totais_declarados.get("Spread total R$:"),
        refs_extratos=refs_extratos,
        saldos_extratos={ext.banco: (ext.saldo_inicial, ext.saldo_final) for ext in (aurora, meridiano)},
        contas_lancaveis=set(plano),
        fontes_rastro=fontes_rastro,
    )
    excl: dict[str, list] = {}
    for op, motivo, _ in cls_remessa.excluidas:
        excl.setdefault(motivo, []).append(op)
    return {
        "arquivos": [arq_orbe.name, arq_taxas.name, f"{arq_ponte.name} (anexo {mail.nome_anexo})"],
        "avisos": orbe.avisos + taxas.avisos + cadastro.avisos + ponte.avisos + aurora.avisos + meridiano.avisos + avisos_extra,
        "extratos": {
            "leituras": (aurora, meridiano),
            "classif": classif,
            "conf": conf,
            "ia": ia,
            "pendencias": [p for c in classif for p in c.pendencias] + conf.pendencias,
        },
        "remessa": {
            "comissoes": remessa.comissoes,
            "total": sum((c["comissao_brl"] for c in remessa.comissoes), ZERO),
            "elegiveis": len(cls_remessa.elegiveis),
            "spread_elegivel": sum((o.spread_brl for o, _ in cls_remessa.elegiveis), ZERO),
            "spread_anexo": sum((o.spread_brl for o in ponte.operacoes), ZERO),
            "spread_declarado": ponte.totais_declarados.get("Spread total R$:"),
            "linhas": ponte.total_linhas_dados,
            "exclusoes": {m: (len(ops), sum((o.spread_brl for o in ops), ZERO), [o.ref_origem for o in ops]) for m, ops in excl.items()},
            "pendentes": len(cls_remessa.pendentes),
            "arredondamento": remessa.comparacao_arredondamento,
            "divergencias": div_remessa.linhas,
        },
        "comissoes": checkout.comissoes,
        "total_checkout": sum((c["comissao_brl"] for c in checkout.comissoes), ZERO),
        "lojistas": {c["cnpj"]: c["lojista"] for c in comissoes},
        "notas": notas.linhas,
        "pendencias_novas": divergencias.pendencias + notas.pendencias + pend_repasse + div_remessa.pendencias_derivadas + contestacao.pendencias,
        "residuo_checkout": (divergencias.residuo, divergencias.linhas_com_residuo),
        "pendencias": pendencias,
        "transacoes_em_pendencia": len(checkout.em_pendencia) + len(orbe.linhas_invalidas),
        "transacoes_lidas": orbe.total_linhas_dados,
        "divergencias": divergencias.linhas,
        "divergencias_zeradas": divergencias.grupos_zerados,
        "conservacao": (
            sum((c.transacao.valor_taxa for c in checkout.por_transacao.values()), ZERO),
            sum((c["comissao_brl"] for c in checkout.comissoes), ZERO),
            sum((d["diferenca_brl"] for d in divergencias.linhas), ZERO),
        ),
        "erros_validacao": erros,
        "competencia": competencia,
        "lancamentos": lancamentos,
        "arquivos_saida": sorted(p.name for p in saida.glob("*.csv")),
        "fontes_rastro": fontes_rastro,
    }


def _imprimir_divergencias(r: dict) -> None:
    divs = r["divergencias"]
    print(f"\nDivergências de taxa CHECKOUT: {len(divs)} listadas "
          f"(+ {r['divergencias_zeradas']} vendas divergentes zeradas pelo próprio estorno, não listadas)")
    por_lojista: dict[str, list] = {}
    for d in divs:
        acc = por_lojista.setdefault(d["cnpj"], [d["lojista"], 0, ZERO])
        acc[1] += 1
        acc[2] += d["diferenca_brl"]
    for cnpj, (nome, n, total) in sorted(por_lojista.items(), key=lambda kv: (-kv[1][2], kv[0])):
        print(f"  {cnpj}  {nome[:40]:<40} {fmt_dinheiro(total):>12}  ({n} divergências)")
    for direcao in ("COBROU_A_MAIS", "COBROU_A_MENOS"):
        sel = [d["diferenca_brl"] for d in divs if d["direcao"] == direcao]
        print(f"  {direcao:<16} {len(sel):>4} divergências  {fmt_dinheiro(sum(sel, ZERO)):>12}")
    fonte, com, div = r["conservacao"]
    residuo, n_res = r["residuo_checkout"]
    print(f"  conservação: Σ valor_taxa Orbe {fmt_dinheiro(fonte)} = Σ comissão {fmt_dinheiro(com)}"
          f" + Σ divergências {fmt_dinheiro(div)} + resíduo de truncamento {fmt_dinheiro(residuo)} ({n_res} linhas)")


def _imprimir_remessa(r: dict) -> None:
    m = r["remessa"]
    print(f"\nComissão REMESSA por lojista ({len(m['comissoes'])} lojistas, {m['elegiveis']} operações elegíveis):")
    for c in m["comissoes"]:
        print(f"  {c['cnpj']}  {c['lojista'][:40]:<40} {fmt_dinheiro(c['comissao_brl']):>12}  ({c['qtd_transacoes']} operações)")
    print(f"  {'TOTAL':<56} {fmt_dinheiro(m['total']):>12}")
    dif_arred = [a for a in m["arredondamento"] if a["diferenca"] != 0]
    total_uma_vez = sum((a["total_uma_vez"] for a in m["arredondamento"]), ZERO)
    print(f"  arredondamento: por operação (Q-H) {fmt_dinheiro(m['total'])} × 50% do total do lojista arredondado uma vez "
          f"{fmt_dinheiro(total_uma_vez)} → diferença {fmt_dinheiro(m['total'] - total_uma_vez)} em {len(dif_arred)} lojistas")
    for a in dif_arred:
        print(f"    {a['cnpj']} {r['lojistas'].get(a['cnpj'], '')[:30]:<30} {fmt_dinheiro(a['por_operacao'])} × "
              f"{fmt_dinheiro(a['total_uma_vez'])} ({fmt_dinheiro(a['diferenca'])})")
    print(f"  exclusões ({sum(n for n, _, _ in m['exclusoes'].values())} linhas):")
    for motivo, (n, spread, refs) in sorted(m["exclusoes"].items()):
        print(f"    {motivo:<18} {n:>3} linhas  Spread R$ {fmt_dinheiro(spread):>10}  {', '.join(refs)}")
    print(f"  conservação: Σ Spread R$ do anexo {fmt_dinheiro(m['spread_anexo'])} (declarado "
          f"{fmt_dinheiro(m['spread_declarado']) if m['spread_declarado'] is not None else '-'}) = elegíveis "
          f"{fmt_dinheiro(m['spread_elegivel'])} + exclusões "
          f"{fmt_dinheiro(sum((s for _, s, _ in m['exclusoes'].values()), ZERO))}; {m['linhas']} linhas, {m['pendentes']} pendentes")
    divs = m["divergencias"]
    print(f"\nDivergências de spread REMESSA: {len(divs)}, total {fmt_dinheiro(sum((d['diferenca_brl'] for d in divs), ZERO))}")
    grupos: dict[tuple, list] = {}
    for d in divs:
        chave = ("SPREAD_NEGATIVO" if d["spread_brl"] < 0 else "ACIMA_DO_CONTRATADO", d["cnpj"])
        grupos.setdefault(chave, []).append(d)
    for (tipo, cnpj), ds in sorted(grupos.items()):
        part = sum((d["participacao_tarvo_no_spread"] or ZERO for d in ds), ZERO)
        print(f"  {tipo:<20} {cnpj} {ds[0]['lojista'][:30]:<30} {len(ds):>3}  {fmt_dinheiro(sum((d['diferenca_brl'] for d in ds), ZERO)):>10}"
              + (f"  participação Tarvo no spread {fmt_dinheiro(part)} (informativa)" if tipo == "SPREAD_NEGATIVO" else ""))


def _imprimir_notas(r: dict) -> None:
    notas = r["notas"]
    print(f"\nNotas a emitir: {len(notas)}")
    for linha in ("CHECKOUT", "REMESSA"):
        sel = [n for n in notas if n["linha_negocio"] == linha]
        print(f"  {linha:<9} {len(sel):>3} notas  {fmt_dinheiro(sum((n['valor_brl'] for n in sel), ZERO)):>12}")
    for n in notas:
        if n["linha_negocio"] == "REMESSA":
            print(f"    {n['id_saida']}: {n['tomador']} — {n['discriminacao']}")
    for p in r["pendencias_novas"]:
        print(f"  pendência {p.id_saida} ({fmt_dinheiro(p.valor_brl)}), quem decide: {p.quem_decide}\n    {p.motivo}")


def _imprimir_extratos(r: dict) -> None:
    e = r["extratos"]
    print("\nLançamentos classificados (por regra):")
    for ext, c in zip(e["leituras"], e["classif"]):
        soma = sum((l["valor"] for l in c.linhas), ZERO)
        saldo = (f"saldo final − inicial {fmt_dinheiro(ext.saldo_final - ext.saldo_inicial)}"
                 if ext.saldo_inicial is not None and ext.saldo_final is not None
                 else f"sem saldo inicial no extrato (saldo final {fmt_dinheiro(ext.saldo_final)}; "
                      f"inicial implícito {fmt_dinheiro(ext.saldo_final - soma)})")
        print(f"  {ext.banco:<9} {len(c.linhas):>4} linhas: {len(c.linhas) - len(c.sem_regra)} por regra, "
              f"{len(c.sem_regra)} sem regra; Σ {fmt_dinheiro(soma)} ({saldo})")
        for regra, n in sorted(c.por_regra.items()):
            print(f"      {regra:<40} {n:>3}")
        for lan, motivo in c.sem_regra:
            print(f"    SEM REGRA {lan.ref_origem} {lan.data.isoformat()} {fmt_dinheiro(lan.valor):>12}  {lan.descricao!r}: {motivo}")
    conf = e["conf"]
    print("  transferências Aurora → Meridiano:")
    for saida, par in conf.transferencias:
        print(f"    {saida.ref_origem} {saida.data.isoformat()} {fmt_dinheiro(saida.valor):>12} → "
              + (f"{par.ref_origem} {par.data.isoformat()}" if par else "SEM PAR (pendência)"))
    print("  aplicação × resgate (FIFO):")
    for x in conf.resgates:
        orig = ", ".join(f"{a.ref_origem} {fmt_dinheiro(u)}" for a, u in x["consumidas"])
        print(f"    resgate {x['resgate'].ref_origem} {x['resgate'].data.isoformat()} {fmt_dinheiro(x['resgate'].valor):>11}"
              f" ← {orig}" + (f"  EXCESSO {fmt_dinheiro(x['excesso'])} (saldo aplicado anterior, D36)" if x["excesso"] else ""))
    diverg = [a for a in conf.aportes if a["sobra"] != 0]
    print(f"  aportes × operações da Ponte: {len(conf.aportes)} lojistas, {len(diverg)} com diferença")
    for a in diverg:
        print(f"    {a['cnpj']} {a['lojista'][:30]:<30} aportes {fmt_dinheiro(a['aportes'])} × operações "
              f"{fmt_dinheiro(a['operacoes'])} → sobra {fmt_dinheiro(a['sobra'])}"
              + ("  (NÃO CONFERIDO: nenhum aporte identificado; há PIX RECEB sem regra)" if a["nao_conferido"] else ""))
    ia = e["ia"]
    if ia.decisoes:
        do_cache = sum(1 for d in ia.decisoes if d.resposta and d.resposta.origem == "CACHE")
        print(f"  IA nas sobras ({len(ia.decisoes)} lançamentos: {ia.chamadas_api} chamadas à API, {do_cache} do cache, "
              f"{sum(1 for d in ia.decisoes if d.resposta is None)} sem resposta):")
        for d in ia.decisoes:
            s = d.resposta.sugestao if d.resposta else None
            print(f"    {d.lan.banco} {d.lan.ref_origem} {fmt_dinheiro(d.lan.valor):>12} {d.lan.descricao!r}")
            if s is None:
                print(f"      sem resposta: {d.erro} → HUMANO")
                continue
            print(f"      IA ({d.resposta.origem}): conta {s.conta_codigo}, lojista {s.lojista_cnpj or '-'}, "
                  f"confiança {s.confianca} — {s.justificativa}")
            for item, ok, det in d.checagens:
                print(f"      ({item}) {'OK  ' if ok else 'FALHA'} {det}")
            print(f"      → {'IA (aceita)' if d.aceita else 'HUMANO (pendência IA_REPROVADA)'}")
        print(f"    tokens (chamadas originais): entrada {ia.uso_total['input_tokens']}, saída {ia.uso_total['output_tokens']};"
              f" custo aproximado US$ {ia.custo_usd:.4f}")
        print(f"    sugestões de regra para o mês seguinte (PROPOSTA): {len(ia.sugestoes_regra)}")
    for x in conf.resolvidas:
        print(f"  RESOLVIDA {x['id_pendencia_anterior']}: {x['motivo']}")
    print(f"  pendências novas dos extratos: {len(e['pendencias'])}")
    for p in e["pendencias"]:
        print(f"    {p.id_saida} ({fmt_dinheiro(p.valor_brl) if p.valor_brl is not None else '-'}) → {p.quem_decide}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # console cp1252 (Windows): troca o que não sabe mostrar
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    args = criar_parser().parse_args(argv)
    if not args.dados.is_dir():
        print(f"erro: pasta de dados não encontrada: {args.dados}", file=sys.stderr)
        return 2
    if args.saida.exists() and not args.saida.is_dir():
        print(f"erro: --saida não é uma pasta: {args.saida}", file=sys.stderr)
        return 2
    try:
        r = executar(args.dados, args.saida, args.regras, sem_ia=args.sem_ia, pendencias_anteriores=args.pendencias_anteriores)
    except (ErroEntrada, ErroLeitura, RegraInvalida, RegraPendente, FileNotFoundError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2

    print(f"entrada: {', '.join(r['arquivos'])}")
    for a in r["avisos"]:
        print(f"AVISO {a.arquivo} {a.local}: {a.mensagem}")
    print(f"\nComissão CHECKOUT por lojista ({len(r['comissoes'])} lojistas):")
    for c in r["comissoes"]:
        print(f"  {c['cnpj']}  {c['lojista'][:40]:<40} {fmt_dinheiro(c['comissao_brl']):>12}  ({c['qtd_transacoes']} transações)")
    print(f"  {'TOTAL':<56} {fmt_dinheiro(r['total_checkout']):>12}")
    print(f"\nPendências: {len(r['pendencias'])} ({r['transacoes_em_pendencia']} de {r['transacoes_lidas']} transações da Orbe)")
    for p in r["pendencias"]:
        valor = fmt_dinheiro(p.valor_brl) if p.valor_brl is not None else "-"
        print(f"  {p.id_saida}: {valor} — quem decide: {p.quem_decide}")
    _imprimir_divergencias(r)
    _imprimir_remessa(r)
    _imprimir_notas(r)
    _imprimir_extratos(r)
    if r["erros_validacao"]:
        print(f"\nVALIDADOR: {len(r['erros_validacao'])} ERRO(S)", file=sys.stderr)
        for e in r["erros_validacao"]:
            print(f"  ERRO {e}", file=sys.stderr)
        return 1
    print(f"\nVALIDADOR: OK (rastro fecha com todos os totais; as {r['transacoes_lidas']} linhas da Orbe aparecem uma vez;"
          f" as {r['remessa']['linhas']} linhas do anexo da Ponte também; conservação do checkout e da remessa fecha;"
          " notas = comissões; extratos: cada lançamento uma vez, Σ Aurora = saldo final − inicial, contas lançáveis)")
    _imprimir_resumo(r, args.saida)
    return 0


def _imprimir_resumo(r: dict, saida: Path) -> None:
    """Resumo do fechamento para o financeiro: o que importa, sem jargão."""
    ano, mes = r["competencia"]
    div_c, div_r = r["divergencias"], r["remessa"]["divergencias"]
    notas = r["notas"]
    metodos = {m: sum(1 for l in r["lancamentos"] if l["metodo"] == m) for m in ("REGRA", "IA", "HUMANO")}
    por_resp: dict[str, int] = {}
    for p in r["pendencias"]:
        por_resp[p.quem_decide] = por_resp.get(p.quem_decide, 0) + 1

    def parte(divs, direcao):
        sel = [d["diferenca_brl"] for d in divs if d["direcao"] == direcao]
        return len(sel), fmt_brl(abs(sum(sel, ZERO)))

    obrig = ["comissoes_por_lojista.csv", "divergencias_taxa.csv", "notas_a_emitir.csv",
             "lancamentos_classificados.csv", "pendencias.csv", "rastro.csv"]
    extras = [a for a in r["arquivos_saida"] if a not in obrig]
    linha = "=" * 76
    print(f"\n{linha}\nRESUMO DO FECHAMENTO - {nome_mes(mes)} de {ano}\n{linha}")
    print(f"Comissão de checkout (cartão e Pix):    {fmt_brl(r['total_checkout']):>16}  ({len(r['comissoes'])} lojistas)")
    print(f"Comissão de remessa (50% do spread):    {fmt_brl(r['remessa']['total']):>16}  ({len(r['remessa']['comissoes'])} lojistas)")
    print(f"Notas fiscais a emitir:                 {fmt_brl(sum((n['valor_brl'] for n in notas), ZERO)):>16}  ({len(notas)} notas)")
    print("Taxa cobrada diferente do contrato (a Helena decide cada caso):")
    for nome, divs, unidade in (("checkout", div_c, "transações"), ("remessa", div_r, "operações")):
        for direcao, texto in (("COBROU_A_MAIS", "a mais"), ("COBROU_A_MENOS", "a menos")):
            n, v = parte(divs, direcao)
            if n:
                rotulo = f"  {nome}, cobrado {texto}:"
                print(f"{rotulo:<40}{v:>16}  ({n} {unidade})")
    print(f"Lançamentos dos extratos: {len(r['lancamentos'])} (por regra {metodos['REGRA']}, por IA conferida "
          f"{metodos['IA']}, por decisão de uma pessoa {metodos['HUMANO']})")
    print(f"Pendências: {len(r['pendencias'])}, com motivo e valor em pendencias.csv")
    for resp, n in sorted(por_resp.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {resp}: {n}")
    print(f"Arquivos em {saida.resolve()}:")
    print(f"  os 6 do fechamento: {', '.join(obrig)}")
    if extras:
        print(f"  extras: {', '.join(extras)}")
    print(linha)


if __name__ == "__main__":
    sys.exit(main())
