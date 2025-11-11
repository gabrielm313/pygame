import pygame
import math
from os import path
from config import LARGURA , ALTURA , FPS , IMG_DIR
from assets import load_assets
import sprites

pygame.init()
clock = pygame.time.Clock()

#gera a tela principal com tela cheia
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

#Título do jogo na aba
pygame.display.set_caption('Joguinho')

assets = load_assets()

bg_path = path.join('assets', 'img', 'fundo_pg.png')
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

TAMANHO_DO_AZULEJO = bg_height # dividido pela quantidade de linhas 

# --- Defina aqui as plataformas manualmente (x, y em pixels do mundo) ---
platform_rects = [
            
            pygame.Rect(390,353, 1760 , 4),  
            pygame.Rect(2322, 520, 1220, 4),
            pygame.Rect(3750, 360, 1300, 4),
            pygame.Rect(7640, 360, 1760, 4),
            pygame.Rect(11590, 360, 1450, 4),
            pygame.Rect(13200, 530, 910, 4)
        ]

Astronauta = sprites.Astronauta
Bullet = sprites.Bullet

# Grupos e sprite
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
platforms = pygame.sprite.Group()
                                                                                                                                                                                                                      
astronauta = Astronauta(all_sprites, assets,row = 0 , column = 0, platforms = platform_rects)
all_sprites.add(astronauta)

# reposiciona para o início (ou centro) do mapa:
astronauta.rect.centerx = LARGURA // 2
astronauta.rect.bottom  = ALTURA - 40

# === Camera / scrolling variables ===
camera_x = 0                               # deslocamento horizontal atual da câmera
camera_speed_smooth = 0.5                  # fator para suavizar o movimento (0.0 - 1.0)
left_deadzone = LARGURA // 3               # 1/3 da tela pela esquerda
right_deadzone = (LARGURA * 2) // 3        # 1/3 da tela pela direita
max_camera_x = max(0, bg_width - LARGURA)  # limite para não sair do background

# tiro / cooldown
SHOT_COOLDOWN_MS = 150
last_shot_time = 0

# bloqueio de voltar para a região já passada
LEFT_BACKTRACK_MARGIN = 8
CAMERA_ONLY_FORWARD = False  # se True, câmera só anda pra frente

#deixa os rects(retângulos de plataforma) transparentes longe
for r in platform_rects:
    screen_rect = pygame.Rect(r.x - int(camera_x), r.y, r.w, r.h)
    pygame.draw.rect(window, (207,181,59), screen_rect)

# helper: direção apenas pelas setas (retorna -1/0/1)
from pygame import K_LEFT, K_RIGHT, K_UP, K_DOWN

