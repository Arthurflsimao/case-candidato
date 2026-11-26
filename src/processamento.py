import unicodedata
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

from src.leitores import ler_json, ler_csv, ler_tribunal
from src.validacoes import (
    validar_pagamento,
    normalizar_processo,
    converter_valor,
    validar_data,
    calcular_prazo,
    identificar_correcoes
)


def identificar_duplicados(eventos):
    """
    Agrupa eventos por identificador.

    - Conteúdo sempre idêntico: mantém um registro válido.
    - Conteúdo diferente para o mesmo ID: coloca todos em pendência.
    """
    grupos = {}

    for evento in eventos:
        evento_id = evento["evento_id"]

        if evento_id not in grupos:
            grupos[evento_id] = []

        grupos[evento_id].append(evento)

    validos = []
    duplicados = []
    pendentes = []

    for evento_id, registros in grupos.items():
        primeiro = registros[0]

        todos_iguais = all(
            registro == primeiro
            for registro in registros
        )

        if not todos_iguais:
            pendentes.append({
                "evento_id": evento_id,
                "motivo": "Mesmo identificador encontrado com conteúdo diferente.",
                "registros": registros
            })
            continue

        validos.append(primeiro)

        for _ in registros[1:]:
            duplicados.append({
                "evento_id": evento_id,
                "motivo": "Evento duplicado com conteúdo idêntico."
            })

    return {
        "validos": validos,
        "duplicados": duplicados,
        "pendentes": pendentes
    }


def processar_pagamentos(caminho):
    """
    Lê, valida e identifica duplicidades nos pagamentos.
    """
    registros = ler_json(caminho)

    validacoes_aprovadas = []
    descartados = []

    for registro in registros:
        try:
            pagamento = validar_pagamento(registro)

            pagamento["correcoes"] = identificar_correcoes(
                registro,
                pagamento
            )

            validacoes_aprovadas.append(pagamento)

        except (ValueError, TypeError) as erro:
            descartados.append({
                "registro": registro,
                "motivo": str(erro)
            })

    resultado = identificar_duplicados(validacoes_aprovadas)

    return {
        "validos": resultado["validos"],
        "duplicados": resultado["duplicados"],
        "pendentes": resultado["pendentes"],
        "descartados": descartados
    }


def calcular_saldos(eventos):
    """
    Calcula o saldo líquido de pagamentos por processo.

    Pagamentos aumentam o saldo.
    Estornos diminuem o saldo.
    """
    saldos = defaultdict(lambda: Decimal("0.00"))

    for evento in eventos:
        processo = evento["processo_normalizado"]
        valor = evento["valor"]

        if evento["tipo"] == "pagamento":
            saldos[processo] += valor

        elif evento["tipo"] == "estorno":
            saldos[processo] -= valor

    return dict(saldos)


def indexar_por_processo(registros, campo_processo):
    """
    Organiza registros em um dicionário usando o CNJ normalizado
    como chave.
    """
    indice = {}

    for registro in registros:
        processo = normalizar_processo(
            registro.get(campo_processo)
        )

        if processo in indice:
            raise ValueError(
                f"Processo duplicado encontrado: {processo}"
            )

        indice[processo] = registro

    return indice


def comparar_processos(hub, tribunal):
    """
    Compara os processos do Hub com os do Tribunal.

    Retorna os processos encontrados nos dois arquivos
    e aqueles que aparecem em apenas uma das fontes.
    """
    processos_hub = set(hub.keys())
    processos_tribunal = set(tribunal.keys())

    presentes_nos_dois = processos_hub & processos_tribunal
    somente_hub = processos_hub - processos_tribunal
    somente_tribunal = processos_tribunal - processos_hub

    return {
        "presentes_nos_dois": presentes_nos_dois,
        "somente_hub": somente_hub,
        "somente_tribunal": somente_tribunal
    }


def normalizar_texto(texto):
    """
    Padroniza textos para comparação.

    Remove acentos, espaços excedentes e diferenças
    entre letras maiúsculas e minúsculas.
    """
    if texto is None:
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    return " ".join(texto.split())


