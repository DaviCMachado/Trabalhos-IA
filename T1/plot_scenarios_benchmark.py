import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import tkinter as tk
from tkinter import ttk


BASE_DIR = Path(__file__).parent
SCENARIOS_PATH = BASE_DIR / "scenarios.json"


def carregar_dados_validos(caminho_json):
    with open(caminho_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    testes = payload.get("testes", [])
    pontos = []

    for teste in testes:
        entrada = teste.get("in", {})
        saida = teste.get("out", {})

        if saida.get("status") != "ok":
            continue

        bfs = saida.get("bfs", {})
        opt = saida.get("bfs_otimizado", {})

        if not bfs or not opt:
            continue

        ponto = {
            "X": int(entrada.get("X", 0)),
            "Y": int(entrada.get("Y", 0)),
            "Z": int(entrada.get("Z", 0)),
            "tempo_bfs": float(bfs.get("tempo_s", 0.0)),
            "tempo_opt": float(opt.get("tempo_s", 0.0)),
            "mem_bfs": float(bfs.get("memoria_kb", 0.0)),
            "mem_opt": float(opt.get("memoria_kb", 0.0)),
        }
        pontos.append(ponto)

    pontos.sort(key=lambda p: (p["X"], p["Y"], p["Z"]))
    return pontos


def plotar_cenarios(pontos):
    if not pontos:
        print("❌ Nenhum cenário válido encontrado em scenarios.json (status=ok).")
        return


    # Estado do modo: 'miscan' ou 'livre'
    modo = {"valor": "miscan"}  # começa em mis=can

    # Obter todos os valores únicos de Z
    valores_z = sorted({p['Z'] for p in pontos})
    z_inicial = valores_z[0]
    z_selecionado = {"valor": z_inicial}

    # Função para filtrar pontos pelo Z e modo selecionados
    def filtrar_por_z_e_modo(z, modo):
        if modo == "miscan":
            return [p for p in pontos if p['Z'] == z and p['X'] == p['Y']]
        else:
            return [p for p in pontos if p['Z'] == z and p['X'] > p['Y']]

    # Função para plotar os dados filtrados

    def plot_filtrado(z):
        pts = filtrar_por_z_e_modo(z, modo["valor"])
        ax_tempo.clear()
        ax_mem.clear()

        if modo["valor"] == "miscan":
            modo_str = "mis=can (X=Y)"
        else:
            modo_str = "livre (X>Y)"

        if not pts:
            ax_tempo.set_title(f"Nenhum cenário com Z={z} e modo {modo_str}")
            fig.canvas.draw_idle()
            return None

        labels = [f"{p['X']},{p['Y']},{p['Z']}" for p in pts]
        eixo_x = list(range(len(pts)))
        tempo_bfs = [p["tempo_bfs"] for p in pts]
        tempo_opt = [p["tempo_opt"] for p in pts]
        mem_bfs = [p["mem_bfs"] for p in pts]
        mem_opt = [p["mem_opt"] for p in pts]


        # Linhas e pontos (scatter) para tooltips
        linha_tempo_bfs, = ax_tempo.plot(
            eixo_x,
            tempo_bfs,
            marker="o",
            linewidth=2,
            color="#1f77b4",
            label="Tempo BFS (s)",
        )
        scatter_tempo_bfs = ax_tempo.scatter(
            eixo_x, tempo_bfs, color="#1f77b4", marker="o", s=60, alpha=0, picker=True, zorder=20
        )
        linha_tempo_opt, = ax_tempo.plot(
            eixo_x,
            tempo_opt,
            marker="o",
            linewidth=2,
            color="#ff7f0e",
            label="Tempo BFS Otimizado (s)",
        )
        scatter_tempo_opt = ax_tempo.scatter(
            eixo_x, tempo_opt, color="#ff7f0e", marker="o", s=60, alpha=0, picker=True, zorder=20
        )
        linha_mem_bfs, = ax_mem.plot(
            eixo_x,
            mem_bfs,
            marker="s",
            linewidth=2,
            linestyle="--",
            color="#1f77b4",
            label="Memória BFS (KB)",
        )
        scatter_mem_bfs = ax_mem.scatter(
            eixo_x, mem_bfs, color="#1f77b4", marker="s", s=60, alpha=0, picker=True, zorder=30, clip_on=False
        )
        linha_mem_opt, = ax_mem.plot(
            eixo_x,
            mem_opt,
            marker="s",
            linewidth=2,
            linestyle="--",
            color="#ff7f0e",
            label="Memória BFS Otimizado (KB)",
        )
        scatter_mem_opt = ax_mem.scatter(
            eixo_x, mem_opt, color="#ff7f0e", marker="s", s=60, alpha=0, picker=True, zorder=30, clip_on=False
        )

        scatters = [scatter_tempo_bfs, scatter_tempo_opt, scatter_mem_bfs, scatter_mem_opt]

        ax_tempo.set_xlabel("Cenários (X,Y,Z) em ordem crescente", fontsize=11)
        ax_tempo.set_xticks(eixo_x)
        ax_tempo.set_xticklabels(labels, rotation=60, ha="right", fontsize=9)
        fig.suptitle(
            f"Comparação BFS vs BFS Otimizado por Cenário (Z={z}, modo: {modo_str})\n"
            "(4 linhas: tempo BFS, tempo otimizado, memória BFS, memória otimizado)",
            fontsize=14,
            fontweight="bold",
        )
        linhas = [linha_tempo_bfs, linha_tempo_opt, linha_mem_bfs, linha_mem_opt]
        estado = {"tempo_visivel": True, "memoria_visivel": True}

        def atualizar_legenda():
            linhas_visiveis = [l for l in linhas if l.get_visible()]
            labels_visiveis = [l.get_label() for l in linhas_visiveis]
            if linhas_visiveis:
                ax_tempo.legend(linhas_visiveis, labels_visiveis, loc="upper left", framealpha=0.95)
            else:
                legenda = ax_tempo.get_legend()
                if legenda is not None:
                    legenda.remove()

        atualizar_legenda()

        def alternar_tempo(event):
            estado["tempo_visivel"] = not estado["tempo_visivel"]
            linha_tempo_bfs.set_visible(estado["tempo_visivel"])
            linha_tempo_opt.set_visible(estado["tempo_visivel"])
            atualizar_legenda()
            fig.canvas.draw_idle()

        def alternar_memoria(event):
            estado["memoria_visivel"] = not estado["memoria_visivel"]
            linha_mem_bfs.set_visible(estado["memoria_visivel"])
            linha_mem_opt.set_visible(estado["memoria_visivel"])
            atualizar_legenda()
            fig.canvas.draw_idle()

        btn_tempo.on_clicked(alternar_tempo)
        btn_memoria.on_clicked(alternar_memoria)


        # Tooltips separados para cada eixo
        tooltip_tempo = ax_tempo.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w", ec="#333", lw=1.5),
                                    arrowprops=dict(arrowstyle="->", lw=1.5),
                                    fontsize=12, zorder=100, clip_on=False)
        tooltip_mem = ax_mem.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w", ec="#333", lw=1.5),
                                    arrowprops=dict(arrowstyle="->", lw=1.5),
                                    fontsize=12, zorder=100, clip_on=False)
        tooltip_tempo.set_visible(False)
        tooltip_mem.set_visible(False)

        def on_motion(event):
            vis_tempo = tooltip_tempo.get_visible()
            vis_mem = tooltip_mem.get_visible()
            if event.inaxes not in [ax_tempo, ax_mem]:
                if vis_tempo:
                    tooltip_tempo.set_visible(False)
                if vis_mem:
                    tooltip_mem.set_visible(False)
                fig.canvas.draw_idle()
                return
            for idx, scatter in enumerate(scatters):
                cont, ind = scatter.contains(event)
                if cont:
                    i = ind["ind"][0]
                    if idx == 0:
                        txt = f"BFS\n{labels[i]}\nTempo: {tempo_bfs[i]:.6g} s"
                        xy = (eixo_x[i], tempo_bfs[i])
                        tooltip = tooltip_tempo
                        other = tooltip_mem
                    elif idx == 1:
                        txt = f"BFS Otimizado\n{labels[i]}\nTempo: {tempo_opt[i]:.6g} s"
                        xy = (eixo_x[i], tempo_opt[i])
                        tooltip = tooltip_tempo
                        other = tooltip_mem
                    elif idx == 2:
                        txt = f"BFS\n{labels[i]}\nMemória: {mem_bfs[i]:.4g} KB"
                        xy = (eixo_x[i], mem_bfs[i])
                        tooltip = tooltip_mem
                        other = tooltip_tempo
                    else:
                        txt = f"BFS Otimizado\n{labels[i]}\nMemória: {mem_opt[i]:.4g} KB"
                        xy = (eixo_x[i], mem_opt[i])
                        tooltip = tooltip_mem
                        other = tooltip_tempo
                    tooltip.xy = xy
                    tooltip.set_text(txt)
                    tooltip.set_visible(True)
                    tooltip.set_zorder(100)
                    other.set_visible(False)
                    fig.canvas.draw_idle()
                    return
            if vis_tempo:
                tooltip_tempo.set_visible(False)
            if vis_mem:
                tooltip_mem.set_visible(False)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_motion)

        fig.tight_layout(rect=[0, 0.12, 1, 1])
        fig.canvas.draw_idle()
        return (alternar_tempo, alternar_memoria)

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax_tempo = plt.subplots(figsize=(16, 8))
    plt.subplots_adjust(bottom=0.18)
    ax_mem = ax_tempo.twinx()


    # Botões
    ax_btn_tempo = fig.add_axes([0.22, 0.04, 0.18, 0.07])
    ax_btn_memoria = fig.add_axes([0.42, 0.04, 0.18, 0.07])
    btn_tempo = Button(ax_btn_tempo, "Exibir/Ocultar Tempo")
    btn_memoria = Button(ax_btn_memoria, "Exibir/Ocultar Memória")

    # Botão para selecionar Z
    ax_btn_z = fig.add_axes([0.62, 0.04, 0.16, 0.07])
    btn_z = Button(ax_btn_z, f"Selecionar Z (atual: {z_inicial})")

    # Botão para alternar modo
    ax_btn_modo = fig.add_axes([0.02, 0.04, 0.18, 0.07])
    btn_modo = Button(ax_btn_modo, "Alternar Modo (mis=can)")


    def abrir_seletor_z(event):
        root = tk.Tk()
        root.title("Selecionar Capacidade Z")
        root.geometry("250x100")
        root.resizable(False, False)
        tk.Label(root, text="Escolha o valor de Z:").pack(pady=8)
        var = tk.StringVar(value=str(z_selecionado["valor"]))
        combo = ttk.Combobox(root, textvariable=var, values=[str(z) for z in valores_z], state="readonly")
        combo.pack(pady=4)
        def confirmar():
            z_sel = int(combo.get())
            z_selecionado["valor"] = z_sel
            btn_z.label.set_text(f"Selecionar Z (atual: {z_sel})")
            plot_filtrado(z_sel)
            root.destroy()
        btn_ok = tk.Button(root, text="OK", command=confirmar)
        btn_ok.pack(pady=4)
        root.mainloop()

    btn_z.on_clicked(abrir_seletor_z)

    def alternar_modo(event):
        if modo["valor"] == "miscan":
            modo["valor"] = "livre"
            btn_modo.label.set_text("Alternar Modo (livre)")
        else:
            modo["valor"] = "miscan"
            btn_modo.label.set_text("Alternar Modo (mis=can)")
        plot_filtrado(z_selecionado["valor"])

    btn_modo.on_clicked(alternar_modo)

    # Plot inicial
    plot_filtrado(z_inicial)
    plt.show()


def main():
    if not SCENARIOS_PATH.exists():
        print(f"❌ Arquivo não encontrado: {SCENARIOS_PATH}")
        print("💡 Rode primeiro o run_benchmarks.py para gerar dados.")
        return

    pontos = carregar_dados_validos(SCENARIOS_PATH)
    print(f"📊 Cenários válidos carregados: {len(pontos)}")
    plotar_cenarios(pontos)


if __name__ == "__main__":
    main()
