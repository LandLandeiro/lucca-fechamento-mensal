# Status

> Painel atualizado ao fim de cada etapa. Última atualização: 16/10 ~21h30 (E1 + E2).

**Nível atual:** **Mínimo — conferido** (comissão CHECKOUT por lojista + rastro + validador)
**Próximo passo:** E5a: divergências de checkout.

## Mínimo

- [x] Leitor Orbe (com testes)
- [x] Leitor taxas + cadastro EC→CNPJ (com testes)
- [x] `comissoes_por_lojista.csv` — CHECKOUT
- [x] `rastro.csv` das comissões CHECKOUT (1943/1943 linhas da Orbe, cada uma exatamente uma vez: COM-… ou PEN-…)
- [x] Validador (soma do rastro = total; formato; cobertura das linhas da Orbe); falha = código 1
- [x] **Conferência do mínimo:** um script independente do Lucca (outra sessão de IA, sem ver este código) recalculou do zero e bateu os 21 lojistas no centavo: total 207.031,31, 57 transações em pendência, 1.943 linhas. Também bate com a exploração (ver Números)
- [x] Saída em ordem determinística: comissão decrescente, depois CNPJ; rastro por `id_saida` e linha

## Alvo

- [ ] Leitor e-mail Ponte + anexo
- [ ] Comissão REMESSA
- [ ] `divergencias_taxa.csv` (CHECKOUT e REMESSA), amostra conferida, zero alarme falso conhecido
- [ ] `notas_a_emitir.csv`
- [ ] Leitores Aurora, Meridiano, plano de contas
- [ ] `lancamentos_classificados.csv` (REGRA → IA → HUMANO)

## Extra

- [ ] `pendencias.csv` completo (motivo + quem decide); hoje só a do checkout
- [ ] Rastro de 100% dos números
- [ ] Roda em outubro sem mudar código: arquivos achados por prefixo, vigências e regras lidas do `regras.yaml`; falta testar com um arquivo de outro mês

## Regras (`regras.yaml`)

- 41 regras: CONFIRMADO 19 · SEI 11 · ASSUMO 8 · PENDENTE 3 (`divergencias.data_referencia_vigencia`, `remessa.arredondamento_participacao`, `contabil.padroes_de_descricao`, este último preenchido na E6)
- HIPOTESES com os textos literais do financeiro (Q-A…Q-G → P01–P11), fonte `docs/FINANCEIRO_SLACK.md`

## Números atuais (saída de `python -m tarvo --dados data --saida saida`)

- **Comissão CHECKOUT total: R$ 207.031,31**, em 21 lojistas e 1.886 transações
- **Pendências: 1**, a Atlas Idiomas (EC 1076801732): 57 transações, R$ 7.876,05 cobrados pela Orbe (informativo); quem decide: comercial
- **Validador: OK**
- Conferência independente (exploração em outro programa, centavos inteiros): Σ `valor_taxa` 231.880,36 − Atlas 7.876,05 − Casa cobrado 15.391,27 + Casa contratado −5,50 − divergências de taxa (Rota 1.546,28 + Bridge 29,95) = **207.031,31** ✓
- **Casa do Estudante = −5,50 (decidido, mantido):** as 118 transações de setembro dão 0 (condição especial). O estorno TX88445133 (L433) é de uma venda de 21/08, fora da vigência 2026-09-01–2026-12-31; pela regra das 20:06 usa a taxa de 21/08 (débito 1,49%) → −5,50. Correto pelas regras 20:06 e 20:47; na E6 vira pendência para a Helena (negativo não emite nota)
- `ref_origem` no rastro = `id_transacao` em todas as linhas (COM- e PEN-); a linha física vai na coluna extra `linha_arquivo`
