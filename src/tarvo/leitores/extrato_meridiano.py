"""Leitor do extrato do Banco Meridiano (`05b_extrato_banco_meridiano_*.ofx`).

Armadilhas de leitura encontradas na exploração:
- OFX 1.02 SGML: tags de folha sem fechamento (`<TRNAMT>-450.00`); não é XML válido.
- O cabeçalho declara `ENCODING:USASCII` e `CHARSET:1252`, mas há bytes acentuados
  (Latin-1/CP1252): decodificar pelo CHARSET do cabeçalho (1252), não como ASCII nem UTF-8.
- CRLF; valores com ponto decimal e sinal; datas `AAAAMMDDhhmmss[-3:BRT]`.
- Sem saldo inicial; só `LEDGERBAL` final.
- `ref_origem` = `FITID` (único no arquivo de set/2026); a linha física do `<STMTTRN>`
  também é guardada.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from tarvo.leitores.extrato_aurora import LeituraExtrato
from tarvo.leitores.orbe import LinhaInvalida
from tarvo.modelo import Aviso, LancamentoBancario

BANCO = "MERIDIANO"
_RE_VALOR = re.compile(r"^-?\d+\.\d{2}$")
_RE_DATA = re.compile(r"^(\d{4})(\d{2})(\d{2})")
_RE_TAG = re.compile(r"<(\w+)>([^\r\n<]*)")


def ler_extrato_meridiano(caminho: Path) -> LeituraExtrato:
    """Lê todos os STMTTRN e o LEDGERBAL."""
    nome = caminho.name
    bruto = caminho.read_bytes()
    res = LeituraExtrato(arquivo=nome, banco=BANCO)
    cab = bruto[:400].decode("ascii", errors="replace")
    m = re.search(r"CHARSET:(\d+)", cab)
    encoding = f"cp{m.group(1)}" if m else "latin-1"
    if not m:
        res.avisos.append(Aviso(nome, "-", "OFX sem CHARSET no cabeçalho; lido como Latin-1"))
    texto = bruto.decode(encoding, errors="strict")
    linhas = texto.splitlines()

    vistos: set[str] = set()
    bloco: dict | None = None
    inicio = 0
    for n, linha in enumerate(linhas, start=1):
        s = linha.strip()
        if s.upper() == "<STMTTRN>":
            bloco, inicio = {}, n
            continue
        if s.upper() == "</STMTTRN>" and bloco is not None:
            _fechar(res, bloco, inicio, linha_bruta="\n".join(linhas[inicio - 1:n]), vistos=vistos)
            bloco = None
            continue
        if bloco is not None:
            for tag, valor in _RE_TAG.findall(s):
                bloco[tag.upper()] = valor.strip()

    m = re.search(r"<LEDGERBAL>.*?<BALAMT>([-\d.]+).*?<DTASOF>(\d{8})", texto, re.S)
    if m:
        res.saldo_final = Decimal(m.group(1))
        d = _RE_DATA.match(m.group(2))
        res.data_saldo_final = date(int(d.group(1)), int(d.group(2)), int(d.group(3)))
    return res


def _fechar(res: LeituraExtrato, b: dict, n: int, linha_bruta: str, vistos: set[str]) -> None:
    ref = b.get("FITID") or f"L{n}"
    valor, dt = b.get("TRNAMT", ""), _RE_DATA.match(b.get("DTPOSTED", ""))
    if not b.get("FITID") or not _RE_VALOR.match(valor) or not dt:
        res.linhas_invalidas.append(LinhaInvalida(n, ref, "FITID, TRNAMT ou DTPOSTED ilegível", linha_bruta))
        return
    if ref in vistos:
        res.linhas_invalidas.append(LinhaInvalida(n, ref, "FITID repetido no arquivo", linha_bruta))
        return
    vistos.add(ref)
    lan = LancamentoBancario(
        banco=BANCO, ref_origem=ref, data=date(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))),
        descricao=b.get("MEMO", ""), valor=Decimal(valor), documento=b.get("CHECKNUM") or None,
        arquivo_origem=res.arquivo,
    )
    tipo = b.get("TRNTYPE", "").upper()
    if (tipo == "CREDIT" and lan.valor < 0) or (tipo == "DEBIT" and lan.valor > 0):
        res.avisos.append(Aviso(res.arquivo, ref, f"TRNTYPE {tipo} com valor {lan.valor}"))
    res.lancamentos.append(lan)
    res.linhas_arquivo[ref] = n


def ler_saldo_final_meridiano(caminho: Path) -> dict:
    """LEDGERBAL (saldo final e data)."""
    r = ler_extrato_meridiano(caminho)
    return {"final": r.saldo_final, "data": r.data_saldo_final}
