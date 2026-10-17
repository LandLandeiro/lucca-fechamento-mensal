# Auditoria antes do Checkpoint 1

> **Atualização 17/10 11:53 (correções da avaliação simulada, D52–D62):** `scripts/auditar_saida.py` na saída nova: **0 violações**. Comissões, divergências, notas, lançamentos (valores) e contestação não mudaram. Mudou: 14 pendências (+3 DIVERGENCIA_CHECKOUT, D53), `ref_origem` das pendências só com ids (D55), e os 7 lançamentos da EduAbroad passaram a REGRA (D52). Na tabela 4b abaixo, as linhas 8 (IA, 5 lançamentos, 394.222,69) e 9 (decisões humanas, 2, 62.037,47) agora estão dentro das linhas 2 (`meridiano.aporte_lojista`, 64 lançamentos) e 3 (`aurora.repasse_lojista`, 44): 147 lançamentos por regra ASSUMO, 37 por regra CONFIRMADO, 0 por IA, 0 por decisão humana.

## Resultado final, depois das decisões do Lucca (17/10 ~09h15, D45)

| # | Item | Resultado |
|---|---|---|
| 1 | Matriz de conformidade (Q-A…Q-M) | ✅ 13 de 13 (`docs/CONFORMIDADE.md`) |
| 2 | Formato contra `docs/case.md` | ✅ nenhuma violação; nenhum `;` dentro de campo em nenhum CSV (antes: 1.153 campos, 10 deles no `motivo` de `pendencias.csv`) |
| 3 | Coerência entre arquivos | ✅ 4.984 de 4.984 linhas do rastro existem na fonte |
| 4 | Regras ASSUMO por R$ | listadas no item 4 abaixo (o item 7 da tabela 4a saiu: virou por operação) |
| 5 | "Rastro de 100% dos números" | ✅ **marcado no STATUS**: o validador agora confere a origem de toda linha do rastro |

`scripts/auditar_saida.py` na saída nova: **0 violações, 0 avisos.** O que mudou:

| Decisão | O que foi feito | Teste |
|---|---|---|
| 1. Metade do excesso por operação | `PEN-EXCESSO_REMESSA-17217888000111` = Σ round(50% × divergência) das 23 operações = **709,46** (era 709,43); a linha `arredondamento` de −0,03 saiu do rastro | `test_pendencia_metade_do_excesso_da_mundo_aberto` |
| 2. Nenhum `;` dentro de campo | o escritor troca `;` por `,` em todo texto (quoting padrão do `csv` mantido); o validador recusa `;` dentro de campo em qualquer CSV da pasta | `test_nenhum_ponto_e_virgula_dentro_de_campo`, `test_validador_recusa_ponto_e_virgula_em_campo` |
| 3. `divergencias.data_referencia_vigencia` | removida do `regras.yaml`: coberta pela Q-B (`checkout.estorno`, taxa da data da venda original). Regras: 0 PENDENTE | `test_oxford_estorno_de_venda_de_agosto` (comportamento) |
| 4. Origem de toda linha do rastro | o validador recebe todas as fontes (id_transacao da Orbe, Nº Operação + linha do anexo da Ponte, L<n> do Aurora, FITID + linha do Meridiano) e recusa qualquer linha do rastro, de qualquer `id_saida`, que não exista nelas | `test_validador_recusa_rastro_sem_linha_de_origem` |
| 4. Saldo negativo do Aurora (Q-M) | teste prova que o saldo corrido fica negativo em setembro e que nenhuma pendência trata disso | `test_saldo_negativo_do_aurora_nao_vira_pendencia` |

Números que não mudaram: comissões (207.039,73 e 39.543,45), divergências, notas, lançamentos e as outras 10 pendências; só a EXCESSO_REMESSA (+0,03) e textos (`;` → `,`).

---

## Auditoria inicial (17/10 ~09h, antes das decisões)

