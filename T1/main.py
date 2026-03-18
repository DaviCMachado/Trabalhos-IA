


class Node:

    def __init__(self, cani, miss, marg):
        self.canibais = cani
        self.missionarios = miss
        self.margem = marg
        self.children = []

    def add(self, child):
        self.children.append(child)

    def remove(self, child):
        self.children.pop(child)


class SearchEngine:

    def __init__(self):
        pass
        

def main():

    engine = SearchEngine()
    while (True):
        choice = input("Escolha o tipo de busca: 1 - bfs, 2 - djikstra, 3 - alphastar\n")
        match choice:
            case 1:
                engine.bfs()
            case 2: 
                engine.djikstra()
            case 3:
                engine.alphastar()

# gerar relatorio pdf com metricas como tempo e memoria utilizada, alem de nos visitados, fator de expansão, etc 


if __name__ == "__main__":
    main()