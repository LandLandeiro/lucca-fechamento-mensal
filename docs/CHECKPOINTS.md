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

## Checkpoint 2 · 17/10, 15:38

Postado às 15:38 de 17/10, dentro do prazo: a organização mudou o prazo do Checkpoint 2 de 15:30 para 16:00 no canal de avisos (`#hackathon-avisos`). Texto literal:

---

Checkpoint 2 · Lucca Landeiro (time solo)

O que já funciona
- Fechamento completo em um comando: comissão das duas linhas, 237 divergências transação por transação, 21 notas (R$ 243.284,29), 184 lançamentos classificados e 15 pendências com motivo e quem decide. Todo número tem rastro que fecha com as linhas de origem.
- O arquivo 06 da Orbe (ajustes tardios) entrou sem mudar código: −R$ 3.304,39 nas notas, com a regra da Helena para antes e depois da aprovação.
- Roda em outubro: teste com um mês sintético (lojista novo, nome novo resolvido pela IA, Atlas com contrato).
- Seu ponto 1: cada regra está marcada como fato, premissa ou resposta do financeiro (CONFIRMADO 52, ASSUMO 38, SEI 13), com a citação literal da Helena e teste.
- Seu ponto 2: uma auditoria cega, feita por outra sessão sem o regras.yaml nem o código, escreveu as regras do zero e chegou às mesmas notas no centavo. As diferenças de regra que ela achou foram tratadas (docs/auditoria_regras).
- Painel só de leitura (o que depende de quem e a busca de rastro) e CI verde em Windows e Linux.

O que mudou no plano
- Bridge: deixou de ser "condição não informada" e virou erro da Orbe com contrato ("o que decide é o contrato"). R$ 1.575,80 a recuperar da Orbe, somando Rota e Bridge.
- Casa do Estudante: concessão do comercial, custo da própria Tarvo (R$ 15.396,77), sem recuperação da Orbe.
- Entraram o painel e os rascunhos de contestação; a provisão saiu, porque fica fora do fechamento.
- Continua fora: conciliação parcela por parcela, e as decisões da Helena viram pendência.

Próximo: auditoria final, congelar às 17h e pitch.

---