> 17/10 ~09h, sobre a saída do commit `b651260` (`python -m tarvo --dados data --saida saida`). Só leitura do cálculo: nenhum número da saída mudou. Reproduzir: `.\.venv\Scripts\python.exe scripts\auditar_saida.py` (lê só `saida/` e `data/`, sem importar o pacote `tarvo`; sai com 1 se houver violação).
> Antes de confiar no script, ele foi testado contra uma cópia estragada da saída (BOM, CRLF, vírgula decimal, data DD/MM/AAAA, CNPJ com DV errado, confiança 1,50, rastro que não fecha): **as 7 mutações foram acusadas** (12 violações). Na saída real: **1 violação** (item 3, C5).

## Resumo

| # | Item | Resultado |
|---|---|---|
| 1 | Matriz de conformidade (Q-A…Q-M) | ❌ 9 ✅, 3 ⚠️, 1 ❌ (Q-H, R$ 0,03): ver `docs/CONFORMIDADE.md` |
| 2 | Formato contra `docs/case.md` | ✅ nenhuma violação; ⚠️ 1 risco (`;` dentro do `motivo` de `pendencias.csv`, entre aspas) |
| 3 | Coerência entre arquivos | ❌ 1 linha do rastro sem origem física (−0,03, PEN-EXCESSO_REMESSA); o resto ✅ |
| 4 | Regras ASSUMO por R$ de impacto | ✅ listadas abaixo |
| 5 | "Rastro de 100% dos números" no STATUS | ❌ não marcado: o validador garante soma e cobertura, mas não a origem de toda linha do rastro (abaixo) |

## 1. Conformidade com as respostas do financeiro

Matriz completa, uma linha por trecho literal: `docs/CONFORMIDADE.md`. Achados:

- ❌ **Q-H × Q-J, R$ 0,03.** A pendência `PEN-EXCESSO_REMESSA-17217888000111` vale round(50% × 1.418,85) = **709,43**. A Q-H manda "linha por linha, e depois soma" e "por operação, com o mesmo arredondamento": Σ round(50% × divergência de cada operação) = **709,46**. A diferença vai para o rastro como uma linha `arredondamento` de −0,03 sem linha de origem. Não alterei (é cálculo).
- ⚠️ **Q-B.** `divergencias.data_referencia_vigencia` está PENDENTE (`valor: null`) e nenhum código a lê; a Q-B já respondeu ("a taxa usada é a que valia na data da venda original") e o cálculo usa `checkout.estorno` (CONFIRMADO). Sem efeito na saída.
- ⚠️ **Q-M.** `extratos.saldo_negativo_aurora` e `extratos.conciliacao_orbe_por_parcela` são regras de escopo, sem código e sem teste. A saída está coerente (nenhuma pendência de saldo negativo), mas nada impede uma regressão.
- Nenhuma resposta ficou sem regra. Q-K conferida no texto: "descont" aparece 0 vezes em `saida/`.

## 2. Formato, arquivo por arquivo

| Checagem | comissoes | divergencias | notas | lancamentos | pendencias | rastro | extras (contestacao, sugestoes) |
|---|---|---|---|---|---|---|---|
| Colunas obrigatórias na ordem exata | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| `;` e mesmo nº de campos em toda linha | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ponto decimal, sem milhar (dinheiro `0.00`; `_pct` com ponto) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Datas `AAAA-MM-DD` | n/a | ✅ | n/a | ✅ | n/a | n/a | ✅ |
| CNPJ 14 dígitos com DV válido, nunca vazio | ✅ | ✅ | ✅ (`tomador_cnpj`) | n/a | n/a | n/a | ✅ |
| `linha_negocio` ∈ {CHECKOUT, REMESSA} | ✅ | ✅ | ✅ | n/a | n/a | n/a | n/a |
| `metodo` ∈ {REGRA, IA, HUMANO}; `banco` ∈ {AURORA, MERIDIANO} | n/a | n/a | n/a | ✅ | n/a | n/a | ✅ |
| `confianca` 0–1 em REGRA/IA, vazia em HUMANO | n/a | n/a | n/a | ✅ (177 × 1.00; 5 IA 0.85–0.88; 2 HUMANO vazias) | n/a | n/a | n/a |
| UTF-8 sem BOM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fim de linha só LF | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Violações: nenhuma.**

⚠️ **Risco (não é violação):** campos de texto com `;` saem entre aspas, como manda o padrão de CSV (RFC 4180), e qualquer leitor de CSV (pandas, `csv`, Excel) os lê certo. Mas um corretor que divida a linha por `;` desalinha as colunas. Onde acontece:

| Arquivo | Coluna | Linhas | Efeito num `split(";")` |
|---|---|---|---|
| `pendencias.csv` | `motivo` (**obrigatória**) | 10 de 11 | desloca `quem_decide` |
| `divergencias_taxa.csv` | `motivo` (extra) | 227 de 227 | só depois das 7 obrigatórias |
| `rastro.csv` | `nota` (extra) | 908 de 4.985 | só depois das 4 obrigatórias |
| `lancamentos_classificados.csv` | `justificativa_ia` (extra) | 4 de 184 | só depois das 9 obrigatórias |
| `contestacao_ponte.csv` | `observacao` (extra) | 4 de 28 | arquivo extra |

Correção possível (para o Lucca decidir; muda o texto da saída): trocar `;` por `,` nos textos livres no escritor. Não apliquei, porque o arquivo está correto pelo padrão e a troca altera textos já revisados.

## 3. Coerência entre arquivos

| Checagem | Resultado |
|---|---|
| Σ notas = Σ comissões positivas | ✅ CHECKOUT 207.045,23 = 207.045,23 (20 notas, uma por comissão > 0, cada nota = a comissão do lojista); REMESSA 39.543,45 = 39.543,45 (1 nota, 14 comissões). Sem nota: Casa −5,50 (pendência NF_NEGATIVA) |
| Toda divergência aponta transação ou operação existente | ✅ 227 de 227: 200 `id_transacao` do relatório da Orbe, 27 `Nº Operação` do anexo da Ponte (lido direto do `.eml`) |
| Toda pendência com tipo, ref_origem, motivo e quem_decide | ✅ 11 de 11 (e todas com `valor_brl`) |
| Todo `id_saida` no rastro e a soma fecha | ✅ 478 números (comissões, divergências, notas, lançamentos, pendências): todos com rastro e Σ = número, no centavo; nenhum id do rastro sem número de saída (exceto as 2 exclusões anotadas `EXC-`, que não têm número por desenho). Extras: Σ de `contestacao_ponte.csv` por pendência = valor da pendência; `valor_total` de `sugestoes_regra.csv` = Σ dos lançamentos citados |
| Toda linha do rastro existe na fonte (ref + linha física) | ❌ 4.984 de 4.985. A exceção: `PEN-EXCESSO_REMESSA-17217888000111`, ref `arredondamento`, linha 0, −0,03 (o mesmo achado do item 1) |
| Conta de todo lançamento é ANALITICA com ACEITA_LANCTO=S | ✅ 184 de 184 (plano lido direto do `04_plano`) |

## 4. Regras ASSUMO que afetam a saída, por R$ de impacto

São os pontos onde o gabarito pode discordar de nós. Medidos com o próprio código, trocando só a regra em questão (cenário alternativo entre parênteses). Duas naturezas diferentes, por isso duas tabelas.

**4a. ASSUMO que mudam um valor reportado**

