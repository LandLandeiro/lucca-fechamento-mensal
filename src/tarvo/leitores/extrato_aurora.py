"""Leitor do extrato do Banco Aurora (`05a_extrato_banco_aurora_*.csv`).

Armadilhas de leitura encontradas na exploração:
- UTF-8 sem BOM, quebra de linha LF, separador `;` (se não for UTF-8 válido, lê como
  Latin-1 e registra aviso).
- Linhas que não são lançamento: L1–L5 cabeçalho do banco (cliente, CNPJ, agência,
  período), L6 vazia, L7 cabeçalho de colunas, L8 "SALDO ANTERIOR", linha vazia,
  "SALDO FINAL" e o rodapé "Os lançamentos estão sujeitos a confirmação.". Identificar
  pelo conteúdo (data válida na 1ª coluna e não ser SALDO), nunca por número fixo de linha.
- Valores com milhar em ponto e decimal em vírgula (`-1.019.882,54`).
- A coluna Saldo permite conferir o saldo corrido (em set/2026 bate linha a linha).
- `ref_origem` = `L<n>`, número da linha física do arquivo contado a partir de 1
  (1º lançamento de set/2026 = L9).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from tarvo.formatos import FormatoInvalido, data_br, decimal_br
from tarvo.leitores.orbe import LinhaInvalida
from tarvo.modelo import Aviso, LancamentoBancario

BANCO = "AURORA"
_RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


@dataclass
class LeituraExtrato:
    arquivo: str
    banco: str
    lancamentos: list[LancamentoBancario] = field(default_factory=list)
    linhas_arquivo: dict[str, int] = field(default_factory=dict)  # ref_origem → linha física
    linhas_invalidas: list[LinhaInvalida] = field(default_factory=list)
    avisos: list[Aviso] = field(default_factory=list)
    saldo_inicial: Decimal | None = None
    saldo_final: Decimal | None = None
    data_saldo_final: date | None = None


CABECALHO_ESPERADO = ["Data", "Lançamento", "Documento", "Valor (R$)", "Saldo (R$)"]


def ler_extrato_aurora(caminho: Path) -> LeituraExtrato:
    """Lê os lançamentos (sem saldos nem cabeçalhos) e os saldos declarados."""
    nome = caminho.name
    bruto = caminho.read_bytes()
    res = LeituraExtrato(arquivo=nome, banco=BANCO)
    try:
        texto = bruto.decode("utf-8")
    except UnicodeDecodeError:
        texto = bruto.decode("latin-1")
        res.avisos.append(Aviso(nome, "-", "arquivo não é UTF-8 válido; lido como Latin-1"))
    texto = texto.lstrip("﻿")

    saldo_corrido: Decimal | None = None
    cabecalho_visto = False
    for n, linha in enumerate(texto.splitlines(), start=1):
        c = [x.strip() for x in linha.split(";")]
        if c and c[0] == "Data" and not cabecalho_visto:  # D84: lido por posição; o cabeçalho é conferido e avisa
            cabecalho_visto = True
            if c[:5] != CABECALHO_ESPERADO:
                res.avisos.append(Aviso(nome, f"L{n}", f"cabeçalho de colunas diferente do esperado: {c[:5]} × "
                                                     f"{CABECALHO_ESPERADO}; o leitor usa a posição das colunas, confira o layout"))
            continue
        if len(c) < 5:
            continue
        data_txt, historico, documento, valor_txt, saldo_txt = c[:5]
        if historico.upper().startswith("SALDO ANTERIOR"):
            try:
                res.saldo_inicial = saldo_corrido = decimal_br(saldo_txt, milhar=True)
            except FormatoInvalido as e:
                res.avisos.append(Aviso(nome, f"L{n}", f"saldo anterior ilegível: {e}"))
            continue
        if historico.upper().startswith("SALDO FINAL"):
            try:
                res.saldo_final = decimal_br(saldo_txt, milhar=True)
            except FormatoInvalido as e:
                res.avisos.append(Aviso(nome, f"L{n}", f"saldo final ilegível: {e}"))
            continue
        if not _RE_DATA.match(data_txt):
            continue  # cabeçalho, linha vazia, rodapé
        ref = f"L{n}"
        try:
            lan = LancamentoBancario(
                banco=BANCO, ref_origem=ref, data=data_br(data_txt), descricao=historico,
                valor=decimal_br(valor_txt, milhar=True), documento=documento or None, arquivo_origem=nome,
            )
            saldo = decimal_br(saldo_txt, milhar=True) if saldo_txt else None
        except FormatoInvalido as e:
            res.linhas_invalidas.append(LinhaInvalida(n, ref, str(e), linha))
            continue
        res.lancamentos.append(lan)
        res.linhas_arquivo[ref] = n
        if saldo_corrido is not None:
            saldo_corrido += lan.valor
            if saldo is not None and saldo != saldo_corrido:
                res.avisos.append(Aviso(nome, ref, f"saldo corrido {saldo_corrido} ≠ saldo do extrato {saldo}"))
                saldo_corrido = saldo
        if saldo is not None:
            res.data_saldo_final = lan.data
    if not cabecalho_visto:
        res.avisos.append(Aviso(nome, "-", f"cabeçalho de colunas {CABECALHO_ESPERADO} não encontrado; confira o layout"))
    return res


def ler_saldos_aurora(caminho: Path) -> dict:
    """Saldo anterior e final declarados no extrato."""
    r = ler_extrato_aurora(caminho)
    return {"inicial": r.saldo_inicial, "final": r.saldo_final}
