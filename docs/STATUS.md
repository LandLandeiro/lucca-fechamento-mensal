# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 17/10 ~09h45 (prova de outubro).

**Nível atual:** **Alvo** (todos os 6 CSVs gerados e validados); lançamentos por REGRA e IA verificada, sobras recusadas em HUMANO
**Próximo passo:** README (limitações) e pitch.

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
- [x] Leitores Aurora, Meridiano, plano de contas (com testes)
- [x] `lancamentos_classificados.csv` parte 1 (REGRA): 184 lançamentos, 177 por regra, 7 HUMANO + pendência (só EduAbroad)
- [x] `lancamentos_classificados.csv` parte 2 (IA nas sobras, D42): 7 sobras → 5 IA verificadas (aportes da EduAbroad), 2 por decisão humana (L28, L69 → 2.1.01.001 EduAbroad, D44)
- [x] Extra `sugestoes_regra.csv`: SUG-001 (alias "EDU ABROAD CONSULTORIA" → EduAbroad) **APROVADA**, vira regra a partir de 2026-10-01 (`classificacao_extratos.aliases_lojista`)

## Extra

- [x] `pendencias.csv` com motivo e quem decide: 11 pendências (checkout, remessa, notas, extratos)
- [x] Extra `contestacao_ponte.csv` (Q-L): 28 operações em 3 pendências CONTESTACAO_PONTE, pronto para a Helena mandar à Ponte
- [x] **Rastro de 100% dos números** (17/10 ~09h15, D45): o validador recusa número sem rastro ou com soma diferente, e linha do rastro de qualquer `id_saida` que não exista na fonte (id_transacao, Nº Operação + linha, L<n>, FITID + linha); auditoria independente com 0 violações (`docs/AUDITORIA.md`)
- [x] Auditoria independente da saída (`scripts/auditar_saida.py`, sem importar o pacote): formato sem violação; coerência com 1 achado (o −0,03 acima); matriz de conformidade Q-A…Q-M em `docs/CONFORMIDADE.md`
- [x] **Roda em outubro sem mudar código** (17/10, D48–D50): `tests/test_outubro.py` (12 testes, no CI) fecha um mês sintético gerado de setembro (`tests/fixtures/gerar_outubro.py`, datas +1 mês, EC novo, estorno da Bridge de venda de 05/09, TED de 300 mil em 01/10, PIX da EduAbroad). Resultado: exit 0, validador OK, auditoria 0 violações; competência 10/2026; Casa com taxa 0; EC novo vira pendência; estorno pela taxa antiga (2,59%); EduAbroad por REGRA (alias), 0 linhas para a IA; TED de 300 mil por REGRA; nenhuma pendência cita "setembro". Com `--pendencias-anteriores`, a L92 de setembro sai resolvida

## Regras (`regras.yaml`)

- 86 entradas: CONFIRMADO 44 · ASSUMO 30 · SEI 12 · PENDENTE 0 (`divergencias.data_referencia_vigencia` removida: coberta pela Q-B, D45). Novas: `classificacao.modelo_ia`, `classificacao.verificacao_ia`, `classificacao_extratos.aliases_lojista` e 2 `decisoes_humanas` (por linha, não são regras)
- **Q-K (22:33):** a conferência do repasse não prevê desconto (D38). **Q-L (22:34):** contestação com a Ponte por motivo (D39). **Q-M (22:34):** `orbe_recebivel` CONFIRMADO; saldo negativo do Aurora (conta garantida) e conciliação da Orbe por parcela ficam de fora
- **Q-H (21:13) corrigiu o ASSUMO de truncar (D09):** arredondamento comum (meio para longe do zero) por linha na comissão, nas divergências e nos 50% da remessa (D27). Q-I (21:14): contas das obrigações de agosto e despesas diretas CONFIRMADO. Q-J (21:45): nota de remessa pelo realizado + pendência da nossa metade do excesso
- HIPOTESES com os textos literais do financeiro (Q-A…Q-M → P01–P17), fonte `docs/FINANCEIRO_SLACK.md`

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
  - spreads negativos: 4, **−R$ 3.565,98** COBROU_A_MENOS ("trava vencida (2h); em contestação com a Ponte (Helena)"): Canguru −1.001,30, Novo Horizonte −637,91, Dublin −574,90, Ponte Aérea −1.351,87; `participacao_tarvo_no_spread` **−917,03** (informativa, D38)
  - nenhum alarme de ruído: os outros 13 lojistas ficam dentro de 0,005 p.p.

### Notas a emitir

- **21 notas**: 20 CHECKOUT, uma por lojista com comissão > 0, **R$ 207.045,23** (= 207.039,73 + 5,50 da Casa, que fica fora); 1 REMESSA, NF-75374179000146-REMESSA para a Ponte Câmbio S.A., **R$ 39.543,45** (pelo realizado, com o excesso da Mundo Aberto; Q-J)
- Competência 09/2026 lida dos dados (mês único da Orbe; "Competência: 09/2026" no relatório da Ponte)

### Pendências e validador

