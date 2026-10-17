"""IA nas sobras (E6b parte 2, D42): a IA sugere, o código prova. Sem rede: cliente mockado + cache em pasta temporária.

Em setembro nenhuma linha precisa da IA: a regra reconhece a EduAbroad pelo nome da Orbe ligado ao EC (D52).
Aqui o caso é o que a IA existe para resolver: um nome NOVO no extrato. Numa cópia do data pack, os 7 PIX da
EduAbroad chegam como "EDU ABROAD INTL SERVICOS", que não está na planilha, no relatório da Orbe nem nos aliases.
"""

import csv
from decimal import Decimal

import pytest

from tarvo.__main__ import executar, main
from tarvo.classificacao.por_ia import SugestaoIA, ler_chave
from conftest import DADOS, RAIZ, copiar_dados

EDU = "16181276000153"  # EduAbroad
MUNDO_ABERTO = "17217888000111"
SOBRAS = {"AURORA-L28", "AURORA-L69", "MERIDIANO-MRD2026090036", "MERIDIANO-MRD2026090180",
          "MERIDIANO-MRD2026090340", "MERIDIANO-MRD2026090484", "MERIDIANO-MRD2026090636"}
NOME_NOVO = "EDU ABROAD INTL SERVICOS"
TROCAS = {"05a_*.csv": [(b"PIX ENVIADO EDU ABROAD CONSULTORIA LTD", b"PIX ENVIADO " + NOME_NOVO.encode())],
          "05b_*.ofx": [(b"PIX RECEB EDU ABROAD CONSULTORIA L", b"PIX RECEB " + NOME_NOVO.encode())]}


class ClienteFalso:
    """Devolve a sugestão de `responder(entrada)` e conta as chamadas; nunca toca a rede."""

    def __init__(self, responder):
        self.responder = responder
        self.chamadas = []

    def sugerir(self, sistema, entrada):
        assert "{{CONTAS}}" not in sistema and "2.1.02.001" in sistema and EDU in sistema
        self.chamadas.append(entrada)
        return self.responder(entrada), {"input_tokens": 1000, "output_tokens": 100}


def valida(entrada):
    if entrada["banco"] == "AURORA":
        return SugestaoIA(conta_codigo="2.1.01.001", lojista_cnpj=EDU, justificativa="repasse à EduAbroad", confianca=0.95)
    return SugestaoIA(conta_codigo="2.1.02.001", lojista_cnpj=EDU, justificativa="aporte da EduAbroad", confianca=0.95)


def _csv(pasta, nome):
    with open(pasta / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _dados_nome_novo(tmp_path):
    destino = tmp_path / "dados_nome_novo"
    return destino if destino.exists() else copiar_dados(destino, TROCAS)


def _rodar(tmp_path, nome, cliente, cache=None):
    pasta = tmp_path / nome
    r = executar(_dados_nome_novo(tmp_path), pasta, RAIZ / "regras.yaml", cliente_ia=cliente,
                 cache_ia=cache or (tmp_path / "cache"))
    lan = {f"{l['banco']}-{l['ref_origem']}": l for l in _csv(pasta, "lancamentos_classificados.csv")}
    pend = {p["id_saida"]: p for p in _csv(pasta, "pendencias.csv")}
    return r, pasta, lan, pend


def test_i_sugestao_valida_vira_ia_e_vai_para_o_cache(tmp_path):
    cliente = ClienteFalso(valida)
    r, pasta, lan, pend = _rodar(tmp_path, "s1", cliente)
    assert r["erros_validacao"] == []
    assert len(cliente.chamadas) == 7
    for k in SOBRAS:
        assert lan[k]["metodo"] == "IA" and lan[k]["confianca"] == "0.95", k
    assert lan["AURORA-L28"]["conta_codigo"] == "2.1.01.001" and lan["MERIDIANO-MRD2026090036"]["conta_codigo"] == "2.1.02.001"
    assert not [p for p in pend if "SEM_REGRA" in p or "IA_REPROVADA" in p]
    # (c) Meridiano: a soma fecha e a EduAbroad passa a ser conferida (sem "não conferido")
    edu = next(a for a in r["extratos"]["conf"].aportes if a["cnpj"] == EDU)
    assert edu["aportes"] == edu["operacoes"] == Decimal("394222.69") and not edu["nao_conferido"]
    d = next(d for d in r["extratos"]["ia"].decisoes if d.lan.ref_origem == "MRD2026090036")
    assert any(item == "c" and ok and "394222.69 (regra 0.00 + IA 394222.69) = Σ (Valor R$ + IOF) das operações na Ponte 394222.69" in det for item, ok, det in d.checagens)
    # aprendizado: alias proposto (nome novo), não aplicado no mês
    sug = _csv(pasta, "sugestoes_regra.csv")
    assert {(s["tipo"], s["banco"], s["padrao_ou_nome"], s["lojista_cnpj"], s["status"]) for s in sug} == {
        ("ALIAS_LOJISTA", "AURORA", NOME_NOVO, EDU, "PROPOSTA"),
        ("ALIAS_LOJISTA", "MERIDIANO", NOME_NOVO, EDU, "PROPOSTA"),
    }
    assert len(list((tmp_path / "cache").glob("*.json"))) == 7
    # reexecução sem cliente: tudo do cache, mesmo resultado, zero chamadas
    r2, pasta2, lan2, _ = _rodar(tmp_path, "s1b", None)
    assert r2["extratos"]["ia"].chamadas_api == 0
    assert (pasta / "lancamentos_classificados.csv").read_bytes() == (pasta2 / "lancamentos_classificados.csv").read_bytes()


@pytest.mark.parametrize("caso, responder, item", [
    ("ii_conta_inexistente", lambda e: SugestaoIA(conta_codigo="9.9.99", lojista_cnpj=EDU, justificativa="x", confianca=0.95), "(a)"),
    ("iii_confianca_baixa", lambda e: valida(e).model_copy(update={"confianca": 0.5}), "(d)"),
])
def test_ii_iii_conta_inexistente_ou_confianca_baixa_viram_humano(tmp_path, caso, responder, item):
    r, _, lan, pend = _rodar(tmp_path, caso, ClienteFalso(responder))
    assert r["erros_validacao"] == []
    for k in SOBRAS:
        assert (lan[k]["metodo"], lan[k]["conta_codigo"], lan[k]["confianca"]) == ("HUMANO", "", "0.00"), k
        p = pend[f"PEN-IA_REPROVADA-{k}"]
        assert item in p["motivo"] and p["quem_decide"] == "analista (Lucca)"


def test_iv_lojista_cuja_soma_nao_bate_vira_humano(tmp_path):
    def responder(e):
        if e["banco"] == "MERIDIANO":  # atribui os aportes a outro lojista: a soma dele deixa de fechar
            return SugestaoIA(conta_codigo="2.1.02.001", lojista_cnpj=MUNDO_ABERTO, justificativa="x", confianca=0.95)
        return valida(e)
    r, _, lan, pend = _rodar(tmp_path, "iv", ClienteFalso(responder))
    assert r["erros_validacao"] == []
    for k in SOBRAS:
        if k.startswith("MERIDIANO"):
            assert lan[k]["metodo"] == "HUMANO"
            assert "(c)" in pend[f"PEN-IA_REPROVADA-{k}"]["motivo"] and "≠ Σ (Valor R$ + IOF)" in pend[f"PEN-IA_REPROVADA-{k}"]["motivo"]
        else:  # Aurora: EduAbroad tem vendas na Orbe no mês
            assert lan[k]["metodo"] == "IA"


def test_conta_que_exige_lojista_sem_lojista_vira_humano(tmp_path):
    r, _, lan, pend = _rodar(tmp_path, "b", ClienteFalso(lambda e: valida(e).model_copy(update={"lojista_cnpj": None})))
    assert lan["MERIDIANO-MRD2026090036"]["metodo"] == "HUMANO"
    assert "exige lojista" in pend["PEN-IA_REPROVADA-MERIDIANO-MRD2026090036"]["motivo"]


def test_sem_chave_e_sem_cache_vira_humano_com_aviso(tmp_path):
    r, _, lan, pend = _rodar(tmp_path, "sem", None, cache=tmp_path / "vazio")
    assert r["erros_validacao"] == []
    assert all(lan[k]["metodo"] == "HUMANO" for k in SOBRAS)
    assert "sem chave da API e sem resposta em cache" in pend["PEN-SEM_REGRA-AURORA-L28"]["motivo"]
    assert any("sem chave" in a.mensagem for a in r["avisos"])


def test_cli_sem_ia_sai_com_zero(tmp_path):
    assert main(["--dados", str(DADOS), "--saida", str(tmp_path / "s"), "--sem-ia"]) == 0
    pend = _csv(tmp_path / "s", "pendencias.csv")
    assert not [p for p in pend if p["tipo"] == "SEM_REGRA"]  # setembro: tudo por regra (D52)


def test_setembro_nao_manda_nada_para_a_ia(tmp_path):
    """D52: regra primeiro, sempre. Com o nome da Orbe ligado ao EC, as 7 linhas da EduAbroad são REGRA."""
    r = executar(DADOS, tmp_path / "s", RAIZ / "regras.yaml", cliente_ia=ClienteFalso(valida), cache_ia=tmp_path / "c")
    assert r["extratos"]["ia"].decisoes == [] and r["extratos"]["ia"].chamadas_api == 0
    lan = {f"{l['banco']}-{l['ref_origem']}": l for l in _csv(tmp_path / "s", "lancamentos_classificados.csv")}
    assert all(lan[k]["metodo"] == "REGRA" for k in SOBRAS)


def test_chave_vem_do_env_local_e_nunca_aparece(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("TARVO_SEM_REDE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = tmp_path / ".env.local"
    env.write_text("# comentário\nANTHROPIC_API_KEY=chave-de-teste-123\n", encoding="utf-8")
    assert ler_chave(env) == "chave-de-teste-123"
    assert ler_chave(tmp_path / "nao_existe") is None
    monkeypatch.setenv("TARVO_SEM_REDE", "1")
    assert ler_chave(env) is None  # testes: nunca rede
    assert "chave-de-teste-123" not in capsys.readouterr().out


def test_confianca_com_tres_casas_e_quantizada_antes_do_cache(tmp_path):
    """Bug (avaliação simulada): 0.855 ia para o cache e a saída recusava a fração de centavo, quebrando toda
    execução seguinte. Agora: 2 casas antes de gravar (0.855 → 0.86), e o cache sai com 0.86."""
    import json
    cliente = ClienteFalso(lambda e: valida(e).model_copy(update={"confianca": 0.855}))
    r, _, lan, _ = _rodar(tmp_path, "q", cliente)
    assert r["erros_validacao"] == []
    assert all(lan[k]["metodo"] == "IA" and lan[k]["confianca"] == "0.86" for k in SOBRAS)
    assert {json.loads(p.read_text(encoding="utf-8"))["resposta"]["confianca"] for p in (tmp_path / "cache").glob("*.json")} == {0.86}


def test_cache_antigo_com_tres_casas_e_lido_sem_erro(tmp_path):
    """Um cache gravado antes da correção (0.857) é lido e arredondado (0.86), sem derrubar a execução."""
    import json
    _rodar(tmp_path, "a", ClienteFalso(valida))
    for p in (tmp_path / "cache").glob("*.json"):
        dados = json.loads(p.read_text(encoding="utf-8"))
        dados["resposta"]["confianca"] = 0.857
        p.write_text(json.dumps(dados), encoding="utf-8")
    r, _, lan, _ = _rodar(tmp_path, "b", None)
    assert r["erros_validacao"] == [] and r["extratos"]["ia"].chamadas_api == 0
    assert all(lan[k]["confianca"] == "0.86" for k in SOBRAS)


def test_com_chave_usa_o_cliente_real_e_sem_chave_o_cache(tmp_path, monkeypatch):
    """Item 8: com chave (e sem TARVO_SEM_REDE) o caminho cria o cliente da API; sem chave, None → só cache."""
    from tarvo.classificacao.por_ia import ClienteAnthropic, cliente_padrao
    from tarvo.regras import carregar_regras
    regras = carregar_regras(RAIZ / "regras.yaml")
    env = tmp_path / ".env.local"
    env.write_text("ANTHROPIC_API_KEY=chave-de-teste\n", encoding="utf-8")
    monkeypatch.delenv("TARVO_SEM_REDE", raising=False)
    assert isinstance(cliente_padrao(env, regras), ClienteAnthropic)  # não chama a rede ao criar
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert cliente_padrao(tmp_path / "sem_env", regras) is None


def test_fixture_de_outubro_responde_pelo_cache_commitado(tmp_path):
    """O comando do README sem chave: a linha de nome novo vem de cache_ia/ (resposta real gravada) e é aceita."""
    from tarvo.__main__ import CACHE_IA_PADRAO
    r = executar(RAIZ / "tests" / "fixtures" / "outubro", tmp_path / "s", RAIZ / "regras.yaml", cache_ia=CACHE_IA_PADRAO)
    (d,) = r["extratos"]["ia"].decisoes
    assert d.resposta.origem == "CACHE" and d.aceita and d.resposta.sugestao.lojista_cnpj == "14760206000124"
    (s,) = _csv(tmp_path / "s", "sugestoes_regra.csv")
    assert (s["padrao_ou_nome"], s["status"]) == ("NEI EDUCACAO INTERNACIONAL", "PROPOSTA")
