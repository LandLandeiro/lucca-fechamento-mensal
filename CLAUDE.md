# Tarvo · fechamento de setembro/2026 (Desafio Barte AI)

Leia `docs/case.md` (instruções oficiais) e `HIPOTESES.md` antes de qualquer tarefa. O data pack está em `data/` e **não pode ser alterado nem limpo à mão**: a solução lê os arquivos como chegam.

## Regras deste projeto

1. **Regra de negócio não se inventa.** Se a regra não está nos dados nem em `HIPOTESES.md` como CONFIRMADO ou ASSUMO, pare e me diga — eu decido se pergunto ao financeiro ou assumo e registro.
2. **Todo número de saída tem rastro** até as linhas de origem (`rastro.csv`); a soma das linhas por `id_saida` tem que bater com o número reportado. Total que não fecha = número inventado.
3. **Dinheiro em centavos inteiros** nas contas; formatar só ao escrever a saída. Percentuais sem arredondar no meio do caminho.
4. **Alarme falso conta contra.** Na dúvida, não afirme: vira linha em `pendencias.csv` com motivo e quem decide.
5. **IA só onde há ambiguidade real** (ex.: classificar lançamento sem regra clara), sempre com `metodo` e `confianca`. Regra determinística primeiro.
6. Formato de saída é fixo (ver `docs/case.md`): CSV com `;`, ponto decimal, datas AAAA-MM-DD, CNPJ só números (14 dígitos).
7. A solução tem que rodar de novo em outubro com arquivos novos no mesmo formato: nada de valor fixo de setembro no código.

## Como trabalhar comigo (Lucca)

- Antes de construir, diga o plano em poucas linhas. Explique decisões técnicas em 2–3 linhas para eu defender.
- Quando eu pedir análise, não escreva código de solução.
- Commits pequenos, em português. Nunca peça nem escreva a chave da API: ela está só no `.env.local`.
