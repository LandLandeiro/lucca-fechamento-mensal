"""Regra aplicada em cada linha do rastro (D96, Q-AM): `saida/rastro_regras.csv`.

O `rastro.csv` diz de onde vem cada número; este arquivo diz por qual regra do `regras.yaml` ele foi calculado,
com o status e a fonte, sem mudar o formato do rastro. Uma linha do rastro pode ter mais de uma regra (ex.: o
estorno da Casa usa a regra do estorno e a condição especial). Determinístico: deriva do rastro e dos lançamentos já
calculados, na mesma ordem.

Colunas: id_saida; ref_origem; regra; status; fonte (a fonte resumida: o texto da regra antes da primeira citação;
a fala inteira está no `regras.yaml` e em docs/FINANCEIRO_SLACK.md).
"""

import csv
import re
from pathlib import Path

CABECALHO = ["id_saida", "ref_origem", "regra", "status", "fonte"]
SEM_REGRA = "(sem regra própria no regras.yaml)"

# tipo da pendência → regras que a produzem
POR_PENDENCIA = {
    "DIVERGENCIA_CHECKOUT": ["divergencias.pendencia_por_lojista", "divergencias.valor_a_devolver"],
    "DEVOLUCAO_CONCESSAO_COMERCIAL": ["cadastro.condicoes_especiais", "divergencias.valor_a_devolver"],
    "NF_NEGATIVA": ["notas.estrutura_nf_checkout"],
    "NOTA_BLOQUEADA": ["notas.nota_com_transacao_pendente"],
    "SEM_CONTRATO_VIGENTE": ["cadastro.lojista_sem_contrato_vigente", "cadastro.identificacao_sem_contrato"],
    "EC_SEM_CADASTRO": ["cadastro.mapeamento_ec_confirmado"],
    "ALERTA_ANTECIPACAO": ["checkout.alerta_antecipacao"],
    "CONFERENCIA_REPASSE": ["notas.conferencia_repasse"],
    "CONTESTACAO_PONTE": ["remessa.contestacao_ponte", "remessa.valor_contestado"],
    "EXCESSO_REMESSA": ["remessa.excesso_cobrado_na_remessa"],
    "AJUSTE_SEM_ORIGINAL": ["orbe.ajuste_sem_original"],
    "ID_REPETIDO_ORBE": ["orbe.id_repetido_entre_arquivos"],
    "AJUSTE_PONTE": ["remessa.ajuste_contestacao"],
    "SPREAD_NEGATIVO_SEM_TRAVA": ["remessa.spread_negativo_por_observacao"],
    "CADASTRO_REMESSA": ["remessa.cnpj_fora_da_planilha"],
    "ACOMPANHAMENTO_APORTE": ["classificacao_extratos.conferencias"],
}


def _regras_checkout(l: dict, nf: bool) -> list[str]:
    tipo, nota = l.get("tipo_lancamento") or "", l.get("nota") or ""
    base = {"VENDA": ["checkout.base_comissao"], "ESTORNO": ["checkout.estorno"],
            "ANTECIPACAO": ["checkout.composicao_comissao", "checkout.data_base_antecipacao"],
            "REVERSAO ANTECIPACAO": ["checkout.composicao_comissao"]}.get(tipo, [])
    if "condicoes_especiais[" in nota:
        base.append("cadastro.condicoes_especiais")
    if "fora dos arquivos" in nota:
        base.append("orbe.ajuste_sem_original")
    if (l.get("arquivo_origem") or "").startswith("06_"):
        base.append("orbe.ajustes_tardios")
    return base + (["notas.estrutura_nf_checkout"] if nf else [])


def _regras_remessa(l: dict, nf: bool) -> list[str]:
    nota = l.get("nota") or ""
    base = ["ponte.participacao_tarvo", "remessa.arredondamento_participacao"]
    if "liquidada em" in nota:
        base.append("remessa.liquidacao_no_mes_seguinte")
    if "RESSALVA" in nota.upper():
        base.append("remessa.status_aprovado_com_ressalva")
    return base + (["ponte.tomador_nf_remessa"] if nf else [])


def regras_da_linha(l: dict, regra_do_lancamento: dict[str, str]) -> list[str]:
    """Chaves do regras.yaml aplicadas numa linha do rastro (SEM_REGRA se nenhuma)."""
    ids = l["id_saida"]
    if ids.startswith("LAN-"):
        return [regra_do_lancamento.get(ids) or SEM_REGRA]
    if ids.startswith(("COM-", "NF-")):
        nf = ids.startswith("NF-")
        return _regras_remessa(l, nf) if ids.endswith("-REMESSA") else _regras_checkout(l, nf)
    if ids.startswith("DIV-"):
        if (l.get("tipo_lancamento") or "") == "REMESSA":
            return ["remessa.divergencia_spread", "remessa.formula_divergencia"]
        regras = ["divergencias.criterio_checkout"]
        if (l.get("tipo_lancamento") or "") == "ESTORNO":
            regras.append("divergencias.estorno_de_venda_divergente")
        return regras
    if ids == "EXC-REMESSA-DUPLICATA":
        return ["remessa.operacao_duplicada"]
    if ids.startswith("EXC-REMESSA-SPREAD_NEGATIVO"):
        return ["remessa.spread_negativo"]
    m = re.match(r"PEN-([A-Z_]+?)-", ids + "-")
    if m and m.group(1) in POR_PENDENCIA:
        return POR_PENDENCIA[m.group(1)]
    if ids.startswith(("PEN-AURORA", "PEN-MERIDIANO")) or (l.get("tipo_lancamento") or "").startswith("EXTRATO"):
        banco = "AURORA" if "aurora" in (l.get("arquivo_origem") or "") else "MERIDIANO"
        return [regra_do_lancamento.get(f"LAN-{banco}-{l['ref_origem']}") or SEM_REGRA]
    return [SEM_REGRA]


def _chave(regra: str, regras: dict) -> str:
    if regra in regras:
        return regra
    return f"classificacao_extratos.{regra}" if f"classificacao_extratos.{regra}" in regras else regra


def _fonte_curta(fonte: str) -> str:
    corte = min([i for i in (fonte.find("'"), fonte.find('"'), fonte.find("“")) if i >= 0] or [len(fonte)])
    curta = " ".join(fonte[:corte].replace(";", ",").split()).strip(" :(—-,")  # sem ';' dentro do campo (formato fixo)
    return (curta[:117] + "...") if len(curta) > 120 else curta


def linhas_rastro_regras(rastro: list[dict], lancamentos: list[dict], regras: dict) -> list[dict]:
    regra_do_lancamento = {l["id_saida"]: l.get("regra_aplicada") or "" for l in lancamentos}
    vistas, saida = set(), []
    for l in rastro:
        for r in regras_da_linha(l, regra_do_lancamento):
            chave = _chave(r, regras)
            k = (l["id_saida"], l["ref_origem"], chave)
            if k in vistas:
                continue
            vistas.add(k)
            info = regras.get(chave)
            saida.append({"id_saida": l["id_saida"], "ref_origem": l["ref_origem"], "regra": chave,
                          "status": info["status"] if info else "",
                          "fonte": _fonte_curta(str(info.get("fonte") or "")) if info else ""})
    return saida


def escrever_rastro_regras(saida: Path, linhas: list[dict]) -> Path:
    destino = saida / "rastro_regras.csv"
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CABECALHO, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    return destino
