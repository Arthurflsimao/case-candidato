
import unittest
from decimal import Decimal

from src.processamento import (
    identificar_duplicados,
    calcular_saldos,
    conciliar_dados
)


class TestProcessamento(unittest.TestCase):

    def test_identificar_evento_duplicado(self):
        eventos = [
            {
                "evento_id": "ev-001",
                "valor": 1500,
                "tipo": "pagamento"
            },
            {
                "evento_id": "ev-001",
                "valor": 1500,
                "tipo": "pagamento"
            }
        ]

        resultado = identificar_duplicados(eventos)

        self.assertEqual(len(resultado["validos"]), 1)
        self.assertEqual(len(resultado["duplicados"]), 1)
        self.assertEqual(len(resultado["pendentes"]), 0)

    def test_identificar_conflito_de_evento(self):
        eventos = [
            {
                "evento_id": "ev-002",
                "valor": 1500,
                "tipo": "pagamento"
            },
            {
                "evento_id": "ev-002",
                "valor": 2000,
                "tipo": "pagamento"
            }
        ]

        resultado = identificar_duplicados(eventos)

        self.assertEqual(len(resultado["validos"]), 0)
        self.assertEqual(len(resultado["duplicados"]), 0)
        self.assertEqual(len(resultado["pendentes"]), 1)

        self.assertEqual(
            len(resultado["pendentes"][0]["registros"]),
            2
        )

    def test_calcular_saldos_com_estorno(self):
        eventos = [
            {
                "processo_normalizado": "00123451020198260053",
                "valor": Decimal("5000.00"),
                "tipo": "pagamento"
            },
            {
                "processo_normalizado": "00123451020198260053",
                "valor": Decimal("2000.00"),
                "tipo": "estorno"
            }
        ]

        resultado = calcular_saldos(eventos)

        self.assertEqual(
            resultado["00123451020198260053"],
            Decimal("3000.00")
        )

    def test_conciliar_diferenca_de_valores(self):
        processo = "00123451020198260053"

        hub = {
            processo: {
                "numero_processo": "0012345-10.2019.8.26.0053",
                "ente": "Município de São Paulo",
                "valor_face": "31.000,00"
            }
        }

        tribunal = {
            processo: {
                "numero_processo": "0012345-10.2019.8.26.0053",
                "ente_devedor": "Município de São Paulo",
                "valor_face": "30.000,00"
            }
        }

        resultado = conciliar_dados(hub, tribunal)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["situacao"], "divergente")
        self.assertFalse(resultado[0]["valores_iguais"])

        self.assertEqual(
            resultado[0]["diferenca_valor"],
            Decimal("-1000.00")
        )

        self.assertTrue(resultado[0]["entes_iguais"])

    def test_conciliar_diferenca_de_ente(self):
        processo = "00123451020198260053"

        hub = {
            processo: {
                "numero_processo": processo,
                "ente": "Município de Santos",
                "valor_face": "9.800,00"
            }
        }

        tribunal = {
            processo: {
                "numero_processo": processo,
                "ente_devedor": "União",
                "valor_face": "9.800,00"
            }
        }

        resultado = conciliar_dados(hub, tribunal)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["situacao"], "divergente")
        self.assertTrue(resultado[0]["valores_iguais"])
        self.assertFalse(resultado[0]["entes_iguais"])

    def test_conciliar_processo_somente_no_hub(self):
        processo = "00123451020198260053"

        hub = {
            processo: {
                "numero_processo": processo,
                "ente": "Município de São Paulo",
                "valor_face": "31.000,00"
            }
        }

        tribunal = {}

        resultado = conciliar_dados(hub, tribunal)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["situacao"], "somente_hub")
        self.assertEqual(
            resultado[0]["valor_hub"],
            Decimal("31000.00")
        )
        self.assertIsNone(resultado[0]["valor_tribunal"])

    def test_conciliar_processo_somente_no_tribunal(self):
        processo = "00234562120208260053"

        hub = {}

        tribunal = {
            processo: {
                "numero_processo": processo,
                "ente_devedor": "Município de São Paulo",
                "valor_face": "30.000,00"
            }
        }

        resultado = conciliar_dados(hub, tribunal)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["situacao"], "somente_tribunal")
        self.assertEqual(
            resultado[0]["valor_tribunal"],
            Decimal("30000.00")
        )
        self.assertIsNone(resultado[0]["valor_hub"])


if __name__ == "__main__":
    unittest.main()
