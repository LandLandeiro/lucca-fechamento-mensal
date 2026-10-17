"""Decisões humanas por linha (`decisoes_humanas` em `regras.yaml`): não são regras.

Cada decisão vale só para a linha exata (banco, ref_origem, data, descrição e valor iguais).
A linha sai com metodo HUMANO, a conta decidida, confiança vazia e `regra_aplicada` =
`decisoes_humanas.<chave>`; a pendência SEM_REGRA dela sai da lista. Decisão da competência que
não acha a sua linha vira aviso (nunca se aplica a outra linha). Roda antes da IA: linha
decidida não vai para a IA. Decisão com `substituida` (ex.: L28/L69, que a regra passou a cobrir na
D52) é histórico: não se aplica nem gera aviso.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from tarvo.cadastro import normalizar_nome
from tarvo.regras import valor_da_regra

PREFIXO = "decisoes_humanas."


def aplicar_decisoes_humanas(classif: list, regras: dict, competencia: tuple[int, int]) -> list[str]:
    """Aplica as decisões in place nos resultados de `classificar_por_regra`; devolve avisos."""
    decisoes = {k: valor_da_regra(regras, k) for k in regras if k.startswith(PREFIXO) and not regras[k].get("substituida")}
    usadas: set[str] = set()
    for c in classif:
        for lan, motivo in list(c.sem_regra):
            chave = next((k for k, v in decisoes.items()
                          if v["banco"] == lan.banco and v["ref_origem"] == lan.ref_origem
                          and date.fromisoformat(str(v["data"])) == lan.data
                          and normalizar_nome(v["descricao"]) == normalizar_nome(lan.descricao)
                          and Decimal(str(v["valor"])) == lan.valor), None)
            if chave is None:
                continue
            v = decisoes[chave]
            usadas.add(chave)
            c.sem_regra.remove((lan, motivo))
            linha = next(l for l in c.linhas if (l["banco"], l["ref_origem"]) == (lan.banco, lan.ref_origem))
            linha.update({"conta_codigo": v["conta"], "metodo": "HUMANO", "confianca": None,
                          "regra_aplicada": chave, "status_regra": regras[chave]["status"],
                          "lado_contrapartida": "D" if lan.valor < 0 else "C"})
            if v.get("lojista_cnpj"):
                c.lojista_por_lancamento[(lan.banco, lan.ref_origem)] = str(v["lojista_cnpj"])
            pid = f"PEN-SEM_REGRA-{lan.banco}-{lan.ref_origem}"
            c.pendencias = [p for p in c.pendencias if p.id_saida != pid]
            c.rastro_pendencias = [l for l in c.rastro_pendencias if l["id_saida"] != pid]
    avisos = []
    for k, v in sorted(decisoes.items()):
        d = date.fromisoformat(str(v["data"]))
        if (d.year, d.month) == competencia and k not in usadas:
            avisos.append(f"decisão {k} não achou a linha {v['banco']} {v['ref_origem']} ({v['data']}, {v['valor']}): não aplicada")
    return avisos
