"""Leitor do extrato do Banco Meridiano (`05b_extrato_banco_meridiano_*.ofx`).

Armadilhas de leitura encontradas na exploração:
- OFX 1.02 SGML: tags de folha sem fechamento (`<TRNAMT>-450.00`); não é XML válido.
- O cabeçalho declara `ENCODING:USASCII` e `CHARSET:1252`, mas há bytes acentuados
  (Latin-1/CP1252): decodificar como cp1252, não como ASCII nem UTF-8.
- CRLF; valores com ponto decimal e sinal; datas `AAAAMMDDhhmmss[-3:BRT]`.
- Sem saldo inicial; só `LEDGERBAL` final.
- `ref_origem` = `FITID` (único no arquivo de set/2026).
"""

from __future__ import annotations

from pathlib import Path

from tarvo.modelo import LancamentoBancario


def ler_extrato_meridiano(caminho: Path) -> list[LancamentoBancario]:
    """Lê todos os STMTTRN."""
    raise NotImplementedError


def ler_saldo_final_meridiano(caminho: Path) -> dict:
    """Lê LEDGERBAL (saldo final e data)."""
    raise NotImplementedError
