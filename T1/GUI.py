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
    def __init__(self, arquivo_grafo, ax=None, tipo="normal", capacidade_barco=None, synchronizer=None):
        self.arquivo = arquivo_grafo
        self.ax = ax
        self.tipo = tipo  # "normal" ou "otimizado"
        self.synchronizer = synchronizer  # Para sincronizar múltiplos visualizadores
        self.raiz = self._carregar_grafo()
        self.total_canibais = self.raiz.canibais
        self.total_missionarios = self.raiz.missionarios
        self.capacidade_barco = self._inferir_capacidade_barco(capacidade_barco)
        self.passos_bfs = []
        self._mapear_ordem_bfs(self.raiz)

        self.grafo_completo = self._construir_grafo_completo()
        id_raiz = f"{self.raiz.canibais}C_{self.raiz.missionarios}M_{self.raiz.margem}"
        self.posicoes_arvore_fixas = hierarquia_pos(self.grafo_completo, root=id_raiz)
        self.nos_limpos_por_iteracao = self._precomputar_nos_limpos_otimizado(id_raiz)
        
        self.index_atual = 0
        self.modo_arvore = True  # Estado inicial
        self.G = nx.DiGraph()
        self.zoom_limits = None
        self.pan_ativo = False
        self.pan_inicio = None
        self.pan_xlim_inicio = None
        self.pan_ylim_inicio = None
    
    def atualizar_com_indice(self, index):
        """Atualiza a exibição com um novo índice (usado pela sincronização)"""
        self.index_atual = index
        self.atualizar_grafico()


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

    def _precomputar_nos_limpos_otimizado(self, id_raiz):
        """Simula a limpeza do BFS otimizado e retorna nós limpos por iteração."""
        if self.tipo != "otimizado":
            return {}

        objetivo_id = None
        if self.passos_bfs and self._eh_objetivo(self.passos_bfs[-1]):
            no_final = self.passos_bfs[-1]
            objetivo_id = f"{no_final.canibais}C_{no_final.missionarios}M_{no_final.margem}"

        fila = deque([id_raiz])
        visitados = set()
        limpos_acumulados = set()
        limpos_por_iteracao = {}
        iteracao = 0

        while fila:
            atual = fila.popleft()
            if atual in visitados:
                continue

            visitados.add(atual)
            iteracao += 1

            if objetivo_id is not None and atual == objetivo_id:
                limpos_por_iteracao[iteracao] = set(limpos_acumulados)
                break

            filhos_novos = [v for v in self.grafo_completo.successors(atual) if v not in visitados]
            fila.extend(filhos_novos)

            if not filhos_novos and atual != id_raiz:
                limpos_acumulados.add(atual)

            limpos_por_iteracao[iteracao] = set(limpos_acumulados)

        if iteracao < len(self.passos_bfs):
            ultimo = set(limpos_acumulados)
            for i in range(iteracao + 1, len(self.passos_bfs) + 1):
                limpos_por_iteracao[i] = set(ultimo)

        return limpos_por_iteracao

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
    
    def _label_no_compacto(self, no_id):
        """Label compacto para não poluir o visual"""
        canibais, resto = no_id.split("C_", 1)
        missionarios, margem = resto.split("M_", 1)
        canibais = int(canibais)
        missionarios = int(missionarios)
        margem_char = "E" if self._normalizar_margem(margem) == "esquerda" else "D"
        return f"M{missionarios}C{canibais}|{margem_char}"

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
        self.ax.figure.canvas.draw_idle()

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
        self.ax.figure.canvas.draw_idle()

    def atualizar_grafico(self):
        limites_zoom = self.zoom_limits
        self.ax.clear()
        self.G.clear()
        nos_limpos_ate_iteracao = self.nos_limpos_por_iteracao.get(self.index_atual + 1, set())
        
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
            elif self.tipo == "otimizado" and node in nos_limpos_ate_iteracao:
                colors.append('#f39c12') # Laranja: Nó limpo da memória pelo otimizado
            else:
                colors.append('#3498db') # Azul: Nós já explorados

        labels = {node: self._label_no(node) for node in self.G.nodes()}

        nx.draw(self.G, pos, labels=labels, with_labels=True, node_color=colors, 
                node_size=2400, font_size=8, ax=self.ax, 
                edge_color='#bdc3c7', arrows=True, arrowsize=15)

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
        
        self.ax.figure.canvas.draw_idle()

    def avancar(self, event):
        if self.index_atual < len(self.passos_bfs) - 1:
            self.index_atual += 1
            self.atualizar_grafico()

    def retroceder(self, event):
        if self.index_atual > 0:
            self.index_atual -= 1
            self.atualizar_grafico()
            if self.synchronizer:
                self.synchronizer.sincronizar(self.index_atual)


