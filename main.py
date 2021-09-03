import copy
import random
import math
import time
import concurrent.futures
from datetime import timedelta

tamanho_tabuleiro = 8
inicial_x = 5
inicial_y = 5
iteracoes_simulated = 200  # 50
iteracoes_ils = 1000  # 100
valor_temperatura = 0.1
avaliacao_maxima = 64


def pega_posicao_pulo(x_atual: int, y_atual: int, movimento: int):
    x_destino = 0
    y_destino = 0
    if movimento == 0:
        x_destino = x_atual + 1
        y_destino = y_atual + 2
    elif movimento == 1:
        x_destino = x_atual + 2
        y_destino = y_atual + 1
    elif movimento == 2:
        x_destino = x_atual + 2
        y_destino = y_atual - 1
    elif movimento == 3:
        x_destino = x_atual + 1
        y_destino = y_atual - 2
    elif movimento == 4:
        x_destino = x_atual - 1
        y_destino = y_atual - 2
    elif movimento == 5:
        x_destino = x_atual - 2
        y_destino = y_atual - 1
    elif movimento == 6:
        x_destino = x_atual - 2
        y_destino = y_atual + 1
    elif movimento == 2:
        x_destino = x_atual - 1
        y_destino = y_atual + 2
    return x_destino, y_destino


def posicao_valida(x: int, y: int, matriz_avaliacao):
    if 0 <= x < tamanho_tabuleiro:
        if 0 <= y < tamanho_tabuleiro:
            if matriz_avaliacao[x][y] == 0:  # Se ainda não foi  visitado, valido
                return 1
    return 0


# Avalia a solucao atual, retornando um score de 0 a tamanho_tabuleiro*tamanho_tabuleiro
# indicando quantos pulos no total foram corretos
# Cria-se uma matriz que guarda quantas vezes uma casa foi visitada.
# Se a casa foi visitada exatamente uma vez, +1 no score se não for a casa final
# Se for a casa final, verificar antes se é o último movimento
def avalia_solucao(solucao: []):
    x = inicial_x
    y = inicial_y
    resultado_avaliacao = 0
    matriz_avaliacao = [[0 for x in range(tamanho_tabuleiro)] for y in range(tamanho_tabuleiro)]
    for index in range(len(solucao)):
        x_destino, y_destino = pega_posicao_pulo(x, y, solucao[index])
        if posicao_valida(x_destino, y_destino, matriz_avaliacao):
            resultado_avaliacao = resultado_avaliacao + 1
            x = x_destino
            y = y_destino
            matriz_avaliacao[x][y] = matriz_avaliacao[x][y] + 1
    return resultado_avaliacao


# Criação aleatória de solucao
def cria_solucao_inicial():
    solucao_inicial = [random.randint(0, 7) for x in range(tamanho_tabuleiro * tamanho_tabuleiro)]
    return solucao_inicial


def altera_aleatorio(solucao: []):
    copia = copy.deepcopy(solucao)
    index = random.randint(0, len(copia) - 1)
    copia[index] = random.randint(0, 7)
    return copia


# Executa a busca local do ILS. Simulated Annealing
def simulated_annealing(resposta_atual: []):
    melhor_global = copy.deepcopy(resposta_atual)
    melhor_avaliacao = avalia_solucao(melhor_global)
    for i in range(iteracoes_simulated):
        melhor_local = altera_aleatorio(melhor_global)
        avaliacao_local = avalia_solucao(melhor_local)
        if avaliacao_local > melhor_avaliacao:
            melhor_global = melhor_local
            melhor_avaliacao = avaliacao_local
        else:
            diferenca_avaliacao = melhor_avaliacao - avaliacao_local
            temp = valor_temperatura / float(i + 1)
            trocar_pior = math.exp(-diferenca_avaliacao/temp)
            if random.randint(0, 1) < trocar_pior:
                melhor_global = melhor_local
                melhor_avaliacao = avaliacao_local
    return melhor_global


