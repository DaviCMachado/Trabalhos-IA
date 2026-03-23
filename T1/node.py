class Node:
    def __init__(self, miss, cani, marg, acao="Estado Inicial", parent=None):
        self.missionarios = miss
        self.canibais = cani
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
            caminho.append(f"[{atual.acao}] -> Esq: {atual.missionarios}M, {atual.canibais}C | Dir: {X - atual.missionarios}M, {Y - atual.canibais}C | Barco: {atual.margem}")
            atual = atual.parent
        return caminho[::-1]