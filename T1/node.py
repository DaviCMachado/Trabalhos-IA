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

    def obter_caminho_solucao(self, X, Y, Z):
        caminho = []
        atual = self
        while atual:
            caminho.append(f"[{atual.acao}] -> Esq: {atual.canibais}C, {atual.missionarios}M | Dir: {X - atual.canibais}C, {Y - atual.missionarios}M | Barco: {atual.margem}")
            atual = atual.parent
        return caminho[::-1]