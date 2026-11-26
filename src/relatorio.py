import csv
import json
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path


def serializar_valor(valor):
    """
    Converte tipos especiais do Python para formatos
    compatíveis com JSON.
    """
    if isinstance(valor, Decimal):
        return str(valor)

    if isinstance(valor, (date, datetime)):
        return valor.isoformat()

    if isinstance(valor, set):
        return sorted(valor)

    raise TypeError(
        f"Tipo de dado não suportado: {type(valor).__name__}"
    )


def salvar_json(dados, caminho):
    """
    Salva os dados em um arquivo JSON.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=4,
            default=serializar_valor
        )


def formatar_valor_csv(valor):
    """
    Padroniza valores antes de gravá-los em CSV.
    """

    if isinstance(valor, Decimal):
        return f"{valor:.2f}"

    if isinstance(valor, (date, datetime)):
        return valor.isoformat()

    if valor is None:
        return ""

    return valor


def salvar_csv(registros, caminho):
    """
    Salva uma lista de dicionários em um arquivo CSV.
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    if not registros:
        return

    campos = list(
        dict.fromkeys(
            campo
            for registro in registros
            for campo in registro.keys()
        )
    )

    with caminho.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos,
            delimiter=";"
        )

        escritor.writeheader()
        escritor.writerows([
    {
        campo: formatar_valor_csv(valor)
        for campo, valor in registro.items()
    }
    for registro in registros
])


def gerar_relatorio_pagamentos(pagamentos):
    """
    Reúne pagamentos válidos, duplicados,
    pendentes e descartados em uma lista.
    """

    registros = []

    # Pagamentos válidos.
    for pagamento in pagamentos["validos"]:
        registros.append({
            "status": "valido",
            "evento_id": pagamento.get("evento_id"),
            "processo": pagamento.get("processo_normalizado"),
            "valor": pagamento.get("valor"),
            "tipo": pagamento.get("tipo"),
            "data_pagamento": pagamento.get("data_pagamento"),
            "motivo": ""
        })

    # Pagamentos duplicados.
    for pagamento in pagamentos["duplicados"]:
        registros.append({
            "status": "duplicado",
            "evento_id": pagamento.get("evento_id"),
            "processo": "",
            "valor": "",
            "tipo": "",
            "data_pagamento": "",
            "motivo": pagamento.get("motivo")
        })

    # Pagamentos pendentes.
    for pagamento in pagamentos["pendentes"]:
        for registro in pagamento.get("registros", []):
            registros.append({
                "status": "pendente",
                "evento_id": pagamento.get("evento_id"),
                "processo": registro.get("processo_normalizado"),
                "valor": registro.get("valor"),
                "tipo": registro.get("tipo"),
                "data_pagamento": registro.get("data_pagamento"),
                "motivo": pagamento.get("motivo")
            })

    # Pagamentos descartados.
    for pagamento in pagamentos["descartados"]:
        registro = pagamento.get("registro", {})

        registros.append({
            "status": "descartado",
            "evento_id": registro.get("evento_id"),
            "processo": (
    "".join(
        caractere
        for caractere in str(registro.get("processo", ""))
        if caractere.isdigit()
    )
        if registro.get("processo")
        else ""
),
            "valor": registro.get("valor"),
            "tipo": registro.get("tipo"),
            "data_pagamento": registro.get("data_pagamento"),
            "motivo": pagamento.get("motivo")
        })

    return registros


def gerar_relatorio_saldos(saldos):
    """
    Converte os saldos agrupados por processo
    em uma lista de registros para exportação.
    """

    registros = []

    for processo, saldo in sorted(saldos.items()):
        registros.append({
            "processo": processo,
            "saldo": saldo
        })

    return registros


def gerar_relatorio_conciliacao(conciliacao):
    """
    Prepara os resultados da conciliação
    entre os dados do Hub e do Tribunal.
    """

    registros = []

    for item in conciliacao:
        registros.append({
            "processo": item.get("processo"),
            "valor_hub": item.get("valor_hub"),
            "valor_tribunal": item.get("valor_tribunal"),
            "diferenca_valor": item.get("diferenca_valor"),
            "valores_iguais": item.get("valores_iguais"),
            "ente_hub": item.get("ente_hub"),
            "ente_tribunal": item.get("ente_tribunal"),
            "entes_iguais": item.get("entes_iguais")
        })

    return registros


def gerar_relatorio_prazos(prazos):
    """
    Prepara os resultados da conferência
    dos prazos de pagamento.
    """

    registros = []

    for item in prazos:
        registros.append({
            "processo": item.get("processo"),
            "data_apresentacao": item.get("data_apresentacao"),
            "prazo_hub": item.get("prazo_hub"),
            "prazo_calculado": item.get("prazo_calculado"),
            "situacao": item.get("situacao"),
            "motivo": item.get("motivo", "")
        })

    return registros


def gerar_relatorios(resultado, diretorio_saida="saida"):
    """
    Gera todos os relatórios do processamento.
    """

    diretorio_saida = Path(diretorio_saida)
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    pagamentos = resultado["pagamentos"]
    saldos = resultado["saldos"]
    conciliacao = resultado["conciliacao"]
    prazos = resultado["prazos"]

    # 1. Relatório de pagamentos.
    registros_pagamentos = gerar_relatorio_pagamentos(pagamentos)

    salvar_csv(
        registros_pagamentos,
        diretorio_saida / "pagamentos.csv"
    )

    # 2. Relatório de saldos.
    registros_saldos = gerar_relatorio_saldos(saldos)

    salvar_csv(
        registros_saldos,
        diretorio_saida / "saldos.csv"
    )

    # 3. Relatório de conciliação.
    registros_conciliacao = gerar_relatorio_conciliacao(conciliacao)

    salvar_csv(
        registros_conciliacao,
        diretorio_saida / "conciliacao.csv"
    )

    # 4. Relatório de prazos.
    registros_prazos = gerar_relatorio_prazos(prazos)

    salvar_csv(
        registros_prazos,
        diretorio_saida / "prazos.csv"
    )

    # 5. Relatório geral em JSON.
    relatorio = {
        "resumo_pagamentos": {
            "validos": len(pagamentos["validos"]),
            "duplicados": len(pagamentos["duplicados"]),
            "pendentes": len(pagamentos["pendentes"]),
            "registros_em_conflito": sum(
                len(item.get("registros", []))
                for item in pagamentos["pendentes"]
            ),
            "descartados": len(pagamentos["descartados"])
        },
        "saldos": registros_saldos,
        "comparacao_processos": {
            chave: sorted(valores)
            for chave, valores
            in resultado["comparacao_processos"].items()
        },
        "conciliacao": registros_conciliacao,
        "prazos": registros_prazos
    }

    salvar_json(
        relatorio,
        diretorio_saida / "relatorio.json"
    )

    return {
        "diretorio": str(diretorio_saida),
        "arquivos": [
            "pagamentos.csv",
            "saldos.csv",
            "conciliacao.csv",
            "prazos.csv",
            "relatorio.json"
        ]
    }
