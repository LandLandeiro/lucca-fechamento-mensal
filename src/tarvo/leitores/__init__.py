"""Leitores: um por fonte. Leem o arquivo exatamente como chega, sem limpeza manual.

Regra comum: todo registro nasce com `arquivo_origem` e `ref_origem`. Leitor não
aplica regra de negócio; só converte formato (encoding, decimal, data) de forma exata.
Detalhes de cada formato em docs/EXPLORACAO.md, seção 0.
"""