def executar_duas_gui_simultaneas(arquivo_normal, arquivo_otimizado, Z):
    """Abre duas GUIs lado a lado (normal e otimizado) com sincronização"""
    
    # Criar figura com 2 subplots
    fig = plt.figure(figsize=(20, 9))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    
    # Criar os visualizadores
    viz_normal = BFSVisualizer(arquivo_normal, ax=ax1, tipo="normal", capacidade_barco=Z)
    viz_otimizado = BFSVisualizer(arquivo_otimizado, ax=ax2, tipo="otimizado", capacidade_barco=Z)
    
    # Sincronizador para manter ambos no mesmo índice
    class Sincronizador:
        def __init__(self, v1, v2):
            self.v1 = v1
            self.v2 = v2
        
        def sincronizar(self, index):
            self.v1.index_atual = index
            self.v2.index_atual = index
            self.v1.atualizar_grafico()
            self.v2.atualizar_grafico()
        
        def avancar(self, event):
            max_index = max(len(self.v1.passos_bfs), len(self.v2.passos_bfs)) - 1
            if self.v1.index_atual < max_index:
                novo_index = self.v1.index_atual + 1
                self.sincronizar(novo_index)
        
        def retroceder(self, event):
            if self.v1.index_atual > 0:
                novo_index = self.v1.index_atual - 1
                self.sincronizar(novo_index)
        
        def alternar_layout(self, event):
            self.v1.modo_arvore = not self.v1.modo_arvore
            self.v2.modo_arvore = not self.v2.modo_arvore
            self.v1.atualizar_grafico()
            self.v2.atualizar_grafico()
    
    sincronizador = Sincronizador(viz_normal, viz_otimizado)
    viz_normal.synchronizer = sincronizador
    viz_otimizado.synchronizer = sincronizador
    
    # Adicionar títulos aos subplots
    viz_normal.ax.text(0.5, 1.05, "BFS Normal", ha='center', va='bottom', 
                       transform=viz_normal.ax.transAxes, fontsize=13, fontweight='bold')
    viz_otimizado.ax.text(0.5, 1.05, "BFS Otimizado", ha='center', va='bottom',
                          transform=viz_otimizado.ax.transAxes, fontsize=13, fontweight='bold')
    
    # Botões de Navegação (compartilhados)
    plt.subplots_adjust(left=0.17, bottom=0.15)

    # Legenda global única (canto esquerdo da tela)
    patch_azul = mpatches.Patch(color='#3498db', label='Azul: Nós explorados')
    patch_verde = mpatches.Patch(color='#2ecc71', label='Verde: Caminho até raiz')
    patch_vermelho = mpatches.Patch(color='#e74c3c', label='Vermelho: Nó em foco')
    patch_laranja = mpatches.Patch(color='#f39c12', label='Laranja: Nó limpo da memória (apenas otimizado)')
    fig.legend(
        handles=[patch_azul, patch_verde, patch_vermelho, patch_laranja],
        loc='center left',
        bbox_to_anchor=(0.01, 0.5),
        fontsize=10,
        framealpha=0.95
    )
    
    ax_prev = fig.add_axes([0.3, 0.05, 0.1, 0.06])
    ax_next = fig.add_axes([0.41, 0.05, 0.1, 0.06])
    ax_mode = fig.add_axes([0.55, 0.05, 0.2, 0.06])
    
    btn_prev = Button(ax_prev, '⬅ Anterior')
    btn_next = Button(ax_next, 'Próximo ➡')
    btn_mode = Button(ax_mode, 'Alternar: Árvore/Grafo')
    
    btn_prev.on_clicked(sincronizador.retroceder)
    btn_next.on_clicked(sincronizador.avancar)
    btn_mode.on_clicked(sincronizador.alternar_layout)
    
    # Conectar eventos do canvas
    fig.canvas.mpl_connect('scroll_event', lambda event: handle_scroll(event, viz_normal, viz_otimizado))
    fig.canvas.mpl_connect('button_press_event', lambda event: handle_click_press(event, viz_normal, viz_otimizado))
    fig.canvas.mpl_connect('button_release_event', lambda event: handle_click_release(event, viz_normal, viz_otimizado))
    fig.canvas.mpl_connect('motion_notify_event', lambda event: handle_move(event, viz_normal, viz_otimizado))
    
    # Título geral
    fig.suptitle(f"Comparação de BFS - Capacidade do barco: {Z}", 
                 fontsize=14, fontweight='bold', y=0.98)
    
    # Atualizar os gráficos inicial
    viz_normal.atualizar_grafico()
    viz_otimizado.atualizar_grafico()
    
    plt.show()


def handle_scroll(event, viz1, viz2):
    """Manipula zoom individual para cada plot"""
    if event.inaxes == viz1.ax:
        viz1._ao_scroll_zoom(event)
    elif event.inaxes == viz2.ax:
        viz2._ao_scroll_zoom(event)


def handle_click_press(event, viz1, viz2):
    """Manipula clique individual"""
    if event.inaxes == viz1.ax:
        viz1._ao_click_mouse(event)
    elif event.inaxes == viz2.ax:
        viz2._ao_click_mouse(event)


def handle_click_release(event, viz1, viz2):
    """Manipula soltar clique"""
    if event.inaxes == viz1.ax or event.inaxes == viz2.ax:
        if event.inaxes == viz1.ax:
            viz1._ao_soltar_mouse(event)
        else:
            viz2._ao_soltar_mouse(event)


def handle_move(event, viz1, viz2):
    """Manipula movimento do mouse"""
    if event.inaxes == viz1.ax:
        viz1._ao_mover_mouse(event)
    elif event.inaxes == viz2.ax:
        viz2._ao_mover_mouse(event)


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

    print("Informe os parâmetros para abrir os gráfos:")
    X = pedir_inteiro("Missionários (X): ", minimo=0)
    Y = pedir_inteiro("Canibais (Y): ", minimo=0)
    Z = pedir_inteiro("Capacidade do barco (Z): ", minimo=1)

    arquivo_base = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"
    
    print("\n🚀 Abrindo visualizações comparativas...\n")
    
    if arquivo_base.exists():
        executar_duas_gui_simultaneas(arquivo_base, arquivo_base, Z)
    else:
        print("❌ Arquivo não encontrado:")
        print(f"   • Grafo base: {arquivo_base}")
        print("\n💡 Rode o main.py com os mesmos valores de X, Y e Z para gerar o grafo.")