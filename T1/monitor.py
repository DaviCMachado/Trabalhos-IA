import pickle
import matplotlib.pyplot as plt
import gc
from pathlib import Path
from search_engine import SearchEngine
from node import Node


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
            tempo = fn()
            if nome == "normal":
                tempos_normal.append(tempo)
            else:
                tempos_otimizado.append(tempo)

    media_normal = sum(tempos_normal) / len(tempos_normal) if tempos_normal else 0.0
    media_otimizado = sum(tempos_otimizado) / len(tempos_otimizado) if tempos_otimizado else 0.0

    return media_normal, media_otimizado


def executar_busca(tipo, X, Y, Z, arquivo_grafo):
    objetivo = (0, 0, "direita")
    engine = SearchEngine(X, Y, Z, arquivo_grafo=arquivo_grafo, pickle_module=pickle)
    raiz = Node(X, Y, "esquerda")

    if tipo == "otimizado":
        return engine.bfs_memory_optimized(raiz, objetivo)
    return engine.bfs(raiz, objetivo)

class PerformanceMonitor:
    def __init__(self, arquivo_grafo, tipo="normal", X=None, Y=None, Z=None, verbose=True):
        self.arquivo = arquivo_grafo
        self.tipo = tipo  # "normal" ou "otimizado"
        self.X = X
        self.Y = Y
        self.Z = Z
        self.iteracoes = []
        self.memorias = []
        self.tempo_execucao = 0.0
        self.resultado = None
        
        if verbose:
            print(f"📊 Analisando consumo de memória por iteração ({tipo})...")
        self.resultado = executar_busca(self.tipo, self.X, self.Y, self.Z, self.arquivo)
        self.tempo_execucao = self.resultado["tempo"]
        self.iteracoes = self.resultado.get("iteracoes_memoria", self.resultado.get("iteracoes_memoria_real", []))
        self.memorias = self.resultado.get("serie_memoria", self.resultado.get("serie_memoria_real", []))

    def plotar_em_subplot(self, ax):
        """Plota o gráfico em um subplot fornecido"""
        if not self.iteracoes or not self.memorias:
            ax.set_title("Sem dados de memória", fontsize=12, fontweight='bold')
            ax.set_xlabel("Iteração (Nós Explorados)", fontsize=10)
            ax.set_ylabel("Memória (KB)", fontsize=10)
            ax.grid(True, alpha=0.3)
            return None

        # Linha de Memória
        linha, = ax.plot(self.iteracoes, self.memorias, marker='o', linestyle='-', 
                 color='#8e44ad', markersize=4, alpha=0.8, label='Memória (KB)')
        
        # Preenchimento sob a curva
        ax.fill_between(self.iteracoes, self.memorias, color='#8e44ad', alpha=0.18)

        # Configurações de Eixos
        tipo_label = "BFS Normal" if self.tipo == "normal" else "BFS Otimizado"
        pico_memoria = self.resultado["memoria"] if self.resultado else 0.0
        memoria_atual = self.resultado.get("memoria_atual", 0.0) if self.resultado else 0.0
        ax.set_title(
            f"{tipo_label} ({self.X}x{self.Y}, Barco={self.Z})\nTempo: {self.tempo_execucao:.6f} s | Pico: {pico_memoria:.2f} KB | Atual: {memoria_atual:.2f} KB",
            fontsize=12,
            fontweight='bold'
        )
        ax.set_xlabel("Iteração (Nós Explorados)", fontsize=10)
        ax.set_ylabel("Memória (KB)", fontsize=10)
        
        # Destaque de pico no gráfico
        indice_pico = max(range(len(self.memorias)), key=self.memorias.__getitem__)
        pico_mem = self.memorias[indice_pico]
        iteracao_pico = self.iteracoes[indice_pico]

        ax.axhline(y=pico_mem, color='red', linestyle='--', linewidth=1.6, alpha=0.9, zorder=7, label=f"Pico: {pico_mem:.2f} KB")
        ax.scatter(
            [iteracao_pico],
            [pico_mem],
            color='red',
            edgecolors='white',
            linewidths=0.8,
            s=70,
            zorder=8
        )
        ax.annotate(
            f"Pico {pico_mem:.2f} KB",
            xy=(iteracao_pico, pico_mem),
            xytext=(8, 8),
            textcoords='offset points',
            fontsize=9,
            color='red',
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.85),
            zorder=9
        )

        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return linha


