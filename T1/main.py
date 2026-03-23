
# Descricao do problema:
# Há X missionarios e Y canibais no lado ESQUERDO de um rio. Há um barco que pode transportar pessoas. 
# Como levar todos eles para o lado DIREITO do rio? 

# Restricoes:
# O barco leva apenas Z pessoas por vez
# Nao pode deixar os canibais em maior numero do que os missionarios

# 1. A Regra do "Game Over" Imediato: Se logo no início você tem mais canibais do que missionários na margem (e há pelo menos 1 missionário), 
# o problema é impossível. Condição: Se Y > X (com X > 0) ---> Sem solução.

# 2. A Regra dos "Números Iguais" (X = Y = N)
# Quando você tem o mesmo número de missionários e canibais (ex: 3x3, 4x4, 6x6), 
# a capacidade do barco (Z) determina o limite máximo de pessoas que podem atravessar.
 
# A matemática dita o seguinte:Se Z = 1: Impossível. (Alguém tem que remar de volta, então o barco nunca avança).
# Se Z = 2: Só é possível se N <= 3. (É por isso que 3x3 funciona, mas 4x4, 5x5 ou o seu 6x6 falham).
# Se Z = 3: Só é possível se N <= 5. 
# Se Z >= 4: É possível para qualquer número (infinitos missionários e canibais podem atravessar).
# A Fórmula Matemática para Z <= 3: O problema só tem solução se o número total de cada grupo (N) for menor ou igual a (2 * Z) - 1.
#
# Mas por que 4x4 com Barco=2 é impossível? O problema não é o começo nem o fim, é o "meio" da travessia.
# Quando você tem 4 de cada, você consegue mandar 2 canibais para a direita algumas vezes. 
# Mas chega um momento em que você precisa começar a passar missionários para não esgotar as combinações seguras.
# Como o barco só leva 2 pessoas, você manda 2 missionários. 
# Ao chegarem na outra margem, você terá 2 Missionários e 2 Canibais de cada lado do rio. 
# Alguém tem que voltar com o barco: 
    # Se voltar um Missionário, a margem de onde ele saiu fica com mais canibais ---> Morreu.
    # Se voltar um Canibal, a margem para onde ele chega fica com mais canibais ---> Morreu.
    # Se voltar 1 Missionário e 1 Canibal, você literalmente desfaz a última viagem e entra em Loop Infinito.
    # Por isso, qualquer número maior que 3 com um barco de 2 lugares gera um deadlock!
# x = 4, y = 4, z = 2 ---> Vai dar Sem Solução (limite matemático excedido).
# x = 4, y = 4, z = 3 ---> Vai dar Solução Encontrada (porque para barco de tamanho 3, o limite é 5).

import pickle
import gc
from pathlib import Path

# Configurações Globais: Missionários, Canibais e Capacidade do Barco
X, Y, Z = 1200, 1000, 2
# Definimos o caminho globalmente para evitar erros de sincronização
PASTA_DADOS = Path(__file__).parent / "data"
ARQUIVO_GRAFO = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"

from node import Node
from search_engine import SearchEngine


def medir_tempos_justos(executar_normal, executar_otimizado, rodadas=8, aquecimento=2):
    """Compara tempos reduzindo viés de cache por ordem de execução."""
    for _ in range(aquecimento):
        executar_normal()
        executar_otimizado()

    tempos_normal = []
    tempos_otimizado = []

    for i in range(rodadas):
        if i % 2 == 0:
            ordem = (("normal", executar_normal), ("otimizado", executar_otimizado))
        else:
            ordem = (("otimizado", executar_otimizado), ("normal", executar_normal))

        for nome, fn in ordem:
            gc.collect()
            resultado = fn()
            if nome == "normal":
                tempos_normal.append(resultado["tempo"])
            else:
                tempos_otimizado.append(resultado["tempo"])

    media_normal = sum(tempos_normal) / len(tempos_normal) if tempos_normal else 0.0
    media_otimizado = sum(tempos_otimizado) / len(tempos_otimizado) if tempos_otimizado else 0.0
    return media_normal, media_otimizado


def salvar_grafo(arquivo_destino, raiz):
    arquivo_destino.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo_destino, "wb") as f:
        pickle.dump(raiz, f)
    print(f"💾 Grafo salvo em {arquivo_destino}")

def imprimir_relatorio(res, titulo="BFS"):
    print("\n" + "="*60)
    print(f"📊 Relatório: {titulo}")
    print("="*60)
    if res["sucesso"]:
        print(f"🎉 SOLUÇÃO ENCONTRADA!")
        print(f"⏱️  Tempo: {res['tempo']:.6f}s | 💾 Memória: {res['memoria']:.2f}KB")
        print(f"🔍 Nós explorados: {res['visitados']}")
        print("-" * 60)
        passos = res["no_final"].obter_caminho_solucao(X, Y, Z)
        for i, p in enumerate(passos):
            print(f"Passo {i}: {p}")
    else:
        print("❌ Não foi possível encontrar uma solução no grafo carregado.")
    print("="*60)

