"""Leitor do e-mail da Ponte Câmbio (`03_email_ponte_cambio_*.eml`) e do anexo .xlsx.

Armadilhas de leitura encontradas na exploração:
- MIME multipart; assunto em encoded-word UTF-8; corpo text/plain em quoted-printable.
- O corpo traz informação de negócio (participação de 50% do spread realizado, data de
  crédito, NF de intermediação, status "APROVADO C/ RESSALVA", prazo de contestação,
  CNPJ da Ponte). O leitor devolve o texto; a interpretação fica em `regras.yaml`.
- Anexo .xlsx em base64: usar o pacote `email` em vez de fatiar linhas (a última linha
  do base64 é curta e some num filtro por tamanho).
- Aba "Operações": título em R1–R3 (parceiro, CNPJ, competência), cabeçalho em R5,
  dados até a primeira linha sem "Nº Operação"; depois vêm linhas de total
  ("Total de operações:", "Spread total R$:") que NÃO são dados.
- Aba "Resumo": totais por moeda (só para conferência).
- Datas como serial do Excel; CNPJ com e sem máscara; nome cortado em 20 caracteres.
- Floats binários (72214.46000000001): converter via str → Decimal e quantizar.
- `Nº Operação` pode repetir (PC-0926-0162 aparece 2×, a 2ª com obs "reprocessada").
  O leitor preserva as duas linhas; a duplicidade é tratada depois.
- `ref_origem` = `Nº Operação` (a linha da planilha também é guardada).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tarvo.modelo import OperacaoPonte


@dataclass(frozen=True)
class EmailPonte:
    remetente: str
    data_envio: str
    assunto: str
    corpo: str
    nome_anexo: str
    anexo_xlsx: bytes


def ler_email(caminho: Path) -> EmailPonte:
    """Decodifica o .eml: cabeçalhos, corpo em texto e bytes do anexo .xlsx."""
    raise NotImplementedError


def ler_operacoes(anexo_xlsx: bytes, nome_anexo: str) -> list[OperacaoPonte]:
    """Lê a aba "Operações" do anexo."""
    raise NotImplementedError


def ler_totais_declarados(anexo_xlsx: bytes) -> dict:
    """Lê as linhas de total e a aba "Resumo", para conferir contra as operações."""
    raise NotImplementedError
