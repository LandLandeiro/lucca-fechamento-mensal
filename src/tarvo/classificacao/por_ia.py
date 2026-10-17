"""Classificação por IA, só nas sobras sem regra (E6b parte 2): a IA sugere, o código prova.

Responsabilidade: para cada lançamento que nenhuma regra de `classificacao_extratos` cobriu,
pedir ao modelo (`classificacao.modelo_ia`) uma contrapartida da lista fechada de contas
lançáveis e, se houver, o lojista, com saída estruturada (pydantic, `messages.parse`). A
sugestão só vale depois da verificação no código (`classificacao.verificacao_ia`, D42):

  (a) a conta existe, é ANALITICA e tem ACEITA_LANCTO=S (lista de contas lançáveis);
  (b) o CNPJ indicado está no cadastro; conta que as regras só aceitam com lojista
      (repasse/aporte) exige lojista;
  (c) prova independente: Meridiano → Σ PIX RECEB atribuídos ao lojista (regra + IA) =
      Σ (Valor R$ + IOF) das operações dele no relatório da Ponte; Aurora → o lojista tem
      EC no relatório da Orbe com VENDA no mês;
  (d) confiança ≥ `classificacao.limiar_confianca_ia`.

Passou tudo → metodo=IA com a confiança. Falhou qualquer item → HUMANO + pendência
IA_REPROVADA com o motivo exato. Sem resposta (sem chave e sem cache, `--sem-ia`, erro da
API) → HUMANO + a pendência SEM_REGRA, com aviso; nunca quebra.

Cache: cada resposta aceita pelo parser vai para `cache_ia/<sha256>.json`, chave =
(versão + hash do prompt, modelo, linha). Reexecução usa o cache: determinística, custo zero.
A chave da API vem do `.env.local` (ou do ambiente) e nunca é impressa, logada nem gravada.

Aprendizado para o mês seguinte: as sugestões aprovadas viram linhas de
`sugestoes_regra.csv` (status PROPOSTA); nenhum alias é aplicado no mês.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional, Protocol

from pydantic import BaseModel

from tarvo.cadastro import Cadastro, lojista_por_nome_bancario, normalizar_nome
from tarvo.formatos import fmt_dinheiro
from tarvo.modelo import ContaContabil, LancamentoBancario, OperacaoPonte, Pendencia, TransacaoOrbe
from tarvo.regras import valor_da_regra

ZERO = Decimal("0")
PROMPT_PADRAO = Path(__file__).resolve().parents[1] / "prompts" / "classificar_lancamento.md"
VARIAVEL_CHAVE = "ANTHROPIC_API_KEY"
VARIAVEL_SEM_REDE = "TARVO_SEM_REDE"  # testes: só cache, nunca rede


class SugestaoIA(BaseModel):
    """Saída estruturada pedida ao modelo (validada pelo SDK com pydantic)."""

    conta_codigo: str
    lojista_cnpj: Optional[str] = None
    justificativa: str
    confianca: float


@dataclass
class RespostaIA:
    sugestao: SugestaoIA
    uso: dict  # input_tokens, output_tokens da chamada original
    origem: str  # CACHE | API


class ClienteIA(Protocol):
    def sugerir(self, sistema: str, entrada: dict) -> tuple[SugestaoIA, dict]: ...


class ErroIA(RuntimeError):
    """Falha ao obter a sugestão (rede, autenticação, recusa, resposta fora do schema)."""


# ---------------------------------------------------------------------------
# chave, prompt, cache
# ---------------------------------------------------------------------------

def ler_chave(arquivo_env: Path) -> str | None:
    """ANTHROPIC_API_KEY do `.env.local` (se existir) ou do ambiente. Nunca imprime o valor."""
    if os.environ.get(VARIAVEL_SEM_REDE):
        return None
    try:
        texto = arquivo_env.read_text(encoding="utf-8")
    except OSError:
        texto = ""
    m = re.search(rf"^\s*{VARIAVEL_CHAVE}\s*=\s*(.*?)\s*$", texto, re.MULTILINE)
    valor = m.group(1).strip().strip("'\"") if m else ""
    return valor or os.environ.get(VARIAVEL_CHAVE) or None


@dataclass(frozen=True)
class Prompt:
    versao: str
    sha256: str
    modelo_texto: str  # com {{CONTAS}} e {{LOJISTAS}}

    def sistema(self, plano: dict[str, ContaContabil], cadastro: Cadastro) -> str:
        contas = "\n".join(f"- {c.codigo} — {c.descricao} — {c.natureza}" for c in sorted(plano.values(), key=lambda c: c.codigo))
        lojistas = "\n".join(f"- {lj.nome} — {cnpj}" for cnpj, lj in sorted(cadastro.lojistas.items(), key=lambda kv: kv[1].nome))
        return self.modelo_texto.replace("{{CONTAS}}", contas).replace("{{LOJISTAS}}", lojistas)


def carregar_prompt(caminho: Path = PROMPT_PADRAO) -> Prompt:
    texto = caminho.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto.replace("\r\n", "\n"), re.DOTALL)
    if not m:
        raise ValueError(f"{caminho}: prompt sem cabeçalho '---' com a versão")
    versao = re.search(r"^versao:\s*(\S+)", m.group(1), re.MULTILINE)
    if not versao:
        raise ValueError(f"{caminho}: cabeçalho sem 'versao:'")
    corpo = m.group(2).strip() + "\n"
    return Prompt(versao.group(1), hashlib.sha256(corpo.encode("utf-8")).hexdigest(), corpo)


def entrada_da_linha(lan: LancamentoBancario) -> dict:
    return {
        "banco": lan.banco,
        "data": lan.data.isoformat(),
        "descricao": lan.descricao,
        "valor": format(abs(lan.valor), "f"),
        "sinal": "+" if lan.valor > 0 else "-",
    }


def chave_cache(prompt: Prompt, modelo: str, entrada: dict) -> str:
    base = json.dumps({"prompt_versao": prompt.versao, "prompt_sha256": prompt.sha256, "modelo": modelo,
                       "linha": entrada}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def obter_sugestao(
    lan: LancamentoBancario, prompt: Prompt, sistema: str, modelo: str, cache_dir: Path, cliente: ClienteIA | None
) -> RespostaIA:
    """Cache primeiro; sem cache, chama o cliente (se houver) e grava. Levanta ErroIA se não houver resposta."""
    entrada = entrada_da_linha(lan)
    caminho = cache_dir / f"{chave_cache(prompt, modelo, entrada)}.json"
    if caminho.exists():
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            return RespostaIA(SugestaoIA.model_validate(dados["resposta"]), dados.get("uso", {}), "CACHE")
        except (ValueError, KeyError) as e:
            raise ErroIA(f"cache ilegível ({caminho.name}): {e}") from e
    if cliente is None:
        raise ErroIA("sem chave da API e sem resposta em cache")
    sugestao, uso = cliente.sugerir(sistema, entrada)
    cache_dir.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({
        "prompt_versao": prompt.versao, "prompt_sha256": prompt.sha256, "modelo": modelo, "linha": entrada,
        "resposta": sugestao.model_dump(), "uso": uso, "gerado_em": date.today().isoformat(),
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RespostaIA(sugestao, uso, "API")


class ClienteAnthropic:
    """Cliente real: `messages.parse` com `output_format=SugestaoIA` (SDK anthropic 1.x)."""

    def __init__(self, chave: str, config: dict):
        import anthropic  # importado só quando há chave

        self._anthropic = anthropic
        self._cliente = anthropic.Anthropic(api_key=chave, timeout=60.0, max_retries=2)
        self._config = config

    def sugerir(self, sistema: str, entrada: dict) -> tuple[SugestaoIA, dict]:
        a = self._anthropic
        try:
            resp = self._cliente.messages.parse(
                model=self._config["id"],
                max_tokens=int(self._config["max_tokens"]),
                system=sistema,
                messages=[{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}],
                output_config={"effort": self._config["effort"]},
                output_format=SugestaoIA,
            )
        except a.AuthenticationError as e:
            raise ErroIA("chave da API recusada (401)") from e
        except a.RateLimitError as e:
            raise ErroIA("limite de requisições da API (429)") from e
        except a.APIStatusError as e:
            raise ErroIA(f"erro da API ({e.status_code})") from e
        except a.APIConnectionError as e:
            raise ErroIA("sem conexão com a API") from e
        except ValueError as e:  # resposta fora do schema
            raise ErroIA(f"resposta fora do schema: {e}") from e
        if resp.stop_reason != "end_turn" or resp.parsed_output is None:
            raise ErroIA(f"resposta sem sugestão (stop_reason={resp.stop_reason})")
        uso = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}
        return resp.parsed_output, uso


# ---------------------------------------------------------------------------
# verificação e aplicação
# ---------------------------------------------------------------------------

@dataclass
class Decisao:
    lan: LancamentoBancario
    linha_arquivo: int
    motivo_sem_regra: str
    resposta: RespostaIA | None = None
    erro: str | None = None  # sem resposta
    checagens: list[tuple[str, bool, str]] = field(default_factory=list)  # (item, ok, detalhe)

    @property
    def aceita(self) -> bool:
        return self.resposta is not None and all(ok for _, ok, _ in self.checagens)

    @property
    def falhas(self) -> list[str]:
        return [f"({item}) {detalhe}" for item, ok, detalhe in self.checagens if not ok]


@dataclass
class ResultadoIA:
    decisoes: list[Decisao] = field(default_factory=list)
    sugestoes_regra: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    chamadas_api: int = 0
    uso_total: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    custo_usd: Decimal = ZERO


def _contas_que_exigem_lojista(regras: dict, banco: str) -> dict[str, str]:
    """conta → nome da regra, para as regras com lojista: true do banco (D42 b)."""
    prefixo = f"classificacao_extratos.{banco.lower()}."
    return {regras[k]["valor"]["conta"]: k for k in regras
            if k.startswith(prefixo) and isinstance(regras[k]["valor"], dict) and regras[k]["valor"].get("lojista")}


def classificar_sobras(
    sobras: list[tuple[LancamentoBancario, str, int]],
    plano: dict[str, ContaContabil],
    cadastro: Cadastro,
    regras: dict,
    competencia: tuple[int, int],
    transacoes_orbe: list[TransacaoOrbe],
    operacoes_ponte: list[tuple[OperacaoPonte, str]],
    aportes_por_regra: dict[str, Decimal],
    cache_dir: Path,
    cliente: ClienteIA | None,
    sem_ia: bool = False,
    prompt: Prompt | None = None,
) -> ResultadoIA:
    """`sobras` = (lançamento, motivo de não ter regra, linha física); `aportes_por_regra` = Σ PIX RECEB
    por CNPJ já identificados por regra no Meridiano; `operacoes_ponte` = operações únicas (op, cnpj)."""
    config = valor_da_regra(regras, "classificacao.modelo_ia")
    valor_da_regra(regras, "classificacao.uso_ia")
    valor_da_regra(regras, "classificacao.verificacao_ia")
    limiar = Decimal(str(valor_da_regra(regras, "classificacao.limiar_confianca_ia")))
    res = ResultadoIA()
    if not sobras:
        return res
    prompt = prompt or carregar_prompt()
    sistema = prompt.sistema(plano, cadastro)
    if sem_ia:
        res.avisos.append(f"IA desligada (--sem-ia): {len(sobras)} lançamentos sem regra ficam para uma pessoa")
    elif cliente is None:
        res.avisos.append("sem chave da API: só respostas em cache; o que não estiver no cache fica para uma pessoa")

    for lan, motivo, linha_n in sobras:
        d = Decisao(lan, linha_n, motivo)
        res.decisoes.append(d)
        if sem_ia:
            d.erro = "IA desligada (--sem-ia)"
            continue
        try:
            d.resposta = obter_sugestao(lan, prompt, sistema, config["id"], cache_dir, cliente)
        except ErroIA as e:
            d.erro = str(e)
            res.avisos.append(f"IA sem resposta para {lan.banco} {lan.ref_origem}: {e}")
            continue
        if d.resposta.origem == "API":
            res.chamadas_api += 1
        for k in res.uso_total:
            res.uso_total[k] += int(d.resposta.uso.get(k, 0))

    preco = config.get("preco_usd_por_milhao", {})
    res.custo_usd = (Decimal(res.uso_total["input_tokens"]) * Decimal(str(preco.get("entrada", 0)))
                     + Decimal(res.uso_total["output_tokens"]) * Decimal(str(preco.get("saida", 0)))) / Decimal(1_000_000)

    # (c) Meridiano: Σ por lojista dos PIX RECEB atribuídos (regra + IA) × Σ (Valor R$ + IOF) da Ponte
    devido: dict[str, Decimal] = {}
    for op, cnpj in operacoes_ponte:
        devido[cnpj] = devido.get(cnpj, ZERO) + op.valor_brl + op.iof_brl
    ia_meridiano: dict[str, Decimal] = {}
    for d in res.decisoes:
        s = d.resposta.sugestao if d.resposta else None
        if s and s.lojista_cnpj and d.lan.banco == "MERIDIANO" and d.lan.valor > 0:
            ia_meridiano[s.lojista_cnpj] = ia_meridiano.get(s.lojista_cnpj, ZERO) + d.lan.valor
    # Aurora: lojista com EC no relatório da Orbe e VENDA no mês
    vendas: dict[str, tuple[int, Decimal]] = {}
    for t in transacoes_orbe:
        cnpj = cadastro.por_ec.get(t.cod_estabelecimento)
        if cnpj and t.tipo_lancamento == "VENDA" and (t.data_movimento.year, t.data_movimento.month) == competencia:
            n, v = vendas.get(cnpj, (0, ZERO))
            vendas[cnpj] = (n + 1, v + t.valor_bruto)

    for d in res.decisoes:
        if d.resposta is None:
            continue
        s, lan = d.resposta.sugestao, d.lan
        # (a)
        conta = plano.get(s.conta_codigo)
        d.checagens.append(("a", conta is not None,
                            f"conta {s.conta_codigo} {'lançável: ' + conta.descricao if conta else 'não existe ou não aceita lançamento (TIPO ANALITICA e ACEITA_LANCTO=S)'}"))
        # (b)
        exige = _contas_que_exigem_lojista(regras, lan.banco)
        if s.lojista_cnpj:
            lj = cadastro.lojistas.get(s.lojista_cnpj)
            d.checagens.append(("b", lj is not None,
                                f"CNPJ {s.lojista_cnpj} {'no cadastro: ' + lj.nome if lj else 'não está no cadastro'}"))
        elif s.conta_codigo in exige:
            d.checagens.append(("b", False, f"conta {s.conta_codigo} exige lojista (regra {exige[s.conta_codigo]}) e a IA não indicou nenhum"))
        # (c)
        if s.lojista_cnpj and s.lojista_cnpj in cadastro.lojistas:
            cnpj = s.lojista_cnpj
            if lan.banco == "MERIDIANO" and lan.valor > 0:
                recebido = aportes_por_regra.get(cnpj, ZERO) + ia_meridiano.get(cnpj, ZERO)
                esperado = devido.get(cnpj, ZERO)
                d.checagens.append(("c", recebido == esperado and esperado != 0,
                                    f"Σ PIX RECEB atribuídos a {cadastro.lojistas[cnpj].nome} {fmt_dinheiro(recebido)} "
                                    f"(regra {fmt_dinheiro(aportes_por_regra.get(cnpj, ZERO))} + IA {fmt_dinheiro(ia_meridiano.get(cnpj, ZERO))}) "
                                    f"{'=' if recebido == esperado else '≠'} Σ (Valor R$ + IOF) das operações na Ponte {fmt_dinheiro(esperado)}"))
            elif lan.banco == "AURORA":
                n, v = vendas.get(cnpj, (0, ZERO))
                d.checagens.append(("c", n > 0, f"{cadastro.lojistas[cnpj].nome}: {n} vendas na Orbe no mês "
                                                f"(bruto {fmt_dinheiro(v)}) pelo EC {', '.join(cadastro.lojistas[cnpj].ecs_orbe) or '-'}"))
            else:
                d.checagens.append(("c", False, "saída do Meridiano com lojista: não há prova independente definida"))
        # (d)
        c = Decimal(str(s.confianca))
        d.checagens.append(("d", limiar <= c <= 1, f"confiança {c} {'≥' if c >= limiar else '<'} {limiar}"))

    res.sugestoes_regra = _sugestoes(res.decisoes, regras, cadastro)
    return res


def _sugestoes(decisoes: list[Decisao], regras: dict, cadastro: Cadastro) -> list[dict]:
    """Aprendizado para o mês seguinte: alias do nome do extrato (quando uma regra com lojista casou o
    padrão mas não achou o nome) ou padrão de descrição novo. Status PROPOSTA; nada é aplicado."""
    grupos: dict[tuple, dict] = {}
    for d in decisoes:
        if not d.aceita:
            continue
        s, lan = d.resposta.sugestao, d.lan
        desc = normalizar_nome(lan.descricao)
        tipo, chave_regra, padrao = "PADRAO_DESCRICAO", "", f"^{re.escape(desc)}$"
        for k in regras:
            if not k.startswith(f"classificacao_extratos.{lan.banco.lower()}."):
                continue
            v = regras[k]["valor"]
            if not (isinstance(v, dict) and v.get("lojista") and v.get("conta") == s.conta_codigo):
                continue
            m = re.search(v["padrao"], desc)
            sinal_ok = (lan.valor > 0) if v["sinal"] == "+" else (lan.valor < 0)
            if m and sinal_ok and lojista_por_nome_bancario(cadastro, m.group("lojista"))[0] is None:
                tipo, chave_regra, padrao = "ALIAS_LOJISTA", k, m.group("lojista").strip()
                break
        g = grupos.setdefault((tipo, lan.banco, padrao, s.conta_codigo, s.lojista_cnpj), {
            "tipo": tipo, "banco": lan.banco, "padrao_ou_nome": padrao, "regra_afetada": chave_regra,
            "conta_codigo": s.conta_codigo, "lojista_cnpj": s.lojista_cnpj,
            "lojista": cadastro.lojistas[s.lojista_cnpj].nome if s.lojista_cnpj else "",
            "qtd_lancamentos": 0, "valor_total": ZERO, "refs": [], "evidencias": [],
        })
        g["qtd_lancamentos"] += 1
        g["valor_total"] += lan.valor
        g["refs"].append(lan.ref_origem)
        prova = next((det for item, _, det in d.checagens if item == "c"), "sem prova de lojista (conta sem lojista)")
        if prova not in g["evidencias"]:
            g["evidencias"].append(prova)
    linhas = []
    for i, g in enumerate(sorted(grupos.values(), key=lambda g: (g["banco"], g["tipo"], g["padrao_ou_nome"])), start=1):
        linhas.append({
            "id_sugestao": f"SUG-{i:03d}", "tipo": g["tipo"], "banco": g["banco"], "padrao_ou_nome": g["padrao_ou_nome"],
            "regra_afetada": g["regra_afetada"], "conta_codigo": g["conta_codigo"], "lojista_cnpj": g["lojista_cnpj"],
            "lojista": g["lojista"], "qtd_lancamentos": g["qtd_lancamentos"], "valor_total": g["valor_total"],
            "refs": ", ".join(g["refs"]), "evidencia": "; ".join(g["evidencias"]), **_aprovacao(g, regras),
        })
    return linhas


def _aprovacao(g: dict, regras: dict) -> dict:
    """APROVADA se um alias de `classificacao_extratos.aliases_lojista` cobre a sugestão (mesmo CNPJ e banco,
    nome por prefixo em fronteira de palavra); senão PROPOSTA."""
    if g["tipo"] == "ALIAS_LOJISTA" and "classificacao_extratos.aliases_lojista" in regras:
        alvo = normalizar_nome(g["padrao_ou_nome"])
        for a in valor_da_regra(regras, "classificacao_extratos.aliases_lojista"):
            nome = normalizar_nome(a["nome"])
            casa = alvo == nome or nome.startswith(alvo) or (alvo.startswith(nome) and alvo[len(nome)] == " ")
            if casa and str(a["cnpj"]) == g["lojista_cnpj"] and g["banco"] in a["bancos"]:
                return {"status": "APROVADA",
                        "aprovacao": f"classificacao_extratos.aliases_lojista {a['nome']!r}, vigência {a['vigencia_inicio']}"}
    return {"status": "PROPOSTA", "aprovacao": ""}


def aplicar(res: ResultadoIA, classif: list, prompt_versao: str) -> None:
    """Atualiza as linhas e pendências de `classificar_por_regra` com as decisões da IA (in place)."""
    por_id = {(d.lan.banco, d.lan.ref_origem): d for d in res.decisoes}
    for c in classif:
        for linha in c.linhas:
            d = por_id.get((linha["banco"], linha["ref_origem"]))
            if d is None:
                continue
            s = d.resposta.sugestao if d.resposta else None
            if s:
                linha["sugestao_ia"] = f"{s.conta_codigo} / {s.lojista_cnpj or '-'} / confiança {s.confianca}"
                linha["justificativa_ia"] = s.justificativa
            if d.aceita:
                linha.update({"conta_codigo": s.conta_codigo, "metodo": "IA", "confianca": Decimal(str(s.confianca)),
                              "regra_aplicada": f"ia (prompt v{prompt_versao})", "status_regra": "IA verificada (D42)",
                              "lado_contrapartida": "D" if d.lan.valor < 0 else "C"})
                if s.lojista_cnpj:
                    c.lojista_por_lancamento[(d.lan.banco, d.lan.ref_origem)] = s.lojista_cnpj
        ids_sem_regra = {f"PEN-SEM_REGRA-{b}-{r}" for b, r in por_id}
        manter, manter_rastro = [], []
        for p in c.pendencias:
            if p.id_saida not in ids_sem_regra:
                manter.append(p)
        for l in c.rastro_pendencias:
            if l["id_saida"] not in ids_sem_regra:
                manter_rastro.append(l)
        c.pendencias, c.rastro_pendencias = manter, manter_rastro
        for lan, motivo in list(c.sem_regra):
            d = por_id.get((lan.banco, lan.ref_origem))
            if d is None:
                continue
            if d.aceita:
                c.sem_regra.remove((lan, motivo))
                continue
            if d.resposta is None:
                pid, tipo = f"PEN-SEM_REGRA-{lan.banco}-{lan.ref_origem}", "SEM_REGRA"
                texto = f"{lan.banco} {lan.data.isoformat()} {lan.descricao!r}: sem regra ({motivo}); IA sem resposta: {d.erro}"
            else:
                pid, tipo = f"PEN-IA_REPROVADA-{lan.banco}-{lan.ref_origem}", "IA_REPROVADA"
                s = d.resposta.sugestao
                texto = (f"{lan.banco} {lan.data.isoformat()} {lan.descricao!r}: sem regra; a IA sugeriu conta {s.conta_codigo}, "
                         f"lojista {s.lojista_cnpj or '-'}, confiança {s.confianca}, e a verificação recusou: "
                         + "; ".join(d.falhas))
            c.pendencias.append(Pendencia(pid, tipo, lan.ref_origem, lan.valor, texto, "analista (Lucca)"))
            c.rastro_pendencias.append({
                "id_saida": pid, "arquivo_origem": lan.arquivo_origem, "ref_origem": lan.ref_origem, "valor": lan.valor,
                "linha_arquivo": d.linha_arquivo, "tipo_lancamento": f"EXTRATO {lan.banco}",
                "nota": "lançamento sem regra" + (" e sugestão da IA recusada" if d.resposta else ""),
            })


def cliente_padrao(arquivo_env: Path, regras: dict) -> ClienteIA | None:
    chave = ler_chave(arquivo_env)
    if not chave:
        return None
    return ClienteAnthropic(chave, valor_da_regra(regras, "classificacao.modelo_ia"))

