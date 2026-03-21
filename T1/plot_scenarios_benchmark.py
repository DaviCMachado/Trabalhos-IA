import json
from pathlib import Path

import matplotlib.pyplot as plt


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

    labels = [f"{p['X']},{p['Y']},{p['Z']}" for p in pontos]
    eixo_x = list(range(len(pontos)))

    tempo_bfs = [p["tempo_bfs"] for p in pontos]
    tempo_opt = [p["tempo_opt"] for p in pontos]
    mem_bfs = [p["mem_bfs"] for p in pontos]
    mem_opt = [p["mem_opt"] for p in pontos]

    plt.style.use("seaborn-v0_8-darkgrid")
    fig, ax_tempo = plt.subplots(figsize=(16, 8))
    ax_mem = ax_tempo.twinx()

    linha_tempo_bfs, = ax_tempo.plot(
        eixo_x,
        tempo_bfs,
        marker="o",
        linewidth=2,
        color="#1f77b4",
        label="Tempo BFS (s)",
    )
    linha_tempo_opt, = ax_tempo.plot(
        eixo_x,
        tempo_opt,
        marker="o",
        linewidth=2,
        color="#ff7f0e",
        label="Tempo BFS Otimizado (s)",
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
    linha_mem_opt, = ax_mem.plot(
        eixo_x,
        mem_opt,
        marker="s",
        linewidth=2,
        linestyle="--",
        color="#ff7f0e",
        label="Memória BFS Otimizado (KB)",
    )

    ax_tempo.set_xlabel("Cenários (X,Y,Z) em ordem crescente", fontsize=11)
    ax_tempo.set_ylabel("Tempo de Execução (s)", fontsize=11, color="#1f77b4")
    ax_mem.set_ylabel("Uso de Memória (KB)", fontsize=11, color="#2ca02c")

    ax_tempo.set_xticks(eixo_x)
    ax_tempo.set_xticklabels(labels, rotation=60, ha="right", fontsize=9)

    fig.suptitle(
        "Comparação BFS vs BFS Otimizado por Cenário\n"
        "(4 linhas: tempo BFS, tempo otimizado, memória BFS, memória otimizado)",
        fontsize=14,
        fontweight="bold",
    )

    linhas = [linha_tempo_bfs, linha_tempo_opt, linha_mem_bfs, linha_mem_opt]
    labels_legenda = [l.get_label() for l in linhas]
    ax_tempo.legend(linhas, labels_legenda, loc="upper left", framealpha=0.95)

    plt.tight_layout()
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
