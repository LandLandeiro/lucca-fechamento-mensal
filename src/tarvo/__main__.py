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

from tarvo.cadastro import montar_cadastro
from tarvo.calculos.comissoes import comissao_checkout, ordem_comissao
from tarvo.calculos.divergencias import divergencias_checkout, divergencias_remessa
from tarvo.calculos.notas import conferencia_repasse, notas_a_emitir
from tarvo.calculos.remessa import classificar_remessa, comissao_remessa
from tarvo.formatos import fmt_dinheiro, modo_arredondamento
from tarvo.leitores.orbe import ErroLeitura, ler_orbe
from tarvo.leitores.ponte_email import ler_email, ler_operacoes
from tarvo.leitores.taxas import ler_taxas_vigentes
from tarvo.modelo import Aviso, Pendencia
from tarvo.pendencias import consolidar_pendencias, pendencia_para_linha
from tarvo.regras import RegraInvalida, RegraPendente, carregar_regras, valor_da_regra
from tarvo.saida.escritor import escrever_saida
from tarvo.saida.validador import validar_saida

PADRAO_ORBE = "01_orbe_relatorio_comissoes_*.csv"
PADRAO_TAXAS = "02_tabela_taxas_contratadas*.xlsx"
PADRAO_PONTE = "03_email_ponte_cambio_*.eml"
ZERO = Decimal("0")


class ErroEntrada(RuntimeError):
    pass


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tarvo",
        description="Fechamento mensal da Tarvo: lê o data pack como chega e gera os CSVs de saída.",
    )
    parser.add_argument("--dados", type=Path, default=Path("data"), help="pasta do data pack (padrão: data)")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="pasta dos CSVs gerados (padrão: saida)")
    parser.add_argument("--regras", type=Path, default=Path("regras.yaml"), help="arquivo de regras (padrão: regras.yaml)")
    return parser


def achar_unico(pasta: Path, padrao: str) -> Path:
    achados = sorted(pasta.glob(padrao))
    if len(achados) != 1:
        raise ErroEntrada(f"esperado 1 arquivo {padrao!r} em {pasta}, achei {len(achados)}: {[p.name for p in achados]}")
    return achados[0]


def executar(dados: Path, saida: Path, regras_path: Path) -> dict:
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
        nf_remessa, ponte.totais_declarados.get("Spread total R$:"), cls_remessa, mail.corpo, ponte.arquivo, regras
    )
    pendencias = consolidar_pendencias(
        checkout.pendencias, remessa.pendencias, div_remessa.pendencias, pend_leitura, notas.pendencias, pend_repasse,
        div_remessa.pendencias_derivadas,
    )
    divs = divergencias.linhas + div_remessa.linhas
    rastro = sorted(
        checkout.rastro + divergencias.rastro + remessa.rastro + div_remessa.rastro
        + notas.rastro + notas.rastro_pendencias + rastro_repasse + div_remessa.rastro_pendencias,
        key=lambda l: (l["id_saida"], l["linha_arquivo"], l["ref_origem"]),
    )
    escrever_saida(
        {
            "comissoes_por_lojista.csv": comissoes,
            "divergencias_taxa.csv": divs,
            "notas_a_emitir.csv": notas.linhas,
            "pendencias.csv": [pendencia_para_linha(p) for p in pendencias],
            "rastro.csv": rastro,
        },
        saida,
    )
    erros = validar_saida(
        saida,
        refs_esperadas={
            orbe.arquivo: {(t.ref_origem, t.linha_arquivo) for t in orbe.transacoes},
            ponte.arquivo: {(o.ref_origem, o.linha_planilha) for o in ponte.operacoes},
        },
        fonte_orbe={orbe.arquivo: {t.ref_origem: (t.valor_taxa, t.valor_bruto, t.taxa_aplicada_pct / 100) for t in orbe.transacoes}},
        modo_checkout=modo_arredondamento(valor_da_regra(regras, "checkout.arredondamento_comissao_contratada")),
        spread_ponte={ponte.arquivo: {(o.ref_origem, o.linha_planilha): o.spread_brl for o in ponte.operacoes}},
        spread_declarado=ponte.totais_declarados.get("Spread total R$:"),
    )
    excl: dict[str, list] = {}
    for op, motivo, _ in cls_remessa.excluidas:
        excl.setdefault(motivo, []).append(op)
    return {
        "arquivos": [arq_orbe.name, arq_taxas.name, f"{arq_ponte.name} (anexo {mail.nome_anexo})"],
        "avisos": orbe.avisos + taxas.avisos + cadastro.avisos + ponte.avisos + avisos_extra,
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
        "pendencias_novas": notas.pendencias + pend_repasse + div_remessa.pendencias_derivadas,
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
        impacto = sum((d["impacto_repasse_tarvo"] or ZERO for d in ds), ZERO)
        print(f"  {tipo:<20} {cnpj} {ds[0]['lojista'][:30]:<30} {len(ds):>3}  {fmt_dinheiro(sum((d['diferenca_brl'] for d in ds), ZERO)):>10}"
              + (f"  impacto no repasse {fmt_dinheiro(impacto)}" if tipo == "SPREAD_NEGATIVO" else ""))


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
        r = executar(args.dados, args.saida, args.regras)
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
    if r["erros_validacao"]:
        print(f"\nVALIDADOR: {len(r['erros_validacao'])} ERRO(S)", file=sys.stderr)
        for e in r["erros_validacao"]:
            print(f"  ERRO {e}", file=sys.stderr)
        return 1
    print(f"\nVALIDADOR: OK (rastro fecha com todos os totais; as {r['transacoes_lidas']} linhas da Orbe aparecem uma vez;"
          f" as {r['remessa']['linhas']} linhas do anexo da Ponte também; conservação do checkout e da remessa fecha;"
          " notas = comissões)")
    print(f"saída: {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
