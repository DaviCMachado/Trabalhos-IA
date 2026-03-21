
# Descricao do problema:
# Há X missionarios e Y canibais no lado ESQUERDO de um rio. Há um barco que pode transportar pessoas. 
# Como levar todos eles para o lado DIREITO do rio? 

# Restricoes:
# O barco leva apenas Z pessoas por vez
# Nao pode deixar os canibais em maior numero do que os missionarios

# 1. A Regra do "Game Over" ImediatoSe logo no início você tem mais canibais do que missionários na margem (e há pelo menos 1 missionário), 
# o problema é impossível.Condição: Se X > Y (com Y > 0) ---> Sem solução.

# 2. A Regra dos "Números Iguais" (X = Y = N)
# Quando você tem o mesmo número de missionários e canibais (ex: 3x3, 4x4, 6x6), 
# a capacidade do barco (Z) determina o limite máximo de pessoas que podem atravessar. 
# A matemática dita o seguinte:Se Z = 1: Impossível. (Alguém tem que remar de volta, então o barco nunca avança).
# Se Z = 2: Só é possível se N <= 3. (É por isso que 3x3 funciona, mas 4x4, 5x5 ou o seu 6x6 falham).
# Se Z = 3: Só é possível se N <= 5. 
# Se Z >= 4: É possível para qualquer número (infinitos missionários e canibais podem atravessar).
# A Fórmula Matemática para Z <= 3: O problema só tem solução se o número total de cada grupo (N) for menor ou igual a (2 * Z) - 1.
#
#  Mas por que 4x4 com Barco=2 é impossível? (O Gargalo)O problema não é o começo nem o fim, é o "meio" da travessia.
# Quando você tem 4 de cada, você consegue mandar 2 canibais para a direita algumas vezes. 
# Mas chega um momento em que você precisa começar a passar missionários para não esgotar as combinações seguras.Como o barco só leva 2 pessoas, 
# você manda 2 missionários. Ao chegarem na outra margem, você terá 2 Missionários e 2 Canibais de cada lado do rio. 
# Alguém tem que voltar com o barco: 
# Se voltar um Missionário, a margem de onde ele saiu fica com mais canibais ---> Morreu.
# Se voltar um Canibal, a margem para onde ele chega fica com mais canibais ---> Morreu.
# Se voltar 1 Missionário e 1 Canibal, você literalmente desfaz a última viagem e entra em Loop Infinito.
# Por isso, qualquer número maior que 3 com um barco de 2 lugares gera um "deadlock" (impasse) no meio do rio!
# Faça o teste no seu código!Para provar essa matemática na prática, mude os parâmetros no seu código para:
# x = 4, y = 4, z = 2 ---> Vai dar Sem Solução (limite matemático excedido).
# x = 4, y = 4, z = 3 ---> Vai dar Solução Encontrada (porque para barco de tamanho 3, o limite é 5).

x = 5 
y = 5 
z = 3

import pickle
import time
import tracemalloc
import os
from collections import deque
from pathlib import Path

# Configurações Globais
X, Y, Z = 9, 9, 4
# Definimos o caminho globalmente para evitar erros de sincronização
PASTA_DADOS = Path(__file__).parent / "data"

# Assim, cada combinação de X, Y, Z gera seu próprio arquivo
ARQUIVO_GRAFO = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"

class Node:
    def __init__(self, cani, miss, marg, acao="Estado Inicial", parent=None):
        self.canibais = cani
        self.missionarios = miss
        self.margem = marg
        self.acao = acao
        self.children = []
        self.parent = parent

    def add(self, child):
        self.children.append(child)

    def obter_caminho_solucao(self):
        caminho = []
        atual = self
        while atual:
            caminho.append(f"[{atual.acao}] -> Esq: {atual.canibais}C, {atual.missionarios}M | Dir: {X - atual.canibais}C, {Y - atual.missionarios}M | Barco: {atual.margem}")
            atual = atual.parent
        return caminho[::-1]

class SearchEngine:
    def __init__(self):
        self.nos_visitados = 0

    def conferir_movimento_valido(self, cani_esq, miss_esq):
        cani_dir, miss_dir = X - cani_esq, Y - miss_esq
        if cani_esq < 0 or miss_esq < 0 or cani_dir < 0 or miss_dir < 0: return False
        if (miss_esq > 0 and cani_esq > miss_esq) or (miss_dir > 0 and cani_dir > miss_dir): return False
        return True

    def gerar_e_salvar_grafo(self, raiz):
        """Explora o espaço de estados e salva no diretório configurado"""
        fila = deque([raiz])
        visitados = {(raiz.canibais, raiz.missionarios, raiz.margem)}
        
        while fila:
            atual = fila.popleft()
            prox_margem = "direita" if atual.margem == "esquerda" else "esquerda"

            for b_cani in range(Z + 1):
                for b_miss in range(Z + 1):
                    if 0 < b_cani + b_miss <= Z:
                        novo_c = atual.canibais - b_cani if prox_margem == "direita" else atual.canibais + b_cani
                        novo_m = atual.missionarios - b_miss if prox_margem == "direita" else atual.missionarios + b_miss
                        
                        if self.conferir_movimento_valido(novo_c, novo_m):
                            estado = (novo_c, novo_m, prox_margem)
                            if estado not in visitados:
                                acao = f"Moveu {b_cani}C e {b_miss}M para {prox_margem.upper()}"
                                filho = Node(novo_c, novo_m, prox_margem, acao, atual)
                                atual.add(filho)
                                visitados.add(estado)
                                fila.append(filho)
        
        # Garante a criação da pasta antes de salvar
        PASTA_DADOS.mkdir(exist_ok=True)
        with open(ARQUIVO_GRAFO, "wb") as f:
            pickle.dump(raiz, f)
        
        return raiz

    def bfs(self, raiz, objetivo_tupla):
        self.nos_visitados = 0
        tracemalloc.start()
        start_t = time.perf_counter()
        
        fila = deque([raiz])
        visitados = set()

        while fila:
            atual = fila.popleft()
            self.nos_visitados += 1
            
            if (atual.canibais, atual.missionarios, atual.margem) == objetivo_tupla:
                tempo = time.perf_counter() - start_t
                _, pico_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "sucesso": True,
                    "no_final": atual,
                    "tempo": tempo,
                    "memoria": pico_mem / 1024,
                    "visitados": self.nos_visitados
                }

            visitados.add((atual.canibais, atual.missionarios, atual.margem))
            for filho in atual.children:
                if (filho.canibais, filho.missionarios, filho.margem) not in visitados:
                    fila.append(filho)

        tracemalloc.stop()
        return {"sucesso": False, "tempo": time.perf_counter() - start_t}

def imprimir_relatorio(res):
    print("\n" + "="*60)
    if res["sucesso"]:
        print(f"🎉 SOLUÇÃO ENCONTRADA!")
        print(f"⏱️  Tempo: {res['tempo']:.6f}s | 💾 Memória: {res['memoria']:.2f}KB")
        print(f"🔍 Nós explorados: {res['visitados']}")
        print("-" * 60)
        passos = res["no_final"].obter_caminho_solucao()
        for i, p in enumerate(passos):
            print(f"Passo {i}: {p}")
    else:
        print("❌ Não foi possível encontrar uma solução no grafo carregado.")
    print("="*60)

def main():
    engine = SearchEngine()
    raiz = None

    if ARQUIVO_GRAFO.exists():
        print(f"📂 Arquivo de grafo detectado em: {ARQUIVO_GRAFO}")
        print("[1] Usar grafo existente (mais rápido)")
        print("[2] Gerar novo grafo (sobrescrever)")
        opcao = input("Escolha uma opção: ")

        if opcao == "2":
            print("⚙️  Gerando novo espaço de estados...")
            raiz_original = Node(X, Y, "esquerda")
            raiz = engine.gerar_e_salvar_grafo(raiz_original)
        else:
            print("📥 Carregando dados do disco...")
            with open(ARQUIVO_GRAFO, "rb") as f:
                raiz = pickle.load(f)
    else:
        print(f"⚠️  Grafo não encontrado. Criando base de dados inicial...")
        raiz_original = Node(X, Y, "esquerda")
        raiz = engine.gerar_e_salvar_grafo(raiz_original)

    # Execução da Busca
    objetivo = (0, 0, "direita")
    resultado = engine.bfs(raiz, objetivo)

    # Relatório
    imprimir_relatorio(resultado)

if __name__ == "__main__":
    main()