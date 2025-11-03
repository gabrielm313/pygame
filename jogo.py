import pygame
import random
from config import LARGURA, ALTURA

pygame.init()

#gera a tela principal
window = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Joguinho')

game = True
while game:
    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.KEYUP:
            game = False

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados