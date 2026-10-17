"""Classificação determinística dos extratos por padrões de descrição (`classificacao_extratos` em `regras.yaml`).

Cada lançamento recebe a contrapartida da primeira regra do seu banco cujo padrão (regex
sobre a descrição normalizada) e sinal casam; as regras com `lojista: true` exigem que o
nome depois do padrão seja um lojista do cadastro (prefixo exato, D31) e as com
`mes_anterior: true` exigem que o mês citado seja o anterior à competência do extrato.
Nenhuma regra cita número de linha: o mesmo arquivo de regras serve para outubro.

O lado do lançamento vem do sinal do movimento (D12): saída → crédito no banco e débito na
contrapartida; entrada → o inverso. Linha sem regra → metodo HUMANO, conta vazia, pendência
SEM_REGRA (a IA tenta depois, em por_ia). Nada some.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from tarvo.cadastro import Cadastro, lojista_por_nome_bancario, normalizar_nome
from tarvo.modelo import ContaContabil, LancamentoBancario, Pendencia
from tarvo.regras import valor_da_regra


@dataclass
class ResultadoClassificacao:
    linhas: list[dict] = field(default_factory=list)
    rastro: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro_pendencias: list[dict] = field(default_factory=list)
    sem_regra: list[tuple[LancamentoBancario, str]] = field(default_factory=list)
    por_regra: dict[str, int] = field(default_factory=dict)
    lojista_por_lancamento: dict[tuple[str, str], str] = field(default_factory=dict)  # (banco, ref) → cnpj


def id_lancamento(banco: str, ref: str) -> str:
    return f"LAN-{banco}-{ref}"


def _mes_anterior(competencia: tuple[int, int]) -> str:
    ano, mes = competencia
    ano, mes = (ano - 1, 12) if mes == 1 else (ano, mes - 1)
    return f"{mes:02d}/{ano}"


def aliases_vigentes(regras: dict, banco: str, data: date) -> list[tuple[str, str]]:
    """(cnpj, nome) dos aliases aprovados para o banco com vigência até a data do lançamento (D44)."""
    if "classificacao_extratos.aliases_lojista" not in regras:
        return []
    return [(str(a["cnpj"]), a["nome"]) for a in valor_da_regra(regras, "classificacao_extratos.aliases_lojista")
            if banco in a["bancos"] and data >= date.fromisoformat(str(a["vigencia_inicio"]))]


def classificar_por_regra(
    lancamentos: list[LancamentoBancario],
    linhas_arquivo: dict[str, int],
    plano: dict[str, ContaContabil],
    regras: dict,
    cadastro: Cadastro,
    competencia: tuple[int, int],
) -> ResultadoClassificacao:
    """Classifica os lançamentos de um banco; `plano` = só as contas lançáveis."""
    contas_banco = valor_da_regra(regras, "extratos.conta_banco")
    res = ResultadoClassificacao()
    for lan in lancamentos:
        banco = lan.banco
        conta_banco = contas_banco[banco]
        prefixo = f"classificacao_extratos.{banco.lower()}."
        candidatas = [(k, r) for k, r in regras.items() if k.startswith(prefixo)]
        desc = normalizar_nome(lan.descricao)
        achou = None
        motivos: list[str] = []
        for chave, regra in candidatas:
            v = valor_da_regra(regras, chave)
            m = re.search(v["padrao"], desc)
            if not m:
                continue
            sinal_ok = (lan.valor > 0) if v["sinal"] == "+" else (lan.valor < 0)
            if not sinal_ok:
                motivos.append(f"{chave.rsplit('.', 1)[1]}: padrão casa mas o sinal não ({lan.valor})")
                continue
            if v.get("mes_anterior") and m.groupdict().get("mes") != _mes_anterior(competencia):
                motivos.append(f"{chave.rsplit('.', 1)[1]}: mês {m.groupdict().get('mes')} não é o anterior à competência "
                               f"({_mes_anterior(competencia)})")
                continue
            cnpj = None
            if v.get("lojista"):
                cnpj, motivo = lojista_por_nome_bancario(cadastro, m.group("lojista"), aliases_vigentes(regras, banco, lan.data))
                if cnpj is None:
                    motivos.append(f"{chave.rsplit('.', 1)[1]}: {motivo}")
                    continue
            achou = (chave, regra, v, cnpj)
            break

        ida = id_lancamento(banco, lan.ref_origem)
        linha_n = linhas_arquivo.get(lan.ref_origem, 0)
        if achou is None:
            motivo = "; ".join(motivos) or "nenhum padrão de classificacao_extratos casa com a descrição"
            res.sem_regra.append((lan, motivo))
            res.linhas.append(_linha(ida, lan, "", "HUMANO", None, "", "", conta_banco))
            pid = f"PEN-SEM_REGRA-{banco}-{lan.ref_origem}"
            res.pendencias.append(Pendencia(pid, "SEM_REGRA", lan.ref_origem, lan.valor,
                                            f"{banco} {lan.data.isoformat()} {lan.descricao!r}: sem regra ({motivo}); "
                                            f"vai para a IA (por_ia)", "analista (Lucca)"))
            res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha_n, "lançamento sem regra"))
        else:
            chave, regra, v, cnpj = achou
            if v["conta"] not in plano:
                raise ValueError(f"{chave}: conta {v['conta']} não existe ou não aceita lançamento")
            nome_regra = chave.split(".", 1)[1]
            res.por_regra[nome_regra] = res.por_regra.get(nome_regra, 0) + 1
            res.linhas.append(_linha(ida, lan, v["conta"], "REGRA", Decimal("1"), nome_regra, regra["status"], conta_banco))
            if cnpj:
                res.lojista_por_lancamento[(banco, lan.ref_origem)] = cnpj
            if v.get("pendencia"):
                pid = f"PEN-{nome_regra.rsplit('.', 1)[1].upper()}-{banco}-{lan.ref_origem}"
                res.pendencias.append(Pendencia(pid, nome_regra.rsplit(".", 1)[1].upper(), lan.ref_origem, lan.valor,
                                                f"{banco} {lan.data.isoformat()} {lan.descricao!r}: classificado em "
                                                f"{v['conta']}; {v['pendencia']}", "Helena"))
                res.rastro_pendencias.append(_rastro(pid, lan, lan.valor, linha_n, v["pendencia"]))
        res.rastro.append(_rastro(ida, lan, lan.valor, linha_n, f"lançamento {banco}"))
    return res


def _linha(ida, lan, conta, metodo, confianca, regra, status, conta_banco) -> dict:
    # D12: saída do banco → débito na contrapartida; entrada → crédito
    lado = "D" if lan.valor < 0 else "C"
    return {
        "id_saida": ida, "banco": lan.banco, "ref_origem": lan.ref_origem, "data": lan.data,
        "descricao": lan.descricao, "valor": lan.valor, "conta_codigo": conta, "metodo": metodo,
        "confianca": confianca, "regra_aplicada": regra, "status_regra": status,
        "contrapartida_banco": conta_banco, "lado_contrapartida": lado if conta else "",
        "sugestao_ia": "", "justificativa_ia": "",  # colunas fixas: preenchidas por por_ia quando a IA responde
    }


def _rastro(id_saida, lan, valor, linha, nota) -> dict:
    return {
        "id_saida": id_saida, "arquivo_origem": lan.arquivo_origem, "ref_origem": lan.ref_origem,
        "valor": valor, "linha_arquivo": linha, "tipo_lancamento": f"EXTRATO {lan.banco}", "nota": nota,
    }
