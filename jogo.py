import pygame
import random
from config import LARGURA, ALTURA
from assets import load_assets, ASTRONAUTA_IMG
from sprites import Astronauta

pygame.init()
clock = pygame.time.Clock()

#gera a tela principal com tela cheia
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('Joguinho')

assets = load_assets()

all_sprites = pygame.sprite.Group()

astronauta = Astronauta(all_sprites, assets)
all_sprites.add(astronauta)

game = True
while game:
    dt = clock.tick(30)  # limita a 60 FPS

    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.QUIT:
            game = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
                
            #colocar o jogo em tela cheia
            if event.key == pygame.K_F11:
                fullscreen = not pygame.display.get_surface().get_flags() & pygame.FULLSCREEN
                if fullscreen:
                    window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    window = pygame.display.set_mode((LARGURA, ALTURA))
            # Dependendo da tecla, altera a velocidade.
            if event.key == pygame.K_LEFT:
                astronauta.speedx = -10
            if event.key == pygame.K_RIGHT:
                astronauta.speedx = 10
            if event.key == pygame.K_SPACE:
                astronauta.pular()
            if event.key == pygame.K_DOWN:
                astronauta.agachar()

        # Verifica se soltou alguma tecla.
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT and astronauta.speedx < 0:
                astronauta.speedx = 0
            if event.key == pygame.K_RIGHT and astronauta.speedx > 0:
                astronauta.speedx = 0
            if event.key == pygame.K_DOWN:
                astronauta.levantar()

    # ---- Atualiza os sprites
    all_sprites.update(dt)

    window.fill((30, 30, 30))
    all_sprites.draw(window)
    pygame.display.flip()

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados