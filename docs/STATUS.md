# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 16/10 20h41 (E0 + respostas do financeiro).

**Nível atual:** nenhum (estrutura pronta, sem cálculo)
**Próximo passo:** E1: leitores da Orbe e das taxas + cadastro. Acompanhar em `#duvidas-hackathon-ai` as respostas a P01/P06 (MN AI 20:30), à estrutura de NF (MN AI 20:26) e às minhas de 20:36 (P02, P07, P08, P09).

## Mínimo

- [ ] Leitor Orbe (com testes)
- [ ] Leitor taxas + cadastro EC→CNPJ (com testes)
- [ ] `comissoes_por_lojista.csv` — CHECKOUT
- [ ] `rastro.csv` das comissões CHECKOUT
- [ ] Validador (soma do rastro = total; formato)
- [ ] 2 lojistas conferidos à mão

## Alvo

- [ ] Leitor e-mail Ponte + anexo
- [ ] Comissão REMESSA
- [ ] `divergencias_taxa.csv` (CHECKOUT e REMESSA), amostra conferida, zero alarme falso conhecido
- [ ] `notas_a_emitir.csv`
- [ ] Leitores Aurora, Meridiano, plano de contas
- [ ] `lancamentos_classificados.csv` (REGRA → IA → HUMANO)

## Extra

- [ ] `pendencias.csv` completo (motivo + quem decide)
- [ ] Rastro de 100% dos números
- [ ] Roda em outubro sem mudar código (nenhum valor de setembro fixo)

## Regras (`regras.yaml`)

- 40 regras: SEI 13 · ASSUMO 7 · CONFIRMADO 5 · PENDENTE 15
- Bloqueio para o mínimo (comissão CHECKOUT): `checkout.composicao_comissao` (antecipação/reversão) está PENDENTE. O arredondamento foi resolvido (D09)

## Números atuais

Ainda não há saída gerada. Referências da exploração (`docs/EXPLORACAO.md`), **não são saída**: Σ `valor_taxa` Orbe = R$ 231.880,36; Σ spread Ponte = R$ 78.073,59 (inclui a duplicata).