def get_shot_direction_from_arrows():
    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0
    if keys[K_RIGHT]:
        dx += 1
    if keys[K_LEFT]:
        dx -= 1
    if keys[K_DOWN]:
        dy += 1
    if keys[K_UP]:
        dy -= 1
    return dx, dy

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
    # dt em milissegundos e segundos
    dt_ms = clock.tick(FPS)
    dt = dt_ms / 1000.0

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
                right_deadzone = (LARGURA * 2) // 3 + 100

            # Dependendo da tecla, altera a velocidade.
            if event.key == pygame.K_LEFT:
                    astronauta.speedx = -7
            
            if event.key == pygame.K_RIGHT:
                    astronauta.speedx = 7            

            if event.key == pygame.K_c:
                if hasattr(astronauta, "pular"):
                    astronauta.pular()
            
            # ---------- DISPARO: dispara apenas se SETA estiver pressionada ----------
            # dispara ao apertar qualquer letra, mas só cria bala se setas definirem direção
            if event.key == pygame.K_x:
                now = pygame.time.get_ticks()
                if now - last_shot_time >= SHOT_COOLDOWN_MS:
                    # pega direção a partir das setas
                    dir_x, dir_y = get_shot_direction_from_arrows()

                    # se nenhuma seta pressionada, NÃO DISPARA
                    if dir_x == 0 and dir_y == 0:  
                        pass  # não dispara: continua no loop
                    else:
                        last_shot_time = now

                        # posição do cano (mundo) — usa get_gun_tip() se tiver
                        if hasattr(astronauta, "get_gun_tip"):
                            gun_x, gun_y = astronauta.get_gun_tip()
                        else:
                            gun_x, gun_y = astronauta.rect.centerx + 20, astronauta.rectc.centerccy

                        # cria a bala usando vetor das setas (Bullet normaliza internamente)
                        b = Bullet(gun_x, gun_y, dir_x, dir_y,
                                   speed=900, world_w=bg_width, world_h=bg_height)
                        bullets.add(b)
                        all_sprites.add(b)

            if event.key == pygame.K_DOWN:
                # se estiver em cima de uma plataforma, deseja "cair" dela:
                if astronauta.on_ground:
                    # ativa drop_through por um curtíssimo período e força início da queda
                    astronauta.drop_through_timer = astronauta.drop_through_duration
                    astronauta.on_ground = False
                    # garante uma pequena velocidade para iniciar a queda (evita ficar parado)
                    if astronauta.speedy <= 0:
                        astronauta.speedy = 1
                

        # Verifica se soltou alguma tecla.
        if event.type == pygame.KEYUP :
            if event.key == pygame.K_LEFT:
                astronauta.speedx = 0
            if event.key == pygame.K_RIGHT:
                astronauta.speedx = 0

        # Tratamento de resize (se usar janela)
        if event.type == pygame.VIDEORESIZE:
            LARGURA, ALTURA = event.w, event.h
            reconfigure_display(fullscreen=False)

    # ---- Atualiza os sprites
    all_sprites.update(dt)
    bullets.update(dt)

    # posição do jogador na tela (em coordenadas do mundo)
    player_screen_x = astronauta.rect.centerx - camera_x  # onde o player aparece na tela

    # decidimos target da câmera com base em ambas deadzones
    if player_screen_x > right_deadzone:
        target_camera_x = astronauta.rect.centerx - right_deadzone
    elif player_screen_x < left_deadzone:
        target_camera_x = astronauta.rect.centerx - left_deadzone
    else:
        target_camera_x = camera_x  # dentro das zonas, não movemos a câmera

    # suaviza movimento da câmera (pode multiplicar por dt/1000 se quiser frame-rate independent)
    camera_x += (target_camera_x - camera_x) * camera_speed_smooth

    # evitar micro-jitter: se estiver bem próximo, zere a diferença
    if abs(target_camera_x - camera_x) < 0.5:
        camera_x = target_camera_x

    # Limita câmera aos limites do background
    camera_x = max(0, min(camera_x, max_camera_x))

    # Trava jogador para não voltar para área já passada
    min_allowed_x = int(camera_x) + LEFT_BACKTRACK_MARGIN
    if astronauta.rect.left < min_allowed_x:
        astronauta.rect.left = min_allowed_x
        if astronauta.speedx < 0:
            astronauta.speedx = 0

    window.fill((0, 0, 0))
    window.blit(bg_image, (-int(camera_x), 0))

    # desenha os sprites manualmente subtraindo camera_x das coordenadas
    for sprite in all_sprites:
        draw_x = sprite.rect.x - int(camera_x)
        draw_y = sprite.rect.y
        window.blit(sprite.image, (draw_x, draw_y))

    # <<=== COLOQUE AQUI O LOOP DAS PLATAFORMAS ===>>
    for r in platform_rects:
        screen_rect = pygame.Rect(r.x - int(camera_x), r.y, r.w, r.h)

    mx, my = pygame.mouse.get_pos()            # coords na tela
    world_x = mx + int(camera_x)               # coords no mundo
    world_y = my                               

    # desenhar um pequeno marcador na posição do cursor (na tela)
    pygame.draw.circle(window, (255, 0, 0), (mx, my), 4)

    # escrever texto com as coordenadas
    font = pygame.font.Font(None, 24)  # reutilize um font global se preferir
    txt = f"Screen: ({mx}, {my})  World: ({world_x}, {world_y})"
    surf = font.render(txt, True, (255,255,255))
    window.blit(surf, (10, 10))  

    pygame.display.flip()

    # ----- Atualiza estado do jogo
    pygame.display.update()  # Mostra o novo frame para o jogador

# ===== Finalização =====
pygame.quit()  # Função do PyGame que finaliza os recursos utilizados

