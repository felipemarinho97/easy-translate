import numpy as np
from difflib import SequenceMatcher

def similaridade(str1, str2):
    # Usando SequenceMatcher para calcular similaridade
    return SequenceMatcher(None, str1, str2).ratio()

def align_lists(lista1, lista2):
    n = len(lista1)
    m = len(lista2)
    
    # Criar matriz de custos
    dp = np.zeros((n + 1, m + 1))
    
    # Preencher a matriz com os scores de similaridade
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = similaridade(lista1[i-1], lista2[j-1])
            dp[i][j] = max(dp[i-1][j-1] + sim, dp[i-1][j], dp[i][j-1])

    # exibir a matriz de DP
    if __name__ == "__main__":
        print("Matriz de DP:")
        for i in range(n + 1):
            for j in range(m + 1):
                print(f"{dp[i][j]:.2f}", end=" ")
            print()

    # Reconstruir o alinhamento a partir da matriz de DP
    i, j = n, m
    alinhamento1, alinhamento2 = [''] * n, [''] * n
    
    while i > 0 and j > 0:
        if dp[i][j] == dp[i-1][j-1] + similaridade(lista1[i-1], lista2[j-1]):
            alinhamento1[i-1] = lista1[i-1]
            alinhamento2[i-1] = lista2[j-1]
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i-1][j]:
            alinhamento1[i-1] = lista1[i-1]
            alinhamento2[i-1] = ''
            i -= 1
        else:
            j -= 1
    
    # Caso existam itens restantes na lista1 que não foram alinhados
    while i > 0:
        alinhamento1[i-1] = lista1[i-1]
        alinhamento2[i-1] = ''
        i -= 1
    
    return alinhamento1, alinhamento2

if __name__ == "__main__":
    # Exemplo de uso
    lista1 = [
        "But sometimes", "we need to be flexible when", "dealing with real situations.",
        "Flexible? How?", "Flexible...", "Just...", "You are asking me to teach you this?",
        "Forget it.", "Get back to work now.", "Mr. Seven. What's up?", "Have you sold your lousy restaurant yet?"
    ]

    lista2 = [
        "Mas às vezes", "precisamos ser flexíveis ao lidar com situações reais.",
        "Flexível? Como?", "Flexível...", "Bem...", "Você está me pedindo para me ensinar isso?",
        "Esqueça.", "Volte ao trabalho agora.", "Senhor Sete. O que está acontecendo?",
        "Você já vendeu seu restaurante de merda ainda?", "Quase!"
    ]

    alinhado1, alinhado2 = align_lists(lista1, lista2)

    for a, b in zip(alinhado1, alinhado2):
        print(f"{a} -> {b}")
