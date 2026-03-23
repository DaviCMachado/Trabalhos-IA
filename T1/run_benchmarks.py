import json
import os
import time
import gc
import statistics
import csv
from datetime import datetime
from pathlib import Path

from node import Node
from search_engine import SearchEngine

BASE_DIR = Path(__file__).parent
SCENARIOS_PATH = BASE_DIR / "scenarios.json"
SCENARIOS_CSV_PATH = BASE_DIR / "scenarios.csv"
PASTA_DADOS = BASE_DIR / "data"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)


def medir_tempos_justos(executar_normal, executar_otimizado, rodadas=8, aquecimento=2):
    """Compara tempos com aquecimento e ordem alternada para reduzir viés."""
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
            resultado = fn()
            if nome == "normal":
                tempos_normal.append(resultado["tempo"])
            else:
                tempos_otimizado.append(resultado["tempo"])

    media_normal = sum(tempos_normal) / len(tempos_normal) if tempos_normal else 0.0
    media_otimizado = sum(tempos_otimizado) / len(tempos_otimizado) if tempos_otimizado else 0.0

    mediana_normal = statistics.median(tempos_normal) if tempos_normal else 0.0
    mediana_otimizado = statistics.median(tempos_otimizado) if tempos_otimizado else 0.0

    desvio_normal = statistics.stdev(tempos_normal) if len(tempos_normal) > 1 else 0.0
    desvio_otimizado = statistics.stdev(tempos_otimizado) if len(tempos_otimizado) > 1 else 0.0

    return {
        "normal": {
            "media": media_normal,
            "mediana": mediana_normal,
            "desvio": desvio_normal,
            "amostras": len(tempos_normal),
        },
        "otimizado": {
            "media": media_otimizado,
            "mediana": mediana_otimizado,
            "desvio": desvio_otimizado,
            "amostras": len(tempos_otimizado),
        },
    }


