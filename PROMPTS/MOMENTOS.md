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
