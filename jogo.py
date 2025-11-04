import pygame
import random
from config import LARGURA, ALTURA
from assets import load_assets, PLAYER_IMG
from sprites import Jogador

pygame.init()
clock = pygame.time.Clock()

#gera a tela principal
window = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption('Joguinho')

assets = load_assets()

all_sprites = pygame.sprite.Group()

player = Jogador(all_sprites, assets)
all_sprites.add(player)

game = True
while game:
    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.QUIT:
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
    # ---- Atualizad os sprites
    all_sprites.update()

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados