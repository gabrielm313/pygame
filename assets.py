import pygame
import os
from config import IMG_DIR

PLAYER_IMG = 'player_img'

def load_assets():
    assets = {}
    #para adicionar a imagem do player foi utilizado chatgpt
    player_path = os.path.join(IMG_DIR, 'player.png') 
    assets[PLAYER_IMG] = pygame.image.load(player_path).convert_alpha()

    return assets

    