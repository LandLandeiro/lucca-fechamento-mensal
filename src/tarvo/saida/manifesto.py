"""Manifesto da execução (D95, Q-AM): o que entrou no fechamento, para refazer qualquer número sem perguntar.

`saida/manifesto.csv` é determinístico (vai para o git e o CI compara): cada arquivo da pasta de dados com o papel,
as linhas lidas, o tamanho e o sha256, e a versão das regras (sha256 do regras.yaml, com fim de linha normalizado, e
a contagem por status). Data e hora não entram aqui, senão a saída mudaria a cada execução: vão para um log em
`logs/` (fora do git), um arquivo por execução, com o manifesto e os totais.
"""

import csv
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path

CABECALHO = ["arquivo", "papel", "linhas_lidas", "bytes", "sha256"]


def _conteudo(caminho: Path, texto: bool) -> bytes:
    conteudo = caminho.read_bytes()
    return conteudo.replace(b"\r\n", b"\n") if texto else conteudo  # texto: o mesmo hash no Windows e no Linux


def linhas_manifesto(dados: Path, lidos: dict[str, tuple[str, int]], regras_path: Path, regras: dict,
                     extras: dict[Path, tuple[str, int]] | None = None) -> list[dict]:
    """`lidos`: nome do arquivo de dados → (papel, linhas lidas). Arquivo da pasta que não foi lido entra com o papel
    "não lido". `extras`: arquivos de fora da pasta de dados (ex.: --orbe-anterior), tratados como texto."""
    linhas = []
    for c in sorted(p for p in dados.iterdir() if p.is_file()):
        papel, qtd = lidos.get(c.name, ("não lido (documentação ou arquivo não reconhecido)", None))
        conteudo = _conteudo(c, texto=False)  # data/ é binário no git (-text): os bytes são os que chegaram
        linhas.append({"arquivo": c.name, "papel": papel, "linhas_lidas": "" if qtd is None else qtd,
                       "bytes": len(conteudo), "sha256": hashlib.sha256(conteudo).hexdigest()})
    for c, (papel, qtd) in sorted((extras or {}).items()):
        conteudo = _conteudo(c, texto=True)
        linhas.append({"arquivo": c.name, "papel": papel, "linhas_lidas": qtd,
                       "bytes": len(conteudo), "sha256": hashlib.sha256(conteudo).hexdigest()})
    status = Counter(r["status"] for r in regras.values())
    conteudo = _conteudo(regras_path, texto=True)
    linhas.append({"arquivo": regras_path.name,
                   "papel": "versão das regras: " + " · ".join(f"{s} {status.get(s, 0)}" for s in ("CONFIRMADO", "ASSUMO", "SEI", "PENDENTE")),
                   "linhas_lidas": len(regras), "bytes": len(conteudo), "sha256": hashlib.sha256(conteudo).hexdigest()})
    return linhas


def escrever_manifesto(saida: Path, linhas: list[dict]) -> Path:
    destino = saida / "manifesto.csv"
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CABECALHO, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    return destino


def registrar_execucao(pasta_logs: Path, linhas: list[dict], comando: list[str], totais: dict[str, str],
                       agora: datetime | None = None) -> Path:
    """Um log por execução em `logs/` (no .gitignore): data e hora, comando, manifesto e totais."""
    agora = agora or datetime.now().astimezone()
    pasta_logs.mkdir(parents=True, exist_ok=True)
    destino = pasta_logs / f"execucao_{agora.strftime('%Y%m%d-%H%M%S')}.log"
    texto = [f"execução: {agora.isoformat(timespec='seconds')}", f"comando: {' '.join(comando)}", "", "arquivos:"]
    texto += [f"  {l['arquivo']}; {l['papel']}; linhas lidas {l['linhas_lidas']}; {l['bytes']} bytes; sha256 {l['sha256']}"
              for l in linhas]
    texto += ["", "totais:"] + [f"  {k}: {v}" for k, v in totais.items()]
    destino.write_text("\n".join(texto) + "\n", encoding="utf-8")
    return destino
