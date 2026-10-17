# Histórico das sessões de IA (sem edição, exceto chaves e dados pessoais)

| # | Quando | Ferramenta | Para quê | Arquivo |
|---|---|---|---|---|
| 01 | 16/10, 10h43 – 17/10, 17h | Claude (app) | preparação, plano e conferência independente (os scripts estão em `scripts/verificacao_independente/`) | registrado como relatório no 03. O claude.ai só exporta a conta inteira, com conversas pessoais de fora do projeto, e a cópia turno a turno por IA foi bloqueada pelo filtro de segurança do modelo |
| 02 | 16/10, noite – 17/10, 00h40 | Claude Code | exploração do data pack, perguntas ao financeiro e construção (E0–E6b parte 1, Q-H…Q-M, teste de reprodutibilidade) | [02-construcao-claude-code-noite.txt](02-construcao-claude-code-noite.txt) |
| 03 | 17/10, ~16h50 | Claude (app) | relatório da sessão de planejamento e conferência (versão 2; a versão 1, de ~12h30, está no histórico do git) | [03-claude-app-relatorio.md](03-claude-app-relatorio.md) |
| 04 | 17/10, ~11h | Claude Code (sessão nova, sem contexto) | avaliação simulada da banca (saída em `docs/AVALIACAO_SIMULADA.md`) | [04-avaliacao-simulada.txt](04-avaliacao-simulada.txt), gerado do `.jsonl` completo da sessão (o export original foi apagado por engano e o da sessão retomada saiu resumido; ver `docs/DIARIO.md`, 12:43–13:07) |
| 05 | 17/10, 08h – 16h43 | Claude Code | construção da manhã e da tarde (E6b parte 2, auditoria, CI, outubro, D52–D96, painel na main, documentação, histórico) | [05-construcao-claude-code-manha-tarde.txt](05-construcao-claude-code-manha-tarde.txt) |
| 06 | 17/10, 15h49 – 16h23 | Claude Code (sessão nova, sem contexto) | auditoria final da banca: recontagem sem importar `src/`, clone limpo, formato, rastro e docs × saída | [06-auditoria-final.txt](06-auditoria-final.txt) |
| 07 | 17/10, 12h21 – 14h53 | Claude Code (worktree da branch `relatorio`) | painel do fechamento (`saida/painel.html`, `docs/PAINEL.md`) | [07-painel-claude-code.txt](07-painel-claude-code.txt) |

O ensaio de 16/10 à tarde (repositório `barte-esqueleto`) ficou fora deste repositório; ver `HIPOTESES.md`, "Origem do código".

Exportar uma sessão do Claude Code: `/export` dentro da sessão, salvar aqui.
