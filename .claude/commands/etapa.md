---
description: Executa uma etapa do PLANO (E1, E2…) seguindo o protocolo do projeto
argument-hint: <etapa, ex.: E2>
---

Etapa pedida: **$ARGUMENTS**

1. Leia `docs/PLANO.md` (seções 7 e 9: o que a etapa entrega e quando está "pronta"), `docs/STATUS.md`, `regras.yaml` e `HIPOTESES.md`.
2. Antes de escrever código, diga em poucas linhas: o plano da etapa, os arquivos que vai mexer e **quais regras de `regras.yaml` a etapa usa**. Se alguma estiver com `valor: null`, pare e me pergunte: não invente valor, não use padrão "razoável".
3. Implemente com testes. Casos esperados vêm das fontes (linha de origem citada no teste), nunca da própria saída do código.
4. Rode `python -m tarvo --dados data --saida saida` e `pytest`.
5. Siga o PROTOCOLO de fim de etapa do `CLAUDE.md`: testes → `docs/STATUS.md` → `docs/DIARIO.md` → `docs/DECISOES.md` (se houver) → commit `"<etapa>: <resumo>"`.
6. No fim, mostre: o que ficou pronto, os números gerados (com 1 exemplo de rastro conferido) e o que virou pendência.
