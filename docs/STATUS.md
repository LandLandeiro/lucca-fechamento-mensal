# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 16/10 ~22h55 (respostas Q-H/Q-I/Q-J: arredondamento comum).

**Nível atual:** **Mínimo — conferido** + comissão REMESSA + divergências + notas a emitir (Alvo, falta só a classificação dos extratos)
**Próximo passo:** E6b: leitores do Aurora, do Meridiano e do plano de contas + `lancamentos_classificados.csv` (REGRA → IA → HUMANO).

## Mínimo

- [x] Leitor Orbe (com testes)
- [x] Leitor taxas + cadastro EC→CNPJ (com testes)
- [x] `comissoes_por_lojista.csv` — CHECKOUT
- [x] `rastro.csv` das comissões CHECKOUT (1943/1943 linhas da Orbe, cada uma exatamente uma vez: COM-… ou PEN-…)
- [x] Validador (soma do rastro = total; formato; cobertura das linhas da Orbe); falha = código 1
- [x] **Conferência do mínimo:** um script independente do Lucca (outra sessão de IA, sem ver este código) recalculou do zero e bateu os 21 lojistas no centavo: 207.031,31 com truncamento; refeita depois da Q-H (arredondamento comum): 207.039,73, de novo no centavo, com 57 transações em pendência e 1.943 linhas
- [x] Saída em ordem determinística: linha de negócio, comissão decrescente, CNPJ; rastro por `id_saida` e linha

## Alvo

- [x] Leitor e-mail Ponte + anexo (stdlib `email`; aba e colunas pelo cabeçalho; totais conferidos com o declarado)
- [x] Comissão REMESSA (E4): 228 operações elegíveis, R$ 39.543,45
- [x] `divergencias_taxa.csv`, parte **CHECKOUT** (E5a): 200 divergências, líquidas com os estornos (D10); conservação com resíduo de truncamento validada
- [x] `divergencias_taxa.csv`, parte **REMESSA** (E4): 27 divergências (23 Mundo Aberto + 4 spreads negativos)
- [ ] Amostra de divergências conferida pelo Lucca
- [x] `notas_a_emitir.csv` (E6a): 20 notas CHECKOUT (R$ 207.045,23) + 1 nota REMESSA para a Ponte (R$ 39.543,45)
- [ ] Leitores Aurora, Meridiano, plano de contas
- [ ] `lancamentos_classificados.csv` (REGRA → IA → HUMANO)

## Extra

- [ ] `pendencias.csv` completo (motivo + quem decide); hoje: Atlas, nota negativa da Casa, conferência do repasse, metade do excesso da Mundo Aberto (faltam as dos extratos)
- [ ] Rastro de 100% dos números
- [ ] Roda em outubro sem mudar código: arquivos achados por prefixo, competência lida do relatório da Ponte, vigências e regras lidas do `regras.yaml`; falta testar com um arquivo de outro mês

## Regras (`regras.yaml`)

- 50 regras: CONFIRMADO 26 · SEI 11 · ASSUMO 11 · PENDENTE 2 (`divergencias.data_referencia_vigencia`, sem uso; `contabil.padroes_de_descricao`, preenchido na E6b)
- **Q-H (21:13) corrigiu o ASSUMO de truncar (D09):** arredondamento comum (meio para longe do zero) por linha na comissão, nas divergências e nos 50% da remessa (D27). Q-I (21:14): contas das obrigações de agosto e despesas diretas CONFIRMADO. Q-J (21:45): nota de remessa pelo realizado + pendência da nossa metade do excesso
- HIPOTESES com os textos literais do financeiro (Q-A…Q-J → P01–P14), fonte `docs/FINANCEIRO_SLACK.md`

## Números atuais (saída de `python -m tarvo --dados data --saida saida`)

Todos conferidos no centavo contra a previsão independente do Lucca antes do commit.

### Comissão

- **CHECKOUT: R$ 207.039,73**, em 21 lojistas e 1.886 transações (Bridge 11.916,02; Casa −5,50)
- **REMESSA: R$ 39.543,45**, em 14 lojistas e 228 operações elegíveis (round(50% × Spread R$) por operação, Q-H d)
  - comparação: 50% do total de cada lojista arredondado uma vez = 39.542,92 (R$ 0,53 em 12 lojistas)

### Remessa: destino das 233 linhas do anexo

