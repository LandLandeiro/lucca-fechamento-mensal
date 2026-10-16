"""Leitor da tabela de taxas contratadas (`02_tabela_taxas_contratadas.xlsx`).

Armadilhas de leitura encontradas na exploração:
- Duas abas: "Taxas vigentes" (usar) e "ANTIGO 2025 - nao usar" (nunca para taxa; é a
  única fonte de alguns dados cadastrais, ex.: CNPJ da Atlas Idiomas).
- "Taxas vigentes": R1–R2 título e "última atualização", R4 grupo mesclado (D4:I4),
  cabeçalho em R5, dados de R6 até a primeira linha vazia; depois de uma linha vazia,
  nota de rodapé ("* spread em branco = padrão").
- Percentual misturado na mesma coluna: número (0.0269) e texto ("2,69%", ex.: R20, R21).
- Ruído de float (0.007900000000000001): converter via str → Decimal e quantizar em
  4 casas de fração.
- CNPJ em 3 formatos: com máscara, só dígitos, e NÚMERO sem zero à esquerda (R14, R25).
- EC Orbe vazio em alguns lojistas (R8, R9 "EC pendente", R28) e nos só de remessa.
- Vigência em texto livre ("01/01/2026", "até 14/09/2026", "a partir de 15/09/2026").
- Spread remessa pode ser número, vazio ou o texto "padrão".
- Comentário de célula (A13) e linha inativa com estilo diferente (R30, obs "INATIVO").
- Ler com openpyxl (`data_only=True`); os comentários vêm do objeto da célula.
"""

from __future__ import annotations

from pathlib import Path

from tarvo.modelo import TaxaContratada


def ler_taxas_vigentes(caminho: Path) -> list[TaxaContratada]:
    """Lê a aba "Taxas vigentes", com os valores crus e o número da linha da planilha."""
    raise NotImplementedError


def ler_aba_antiga(caminho: Path) -> list[dict]:
    """Lê a aba "ANTIGO 2025 - nao usar" só como referência cadastral (nunca como taxa)."""
    raise NotImplementedError
