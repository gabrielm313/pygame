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
    
    ALIEN_SIZE = (100, 90)   # largura, altura em px -> ajuste para ficar maior/menor
    UFO_SIZE   = (140, 80)
    LASER_SIZE = (12, 28)    # tamanho do sprite do laser inimigo (opcional)

    # tenta carregar, se alguma imagem não existir, cria placeholder
    def safe_load(name, filename):
        p = os.path.join(IMG_DIR, filename)
        if os.path.exists(p):
            return pygame.image.load(p).convert_alpha()
        else:
            s = pygame.Surface((32,32), pygame.SRCALPHA)
            s.fill((255,0,255))
            return s

    raw_alien = safe_load('alien', 'alien.png')     # nome do arquivo que vc colocou na pasta img
    raw_ufo   = safe_load('ovni', 'ovni.png')       # ajuste nome de arquivo se necessário
    raw_laser = safe_load('enemy_laser', 'enemy_laser.png')

    # escala com smoothscale (mantém qualidade)
    assets[ALIEN_IMG] = pygame.transform.smoothscale(raw_alien, ALIEN_SIZE)
    assets[OVNI_IMG]   = pygame.transform.smoothscale(raw_ufo, UFO_SIZE)
    assets[ENEMY_LASER_IMG] = pygame.transform.smoothscale(raw_laser, LASER_SIZE)

    fundo_path = os.path.join(IMG_DIR, 'fundo_pg.png') 
    fundo_pygame= pygame.image.load(fundo_path)
    assets[FUNDO_IMG] = fundo_pygame
    assets[ASTRONAUTA_IMG] = pygame.image.load(os.path.join(IMG_DIR, 'astronauta1.png')).convert_alpha()
    
    return assets

    