# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 16/10 ~22h15 (E4).

**Nível atual:** **Mínimo — conferido** + comissão REMESSA + divergências CHECKOUT e REMESSA (parte do Alvo)
**Próximo passo:** Lucca decide a D21 (valor da divergência do spread negativo) e confirma D17 e D20; confere uma amostra das divergências. Depois, E6: notas a emitir + leitores dos extratos.

## Mínimo

- [x] Leitor Orbe (com testes)
- [x] Leitor taxas + cadastro EC→CNPJ (com testes)
- [x] `comissoes_por_lojista.csv` — CHECKOUT
- [x] `rastro.csv` das comissões CHECKOUT (1943/1943 linhas da Orbe, cada uma exatamente uma vez: COM-… ou PEN-…)
- [x] Validador (soma do rastro = total; formato; cobertura das linhas da Orbe); falha = código 1
- [x] **Conferência do mínimo:** um script independente do Lucca (outra sessão de IA, sem ver este código) recalculou do zero e bateu os 21 lojistas no centavo: total 207.031,31, 57 transações em pendência, 1.943 linhas. Também bate com a exploração (ver Números)
- [x] Saída em ordem determinística: linha de negócio, comissão decrescente, CNPJ; rastro por `id_saida` e linha

## Alvo

- [x] Leitor e-mail Ponte + anexo (stdlib `email`; aba e colunas pelo cabeçalho; totais conferidos com o declarado)
- [x] Comissão REMESSA (E4): 228 operações elegíveis, R$ 39.542,89
- [x] `divergencias_taxa.csv`, parte **CHECKOUT** (E5a): 200 divergências, líquidas com os estornos (D10); conservação validada
- [x] `divergencias_taxa.csv`, parte **REMESSA** (E4): 27 divergências (23 Mundo Aberto + 4 spreads negativos)
- [ ] Amostra de divergências conferida pelo Lucca
- [ ] `notas_a_emitir.csv`
- [ ] Leitores Aurora, Meridiano, plano de contas
- [ ] `lancamentos_classificados.csv` (REGRA → IA → HUMANO)

## Extra

- [ ] `pendencias.csv` completo (motivo + quem decide); hoje só a do checkout (Atlas)
- [ ] Rastro de 100% dos números
- [ ] Roda em outubro sem mudar código: arquivos achados por prefixo, competência lida do relatório da Ponte, vigências e regras lidas do `regras.yaml`; falta testar com um arquivo de outro mês

## Regras (`regras.yaml`)

- 44 regras: CONFIRMADO 20 · SEI 11 · ASSUMO 11 · PENDENTE 2 (`divergencias.data_referencia_vigencia`, sem uso; `contabil.padroes_de_descricao`, preenchido na E6)
- **A confirmar pelo Lucca:** D17 (reversão líquida com a antecipação), D20 (arredondamento da divergência de remessa), **D21 (valor da divergência do spread negativo)**
- HIPOTESES com os textos literais do financeiro (Q-A…Q-G → P01–P11), fonte `docs/FINANCEIRO_SLACK.md`

## Números atuais (saída de `python -m tarvo --dados data --saida saida`)

### Comissão

- **CHECKOUT: R$ 207.031,31**, em 21 lojistas e 1.886 transações
- **REMESSA: R$ 39.542,89**, em 14 lojistas e 228 operações elegíveis (50% × Spread R$, ROUND_HALF_EVEN por operação, D19)
  - comparação: 50% do total de cada lojista arredondado uma vez = 39.542,87 (R$ 0,02 em 7 lojistas); 50% exato de 79.085,76 = 39.542,88

### Remessa: destino das 233 linhas do anexo

- 228 elegíveis (spread 79.085,76), incluindo as 16 "APROVADO C/ RESSALVA" e as 6 liquidadas em 01/10
- 1 duplicata excluída: PC-0926-0162 R77 "reprocessada" (spread 821,88); a R76 conta
- 4 spreads negativos excluídos (−1.834,05): PC-0926-0210, -0326, -0491, -0545 → divergências
- 0 fora de competência, 0 pendências
- **Conservação:** Σ Spread R$ do anexo 78.073,59 (= declarado na R241) = 79.085,76 + 821,88 − 1.834,05 + 0 ✓

### Divergências

- **CHECKOUT: 200, R$ 16.973,00**, todas COBROU_A_MAIS; decisão: Helena

  | Lojista | Divergências | R$ |
  |---|---:|---:|
  | Casa do Estudante (tarifa zerada; tudo o que a Orbe cobrou em setembro) | 116 | 15.396,77 |
  | Rota Global (+0,50 p.p. desde 12/09) | 79 | 1.546,28 |
  | Escola Bridge de Idiomas (2,59% em vez de 2,19% de 15 a 18/09) | 5 | 29,95 |

  Mais 5 vendas divergentes estornadas por inteiro no mês (4 da Rota, 1 da Casa): líquido 0, não listadas (D10)
- **REMESSA: 27, total −R$ 2.147,11**
  - **Mundo Aberto: 23, R$ 1.418,88** COBROU_A_MAIS (1,5% aplicado × 1,2% contratado; pela coluna "Spread %" arredondada: 1.418,85, D22)
  - spreads negativos: 4, −R$ 3.565,99 COBROU_A_MENOS ("trava vencida (2h), Helena contesta"): Canguru −1.001,30, Novo Horizonte −637,91, Dublin −574,91, Ponte Aérea −1.351,87. **Valor pela fórmula do valor cheio (D21, a confirmar);** pelo próprio spread seria −1.834,05
  - nenhum alarme de ruído: os outros 13 lojistas ficam dentro de 0,005 p.p.
- **Conservação do checkout:** Σ `valor_taxa` Orbe das linhas não pendentes 224.004,31 = Σ comissão 207.031,31 + Σ divergências 16.973,00 ✓

### Pendências e validador

- **Pendências: 1**, a Atlas Idiomas (EC 1076801732): 57 transações, R$ 7.876,05 cobrados pela Orbe (informativo); quem decide: comercial
- **Validador: OK** (formato; rastro fecha por `id_saida`; cada linha da Orbe e do anexo exatamente uma vez em COM-/PEN-/EXC-; conservação do checkout e da remessa; comissão de cada operação = metade do spread; nenhuma divergência apontando linha pendente)
- Conferência independente do checkout (exploração): 231.880,36 − Atlas 7.876,05 − Casa cobrado 15.391,27 + Casa contratado −5,50 − divergências 1.576,23 = **207.031,31** ✓
- **Casa do Estudante = −5,50 no checkout (decidido):** estorno TX88445133 de venda de 21/08, fora da condição especial; na E6 vira pendência para a Helena (negativo não emite nota). Na remessa a Casa segue normal (R$ 3.075,86; D24)
- `ref_origem` no rastro = `id_transacao` (Orbe) ou `Nº Operação` (Ponte); a linha física vai na coluna extra `linha_arquivo`