# Rola um dado. Se der 6, muda o pulo para um aleatório.
def perturbacao(resposta_atual: [], avaliacao):
    if avaliacao == avaliacao_maxima:
        return resposta_atual
    resposta = copy.deepcopy(resposta_atual)
    for index in range(len(resposta)):
        rola_dado = random.randint(1, 5)
        if rola_dado > 5:
            resposta[index] = random.randint(0, 7)
    return resposta


def executa_ils(resposta_atual: []):
    melhor_global = copy.deepcopy(resposta_atual)
    melhor_global = simulated_annealing(melhor_global)
    avaliacao_global = avalia_solucao(melhor_global)
    iteracoes = 0
    while iteracoes < iteracoes_ils:
        melhor_local = perturbacao(melhor_global, avaliacao_global)
        melhor_local = simulated_annealing(melhor_local)
        avaliacao_iteracao = avalia_solucao(melhor_local)
        if avaliacao_iteracao > avaliacao_global:
            melhor_global = melhor_local
            avaliacao_global = avaliacao_iteracao
        iteracoes = iteracoes + 1

    return melhor_global


def avalia_populacao(populacao):
    avaliacoes = []
    for j in range(len(populacao)):
        avaliacoes.append(avalia_solucao(populacao[j]))
    return avaliacoes


def altera_cromossomo(cromossomo, qtd_genes_mutaveis):
    indices = random.sample(range(0, len(cromossomo) - 1), qtd_genes_mutaveis)
    for indice in indices:
        novo_movimento = random.randint(0, 7)
        cromossomo[indice] = novo_movimento


def mutacao_populacao(populacao, avaliacoes, taxa_mutacao, qtd_genes_mutaveis):
    for i in range(taxa_mutacao):
        individuos_escolhidos = random.sample(range(0, len(populacao) - 1), taxa_mutacao)
        for j in range(qtd_genes_mutaveis):
            cromossomo_atual = populacao[individuos_escolhidos[j]]
            if avaliacoes[j] != avaliacao_maxima:
                altera_cromossomo(cromossomo_atual, qtd_genes_mutaveis)


# Escolhe n melhores individuos para reproduzir
def escolher_populacao(populacao_atual, avaliacoes, n_reproducoes):
    populacao = []
    avaliacoes_escolhidas = []
    indices_ordenados = sorted(range(len(avaliacoes)), key=avaliacoes.__getitem__)
    indices_ordenados.reverse()
    for i in range(min(n_reproducoes, len(indices_ordenados))):
        populacao.append(populacao_atual[indices_ordenados[i]])
        avaliacoes_escolhidas.append(avaliacoes[indices_ordenados[i]])

    return populacao, avaliacoes_escolhidas


# https://stackoverflow.com/questions/10324015/fitness-proportionate-selection-roulette-wheel-selection-in-python
def weighted_random_choice(populacao, choices):
    max_val = sum(choices.values())
    pick = random.uniform(0, max_val)
    current = 0
    for key, value in choices.items():
        current += value
        if current > pick:
            return populacao[key]


def crossover(cromossomo_a, cromossomo_b):
    ponto_corte = random.randint(0, avaliacao_maxima - 1)
    novo_cromossomo = []
    for i in range(0, ponto_corte):
        novo_cromossomo.append(cromossomo_a[i])

    for i in range(ponto_corte, avaliacao_maxima - 1):
        novo_cromossomo.append(cromossomo_b[i])

    return novo_cromossomo


def reproducoes(populacao, avaliacoes):
    nova_populacao = copy.deepcopy(populacao)

    dicionario_fitness = {}
    for i in range(len(populacao)):
        dicionario_fitness[i] = avaliacoes[i]

    for i in range(len(populacao)):
        cromossomo_a = weighted_random_choice(populacao, dicionario_fitness)
        cromossomo_b = weighted_random_choice(populacao, dicionario_fitness)
        nova_populacao.append(crossover(cromossomo_a, cromossomo_b))
    return nova_populacao


def pega_melhor_avaliacao(populacao):
    avaliacao = avalia_populacao(populacao)
    maior_valor = 0
    indice = 0
    for i in range(len(avaliacao)):
        aval = avaliacao[i]
        if aval > maior_valor:
            maior_valor = aval
            indice = i
    return maior_valor, populacao[indice]


