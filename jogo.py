import pygame
import random
from config import LARGURA, ALTURA
from assets import PLAYER_IMG

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
        
        if event.type == pygame.KEYDOWN:
            # Dependendo da tecla, altera a velocidade.
            if event.key == pygame.K_LEFT:
                PLAYER_IMG.speedx -= 4
            if event.key == pygame.K_RIGHT:
                PLAYER_IMG.speedx += 4
        # Verifica se soltou alguma tecla.
        if event.type == pygame.KEYUP:
            # Dependendo da tecla, altera a velocidade.
            if event.key == pygame.K_LEFT:
                PLAYER_IMG.speedx += 4
            if event.key == pygame.K_RIGHT:
                PLAYER_IMG.speedx -= 4

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados