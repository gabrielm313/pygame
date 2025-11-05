import pygame
import os
from config import IMG_DIR , PLAYER_LARG , PLAYER_ALTU 

ASTRONAUTA_IMG = 'astronauta1'
FUNDO_IMG = 'fundo_pg'

def load_assets():
    assets = {}

    #para adicionar a imagem do player foi utilizado chatgpt
    ast_path = os.path.join(IMG_DIR, 'astronauta1.png') 
    astronauta1= pygame.image.load(ast_path).convert_alpha()
    
    fundo_path = os.path.join(IMG_DIR, 'fundo_pg.png') 
    fundo_pygame= pygame.image.load(fundo_path)
    assets[FUNDO_IMG] = fundo_pygame
    # --- ajuste conforme seu sheet: 5 colunas x 5 linhas ---
    COLS = 5
    ROWS = 5
    sheet_w, sheet_h = astronauta1.get_width(), astronauta1.get_height()
    FRAME_W = sheet_w / COLS
    FRAME_H = sheet_h / ROWS

    #Fator da escala do personagem
    # ESCALA = 1.5

    frames = []
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * FRAME_W, r * FRAME_H, FRAME_W, FRAME_H)
            image = astronauta1.subsurface(rect).copy()

            # novo_tam = (int(FRAME_W * ESCALA) , int(FRAME_H * ESCALA))
            image = pygame.transform.scale(image, (PLAYER_LARG , PLAYER_ALTU))

            frames.append(image)

    assets[ASTRONAUTA_IMG] = frames

    return assets

    