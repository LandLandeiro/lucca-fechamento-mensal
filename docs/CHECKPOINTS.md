# Checkpoints

## Checkpoint 1 · 17/10, 10:44

Enviado por DM ao Manuel Freitas (Barte) às 10:44 de 17/10. Texto literal:

---

Lucca Landeiro (time solo) · Checkpoint 1

1. Causa raiz: o contrato muda e ninguém avisa quem cobra. As regras vivem em três lugares (planilha que "passa por várias mãos", e-mail da Ponte, cabeça da Helena), e nada compara contratado × cobrado: Casa do Estudante zerada e a Orbe cobrou R$ 15,4 mil; Rota +0,50 p.p. sem mudança de contrato; Mundo Aberto a 1,20% e a Ponte em 1,5%.

2. Nível: Extra. Mínimo e Alvo prontos e conferidos no centavo por script independente; rastro de 100% validado; "roda em outubro sem mudar código" provado com teste; CI verde em Windows/Linux.

3. Plano até 18h30:
- 12h30: ajustar regras às respostas pendentes do financeiro + relatório de "o que está em jogo"
- 16h00: rascunhos de contestação (Orbe/Ponte) + checkpoint 2
- 17h00: congelar; checagem de consistência docs × saída
- 18h15: repositório público + teste de clone limpo

4. Três premissas não confirmadas:
- Spreads negativos (4 ops) listados como divergência além da contestação. Se errado: saem 4 linhas (R$ 3.565,98) do divergencias_taxa.
- Venda estornada no mesmo mês não gera divergência (líquido zero). Se errado: voltam 5 linhas (4 Rota, 1 Casa).
- Devolução Pix de R$ 12.400 em 2.1.01.001 (repasse volta a ser devido). Se errado: muda a conta de 1 lançamento para 2.1.01.002.
Todas estão no regras.yaml; a mudança é uma linha e o validador refaz tudo.

5. Fora de propósito: conciliação Orbe × banco parcela por parcela (sem agenda de recebíveis, como a Helena pediu) e qualquer decisão da Helena (devolver, contestar, nota negativa): vira pendência com valor e responsável.

6. Quem faz o quê: sozinho. Eu decido regras e premissas e falo com o financeiro; o Claude Code constrói e testa; outra sessão de IA recalcula tudo de forma independente para conferir.

---

**Resposta do Manuel Freitas** (literal):

> Lucca, boa leitura de causa raiz: você sustenta com casos do próprio mês, e as premissas já trazem impacto e o que muda se estiverem erradas.
> Antes das 18h30: (1) confira as três premissas contra o que já foi respondido no canal e deixe explícito o que é fato, o que é premissa e o que é resposta do financeiro; (2) garanta que a conferência independente testa as regras, não só a conta, porque duas IAs partindo do mesmo `regras.yaml` erram juntas.
> Pergunta para levar ao pitch: se uma regra estiver errada, o que na sua solução avisa a Helena antes de o lojista reclamar?

### Conferência independente das regras (ponto 2 do Manuel)

Uma sessão nova de IA, só com o case, os dados e as falas da Helena (sem `regras.yaml` nem código), escreveu as regras do zero e recalculou os totais; só depois comparou com a nossa solução. Resultado: notas 243.284,29, Ponte 39.543,45, devolução e lançamentos iguais no centavo; 0 diferenças altas; 7 médias, tratadas nas D84–D89 ou explicadas. Detalhe e o que fizemos com cada uma: `docs/auditoria_regras/README.md`.

### O que virou cada premissa (ponto 1 do Manuel)

| Premissa do checkpoint | O que respondeu o canal | Como está hoje |
|---|---|---|
| Spreads negativos listados como divergência além da contestação | Q-O (Helena 09:44): "No spread negativo o lojista não pagou a mais. O prejuízo é nosso com a Ponte, então é pendência de contestação. Se quiserem listar também nas divergências, tudo bem, desde que fique claro que é outra natureza." E Q-AA 3 (11:37): "Coloquem os dois na pendência, deixando claro qual é qual" | **Resposta do financeiro.** Continuam nas 4 linhas de `divergencias_taxa.csv` com natureza `spread_negativo` (D63), e a contestação traz os dois valores: o do relatório (−1.834,05, o que aconteceu) e a diferença até o contrato (−3.565,98, o que se pede à Ponte, D80) |
| Venda estornada no mesmo mês não gera divergência | Q-N 3 (Helena 09:44): "A venda e o estorno se anulam. Cobro da Orbe só o que sobrou de diferença líquida." Q-AB 3 (11:38): "é transação por transação. O estorno de uma venda que veio com taxa errada também entra, com valor negativo." | **Resposta do financeiro: CONFIRMADO, com ajuste.** A cobrança segue pelo líquido (D69), e a lista passou a ter as duas linhas, o estorno negativo (D77): os 5 pares voltaram para `divergencias_taxa.csv` |
| Devolução Pix de R$ 12.400 em 2.1.01.001 | Q-R 2 (Helena 09:48): "As duas contas fazem sentido. Escolham uma, mantenham o mesmo critério e escrevam o motivo." | **Premissa: ASSUMO com motivo e aceite** (D65): baixa a conta onde o repasse estava (L26, 09/09, 2.1.01.001) |

Onde fica cada tipo de afirmação, com as contagens: README, seção "Fato, resposta e premissa".

## Checkpoint 2 · 17/10, 16:00
