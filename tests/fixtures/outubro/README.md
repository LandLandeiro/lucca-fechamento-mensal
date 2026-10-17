# DADO SINTÉTICO DE TESTE: não é dado real da Tarvo

Gerado por `tests/fixtures/gerar_outubro.py` a partir do data pack de setembro (`data/`), só para provar
que o fechamento roda em outubro sem mudar código (`tests/test_outubro.py`). As datas foram deslocadas
um mês (set → out), os identificadores com o mês foram renumerados, e há seis novidades:

1. um EC novo (1099000001, "ESCOLA NOVA INTERCAMBIO"), sem cadastro na planilha;
2. um estorno em 08/10 da venda TX88415459 da Bridge, de 05/09 (antes da taxa nova de 15/09);
3. no Meridiano, em 01/10, a TED de 300.000,00 de mesma titularidade (a transferência que estava em trânsito);
4. PIX recebidos "EDU ABROAD CONSULTORIA" (casam pelo nome da Orbe ligado ao EC);
5. um aporte da Nórdica com nome novo ("PIX RECEB NEI EDUCACAO INTERNACIONAL"), que vai para a IA;
6. a Atlas com contrato na planilha (linha nova, vigência a partir de 10/09/2026, taxas sintéticas).

Os valores e o plano de contas são os de setembro; a planilha de taxas é a de setembro mais a linha da Atlas. Não use estes números para nada além de teste.