def conciliar_dados(hub, tribunal):
    """
    Compara os dados do Hub e do Tribunal.

    Registra também processos encontrados em apenas
    uma das fontes.
    """
    conciliacao = []

    todos_processos = set(hub.keys()) | set(tribunal.keys())

    for processo in sorted(todos_processos):
        registro_hub = hub.get(processo)
        registro_tribunal = tribunal.get(processo)

        # Processo presente nas duas fontes.
        if registro_hub and registro_tribunal:
            valor_hub = converter_valor(
                registro_hub["valor_face"]
            )

            valor_tribunal = converter_valor(
                registro_tribunal["valor_face"]
            )

            ente_hub = normalizar_texto(
                registro_hub["ente"]
            )

            ente_tribunal = normalizar_texto(
                registro_tribunal["ente_devedor"]
            )

            conciliacao.append({
                "processo": processo,
                "situacao": (
                    "conciliado"
                    if valor_hub == valor_tribunal and ente_hub == ente_tribunal
                    else "divergente"
                ),
                "valor_hub": valor_hub,
                "valor_tribunal": valor_tribunal,
                "valores_iguais": valor_hub == valor_tribunal,
                "diferenca_valor": valor_tribunal - valor_hub,
                "ente_hub": registro_hub["ente"],
                "ente_tribunal": registro_tribunal["ente_devedor"],
                "entes_iguais": ente_hub == ente_tribunal
            })

        # Processo encontrado somente no Hub.
        elif registro_hub:
            conciliacao.append({
                "processo": processo,
                "situacao": "somente_hub",
                "valor_hub": converter_valor(
                    registro_hub["valor_face"]
                ),
                "valor_tribunal": None,
                "valores_iguais": None,
                "diferenca_valor": None,
                "ente_hub": registro_hub["ente"],
                "ente_tribunal": None,
                "entes_iguais": None
            })

        # Processo encontrado somente no Tribunal.
        else:
            conciliacao.append({
                "processo": processo,
                "situacao": "somente_tribunal",
                "valor_hub": None,
                "valor_tribunal": converter_valor(
                    registro_tribunal["valor_face"]
                ),
                "valores_iguais": None,
                "diferenca_valor": None,
                "ente_hub": None,
                "ente_tribunal": registro_tribunal["ente_devedor"],
                "entes_iguais": None
            })

    return conciliacao



def conferir_prazos(hub, apresentacoes):
    """
    Compara os prazos do Hub com os prazos calculados.

    Datas com fuso horário ficam pendentes de confirmação,
    pois a regra de referência temporal ainda não foi definida.
    """
    resultados = []

    for apresentacao in apresentacoes:
        processo = normalizar_processo(
            apresentacao["processo"]
        )

        if processo not in hub:
            resultados.append({
                "processo": processo,
                "situacao": "Pendente",
                "motivo": "Processo não encontrado no Hub."
            })
            continue

        data_original = apresentacao["apresentado_em"]
        data_apresentacao = validar_data(data_original)

        prazo_hub = validar_data(
            hub[processo]["prazo_pagamento"]
        )

        prazo_calculado = calcular_prazo(data_apresentacao)

        # Não assumir uma regra de fuso horário ainda não confirmada.
        if (
            isinstance(data_apresentacao, datetime)
            and data_apresentacao.tzinfo is not None
        ):
            resultados.append({
                "processo": processo,
                "data_apresentacao": data_apresentacao,
                "prazo_hub": prazo_hub,
                "prazo_calculado": prazo_calculado,
                "situacao": "Pendente",
                "motivo": "Aguardando confirmação do fuso horário pelo tribunal."
            })
            continue

        if prazo_calculado == prazo_hub:
            situacao = "Conferido"
            motivo = None
        else:
            situacao = "Divergente"
            motivo = "Prazo registrado no Hub diferente do prazo calculado."

        resultados.append({
            "processo": processo,
            "data_apresentacao": data_apresentacao,
            "prazo_hub": prazo_hub,
            "prazo_calculado": prazo_calculado,
            "situacao": situacao,
            "motivo": motivo
        })

    return resultados


def executar_processamento(
    caminho_pagamentos,
    caminho_apresentacoes,
    caminho_hub,
    caminho_tribunal
):
    """
    Executa o processamento completo dos arquivos do case.

    Reúne validações, pagamentos, saldos,
    conciliação e conferência de prazos.
    """

    # 1. Processa e valida os pagamentos.
    pagamentos = processar_pagamentos(caminho_pagamentos)

    # 2. Calcula os saldos considerando apenas eventos válidos.
    saldos = calcular_saldos(pagamentos["validos"])

    # 3. Lê os arquivos originais.
    apresentacoes = ler_json(caminho_apresentacoes)
    registros_hub = ler_csv(caminho_hub)
    registros_tribunal = ler_tribunal(caminho_tribunal)

    # 4. Indexa os registros pelo número CNJ normalizado.
    hub = indexar_por_processo(
        registros_hub,
        "processo"
    )

    tribunal = indexar_por_processo(
        registros_tribunal,
        "numero_processo"
    )

    # 5. Identifica processos presentes e ausentes nas fontes.
    comparacao = comparar_processos(hub, tribunal)

    # 6. Compara valores e entes dos processos em comum.
    conciliacao = conciliar_dados(hub, tribunal)

    # 7. Confere os prazos de pagamento.
    prazos = conferir_prazos(hub, apresentacoes)

    # 8. Reúne todos os resultados.
    return {
        "pagamentos": pagamentos,
        "saldos": saldos,
        "comparacao_processos": comparacao,
        "conciliacao": conciliacao,
        "prazos": prazos
    }


