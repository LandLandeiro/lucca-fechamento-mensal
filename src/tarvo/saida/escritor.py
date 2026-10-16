"""Escritor dos CSVs de `saida/`.

Formato fixo (docs/case.md): separador `;`, ponto decimal, datas AAAA-MM-DD, CNPJ só
números (14 dígitos), `linha_negocio` CHECKOUT|REMESSA, `banco` AURORA|MERIDIANO,
`metodo` REGRA|IA|HUMANO. A formatação acontece só aqui; as contas chegam em Decimal.
"""

from __future__ import annotations

from pathlib import Path

from tarvo.modelo import ResultadoFechamento

COLUNAS = {
    "comissoes_por_lojista.csv": ["id_saida", "cnpj", "lojista", "linha_negocio", "comissao_brl"],
    "divergencias_taxa.csv": [
        "id_saida", "cnpj", "linha_negocio", "ref_origem",
        "taxa_contratada_pct", "taxa_aplicada_pct", "diferenca_brl",
    ],
    "notas_a_emitir.csv": [
        "id_saida", "tomador_cnpj", "tomador", "linha_negocio", "valor_brl", "discriminacao",
    ],
    "lancamentos_classificados.csv": [
        "id_saida", "banco", "ref_origem", "data", "descricao", "valor",
        "conta_codigo", "metodo", "confianca",
    ],
    "pendencias.csv": ["id_saida", "tipo", "ref_origem", "valor_brl", "motivo", "quem_decide"],
    "rastro.csv": ["id_saida", "arquivo_origem", "ref_origem", "valor"],
}


def escrever_saida(resultado: ResultadoFechamento, pasta: Path) -> list[Path]:
    """Escreve os 6 CSVs e devolve os caminhos."""
    raise NotImplementedError
