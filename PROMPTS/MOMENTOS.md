# Momentos que importaram

Os 4 mais fortes, no formato do case: o que pedi, o que a IA devolveu e o que fiz com isso. Os dois primeiros são momentos em que a IA errou ou me levou para o lugar errado.

## 1. A IA concluiu "truncar como a Orbe"; a Helena disse que a Tarvo não trunca, e a correção foi uma linha

- **Pedi** a análise do data pack. **A IA devolveu** que a Orbe trunca os centavos (1.001 linhas só fecham truncando) e que arredondar geraria cerca de 1.000 alarmes falsos de R$ 0,01. Registrei "truncar" como premissa ASSUMO no `regras.yaml`, com essa base (D09, commit `0eb28a3`).
- **O que fiz:** às 21:13 a Helena respondeu: *"A gente não trunca. Arredondamento comum para o centavo... linha por linha"*. Como a premissa estava escrita num lugar só, a correção foi uma linha no `regras.yaml` (`TRUNCAR` → `ROUND_HALF_UP`), sem reescrever o cálculo. O centavo de diferença com a Orbe virou resíduo explícito (−9,07), não divergência (D27, commit `cc7022d`).

## 2. A IA de classificação não reconheceu o lojista; o código barrou e eu decidi com a soma

- **Pedi** que a IA classificasse os 7 lançamentos de extrato que nenhuma regra cobria, com lista fechada de contas e lojistas. **A IA devolveu** o vínculo certo nos 5 PIX recebidos, mas nos 2 PIX enviados achou que "EDU ABROAD CONSULTORIA LTD" podia ser um fornecedor (confiança 0,4 e 0,5). O código aceitou os 5, porque somam 394.222,69, exatamente as operações da EduAbroad na Ponte, e barrou os 2.
- **O que fiz:** não reescrevi o prompt para forçar o acerto. Decidi as 2 linhas com a evidência da soma e das vendas da EduAbroad na Orbe, como decisão humana explícita, e aprovei a sugestão da IA como regra a partir de outubro (D42, D44, commits `eda5423` e `b651260`).
- **Depois, a correção:** uma avaliação simulada da banca, feita numa sessão nova sem o contexto da construção (`docs/AVALIACAO_SIMULADA.md`), apontou que a regra resolvia: "EDU ABROAD CONSULTORIA" é o nome que o relatório da Orbe usa para o EC da EduAbroad, e nós tínhamos restringido essa regra (D35) para a IA ter trabalho. Foi um erro nosso. Na D52 voltei a regra: as 7 linhas são REGRA, a IA fica com 0 linhas em setembro e só recebe nome que nenhuma regra reconhece (o teste de outubro tem um). As decisões L28/L69 ficaram no `regras.yaml` como histórico.

## 3. O rascunho do checkpoint dizia mais do que tinha sido verificado

- **Pedi** a revisão do rascunho do Checkpoint 1, escrito com a IA do planejamento, antes de postar. **A IA do código** conferiu cada afirmação contra a saída e apontou: "todos os totais foram conferidos por um script independente" (a conferência independente cobria comissões, divergências e notas, não os extratos) e "cada resposta do financeiro mudou um valor, não o programa" (falso para Q-J, Q-K e Q-L).
- **O que fiz:** corrigi o rascunho antes de postar (e acrescentei o status SEI/ASSUMO/CONFIRMADO nas hipóteses); depois pedi a auditoria completa da saída (`docs/AUDITORIA.md`), que achou mais um erro real de R$ 0,03 (D45).

## 4. Verificação cruzada: outra sessão de IA, sem ver o código, recalculou do zero

- **Pedi**, em outra sessão de IA que não via este código, um script que recalculasse do zero comissões, divergências, remessa e notas. **Bateu no centavo** em todas essas etapas: 207.031,31 com truncamento (registrada no commit `3f83a5a`) e, depois da correção da Helena, 207.039,73, 16.973,65, 39.543,45 e as 21 notas (commit `cc7022d`).
- **O que fiz:** só aceitei cada etapa depois de bater. Quando a minha previsão não bateu (16 pendências esperadas × 15 calculadas, na E6b), a IA mostrou o porquê antes do commit, e o número ficou como estava.

## 5. Quanto devolver: a fórmula da Helena ficou, e o valor a devolver virou outra coluna

- **O que aconteceu:** a pendência da Casa pedia para devolver R$ 15.397,42, o valor da divergência pela fórmula da Q-H c (bruto × (taxa aplicada − contratada)). A resposta da Helena a uma pergunta de outro time no canal (Q-U 4, Turma do Barulho) mostrou o problema: *"A Orbe já liquida o líquido"*, então o lojista perdeu exatamente o que a Orbe descontou acima do contrato, que é o `valor_taxa` truncado menos a comissão contratada. A diferença era o centavo de truncamento da Orbe: Casa 15.396,77, Rota 1.545,86, Bridge 29,94.
- **Pedi** para trocar o valor da divergência. **A IA parou antes de implementar:** a troca contrariava a Q-H c, uma resposta CONFIRMADO da Helena (*"O valor da divergência eu quero como valor bruto × (taxa aplicada − contratada)"*), e sugeriu separar os dois valores.
- **O que fiz:** aceitei separar (D71). `diferenca_brl` segue a Q-H c, e `valor_a_devolver_brl` (Q-U 4) é a coluna que pendências, rascunhos e totais usam. Daí saiu a conta da causa raiz (D74): devolver R$ 16.972,57, recuperar da Orbe R$ 1.545,86, custo para a Tarvo R$ 15.426,71.

## Outros momentos (resumo)

- **A IA apagou um arquivo meu (17/10, ~12h53).** Ao mover o export da avaliação simulada para `PROMPTS/`, ela encadeou com `;` um `sed` que falhou e o `rm` do original, que não estava no git: o `rm` rodou mesmo com a cópia vazia. Ela parou, contou o que tinha feito e mostrou de onde recuperar: a sessão original, guardada pelo Claude Code em `.jsonl`. Regra a partir dali: script Python para trocas, conferir a cópia (tamanho, linhas, nada pessoal) e só apagar com `&&` em cada passo.

- **Casa do Estudante −5,50:** eu pedi o teste "Casa = 0"; o código deu −5,50 (estorno de uma venda de agosto, pela taxa de agosto). A IA não ajustou o código ao teste: mostrou a conta e perguntou. Mantive −5,50, que virou pendência de nota negativa.
- **A IA apagou o próprio trabalho** com `git checkout --` num arquivo não commitado, durante um teste de mutação; percebeu na saída do comando e restaurou da cópia. Regra a partir dali: mutação só com backup.
- **Nomes da Orbe:** a união que eu pedi (planilha ∪ todos os nomes da Orbe) teria ligado a EduAbroad por regra, contra a minha decisão de passar pela IA. A IA restringiu aos ECs sem vínculo e me avisou (D35).
- **Auditoria:** o script de auditoria quebrava com decimal malformado, o mesmo erro que o validador teve antes (D26). Foi testado com saídas estragadas de propósito antes de eu confiar nele.
- **Prova de outubro:** a varredura achou mês fixo em dois textos ("conferir no extrato de outubro"). Parei antes de corrigir, como pedi; o texto passou a vir da data (D48).
