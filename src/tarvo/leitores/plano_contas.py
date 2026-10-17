"""Leitor do plano de contas do ERP Fênix (`04_plano_de_contas_fenix_erp.csv`).

Armadilhas de leitura encontradas na exploração:
- Encoding Latin-1 (ISO-8859-1), não UTF-8; CRLF; separador `;`; cabeçalho na linha 1.
- Contas SINTETICA e ANALITICA; só ANALITICA com `ACEITA_LANCTO = S` pode receber lançamento.
- `COD_SUPERIOR` vazio nas contas de 1º nível.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from tarvo.leitores.orbe import ErroLeitura
from tarvo.modelo import ContaContabil

COLUNAS = ["COD_CONTA", "DESCRICAO", "TIPO", "NATUREZA", "ACEITA_LANCTO", "COD_SUPERIOR", "DT_CRIACAO"]


def ler_plano_contas(caminho: Path) -> list[ContaContabil]:
    """Lê todas as contas do plano."""
    texto = caminho.read_bytes().decode("latin-1")
    leitor = csv.reader(io.StringIO(texto, newline=""), delimiter=";")
    cab = next(leitor, None)
    if cab != COLUNAS:
        raise ErroLeitura(f"{caminho.name}: cabeçalho diferente do esperado: {cab}")
    contas = []
    for c in leitor:
        if not any(x.strip() for x in c):
            continue
        d = dict(zip(COLUNAS, (x.strip() for x in c)))
        contas.append(ContaContabil(
            codigo=d["COD_CONTA"], descricao=d["DESCRICAO"], tipo=d["TIPO"], natureza=d["NATUREZA"],
            aceita_lancamento=d["ACEITA_LANCTO"].upper() == "S", codigo_superior=d["COD_SUPERIOR"] or None,
        ))
    return contas


def contas_lancaveis(plano: list[ContaContabil]) -> dict[str, ContaContabil]:
    """Só ANALITICA com ACEITA_LANCTO = S (regra SEI plano_contas.contas_lancaveis)."""
    return {c.codigo: c for c in plano if c.tipo.upper() == "ANALITICA" and c.aceita_lancamento}