| # | Regra | Onde | Impacto em R$ | Alternativa que o gabarito pode usar |
|---|---|---|---|---|
| 1 | `classificacao_extratos.conferencias` (D33, D36) | pendências | **318.632,00** em pendências que dependem do critério: transferência em trânsito −300.000,00 (L92) + aporte sem operação 18.240,00 (MRD2026090425); e 392,00 que **não** viraram pendência (resgate acima do aplicado, D36) | sem casar transferência em 1 dia útil; resgate como pendência |
| 2 | `remessa.divergencia_spread_negativo` (D21) | `divergencias_taxa.csv` | **1.731,93**: os 4 negativos valem −3.565,98 contra o contrato | só o Spread R$ do relatório (−1.834,05) |
| 3 | `remessa.valor_contestado` (D39) | `pendencias.csv` (CONTESTACAO_PONTE negativos) | **1.731,93**: −1.834,05 pelo Spread R$ | a divergência contra o contrato (−3.565,98) |
| 4 | `divergencias.estorno_de_venda_divergente` (D10) | `divergencias_taxa.csv` | **107,53** (bruto): 5 vendas divergentes estornadas no mês, líquido 0, não listadas (4 Rota, 1 Casa); o total não muda | listar venda (+107,53) e estorno (−107,53) |
| 5 | `ponte.tolerancia_spread_pct` (H07) | `divergencias_taxa.csv` | **24,58** (Σ\|·\|; Σ 1,46): 193 divergências de ruído de 4ª casa, a maior de 0,74, não listadas | tolerância zero |
| 6 | `remessa.formula_divergencia` (D28) | `divergencias_taxa.csv` | **0,03**: Mundo Aberto 1.418,85 | pelo Spread R$ (D22): 1.418,88; negativos iguais |
| 7 | arredondamento da metade em `remessa.excesso_cobrado_na_remessa` (regra CONFIRMADO, detalhe nosso) | `pendencias.csv` | **0,03**: 709,43 | por operação (Q-H): 709,46 |
| 8 | `divergencias.reversao_liquida_com_antecipacao` (D17) | `divergencias_taxa.csv` | **0,00** em setembro: nenhuma antecipação divergente teve reversão no mês | — |
| 9 | `classificacao_extratos.aliases_lojista` (D44) | — | **0,00** em setembro: vigência a partir de 01/10 | — |
| 10 | `notas.discriminacao`, `remessa.motivo_spread_negativo` | textos | **0,00** (só redação) | — |

**4b. ASSUMO que decidem a conta de um lançamento** (o valor do lançamento vem do banco; o que pode discordar é a conta). R$ = Σ |valor| dos lançamentos classificados pela regra.

| # | Regra | Lançamentos | R$ classificado | Conta |
|---|---|---|---|---|
| 1 | `meridiano.liquidacao_ponte` | 21 | 5.611.447,12 | 2.1.02.001 |
| 2 | `meridiano.aporte_lojista` | 59 | 5.235.464,43 | 2.1.02.001 |
| 3 | `aurora.repasse_lojista` (inclui a Atlas pela `lojistas_do_extrato`, D35: 249.301,77) | 42 | 4.168.230,14 | 2.1.01.001 |
| 4 | `aurora.transferencia_meridiano` | 4 | 1.450.000,00 | 1.1.09.001 |
| 5 | `meridiano.mesma_titularidade` | 3 | 1.150.000,00 | 1.1.09.001 |
| 6 | `meridiano.aplicacao_automatica` | 3 | 588.124,00 | 1.1.02.001 |
| 7 | `meridiano.resgate_automatico` | 3 | 472.881,00 | 1.1.02.001 |
| 8 | `classificacao.uso_ia`, `limiar_confianca_ia` (0,8), `verificacao_ia`, `modelo_ia`, `vinculo_bancario_por_ia` | 5 | 394.222,69 | 2.1.02.001 (confianças 0,85 e 0,88: com limiar 0,9, viram HUMANO) |
| 9 | `decisoes_humanas.aurora_L69_2026_09` e `aurora_L28_2026_09` | 2 | 62.037,47 | 2.1.01.001 |
| 10 | `aurora.devolucao_pix_lojista` | 1 | 12.400,00 | 2.1.01.001 |
| 11 | `aurora.pix_sem_identificacao` | 1 | 7.350,00 | 1.1.09.002 |
| 12 | `meridiano.rendimento_aplicacao` | 1 | 3.912,66 | 3.2.01 |
| 13 | `meridiano.seguro` | 1 | 1.830,44 | 4.2.05 |
| 14 | `meridiano.iof` | 1 | 48,21 | 4.3.01 |