- **Pendências de checkout, remessa e notas: 7**
  - Atlas Idiomas (EC 1076801732): 57 transações, R$ 7.876,05 cobrados pela Orbe (informativo); quem decide: comercial
  - **NF_NEGATIVA, Casa do Estudante −5,50:** não emite nota; linha não nula TX88445133 (L433), estorno de venda de 2026-08-21; quem decide: Helena
  - **CONFERENCIA_REPASSE, R$ 39.543,45 (faturado):** conferir o TED da Ponte quando cair (previsto 06/10); total do relatório 78.073,59, que inclui 4 spreads negativos (−1.834,05) e a duplicata PC-0926-0162 (821,88), ambos em contestação; sem prever desconto (Q-K, D38); quem decide: Helena
  - **CONTESTACAO_PONTE (Q-L, D39), quem decide: Helena:** Mundo Aberto acima de 1,20%, 23 operações, **1.418,85**; spreads negativos, 4 operações, **−1.834,05** (Spread R$; −3.565,98 contra o contrato); duplicata PC-0926-0162 (R77), **821,88**. Lista por operação em `contestacao_ponte.csv`
  - **EXCESSO_REMESSA, Mundo Aberto R$ 709,46** (Σ por operação de round(50% × divergência), Q-H b, D45): a nota sai pelo realizado; a nossa metade sai no mês em que a Ponte devolver a diferença; quem decide: Helena
- **Validador: OK** (formato; rastro fecha por `id_saida`; cada linha da Orbe e do anexo exatamente uma vez em COM-/PEN-/EXC-; conservação do checkout com divergência recalculada da fonte e resíduo por linha ≤ 1 centavo onde as taxas são iguais; conservação da remessa; comissão de cada operação = metade do spread; notas = comissões; nenhuma nota ≤ 0; Σ `contestacao_ponte.csv` por pendência = valor da pendência)
- `ref_origem` no rastro = `id_transacao` (Orbe) ou `Nº Operação` (Ponte); a linha física vai na coluna extra `linha_arquivo`

### Lançamentos classificados (E6b parte 1: só REGRA)

- **AURORA: 84 linhas, 82 por regra, 2 HUMANO por decisão explícita (L28, L69 → 2.1.01.001, D44).** Σ −2.532.423,41 = saldo final − saldo anterior ✓. Regras: repasse_lojista 42 (inclui a Atlas, D35), orbe_recebivel 21, transferencia_meridiano 4, tarifa 2 e 1 cada (folha, ISS, INSS, FGTS, IRRF, PIS, COFINS, condomínio, cloud, assinatura, contabilidade, PIX sem identificação, devolução)
- **MERIDIANO: 100 linhas, 95 por regra, 5 por IA verificada, 0 HUMANO.** Sem saldo inicial no OFX (inicial implícito 204.118,03, D34). Regras: aporte_lojista 59, liquidacao_ponte 21, mesma_titularidade 3, aplicação 3, resgate 3, tarifa 2, repasse_comissao_ponte 1, seguro 1, IOF 1, rendimento_aplicacao 1 (H37)
- **Sem regra (7, só EduAbroad) → IA (D42), resposta real em `cache_ia/` (7 chamadas a `claude-haiku-5-5`, 18.118 tokens de entrada + 2.379 de saída, ~US$ 0,003; reexecução: 0 chamadas, hashes iguais):**
  - PIX RECEB EDU ABROAD (MRD…0036, 0180, 0340, 0484, 0636) → 2.1.02.001 EduAbroad, confiança 0,85–0,88; prova: Σ PIX RECEB 394.222,69 = Σ (Valor R$ + IOF) das operações da Ponte 394.222,69 → **IA**
  - PIX ENVIADO EDU ABROAD (L28 −14.147,48; L69 −47.889,99) → a IA sugeriu 2.1.01.001 **sem lojista** ("CONSULTORIA LTD" não bate com o cadastro; pode ser fornecedor), confiança 0,5 e 0,4 → (b) e (d) falham → o código barrou → **decisão do Lucca** (D44): 2.1.01.001 EduAbroad, metodo HUMANO, confiança vazia, com a evidência da soma e das vendas na Orbe
- **Transferências:** L12 → MRD2026090107, L44 → MRD2026090274, L58 → MRD2026090454 (mesmo dia); **L92 (−300.000,00) sem par → pendência em trânsito (cai em 01/10)**
- **Aportes × Ponte:** 14 lojistas; Ponte Aérea com +18.240,00 = PIX MRD2026090425 sem operação → pendência; EduAbroad conferida: aportes pela IA verificada = operações (394.222,69); Bagagem fecha (duplicata conta uma vez)
- **Aplicação × resgate (FIFO):** resgate MRD2026090254 (09/09, 162.128,00) excede em **392,00** a aplicação de 05/09 → saldo aplicado anterior a 01/09, linha inteira em 1.1.02.001, sem pendência (D36); os outros dois resgates cabem no saldo aplicado
- **Pendências dos extratos: 4** ( PIX sem identificação 7.350,00, devolução Mundo Aberto 12.400,00, transferência em trânsito −300.000,00, aporte sem operação 18.240,00). **Total no `pendencias.csv`: 11** (+ Atlas sem contrato, nota negativa da Casa, conferência do TED, excesso da Mundo Aberto, 3 contestações com a Ponte). Saldo negativo do Aurora: conta garantida, não é pendência (Q-M)

