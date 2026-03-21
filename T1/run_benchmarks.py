import pickle
import json
import time
from pathlib import Path

# Importa os módulos do projeto
from node import Node
from search_engine import SearchEngine

PASTA_DADOS = Path(__file__).parent / "data"
PASTA_DADOS.mkdir(exist_ok=True)


def rodar_teste(idx, entrada):
    X = entrada["X"]
    Y = entrada["Y"]
    Z = entrada["Z"]

    arquivo_grafo = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"

    print(f"\n{'='*60}")
    print(f"🧪 TESTE #{idx + 1} | X={X} missionários | Y={Y} canibais | Z={Z} lugares no barco")
    print(f"{'='*60}")

    engine = SearchEngine(
        X, Y, Z,
        pasta_dados=PASTA_DADOS,
        arquivo_grafo=arquivo_grafo,
        pickle_module=pickle
    )

    # Gera ou carrega o grafo (sem perguntar — sempre gera se não existir, reutiliza se existir)
    if arquivo_grafo.exists():
        print(f"📂 Reutilizando grafo salvo em: {arquivo_grafo.name}")
        with open(arquivo_grafo, "rb") as f:
            raiz = pickle.load(f)
    else:
        print(f"⚙️  Gerando espaço de estados...")
        raiz_original = Node(X, Y, "esquerda")
        raiz = engine.gerar_e_salvar_grafo(raiz_original)

    # Executa a busca
    objetivo = (0, 0, "direita")
    resultado = engine.bfs(raiz, objetivo)

    # Exibe relatório
    if resultado["sucesso"]:
        print(f"✅ SOLUÇÃO ENCONTRADA!")
        print(f"⏱️  Tempo: {resultado['tempo']:.6f}s | 💾 Memória: {resultado['memoria']:.2f}KB")
        print(f"🔍 Nós explorados: {resultado['visitados']}")
        print(f"{'-'*60}")
        passos = resultado["no_final"].obter_caminho_solucao(X, Y, Z)
        for i, p in enumerate(passos):
            print(f"  Passo {i}: {p}")
    else:
        print(f"❌ Sem solução para esta configuração.")
        print(f"⏱️  Tempo: {resultado['tempo']:.6f}s | 🔍 Nós explorados: {resultado['visitados']}")

    return resultado["sucesso"]


def main():
    caminho_json = Path(__file__).parent / "scenarios.json"

    if not caminho_json.exists():
        print(f"❌ Arquivo scenarios.json não encontrado em: {caminho_json}")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    testes = dados.get("testes", [])
    total = len(testes)
    sucessos = 0

    print(f"\n🚀 Iniciando execucao dos cenários — {total} teste(s) encontrado(s)")
    inicio_total = time.perf_counter()

    for idx, teste in enumerate(testes):
        entrada = teste["in"]
        ok = rodar_teste(idx, entrada)
        if ok:
            sucessos += 1

    fim_total = time.perf_counter()



if __name__ == "__main__":
    main()