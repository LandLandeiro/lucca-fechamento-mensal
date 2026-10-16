"""Leitor do plano de contas do ERP Fênix (`04_plano_de_contas_fenix_erp.csv`).

Armadilhas de leitura encontradas na exploração:
- Encoding Latin-1 (ISO-8859-1), não UTF-8; CRLF; separador `;`; cabeçalho na linha 1.
- Contas SINTETICA e ANALITICA; só `ACEITA_LANCTO = S` pode receber lançamento.
- `COD_SUPERIOR` vazio nas contas de 1º nível.
"""

from __future__ import annotations

from pathlib import Path

from tarvo.modelo import ContaContabil


def ler_plano_contas(caminho: Path) -> list[ContaContabil]:
    """Lê todas as contas do plano."""
    raise NotImplementedError
