"""Painel do fechamento: `saida/painel.html`, um arquivo único gerado da saída já pronta.

Responsabilidade: só leitura e apresentação. O painel lê `saida/*.csv`, `regras.yaml`, o rastro e
o data pack (sha256 de cada arquivo; `valor_taxa` da Orbe para a coluna "pela taxa aplicada") e não
calcula regra de negócio nova: todo valor exibido é uma soma de linhas da saída (Decimal) e o rastro
inteiro vai embutido como JSON para a busca.

Campos que a main ainda pode não ter (`natureza`, pendências `ALERTA_*`, `saida/rascunhos/`) são
opcionais: sem eles a seção some. Mapeamento de pendência → destino do dinheiro e → coluna do kanban:
`docs/PAINEL.md`. Determinístico: sem data/hora e sem hash de commit; a versão é o sha256 dos insumos.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tarvo.regras import carregar_regras

AQUI = Path(__file__).resolve().parent
ZERO = Decimal("0")
CNPJ_RE = re.compile(r"(?<!\d)(\d{14})(?!\d)")
REGRA_NA_NOTA_RE = re.compile(r"regras\.yaml ([a-z_]+(?:\.[a-z_]+)+)")

# coluna do valor reportado em cada CSV de saída (a primeira que existir)
COLUNAS_VALOR = ("comissao_brl", "diferenca_brl", "valor_brl", "valor")

# ---------------------------------------------------------------------------
# Mapeamentos (docs/PAINEL.md). Tipos são a lista de pendencias.csv; tipo novo cai em "outras".
# ---------------------------------------------------------------------------

GRUPOS = (  # (chave, rótulo, descrição)
    ("devolver_lojista", "Devolver ao lojista", "a Orbe cobrou acima do contrato: o lojista já recebeu a menos (Q-U 4)"),
    ("recuperar_orbe", "Recuperar da Orbe", "só o que a Orbe cobrou contra o contrato que ela conhecia (natureza contrato_orbe)"),
    ("repasse_devolvido", "Repasse que voltou", "PIX de repasse devolvido pelo banco: refazer quando o motivo for apurado"),
    ("contestar_ponte", "Contestar com a Ponte", "relatório da Ponte com valor que o fechamento não aceita"),
    ("receita_parada", "Receita parada", "comissão que não vira nota"),
    ("sem_origem", "Sem origem", "entrada ou lançamento sem dono identificado"),
    ("em_transito", "Em trânsito", "dinheiro que chega depois; conferir no mês seguinte"),
    ("outras", "Outras pendências", "tipo sem destino mapeado"),
)
GRUPO_POR_TIPO = {
    "DIVERGENCIA_CHECKOUT": "devolver_lojista",  # toda divergência de checkout (Q-A, Q-U 4); a natureza só decide o "recuperar"
    "DEVOLUCAO_PIX_LOJISTA": "repasse_devolvido",
    "CONTESTACAO_PONTE": "contestar_ponte",
    "EXCESSO_REMESSA": "contestar_ponte",
    "SPREAD_NEGATIVO_SEM_TRAVA": "contestar_ponte",
    "SEM_CONTRATO_VIGENTE": "receita_parada",
    "NF_NEGATIVA": "receita_parada",
    "NOTA_BLOQUEADA": "receita_parada",
    "PIX_SEM_IDENTIFICACAO": "sem_origem",
    "TRANSFERENCIA_SEM_ORIGEM": "sem_origem",
    "SEM_REGRA": "sem_origem",
    "IA_REPROVADA": "sem_origem",
    "TRANSFERENCIA_EM_TRANSITO": "em_transito",
    "APORTE_SEM_OPERACAO": "em_transito",
    "CONFERENCIA_REPASSE": "em_transito",
}
# natureza (divergencias_taxa.csv, D63) que a Tarvo recupera da Orbe; o mesmo valor volta ao lojista, por isso não soma
NATUREZA_RECUPERAR = "contrato_orbe"
NAO_SOMA_RECUPERAR = "não soma: é o mesmo valor que volta ao lojista"
# rótulo do valor quando ele não é o que o título sugere
ROTULO_VALOR = {"SEM_CONTRATO_VIGENTE": "taxa cobrada pela Orbe (referência); comissão a definir pelo comercial"}

# não somam ao total (o valor já está em outro número, ou é dinheiro que ainda vai chegar)
NAO_SOMA = {
    "TRANSFERENCIA_EM_TRANSITO": "em trânsito entre contas próprias",
    "APORTE_SEM_OPERACAO": "aporte do lojista para remessa futura",
    "CONFERENCIA_REPASSE": "já está na nota de remessa",
    "EXCESSO_REMESSA": "é a metade da Tarvo dentro do valor contestado",
}

COLUNAS_KANBAN = (  # (chave, rótulo); o rótulo da 1ª usa o nome de quem fecha (regras.yaml)
    ("dona", "Com {dona}"),
    ("comercial", "Com o comercial"),
    ("contraparte", "Com uma contraparte"),
    ("acompanhar", "Acompanhar"),
    ("regra", "Fechadas por regra"),
)
COLUNA_POR_TIPO = {
    "CONTESTACAO_PONTE": "contraparte",
    "EXCESSO_REMESSA": "contraparte",
    "TRANSFERENCIA_EM_TRANSITO": "acompanhar",
    "CONFERENCIA_REPASSE": "acompanhar",
    "APORTE_SEM_OPERACAO": "acompanhar",
}

TITULOS = {
    "DIVERGENCIA_CHECKOUT": "Taxa do checkout diferente do contrato",
    "CONTESTACAO_PONTE": "Contestação com a Ponte",
    "EXCESSO_REMESSA": "Metade da Tarvo no spread cobrado a mais",
    "SEM_CONTRATO_VIGENTE": "Lojista sem contrato vigente: não fatura",
    "NF_NEGATIVA": "Comissão do mês negativa: sem nota",
    "NOTA_BLOQUEADA": "Nota bloqueada por transação pendente",
    "PIX_SEM_IDENTIFICACAO": "PIX recebido sem identificação",
    "DEVOLUCAO_PIX_LOJISTA": "PIX de repasse devolvido",
    "TRANSFERENCIA_EM_TRANSITO": "Transferência entre contas em trânsito",
    "APORTE_SEM_OPERACAO": "Aporte de lojista sem operação de câmbio",
    "CONFERENCIA_REPASSE": "Conferir o repasse da Ponte quando cair",
    "ALERTA_ANTECIPACAO": "Antecipação acima do que o lojista vendeu",
    "PROVISAO_DO_MES": "Provisão de folha e impostos do mês",
}
SUBTITULOS = {  # sufixo do id_saida
    "DUPLICATA": "operação repetida no relatório",
    "SPREAD_NEGATIVO": "spread negativo",
    "SPREAD_ACIMA_DO_CONTRATADO": "spread acima do contratado",
}
TITULO_NATUREZA = {"condicao_nao_informada": "Condição não informada à Orbe: devolver ao lojista",
                   "contrato_orbe": "Orbe cobrou acima do contrato: devolver e recuperar"}

# regra de cada número de saída (chave do regras.yaml); a nota do rastro, quando cita o regras.yaml, é mais específica
REGRA_POR_TIPO_PENDENCIA = {
    "DIVERGENCIA_CHECKOUT": "divergencias.valor_a_devolver",
    "ALERTA_ANTECIPACAO": "checkout.alerta_antecipacao",
    "PROVISAO_DO_MES": "contabil.provisao_do_mes",
    "CONTESTACAO_PONTE": "remessa.contestacao_ponte",
    "EXCESSO_REMESSA": "remessa.excesso_cobrado_na_remessa",
    "NF_NEGATIVA": "notas.estrutura_nf_checkout",
    "NOTA_BLOQUEADA": "notas.nota_com_transacao_pendente",
    "SEM_CONTRATO_VIGENTE": "cadastro.lojista_sem_contrato_vigente",
    "CONFERENCIA_REPASSE": "notas.conferencia_repasse",
    "TRANSFERENCIA_EM_TRANSITO": "classificacao_extratos.conferencias",
    "APORTE_SEM_OPERACAO": "classificacao_extratos.conferencias",
    "PIX_SEM_IDENTIFICACAO": "classificacao_extratos.aurora.pix_sem_identificacao",
    "DEVOLUCAO_PIX_LOJISTA": "classificacao_extratos.aurora.devolucao_pix_lojista",
    "SPREAD_NEGATIVO_SEM_TRAVA": "remessa.spread_negativo_por_observacao",
}
REGRA_POR_EXCLUSAO = {"DUPLICATA": "remessa.operacao_duplicada", "SPREAD_NEGATIVO": "remessa.spread_negativo"}

ROTULO_ARQUIVO = {
    "comissoes_por_lojista.csv": "Comissão por lojista",
    "divergencias_taxa.csv": "Divergências de taxa",
    "notas_a_emitir.csv": "Notas a emitir",
    "lancamentos_classificados.csv": "Lançamentos classificados",
    "pendencias.csv": "Pendências",
    "rastro.csv": "Rastro",
    "contestacao_ponte.csv": "Contestação da Ponte (anexo)",
    "sugestoes_regra.csv": "Sugestões de regra",
}


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


def _ler_csv(caminho: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not caminho.exists():
        return [], []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f, delimiter=";")
        return list(leitor.fieldnames or []), [dict(l) for l in leitor]


def _dec(texto: str | None) -> Decimal | None:
    if texto is None or str(texto).strip() == "":
        return None
    try:
        return Decimal(str(texto).strip())
    except InvalidOperation:
        return None


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


@dataclass
class Pendencia:
    id: str
    tipo: str
    refs: list[str]
    valor: Decimal | None
    motivo: str
    quem_decide: str
    natureza: str = ""
    grupo: str = "outras"
    coluna: str = "dona"
    soma: bool = True
    nao_soma_motivo: str = ""
    titulo: str = ""
    contraparte: str = ""
    alerta: bool = False
    devolver: Decimal | None = None  # DIVERGENCIA_CHECKOUT: Σ valor_a_devolver_brl das transações (fallback: valor_brl)
    recuperar: Decimal = ZERO  # parte de natureza contrato_orbe
    rotulo_valor: str = ""


@dataclass
class Painel:
    competencia: str = ""
    dona: str = ""
    notas: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    regras: dict[str, dict] = field(default_factory=dict)
    arquivos_saida: list[tuple[str, int]] = field(default_factory=list)
    rascunhos: list[str] = field(default_factory=list)
    insumos: list[tuple[str, str, int]] = field(default_factory=list)
    rastro_cab: list[str] = field(default_factory=list)
    rastro: list[dict[str, str]] = field(default_factory=list)
    saidas: dict[str, dict] = field(default_factory=dict)  # id_saida → arquivo, valor reportado, Σ rastro, linhas, regra
    fechadas: list[dict] = field(default_factory=list)
    lojistas: list[dict] = field(default_factory=list)
    remessa: list[dict] = field(default_factory=list)
    residuo: Decimal | None = None
    nomes: dict[str, str] = field(default_factory=dict)
    hipoteses: dict = field(default_factory=dict)


def _nomes_por_cnpj(saida: Path) -> dict[str, str]:
    nomes: dict[str, str] = {}
    for arquivo, col_cnpj, col_nome in (
        ("comissoes_por_lojista.csv", "cnpj", "lojista"),
        ("notas_a_emitir.csv", "tomador_cnpj", "tomador"),
        ("divergencias_taxa.csv", "cnpj", "lojista"),
        ("contestacao_ponte.csv", "cnpj", "lojista"),
    ):
        for l in _ler_csv(saida / arquivo)[1]:
            if l.get(col_cnpj) and l.get(col_nome):
                nomes.setdefault(l[col_cnpj], l[col_nome])
    return nomes


def _dona(regras: dict[str, dict], pendencias: list[dict[str, str]]) -> str:
    """Quem fecha: o `quem_decide` das pendências por lojista no regras.yaml; senão o mais frequente."""
    regra = regras.get("divergencias.pendencia_por_lojista")
    if regra and isinstance(regra.get("valor"), dict) and regra["valor"].get("quem_decide"):
        return str(regra["valor"]["quem_decide"])
    simples = Counter(p["quem_decide"] for p in pendencias if p.get("quem_decide") and " " not in p["quem_decide"].strip())
    return simples.most_common(1)[0][0] if simples else ""


def _classificar(p: Pendencia, dona: str, natureza_por_ref: dict[str, str], nomes: dict[str, str], ponte: str,
                 lojistas_extra: list[str]) -> None:
    tipo = p.tipo.upper()
    p.alerta = tipo.startswith("ALERTA")
    if not p.natureza and tipo == "DIVERGENCIA_CHECKOUT":
        vistas = sorted({natureza_por_ref[r] for r in p.refs if r in natureza_por_ref})
        p.natureza = vistas[0] if len(vistas) == 1 else ""
    p.grupo = GRUPO_POR_TIPO.get(tipo, "outras")
    p.rotulo_valor = ROTULO_VALOR.get(tipo, "")
    if p.alerta:
        p.grupo = ""
        p.soma, p.nao_soma_motivo = False, "alerta: informativo"
    elif tipo in NAO_SOMA:
        p.soma, p.nao_soma_motivo = False, NAO_SOMA[tipo]
    elif p.valor is None:
        p.soma, p.nao_soma_motivo = False, "sem valor"

    quem = p.quem_decide.lower()
    if tipo in COLUNA_POR_TIPO:
        p.coluna = COLUNA_POR_TIPO[tipo]
    elif dona and dona.lower() in quem:
        p.coluna = "dona"
    elif "comercial" in quem:
        p.coluna = "comercial"
    elif "analista" in quem or "conferir" in quem:
        p.coluna = "acompanhar"
    else:
        p.coluna = "dona"

    sufixo = next((s for s in SUBTITULOS if p.id.upper().split("-", 2)[-1].startswith(s)), None)
    titulo = TITULO_NATUREZA.get(p.natureza) or TITULOS.get(tipo) or tipo.replace("_", " ").capitalize()
    if sufixo and tipo == "CONTESTACAO_PONTE":
        titulo = f"{titulo}: {SUBTITULOS[sufixo]}"
    p.titulo = titulo

    partes = []
    if p.recuperar:
        partes.append("Orbe")
    if p.grupo == "contestar_ponte" or tipo == "CONFERENCIA_REPASSE":
        partes.append(ponte or "Ponte")
    m = CNPJ_RE.search(p.id)
    if m:
        partes.append(nomes.get(m.group(1), m.group(1)))
    m_ec = re.search(r"EC(\d+)", p.id)
    if m_ec:
        partes.append(f"EC {m_ec.group(1)}")
    for banco in ("AURORA", "MERIDIANO"):
        if f"-{banco}-" in p.id:
            partes.append(banco.capitalize())
    if not m:
        partes.extend(lojistas_extra)
    p.contraparte = " · ".join(dict.fromkeys(partes)) or "—"


def _sem_markdown(texto: str) -> str:
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    return " ".join(texto.replace("**", "").replace("~~", "").replace("`", "").split())


def ler_hipoteses(caminho: Path) -> dict:
    """`HIPOTESES.md`: a frase de contagem do Resumo e as linhas da tabela de Premissas (H01…), com o status da coluna 4.

    A tabela do Histórico (substituídas) é contada à parte. Arquivo ausente → {} (a seção usa o regras.yaml)."""
    if not caminho.exists():
        return {}
    secao, resumo, linhas, substituidas = "", "", [], 0
    for bruta in caminho.read_text(encoding="utf-8").splitlines():
        if bruta.startswith("## "):
            secao = bruta[3:].strip().lower()
            continue
        if secao == "resumo" and not resumo and re.match(r"-\s+\*\*\d+ premissas", bruta):
            resumo = _sem_markdown(bruta.lstrip("- ")).split(" As H")[0]
        if not re.match(r"\|\s*H\d+", bruta):
            continue
        celulas = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", bruta.strip().strip("|"))]
        if secao.startswith("histórico"):
            substituidas += 1
        elif secao == "premissas" and len(celulas) >= 7:
            status_txt = _sem_markdown(celulas[3])
            linhas.append({"id": celulas[0], "tema": _sem_markdown(celulas[1]), "premissa": _sem_markdown(celulas[2]),
                           "status": status_txt.split(" ")[0], "status_txt": status_txt, "base": _sem_markdown(celulas[4]),
                           "impacto": _sem_markdown(celulas[5])})
    contagem_resumo = {st: int(n) for n, st in re.findall(r"(\d+) (CONFIRMADO|ASSUMO|SEI|PENDENTE)", resumo)}
    m_sub = re.search(r"(\d+) substitu", resumo)
    m_tot = re.search(r"(\d+) premissas", resumo)
    return {"arquivo": caminho.name, "resumo": resumo, "contagem_resumo": contagem_resumo,
            "substituidas_resumo": int(m_sub.group(1)) if m_sub else None, "total_resumo": int(m_tot.group(1)) if m_tot else None,
            "linhas": linhas, "substituidas": substituidas}


def carregar(saida: Path, dados: Path, regras_path: Path, hipoteses_path: Path | None = None) -> Painel:
    pn = Painel()
    pn.regras = carregar_regras(regras_path)
    pn.hipoteses = ler_hipoteses(hipoteses_path or regras_path.parent / "HIPOTESES.md")
    pn.nomes = _nomes_por_cnpj(saida)

    _, notas = _ler_csv(saida / "notas_a_emitir.csv")
    pn.notas = notas
    comps = sorted({n.get("competencia", "") for n in notas if n.get("competencia")})
    pn.competencia = comps[0] if len(comps) == 1 else " · ".join(comps)

    _, pend = _ler_csv(saida / "pendencias.csv")
    pn.dona = _dona(pn.regras, pend)
    _, divs = _ler_csv(saida / "divergencias_taxa.csv")
    natureza_por_ref = {d["ref_origem"]: d["natureza"] for d in divs if d.get("natureza")}
    div_checkout = {d["ref_origem"]: d for d in divs if d.get("linha_negocio") == "CHECKOUT"}
    tem_devolver = bool(divs) and "valor_a_devolver_brl" in divs[0]
    ponte_regra = pn.regras.get("ponte.tomador_nf_remessa", {}).get("valor") or {}
    ponte = ponte_regra.get("nome", "") if isinstance(ponte_regra, dict) else ""
    # lojistas de uma pendência sem CNPJ no id (ex.: contestação de duplicata): pelo anexo da contestação
    lojistas_por_pend: dict[str, set[str]] = defaultdict(set)
    for c in _ler_csv(saida / "contestacao_ponte.csv")[1]:
        if c.get("id_pendencia") and c.get("cnpj"):
            lojistas_por_pend[c["id_pendencia"]].add(pn.nomes.get(c["cnpj"], c["cnpj"]))
    for l in pend:
        p = Pendencia(
            id=l["id_saida"], tipo=l.get("tipo", ""), refs=[r for r in (l.get("ref_origem") or "").split("|") if r],
            valor=_dec(l.get("valor_brl")), motivo=l.get("motivo", ""), quem_decide=l.get("quem_decide", ""),
            natureza=l.get("natureza", "") or "",
        )
        if p.tipo.upper() == "DIVERGENCIA_CHECKOUT":
            linhas_div = [div_checkout[r] for r in p.refs if r in div_checkout]
            if tem_devolver and linhas_div:
                p.devolver = sum((_dec(d.get("valor_a_devolver_brl")) or ZERO for d in linhas_div), ZERO)
                p.recuperar = sum((_dec(d.get("valor_a_devolver_brl")) or ZERO for d in linhas_div
                                   if d.get("natureza") == NATUREZA_RECUPERAR), ZERO)
            else:
                p.devolver = p.valor
        _classificar(p, pn.dona, natureza_por_ref, pn.nomes, ponte, sorted(lojistas_por_pend.get(p.id, ())))
        pn.pendencias.append(p)

    pn.arquivos_saida = [(c.name, max(sum(1 for _ in open(c, encoding="utf-8")) - 1, 0)) for c in sorted(saida.glob("*.csv"))]
    pasta_rasc = saida / "rascunhos"
    if pasta_rasc.is_dir():
        pn.rascunhos = sorted(c.relative_to(saida).as_posix() for c in pasta_rasc.rglob("*") if c.is_file())
    if dados.is_dir():
        pn.insumos = [(c.name, _sha256(c)[:12], c.stat().st_size) for c in sorted(dados.iterdir()) if c.is_file()]
    for extra in (regras_path, hipoteses_path or regras_path.parent / "HIPOTESES.md"):
        if extra.exists():
            pn.insumos.append((extra.name, _sha256(extra)[:12], extra.stat().st_size))

    pn.rastro_cab, pn.rastro = _ler_csv(saida / "rastro.csv")
    _montar_saidas(pn, saida)
    _montar_fechadas(pn, saida)
    _montar_lojistas(pn, dados, divs)
    return pn


def _montar_saidas(pn: Painel, saida: Path) -> None:
    soma: dict[str, Decimal] = defaultdict(lambda: ZERO)
    linhas: Counter = Counter()
    for r in pn.rastro:
        soma[r["id_saida"]] += _dec(r.get("valor")) or ZERO
        linhas[r["id_saida"]] += 1
    reportado: dict[str, tuple[str, str]] = {}
    lanc_regra: dict[str, str] = {}
    pend_tipo = {p.id: p.tipo.upper() for p in pn.pendencias}
    div_linha: dict[str, dict] = {}
    for caminho in sorted(saida.glob("*.csv")):
        if caminho.name == "rastro.csv":
            continue
        cab, linhas_csv = _ler_csv(caminho)
        col = next((c for c in COLUNAS_VALOR if c in cab), None)
        if "id_saida" not in cab or not col:
            continue
        for l in linhas_csv:
            reportado.setdefault(l["id_saida"], (caminho.name, l.get(col, "")))
            if caminho.name == "lancamentos_classificados.csv":
                if l.get("metodo") == "REGRA" and l.get("regra_aplicada"):
                    lanc_regra[l["id_saida"]] = f"classificacao_extratos.{l['regra_aplicada']}"
                elif l.get("metodo") == "IA":
                    lanc_regra[l["id_saida"]] = "classificacao.uso_ia"
            if caminho.name == "divergencias_taxa.csv":
                div_linha[l["id_saida"]] = l
    for ident in sorted(set(soma) | set(reportado)):
        arquivo, valor = reportado.get(ident, ("rastro.csv", ""))
        pn.saidas[ident] = {
            "arquivo": arquivo,
            "reportado": valor,
            "soma": str(soma.get(ident, ZERO)),
            "linhas": linhas.get(ident, 0),
            "confere": (_dec(valor) == soma.get(ident, ZERO)) if _dec(valor) is not None else None,
            "regra": _regra_da_saida(ident, pend_tipo, lanc_regra, div_linha, pn.regras),
        }


def _regra_da_saida(ident: str, pend_tipo, lanc_regra, div_linha, regras) -> str:
    chave = ""
    if ident in pend_tipo:
        chave = REGRA_POR_TIPO_PENDENCIA.get(pend_tipo[ident], "")
    elif ident in lanc_regra:
        chave = lanc_regra[ident]
    elif ident.startswith("COM-"):
        chave = "checkout.base_comissao" if ident.endswith("-CHECKOUT") else "ponte.participacao_tarvo"
    elif ident.startswith("NF-"):
        chave = "notas.estrutura_nf_checkout" if ident.endswith("-CHECKOUT") else "ponte.tomador_nf_remessa"
    elif ident in div_linha:
        d = div_linha[ident]
        if d.get("linha_negocio") == "CHECKOUT":
            chave = "divergencias.criterio_checkout"
        elif d.get("natureza") == "spread_negativo" or (d.get("direcao") == "COBROU_A_MENOS"):
            chave = "remessa.divergencia_spread_negativo"
        else:
            chave = "remessa.formula_divergencia"
    elif ident.startswith("EXC-"):
        chave = next((v for k, v in REGRA_POR_EXCLUSAO.items() if ident.upper().endswith(k)), "")
    return chave if chave in regras else ""


def _montar_fechadas(pn: Painel, saida: Path) -> None:
    """Coluna "Fechadas por regra": o que o sistema decidiu sozinho. Um cartão por grupo:
    classificação de cada extrato (as regras dele, com contagem e um exemplo), cada exclusão EXC-* e cada condição especial."""
    _, lancs = _ler_csv(saida / "lancamentos_classificados.csv")
    por_banco: dict[str, dict[str, dict]] = defaultdict(dict)
    for l in lancs:
        if l.get("metodo") not in ("REGRA", "IA"):
            continue
        chave = pn.saidas.get(l["id_saida"], {}).get("regra", "")
        if not chave:
            continue
        banco = (l.get("banco") or "").capitalize() if l.get("metodo") == "REGRA" else "IA"
        r = por_banco[banco].setdefault(chave, {"regra": chave, "qtd": 0, "valor": ZERO, "exemplo": l["id_saida"]})
        r["qtd"] += 1
        r["valor"] += _dec(l.get("valor")) or ZERO
    cartoes = []
    for banco, regras in sorted(por_banco.items()):
        itens = sorted(regras.values(), key=lambda r: (-r["qtd"], r["regra"]))
        qtd = sum(r["qtd"] for r in itens)
        titulo = (f"Extrato {banco}: {qtd} lançamentos classificados por {len(itens)} {'regra' if len(itens) == 1 else 'regras'}"
                  if banco != "IA" else f"{qtd} lançamentos classificados pela IA e conferidos pelo código")
        cartoes.append({"tipo": "classificacao", "titulo": titulo, "regra": "", "qtd": qtd, "regras": itens,
                        "valor": sum((r["valor"] for r in itens), ZERO), "exemplo": itens[0]["exemplo"]})
    for ident, s in sorted(pn.saidas.items()):
        if ident.startswith("EXC-"):
            cartoes.append({"tipo": "exclusao", "regra": s["regra"], "qtd": s["linhas"], "valor": Decimal(s["soma"]), "exemplo": ident,
                            "titulo": "Fora da comissão por regra: " + ident.split("-", 2)[-1].replace("_", " ").lower(), "regras": []})
    especiais: dict[str, dict] = {}
    for r in pn.rastro:
        m = re.search(r"regras\.yaml (cadastro\.condicoes_especiais)\[([^\]]+)\]", r.get("nota", ""))
        if m and r["id_saida"].startswith("COM-"):
            g = especiais.setdefault(m.group(2), {"tipo": "condicao", "regra": m.group(1), "qtd": 0, "valor": ZERO,
                                                  "exemplo": r["ref_origem"], "regras": [],
                                                  "titulo": f"Condição especial aplicada: {m.group(2)}"})
            g["qtd"] += 1
            g["valor"] += _dec(r.get("valor")) or ZERO
    pn.fechadas = cartoes + [especiais[k] for k in sorted(especiais)]


def _montar_lojistas(pn: Painel, dados: Path, divs: list[dict]) -> None:
    """Contratado × cobrado (checkout): comissão pela planilha (saída) × taxa que a Orbe cobrou (data pack)."""
    por_saida: dict[str, list[dict]] = defaultdict(list)
    for r in pn.rastro:
        por_saida[r["id_saida"]].append(r)
    arquivo_orbe = next((r["arquivo_origem"] for i, rs in por_saida.items() if i.startswith("COM-") and i.endswith("-CHECKOUT") for r in rs), "")
    taxa_orbe: dict[str, Decimal] = {}
    nome_orbe: dict[str, Counter] = defaultdict(Counter)
    if arquivo_orbe and (dados / arquivo_orbe).exists():
        from tarvo.leitores.orbe import ler_orbe

        for t in ler_orbe(dados / arquivo_orbe).transacoes:
            taxa_orbe[t.ref_origem] = t.valor_taxa
            nome_orbe[t.cod_estabelecimento][t.nome_estabelecimento] += 1
    div_cnpj: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for d in divs:
        if d.get("linha_negocio") == "CHECKOUT":
            div_cnpj[d["cnpj"]] += _dec(d.get("diferenca_brl")) or ZERO

    def linha(ident: str, cnpj: str, nome: str, planilha: Decimal | None, situacao: str | None) -> dict:
        rs = por_saida.get(ident, [])
        vendas = [r for r in rs if r.get("tipo_lancamento") == "VENDA"]
        aplicada = sum((taxa_orbe[r["ref_origem"]] for r in rs if r["ref_origem"] in taxa_orbe), ZERO) if taxa_orbe else None
        diferenca = aplicada - planilha if (aplicada is not None and planilha is not None) else None
        div = div_cnpj.get(cnpj, ZERO)
        if situacao is None:
            situacao = "com_diferenca" if div != 0 else "confere"
        return {"id": ident, "cnpj": cnpj, "nome": nome, "vendas": len(vendas),
                "volume": sum((_dec(r.get("valor_bruto")) or ZERO for r in vendas), ZERO),
                "planilha": planilha, "aplicada": aplicada, "diferenca": diferenca, "divergencia": div, "situacao": situacao}

    for ident, s in pn.saidas.items():
        if ident.startswith("COM-") and ident.endswith("-CHECKOUT") and s["arquivo"] == "comissoes_por_lojista.csv":
            cnpj = ident[len("COM-"):-len("-CHECKOUT")]
            pn.lojistas.append(linha(ident, cnpj, pn.nomes.get(cnpj, cnpj), _dec(s["reportado"]), None))
    for p in pn.pendencias:
        if p.tipo.upper() == "SEM_CONTRATO_VIGENTE":
            m = re.search(r"EC(\d+)", p.id)
            ec = m.group(1) if m else ""
            nome = nome_orbe[ec].most_common(1)[0][0] if nome_orbe.get(ec) else (f"EC {ec}" if ec else p.id)
            pn.lojistas.append(linha(p.id, "", f"{nome} (EC {ec})" if ec else nome, None, "sem_contrato"))
    pn.lojistas.sort(key=lambda l: (-(l["divergencia"]), l["nome"]))

    # remessa (Ponte): spread realizado e comissão pela saída; divergência = lojista pagou spread ≠ contratado
    # spread negativo é outra natureza (Helena 09:44, Q-O: "o lojista não pagou a mais"): coluna à parte, nunca "com diferença"
    div_rem: dict[str, Decimal] = defaultdict(lambda: ZERO)
    negativo: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for d in divs:
        if d.get("linha_negocio") == "REMESSA" and d.get("cnpj"):
            e_negativo = d.get("natureza") == "spread_negativo" or (not d.get("natureza") and (_dec(d.get("spread_brl")) or ZERO) < 0)
            if e_negativo:
                negativo[d["cnpj"]] += _dec(d.get("spread_brl")) or ZERO
            else:
                div_rem[d["cnpj"]] += _dec(d.get("diferenca_brl")) or ZERO
    for ident, s in pn.saidas.items():
        if ident.startswith("COM-") and ident.endswith("-REMESSA") and s["arquivo"] == "comissoes_por_lojista.csv":
            cnpj = ident[len("COM-"):-len("-REMESSA")]
            rs = por_saida.get(ident, [])
            div = div_rem.get(cnpj, ZERO)
            pn.remessa.append({"id": ident, "cnpj": cnpj, "nome": pn.nomes.get(cnpj, cnpj), "operacoes": len(rs),
                               "spread": sum((_dec(r.get("spread_brl")) or ZERO for r in rs), ZERO),
                               "comissao": _dec(s["reportado"]), "divergencia": div, "negativo": negativo.get(cnpj, ZERO),
                               "situacao": "com_diferenca" if div != 0 else ("spread_negativo" if negativo.get(cnpj) else "confere")})
    pn.remessa.sort(key=lambda l: (-(abs(l["divergencia"])), l["negativo"], l["nome"]))
    if taxa_orbe:
        com_ids = [i for i in pn.saidas if i.startswith("COM-") and i.endswith("-CHECKOUT")]
        soma_vt = sum((taxa_orbe.get(r["ref_origem"], ZERO) for i in com_ids for r in por_saida[i]), ZERO)
        soma_com = sum((_dec(r.get("valor")) or ZERO for i in com_ids for r in por_saida[i]), ZERO)
        soma_div = sum(div_cnpj.values(), ZERO)
        pn.residuo = soma_vt - soma_com - soma_div


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------


def em_jogo(pendencias) -> Decimal:
    """Dinheiro em jogo: Σ |valor_brl| (direções diferentes não se compensam: o spread negativo não abate o cobrado a mais)."""
    return sum((abs(p.valor) for p in pendencias if p.valor is not None), ZERO)


def _e(texto) -> str:
    return html.escape(str(texto), quote=True)


def brl(valor: Decimal | None, sinal: bool = False) -> str:
    if valor is None:
        return "—"
    q = valor.quantize(Decimal("0.01"))
    inteiro, _, cent = f"{abs(q):.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    texto = f"R$ {'.'.join(grupos)},{cent}"
    if q < 0:
        return "−" + texto
    return ("+" + texto) if (sinal and q > 0) else texto


def _num(valor: Decimal | None) -> str:
    return "" if valor is None else f"{valor.quantize(Decimal('0.01'))}"


def _cnpj_fmt(c: str) -> str:
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}" if len(c) == 14 and c.isdigit() else c


def _resumo_valor(valor, limite: int = 240) -> str:
    if isinstance(valor, dict):
        texto = "; ".join(f"{k}: {_resumo_valor(v, limite)}" for k, v in valor.items())
    elif isinstance(valor, list):
        texto = ", ".join(_resumo_valor(v, limite) for v in valor)
    else:
        texto = str(valor)
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def _refs_curtas(refs: list[str]) -> str:
    if not refs:
        return "—"
    return refs[0] if len(refs) == 1 else f"{refs[0]} +{len(refs) - 1}"


ICONES = {
    "visao": '<path d="M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z"/>',
    "decisoes": '<rect x="3" y="4" width="5" height="16" rx="1"/><rect x="10" y="4" width="5" height="11" rx="1"/><rect x="17" y="4" width="4" height="7" rx="1"/>',
    "contratado": '<path d="M12 3v18M5 7h14M5 7l-3 7a4 4 0 0 0 6 0zM19 7l-3 7a4 4 0 0 0 6 0z"/>',
    "notas": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
    "alerta": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01"/>',
    "arquivo": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>',
    "seta": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "busca": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
}


def _icone(nome: str, classe: str = "ic") -> str:
    return (f'<svg class="{classe}" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONES[nome]}</svg>')


def _link_rastro(ident: str, texto: str = "Rastro") -> str:
    return f'<a class="link-rastro" href="#notas?id={_e(ident)}">{_icone("seta", "ic ic-s")}{_e(texto)}</a>'


STATUS_CLASSE = {"SEI": "st-sei", "ASSUMO": "st-assumo", "CONFIRMADO": "st-confirmado", "PENDENTE": "st-pendente"}


def _badge(status: str) -> str:
    return f'<span class="badge {STATUS_CLASSE.get(status, "")}">{_e(status)}</span>'


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------


def itens_por_grupo(pn: Painel) -> dict[str, list[tuple[Pendencia, Decimal, bool, str]]]:
    """Destino do dinheiro: (pendência, valor no grupo, soma?, motivo de não somar). Só pendências com valor e sem alerta.

    Toda divergência de checkout entra em "devolver ao lojista" pelo valor a devolver; a parte contrato_orbe aparece
    também em "recuperar da Orbe", sem somar (é o mesmo dinheiro)."""
    grupos: dict[str, list] = defaultdict(list)
    for p in pn.pendencias:
        if p.alerta or p.valor is None or not p.grupo:
            continue
        if p.grupo == "devolver_lojista" and p.devolver is not None:
            grupos["devolver_lojista"].append((p, p.devolver, p.soma, p.nao_soma_motivo))
            if p.recuperar:
                grupos["recuperar_orbe"].append((p, p.recuperar, False, NAO_SOMA_RECUPERAR))
        else:
            grupos[p.grupo].append((p, p.valor, p.soma, p.nao_soma_motivo))
    return grupos


def custo_tarvo(pn: Painel) -> tuple[Decimal, Decimal, Decimal, list[Pendencia]]:
    """Custo para a Tarvo = devolver ao lojista − recuperar da Orbe (só divergências de checkout)."""
    divs = [p for p in pn.pendencias if p.tipo.upper() == "DIVERGENCIA_CHECKOUT" and p.devolver is not None]
    devolver = sum((p.devolver for p in divs), ZERO)
    recuperar = sum((p.recuperar for p in divs), ZERO)
    return devolver, recuperar, devolver - recuperar, divs


def _tela_visao(pn: Painel) -> str:
    total_notas = sum((_dec(n.get("valor_brl")) or ZERO for n in pn.notas), ZERO)
    por_linha: dict[str, list[Decimal]] = defaultdict(list)
    for n in pn.notas:
        por_linha[n.get("linha_negocio", "")].append(_dec(n.get("valor_brl")) or ZERO)
    sub = " · ".join(f"{_e(k.capitalize())}: {len(v)} {'nota' if len(v) == 1 else 'notas'}, {brl(sum(v, ZERO))}" for k, v in sorted(por_linha.items()))
    h = [f'<section id="visao" class="tela" aria-labelledby="t-visao">',
         f'<p class="eyebrow">Fechamento · competência {_e(pn.competencia)}</p>',
         f'<h1 id="t-visao" data-total-notas="{_num(total_notas)}" data-qtd-notas="{len(pn.notas)}">'
         f'<span class="num">{brl(total_notas)}</span> a faturar em {len(pn.notas)} notas</h1>',
         f'<p class="sub">{sub} · <a href="#notas">ver as notas</a></p>']

    devolver, recuperar, custo, divs = custo_tarvo(pn)
    if divs:
        links_dev = " ".join(_link_rastro(p.id, p.contraparte.split(" · ")[-1]) for p in sorted(divs, key=lambda p: -p.devolver))
        links_rec = " ".join(_link_rastro(p.id, p.contraparte.split(" · ")[-1]) for p in divs if p.recuperar)
        h.append(f'<p class="custo" data-devolver="{_num(devolver)}" data-recuperar="{_num(recuperar)}" data-custo="{_num(custo)}">'
                 f'<span class="custo-rot">Custo para a Tarvo</span> <strong class="num">{brl(custo)}</strong>'
                 f'<span class="custo-conta">= devolver ao lojista <span class="num">{brl(devolver)}</span> − recuperar da Orbe '
                 f'<span class="num">{brl(recuperar)}</span></span>'
                 f'<span class="custo-rastro">Rastro do devolver: {links_dev}'
                 + (f' · do recuperar: {links_rec}' if links_rec else "") + '</span></p>')

    alertas = [p for p in pn.pendencias if p.alerta]
    if alertas:
        h.append('<div class="alertas" role="region" aria-label="Alertas">')
        for p in alertas:
            h.append(f'<div class="alerta">{_icone("alerta")}<div><strong>{_e(p.titulo)}</strong>'
                     f'<p>{_e(p.motivo)}</p><p class="meta">{_e(p.quem_decide)} · {brl(p.valor)} · {_link_rastro(p.id)}</p></div></div>')
        h.append("</div>")

    grupos = itens_por_grupo(pn)
    total_geral = sum((abs(v) for itens in grupos.values() for _, v, soma, _m in itens if soma), ZERO)
    h.append('<h2>Dinheiro que depende de uma decisão</h2>')
    h.append(f'<p class="sub" data-total-decisao="{_num(total_geral)}"><strong class="num">{brl(total_geral)}</strong> em jogo: '
             f'soma do valor absoluto de cada pendência com valor (o sinal de pendencias.csv aparece em cada linha). '
             f'Dinheiro em trânsito e valor que já está em outro número aparecem à parte.</p>')
    h.append('<div class="grupos">')
    for chave, rotulo, desc in GRUPOS:
        itens = grupos.get(chave)
        if not itens:
            continue
        soma = sum((abs(v) for _, v, s_, _m in itens if s_), ZERO)
        parte = sum((abs(v) for _, v, s_, _m in itens if not s_), ZERO)
        quem = " · ".join(sorted({p.quem_decide for p, *_ in itens if p.quem_decide}))
        if any(s_ for _, _, s_, _m in itens):
            total_txt = f'<p class="grupo-total num">{brl(soma)}</p>'
        else:
            total_txt = f'<p class="grupo-total num">{brl(parte)}</p><p class="nao-soma">não entra no total</p>'
        h.append(f'<article class="grupo" data-grupo="{chave}" data-total="{_num(soma)}" data-a-parte="{_num(parte)}" data-qtd="{len(itens)}">'
                 f'<header><h3>{_e(rotulo)}</h3><p class="desc">{_e(desc)}</p></header>{total_txt}'
                 f'<p class="meta">{len(itens)} {"pendência" if len(itens) == 1 else "pendências"} · decide: {_e(quem)}</p><ul class="itens">')
        for p, v, s_, motivo in sorted(itens, key=lambda i: (-abs(i[1]), i[0].id)):
            extra = f'<span class="nao-soma">{_e(motivo if motivo.startswith("não soma") else "não entra no total: " + motivo)}</span>' if not s_ else ""
            rot = f'<span class="nao-soma">{_e(p.rotulo_valor)}</span>' if p.rotulo_valor else ""
            h.append(f'<li data-item="{_e(p.id)}" data-valor="{_num(v)}"><div class="item-l"><span class="item-t">{_e(p.titulo)}</span>'
                     f'<span class="item-c">{_e(p.contraparte)}</span>{rot}{extra}</div>'
                     f'<div class="item-r"><span class="num">{brl(v)}</span>{_link_rastro(p.id)}</div></li>')
        h.append("</ul></article>")
    h.append("</div>")

    h.append(_premissas(pn))

    # arquivos
    h.append('<h2>Arquivos da saída</h2><ul class="arquivos">')
    for nome, qtd in pn.arquivos_saida:
        h.append(f'<li><a href="{_e(nome)}">{_icone("arquivo")}<span>{_e(ROTULO_ARQUIVO.get(nome, nome))}</span>'
                 f'<code>{_e(nome)}</code><span class="meta">{qtd} linhas</span></a></li>')
    for rel in pn.rascunhos:
        rotulo = "Rascunho de contestação" + (" (operações)" if rel.endswith(".csv") else "")
        h.append(f'<li><a href="{_e(rel)}">{_icone("arquivo")}<span>{rotulo}</span><code>{_e(rel)}</code></a></li>')
    h.append("</ul></section>")
    return "\n".join(h)


def _premissas(pn: Painel) -> str:
    """Duas contagens com nome: regras do regras.yaml por status (o que o código usa) e premissas do HIPOTESES.md."""
    contagem = Counter(r["status"] for r in pn.regras.values() if not r.get("substituida"))
    substituidas = sum(1 for r in pn.regras.values() if r.get("substituida"))
    h = ['<h2>Premissas que esperam aprovação</h2>']
    hip = pn.hipoteses
    if hip:
        assumo = [l for l in hip["linhas"] if l["status"] == "ASSUMO"]
        cont_tab = Counter(l["status"] for l in hip["linhas"])
        chips = "".join(f'<li data-hip-status="{s}" data-qtd="{cont_tab.get(s, 0)}">{_badge(s)}<span class="num">{cont_tab.get(s, 0)}</span></li>'
                        for s in ("CONFIRMADO", "SEI", "ASSUMO", "PENDENTE"))
        sub_txt = f'<li class="meta">{hip["substituidas"]} substituídas (Histórico)</li>' if hip["substituidas"] else ""
        h.append(f'<p class="sub"><strong>Premissas do {_e(hip["arquivo"])}</strong>, contadas na tabela Premissas. '
                 f'Resumo de lá: “{_e(hip["resumo"])}”</p>')
        h.append(f'<ul class="contagem" aria-label="Premissas do {_e(hip["arquivo"])} por status">{chips}{sub_txt}</ul>')
        h.append(f'<p class="sub">As {len(assumo)} ASSUMO esperam o aceite de quem decide (regra de fechamento: {_e(pn.dona)}; '
                 f'taxa e condição comercial: o comercial, Q-S).</p><div class="premissas">')
        for l in assumo:
            h.append(f'<details class="premissa" data-hipotese="{_e(l["id"])}"><summary><code>{_e(l["id"])}</code>'
                     f'<span class="premissa-v"><strong>{_e(l["tema"])}</strong> · {_e(_resumo_valor(l["premissa"], 140))}</span></summary>'
                     f'<dl><dt>Premissa</dt><dd>{_e(l["premissa"])}</dd><dt>Status</dt><dd>{_e(l["status_txt"])}</dd>'
                     f'<dt>Base e motivo</dt><dd>{_e(l["base"])}</dd><dt>Impacto se errada</dt><dd>{_e(l["impacto"])}</dd></dl></details>')
        h.append("</div>")
    chips = "".join(f'<li data-status="{s}" data-qtd="{contagem.get(s, 0)}">{_badge(s)}<span class="num">{contagem.get(s, 0)}</span></li>'
                    for s in ("CONFIRMADO", "SEI", "ASSUMO", "PENDENTE"))
    extra_sub = f'<li class="meta">{substituidas} decisões substituídas (histórico)</li>' if substituidas else ""
    h.append(f'<p class="sub"><strong>Regras no regras.yaml</strong> (o espelho executável que o código lê; uma premissa '
             f'do {_e(hip.get("arquivo", "HIPOTESES.md"))} pode virar várias regras), por status:</p>')
    h.append(f'<ul class="contagem" aria-label="Regras no regras.yaml por status">{chips}{extra_sub}</ul>')
    if not hip:
        assumo_r = [(k, r) for k, r in sorted(pn.regras.items()) if r["status"] == "ASSUMO" and not r.get("substituida")]
        h.append('<div class="premissas">')
        for k, r in assumo_r:
            h.append(f'<details class="premissa"><summary><code>{_e(k)}</code><span class="premissa-v">{_e(_resumo_valor(r["valor"], 140))}</span></summary>'
                     f'<dl><dt>Valor</dt><dd>{_e(_resumo_valor(r["valor"], 900))}</dd><dt>Fonte e motivo</dt><dd>{_e(_resumo_valor(r.get("fonte", ""), 900))}</dd></dl></details>')
        h.append("</div>")
    return "\n".join(h)


def _tela_decisoes(pn: Painel) -> str:
    h = ['<section id="decisoes" class="tela" aria-labelledby="t-decisoes">',
         '<p class="eyebrow">Somente leitura</p><h1 id="t-decisoes">Decisões do fechamento</h1>',
         '<p class="sub">Cada pendência aparece uma vez, na coluna de quem precisa agir. A última coluna mostra o que o sistema '
         'decidiu sozinho, com a regra e a fonte.</p><div class="kanban">']
    for chave, rotulo in COLUNAS_KANBAN:
        rotulo = rotulo.format(dona=f"a {pn.dona}" if pn.dona else "quem fecha")
        if chave == "regra":
            h.append(f'<section class="coluna" data-coluna="regra" data-qtd="{len(pn.fechadas)}" aria-label="{_e(rotulo)}">'
                     f'<header><h2>{_e(rotulo)}</h2><span class="qtd">{len(pn.fechadas)}</span>'
                     f'<p class="col-total">decidido por regra: não entra no total</p></header><div class="cartoes">')
            for g in pn.fechadas:
                if g["regras"]:
                    linhas = "".join(
                        f'<li><a href="#notas?id={_e(r["regra"])}"><code>{_e(r["regra"].removeprefix("classificacao_extratos."))}</code></a> '
                        f'{_badge(pn.regras.get(r["regra"], {}).get("status", ""))} <span class="num">{r["qtd"]}</span> · ex. '
                        f'<a href="#notas?id={_e(r["exemplo"])}"><code>{_e(r["exemplo"])}</code></a></li>' for r in g["regras"])
                    h.append(f'<article class="cartao cartao-regra" data-fechada="{_e(g["tipo"])}" data-qtd="{g["qtd"]}">'
                             f'<p class="c-titulo">{_e(g["titulo"])}</p><ul class="regras-lista">{linhas}</ul>'
                             f'<p class="c-fonte">Regra, status e fonte de cada uma: clique na chave.</p></article>')
                    continue
                r = pn.regras.get(g["regra"], {})
                fonte = _resumo_valor(r.get("fonte", ""), 180)
                h.append(f'<article class="cartao cartao-regra" data-fechada="{_e(g["tipo"])}" data-regra="{_e(g["regra"])}" data-qtd="{g["qtd"]}">'
                         f'<p class="c-titulo">{_e(g["titulo"])}</p>'
                         f'<p class="c-ref"><code>{_e(g["regra"])}</code> {_badge(r.get("status", ""))}</p>'
                         f'<p class="c-fonte">{_e(fonte)}</p>'
                         f'<p class="c-rodape"><span>{g["qtd"]} {"linha" if g["qtd"] == 1 else "linhas"} · ex. <code>{_e(g["exemplo"])}</code></span>'
                         f'{_link_rastro(g["exemplo"])}</p></article>')
            h.append("</div></section>")
            continue
        membros = [p for p in pn.pendencias if p.coluna == chave]
        soma = em_jogo(p for p in membros if p.soma)
        fora = em_jogo(p for p in membros if not p.soma)
        n_fora = sum(1 for p in membros if not p.soma)
        fora_txt = f'<p class="col-fora">+ {brl(fora)} à parte ({n_fora})</p>' if n_fora else ""
        h.append(f'<section class="coluna" data-coluna="{chave}" data-total="{_num(soma)}" data-qtd="{len(membros)}" aria-label="{_e(rotulo)}">'
                 f'<header><h2>{_e(rotulo)}</h2><span class="qtd">{len(membros)}</span>'
                 f'<p class="col-total num">{brl(soma) if any(p.soma for p in membros) or not membros else "não entra no total"}</p>{fora_txt}</header><div class="cartoes">')
        if not membros:
            h.append('<p class="vazio">Nada aqui.</p>')
        for p in sorted(membros, key=lambda p: (-(abs(p.valor) if p.valor is not None else ZERO), p.id)):
            selo = '<span class="selo-fora">não entra no total</span>' if not p.soma else ""
            alerta = '<span class="selo-alerta">alerta</span>' if p.alerta else ""
            h.append(f'<article class="cartao" data-pendencia="{_e(p.id)}" data-valor="{_num(p.valor)}" data-soma="{"1" if p.soma else "0"}">'
                     f'<p class="c-contra">{_e(p.contraparte)}</p><p class="c-titulo">{_e(p.titulo)}{alerta}</p>'
                     f'<p class="c-ref"><code title="{_e(" | ".join(p.refs))}">{_e(_refs_curtas(p.refs))}</code></p>'
                     f'<p class="c-valor num">{brl(p.valor)}{selo}</p>'
                     + (f'<p class="c-fonte">{_e(p.rotulo_valor)}</p>' if p.rotulo_valor else "") +
                     f'<p class="c-rodape"><span class="c-quem">{_e(p.quem_decide)}</span>{_link_rastro(p.id)}</p></article>')
        h.append("</div></section>")
    h.append("</div></section>")
    return "\n".join(h)


SITUACAO = {"com_diferenca": ("Com diferença", "sit-dif"), "sem_contrato": ("Sem contrato", "sit-sem"), "confere": ("Confere", "sit-ok"),
            "spread_negativo": ("Spread negativo · contestação", "sit-sem")}


def _tela_contratado(pn: Painel) -> str:
    cont = Counter(l["situacao"] for l in pn.lojistas)
    abas = [("todos", "Todos", len(pn.lojistas)), ("com_diferenca", "Com diferença", cont["com_diferenca"]),
            ("sem_contrato", "Sem contrato", cont["sem_contrato"]), ("confere", "Conferem", cont["confere"])]
    h = ['<section id="contratado" class="tela" aria-labelledby="t-contratado">',
         '<p class="eyebrow">Por lojista</p><h1 id="t-contratado">Contratado × cobrado</h1>',
         '<p class="sub">Checkout: comissão pela planilha (taxa contratada, o que a Tarvo fatura) contra o que a Orbe cobrou (taxa aplicada); '
         'a diferença inclui o centavo de truncamento da Orbe e a divergência é só onde a taxa difere. Remessa: spread que a Ponte '
         'aplicou contra o contratado.</p>',
         '<div class="linhas" role="group" aria-label="Linha de negócio">'
         '<button type="button" class="aba-linha" aria-pressed="true" data-linha="checkout">Checkout (Orbe)</button>'
         + ('<button type="button" class="aba-linha" aria-pressed="false" data-linha="remessa">Remessa (Ponte)</button>' if pn.remessa else "")
         + '</div>',
         '<div class="abas" role="tablist" aria-label="Filtrar lojistas">']
    qtd_r = {"todos": len(pn.remessa), **Counter(l["situacao"] for l in pn.remessa)}
    for chave, rotulo, qtd in abas:
        sel = "true" if chave == "todos" else "false"
        h.append(f'<button type="button" role="tab" class="aba" aria-selected="{sel}" aria-controls="tabela-lojistas" data-filtro="{chave}">'
                 f'{_e(rotulo)} <span class="qtd" data-qtd-checkout="{qtd}" data-qtd-remessa="{qtd_r.get(chave, 0)}">{qtd}</span></button>')
    h.append('</div><div class="tabela-caixa" id="tabela-lojistas" role="tabpanel"><table class="tabela"><thead><tr>'
             '<th scope="col">Lojista</th><th scope="col" class="n">Vendas</th><th scope="col" class="n">Volume bruto</th>'
             '<th scope="col" class="n">Pela planilha</th><th scope="col" class="n">Pela taxa aplicada</th>'
             '<th scope="col" class="n">Diferença</th><th scope="col" class="n">Divergência listada</th><th scope="col">Situação</th><th scope="col"><span class="sr">Rastro</span></th></tr></thead><tbody>')
    for l in pn.lojistas:
        rot, cls = SITUACAO[l["situacao"]]
        cnpj = f'<code class="c-cnpj">{_e(_cnpj_fmt(l["cnpj"]))}</code>' if l["cnpj"] else ""
        if l["situacao"] == "sem_contrato":
            cnpj += f'<span class="t-rotulo">{_e(ROTULO_VALOR["SEM_CONTRATO_VIGENTE"])}</span>'
        h.append(f'<tr data-situacao="{l["situacao"]}" data-id="{_e(l["id"])}" data-planilha="{_num(l["planilha"])}" data-aplicada="{_num(l["aplicada"])}" data-divergencia="{_num(l["divergencia"])}">'
                 f'<th scope="row"><span class="t-nome">{_e(l["nome"])}</span>{cnpj}</th><td class="n num">{l["vendas"]}</td>'
                 f'<td class="n num">{brl(l["volume"])}</td><td class="n num">{brl(l["planilha"])}</td><td class="n num">{brl(l["aplicada"])}</td>'
                 f'<td class="n num">{brl(l["diferenca"])}</td><td class="n num">{brl(l["divergencia"]) if l["divergencia"] else "—"}</td>'
                 f'<td><span class="sit {cls}">{rot}</span></td><td>{_link_rastro(l["id"])}</td></tr>')
    h.append("</tbody></table></div>")
    if pn.remessa:
        h.append('<div class="tabela-caixa" id="tabela-remessa" role="tabpanel" hidden><table class="tabela"><thead><tr>'
                 '<th scope="col">Lojista</th><th scope="col" class="n">Operações</th><th scope="col" class="n">Spread realizado (Ponte)</th>'
                 '<th scope="col" class="n">Comissão Tarvo</th><th scope="col" class="n">Divergência listada</th>'
                 '<th scope="col" class="n" title="Spread R$ do relatório, fora da comissão">Spread negativo</th><th scope="col">Situação</th>'
                 '<th scope="col"><span class="sr">Rastro</span></th></tr></thead><tbody>')
        for l in pn.remessa:
            rot, cls = SITUACAO[l["situacao"]]
            h.append(f'<tr data-situacao="{l["situacao"]}" data-remessa="{_e(l["id"])}" data-comissao="{_num(l["comissao"])}" data-divergencia="{_num(l["divergencia"])}">'
                     f'<th scope="row"><span class="t-nome">{_e(l["nome"])}</span><code class="c-cnpj">{_e(_cnpj_fmt(l["cnpj"]))}</code></th>'
                     f'<td class="n num">{l["operacoes"]}</td><td class="n num">{brl(l["spread"])}</td><td class="n num">{brl(l["comissao"])}</td>'
                     f'<td class="n num">{brl(l["divergencia"]) if l["divergencia"] else "—"}</td>'
                     f'<td class="n num">{brl(l["negativo"]) if l["negativo"] else "—"}</td><td><span class="sit {cls}">{rot}</span></td>'
                     f'<td>{_link_rastro(l["id"])}</td></tr>')
        h.append("</tbody></table></div>")
        h.append('<p class="meta nota-remessa" hidden>Divergência é o valor cheio que o lojista pagou de spread diferente do contratado. '
                 'Spread negativo é outra natureza: o lojista não pagou a mais, o prejuízo é da Tarvo com a Ponte (Spread R$ do relatório, '
                 'em contestação). Operações fora da comissão (duplicata, spread negativo) estão em "Fechadas por regra".</p>')
    if pn.residuo is not None:
        regra = pn.regras.get("divergencias.criterio_checkout", {})
        h.append(f'<aside class="nota-residuo" data-residuo="{_num(pn.residuo)}"><p><strong>Resíduo de truncamento da Orbe: '
                 f'<span class="num">{brl(pn.residuo)}</span></strong> no mês. É a soma do que a Orbe cobrou, menos a comissão '
                 f'pela planilha, menos as divergências listadas. Não é divergência: a Orbe trunca o centavo e a Tarvo arredonda.</p>'
                 f'<p class="meta"><code>divergencias.criterio_checkout</code> {_badge(regra.get("status", ""))} {_e(_resumo_valor(regra.get("fonte", ""), 300))}</p></aside>')
    h.append("</section>")
    return "\n".join(h)


def _tela_notas(pn: Painel) -> str:
    total = sum((_dec(n.get("valor_brl")) or ZERO for n in pn.notas), ZERO)
    h = ['<section id="notas" class="tela" aria-labelledby="t-notas">',
         f'<p class="eyebrow">Competência {_e(pn.competencia)}</p><h1 id="t-notas">Notas e rastro</h1>',
         '<h2 id="t-busca">Buscar no rastro</h2>',
         '<form class="busca" id="busca" role="search" aria-labelledby="t-busca">'
         '<label for="q" class="sr">ID da transação, operação, lançamento, nota ou pendência</label>'
         '<input id="q" name="q" type="search" autocomplete="off" spellcheck="false" placeholder="TX…, AN…, PC-…, L50, FITID, NF-…, PEN-…">'
         f'<button type="submit" class="btn">{_icone("busca")}<span>Buscar</span></button></form>',
         '<p class="meta" id="exemplos"></p><div id="resultado" aria-live="polite"></div>',
         f'<h2>Notas a emitir <span class="meta">{len(pn.notas)} · {brl(total)}</span></h2>',
         '<div class="tabela-caixa"><table class="tabela"><thead><tr><th scope="col">Tomador</th><th scope="col">Linha</th>'
         '<th scope="col" class="n">Valor</th><th scope="col">Discriminação</th><th scope="col"><span class="sr">Rastro</span></th></tr></thead><tbody>']
    for n in pn.notas:
        h.append(f'<tr data-nota="{_e(n["id_saida"])}" data-valor="{_e(n.get("valor_brl", ""))}"><th scope="row"><span class="t-nome">{_e(n.get("tomador", ""))}</span>'
                 f'<code class="c-cnpj">{_e(_cnpj_fmt(n.get("tomador_cnpj", "")))}</code></th><td>{_e(n.get("linha_negocio", ""))}</td>'
                 f'<td class="n num">{brl(_dec(n.get("valor_brl")))}</td><td class="t-disc">{_e(n.get("discriminacao", ""))}</td>'
                 f'<td>{_link_rastro(n["id_saida"])}</td></tr>')
    h.append(f'</tbody><tfoot><tr><th scope="row">Total</th><td></td><td class="n num">{brl(total)}</td><td></td><td></td></tr></tfoot></table></div></section>')
    return "\n".join(h)


def _dados_json(pn: Painel) -> str:
    regras_usadas = sorted({s["regra"] for s in pn.saidas.values() if s["regra"]}
                           | {m.group(1) for r in pn.rastro for m in [REGRA_NA_NOTA_RE.search(r.get("nota", ""))] if m}
                           | {g["regra"] for g in pn.fechadas if g["regra"]}
                           | {r["regra"] for g in pn.fechadas for r in g["regras"]})
    dados = {
        "rastro": {"cols": pn.rastro_cab, "rows": [[r.get(c, "") or "" for c in pn.rastro_cab] for r in pn.rastro]},
        "saidas": pn.saidas,
        "regras": {k: {"status": pn.regras[k]["status"], "fonte": _resumo_valor(pn.regras[k].get("fonte", ""), 400)}
                   for k in regras_usadas if k in pn.regras},
        "pendencias": {p.id: {"titulo": p.titulo, "grupo": p.grupo, "coluna": p.coluna, "soma": p.soma} for p in pn.pendencias},
    }
    texto = json.dumps(dados, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return texto.replace("</", "<\\/")


def renderizar(pn: Painel) -> tuple[str, int]:
    # LF sempre: o checkout no Windows (autocrlf) não pode mudar os bytes do painel
    css = (AQUI / "estilo.css").read_text(encoding="utf-8").replace("\r\n", "\n")
    js = (AQUI / "app.js").read_text(encoding="utf-8").replace("\r\n", "\n")
    dados = _dados_json(pn)
    nav = "".join(
        f'<a href="#{t}" data-tela="{t}" aria-label="{rot}">{_icone(t)}<span>{rot}</span></a>'
        for t, rot in (("visao", "Visão geral"), ("decisoes", "Decisões"), ("contratado", "Contratado × cobrado"), ("notas", "Notas e rastro"))
    )
    insumos = "".join(f'<li><code>{_e(n)}</code> <span class="hash" title="sha256">{h}</span></li>' for n, h, _ in pn.insumos)
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Fechamento {_e(pn.competencia)} · Tarvo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<style>
{css}
</style>
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<div class="app">
<nav class="lateral" aria-label="Telas do painel">
<p class="marca"><span class="marca-ponto" aria-hidden="true"></span>Tarvo <span class="meta">fechamento {_e(pn.competencia)}</span></p>
{nav}
</nav>
<main id="conteudo" tabindex="-1">
{_tela_visao(pn)}
{_tela_decisoes(pn)}
{_tela_contratado(pn)}
{_tela_notas(pn)}
<footer class="rodape">
<p><strong>Versão dos insumos</strong> (sha256, 12 primeiros caracteres). Linhas de rastro: <span class="num" data-linhas-rastro="{len(pn.rastro)}">{len(pn.rastro)}</span>.</p>
<ul class="insumos">{insumos}</ul>
<p class="meta">Gerado por <code>python -m tarvo.painel</code> a partir de saida/. Somente leitura: nada aqui altera a saída.</p>
</footer>
</main>
</div>
<script type="application/json" id="dados">{dados}</script>
<script>
{js}
</script>
</body>
</html>
"""
    return pagina, len(dados.encode("utf-8"))


def gerar_painel(saida: Path, dados: Path, regras_path: Path, hipoteses_path: Path | None = None) -> tuple[Path, int]:
    pn = carregar(Path(saida), Path(dados), Path(regras_path), Path(hipoteses_path) if hipoteses_path else None)
    pagina, tamanho_json = renderizar(pn)
    destino = Path(saida) / "painel.html"
    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)
    return destino, tamanho_json
