from collections import deque
import time
import tracemalloc

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

class Node: #possui os estados
    def __init__(self, cani, miss, marg, acao="Estado Inicial", parent=None):
        self.canibais = cani #na esquerda
        self.missionarios = miss #na esquerda
        self.margem = marg #onde o barco esta
        self.acao = acao # Guarda a funcao de transicao
        self.children = []
        self.parent = parent

    def add(self, child):
        self.children.append(child)

    def obter_caminho_solucao(self):
        """Sobe a árvore a partir do nó final até à raiz para mostrar os passos"""
        caminho = []
        atual = self
        while atual:
            caminho.append(f"[{atual.acao}] -> Esquerda: {atual.canibais}C, {atual.missionarios}M | Direita: {x - atual.canibais}C, {y - atual.missionarios}M | Margem do Barco: {atual.margem}")
            atual = atual.parent
        return caminho[::-1] # Inverte a lista para mostrar do inicio ao fim


class SearchEngine:

    def __init__(self):
        self.nos_visitados = 0

    def conferir_movimento_valido(self, cani_esquerda, miss_esquerda):
        cani_direita = x - cani_esquerda
        miss_direita = y - miss_esquerda

        # Impede números negativos (alguém tentar mover mais pessoas do que as que existem)
        if cani_esquerda < 0 or miss_esquerda < 0 or cani_direita < 0 or miss_direita < 0:
            return False

        if miss_esquerda > 0 and cani_esquerda > miss_esquerda:
            return False
        if miss_direita > 0 and cani_direita > miss_direita:
            return False
        
        return True


    def bfs(self, node_inicial, node_final):
        """Executa a Busca em Largura (BFS) completa"""
        
        fila = deque([node_inicial])
        visitados = set() 
        self.nos_visitados = 0
        
        print("\n" + "="*60)
        print("🚀 INICIANDO BUSCA EM LARGURA (BFS)")
        print(f"Parâmetros: {x} Canibais, {y} Missionários | Capacidade Barco: {z}")
        print("="*60 + "\n")

        # Inicia o rastreamento de memória e tempo
        tracemalloc.start()
        start_time = time.perf_counter()

        while fila:
            node_atual = fila.popleft()
            self.nos_visitados += 1

            # 1. Verifica se chegou ao estado final
            if (node_atual.canibais == node_final.canibais and 
                node_atual.missionarios == node_final.missionarios and 
                node_atual.margem == node_final.margem):
                
                # Finaliza rastreamento
                end_time = time.perf_counter()
                _, peak_mem = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                tempo_gasto = end_time - start_time
                mem_kb = peak_mem / 1024
                
                print("\n" + "="*60)
                print(f"🎉 SOLUÇÃO ENCONTRADA! (Nós explorados: {self.nos_visitados})")
                print(f"⏱️  Tempo de execução: {tempo_gasto:.6f} segundos")
                print(f"💾 Memória utilizada (Pico): {mem_kb:.2f} KB")
                print("="*60 + "\n")
                return node_atual

            # 2. Marca o estado atual como visitado 
            estado_atual = (node_atual.canibais, node_atual.missionarios, node_atual.margem)
            if estado_atual in visitados:
                continue
            visitados.add(estado_atual)

            # 3. Descobre para onde o barco vai
            next_margem = "direita" if node_atual.margem == "esquerda" else "esquerda"

            # 4. Gera todas as combinações de barco possíveis
            for barco_cani in range(z + 1):
                for barco_miss in range(z + 1):
                    if barco_cani + barco_miss > z or barco_cani + barco_miss == 0:
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

        # Finaliza rastreamento se não encontrou solução
        end_time = time.perf_counter()
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        tempo_gasto = end_time - start_time
        mem_kb = peak_mem / 1024

        # Se a fila esvaziar e não tiver retornado o 'node_atual', é porque não há solução
        print("\n" + "="*60)
        print(f"❌ NÃO HÁ SOLUÇÃO POSSÍVEL para esta configuração.")
        print(f"Todos os caminhos válidos foram explorados ({self.nos_visitados} estados analisados).")
        print(f"⏱️  Tempo de execução: {tempo_gasto:.6f} segundos")
        print(f"💾 Memória utilizada (Pico): {mem_kb:.2f} KB")
        print("="*60 + "\n")
        return None



def main():
    nodeInicial = Node(x, y, "esquerda")
    nodeFinal = Node(0, 0, "direita")
    
    engine = SearchEngine()

    # Executa a busca
    no_solucao = engine.bfs(nodeInicial, nodeFinal)

    # Imprime o passo a passo APENAS se houver solução
    if no_solucao:
        print("--- CAMINHO PASSO A PASSO ATÉ AO OBJETIVO ---")
        passos = no_solucao.obter_caminho_solucao()
        for i, passo in enumerate(passos):
            print(f"Passo {i}: {passo}")

    # while (True):
    #     choice = input("Escolha o tipo de busca: 1 - bfs, 2 - djikstra, 3 - alphastar\n")
    #     match choice:
    #         case 1:
    #             engine.bfs()
    #         case 2: 
    #             engine.djikstra()
    #         case 3:
    #             engine.alphastar()

# gerar relatorio pdf com metricas como tempo e memoria utilizada, alem de nos visitados, fator de expansão, etc 


if __name__ == "__main__":
    main()