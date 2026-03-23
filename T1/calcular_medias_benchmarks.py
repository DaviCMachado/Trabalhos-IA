import json
import csv
from pathlib import Path

# Caminhos dos arquivos
JSON_PATH = Path(__file__).parent / 'scenarios.json'
CSV_PATH = Path(__file__).parent / 'medias_benchmarks.csv'

# Carrega o JSON
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    data = load_json(JSON_PATH)
    testes = data['testes']
    algs = ['bfs', 'bfs_otimizado']
    # Estruturas para médias gerais, por valor de Z e por balanceamento
    resultados_geral = {alg: {'tempo': [], 'memoria': [], 'visitados': []} for alg in algs}
    resultados_por_z = {}
    resultados_por_balanceio = {}

    def get_balanceio(x, y):
        if x == y:
            return 'balanceado'
        elif x > y:
            return 'mais_missionarios'
        else:
            return 'mais_canibais'

    for t in testes:
        # PULA OS CENÁRIOS QUE AINDA NÃO FORAM EXECUTADOS
        if 'out' not in t:
            continue
            
        x = t['in']['X']
        y = t['in']['Y']
        z = t['in']['Z']
        out = t['out']
        balanceio = get_balanceio(x, y)
        
        if z not in resultados_por_z:
            resultados_por_z[z] = {alg: {'tempo': [], 'memoria': [], 'visitados': []} for alg in algs}
        if balanceio not in resultados_por_balanceio:
            resultados_por_balanceio[balanceio] = {alg: {'tempo': [], 'memoria': [], 'visitados': []} for alg in algs}
            
        for alg in algs:
            # O 'if alg in out' também protege contra testes que foram "skipped" (pulados) no benchmark
            if alg in out:
                resultados_geral[alg]['tempo'].append(out[alg]['tempo_s'])
                resultados_geral[alg]['memoria'].append(out[alg]['memoria_kb'])
                resultados_geral[alg]['visitados'].append(out[alg]['visitados'])
                
                resultados_por_z[z][alg]['tempo'].append(out[alg]['tempo_s'])
                resultados_por_z[z][alg]['memoria'].append(out[alg]['memoria_kb'])
                resultados_por_z[z][alg]['visitados'].append(out[alg]['visitados'])
                
                resultados_por_balanceio[balanceio][alg]['tempo'].append(out[alg]['tempo_s'])
                resultados_por_balanceio[balanceio][alg]['memoria'].append(out[alg]['memoria_kb'])
                resultados_por_balanceio[balanceio][alg]['visitados'].append(out[alg]['visitados'])

    def calcular_medias(resultados, extra_col=None, extra_val=None):
        linhas = []
        for alg in algs:
            n = len(resultados[alg]['tempo'])
            if n == 0:
                continue
            tempo_medio = sum(resultados[alg]['tempo']) / n
            memoria_media = sum(resultados[alg]['memoria']) / n
            visitados_medio = sum(resultados[alg]['visitados']) / n
            row = {
                'algoritmo': alg,
                'tempo_medio_s': tempo_medio,
                'memoria_media_kb': memoria_media,
                'visitados_medio': visitados_medio
            }
            if extra_col and extra_val is not None:
                row[extra_col] = extra_val
            linhas.append(row)
        return linhas

    # Todas as médias
    medias = []
    # Médias gerais
    medias.extend(calcular_medias(resultados_geral))
    # Médias por capacidade de barco (Z)
    for z in sorted(resultados_por_z.keys()):
        medias.extend(calcular_medias(resultados_por_z[z], extra_col='capacidade_barco', extra_val=z))
    # Médias por balanceio
    for balanceio in ['balanceado', 'mais_missionarios', 'mais_canibais']:
        if balanceio in resultados_por_balanceio:
            medias.extend(calcular_medias(resultados_por_balanceio[balanceio], extra_col='balanceio', extra_val=balanceio))

    # Define campos do CSV
    fieldnames = ['algoritmo', 'tempo_medio_s', 'memoria_media_kb', 'visitados_medio', 'capacidade_barco', 'balanceio']
    # Salva CSV
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in medias:
            writer.writerow(row)
    print(f'Médias (geral, por Z e por balanceio) salvas em {CSV_PATH}')

if __name__ == '__main__':
    main()