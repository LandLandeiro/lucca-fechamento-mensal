"""Cadastro unificado de lojistas e taxas contratadas com vigência.

Responsabilidade: normalizar CNPJ para 14 dígitos (com validação de DV), ligar EC Orbe
→ CNPJ só por chave (nunca por semelhança de nome) e interpretar a tabela de taxas
(faixas, vigência, condição especial) segundo `regras.yaml`. O que não tiver chave
confiável vira aviso aqui e pendência no cálculo.

Fontes do vínculo EC → CNPJ, nesta ordem, sempre por igualdade exata:
1. coluna "EC Orbe" da aba vigente;
2. `cadastro.mapeamento_ec_confirmado` (EC → nome exato da linha na aba vigente), D07.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from tarvo.formatos import FormatoInvalido, cnpj_valido, data_br, normalizar_cnpj  # noqa: F401 (reexport)
from tarvo.modelo import Aviso, Lojista, TaxaContratada
from tarvo.regras import RegraInvalida, valor_da_regra

_RE_VIG_DATA = re.compile(r"^(\d{2}/\d{2}/\d{4})$")
_RE_VIG_ATE = re.compile(r"^até (\d{2}/\d{2}/\d{4})$", re.IGNORECASE)
_RE_VIG_A_PARTIR = re.compile(r"^a partir de (\d{2}/\d{2}/\d{4})$", re.IGNORECASE)
_RE_FAIXA_PARCELADO = re.compile(r"^CREDITO PARCELADO (\d+)-(\d+)$")


@dataclass(frozen=True)
class Vigencia:
    inicio: date | None  # None = sem início informado
    fim: date | None  # None = sem fim informado

    def contem(self, d: date) -> bool:
        return (self.inicio is None or self.inicio <= d) and (self.fim is None or d <= self.fim)


@dataclass(frozen=True)
class TaxaEncontrada:
    taxa: Decimal | None  # fração (0.0359); None = não determinada
    fonte: str  # de onde veio (linha da planilha ou regra), ou o motivo de não ter vindo
    condicao: dict | None = None  # a condição especial de regras.yaml que deu a taxa, se houver


@dataclass
class Cadastro:
    lojistas: dict[str, Lojista] = field(default_factory=dict)  # por CNPJ
    por_ec: dict[str, str] = field(default_factory=dict)  # EC → CNPJ
    linhas_por_cnpj: dict[str, list[tuple[TaxaContratada, Vigencia | None]]] = field(default_factory=dict)
    avisos: list[Aviso] = field(default_factory=list)
    # nomes do relatório da Orbe por CNPJ (EC ligado) ou "EC<n>" (EC sem vínculo): só para achar o lojista no extrato
    nomes_orbe: dict[str, set[str]] = field(default_factory=dict)


def adicionar_nomes_orbe(cadastro: Cadastro, transacoes, regras: dict) -> None:
    """Os nomes do relatório da Orbe entram na lista de lojistas das regras de repasse/aporte do extrato
    (`classificacao_extratos.lojistas_do_extrato`; D52 corrige a D35). O vínculo é o EC, nunca semelhança:
    EC ligado a um CNPJ → o nome vale para esse CNPJ (ex.: "EDU ABROAD CONSULTORIA", EC 1020660828 →
    EduAbroad); EC sem vínculo (ex.: Atlas) → identificador "EC<n>"."""
    valor_da_regra(regras, "classificacao_extratos.lojistas_do_extrato")
    for t in transacoes:
        ident = cadastro.por_ec.get(t.cod_estabelecimento) or f"EC{t.cod_estabelecimento}"
        cadastro.nomes_orbe.setdefault(ident, set()).add(t.nome_estabelecimento)


def interpretar_vigencia(texto: str | None) -> Vigencia | None:
    """'01/01/2026' → desde 01/01/2026; 'até 14/09/2026'; 'a partir de 15/09/2026'. Outro texto → None."""
    if not texto:
        return None
    t = texto.strip()
    try:
        if m := _RE_VIG_DATA.match(t):
            return Vigencia(data_br(m.group(1)), None)
        if m := _RE_VIG_ATE.match(t):
            return Vigencia(None, data_br(m.group(1)))
        if m := _RE_VIG_A_PARTIR.match(t):
            return Vigencia(data_br(m.group(1)), None)
    except FormatoInvalido:
        return None
    return None


def montar_cadastro(taxas: list[TaxaContratada], regras: dict, arquivo: str = "") -> Cadastro:
    """Monta o cadastro por CNPJ e o índice EC → CNPJ."""
    cad = Cadastro()
    ecs_conflito: set[str] = set()

    def ligar_ec(ec: str, cnpj: str, origem: str) -> None:
        atual = cad.por_ec.get(ec)
        if atual is not None and atual != cnpj:
            cad.avisos.append(Aviso(arquivo, origem, f"EC {ec} ligado a dois CNPJs ({atual} e {cnpj}); vínculo descartado"))
            ecs_conflito.add(ec)
        cad.por_ec[ec] = cnpj

    for linha in taxas:
        local = f"R{linha.linha_planilha}"
        if linha.cnpj is None:
            cad.avisos.append(Aviso(arquivo, local, f"{linha.lojista}: sem CNPJ válido; linha fora do cadastro"))
            continue
        vig = interpretar_vigencia(linha.vigencia_texto)
        if vig is None:
            cad.avisos.append(Aviso(arquivo, local, f"{linha.lojista}: vigência ilegível {linha.vigencia_texto!r}; taxa da linha não será usada"))
        cad.linhas_por_cnpj.setdefault(linha.cnpj, []).append((linha, vig))
        if linha.cnpj not in cad.lojistas:  # nome = primeira linha do CNPJ na planilha
            cad.lojistas[linha.cnpj] = Lojista(cnpj=linha.cnpj, nome=linha.lojista)
        if linha.ec_orbe:
            ligar_ec(linha.ec_orbe, linha.cnpj, local)

    for ec, nome_linha in valor_da_regra(regras, "cadastro.mapeamento_ec_confirmado").items():
        ec = str(ec)
        alvo = {l.cnpj for l in taxas if l.lojista.strip() == str(nome_linha).strip() and l.cnpj}
        if len(alvo) != 1:
            cad.avisos.append(Aviso("regras.yaml", "cadastro.mapeamento_ec_confirmado",
                                    f"EC {ec} → {nome_linha!r}: {len(alvo)} linhas com esse nome exato; vínculo não aplicado"))
            continue
        ligar_ec(ec, alvo.pop(), "cadastro.mapeamento_ec_confirmado")

    for ec in ecs_conflito:
        cad.por_ec.pop(ec, None)
    for cnpj, lj in list(cad.lojistas.items()):
        ecs = tuple(sorted(e for e, c in cad.por_ec.items() if c == cnpj))
        cad.lojistas[cnpj] = Lojista(cnpj=cnpj, nome=lj.nome, ecs_orbe=ecs)
    return cad


def normalizar_nome(texto: str) -> str:
    """Maiúsculas, sem acento, espaços simples (para comparar nomes por igualdade/prefixo exato)."""
    sem_acento = unicodedata.normalize("NFD", texto or "")
    sem_acento = "".join(ch for ch in sem_acento if unicodedata.category(ch) != "Mn")
    return " ".join(sem_acento.upper().split())


def lojista_por_nome_bancario(cadastro: Cadastro, texto: str, aliases=()) -> tuple[str | None, str]:
    """CNPJ do lojista cujo nome no extrato casa por PREFIXO EXATO com um nome cadastrado (D31, D58).

    Nomes cadastrados: os da planilha, os do relatório da Orbe ligados pelo EC (D52) e os `aliases`
    (cnpj, nome) aprovados e vigentes na data do lançamento (`classificacao_extratos.aliases_lojista`,
    D44). Normalizados, casa de dois jeitos, sempre em fronteira de palavra:
      - nome completo no texto: o nome cadastrado inteiro é o começo do texto ("KIWI EXPERIENCE" →
        "KIWI EXPERIENCE TURISMO LT"), e tem pelo menos 2 palavras ou é nome da Orbe ligado ao EC / alias
        aprovado. "Vela" e "Canguru" (uma palavra, só na planilha) não casam com "VELA TRANSPORTES";
      - o banco cortou o nome: o texto é o começo do nome cadastrado ("ROTA GLOBAL INTERCAMBIO LT" →
        "ROTA GLOBAL INTERCAMBIO LTDA") e traz pelo menos 2 palavras inteiras dele.
    Não há similaridade nem distância de edição: "EDU ABROAD" não casa com "EDUABROAD". Zero ou mais de
    um CNPJ → None com o motivo.
    """
    alvo = normalizar_nome(texto)
    if not alvo:
        return None, "nome vazio"
    achados: dict[str, str] = {}
    candidatos = [(cnpj, l.lojista, False) for cnpj, linhas in cadastro.linhas_por_cnpj.items() for l, _ in linhas]
    candidatos += [(ident, nome, True) for ident, nomes in cadastro.nomes_orbe.items() for nome in sorted(nomes)]
    candidatos += [(ident, nome, True) for ident, nome in aliases]
    for ident, nome_original, ligado in candidatos:
        nome = normalizar_nome(nome_original)
        if _casa_nome(alvo, nome, ligado):
            achados[ident] = nome_original
    if len(achados) == 1:
        cnpj, nome = next(iter(achados.items()))
        return cnpj, f"prefixo exato de {nome!r}"
    if not achados:
        return None, f"{alvo!r} não é prefixo exato de nenhum lojista da planilha (nem o contrário)"
    return None, f"{alvo!r} casa com mais de um lojista: {sorted(achados.values())}"


def _casa_nome(alvo: str, nome: str, ligado: bool) -> bool:
    """Regra de `lojista_por_nome_bancario` (D58). `ligado` = nome da Orbe ligado ao EC ou alias aprovado."""
    if alvo == nome or alvo.startswith(nome + " "):  # nome completo no texto
        return len(nome.split()) >= 2 or ligado
    if nome.startswith(alvo):  # o banco cortou o nome: conta só as palavras inteiras do texto
        palavras = alvo.split()
        if nome[len(alvo)] != " ":
            palavras = palavras[:-1]  # a última foi cortada no meio
        return len(palavras) >= 2
    return False


def lojista_por_ec(cadastro: Cadastro, ec: str) -> Lojista | None:
    """Busca o lojista pelo EC da Orbe (só correspondência exata)."""
    cnpj = cadastro.por_ec.get(ec)
    return cadastro.lojistas.get(cnpj) if cnpj else None


def coluna_do_produto(tipo_lancamento: str, modalidade: str | None, parcelas: int | None, mapa: dict) -> str | None:
    """Coluna da planilha para a transação, segundo `taxas.coluna_por_produto`. None = sem coluna."""
    if tipo_lancamento in ("ANTECIPACAO", "REVERSAO ANTECIPACAO"):
        return mapa.get("ANTECIPACAO")
    if modalidade == "CREDITO PARCELADO":
        if parcelas is None:
            return None
        for chave, coluna in mapa.items():
            m = _RE_FAIXA_PARCELADO.match(chave)
            if m and int(m.group(1)) <= parcelas <= int(m.group(2)):
                return coluna
        return None
    return mapa.get(modalidade) if modalidade else None


def taxa_contratada(cadastro: Cadastro, cnpj: str, coluna: str, data_ref: date, regras: dict) -> TaxaEncontrada:
    """Taxa contratada vigente para a coluna na data de referência.

    Ordem: condição especial de `regras.yaml` (se vigente na data) → linha da planilha
    cuja vigência contém a data (exatamente uma). Qualquer outra situação → taxa None + motivo.
    """
    especial = _condicao_especial(cnpj, coluna, data_ref, regras)
    if especial is not None:
        return especial

    linha, motivo = linha_vigente(cadastro, cnpj, data_ref)
    if linha is None:
        return TaxaEncontrada(None, motivo)
    valor = linha.taxas.get(coluna)
    if isinstance(valor, Decimal):
        return TaxaEncontrada(valor, f"planilha R{linha.linha_planilha} col. {coluna!r}")
    if valor is None:
        return TaxaEncontrada(None, f"planilha R{linha.linha_planilha} col. {coluna!r} vazia")
    return TaxaEncontrada(None, f"planilha R{linha.linha_planilha} col. {coluna!r} em texto: {valor!r}")


def linha_vigente(cadastro: Cadastro, cnpj: str, data_ref: date) -> tuple[TaxaContratada | None, str]:
    """A única linha da planilha do CNPJ cuja vigência contém a data; senão (None, motivo)."""
    candidatas = [(l, v) for l, v in cadastro.linhas_por_cnpj.get(cnpj, []) if v is not None and v.contem(data_ref)]
    if not candidatas:
        return None, f"nenhuma linha da planilha vigente em {data_ref.isoformat()}"
    if len(candidatas) > 1:
        rs = ", ".join(f"R{l.linha_planilha}" for l, _ in candidatas)
        return None, f"mais de uma linha vigente em {data_ref.isoformat()} ({rs})"
    return candidatas[0][0], f"planilha R{candidatas[0][0].linha_planilha}"


CHAVE_CONDICOES = "cadastro.condicoes_especiais"
_LINHA_DO_GRUPO = {"MDR": "CHECKOUT", "ANTECIPACAO": "CHECKOUT", "REMESSA": "REMESSA"}
_CAMPOS_CONDICAO = ("id", "cnpj", "linhas_negocio", "taxa", "vigencia", "fonte")


def _condicao_especial(cnpj: str, coluna: str, data_ref: date, regras: dict) -> TaxaEncontrada | None:
    mapa = valor_da_regra(regras, "taxas.coluna_por_produto")
    grupo = "REMESSA" if coluna == mapa.get("REMESSA") else "ANTECIPACAO" if coluna == mapa.get("ANTECIPACAO") else "MDR"
    return condicao_especial(regras, cnpj, grupo, data_ref)


def condicao_especial(regras: dict, cnpj: str, grupo: str, data_ref: date) -> TaxaEncontrada | None:
    """Taxa de `cadastro.condicoes_especiais` (D61) para o CNPJ, o grupo (MDR | ANTECIPACAO | REMESSA) e a data.

    None = nenhuma condição vale (segue a planilha). Duas ou mais vigentes ao mesmo tempo → taxa None com o
    motivo (vira pendência; o código não escolhe)."""
    achadas = []
    for i, cond in enumerate(valor_da_regra(regras, CHAVE_CONDICOES) or []):
        faltando = [c for c in _CAMPOS_CONDICAO if c not in cond]
        if faltando:
            raise RegraInvalida(f"{CHAVE_CONDICOES}[{i}]: faltam campos {faltando}")
        desconhecidos = set(cond["taxa"]) - set(_LINHA_DO_GRUPO)
        if desconhecidos:
            raise RegraInvalida(f"{CHAVE_CONDICOES}[{cond['id']}]: grupo de taxa desconhecido {sorted(desconhecidos)}")
        if str(cond["cnpj"]) != cnpj or grupo not in cond["taxa"] or _LINHA_DO_GRUPO[grupo] not in cond["linhas_negocio"]:
            continue
        vig = Vigencia(_como_data(cond["vigencia"]["inicio"]), _como_data(cond["vigencia"]["fim"]))
        if vig.contem(data_ref):
            achadas.append((cond, vig))
    if not achadas:
        return None
    if len(achadas) > 1:
        return TaxaEncontrada(None, f"{len(achadas)} condições especiais vigentes em {data_ref.isoformat()} "
                                    f"({', '.join(c['id'] for c, _ in achadas)}): o código não escolhe")
    cond, vig = achadas[0]
    return TaxaEncontrada(Decimal(str(cond["taxa"][grupo])),
                          f"regras.yaml {CHAVE_CONDICOES}[{cond['id']}] ({grupo}, {vig.inicio}–{vig.fim})", cond)


def _como_data(v) -> date:
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))
