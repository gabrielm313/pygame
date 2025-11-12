# assets.py
import pygame
import os
from config import IMG_DIR, PLAYER_LARG, PLAYER_ALTU

# nomes das chaves (use esses nomes no sprites/jogo)
ASTRONAUTA_IMG = 'astronauta1'
FUNDO_IMG = 'fundo_pg'
ALIEN_IMG = 'et'
OVNI_IMG = 'nave alienigena'
ENEMY_LASER_IMG = 'laser'

# tamanhos padrão (ajuste se quiser)b  
ALIEN_LARG = 250
ALIEN_ALTU = 250
OVNI_LARG = 300
OVNI_ALTU = 200

def load_assets():
    pygame.display.get_surface()  # garante init se necessário (não faz try/except)
    assets = {}

    def load_and_scale(name, w, h):
        full_path = os.path.join(IMG_DIR, f'{name}.png')
        if not os.path.exists(full_path):
            # cria uma superfície temporária visível para debug
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((255, 0, 255))
            return surf
        img = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.scale(img, (w, h))

    # astronauta (usa dimensões do config)
    assets[ASTRONAUTA_IMG] = load_and_scale('astronauta1', PLAYER_LARG, PLAYER_ALTU)

    # inimigos
    assets[ALIEN_IMG] = load_and_scale('et', ALIEN_LARG, ALIEN_ALTU)
    assets[OVNI_IMG] = load_and_scale('nave alienigena', OVNI_LARG, OVNI_ALTU)

    # laser inimigo (pode ser .jpg ou .png - tente png primeiro)
    laser_path_png = os.path.join(IMG_DIR, 'laser.png')
    laser_path_jpg = os.path.join(IMG_DIR, 'laser.jpg')
    if os.path.exists(laser_path_png):
        laser_img = pygame.image.load(laser_path_png).convert_alpha()
    elif os.path.exists(laser_path_jpg):
        laser_img = pygame.image.load(laser_path_jpg).convert_alpha()
    else:
        laser_img = pygame.Surface((20, 40), pygame.SRCALPHA)
        laser_img.fill((255, 0, 0))
    assets[ENEMY_LASER_IMG] = pygame.transform.scale(laser_img, (20, 40))

    # fundo (se existir)
    fundo_path = os.path.join(IMG_DIR, 'fundo_pg.png')
    if os.path.exists(fundo_path):
        assets[FUNDO_IMG] = pygame.image.load(fundo_path).convert_alpha()
    else:
        assets[FUNDO_IMG] = pygame.Surface((1920, 1080)).convert_alpha()
        assets[FUNDO_IMG].fill((0, 0, 0))

    return assets