def carregar_cenarios_csv(caminho_csv):
    """Carrega cenários de scenarios.csv com colunas: missionarios,canibais,cap_barco."""
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv}")

    testes = []
    with open(caminho_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for numero_linha, row in enumerate(reader, start=1):
            if not row:
                continue

            campos = [c.strip() for c in row]
            if not any(campos):
                continue

            primeiro = campos[0].lower()
            if primeiro.startswith("#"):
                continue

            if len(campos) < 3:
                print(f"⚠️  Linha {numero_linha} ignorada (esperado 3 colunas): {row}")
                continue

            try:
                x = int(campos[0])
                y = int(campos[1])
                z = int(campos[2])
            except ValueError:
                if numero_linha == 1:
                    # Permite cabeçalho textual na primeira linha.
                    continue
                print(f"⚠️  Linha {numero_linha} ignorada (valores inválidos): {row}")
                continue

            if x < 0 or y < 0 or z <= 0:
                print(f"⚠️  Linha {numero_linha} ignorada (X>=0, Y>=0 e Z>0): {row}")
                continue

            testes.append({"in": {"X": x, "Y": y, "Z": z}})

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

    rodadas_tempo = int(os.getenv("BENCHMARK_TIME_RODADAS", "8"))
    aquecimento_tempo = int(os.getenv("BENCHMARK_TIME_AQUECIMENTO", "2"))

    inicio = time.perf_counter()
    res_bfs = executar_algoritmo(x, y, z, "bfs")
    res_opt = executar_algoritmo(x, y, z, "bfs_otimizado")

    def _exec_bfs_tempo():
        return executar_algoritmo(x, y, z, "bfs")

    def _exec_opt_tempo():
        return executar_algoritmo(x, y, z, "bfs_otimizado")

    metricas_tempo = medir_tempos_justos(
        _exec_bfs_tempo,
        _exec_opt_tempo,
        rodadas=rodadas_tempo,
        aquecimento=aquecimento_tempo,
    )
    tempo_bfs_medio = metricas_tempo["normal"]["media"]
    tempo_opt_medio = metricas_tempo["otimizado"]["media"]
    fim = time.perf_counter()

    print(
        f"BFS: sucesso={res_bfs['sucesso']} | tempo_medio={tempo_bfs_medio:.6f}s | "
        f"mediana={metricas_tempo['normal']['mediana']:.6f}s | desvio={metricas_tempo['normal']['desvio']:.6f}s | "
        f"mem={res_bfs['memoria']:.2f}KB | visitados={res_bfs['visitados']}"
    )
    print(
        f"OPT: sucesso={res_opt['sucesso']} | tempo_medio={tempo_opt_medio:.6f}s | "
        f"mediana={metricas_tempo['otimizado']['mediana']:.6f}s | desvio={metricas_tempo['otimizado']['desvio']:.6f}s | "
        f"mem={res_opt['memoria']:.2f}KB | visitados={res_opt['visitados']}"
    )

    return {
        "grafo": {
            "arquivo": str(arquivo_grafo),
            "status": status_grafo,
        },
        "bfs": {
            "sucesso": res_bfs["sucesso"],
            "tempo_s": round(tempo_bfs_medio, 8),
            "tempo_mediana_s": round(metricas_tempo["normal"]["mediana"], 8),
            "tempo_desvio_s": round(metricas_tempo["normal"]["desvio"], 8),
            "memoria_kb": round(res_bfs["memoria"], 4),
            "visitados": res_bfs["visitados"],
        },
        "bfs_otimizado": {
            "sucesso": res_opt["sucesso"],
            "tempo_s": round(tempo_opt_medio, 8),
            "tempo_mediana_s": round(metricas_tempo["otimizado"]["mediana"], 8),
            "tempo_desvio_s": round(metricas_tempo["otimizado"]["desvio"], 8),
            "memoria_kb": round(res_opt["memoria"], 4),
            "visitados": res_opt["visitados"],
        },
        "benchmark_tempo": {
            "rodadas": rodadas_tempo,
            "aquecimento": aquecimento_tempo,
            "ordem": "alternada",
        },
        "tempo_total_cenario_s": round(fim - inicio, 8),
        "executado_em": datetime.now().isoformat(timespec="seconds"),
    }


def salvar_json(testes, max_x_execucao):
    payload = {
        "meta": {
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "descricao": "Benchmarks BFS vs BFS otimizado para missionários e canibais",
            "origem_cenarios": str(SCENARIOS_CSV_PATH),
            "max_x_execucao": max_x_execucao,
        },
        "testes": testes,
    }

    with open(SCENARIOS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    max_x_execucao_env = os.getenv("BENCHMARK_MAX_X")
    max_x_execucao = int(max_x_execucao_env) if max_x_execucao_env else None

    print(f"🚀 Carregando cenários de {SCENARIOS_CSV_PATH.name}")
    try:
        testes = carregar_cenarios_csv(SCENARIOS_CSV_PATH)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Crie o arquivo scenarios.csv com linhas no formato: missionarios,canibais,cap_barco")
        return

    if not testes:
        print("❌ Nenhum cenário válido encontrado no CSV.")
        print("💡 Exemplo de linha: 100,100,4")
        return

    if max_x_execucao is None:
        print(f"📋 Cenários carregados: {len(testes)} (sem limite de X)")
    else:
        print(f"📋 Cenários carregados: {len(testes)} (limite de execução X<={max_x_execucao})")

    total = len(testes)
    executados = 0
    pulados = 0
    inicio_total = time.perf_counter()

    for idx, teste in enumerate(testes):
        entrada = teste["in"]
        x = entrada["X"]

        if max_x_execucao is not None and x > max_x_execucao:
            teste["out"] = {
                "status": "skipped",
                "motivo": f"X={x} acima do limite BENCHMARK_MAX_X={max_x_execucao}",
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