- 228 elegíveis (spread 79.085,76), incluindo as 16 "APROVADO C/ RESSALVA" e as 6 liquidadas em 01/10
- 1 duplicata excluída: PC-0926-0162 R77 "reprocessada" (spread 821,88); a R76 conta
- 4 spreads negativos excluídos (−1.834,05): PC-0926-0210, -0326, -0491, -0545 → divergências
- 0 fora de competência, 0 pendências
- **Conservação:** Σ Spread R$ do anexo 78.073,59 (= declarado na R241) = 79.085,76 + 821,88 − 1.834,05 + 0 ✓

### Divergências

- **CHECKOUT: 200, R$ 16.973,65**, todas COBROU_A_MAIS; decisão: Helena (round(bruto × (aplicada − contratada)), só onde as taxas diferem; Q-H c)

  | Lojista | Divergências | R$ |
  |---|---:|---:|
  | Casa do Estudante (tarifa zerada; tudo o que a Orbe cobrou em setembro) | 116 | 15.397,42 |
  | Rota Global (+0,50 p.p. desde 12/09) | 79 | 1.546,28 |
  | Escola Bridge de Idiomas (2,59% em vez de 2,19% de 15 a 18/09) | 5 | 29,95 |

  Mais 5 vendas divergentes estornadas por inteiro no mês (4 da Rota, 1 da Casa): líquido 0, não listadas (D10)
- **Conservação do checkout:** Σ `valor_taxa` Orbe 224.004,31 = Σ comissão 207.039,73 + Σ divergências 16.973,65 + **resíduo de truncamento −9,07** (969 linhas com 1 centavo; nenhuma linha acima do limite da D29) ✓
- **REMESSA: 27, total −R$ 2.147,13** (D28: round((Spread % do relatório − contratado) × PTAX × ME))
  - **Mundo Aberto: 23, R$ 1.418,85** COBROU_A_MAIS (1,5% aplicado × 1,2% contratado)
  - spreads negativos: 4, **−R$ 3.565,98** COBROU_A_MENOS ("trava vencida (2h); Helena contesta o desconto no repasse"): Canguru −1.001,30, Novo Horizonte −637,91, Dublin −574,90, Ponte Aérea −1.351,87; `impacto_repasse_tarvo` **−917,03**
  - nenhum alarme de ruído: os outros 13 lojistas ficam dentro de 0,005 p.p.

### Notas a emitir

- **21 notas**: 20 CHECKOUT, uma por lojista com comissão > 0, **R$ 207.045,23** (= 207.039,73 + 5,50 da Casa, que fica fora); 1 REMESSA, NF-75374179000146-REMESSA para a Ponte Câmbio S.A., **R$ 39.543,45** (pelo realizado, com o excesso da Mundo Aberto; Q-J)
- Competência 09/2026 lida dos dados (mês único da Orbe; "Competência: 09/2026" no relatório da Ponte)

### Pendências e validador

- **Pendências: 4**
  - Atlas Idiomas (EC 1076801732): 57 transações, R$ 7.876,05 cobrados pela Orbe (informativo); quem decide: comercial
  - **NF_NEGATIVA, Casa do Estudante −5,50:** não emite nota; linha não nula TX88445133 (L433), estorno de venda de 2026-08-21; quem decide: Helena
  - **CONFERENCIA_REPASSE, R$ 506,65:** TED da Ponte previsto para 06/10; pelo total do relatório (78.073,59) o repasse seria 39.036,80; faturamos 39.543,45; diferença 506,65 = 917,03 (negativos, contestar) − 410,94 (duplicata PC-0926-0162, avisar) + 0,56 (arredondamento por operação contra 50% do total da Ponte); quem decide: Helena
  - **EXCESSO_REMESSA, Mundo Aberto R$ 709,43** (round(50% × 1.418,85)): a nota sai pelo realizado; a nossa metade sai no mês em que a Ponte devolver a diferença; quem decide: Helena
- **Validador: OK** (formato; rastro fecha por `id_saida`; cada linha da Orbe e do anexo exatamente uma vez em COM-/PEN-/EXC-; conservação do checkout com divergência recalculada da fonte e resíduo por linha ≤ 1 centavo onde as taxas são iguais; conservação da remessa; comissão de cada operação = metade do spread; notas = comissões; nenhuma nota ≤ 0)
- `ref_origem` no rastro = `id_transacao` (Orbe) ou `Nº Operação` (Ponte); a linha física vai na coluna extra `linha_arquivo`
