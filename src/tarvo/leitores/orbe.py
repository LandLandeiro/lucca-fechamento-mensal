"""Leitor do relatório de comissões da Orbe (`01_orbe_relatorio_comissoes_*.csv`).

Armadilhas de leitura encontradas na exploração:
- ASCII, quebra de linha CRLF, separador `;`, cabeçalho na linha 1, sem rodapé.
- Decimal com vírgula e SEM separador de milhar (`5773,57`); negativo com `-` à esquerda.
- Datas `DD/MM/AAAA`.
- ANTECIPACAO e REVERSAO ANTECIPACAO vêm com `modalidade`, `qtd_parcelas` e `bandeira` vazios.
- ESTORNO e REVERSAO têm sinal negativo em bruto, taxa e líquido, e trazem
  `id_referencia` + `data_venda_original` (a venda original pode ser de agosto e não
  estar no arquivo).
- `id_transacao` é único (prefixos TX e AN). A `bandeira` do estorno pode diferir da
  venda original: não usar como chave.
- O mesmo EC aparece com até 3 nomes diferentes: o nome não é chave.
- `ref_origem` = `id_transacao`.

O leitor não aplica regra de negócio. Linha que não lê (coluna faltando, número ou data
fora do formato, id repetido) vai para `linhas_invalidas` com o motivo: nunca é corrigida.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from tarvo.formatos import FormatoInvalido, data_br, decimal_br
from tarvo.modelo import Aviso, TransacaoOrbe

COLUNAS = [
    "id_transacao", "data_movimento", "cod_estabelecimento", "nome_estabelecimento",
    "tipo_lancamento", "modalidade", "qtd_parcelas", "bandeira", "valor_bruto",
    "taxa_aplicada_pct", "valor_taxa", "valor_liquido", "id_referencia", "data_venda_original",
]


class ErroLeitura(RuntimeError):
    """O arquivo inteiro não pode ser lido com segurança (encoding, cabeçalho)."""


@dataclass(frozen=True)
class LinhaInvalida:
    linha_arquivo: int
    ref_origem: str  # id_transacao se legível, senão "L<n>"
    motivo: str
    conteudo: str


@dataclass
class LeituraOrbe:
    arquivo: str
    transacoes: list[TransacaoOrbe] = field(default_factory=list)
    linhas_invalidas: list[LinhaInvalida] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    total_linhas_dados: int = 0


def ler_orbe(caminho: Path) -> LeituraOrbe:
    """Lê todas as linhas de dados do relatório da Orbe."""
    nome = caminho.name
    bruto = caminho.read_bytes()
    try:
        texto = bruto.decode("utf-8")  # o arquivo é ASCII; UTF-8 é superconjunto
    except UnicodeDecodeError as e:
        raise ErroLeitura(f"{nome}: bytes fora de ASCII/UTF-8 na posição {e.start}; encoding não confirmado") from e
    if texto.startswith("﻿"):
        texto = texto[1:]

    leitor = csv.reader(io.StringIO(texto, newline=""), delimiter=";")
    cabecalho = next(leitor, None)
    if cabecalho != COLUNAS:
        raise ErroLeitura(f"{nome}: cabeçalho diferente do esperado: {cabecalho}")

    res = LeituraOrbe(arquivo=nome)
    vistos: set[str] = set()
    for campos in leitor:
        n = leitor.line_num
        if not any(c.strip() for c in campos):
            continue  # linha vazia (ex.: quebra final)
        res.total_linhas_dados += 1
        conteudo = ";".join(campos)
        ref = campos[0].strip() if campos and campos[0].strip() else f"L{n}"
        if len(campos) != len(COLUNAS):
            res.linhas_invalidas.append(LinhaInvalida(n, ref, f"{len(campos)} colunas (esperado {len(COLUNAS)})", conteudo))
            continue
        c = dict(zip(COLUNAS, (x.strip() for x in campos)))
        if c["id_transacao"] in vistos:
            res.linhas_invalidas.append(LinhaInvalida(n, ref, "id_transacao repetido no arquivo", conteudo))
            continue
        try:
            t = TransacaoOrbe(
                ref_origem=c["id_transacao"],
                linha_arquivo=n,
                data_movimento=data_br(c["data_movimento"]),
                cod_estabelecimento=c["cod_estabelecimento"],
                nome_estabelecimento=c["nome_estabelecimento"],
                tipo_lancamento=c["tipo_lancamento"],
                modalidade=c["modalidade"] or None,
                qtd_parcelas=_inteiro_opcional(c["qtd_parcelas"]),
                bandeira=c["bandeira"] or None,
                valor_bruto=decimal_br(c["valor_bruto"]),
                taxa_aplicada_pct=decimal_br(c["taxa_aplicada_pct"]),
                valor_taxa=decimal_br(c["valor_taxa"]),
                valor_liquido=decimal_br(c["valor_liquido"]),
                id_referencia=c["id_referencia"] or None,
                data_venda_original=data_br(c["data_venda_original"]) if c["data_venda_original"] else None,
                arquivo_origem=nome,
            )
        except FormatoInvalido as e:
            res.linhas_invalidas.append(LinhaInvalida(n, ref, str(e), conteudo))
            continue
        if not c["id_transacao"] or not c["cod_estabelecimento"].isdigit():
            res.linhas_invalidas.append(LinhaInvalida(n, ref, "id_transacao vazio ou EC não numérico", conteudo))
            continue
        if t.valor_bruto - t.valor_taxa != t.valor_liquido:
            res.avisos.append(Aviso(nome, f"L{n}", f"{t.ref_origem}: líquido ≠ bruto − taxa"))
        vistos.add(t.ref_origem)
        res.transacoes.append(t)

    meses = {(t.data_movimento.year, t.data_movimento.month) for t in res.transacoes}
    if len(meses) > 1:
        res.avisos.append(Aviso(nome, "-", f"data_movimento em mais de um mês: {sorted(meses)}"))
    return res


def _inteiro_opcional(texto: str) -> int | None:
    if not texto:
        return None
    if not texto.isdigit():
        raise FormatoInvalido(f"qtd_parcelas não inteiro: {texto!r}")
    return int(texto)
