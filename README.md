# Tarvo · fechamento de setembro/2026

> Desafio Barte AI · Hackathon de AI Services · 16 e 17/10/2026 · time: [NOME DO TIME] (Lucca Rocha Landeiro)

## O problema (em 2 frases)

[preencher]

## O que a solução entrega

Lê os arquivos de `data/` exatamente como chegam e gera, em `saida/`:

| Arquivo | O que é |
|---|---|
| `comissoes_por_lojista.csv` | comissão de cada lojista por linha de negócio |
| `divergencias_taxa.csv` | taxa contratada × aplicada, transação por transação |
| `notas_a_emitir.csv` | notas fiscais a emitir |
| `lancamentos_classificados.csv` | lançamentos dos dois extratos no plano de contas |
| `pendencias.csv` | o que precisa de uma pessoa, com motivo e quem decide |
| `rastro.csv` | cada número de saída ligado às linhas de origem |

## Como rodar do zero

[preencher: pré-requisitos, instalação, comando único]

Chaves necessárias: `ANTHROPIC_API_KEY` em `.env.local` (modelo em `.env.example`). [dizer se roda sem chave]

## Como a analista usa em outubro

[preencher]

## Onde a IA atua e onde não atua

[preencher]

## Limitações conhecidas

[preencher]

## Organização do repositório

```
data/      data pack original, sem alteração (ver .gitattributes)
docs/      instruções do case
src/       código
saida/     arquivos gerados
PROMPTS/   histórico das sessões de IA + MOMENTOS.md
HIPOTESES.md
```
