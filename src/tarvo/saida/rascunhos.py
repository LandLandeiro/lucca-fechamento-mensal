"""Rascunhos de contestação, um por contraparte e por lojista (Q-T 2, Q-X 1; D68). Sem IA: texto fixo + números.

A Helena (09:53): "Um rascunho por contraparte, com as operações anexadas, eu reviso e envio." (11:01): "uma
pendência por contraparte e por lojista, com o detalhe das transações anexado."

Em `<saida>/rascunhos/`, cada rascunho é um `.md` (assunto, texto curto, total) + um `.csv` com a lista:
- Orbe, por lojista: as divergências de checkout de natureza `contrato_orbe` (D63). As de natureza
  `condicao_nao_informada` (Casa, Bridge) NÃO geram rascunho: não se cobra a Orbe (Q-N 1).
- Ponte, por motivo e lojista, a partir de `contestacao_ponte.csv`: spread acima do contratado (por lojista),
  spreads negativos (um rascunho, subtotal por lojista na lista), duplicata.
A pasta é refeita a cada execução (nada sobra de execução anterior). O validador confere que o total escrito
no `.md` (`total_brl=`) é a soma do `.csv` e que nenhuma linha de `condicao_nao_informada` está num rascunho.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from tarvo.cadastro import normalizar_nome
from tarvo.formatos import fmt_brl, fmt_dinheiro, nome_mes
from tarvo.saida.escritor import formatar

ZERO = Decimal("0")
PASTA = "rascunhos"
COLUNAS_ORBE = ["id_transacao", "data", "tipo_lancamento", "valor_bruto", "taxa_aplicada_pct", "taxa_contratada_pct",
                "valor_brl"]
COLUNAS_PONTE = ["numero_operacao", "linha_anexo", "lojista", "cnpj", "data_contratacao", "moeda", "valor_me", "ptax_ref",
                 "taxa_cliente", "spread_aplicado_pct", "spread_contratado_pct", "spread_brl", "diferenca_contrato_brl", "valor_brl"]


def _slug(nome: str) -> str:
    palavras = [p for p in normalizar_nome(nome).replace("-", " ").split() if p not in ("LTDA", "S.A.", "SA", "ME", "EIRELI")]
    return "_".join(palavras[:2]).lower()


def _escrever(pasta: Path, base: str, colunas: list[str], linhas: list[dict], md: str) -> None:
    with open(pasta / f"{base}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(colunas)
        for l in linhas:
            w.writerow([formatar(c, l.get(c)) for c in colunas])
    (pasta / f"{base}.md").write_bytes(md.encode("utf-8"))


def _md(para: str, assunto: str, texto: list[str], total: Decimal, anexo: str, rodape: str) -> str:
    return "\n".join([
        "> RASCUNHO para a Helena revisar e enviar (gerado pelo fechamento; não foi enviado a ninguém).",
        "",
        f"**Para:** {para}",
        f"**Assunto:** {assunto}",
        "",
        *texto,
        "",
        f"**Total:** {fmt_brl(total)} (`total_brl={fmt_dinheiro(total)}`)",
        "",
        f"**Anexo:** `{anexo}` (uma linha por transação/operação).",
        "",
        rodape,
        "",
    ])


def gerar_rascunhos(saida: Path, divergencias: list[dict], contestacao: list[dict], competencia: tuple[int, int],
                    nome_ponte: str) -> list[str]:
    """Escreve os rascunhos e devolve os nomes dos `.md`, em ordem."""
    pasta = saida / PASTA
    pasta.mkdir(parents=True, exist_ok=True)
    for p in pasta.iterdir():
        if p.is_file() and p.suffix in (".md", ".csv"):
            p.unlink()
    mes = f"{nome_mes(competencia[1])} de {competencia[0]}"
    feitos: list[str] = []

    por_lojista: dict[str, list[dict]] = {}
    for d in divergencias:
        if d["linha_negocio"] == "CHECKOUT" and d["natureza"] == "contrato_orbe":
            por_lojista.setdefault(d["cnpj"], []).append(d)
    for cnpj, ds in sorted(por_lojista.items(), key=lambda kv: kv[1][0]["lojista"]):
        ds = sorted(ds, key=lambda d: (d["data"], d["ref_origem"]))
        nome, total = ds[0]["lojista"], sum((d["diferenca_brl"] for d in ds), ZERO)
        base = f"orbe_{_slug(nome)}"
        sentido = "a mais" if total > 0 else "a menos"
        linhas = [{"id_transacao": d["ref_origem"], "data": d["data"], "tipo_lancamento": d["tipo_lancamento"],
                   "valor_bruto": d["valor_bruto"], "taxa_aplicada_pct": d["taxa_aplicada_pct"],
                   "taxa_contratada_pct": d["taxa_contratada_pct"], "valor_brl": d["diferenca_brl"]} for d in ds]
        _escrever(pasta, base, COLUNAS_ORBE, linhas, _md(
            "Orbe Adquirência", f"Taxa acima do contrato - {nome} (CNPJ {cnpj}) - {mes}",
            [f"No fechamento de {mes}, a taxa aplicada em {len(ds)} transações de {nome} (CNPJ {cnpj}) ficou diferente "
             f"da taxa contratada, de {ds[0]['data'].strftime('%d/%m')} a {ds[-1]['data'].strftime('%d/%m')}. "
             f"A diferença, cobrada {sentido}, soma {fmt_brl(abs(total))}, calculada como valor bruto × (taxa aplicada − "
             f"taxa contratada), transação por transação.",
             "",
             "Pedimos a conferência e a devolução da diferença ao lojista no próximo repasse. A lista anexa traz cada "
             "transação com a taxa aplicada e a contratada."],
            total, f"{base}.csv", "Origem: `divergencias_taxa.csv` (natureza `contrato_orbe`)."))
        feitos.append(f"{base}.md")

    grupos: dict[tuple[str, str], list[dict]] = {}
    for l in contestacao:
        chave = (l["motivo"], l["cnpj"] if l["motivo"] == "SPREAD_ACIMA_DO_CONTRATADO" else "")
        grupos.setdefault(chave, []).append(l)
    textos = {
        "SPREAD_ACIMA_DO_CONTRATADO": lambda ls: (
            f"ponte_{_slug(ls[0]['lojista'])}",
            f"Spread acima do contratado - {ls[0]['lojista']} (CNPJ {ls[0]['cnpj']}) - {mes}",
            [f"Em {len(ls)} operações de {ls[0]['lojista']} em {mes}, o spread aplicado ficou acima do contratado "
             f"({', '.join(sorted({formatar('x_pct', l['spread_contratado_pct']) for l in ls}))}% sobre a PTAX). O lojista "
             f"pagou a mais, no valor cheio, a diferença do total abaixo: (spread aplicado − contratado) × PTAX × valor em "
             f"moeda estrangeira, operação por operação.",
             "", "Pedimos a correção e a devolução ao lojista. A lista anexa traz cada operação."]),
        "SPREAD_NEGATIVO": lambda ls: (
            "ponte_spreads_negativos", f"Spreads negativos - trava vencida - {mes}",
            [f"Em {len(ls)} operações de {mes}, o relatório traz spread negativo com a observação de taxa travada no pedido. "
             f"Pelo contrato, a trava vale 2 horas, e essas operações passaram do prazo. Não aceitamos esses spreads; o "
             f"total abaixo é o Spread R$ do relatório. Subtotais por lojista: "
             + "; ".join(f"{n} {fmt_brl(sum((l['valor_contestado_brl'] for l in ls if l['lojista'] == n), ZERO))}"
                         for n in sorted({l['lojista'] for l in ls})) + ".",
             "", "Pedimos a revisão dessas operações. A lista anexa traz cada uma, com o valor contra o contrato."]),
        "DUPLICATA": lambda ls: (
            "ponte_duplicata", f"Operação repetida no relatório - {mes}",
            [f"O relatório de {mes} traz {len(ls)} operação(ões) repetida(s) com o mesmo número "
             f"({', '.join(l['ref_origem'] for l in ls)}). Contamos cada número uma vez no fechamento.",
             "", "Pedimos a correção do relatório. A lista anexa traz a linha repetida."]),
    }
    for (motivo, _), ls in sorted(grupos.items()):
        ls = sorted(ls, key=lambda l: l["linha_anexo"])
        base, assunto, texto = textos[motivo](ls)
        total = sum((l["valor_contestado_brl"] for l in ls), ZERO)
        linhas = [{"numero_operacao": l["ref_origem"], "linha_anexo": l["linha_anexo"], "lojista": l["lojista"],
                   "cnpj": l["cnpj"], "data_contratacao": l["data_contratacao"], "moeda": l["moeda"], "valor_me": l["valor_me"],
                   "ptax_ref": l["ptax_ref"], "taxa_cliente": l["taxa_cliente"], "spread_aplicado_pct": l["spread_aplicado_pct"],
                   "spread_contratado_pct": l["spread_contratado_pct"], "spread_brl": l["spread_brl"],
                   "diferenca_contrato_brl": l["diferenca_contrato_brl"],
                   "valor_brl": l["valor_contestado_brl"]} for l in ls]
        _escrever(pasta, base, COLUNAS_PONTE, linhas, _md(nome_ponte, assunto, texto, total, f"{base}.csv",
                                                          f"Origem: `contestacao_ponte.csv` (motivo {motivo})."))
        feitos.append(f"{base}.md")
    return sorted(feitos)
