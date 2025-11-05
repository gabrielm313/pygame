import pygame
import os
from config import IMG_DIR

ASTRONAUTA_IMG = 'astronauta1'

def load_assets():
    assets = {}

    #para adicionar a imagem do player foi utilizado chatgpt
    ast_path = os.path.join(IMG_DIR, 'astronauta1.png') 
    astronauta1= pygame.image.load(ast_path).convert_alpha()
    
    # --- ajuste conforme seu sheet: 5 colunas x 5 linhas ---
    COLS = 5
    ROWS = 5
    sheet_w, sheet_h = astronauta1.get_width(), astronauta1.get_height()
    FRAME_W = sheet_w / COLS
    FRAME_H = sheet_h / ROWS

    frames = []
    for r in range(ROWS):
        for c in range(COLS):
            rect = pygame.Rect(c * FRAME_W, r * FRAME_H, FRAME_W, FRAME_H)
            image = astronauta1.subsurface(rect).copy()

            frames.append(image)

    assets[ASTRONAUTA_IMG] = frames
    # 💡 Torna o fundo transparente

    return assets

    