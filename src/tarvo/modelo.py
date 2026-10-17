"""Modelo de dados: dataclasses trocadas entre as etapas.

Responsabilidade: só estrutura, sem lógica. Dinheiro sempre em `Decimal` (centavos
exatos); percentuais em `Decimal` sem arredondar. Todo registro lido carrega
`arquivo_origem` e `ref_origem` desde o leitor, para o rastro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TransacaoOrbe:
    """Uma linha do relatório da Orbe (venda, estorno, antecipação ou reversão)."""

    ref_origem: str  # id_transacao
    linha_arquivo: int
    data_movimento: date
    cod_estabelecimento: str
    nome_estabelecimento: str
    tipo_lancamento: str
    modalidade: str | None
    qtd_parcelas: int | None
    bandeira: str | None
    valor_bruto: Decimal
    taxa_aplicada_pct: Decimal
    valor_taxa: Decimal
    valor_liquido: Decimal
    id_referencia: str | None
    data_venda_original: date | None
    arquivo_origem: str = ""


@dataclass(frozen=True)
class TaxaContratada:
    """Uma linha da aba "Taxas vigentes" (valores crus; a interpretação fica em `cadastro`)."""

    linha_planilha: int
    lojista: str
    cnpj_bruto: str | None  # como veio (repr da célula)
    cnpj: str | None  # 14 dígitos, ou None se não deu para normalizar
    ec_orbe: str | None
    taxas: dict[str, Decimal | str | None]  # coluna -> fração exata, texto não interpretado, ou None
    vigencia_texto: str | None
    obs: str | None
    comentario: str | None = None


@dataclass(frozen=True)
class Aviso:
    """Leitura estranha encontrada por um leitor ou pelo cadastro. Nunca é resolvida por chute."""

    arquivo: str
    local: str  # ex.: "L39", "R14"
    mensagem: str


@dataclass(frozen=True)
class OperacaoPonte:
    """Uma linha da aba "Operações" do anexo da Ponte Câmbio."""

    ref_origem: str  # Nº Operação (pode repetir: a duplicidade é tratada depois)
    linha_planilha: int
    data_contratacao: date
    data_liquidacao: date
    cnpj_cliente_bruto: str
    cliente: str
    moeda: str
    valor_me: Decimal
    taxa_cliente: Decimal
    ptax_ref: Decimal
    valor_brl: Decimal
    spread_brl: Decimal
    spread_pct: Decimal
    spread_estimado_brl: Decimal
    iof_brl: Decimal
    status_compliance: str
    observacao: str | None
    arquivo_origem: str = ""


@dataclass(frozen=True)
class ContaContabil:
    """Uma conta do plano de contas do ERP Fênix."""

    codigo: str
    descricao: str
    tipo: str  # SINTETICA | ANALITICA
    natureza: str  # D | C
    aceita_lancamento: bool
    codigo_superior: str | None


@dataclass(frozen=True)
class LancamentoBancario:
    """Um lançamento de extrato (Aurora ou Meridiano)."""

    banco: str  # AURORA | MERIDIANO
    ref_origem: str  # L<linha física> no Aurora, FITID no Meridiano
    data: date
    descricao: str
    valor: Decimal
    documento: str | None = None
    arquivo_origem: str = ""


@dataclass(frozen=True)
class Lojista:
    """Lojista no cadastro unificado. Chave: CNPJ com 14 dígitos."""

    cnpj: str
    nome: str
    ecs_orbe: tuple[str, ...] = ()
    ativo: bool = True


@dataclass(frozen=True)
class ItemRastro:
    """Liga um número de saída a uma linha de origem. Soma por id_saida = número reportado."""

    id_saida: str
    arquivo_origem: str
    ref_origem: str
    valor: Decimal


@dataclass(frozen=True)
class Pendencia:
    """Algo que exige uma pessoa."""

    id_saida: str
    tipo: str
    ref_origem: str
    valor_brl: Decimal | None
    motivo: str
    quem_decide: str


@dataclass
class ResultadoFechamento:
    """Tudo que a saída escreve (preenchido pelas etapas de cálculo e classificação)."""

    comissoes: list[dict] = field(default_factory=list)
    divergencias: list[dict] = field(default_factory=list)
    notas: list[dict] = field(default_factory=list)
    lancamentos: list[dict] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    rastro: list[ItemRastro] = field(default_factory=list)
