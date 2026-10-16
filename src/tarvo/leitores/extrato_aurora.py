"""Leitor do extrato do Banco Aurora (`05a_extrato_banco_aurora_*.csv`).

Armadilhas de leitura encontradas na exploração:
- UTF-8 sem BOM, quebra de linha LF, separador `;`.
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

from pathlib import Path

from tarvo.modelo import LancamentoBancario


def ler_extrato_aurora(caminho: Path) -> list[LancamentoBancario]:
    """Lê os lançamentos (sem saldos nem cabeçalhos)."""
    raise NotImplementedError


def ler_saldos_aurora(caminho: Path) -> dict:
    """Lê o saldo anterior e o final declarados, para conferir o saldo corrido."""
    raise NotImplementedError
