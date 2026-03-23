from collections import deque
import pickle
import sys
import time
import tracemalloc

from pathlib import Path

from node import Node

class SearchEngine:

    def __init__(self, x, y, z, pasta_dados="data", arquivo_grafo=None, pickle_module=pickle):
        self.nos_visitados = 0
        self.X = x
        self.Y = y
        self.Z = z
        self.PASTA_DADOS = Path(pasta_dados)
        self.ARQUIVO_GRAFO = arquivo_grafo if arquivo_grafo else self.PASTA_DADOS / f"grafo_{x}x{y}_z{z}.pkl"
        self.pickle = pickle_module

    def conferir_movimento_valido(self, cani_esquerda, miss_esquerda):
        cani_direita = self.X - cani_esquerda
        miss_direita = self.Y - miss_esquerda

        if cani_esquerda < 0 or miss_esquerda < 0 or cani_direita < 0 or miss_direita < 0:
            return False

        if miss_esquerda > 0 and cani_esquerda > miss_esquerda:
            return False
        if miss_direita > 0 and cani_direita > miss_direita:
            return False
        
        return True
    
    def gerar_e_salvar_grafo(self, raiz):
        """Explora o espaço de estados e salva no diretório configurado"""
        fila = deque([raiz])
        visitados = {(raiz.canibais, raiz.missionarios, raiz.margem)}
        raiz_estado = (raiz.canibais, raiz.missionarios, raiz.margem)
        adjacencia = {raiz_estado: []}
        
        while fila:
            atual = fila.popleft()
            prox_margem = "direita" if atual.margem == "esquerda" else "esquerda"

            for b_cani in range(self.Z + 1):
                for b_miss in range(self.Z + 1):
                    if 0 < b_cani + b_miss <= self.Z:
                        novo_c = atual.canibais - b_cani if prox_margem == "direita" else atual.canibais + b_cani
                        novo_m = atual.missionarios - b_miss if prox_margem == "direita" else atual.missionarios + b_miss
                        
                        if self.conferir_movimento_valido(novo_c, novo_m):
                            estado = (novo_c, novo_m, prox_margem)
                            if estado not in visitados:
                                acao = f"Moveu {b_cani}C e {b_miss}M para {prox_margem.upper()}"
                                filho = Node(novo_c, novo_m, prox_margem, acao, atual)
                                atual.add(filho)
                                estado_atual = (atual.canibais, atual.missionarios, atual.margem)
                                adjacencia.setdefault(estado_atual, []).append((
                                    estado,
                                    acao,
                                ))
                                adjacencia.setdefault(estado, [])
                                visitados.add(estado)
                                fila.append(filho)
        
        # Garante a criação da pasta antes de salvar
        self.PASTA_DADOS.mkdir(exist_ok=True)
        payload = {
            "format": "flat_graph_v1",
            "meta": {"X": self.X, "Y": self.Y, "Z": self.Z},
            "root": raiz_estado,
            "adjacency": adjacencia,
        }
        with open(self.ARQUIVO_GRAFO, "wb") as f:
            limite_original = sys.getrecursionlimit()
            try:
                sys.setrecursionlimit(max(limite_original, 100_000))
                self.pickle.dump(payload, f)
            finally:
                sys.setrecursionlimit(limite_original)
        
        return raiz

    def check_if_objective(self, node_atual, objetivo_tupla):
        """Verifica se o estado atual é o estado objetivo"""
        return (node_atual.canibais == objetivo_tupla[0] and 
                node_atual.missionarios == objetivo_tupla[1] and 
                node_atual.margem == objetivo_tupla[2])
    
    def gerar_combinacoes_barco(self, node_atual, next_margem, visitados, fila):
        for barco_cani in range(self.Z + 1):
                for barco_miss in range(self.Z + 1):
                    if barco_cani + barco_miss > self.Z or barco_cani + barco_miss == 0:
                        continue  
                    
                    # 5. Calcula os novos valores na margem esquerda
                    if next_margem == "direita":
                        novo_cani = node_atual.canibais - barco_cani
                        novo_miss = node_atual.missionarios - barco_miss
                        acao_str = f"Moveu {barco_cani}C e {barco_miss}M para a DIREITA"
                    else:
                        novo_cani = node_atual.canibais + barco_cani
                        novo_miss = node_atual.missionarios + barco_miss
                        acao_str = f"Moveu {barco_cani}C e {barco_miss}M para a ESQUERDA"

                    # 6. Valida o movimento e gera o filho
                    if self.conferir_movimento_valido(novo_cani, novo_miss):
                        novo_estado_tuplo = (novo_cani, novo_miss, next_margem)
                        
                        # Apenas adicionamos à fila se ainda não visitámos este estado
                        if novo_estado_tuplo not in visitados:
                            filho = Node(novo_cani, novo_miss, next_margem, acao_str, node_atual)
                            node_atual.add(filho)
                            fila.append(filho)

    def bfs(self, raiz, objetivo_tupla):
        self.nos_visitados = 0
        tracemalloc.start()
        start_t = time.perf_counter()
        
        fila = deque([raiz])
        visitados = set()
        iteracoes_memoria_real = []
        serie_memoria_real = []

        while fila:
            node_atual = fila.popleft()
            self.nos_visitados += 1

            mem_loop_atual, _ = tracemalloc.get_traced_memory()
            iteracoes_memoria_real.append(self.nos_visitados)
            serie_memoria_real.append(mem_loop_atual / 1024)

            if self.check_if_objective(node_atual, objetivo_tupla):
                tempo = time.perf_counter() - start_t
                mem_atual, pico_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return {
                    "sucesso": True,
                    "no_final": node_atual,
                    "tempo": tempo,
                    "memoria": pico_mem / 1024,
                    "memoria_atual": mem_atual / 1024,
                    "iteracoes_memoria_real": iteracoes_memoria_real,
                    "serie_memoria_real": serie_memoria_real,
                    "visitados": self.nos_visitados
                }

            estado_atual = (node_atual.canibais, node_atual.missionarios, node_atual.margem)
            if estado_atual in visitados:
                continue
            visitados.add(estado_atual)

            # Gerar sucessores aqui
            next_margem = "direita" if node_atual.margem == "esquerda" else "esquerda"
            self.gerar_combinacoes_barco(node_atual, next_margem, visitados, fila)

        # Fora do loop
        tempo = time.perf_counter() - start_t
        mem_atual, pico_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "sucesso": False,
            "tempo": tempo,
            "memoria": pico_mem / 1024,
            "memoria_atual": mem_atual / 1024,
            "iteracoes_memoria_real": iteracoes_memoria_real,
            "serie_memoria_real": serie_memoria_real,
            "visitados": self.nos_visitados
        }

    def bfs_memory_optimized(self, raiz, objetivo_tupla):
        """BFS com mesma estrutura do normal, mas limpando nós infrutíferos.

        A única diferença em relação ao BFS normal é tentar remover da árvore
        nós sem filhos viáveis após expansão, para reduzir pressão de memória.
        A limpeza acontece por níveis da BFS.
        """
        self.nos_visitados = 0
        tracemalloc.start()
        start_t = time.perf_counter()

        fronteira = deque([raiz])
        visitados = set()
        iteracoes_memoria_real = []
        serie_memoria_real = []

        def podar_no_infrutifero(no):
            if no is raiz:
                return
            pai = no.parent
            if pai is not None:
                pai.children = [child for child in pai.children if child is not no]
            no.parent = None

        while fronteira:
            proxima_fronteira = deque()
            nos_nivel_atual = list(fronteira)

            while fronteira:
                node_atual = fronteira.popleft()
                self.nos_visitados += 1

                mem_loop_atual, _ = tracemalloc.get_traced_memory()
                iteracoes_memoria_real.append(self.nos_visitados)
                serie_memoria_real.append(mem_loop_atual / 1024)

                if self.check_if_objective(node_atual, objetivo_tupla):
                    tempo = time.perf_counter() - start_t
                    mem_atual, pico_mem = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    return {
                        "sucesso": True,
                        "no_final": node_atual,
                        "tempo": tempo,
                        "memoria": pico_mem / 1024,
                        "memoria_atual": mem_atual / 1024,
                        "iteracoes_memoria_real": iteracoes_memoria_real,
                        "serie_memoria_real": serie_memoria_real,
                        "visitados": self.nos_visitados
                    }

                estado_atual = (node_atual.canibais, node_atual.missionarios, node_atual.margem)
                if estado_atual in visitados:
                    continue
                visitados.add(estado_atual)

                filhos_antes = len(node_atual.children)
                next_margem = "direita" if node_atual.margem == "esquerda" else "esquerda"
                self.gerar_combinacoes_barco(node_atual, next_margem, visitados, proxima_fronteira)

                if len(node_atual.children) == filhos_antes:
                    podar_no_infrutifero(node_atual)

            # Limpeza adicional ao fim do nível: remove nós já processados que
            # acabaram sem filhos após podas locais no mesmo nível.
            for no in nos_nivel_atual:
                if len(no.children) == 0:
                    podar_no_infrutifero(no)

            fronteira = proxima_fronteira

        # Fora do loop - sem solução
        tempo = time.perf_counter() - start_t
        mem_atual, pico_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "sucesso": False,
            "tempo": tempo,
            "memoria": pico_mem / 1024,
            "memoria_atual": mem_atual / 1024,
            "iteracoes_memoria_real": iteracoes_memoria_real,
            "serie_memoria_real": serie_memoria_real,
            "visitados": self.nos_visitados
        }
