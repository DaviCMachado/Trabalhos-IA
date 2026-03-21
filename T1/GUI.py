import pickle
import re
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.widgets import Button
from pathlib import Path
from collections import deque
import main  # Mantém classe Node disponível para o pickle (main.Node)


class NodeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "__main__" and name == "Node":
            return main.Node
        return super().find_class(module, name)

def hierarquia_pos(G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
    """Calcula posições para um layout de árvore hierárquico."""
    if not nx.is_tree(G):
        T = nx.dfs_tree(G, root) 
    else:
        T = G

    def _hierarchy_pos(G, node, left, right, vert_gap, vert_loc, xcenter, pos=None, parent=None):
        if pos is None:
            pos = {node: (xcenter, vert_loc)}
        else:
            pos[node] = (xcenter, vert_loc)
        
        children = list(G.neighbors(node))
        if len(children) != 0:
            dx = (right - left) / len(children) 
            nextx = left + dx/2
            for child in children:
                pos = _hierarchy_pos(G, child, left, left + dx, vert_gap, 
                                    vert_loc - vert_gap, nextx, pos=pos, parent=node)
                left += dx
                nextx += dx
        return pos

    return _hierarchy_pos(T, root, 0, width, vert_gap, vert_loc, xcenter)

class BFSVisualizer:
    def __init__(self, arquivo_grafo, capacidade_barco=None):
        self.arquivo = arquivo_grafo
        self.raiz = self._carregar_grafo()
        self.total_canibais = self.raiz.canibais
        self.total_missionarios = self.raiz.missionarios
        self.capacidade_barco = self._inferir_capacidade_barco(capacidade_barco)
        self.passos_bfs = []
        self._mapear_ordem_bfs(self.raiz)

        self.grafo_completo = self._construir_grafo_completo()
        id_raiz = f"{self.raiz.canibais}C_{self.raiz.missionarios}M_{self.raiz.margem}"
        self.posicoes_arvore_fixas = hierarquia_pos(self.grafo_completo, root=id_raiz)
        
        self.index_atual = 0
        self.modo_arvore = True  # Estado inicial
        self.G = nx.DiGraph()
        self.zoom_limits = None
        self.pan_ativo = False
        self.pan_inicio = None
        self.pan_xlim_inicio = None
        self.pan_ylim_inicio = None
        
        # Configuração da Janela
        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        plt.subplots_adjust(bottom=0.2)
        self.fig.suptitle(f"Capacidade do barco: {self.capacidade_barco}", fontsize=12, fontweight='bold', y=0.98)
        
        # Botões de Navegação
        ax_prev = plt.axes([0.2, 0.05, 0.1, 0.06])
        ax_next = plt.axes([0.31, 0.05, 0.1, 0.06])
        self.btn_prev = Button(ax_prev, 'Anterior')
        self.btn_next = Button(ax_next, 'Próximo')
        
        # Botão de Alternar Modo
        ax_mode = plt.axes([0.6, 0.05, 0.2, 0.06])
        self.btn_mode = Button(ax_mode, 'Alternar: Árvore/Grafo')
        
        # Eventos
        self.btn_prev.on_clicked(self.retroceder)
        self.btn_next.on_clicked(self.avancar)
        self.btn_mode.on_clicked(self.alternar_layout)

        self.fig.canvas.mpl_connect('scroll_event', self._ao_scroll_zoom)
        self.fig.canvas.mpl_connect('button_press_event', self._ao_click_mouse)
        self.fig.canvas.mpl_connect('button_release_event', self._ao_soltar_mouse)
        self.fig.canvas.mpl_connect('motion_notify_event', self._ao_mover_mouse)
        
        self.atualizar_grafico()
        plt.show()

    def _carregar_grafo(self):
        with open(self.arquivo, "rb") as f:
            return NodeUnpickler(f).load()

    def _mapear_ordem_bfs(self, raiz):
        fila = deque([raiz])
        visitados = set()
        while fila:
            atual = fila.popleft()
            estado = (atual.canibais, atual.missionarios, atual.margem)
            if estado not in visitados:
                visitados.add(estado)
                self.passos_bfs.append(atual)

                if self._eh_objetivo(atual):
                    break

                for filho in atual.children:
                    fila.append(filho)

    def _normalizar_margem(self, margem):
        mapa = {
            "l": "esquerda",
            "e": "esquerda",
            "left": "esquerda",
            "esquerda": "esquerda",
            "r": "direita",
            "d": "direita",
            "right": "direita",
            "direita": "direita",
        }
        chave = str(margem).strip().lower()
        return mapa.get(chave, chave)

    def _eh_objetivo(self, no):
        return (
            no.canibais == 0
            and no.missionarios == 0
            and self._normalizar_margem(no.margem) == "direita"
        )

    def _inferir_capacidade_barco(self, capacidade_informada=None):
        nome_arquivo = Path(self.arquivo).name
        match = re.search(r"_z(\d+)\.pkl$", nome_arquivo)
        if match:
            return int(match.group(1))
        if capacidade_informada is not None:
            return capacidade_informada
        return "?"

    def _construir_grafo_completo(self):
        grafo = nx.DiGraph()
        fila = deque([self.raiz])
        visitados = set()

        while fila:
            no = fila.popleft()
            estado = (no.canibais, no.missionarios, no.margem)
            if estado in visitados:
                continue

            visitados.add(estado)
            u = f"{no.canibais}C_{no.missionarios}M_{no.margem}"
            grafo.add_node(u)
            for filho in no.children:
                v = f"{filho.canibais}C_{filho.missionarios}M_{filho.margem}"
                grafo.add_edge(u, v)
                fila.append(filho)

        return grafo

    def _texto_margem(self, margem):
        mapa = {
            "L": "Esquerda",
            "E": "Esquerda",
            "left": "Esquerda",
            "R": "Direita",
            "D": "Direita",
            "right": "Direita",
        }
        chave = str(margem).strip()
        return mapa.get(chave, chave)

    def _label_no(self, no_id):
        canibais, resto = no_id.split("C_", 1)
        missionarios, margem = resto.split("M_", 1)
        canibais = int(canibais)
        missionarios = int(missionarios)
        margem_txt = self._texto_margem(margem)
        canibais_dir = self.total_canibais - canibais
        missionarios_dir = self.total_missionarios - missionarios
        return (
            f"Esq -> M:{missionarios} C:{canibais}\n"
            f"Dir -> M:{missionarios_dir} C:{canibais_dir}\n"
            f"Barco: {margem_txt}"
        )

    def alternar_layout(self, event):
        self.modo_arvore = not self.modo_arvore
        self.atualizar_grafico()

    def _ao_scroll_zoom(self, event):
        if event.inaxes != self.ax:
            return

        base_scale = 1.15
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            return

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata

        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor

        relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
        rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
        self.zoom_limits = (self.ax.get_xlim(), self.ax.get_ylim())
        self.fig.canvas.draw_idle()

    def _ao_click_mouse(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == 1 and event.x is not None and event.y is not None:
            self.pan_ativo = True
            self.pan_inicio = (event.x, event.y)
            self.pan_xlim_inicio = self.ax.get_xlim()
            self.pan_ylim_inicio = self.ax.get_ylim()
        if event.button == 3:
            self.zoom_limits = None
            self.atualizar_grafico()

    def _ao_soltar_mouse(self, event):
        if event.button == 1:
            self.pan_ativo = False
            self.pan_inicio = None
            self.pan_xlim_inicio = None
            self.pan_ylim_inicio = None

    def _ao_mover_mouse(self, event):
        if not self.pan_ativo:
            return
        if event.inaxes != self.ax:
            return
        if event.x is None or event.y is None or self.pan_inicio is None:
            return
        if self.pan_xlim_inicio is None or self.pan_ylim_inicio is None:
            return

        x0, y0 = self.pan_inicio
        dx_pixels = event.x - x0
        dy_pixels = event.y - y0

        bbox = self.ax.get_window_extent()
        if bbox.width == 0 or bbox.height == 0:
            return

        largura_dados = self.pan_xlim_inicio[1] - self.pan_xlim_inicio[0]
        altura_dados = self.pan_ylim_inicio[1] - self.pan_ylim_inicio[0]

        dx_dados = (dx_pixels / bbox.width) * largura_dados
        dy_dados = (dy_pixels / bbox.height) * altura_dados

        self.ax.set_xlim(self.pan_xlim_inicio[0] - dx_dados, self.pan_xlim_inicio[1] - dx_dados)
        self.ax.set_ylim(self.pan_ylim_inicio[0] - dy_dados, self.pan_ylim_inicio[1] - dy_dados)

        self.zoom_limits = (self.ax.get_xlim(), self.ax.get_ylim())
        self.fig.canvas.draw_idle()

    def atualizar_grafico(self):
        limites_zoom = self.zoom_limits
        self.ax.clear()
        self.G.clear()
        
        no_foco = self.passos_bfs[self.index_atual]
        id_raiz = f"{self.raiz.canibais}C_{self.raiz.missionarios}M_{self.raiz.margem}"
        
        # Reconstruir o grafo até a iteração atual
        caminho_solucao = []
        temp = no_foco
        while temp:
            caminho_solucao.append(f"{temp.canibais}C_{temp.missionarios}M_{temp.margem}")
            temp = temp.parent

        for i in range(self.index_atual + 1):
            no = self.passos_bfs[i]
            u = f"{no.canibais}C_{no.missionarios}M_{no.margem}"
            self.G.add_node(u)

        ids_visiveis = set(self.G.nodes())
        esta_no_final_objetivo = self.index_atual == len(self.passos_bfs) - 1 and self._eh_objetivo(no_foco)

        for i in range(self.index_atual + 1):
            no = self.passos_bfs[i]
            u = f"{no.canibais}C_{no.missionarios}M_{no.margem}"
            for filho in no.children:
                v = f"{filho.canibais}C_{filho.missionarios}M_{filho.margem}"
                if not esta_no_final_objetivo:
                    self.G.add_edge(u, v)
                elif v in ids_visiveis:
                    self.G.add_edge(u, v)

        # Escolha do Layout
        if self.modo_arvore:
            pos = {node: self.posicoes_arvore_fixas[node] for node in self.G.nodes()}
            tipo_txt = "ÁRVORE (Hierárquico)"
        else:
            pos = nx.spring_layout(self.G, seed=42)
            tipo_txt = "GRAFO (Dinâmico)"

        # Cores e Destaques
        colors = []
        for node in self.G.nodes():
            if node == f"{no_foco.canibais}C_{no_foco.missionarios}M_{no_foco.margem}":
                colors.append('#e74c3c') # Vermelho: No atual sendo expandido
            elif node in caminho_solucao:
                colors.append('#2ecc71') # Verde: Caminho até a raiz
            else:
                colors.append('#3498db') # Azul: Outros nós

        labels = {node: self._label_no(node) for node in self.G.nodes()}

        nx.draw(self.G, pos, labels=labels, with_labels=True, node_color=colors, 
                node_size=2400, font_size=8, ax=self.ax, 
                edge_color='#bdc3c7', arrows=True, arrowsize=15)

        patch_azul = mpatches.Patch(color='#3498db', label='Azul: Nós explorados')
        patch_verde = mpatches.Patch(color='#2ecc71', label='Verde: Caminho até raiz')
        patch_vermelho = mpatches.Patch(color='#e74c3c', label='Vermelho: Nó em foco')
        self.ax.legend(handles=[patch_azul, patch_verde, patch_vermelho], 
                       loc='upper left', fontsize=9, framealpha=0.9)

        margem_foco = self._texto_margem(no_foco.margem)
        canibais_dir_foco = self.total_canibais - no_foco.canibais
        missionarios_dir_foco = self.total_missionarios - no_foco.missionarios
        
        self.ax.set_title(f"Modo: {tipo_txt} | Iteração: {self.index_atual + 1}/{len(self.passos_bfs)}\n"
                 f"Foco -> Esq(M:{no_foco.missionarios}, C:{no_foco.canibais}) | Dir(M:{missionarios_dir_foco}, C:{canibais_dir_foco}) | Barco: {margem_foco}", 
                         fontsize=11, fontweight='bold', pad=20)

        if limites_zoom is not None:
            self.ax.set_xlim(limites_zoom[0])
            self.ax.set_ylim(limites_zoom[1])
            self.zoom_limits = limites_zoom
        
        plt.draw()

    def avancar(self, event):
        if self.index_atual < len(self.passos_bfs) - 1:
            self.index_atual += 1
            self.atualizar_grafico()

    def retroceder(self, event):
        if self.index_atual > 0:
            self.index_atual -= 1
            self.atualizar_grafico()

if __name__ == "__main__":
    PASTA_DADOS = Path(__file__).parent / "data"

    def pedir_inteiro(msg, minimo=0):
        while True:
            try:
                valor = int(input(msg).strip())
                if valor < minimo:
                    print(f"❌ Digite um inteiro >= {minimo}.")
                    continue
                return valor
            except ValueError:
                print("❌ Entrada inválida. Digite um número inteiro.")

    print("Informe os parâmetros para abrir o grafo:")
    X = pedir_inteiro("Missionários (X): ", minimo=0)
    Y = pedir_inteiro("Canibais (Y): ", minimo=0)
    Z = pedir_inteiro("Capacidade do barco (Z): ", minimo=1)

    ARQUIVO = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"
    if ARQUIVO.exists():
        BFSVisualizer(ARQUIVO, capacidade_barco=Z)
    else:
        print(f"❌ Arquivo não encontrado: {ARQUIVO}")
        print("💡 Rode o main.py com os mesmos valores de X, Y e Z para gerar esse grafo.")