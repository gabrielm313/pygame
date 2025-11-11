import pygame
import os
from config import IMG_DIR , PLAYER_LARG , PLAYER_ALTU 

ASTRONAUTA_IMG = 'astronauta1'
FUNDO_IMG = 'fundo_pg'
ALIEN_IMG = 'et'
OVNI_IMG = 'nave alienigena'
ENEMY_LASER_IMG = 'laser'

def load_assets():
    assets = {}

    #para adicionar a imagem do player foi utilizado chatgpt
    ast_path = os.path.join(IMG_DIR, 'astronauta1.png') 
    astronauta1= pygame.image.load(ast_path).convert_alpha()

    assets[ALIEN_IMG] = pygame.image.load(os.path.join(IMG_DIR, 'et.png')).convert_alpha()
    assets[OVNI_IMG] = pygame.image.load(os.path.join(IMG_DIR, 'nave alienigena.png')).convert_alpha()
    assets[ENEMY_LASER_IMG] = pygame.image.load(os.path.join(IMG_DIR, 'laser.jpg')).convert_alpha()

    fundo_path = os.path.join(IMG_DIR, 'fundo_pg.png') 
    fundo_pygame= pygame.image.load(fundo_path)
    assets[FUNDO_IMG] = fundo_pygame
    assets[ASTRONAUTA_IMG] = pygame.image.load(os.path.join(IMG_DIR, 'astronauta1.png')).convert_alpha()
    
    return assets

    