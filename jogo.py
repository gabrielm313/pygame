import pygame
import os
from config import LARGURA, ALTURA
from assets import load_assets, ASTRONAUTA_IMG
from sprites import Astronauta

pygame.init()
clock = pygame.time.Clock()


#gera a tela principal com tela cheia
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h

window = pygame.display.set_mode((LARGURA , ALTURA))

#Título do jogo na aba
pygame.display.set_caption('Joguinho')

assets = load_assets()

# depois escale orig_bg para bg_image como mostrei acima


bg_path = os.path.join('assets', 'img', 'fundo_pg.png')
orig_bg = pygame.image.load(bg_path).convert_alpha()

# escala inicial do background com base na ALTURA atual
def make_bg_for_height(target_height):
    orig_w, orig_h = orig_bg.get_width(), orig_bg.get_height()
    modificador = target_height / orig_h
    new_w = int(orig_w * modificador)
    return pygame.transform.scale(orig_bg, (new_w, target_height))

# decide se vai esticar para a largura da janela ou repetir (tile)
bg_image = make_bg_for_height(ALTURA)
bg_width, bg_height = bg_image.get_width(), bg_image.get_height()

# Grupos e sprite
all_sprites = pygame.sprite.Group()
astronauta = Astronauta(all_sprites, assets)
all_sprites.add(astronauta)

# === Camera / scrolling variables ===
camera_x = 0                          # deslocamento horizontal atual da câmera
camera_speed_smooth = 0.5             # fator para suavizar o movimento (0.0 - 1.0)
left_deadzone = LARGURA // 3          # 1/3 da tela pela esquerda
right_deadzone = (LARGURA * 2) // 3   # 1/3 da tela pela direita
max_camera_x = max(0, bg_width- LARGURA)  # limite para não sair do background

# Função auxiliar para (re)configurar tela e background quando muda fullscreen
def reconfigure_display(fullscreen):
    global window, LARGURA, ALTURA, left_deadzone, right_deadzone
    global bg_image, bg_width, bg_height, max_camera_x

    # primeiro atualiza dimensões reais da tela (importante)
    info = pygame.display.Info()
    LARGURA, ALTURA = info.current_w, info.current_h

    # agora cria a janela/alternativa fullscreen com as novas dimensões
    if fullscreen:
        window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window = pygame.display.set_mode((LARGURA, ALTURA))

    left_deadzone = LARGURA // 3
    right_deadzone = (LARGURA * 2) // 3

    # reescala o background usando a imagem original
    bg_image = make_bg_for_height(ALTURA)

    # atualiza medidas e limite da câmera
    bg_width, bg_height = bg_image.get_width(), bg_image.get_height()
    max_camera_x = max(0, bg_width - LARGURA)


# Main loop
running = True
fullscreen = True

game = True
while game:
    dt = clock.tick(60)  # limita a 60 FPS

    for event in pygame.event.get():
        # ----- Verifica consequências
        if event.type == pygame.QUIT:
            game = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
                
            #colocar o jogo em tela cheia
            if event.key == pygame.K_F11:
                fullscreen = not (pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
                reconfigure_display(fullscreen)
                
                # recalcula deadzones se necessário
                left_deadzone = LARGURA // 3
                right_deadzone = (LARGURA * 2) // 3

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

    # posição do jogador na tela (em coordenadas do mundo)
    player_screen_x = astronauta.rect.centerx - camera_x  # onde o player aparece na tela

    if player_screen_x > right_deadzone and astronauta.speedx > 0:
        # quanto a câmera deve avançar (suavizado)
        desired_shift = astronauta.speedx  # poderia multiplicar por dt ou outro fator
        # Use dt para tornar independente de framerate se quiser:
        camera_x += desired_shift * camera_speed_smooth * (dt / 16)
    
    # Limita câmera aos limites do background
    camera_x = max(0, min(camera_x, max_camera_x))

    window.fill((0, 0, 0))
    window.blit(bg_image, (-int(camera_x), 0))

    # desenha os sprites manualmente subtraindo camera_x das coordenadas
    for sprite in all_sprites:
        draw_x = sprite.rect.x - int(camera_x)
        draw_y = sprite.rect.y
        window.blit(sprite.image, (draw_x, draw_y))


    pygame.display.flip()

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados

