import json
import os
import time
from datetime import datetime
from pathlib import Path

from node import Node
from search_engine import SearchEngine

BASE_DIR = Path(__file__).parent
SCENARIOS_PATH = BASE_DIR / "scenarios.json"
PASTA_DADOS = BASE_DIR / "data"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)


def cenario_tem_solucao(x, y, z):
    """Filtro matemático conservador para evitar cenários sem solução."""
    if x < 0 or y < 0 or z <= 0:
        return False

    if y > x and x > 0:
        return False

    if x == 0 and y == 0:
        return True

    if z == 1:
        return False

    if x == y:
        if z == 2:
            return x <= 3
        if z == 3:
            return x <= 5
        return z >= 4

    # Regra conservadora para casos não simétricos:
    # exige barco grande o bastante para manter margem segura.
    return z >= 3


def escolher_z_soluvel(n):
    """Escolhe Z mínimo conhecido como solucionável para X=Y=n."""
    if n <= 3:
        return 2
    if n <= 5:
        return 3
    return 4


def gerar_cenarios_expandidos(max_x=1000):
    """Gera cenários escaláveis (X=Y) até max_x evitando casos sem solução."""
    valores = [
        1, 2, 3, 4, 5, 6, 8, 10,
        15, 20, 30, 40, 50, 75, 100,
        150, 200, 300, 400, 500, 750, 1000,
    ]
    valores = [v for v in valores if v <= max_x]

    testes = []
    for n in valores:
        z = escolher_z_soluvel(n)
        if cenario_tem_solucao(n, n, z):
            testes.append({"in": {"X": n, "Y": n, "Z": z}})

    return testes


def executar_algoritmo(x, y, z, algoritmo):
    engine = SearchEngine(x, y, z, pasta_dados=PASTA_DADOS)
    raiz = Node(x, y, "esquerda")
    objetivo = (0, 0, "direita")

    if algoritmo == "bfs":
        return engine.bfs(raiz, objetivo)
    return engine.bfs_memory_optimized(raiz, objetivo)


def garantir_grafo_salvo(x, y, z):
    """Gera (ou reutiliza) o grafo do cenário para análise/visualização."""
    arquivo_grafo = PASTA_DADOS / f"grafo_{x}x{y}_z{z}.pkl"
    forcar_regeneracao = os.getenv("BENCHMARK_FORCE_REGENERATE", "0") == "1"

    if arquivo_grafo.exists() and not forcar_regeneracao:
        return arquivo_grafo, "reutilizado"

    engine_gerador = SearchEngine(
        x,
        y,
        z,
        pasta_dados=PASTA_DADOS,
        arquivo_grafo=arquivo_grafo,
    )
    raiz_geracao = Node(x, y, "esquerda")
    engine_gerador.gerar_e_salvar_grafo(raiz_geracao)
    return arquivo_grafo, "gerado"


def benchmark_cenario(idx, entrada):
    x = entrada["X"]
    y = entrada["Y"]
    z = entrada["Z"]

    print("\n" + "=" * 72)
    print(f"🧪 TESTE #{idx + 1} | X={x} | Y={y} | Z={z}")
    print("=" * 72)

    arquivo_grafo, status_grafo = garantir_grafo_salvo(x, y, z)
    print(f"🗂️  Grafo {status_grafo}: {arquivo_grafo.name}")

    inicio = time.perf_counter()
    res_bfs = executar_algoritmo(x, y, z, "bfs")
    res_opt = executar_algoritmo(x, y, z, "bfs_otimizado")
    fim = time.perf_counter()

    print(
        f"BFS: sucesso={res_bfs['sucesso']} | tempo={res_bfs['tempo']:.6f}s | "
        f"mem={res_bfs['memoria']:.2f}KB | visitados={res_bfs['visitados']}"
    )
    print(
        f"OPT: sucesso={res_opt['sucesso']} | tempo={res_opt['tempo']:.6f}s | "
        f"mem={res_opt['memoria']:.2f}KB | visitados={res_opt['visitados']}"
    )

    return {
        "grafo": {
            "arquivo": str(arquivo_grafo),
            "status": status_grafo,
        },
        "bfs": {
            "sucesso": res_bfs["sucesso"],
            "tempo_s": round(res_bfs["tempo"], 8),
            "memoria_kb": round(res_bfs["memoria"], 4),
            "visitados": res_bfs["visitados"],
        },
        "bfs_otimizado": {
            "sucesso": res_opt["sucesso"],
            "tempo_s": round(res_opt["tempo"], 8),
            "memoria_kb": round(res_opt["memoria"], 4),
            "visitados": res_opt["visitados"],
        },
        "tempo_total_cenario_s": round(fim - inicio, 8),
        "executado_em": datetime.now().isoformat(timespec="seconds"),
    }


def salvar_json(testes, max_x_execucao):
    payload = {
        "meta": {
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "descricao": "Benchmarks BFS vs BFS otimizado para missionários e canibais",
            "max_x_execucao": max_x_execucao,
        },
        "testes": testes,
    }

    with open(SCENARIOS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    max_x_execucao = int(os.getenv("BENCHMARK_MAX_X", "200"))
    max_x_catalogo = 1000

    print(f"🚀 Gerando cenários até X={max_x_catalogo} (execução prática até X={max_x_execucao})")
    testes = gerar_cenarios_expandidos(max_x=max_x_catalogo)

    total = len(testes)
    executados = 0
    pulados = 0
    inicio_total = time.perf_counter()

    for idx, teste in enumerate(testes):
        entrada = teste["in"]
        x = entrada["X"]

        if x > max_x_execucao:
            teste["out"] = {
                "status": "skipped",
                "motivo": f"X={x} acima do limite BENCHMARK_MAX_X={max_x_execucao}",
                "executado_em": datetime.now().isoformat(timespec="seconds"),
            }
            pulados += 1
            continue

        if not cenario_tem_solucao(entrada["X"], entrada["Y"], entrada["Z"]):
            teste["out"] = {
                "status": "skipped",
                "motivo": "Cenário filtrado como sem solução",
                "executado_em": datetime.now().isoformat(timespec="seconds"),
            }
            pulados += 1
            continue

        teste["out"] = benchmark_cenario(idx, entrada)
        teste["out"]["status"] = "ok"
        executados += 1

        # Salva incrementalmente para não perder progresso em execuções longas
        salvar_json(testes, max_x_execucao)

    fim_total = time.perf_counter()
    salvar_json(testes, max_x_execucao)

    print("\n" + "=" * 72)
    print("📊 RESUMO FINAL")
    print("=" * 72)
    print(f"Total de cenários gerados: {total}")
    print(f"Executados: {executados}")
    print(f"Pulados: {pulados}")
    print(f"Tempo total: {fim_total - inicio_total:.3f}s")
    print(f"Arquivo atualizado: {SCENARIOS_PATH}")


if __name__ == "__main__":
    main()
