
import unittest
from decimal import Decimal
from datetime import date

from src.validacoes import (
    normalizar_processo,
    converter_valor,
    validar_data,
    calcular_prazo,
    validar_pagamento,
    identificar_correcoes
)


class TestValidacoes(unittest.TestCase):

    def test_normalizar_processo(self):
        processo = "0012345-10.2019.8.26.0053"

        resultado = normalizar_processo(processo)

        self.assertEqual(resultado, "00123451020198260053")

    def test_normalizar_processo_invalido(self):
        with self.assertRaises(ValueError):
            normalizar_processo("12345")

    def test_converter_valor(self):
        resultado = converter_valor("2.500,50")

        self.assertEqual(resultado, Decimal("2500.50"))

    def test_converter_valor_invalido(self):
        with self.assertRaises(ValueError):
            converter_valor(None)

    def test_validar_data(self):
        resultado = validar_data("2025-04-02")

        self.assertEqual(resultado, date(2025, 4, 2))

    def test_calcular_prazo_antes_do_limite(self):
        resultado = calcular_prazo(date(2025, 4, 2))

        self.assertEqual(resultado, date(2026, 12, 31))

    def test_calcular_prazo_depois_do_limite(self):
        resultado = calcular_prazo(date(2025, 4, 3))

        self.assertEqual(resultado, date(2027, 12, 31))

    def test_validar_pagamento(self):
        pagamento = {
            "evento_id": "teste-001",
            "processo": "0012345-10.2019.8.26.0053",
            "valor": "2.500,50",
            "tipo": "pagamento",
            "data_pagamento": "2025-04-10"
        }

        resultado = validar_pagamento(pagamento)

        self.assertEqual(resultado["evento_id"], "teste-001")
        self.assertEqual(
            resultado["processo_normalizado"],
            "00123451020198260053"
        )
        self.assertEqual(resultado["valor"], Decimal("2500.50"))

    def test_validar_pagamento_invalido(self):
        pagamento = {
            "evento_id": "teste-002",
            "processo": "",
            "valor": 1000,
            "tipo": "pagamento",
            "data_pagamento": "2025-04-10"
        }

        with self.assertRaises(ValueError):
            validar_pagamento(pagamento)

    def test_identificar_correcoes(self):
        original = {
            "evento_id": "teste-003",
            "processo": "0012345-10.2019.8.26.0053",
            "valor": "2.500,50",
            "tipo": "pagamento",
            "data_pagamento": "10/04/2025"
        }

        normalizado = validar_pagamento(original)

        resultado = identificar_correcoes(original, normalizado)

        campos = [correcao["campo"] for correcao in resultado]

        self.assertEqual(len(resultado), 3)
        self.assertIn("processo", campos)
        self.assertIn("valor", campos)
        self.assertIn("data_pagamento", campos)

    def test_identificar_correcoes_sem_alteracoes(self):
        original = {
            "evento_id": "teste-004",
            "processo": "00123451020198260053",
            "valor": "2500.50",
            "tipo": "pagamento",
            "data_pagamento": "2025-04-10"
        }

        normalizado = validar_pagamento(original)

        resultado = identificar_correcoes(original, normalizado)

        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()
