# ===== Inicialização =====
# ----- Importa e inicia pacotes
import pygame
import random
import pygame
import os
from config import LARGURA, ALTURA
from assets import load_assets, ASTRONAUTA_IMG

pygame.init()

# ----- Gera tela principal
WIDTH = 1000
HEIGHT = 800
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Jogo Faroeste')

#assets
fundo = os.path.join('assets', 'img', 'faroeste.png')

# Carrega a imagem do background (não sobrescrever window)
fundo_image = pygame.image.load(fundo).convert()  # use convert_alpha() se houver transparência
fundo_width, fundo_height = fundo_image.get_width(), fundo_image.get_height()
# ----- Inicia estruturas de dados
game = True

# ===== Loop principal =====
while game:
    # ----- Trata eventos
    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.KEYUP:
            game = False

    # ----- Gera saídas
    window.fill((0, 0, 0))  # Preenche com a cor branca
    window.blit(fundo_image, (0,0))
    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados

