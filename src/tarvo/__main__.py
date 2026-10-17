"""CLI: `python -m tarvo --dados data --saida saida`.

Nível mínimo (E1+E2): comissão de CHECKOUT por lojista + rastro + pendências, validados.
Os arquivos de entrada são achados pelo prefixo do nome (o mesmo formato chega todo mês);
nada de setembro está fixo no código. Saída inválida → código 1.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from tarvo.cadastro import montar_cadastro
from tarvo.calculos.comissoes import comissao_checkout
from tarvo.formatos import fmt_dinheiro
from tarvo.leitores.orbe import ErroLeitura, ler_orbe
from tarvo.leitores.taxas import ler_taxas_vigentes
from tarvo.modelo import Pendencia
from tarvo.pendencias import consolidar_pendencias, pendencia_para_linha
from tarvo.regras import RegraInvalida, RegraPendente, carregar_regras, valor_da_regra
from tarvo.saida.escritor import escrever_saida
from tarvo.saida.validador import validar_saida

PADRAO_ORBE = "01_orbe_relatorio_comissoes_*.csv"
PADRAO_TAXAS = "02_tabela_taxas_contratadas*.xlsx"


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
    """Roda o fechamento (nível mínimo) e devolve o resumo. Levanta exceção em erro de entrada."""
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

    pend_leitura = [
        Pendencia(f"PEN-LEITURA_INVALIDA-{li.ref_origem}", "LEITURA_INVALIDA", f"{orbe.arquivo}:L{li.linha_arquivo}",
                  None, f"linha não lida: {li.motivo}", "analista (conferir o arquivo com a Orbe)")
        for li in orbe.linhas_invalidas
    ]
    pendencias = consolidar_pendencias(checkout.pendencias, pend_leitura)
    if len(orbe.transacoes) + len(orbe.linhas_invalidas) != orbe.total_linhas_dados:
        raise AssertionError("linhas da Orbe perdidas entre leitura e cálculo")

    escrever_saida(
        {
            "comissoes_por_lojista.csv": checkout.comissoes,
            "pendencias.csv": [pendencia_para_linha(p) for p in pendencias],
            "rastro.csv": checkout.rastro,
        },
        saida,
    )
    erros = validar_saida(saida, {orbe.arquivo: {t.ref_origem for t in orbe.transacoes}})
    return {
        "arquivos": [arq_orbe.name, arq_taxas.name],
        "avisos": orbe.avisos + taxas.avisos + cadastro.avisos,
        "comissoes": checkout.comissoes,
        "total_checkout": sum((c["comissao_brl"] for c in checkout.comissoes), Decimal("0")),
        "pendencias": pendencias,
        "transacoes_em_pendencia": len(checkout.em_pendencia) + len(orbe.linhas_invalidas),
        "transacoes_lidas": orbe.total_linhas_dados,
        "erros_validacao": erros,
    }


def main(argv: list[str] | None = None) -> int:
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
    if r["erros_validacao"]:
        print(f"\nVALIDADOR: {len(r['erros_validacao'])} ERRO(S)", file=sys.stderr)
        for e in r["erros_validacao"]:
            print(f"  ERRO {e}", file=sys.stderr)
        return 1
    print(f"\nVALIDADOR: OK (rastro fecha com todos os totais; as {r['transacoes_lidas']} linhas da Orbe aparecem uma vez)")
    print(f"saída: {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