def algoritmo_genetico(tam_populacao, n_reproducoes, taxa_mutacao, qtd_genes_mutaveis, iteracoes, executar_local):
    populacao = [cria_solucao_inicial() for i in range(tam_populacao)]

    melhor_individuo = []
    maior_valor_global = 0

    for itrs in range(iteracoes):
        avaliacao_rodada = avalia_populacao(populacao)
        mutacao_populacao(populacao, avaliacao_rodada, taxa_mutacao, qtd_genes_mutaveis)
        populacao_escolhida, avaliacao_escolhidos = \
            escolher_populacao(populacao, avalia_populacao(populacao), n_reproducoes)
        populacao = reproducoes(populacao_escolhida, avaliacao_escolhidos)

        # for indivs in range(len(populacao_escolhida)):
        #    populacao.remove(populacao_escolhida[indivs])

        maior_valor, individuo = pega_melhor_avaliacao(populacao)
        if maior_valor == avaliacao_maxima:
            maior_valor_global = maior_valor
            melhor_individuo = individuo
            break
        if executar_local == 1 and (itrs + 1) % iteracoes/2 == 0:
            print("Começando ILS. Como estava antes: " + str(maior_valor_global) + " Tam_populacao: " + str(len(populacao)))
            populacao_local = []
            if populacao.__contains__(melhor_individuo) == 0:  # Colocar o melhor individuo na populacao caso ele não esteja lá.
                populacao_local.append(copy.deepcopy(melhor_individuo))
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_populaco = {executor.submit(executa_ils, populacao[index_indv]): index_indv for index_indv in
                                   range(len(populacao))}
                for future in concurrent.futures.as_completed(future_populaco):
                    populacao_local.append(future.result())
            populacao = populacao_local

        maior_valor, individuo = pega_melhor_avaliacao(populacao)

        if maior_valor == avaliacao_maxima:
            maior_valor_global = maior_valor
            melhor_individuo = individuo
            break
        elif maior_valor_global < maior_valor:
            maior_valor_global = maior_valor
            melhor_individuo = copy.deepcopy(individuo)
        if (itrs + 1) % iteracoes/2 == 0:
            print("Iteracoes: " + str(itrs + 1) + " . Melhor atual: " + str(maior_valor_global))

    return melhor_individuo, maior_valor_global


def passeio_cavalo(populacao: int, n_reproducoes: int, taxa_mutacao: int, qtd_genes_mutaveis: int,
                   iteracoes: int, executar_local):
    tempo_inicio = time.time()
    try:
        if populacao < taxa_mutacao:
            raise ValueError("Mais individuos para fazer mutacao do que tem gente!")
    except ValueError:
        exit("Populacao menor que taxa de mutacao invalida exception")

    try:
        if populacao < taxa_mutacao:
            raise ValueError("Mais individuos para fazer mutacao do que tem gente!")
    except ValueError:
        exit("Populacao menor que taxa de mutacao invalida exception")

    resposta, avaliacao = algoritmo_genetico(tam_populacao=populacao, n_reproducoes=n_reproducoes,
                                             taxa_mutacao=taxa_mutacao, qtd_genes_mutaveis=qtd_genes_mutaveis,
                                             iteracoes=iteracoes, executar_local=executar_local)

    print("Avaliacao final: " + str(avaliacao))
    print(str(resposta))
    tempo_fim = time.time()
    duracao = tempo_fim - tempo_inicio
    print("Duracao: " + str(timedelta(seconds=duracao)))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    for i in range(10):
        print("Rodada " + str(i))
        passeio_cavalo(populacao=50, n_reproducoes=30, taxa_mutacao=15, qtd_genes_mutaveis=1,
                       iteracoes=1000, executar_local=1)
        # passeio_cavalo(populacao=300, n_reproducoes=285, taxa_mutacao=220, qtd_genes_mutaveis=1,
        #               iteracoes=500, executar_local=1)