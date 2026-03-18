# Descricao do problema:
# Há X missionarios e Y canibais no lado ESQUERDO de um rio. Há um barco que pode transportar pessoas. 
# Como levar todos eles para o lado DIREITO do rio? 

# Restricoes:
# O barco leva apenas Z pessoas por vez
# Nao pode deixar os canibais em maior numero do que os missionarios

x = 14000
y = 6
z = 2



class Node: #possui os estados

    def __init__(self, cani, miss, marg, parent=None):
        self.canibais = cani #na esquerda
        self.missionarios = miss #na esquerda
        self.margem = marg #onde o barco esta
        self.children = []
        self.parent = parent

    def add(self, child):
        self.children.append(child)

    def remove(self, child):
        self.children.pop(child)

    def print_profundidade(self):
        print(f"Canibais: {self.canibais}, Missionarios: {self.missionarios}, Margem: {self.margem}")
        for child in self.children:
            child.print_profundidade()


class SearchEngine:

    def __init__(self):
        pass

    def conferir_movimento_valido(self, cani_esquerda, miss_esquerda):
        cani_direita = x - cani_esquerda
        miss_direita = y - miss_esquerda


        if miss_esquerda > 0 and cani_esquerda > miss_esquerda:
            return False
        if miss_direita > 0 and cani_direita> miss_direita:
            return False
        
        return True


    def gerar_proximo_estado_bfs(self, node):
        """Gera todos os filhos do node

        Args:
            node (_type_): _description_
        """
        next_margem = "direita" if node.margem == "esquerda" else "esquerda"

        movimentos_barco = list() #lista com todos as combinacoes de movimento de cani/miss que o barco suporta

        for barco_cani in range(z +1):
            for barco_miss in range(z+1):
                if barco_cani + barco_miss > z or barco_cani + barco_miss == 0: #limitacao do barco
                    continue  
                movimentos_barco.append((barco_cani, barco_miss))      

        if next_margem == "direita":
            for qtd_cani, qtd_miss in movimentos_barco:
                novo_cani = node.canibais - qtd_cani
                novo_miss = node.missionarios - qtd_miss
                if self.conferir_movimento_valido(novo_cani, novo_miss):
                    node.add(Node(novo_cani, novo_miss, next_margem, node))

        if next_margem == "esquerda":
            for qtd_cani, qtd_miss in movimentos_barco:
                novo_cani = node.canibais + qtd_cani
                novo_miss = node.missionarios + qtd_miss
                if self.conferir_movimento_valido(novo_cani, novo_miss):
                    node.add(Node(novo_cani, novo_miss, next_margem, node))

def main():

    nodeInicial = Node(x, y, "esquerda")
    nodeFinal = Node(0, 0, "direita")

    engine = SearchEngine()

    engine.gerar_proximo_estado_bfs(nodeInicial)

    nodeInicial.print_profundidade()

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