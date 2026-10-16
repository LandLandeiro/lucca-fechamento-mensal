---
description: Auditoria SÓ LEITURA da saída contra as fontes (não altera código nem dados)
argument-hint: [entregável opcional, ex.: comissoes]
---

Auditoria **somente leitura**. Escopo: $ARGUMENTS (vazio = todos os entregáveis gerados).

Regras desta sessão:
- **Não edite** nada em `src/`, `data/`, `saida/`, `regras.yaml` nem nos docs. Scripts de conferência só fora do repositório (scratchpad), lendo os arquivos de `data/` direto, **sem importar `tarvo`**: a conferência tem que ser independente do código auditado.
- Não confie na saída: recalcule a partir das fontes.

Checagens:
1. **Rastro fecha:** para cada arquivo de `saida/`, a soma de `rastro.csv` por `id_saida` = número reportado.
2. **Rastro aponta para linhas reais:** cada `ref_origem` existe no `arquivo_origem` e o `valor` bate com a linha.
3. **Amostra contra a fonte:** 3 lojistas de comissão (um grande, um com estorno, um com nome inconsistente), 5 divergências, 3 notas e 5 lançamentos classificados, recalculados à mão a partir dos arquivos originais.
4. **Regras:** cada número usa só regras SEI/ASSUMO/CONFIRMADO de `regras.yaml`; aponte qualquer valor que pareça ter vindo de regra vazia.
5. **Alarmes falsos:** divergências abaixo do ruído (truncamento da Orbe, tolerância de spread da Ponte) ou de lojista mapeado sem chave.
6. **Formato:** `;`, ponto decimal, datas AAAA-MM-DD, CNPJ com 14 dígitos, enums do case.

Saída: tabela com o achado, a evidência (arquivo + linha) e a gravidade (número errado · risco de alarme falso · formato). Sem correções: eu decido o que vira etapa.
