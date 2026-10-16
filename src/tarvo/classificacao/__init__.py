"""Classificação dos lançamentos dos extratos no plano de contas.

Ordem: REGRA (padrões de descrição, confiança 1) → IA nas sobras (com confiança) →
HUMANO abaixo do limiar, com pendência. Só contas analíticas (ACEITA_LANCTO = S).
"""
