# Teste das regras

O ponto 2 do Manuel no Checkpoint 1: a conferência tem que testar as regras, não só a conta, "porque duas IAs partindo do mesmo `regras.yaml` erram juntas". Por isso as regras são testadas contra o que a Helena disse, e não contra o yaml.

**Se uma regra mudar errado, estes testes quebram.**

| teste | o que garante | rodar |
|---|---|---|
| `tests/test_casos_ouro.py` e a marca `caso_ouro` | Cada exemplo concreto da Helena dá o valor que ela afirmou: 131,005 → 131,01 e −0,005 → −0,01 (o modo vem do `regras.yaml`); TX88444848 (estorno de agosto pela taxa de 22/08, −83,12); TX88445133 (Casa, −5,50); PC-0926-0011 (R$ 29,56); PC-0926-0162 (conta uma vez); PC-0926-0210 (os dois valores); Bridge como `contrato_orbe`; par venda e estorno com sinais; PIX de 18.240 como remessa de outubro. Cada teste cita a fala. Um teste de registro impede que um caso suma | `pytest -m caso_ouro` |
| `tests/test_citacoes_regras.py` | Toda regra CONFIRMADO no `regras.yaml` traz uma citação que aparece **literalmente** em `docs/FINANCEIRO_SLACK.md`. Uma fala editada ou inventada não passa | `pytest tests/test_citacoes_regras.py` |
| validador da saída (`src/tarvo/saida/validador.py`) e `scripts/auditar_saida.py` | Todo número tem rastro até a linha de origem e a soma fecha. Também confere o formato, a cobertura de cada arquivo e a natureza de cada divergência | roda no fim de cada fechamento |
| auditoria independente (`docs/auditoria_regras/`) | Outra sessão de IA, sem o `regras.yaml` nem o código, escreveu as regras do zero a partir do case, dos dados e das falas, e só depois comparou com a nossa solução: 0 diferenças altas | feita uma vez, em 17/10 |

## O limite

O teste das citações garante que **a fala existe**, não que **ela sustenta a regra**. Uma regra pode citar uma frase verdadeira que não diz o que a regra faz. Foi o caso da `aurora.orbe_recebivel`: "Os créditos da Orbe vocês classificam" está no canal, mas não confirma a conta 1.1.03.001, e ela voltou a ASSUMO (D90).

Quem conferiu essa leitura, isto é, se cada fala sustenta a sua regra, foi a auditoria independente (`docs/auditoria_regras/`), que leu as falas sem ver as nossas regras.