def gerar_grafo(pasta_destino, arquivo_destino, titulo=""):
    """Gera e salva grafo em um diretório específico"""
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    print(f"\n⚙️  {titulo} - Gerando grafo em {arquivo_destino}...")
    engine = SearchEngine(X, Y, Z, pasta_dados=pasta_destino, arquivo_grafo=arquivo_destino, pickle_module=pickle)
    
    raiz_original = Node(X, Y, "esquerda")
    raiz = engine.gerar_e_salvar_grafo(raiz_original)
    
    print(f"✅ Grafo salvo em {arquivo_destino}")
    return raiz, engine

def main():
    print(f"🚀 Executando BFS Normal e Otimizado")
    print(f"📋 Configuração: X={X}, Y={Y}, Z={Z}")

    # Execução das buscas
    objetivo = (0, 0, "direita")

    engine_base = SearchEngine(X, Y, Z, pasta_dados=PASTA_DADOS, arquivo_grafo=ARQUIVO_GRAFO, pickle_module=pickle)
    raiz_base = Node(X, Y, "esquerda")

    print(f"\n⚙️  Gerando grafo base único...")
    engine_base.gerar_e_salvar_grafo(raiz_base)
    print(f"✅ Grafo base salvo em {ARQUIVO_GRAFO}")

    # Cada execução usa sua própria raiz em memória; o grafo salvo permanece único
    raiz_normal = Node(X, Y, "esquerda")
    raiz_otimizado = Node(X, Y, "esquerda")
    engine_normal = SearchEngine(X, Y, Z, pasta_dados=PASTA_DADOS, arquivo_grafo=ARQUIVO_GRAFO, pickle_module=pickle)
    engine_otimizado = SearchEngine(X, Y, Z, pasta_dados=PASTA_DADOS, arquivo_grafo=ARQUIVO_GRAFO, pickle_module=pickle)
    
    print(f"\n🔍 Executando BFS Normal...")
    resultado_normal = engine_normal.bfs(raiz_normal, objetivo)
    imprimir_relatorio(resultado_normal, "BFS Normal")

    print(f"\n🔍 Executando BFS Otimizado...")
    resultado_otimizado = engine_otimizado.bfs_memory_optimized(raiz_otimizado, objetivo)
    imprimir_relatorio(resultado_otimizado, "BFS Otimizado")

    # Benchmark justo para tempo (mitiga viés de cache/ordem)
    def _exec_normal_benchmark():
        engine = SearchEngine(X, Y, Z, pasta_dados=PASTA_DADOS, arquivo_grafo=ARQUIVO_GRAFO, pickle_module=pickle)
        raiz = Node(X, Y, "esquerda")
        return engine.bfs(raiz, objetivo)

    def _exec_otimizado_benchmark():
        engine = SearchEngine(X, Y, Z, pasta_dados=PASTA_DADOS, arquivo_grafo=ARQUIVO_GRAFO, pickle_module=pickle)
        raiz = Node(X, Y, "esquerda")
        return engine.bfs_memory_optimized(raiz, objetivo)

    tempo_normal_medio, tempo_otimizado_medio = medir_tempos_justos(_exec_normal_benchmark, _exec_otimizado_benchmark)

    # Comparação
    print("\n" + "="*60)
    print("📊 COMPARAÇÃO DOS RESULTADOS")
    print("="*60)
    if resultado_normal["sucesso"] and resultado_otimizado["sucesso"]:
        tempo_diff = abs(tempo_normal_medio - tempo_otimizado_medio)
        mem_diff = abs(resultado_normal["memoria"] - resultado_otimizado["memoria"])
        mem_economia = ((resultado_normal["memoria"] - resultado_otimizado["memoria"]) / resultado_normal["memoria"] * 100) if resultado_normal["memoria"] > 0 else 0
        
        print(f"⏱️  Tempo médio BFS Normal: {tempo_normal_medio:.6f}s")
        print(f"⏱️  Tempo médio BFS Otimizado: {tempo_otimizado_medio:.6f}s")
        print(f"⏱️  Diferença de tempo (média): {tempo_diff:.6f}s")
        print(f"💾 Pico de memória BFS Normal: {resultado_normal['memoria']:.2f}KB")
        print(f"💾 Pico de memória BFS Otimizado: {resultado_otimizado['memoria']:.2f}KB")
        print(f"💾 Diferença de memória: {mem_diff:.2f}KB")
        print(f"💰 Economia de memória (Otimizado): {mem_economia:.2f}%")
        print(f"🔍 Nós explorados (Normal): {resultado_normal['visitados']}")
        print(f"🔍 Nós explorados (Otimizado): {resultado_otimizado['visitados']}")
    print("="*60)

if __name__ == "__main__":
    main()