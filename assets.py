# assets.py
import pygame
import os
from config import IMG_DIR, PLAYER_LARG, PLAYER_ALTU

ALIEN_LARG = 300
ALIEN_ALTU = 300
OVNI_LARG = 300
OVNI_ALTU = 300

ASTRONAUTA_IMG = 'astronauta1'
FUNDO_IMG = 'fundo_pg'
ALIEN_IMG = 'et'
OVNI_IMG = 'nave alienigena'
ENEMY_LASER_IMG = 'laser'

def load_assets():
    assets = {}

    def load_and_scale(name, w, h):
        full_path = os.path.join(IMG_DIR, f'{name}.png')
        if not os.path.exists(full_path):
            # cria superfície de debug quando imagem não existe
            img = pygame.Surface((w, h), pygame.SRCALPHA)
            img.fill((255, 0, 255))
            return img
        img = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.scale(img, (w, h))

    assets[ASTRONAUTA_IMG] = load_and_scale('astronauta1', PLAYER_LARG, PLAYER_ALTU)
    assets[ALIEN_IMG] = load_and_scale('et', ALIEN_LARG, ALIEN_ALTU)
    assets[OVNI_IMG] = load_and_scale('nave alienigena', OVNI_LARG, OVNI_ALTU)

    # laser — tenta carregar .jpg ou .png (prioriza jpg)
    laser_path_jpg = os.path.join(IMG_DIR, 'laser.jpg')
    laser_path_png = os.path.join(IMG_DIR, 'laser.png')
    if os.path.exists(laser_path_jpg):
        laser_img = pygame.image.load(laser_path_jpg).convert_alpha()
    elif os.path.exists(laser_path_png):
        laser_img = pygame.image.load(laser_path_png).convert_alpha()
    else:
        laser_img = pygame.Surface((20, 40), pygame.SRCALPHA)
        laser_img.fill((255, 0, 0))
    assets[ENEMY_LASER_IMG] = pygame.transform.scale(laser_img, (20, 40))

    # fundo
    fundo_path = os.path.join(IMG_DIR, 'fundo_pg.png')
    if os.path.exists(fundo_path):
        assets[FUNDO_IMG] = pygame.image.load(fundo_path).convert_alpha()
    else:
        assets[FUNDO_IMG] = pygame.Surface((1920, 1080)).convert_alpha()
        assets[FUNDO_IMG].fill((0, 0, 0))

    return assets