No total: 140 lançamentos por regra ASSUMO, 37 por regra CONFIRMADO, 5 por IA verificada e 2 por decisão humana.

## 5. "Rastro de 100% dos números" (STATUS)

**Não marquei.** O validador (`src/tarvo/saida/validador.py`) garante:

- os 478 números das cinco tabelas com valor têm rastro, e a soma por `id_saida` é igual ao número (validador e auditoria concordam);
- todo id do rastro existe numa saída (fora as exclusões `EXC-`);
- cada linha de origem aparece exatamente uma vez: 1.943 da Orbe e 233 da Ponte em `COM-`/`PEN-`/`EXC-`, 184 dos extratos em `LAN-`. Essas linhas existem na fonte, e a conservação do checkout e da remessa fecha.

O que falta para marcar:

1. **Uma linha do rastro não aponta para linha de origem:** o `arredondamento` de −0,03 da `PEN-EXCESSO_REMESSA` (item 1). Some se a metade for somada por operação.
2. **O validador não confere a origem das linhas dos ids derivados:** `NF-`, `DIV-` da remessa e as pendências derivadas (NF_NEGATIVA, CONFERENCIA_REPASSE, EXCESSO_REMESSA, APORTE_, CONTESTACAO_PONTE). Ele confere que a soma fecha, mas não que cada (ref, linha) existe no arquivo. Hoje existem todas (C5 da auditoria), menos a do item 1. A garantia vem do script de auditoria, não do validador. A correção seria levar a checagem C5 para o validador (código; não alterei).
3. **O `valor_total` de `sugestoes_regra.csv` não tem rastro no `rastro.csv`.** É arquivo extra; a auditoria confere o total contra os lançamentos citados.

## Correções feitas (documentação; nenhum número mudou)

| Arquivo | Correção |
|---|---|
| `HIPOTESES.md` H30 | Descrevia a conferência do repasse antiga (diferença de 506,65 decomposta em desconto e duplicata), substituída pela Q-K. Marcada como substituída pela H40 (D38) |
| `HIPOTESES.md` H07 | Impacto "~200 alarmes falsos (R$ 1,67)" era de antes da D28. Medido de novo: 193 divergências de ruído, Σ\|·\| 24,58 (Σ 1,46), a maior de 0,74 |
| `HIPOTESES.md` H35 | Ainda listava "TED Orbe → 1.1.03.001" como ASSUMO (virou CONFIRMADO, H42) e contagens de antes da IA. Atualizada: 140 de 184 lançamentos por regra ASSUMO |
| `HIPOTESES.md` H36 | Impacto "7 lançamentos da EduAbroad ficam HUMANO" desatualizado: hoje 5 por IA verificada e 2 por decisão humana (H43) |
| `docs/STATUS.md` | "Rastro de 100% dos números" segue desmarcado, com o que falta; linha da auditoria |
| `README.md` | Organização do repositório: faltavam `cache_ia/` e `scripts/` |
| novos | `docs/CONFORMIDADE.md`, `docs/AUDITORIA.md`, `scripts/auditar_saida.py` |

## Para o Lucca decidir (não alterado: é cálculo, regra ou texto de saída)

1. Metade do excesso por operação (709,46) ou manter 709,43 como ASSUMO: resolve o ❌ dos itens 1, 3 e 5.
2. Trocar `;` por `,` nos textos livres da saída (risco de corretor com `split(";")`, sobretudo em `pendencias.csv`).
3. `divergencias.data_referencia_vigencia`: remover ou fechar como coberta por `checkout.estorno`.
4. Levar a checagem "toda linha do rastro existe na fonte" para o validador, e um teste para "saldo negativo do Aurora não vira pendência".
