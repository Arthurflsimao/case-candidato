from decimal import Decimal, InvalidOperation
import re


def normalizar_processo(numero):
    """
    Remove a pontuação do número CNJ e valida sua estrutura.

    Retorna os 20 dígitos do processo.
    """
    if numero is None:
        raise ValueError("Número do processo não informado.")

    numero = str(numero).strip()

    # Mantém somente os caracteres numéricos.
    digitos = re.sub(r"\D", "", numero)

    # Um número CNJ deve possuir exatamente 20 dígitos.
    if len(digitos) != 20:
        raise ValueError(
            f"Número CNJ inválido: esperado 20 dígitos, encontrado {len(digitos)}."
        )

    return digitos



def converter_valor(valor):
    """
    Converte valores monetários para Decimal.

    Aceita:
    - Formato brasileiro: 45.000,00
    - Formato internacional: 45000.00
    - Inteiros: 45000
    - Valores já representados como Decimal.
    """
    if valor is None:
        raise ValueError("Valor monetário não informado.")

    if isinstance(valor, bool):
        raise ValueError("Valor monetário inválido.")

    if isinstance(valor, Decimal):
        resultado = valor
    else:
        texto = str(valor).strip()

        if not texto:
            raise ValueError("Valor monetário não informado.")

        # Formato brasileiro: 45.000,00 ou 2500,50.
        formato_brasileiro = (
            r"-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{1,2}"
        )

        # Formato internacional: 45000.00 ou 45000.
        formato_internacional = (
            r"-?\d+(?:\.\d{1,2})?"
        )

        if re.fullmatch(formato_brasileiro, texto):
            texto = texto.replace(".", "").replace(",", ".")

        elif not re.fullmatch(formato_internacional, texto):
            raise ValueError(
                f"Valor monetário inválido: {valor}"
            )

        try:
            resultado = Decimal(texto)
        except InvalidOperation:
            raise ValueError(
                f"Valor monetário inválido: {valor}"
            )

    if not resultado.is_finite():
        raise ValueError(f"Valor monetário inválido: {valor}")

    return resultado


from datetime import date, datetime



def validar_data(valor):
    """
    Interpreta datas nos formatos ISO e brasileiro.
    Retorna date para datas simples e datetime para timestamps.
    """
    if valor is None or str(valor).strip() == "":
        raise ValueError("Data não informada.")

    texto = str(valor).strip()

    # Data simples no formato AAAA-MM-DD.
    try:
        return date.fromisoformat(texto)
    except ValueError:
        pass

    # Timestamp ISO, com ou sem fuso horário.
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        pass

    # Data no formato brasileiro DD/MM/AAAA.
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        raise ValueError(
            f"Data inválida ou formato não reconhecido: {valor}"
        )

    
def calcular_prazo(data_apresentacao):
    """
    Calcula o prazo de pagamento conforme a regra do case.

    Até 2 de abril: 31/12 do ano seguinte.
    Após 2 de abril: 31/12 do segundo ano seguinte.
    """
    if isinstance(data_apresentacao, datetime):
        data_apresentacao = data_apresentacao.date()

    if not isinstance(data_apresentacao, date):
        raise ValueError("A apresentação precisa ser uma data válida.")

    if (data_apresentacao.month, data_apresentacao.day) <= (4, 2):
        ano_prazo = data_apresentacao.year + 1
    else:
        ano_prazo = data_apresentacao.year + 2

    return date(ano_prazo, 12, 31)


def validar_pagamento(pagamento):
    """
    Valida os campos obrigatórios de um evento de pagamento.

    Retorna uma cópia normalizada do registro.
    """
    if not isinstance(pagamento, dict):
        raise ValueError("Registro de pagamento inválido.")

    evento_id = pagamento.get("evento_id")
    if not isinstance(evento_id, str) or not evento_id.strip():
        raise ValueError("Identificador do evento não informado.")

    processo = normalizar_processo(pagamento.get("processo"))

    tipo = pagamento.get("tipo")
    if tipo not in ("pagamento", "estorno"):
        raise ValueError(f"Tipo de evento inválido: {tipo}")

    valor = converter_valor(pagamento.get("valor"))

    if valor <= 0:
        raise ValueError("O valor do evento deve ser positivo.")

    data_pagamento = validar_data(pagamento.get("data_pagamento"))

    if isinstance(data_pagamento, datetime):
        data_pagamento = data_pagamento.date()

    return {
        **pagamento,
        "evento_id": evento_id.strip(),
        "processo_normalizado": processo,
        "tipo": tipo,
        "valor": valor,
        "data_pagamento": data_pagamento,
    }


def identificar_correcoes(original, normalizado):
    """
    Identifica diferenças entre o registro original
    e o registro após a normalização.
    """
    correcoes = []

    campos = {
        "processo": "processo_normalizado",
        "valor": "valor",
        "data_pagamento": "data_pagamento"
    }

    for campo_original, campo_normalizado in campos.items():
        valor_original = original.get(campo_original)
        valor_tratado = normalizado.get(campo_normalizado)

        if campo_original == "processo":
            original_comparavel = str(valor_original).strip()
            tratado_comparavel = str(valor_tratado).strip()

        elif campo_original == "valor":
            original_comparavel = converter_valor(valor_original)
            tratado_comparavel = converter_valor(valor_tratado)

            # Compara também a representação monetária.
            if original_comparavel == tratado_comparavel:
                original_comparavel = str(valor_original).strip()
                tratado_comparavel = str(valor_tratado)

        elif campo_original == "data_pagamento":
            original_comparavel = str(valor_original).strip()

            if isinstance(valor_tratado, (date, datetime)):
                tratado_comparavel = valor_tratado.isoformat()
            else:
                tratado_comparavel = str(valor_tratado)

        if original_comparavel != tratado_comparavel:
            correcoes.append({
                "campo": campo_original,
                "valor_original": valor_original,
                "valor_normalizado": valor_tratado
            })

    return correcoes
