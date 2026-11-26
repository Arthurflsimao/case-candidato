from src.processamento import executar_processamento
from src.relatorio import gerar_relatorios


def main():
    resultado = executar_processamento(
        "dados/pagamentos.json",
        "dados/apresentacoes.json",
        "dados/hub.csv",
        "dados/tribunal.csv"
    )

    arquivos = gerar_relatorios(resultado)

    pagamentos = resultado["pagamentos"]

    print("\n=== PROCESSAMENTO CONCLUÍDO ===")

    print("\nPagamentos:")
    print(f"Válidos: {len(pagamentos['validos'])}")
    print(f"Duplicados: {len(pagamentos['duplicados'])}")
    print(f"Pendentes: {len(pagamentos['pendentes'])}")
    print(f"Descartados: {len(pagamentos['descartados'])}")

    print("\nConciliação:")
    print(f"Processos presentes nos dois arquivos: {len(resultado['comparacao_processos']['presentes_nos_dois'])}")
    print(f"Somente no Hub: {len(resultado['comparacao_processos']['somente_hub'])}")
    print(f"Somente no Tribunal: {len(resultado['comparacao_processos']['somente_tribunal'])}")

    print("\nRelatórios gerados:")
    for arquivo in arquivos["arquivos"]:
        print(f"- {arquivos['diretorio']}/{arquivo}")


if __name__ == "__main__":
    main()
