# Decisões técnicas

Cada decisão: o que foi escolhido, a alternativa considerada e o motivo. O Lucca revisa.

| # | Data | Decisão | Alternativa considerada | Motivo |
|---|---|---|---|---|
| D01 | 16/10 20h | **Python 3.12** | Node/TypeScript (usado na exploração, porque não havia Python no PATH) | `email` lê o .eml nativo, `decimal` é exato, `openpyxl` lê células mistas número/texto. A exploração em Node foi descartável e ficou fora do repositório |
| D02 | 16/10 20h | **Sem banco de dados**: arquivos entram, arquivos saem, tudo em memória | SQLite/Postgres | São cerca de 2,4 mil linhas por mês. Um banco acrescenta passo de carga e um estado que esconde o rastro. Reexecutar do zero é barato e mais auditável |
| D03 | 16/10 20h | **Lojista se liga por chave (EC ou CNPJ de 14 dígitos), nunca por semelhança de nome** | casamento aproximado de nomes (fuzzy) | O mesmo EC aparece com até 3 nomes, e "Horizonte" casaria com 2 lojistas diferentes (o case cita isso como erro clássico). Sem chave confiável → pendência |
| D04 | 16/10 20h | **Regras de negócio em `regras.yaml`**, com valor, status, fonte e pergunta | regras dentro do código | Resposta do financeiro muda um dado, não o programa. Cada número fica explicável pela regra e pela fonte. Regra vazia bloqueia o cálculo em vez de virar um padrão inventado |
| D05 | 16/10 20h | **`Decimal` com arredondamento explícito; valor da Orbe = TRUNCAR** (`ROUND_DOWN`) | `float`; centavos em `int`; arredondamento bancário | `float` erra centavo (os anexos já trazem 72214.46000000001). `Decimal` dá centavo exato e deixa o modo de arredondamento visível. Truncar é SEI (1.001 linhas só fecham truncando); arredondar geraria ~1.000 alarmes falsos de R$ 0,01 |
| D06 | 16/10 20h | Pacote em `src/` instalado em modo editável (`pip install -e .`) | rodar com `PYTHONPATH=src` | `python -m tarvo` funciona da raiz em qualquer terminal; o pytest acha o pacote pelo `pyproject.toml` |
| D07 | 16/10 20h40 | **Mapeamento manual de EC** (`cadastro.mapeamento_ec_confirmado` em `regras.yaml`) para os 3 ECs que a planilha não tem | inferir o lojista pelo nome ou pelo padrão de taxas | Não viola "nunca por semelhança de nome" (D03): é um vínculo explícito dado pelo cliente (Helena 20:24), registrado como dado com fonte. O código só faz busca exata nesse vínculo; EC fora dele continua sendo pendência |
| D08 | 16/10 20h40 | Status **PENDENTE** em `regras.yaml`, e `regras.py` recusa estrutura incoerente (PENDENTE com valor, SEI/ASSUMO/CONFIRMADO sem valor ou sem fonte) | `status: null` | Deixa explícito o que ninguém decidiu e impede que um valor entre sem fonte. Pedir o valor de uma regra PENDENTE gera erro, que vira pendência |
