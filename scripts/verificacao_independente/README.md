# Verificação independente (outra sessão de IA)

Estes scripts foram escritos e rodados **fora deste repositório**, numa sessão separada de IA (o Claude no app, usado para planejar e conferir), **sem importar nada de `src/tarvo`**. Cada um recalcula os números do zero a partir de `data/` e foi comparado com a saída do Claude Code antes de cada commit importante.

Estão aqui **como rodaram**, sem edição: os caminhos absolutos são do ambiente onde foram executados (`/mnt/user-data/outputs/tarvo-fechamento/data`), e `remessa.py` lê o anexo do e-mail da Ponte extraído para `ponte.xlsx`.

| Script | Quando | O que conferiu | Resultado |
|---|---|---|---|
| `checkout_truncado_v1.py` | 16/10 ~21h25 | Comissão de checkout por lojista (regra da época: truncar) | 207.031,31, 21 lojistas, 57 linhas da Atlas em pendência: bateu no centavo |
| `divergencias_v1.py` | 16/10 ~21h40 | Divergências de checkout, líquidas com o estorno da própria venda | 200 · 16.973,00: bateu |
| `remessa.py` | 16/10 ~21h55 | Comissão de remessa (50% do Spread R$), negativos, duplicata, Mundo Aberto | 39.542,89 (half-even) → 39.543,45 (half-up), 14 lojistas: bateu |
| `checkout_arredondado.py` | 16/10 ~22h10 | Tudo de novo após a Helena trocar truncar por arredondar (Q-H) | 207.039,73; 200 · 16.973,65; resíduo −9,07: previsão feita ANTES do código, bateu nos 9 números |

Também conferimos, fora do código, a prova da EduAbroad (Σ PIX recebidos 394.222,69 = Σ Valor R$ + IOF das 16 operações na Ponte) antes de a IA rodar.

Limite honesto: estes scripts conferiram comissões, divergências, remessa e notas. Lançamentos e pendências foram conferidos pelo validador, pela auditoria e pela avaliação simulada (`docs/AVALIACAO_SIMULADA.md`).