def monitores_simultaneos(arquivo_normal, arquivo_otimizado, X=None, Y=None, Z=None):
    """Cria e exibe dois gráficos de performance simultaneamente"""
    monitor_normal = PerformanceMonitor(arquivo_normal, tipo="normal", X=X, Y=Y, Z=Z)
    monitor_otimizado = PerformanceMonitor(arquivo_otimizado, tipo="otimizado", X=X, Y=Y, Z=Z)

    # Medição justa de tempo (alternando ordem para evitar viés de cache)
    def _tempo_normal():
        return executar_busca("normal", X, Y, Z, arquivo_normal)["tempo"]

    def _tempo_otimizado():
        return executar_busca("otimizado", X, Y, Z, arquivo_otimizado)["tempo"]

    tempo_normal_medio, tempo_otimizado_medio = medir_tempos_justos(_tempo_normal, _tempo_otimizado)
    monitor_normal.tempo_execucao = tempo_normal_medio
    monitor_otimizado.tempo_execucao = tempo_otimizado_medio

    # Criar figura com 2 subplots lado a lado
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plotar ambos
    linha1 = monitor_normal.plotar_em_subplot(ax1)
    linha2 = monitor_otimizado.plotar_em_subplot(ax2)

    # Hover interativo em camada da figura (acima dos dois gráficos)
    tooltip = fig.text(
        0,
        0,
        "",
        fontsize=9,
        va='bottom',
        ha='left',
        bbox=dict(boxstyle="round", fc="w", ec="#7f8c8d", alpha=0.95),
        zorder=1000,
        visible=False
    )

    def atualizar_tooltip(linha, ind, event):
        xs, ys = linha.get_data()
        idx = ind["ind"][0]
        x = xs[idx]
        y = ys[idx]
        tooltip.set_text(f"Iteração: {int(x)}\nMemória: {y:.2f} KB")

        largura_fig, altura_fig = fig.get_size_inches() * fig.dpi
        xf = min(max((event.x + 14) / largura_fig, 0.02), 0.92)
        yf = min(max((event.y + 14) / altura_fig, 0.02), 0.92)
        tooltip.set_position((xf, yf))

    def on_hover(event):
        mudou = False

        if event.inaxes == ax1:
            cont1, ind1 = linha1.contains(event)
            if cont1:
                atualizar_tooltip(linha1, ind1, event)
                if not tooltip.get_visible():
                    tooltip.set_visible(True)
                mudou = True
            else:
                if tooltip.get_visible():
                    tooltip.set_visible(False)
                    mudou = True

        elif event.inaxes == ax2:
            cont2, ind2 = linha2.contains(event)
            if cont2:
                atualizar_tooltip(linha2, ind2, event)
                if not tooltip.get_visible():
                    tooltip.set_visible(True)
                mudou = True
            else:
                if tooltip.get_visible():
                    tooltip.set_visible(False)
                    mudou = True
        else:
            if tooltip.get_visible():
                tooltip.set_visible(False)
                mudou = True

        if mudou:
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)
    
    # Sincronizar limites verticais para facilitar comparação
    pico_max = max(monitor_normal.resultado["memoria"], monitor_otimizado.resultado["memoria"])
    eixo_y_limite = pico_max * 1.1  # Margem de 10% acima do pico máximo
    ax1.set_ylim(bottom=0, top=eixo_y_limite)
    ax2.set_ylim(bottom=0, top=eixo_y_limite)

    # Sincronizar limite horizontal para facilitar comparação
    x_max_normal = max(monitor_normal.iteracoes) if monitor_normal.iteracoes else 1
    x_max_otim = max(monitor_otimizado.iteracoes) if monitor_otimizado.iteracoes else 1
    x_max_global = max(x_max_normal, x_max_otim)
    ax1.set_xlim(left=1, right=x_max_global)
    ax2.set_xlim(left=1, right=x_max_global)
    
    # Título geral
    fig.suptitle(f"Comparação de Performance - BFS Normal vs Otimizado ({X}x{Y}, Barco={Z})", 
                 fontsize=14, fontweight='bold', y=0.98)

    
    plt.tight_layout()
    
    # Calcular e exibir statísticas comparativas
    print("\n" + "="*60)
    print("📊 COMPARAÇÃO DE PERFORMANCE")
    print("="*60)
    print(f"\nBFS Normal:")
    print(f"  • Total de iterações: {monitor_normal.resultado['visitados']}")
    print(f"  • Tempo de execução: {monitor_normal.tempo_execucao:.6f} s")
    print(f"  • Pico de memória: {monitor_normal.resultado['memoria']:.2f} KB")
    print(f"  • Memória atual: {monitor_normal.resultado.get('memoria_atual', 0.0):.2f} KB")
    print(f"\nBFS Otimizado:")
    print(f"  • Total de iterações: {monitor_otimizado.resultado['visitados']}")
    print(f"  • Tempo de execução: {monitor_otimizado.tempo_execucao:.6f} s")
    print(f"  • Pico de memória: {monitor_otimizado.resultado['memoria']:.2f} KB")
    print(f"  • Memória atual: {monitor_otimizado.resultado.get('memoria_atual', 0.0):.2f} KB")
    
    # Economias
    economia_pico = ((monitor_normal.resultado['memoria'] - monitor_otimizado.resultado['memoria']) /
                     monitor_normal.resultado['memoria'] * 100) if monitor_normal.resultado['memoria'] > 0 else 0
    memoria_atual_normal = monitor_normal.resultado.get('memoria_atual', 0.0)
    memoria_atual_otim = monitor_otimizado.resultado.get('memoria_atual', 0.0)
    economia_final = ((memoria_atual_normal - memoria_atual_otim) / memoria_atual_normal * 100) if memoria_atual_normal > 0 else 0
    diferenca_tempo = monitor_normal.tempo_execucao - monitor_otimizado.tempo_execucao
    
    print(f"\n💰 ECONOMIA COM OTIMIZAÇÃO:")
    print(f"  • Diferença de tempo (normal - otimizado): {diferenca_tempo:.6f} s")
    print(f"  • Redução de pico: {economia_pico:.1f}%")
    print(f"  • Redução de memória atual: {economia_final:.1f}%")
    print("="*60 + "\n")
    
    plt.show()

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

    print("Informe os parâmetros para analisar o grafo:")
    X = pedir_inteiro("Missionários (X): ", minimo=0)
    Y = pedir_inteiro("Canibais (Y): ", minimo=0)
    Z = pedir_inteiro("Capacidade do barco (Z): ", minimo=1)

    arquivo_base = PASTA_DADOS / f"grafo_{X}x{Y}_z{Z}.pkl"
    
    if arquivo_base.exists():
        print("\n🚀 Gerando gráficos comparativos...\n")
        monitores_simultaneos(arquivo_base, arquivo_base, X=X, Y=Y, Z=Z)
    else:
        print("\n❌ Arquivo não encontrado:")
        print(f"   • Grafo base: {arquivo_base}")
        print("\n💡 Rode o main.py com os mesmos valores de X, Y e Z para gerar o grafo.")