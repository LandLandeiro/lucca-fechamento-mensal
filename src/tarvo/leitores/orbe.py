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
"""

from __future__ import annotations

from pathlib import Path

from tarvo.modelo import TransacaoOrbe


def ler_orbe(caminho: Path) -> list[TransacaoOrbe]:
    """Lê todas as linhas de dados do relatório da Orbe."""
    raise NotImplementedError
