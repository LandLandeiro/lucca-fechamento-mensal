"""Notas fiscais a emitir: tomador, linha de negócio, valor e discriminação.

Responsabilidade: agregar as comissões por tomador segundo a regra de faturamento
confirmada (quem é o tomador em cada linha de negócio). `id_saida`:
`NF-<cnpj_tomador>-<linha>`. O rastro aponta para as mesmas linhas da comissão.
"""

from __future__ import annotations

from tarvo.modelo import ItemRastro


def notas_a_emitir(
    comissoes: list[dict], rastro_comissoes: list[ItemRastro], cadastro: dict, regras: dict
) -> tuple[list[dict], list[ItemRastro]]:
    """Lista de notas a emitir, com rastro."""
    raise NotImplementedError
