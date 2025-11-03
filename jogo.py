import pygame
import random
from config import LARGURA, ALTURA

pygame.init()

#gera a tela principal
window = pygame.display.set_mode((LARGURA, ALTURA))

game = True
while game:
    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.KEYUP:
            game = False

    # ----- Gera saídas
    window.fill((0, 0, 255))  # Preenche com a cor branca

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados

