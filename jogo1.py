import pygame
import math
from os import path
from config import LARGURA , ALTURA , FPS , IMG_DIR
from assets import load_assets
import sprites

pygame.init()

# === INICIALIZAÇÃO DOS JOYSTICKS ===
pygame.joystick.init()
joystick1 = None
joystick2 = None

# Tenta pegar o Joystick 1
if pygame.joystick.get_count() > 0:
    joystick1 = pygame.joystick.Joystick(0)
    joystick1.init()
    print(f"Controle 1 detectado: {joystick1.get_name()}")
else:
    print("Nenhum controle de jogo detectado para o Jogador 1.")

# Tenta pegar o Joystick 2 (se houver mais de um)
if pygame.joystick.get_count() > 1:
    joystick2 = pygame.joystick.Joystick(1)
    joystick2.init()
    print(f"Controle 2 detectado: {joystick2.get_name()}")
else:
    print("Apenas um controle (ou nenhum) detectado para o Jogador 2.")
# =================================

clock = pygame.time.Clock()

# gera a tela principal com tela cheia
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# Título do jogo na aba
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

TAMANHO_DO_AZULEJO = bg_height 



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
                                                                                                                        
# JOGADOR 1
astronauta = Astronauta(all_sprites, assets,row = 0 , column = 0, platforms = platform_rects)
all_sprites.add(astronauta)
# JOGADOR 2
astronauta2 = Astronauta(all_sprites, assets,row = 0 , column = 0, platforms = platform_rects)
all_sprites.add(astronauta2)

# reposiciona para o início (ou centro) do mapa:
astronauta.rect.centerx = LARGURA // 2 - 50 # Posição inicial levemente diferente
astronauta.rect.bottom  = ALTURA - 40
astronauta2.rect.centerx = LARGURA // 2 + 50 # Posição inicial levemente diferente
astronauta2.rect.bottom  = ALTURA - 40


# === Camera / scrolling variables ===
camera_x = 0                             # deslocamento horizontal atual da câmera
camera_speed_smooth = 0.5                
left_deadzone = LARGURA // 3             
right_deadzone = (LARGURA * 2) // 3      
max_camera_x = max(0, bg_width - LARGURA)  

# tiro / cooldown
SHOT_COOLDOWN_MS = 150
last_shot_time1 = 0 # Cooldown para JOGADOR 1
last_shot_time2 = 0 # Cooldown para JOGADOR 2

# bloqueio de voltar para a região já passada
LEFT_BACKTRACK_MARGIN = 8
CAMERA_ONLY_FORWARD = False 


# === CONSTANTES E FUNÇÕES DO JOYSTICK ===
JOY_DEADZONE = 0.1 

# Mapeamento Comum do Controle Xbox no Pygame
AXIS_LEFT_X = 0  
AXIS_LEFT_Y = 1  
AXIS_RIGHT_X = 2 
AXIS_RIGHT_Y = 3 
AXIS_RT = 5      
BUTTON_A = 0     

def get_stick_input(joystick, axis_x, axis_y, deadzone=JOY_DEADZONE):
    """Retorna a entrada normalizada do analógico (dx, dy), aplicando deadzone."""
    if joystick is None:
        return 0, 0
    
    dx = joystick.get_axis(axis_x)
    dy = joystick.get_axis(axis_y)

    if abs(dx) < deadzone:
        dx = 0
    if abs(dy) < deadzone:
        dy = 0
    
    norm_x = 0
    if dx > 0:
        norm_x = 1
    elif dx < 0:
        norm_x = -1
        
    norm_y = 0
    if dy > 0:
        norm_y = 1
    elif dy < 0:
        norm_y = -1
        
    return norm_x, norm_y

# helper: direção apenas pelas setas (retorna -1/0/1)
from pygame import K_LEFT, K_RIGHT, K_UP, K_DOWN

def get_shot_direction_from_arrows(joystick):
    """Obtém a direção do tiro do teclado (setas) ou do analógico direito."""
    keys = pygame.key.get_pressed()
    
    # 1. Entrada de Setas (Teclado - prioridade) - Apenas J1 usa teclado
    dx = 0
    dy = 0
    if joystick == joystick1:
        if keys[K_RIGHT]: dx += 1
        if keys[K_LEFT]: dx -= 1
        if keys[K_DOWN]: dy += 1
        if keys[K_UP]: dy -= 1
    
    if dx != 0 or dy != 0:
        return dx, dy
        
    # 2. Entrada do Analógico Direito (Controle)
    if joystick is not None:
        dir_x, dir_y = get_stick_input(joystick, AXIS_RIGHT_X, AXIS_RIGHT_Y)
        
        if dir_x != 0 or dir_y != 0:
            return dir_x, dir_y

    return 0, 0 

# Função auxiliar para (re)configurar tela e background quando muda fullscreen
def reconfigure_display(fullscreen):
    global window, LARGURA, ALTURA, left_deadzone, right_deadzone
    global bg_image, bg_width, bg_height, max_camera_x

    info = pygame.display.Info()
    LARGURA, ALTURA = info.current_w, info.current_h

    if fullscreen:
        window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        window = pygame.display.set_mode((LARGURA, ALTURA))

    bg_image = make_bg_for_height(ALTURA)
    bg_width, bg_height = bg_image.get_width(), bg_image.get_height()
    max_camera_x = max(0, bg_width - LARGURA)


# Função para processar a entrada de um jogador (Joystick e Sprite)
def process_player_input(astronauta, joystick, last_shot_time, dt, is_keyboard_player=False):
    
    # === LEITURA DE ESTADOS CONTÍNUOS ===
    is_rt_pulled = False
    joystick_x_dir = 0
    joystick_y_dir = 0

    if joystick is not None:
        joystick_x_dir, joystick_y_dir = get_stick_input(
            joystick, AXIS_LEFT_X, AXIS_LEFT_Y
        )
        rt_value = joystick.get_axis(AXIS_RT) 
        if rt_value > 0.5: 
            is_rt_pulled = True
            
    # === LÓGICA DE MOVIMENTO CONTÍNUO (Analógico Esquerdo) ===
    
    # Verifica o movimento do teclado APENAS se for o Jogador 1 (is_keyboard_player)
    keys = pygame.key.get_pressed()
    
    if is_keyboard_player:
        if keys[K_LEFT]:
            astronauta.speedx = -7
        elif keys[K_RIGHT]:
            astronauta.speedx = 7
        elif joystick_x_dir == 0:
            astronauta.speedx = 0
    
    # Prioriza o analógico do joystick se ele estiver ativo
    if joystick_x_dir != 0:
        astronauta.speedx = joystick_x_dir * 7 
    elif not is_keyboard_player and joystick_x_dir == 0:
        # Garante que J2 para quando o analógico centraliza
        astronauta.speedx = 0

    # Analógico Esquerdo Y para baixo (Cair da plataforma)
    if joystick_y_dir > 0 and astronauta.on_ground:
        astronauta.drop_through_timer = astronauta.drop_through_duration
        astronauta.on_ground = False
        if astronauta.speedy <= 0:
            astronauta.speedy = 1
            
    # === LÓGICA DE TIRO UNIFICADA ===
    now = pygame.time.get_ticks()
    
    # Se o Jogador 1 estiver usando o teclado para atirar (evento K_x), a flag is_rt_pulled é forçada no loop principal.
    
    if is_rt_pulled: 
        if now - last_shot_time >= SHOT_COOLDOWN_MS: 
            
            dir_x, dir_y = get_shot_direction_from_arrows(joystick)

            if dir_x != 0 or dir_y != 0:
                last_shot_time = now

                if hasattr(astronauta, "get_gun_tip"):
                    gun_x, gun_y = astronauta.get_gun_tip()
                else:
                    gun_x, gun_y = astronauta.rect.centerx + 20, astronauta.rect.centery 

                b = Bullet(gun_x, gun_y, dir_x, dir_y,
                           speed=900, world_w=bg_width, world_h=bg_height)
                bullets.add(b)
                all_sprites.add(b)

    return last_shot_time
# Main loop
running = True
fullscreen = True

game = True
while game:
    
    dt_ms = clock.tick(FPS)
    dt = dt_ms / 1000.0

    # Tempo atual (usado para cooldown)
    now = pygame.time.get_ticks() 
    
    # Flags de tiro por teclado para JOGADOR 1 (K_x)
    j1_shot_by_keyboard = False 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
                
            if event.key == pygame.K_F11:
                fullscreen = not (pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
                reconfigure_display(fullscreen)
                
                left_deadzone = LARGURA // 3
                right_deadzone = (LARGURA * 2) // 3 + 100

            # --- JOGADOR 1: Movimento e Pulo por Teclado ---
            if event.key == pygame.K_LEFT:
                astronauta.speedx = -7
            
            if event.key == pygame.K_RIGHT:
                astronauta.speedx = 7        

            if event.key == pygame.K_c:
                if hasattr(astronauta, "pular"):
                    astronauta.pular()
            
            if event.key == pygame.K_x:
                if now - last_shot_time1 >= SHOT_COOLDOWN_MS: 
                    j1_shot_by_keyboard = True # Flag para atirar J1
            
            if event.key == pygame.K_DOWN:
                if astronauta.on_ground:
                    astronauta.drop_through_timer = astronauta.drop_through_duration
                    astronauta.on_ground = False
                    if astronauta.speedy <= 0:
                        astronauta.speedy = 1
                
        # Verifica se soltou alguma tecla (JOGADOR 1)
        if event.type == pygame.KEYUP :
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                # Se J1 estiver usando teclado, só zera se o joystick não estiver ativo
                if joystick1 is None or get_stick_input(joystick1, AXIS_LEFT_X, AXIS_LEFT_Y)[0] == 0:
                    astronauta.speedx = 0
            
        # === CONTROLE DE JOYSTICK (Eventos Pulo) ===
        if event.type == pygame.JOYBUTTONDOWN:
            if event.joy == 0 and event.button == BUTTON_A: # Botão A no Joystick 1 (J1)
                if hasattr(astronauta, "pular"):
                    astronauta.pular()
            
            if event.joy == 1 and event.button == BUTTON_A: # Botão A no Joystick 2 (J2)
                if hasattr(astronauta2, "pular"):
                    astronauta2.pular()


        if event.type == pygame.VIDEORESIZE:
            LARGURA, ALTURA = event.w, event.h
            reconfigure_display(fullscreen=False)

    # =========================================================
    # === PROCESSAMENTO CONTÍNUO DOS JOGADORES ===
    # =========================================================
    
    # --- JOGADOR 1 (Controlado por Teclado OU Joystick 1) ---
    j1_rt_pulled = False
    if joystick1 is not None:
        if joystick1.get_axis(AXIS_RT) > 0.5:
            j1_rt_pulled = True
    
    # Se o tiro foi acionado pelo teclado, força a flag de RT para processar o tiro
    if j1_shot_by_keyboard:
        j1_rt_pulled = True
    
    last_shot_time1 = process_player_input(
        astronauta, joystick1, last_shot_time1, dt, is_keyboard_player=True)
    
    # Reprocessa o tiro para J1, pois o movimento do teclado é lido antes da função
    if j1_rt_pulled:
        if now - last_shot_time1 >= SHOT_COOLDOWN_MS:
            dir_x, dir_y = get_shot_direction_from_arrows(joystick1) # Usa joystick1/teclado para mira
            if dir_x != 0 or dir_y != 0:
                last_shot_time1 = now
                if hasattr(astronauta, "get_gun_tip"):
                    gun_x, gun_y = astronauta.get_gun_tip()
                else:
                    gun_x, gun_y = astronauta.rect.centerx + 20, astronauta.rect.centery
                b = Bullet(gun_x, gun_y, dir_x, dir_y, speed=900, world_w=bg_width, world_h=bg_height)
                bullets.add(b)
                all_sprites.add(b)

    # --- JOGADOR 2 (Controlado APENAS por Joystick 2) ---
    j2_rt_pulled = False
    if joystick2 is not None:
        if joystick2.get_axis(AXIS_RT) > 0.5:
            j2_rt_pulled = True
    
    last_shot_time2 = process_player_input(
        astronauta2, joystick2, last_shot_time2, dt, is_keyboard_player=False)
    
    # Reprocessa o tiro para J2
    if j2_rt_pulled:
        if now - last_shot_time2 >= SHOT_COOLDOWN_MS:
            dir_x, dir_y = get_shot_direction_from_arrows(joystick2) # Usa joystick2 para mira
            if dir_x != 0 or dir_y != 0:
                last_shot_time2 = now
                if hasattr(astronauta2, "get_gun_tip"):
                    gun_x, gun_y = astronauta2.get_gun_tip()
                else:
                    gun_x, gun_y = astronauta2.rect.centerx + 20, astronauta2.rect.centery
                b = Bullet(gun_x, gun_y, dir_x, dir_y, speed=900, world_w=bg_width, world_h=bg_height)
                bullets.add(b)
                all_sprites.add(b)
    
    
    # ---- Atualiza os sprites
    all_sprites.update(dt)
    bullets.update(dt)

    # Lógica de Câmera (Focando no Jogador 1, ou em um ponto médio se preferir)
    player_screen_x = astronauta.rect.centerx - camera_x 

    if player_screen_x > right_deadzone:
        target_camera_x = astronauta.rect.centerx - right_deadzone
    elif player_screen_x < left_deadzone:
        target_camera_x = astronauta.rect.centerx - left_deadzone
    else:
        target_camera_x = camera_x  

    camera_x += (target_camera_x - camera_x) * camera_speed_smooth

    if abs(target_camera_x - camera_x) < 0.5:
        camera_x = target_camera_x
    
    camera_x = max(0, min(camera_x, max_camera_x))

    # Trava Jogador 1
    min_allowed_x = int(camera_x) + LEFT_BACKTRACK_MARGIN
    if astronauta.rect.left < min_allowed_x:
        astronauta.rect.left = min_allowed_x
        if astronauta.speedx < 0:
            astronauta.speedx = 0
            
    # Trava Jogador 2
    if astronauta2.rect.left < min_allowed_x:
        astronauta2.rect.left = min_allowed_x
        if astronauta2.speedx < 0:
            astronauta2.speedx = 0

    window.fill((0, 0, 0))
    window.blit(bg_image, (-int(camera_x), 0))

    # desenha os sprites manualmente subtraindo camera_x das coordenadas
    for sprite in all_sprites:
        draw_x = sprite.rect.x - int(camera_x)
        draw_y = sprite.rect.y
        window.blit(sprite.image, (draw_x, draw_y))

    # Desenha os retângulos de plataforma (debug)
    for r in platform_rects:
        screen_rect = pygame.Rect(r.x - int(camera_x), r.y, r.w, r.h)
        # pygame.draw.rect(window, (207,181,59, 100), screen_rect, 1)


    mx, my = pygame.mouse.get_pos()             
    world_x = mx + int(camera_x)                 
    world_y = my                                 

    pygame.draw.circle(window, (255, 0, 0), (mx, my), 4)

    font = pygame.font.Font(None, 24) 
    txt = f"Screen: ({mx}, {my})  World: ({world_x}, {world_y})  Cam X: {int(camera_x)}"
    surf = font.render(txt, True, (255,255,255))
    window.blit(surf, (10, 10))

    
    pygame.display.flip()

    pygame.display.update()  

# ===== Finalização =====
pygame.quit()