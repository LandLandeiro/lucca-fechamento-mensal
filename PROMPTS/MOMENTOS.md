# Momentos que importaram

De 2 a 4 momentos. Para cada um: o que pedi, o que a IA devolveu, o que fiz com isso. Pelo menos um em que a IA errou ou me levou para o lugar errado.

## 1. Verificação tripla do mínimo: três caminhos, o mesmo 207.031,31

- **O que aconteceu:** a comissão de checkout saiu de três caminhos que não compartilham código: (1) a exploração, em scripts Node de leitura com centavos inteiros (Σ `valor_taxa` 231.880,36 e as divergências de Rota e Bridge); (2) o código da solução, em Python com `Decimal`; (3) um script meu, numa outra sessão de IA que não viu o código, que recalculou do zero. Os três chegaram a 207.031,31, com os 21 lojistas no centavo, 57 transações em pendência e 1.943 linhas.
- **Como foi percebido:** a IA reconciliou o total do código com os números da exploração (231.880,36 − Atlas − Casa cobrado + Casa contratado − divergências = 207.031,31) e eu pedi a conferência independente antes de aceitar.
- **O que mudou:** o mínimo foi aceito como conferido, e a mesma identidade virou regra do validador da E5a (Σ `valor_taxa` = Σ comissão + Σ divergências).

## 2. Casa do Estudante −5,50: o código achou um caso de borda que o meu teste não previa

- **O que aconteceu:** eu pedi o teste "Casa do Estudante = 0" (tarifa zerada de setembro a dezembro). O código deu −5,50: o estorno TX88445133 (L433) é de uma venda de 21/08, fora da vigência da condição especial; pela regra das 20:06 ele abate pela taxa de 21/08 (débito 1,49% × 369,39).
- **Como foi percebido:** a IA não ajustou o código para bater com o meu teste; mostrou a conta, citou as duas regras e me perguntou.
- **O que mudou:** mantive −5,50 (correto pelas regras 20:06 e 20:47). O teste afirma −5,50 e as 118 transações de setembro em 0; na E6 o negativo vira pendência para a Helena em vez de nota.

## 3. A IA apagou o próprio trabalho com `git checkout --` (erro da IA)

- **O que aconteceu:** num teste de mutação (trocar truncamento por arredondamento para ver se os testes falham), a IA desfez a troca com `git checkout -- src/tarvo/calculos/comissoes.py`. O arquivo ainda não estava commitado, e o comando o voltou ao esqueleto da E0, apagando a implementação.
- **Como foi percebido:** a própria IA notou na saída do comando, antes de seguir, que a versão restaurada era a do HEAD (o esqueleto) e não a dela.
- **O que mudou:** o arquivo foi restaurado da cópia feita antes da mutação, conferido (`ROUND_DOWN` presente, nenhum `ROUND_HALF_UP`) e os 50 testes rodaram de novo. A mutação provou que os testes distinguem as regras (4 falharam). Regra a partir daqui: mutação só com backup explícito, nunca `git checkout` em arquivo não commitado.

## 4. Premissa escrita, cliente corrigiu, mudou uma linha (truncar → arredondar)

- **O que aconteceu:** às 20h55 registrei como ASSUMO "comissão contratada: truncar no centavo, como a Orbe" (D09), com base escrita (1.001 linhas da Orbe só fecham truncando) e com a consequência (tolerância 0). Às 21:13 a Helena respondeu à Fox AI: "A gente não trunca. Arredondamento comum para o centavo... linha por linha" e "Diferença de centavo por causa do truncamento da Orbe não é divergência".
- **Como foi percebido:** a resposta pública no canal contradizia uma premissa marcada como ASSUMO, que eu tinha escrito justamente para poder ser contestada.
- **O que mudou:** a regra virou CONFIRMADO no `regras.yaml` (`TRUNCAR` → `ROUND_HALF_UP`); o modo de arredondamento está num só lugar, então o cálculo não foi reescrito. O centavo de diferença com a Orbe passou a ser resíduo explícito (−9,07), não divergência. Os números novos (207.039,73 · 16.973,65 · 39.543,45 · 506,65) bateram no centavo com a minha previsão independente antes do commit.

## 5. IA sugere, código prova, humano aprova

- **O que aconteceu:** 7 lançamentos da EduAbroad não casavam com nenhuma regra ("EDU ABROAD CONSULTORIA" no banco × "EduAbroad" na planilha). Em vez de criar um alias na mão, pedi a classificação ao `claude-haiku-5-5` com a lista fechada de contas e de lojistas, e o código só aceitou o que conseguiu provar com outra fonte: os 5 PIX recebidos no Meridiano somam 394.222,69, exatamente o Valor R$ + IOF das operações da EduAbroad no relatório da Ponte.
- **Como foi percebido:** nos 2 PIX enviados pelo Aurora a própria IA recusou o vínculo ("consultoria LTD" pode ser um fornecedor) e deu confiança 0,5 e 0,4; o código mandou os dois para uma pessoa com o motivo exato. Não reescrevi o prompt até a resposta "passar": a dúvida da IA é informação.
- **O que mudou:** 5 lançamentos por IA verificada, 2 em pendência para o Lucca, e uma proposta de alias em `sugestoes_regra.csv` para virar regra em outubro, só depois de aprovada. A resposta fica em `cache_ia/`: a banca reexecuta sem chave, sem custo e com o mesmo resultado.
