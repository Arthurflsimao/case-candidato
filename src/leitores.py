import csv
import json
from pathlib import Path


def ler_json(caminho):
    """Lê um arquivo JSON e retorna seus registros."""
    caminho = Path(caminho)

    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, list):
        raise ValueError(f"O arquivo {caminho} deveria conter uma lista de registros.")

    return dados


def ler_csv(caminho, delimitador=",", codificacao="utf-8-sig"):
    """Lê um arquivo CSV e retorna seus registros como dicionários."""
    caminho = Path(caminho)

    with caminho.open("r", encoding=codificacao, newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimitador)

        if leitor.fieldnames is None:
            raise ValueError(f"O arquivo {caminho} não possui cabeçalho.")

        return list(leitor)


def ler_tribunal(caminho):
    """Lê o CSV do tribunal considerando seu formato real."""
    return ler_csv(
        caminho,
        delimitador=";",
        codificacao="cp1252"
    )
