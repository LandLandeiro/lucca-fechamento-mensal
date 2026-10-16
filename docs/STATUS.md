# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 16/10 20h30 (E0).

**Nível atual:** nenhum (estrutura pronta, sem cálculo)
**Próximo passo:** E1: postar as perguntas P01–P09 no `#tarvo-financeiro` (20h30–22h30), depois os leitores da Orbe e das taxas + cadastro.

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

- SEI preenchidas: 14 · ASSUMO: 0 · CONFIRMADO: 0 · vazias: 20 (P01–P09 aguardando resposta)

## Números atuais

Ainda não há saída gerada. Referências da exploração (`docs/EXPLORACAO.md`), **não são saída**: Σ `valor_taxa` Orbe = R$ 231.880,36; Σ spread Ponte = R$ 78.073,59 (inclui a duplicata).
