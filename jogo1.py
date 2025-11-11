import pygame
import math
from os import path
import os
import sys
from config import LARGURA , ALTURA , FPS , IMG_DIR
from assets import load_assets
import sprites

# --------------------------- INICIALIZAÇÃO ---------------------------
pygame.init()
# inicializa mixer (para tocar música)
try:
    pygame.mixer.init()
except Exception as e:
    print("Aviso: pygame.mixer.init() falhou:", e)

# ------------------ CORES / CONFIGURAÇÕES DO MENU ------------------
BUTTON_BG = (120, 40, 40)
BUTTON_HOVER_BG = (70, 70, 120)
BUTTON_BORDER = (255, 255, 255)
BUTTON_TEXT = (245, 245, 245)

MENU_BG_PATH = path.join('assets', 'img', 'inicio.png')
TUTORIAL_PATHS = [
    path.join('assets', 'img', 'tutorial1.png'),
    path.join('assets', 'img', 'tutorial2.png'),
]
MENU_MUSIC_PATH = path.join('assets', 'sounds', 'som9.mp3')
GAME_MUSIC_PATH = path.join('assets', 'sounds', 'som5.mp3')

# === INICIALIZAÇÃO DOS JOYSTICKS ===
pygame.joystick.init()
joystick1 = None
joystick2 = None

if pygame.joystick.get_count() > 0:
    joystick1 = pygame.joystick.Joystick(0)
    joystick1.init()
    print(f"Controle 1 detectado: {joystick1.get_name()}")
if pygame.joystick.get_count() > 1:
    joystick2 = pygame.joystick.Joystick(1)
    joystick2.init()
    print(f"Controle 2 detectado: {joystick2.get_name()}")

clock = pygame.time.Clock()

# gera a tela principal com tela cheia
info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

pygame.display.set_caption('Joguinho')

assets = load_assets()

bg_path = path.join('assets', 'img', 'fundo_pg.png')
if not os.path.exists(bg_path):
    print(f"Atenção: fundo não encontrado em {bg_path}")
    orig_bg = pygame.Surface((1920, 1080)).convert_alpha()
    orig_bg.fill((0, 0, 0))
else:
    orig_bg = pygame.image.load(bg_path).convert_alpha()

def make_bg_for_height(target_height):
    orig_w, orig_h = orig_bg.get_width(), orig_bg.get_height()
    modificador = target_height / orig_h
    new_w = int(orig_w * modificador)
    return pygame.transform.scale(orig_bg, (new_w, target_height))

bg_image = make_bg_for_height(ALTURA)
bg_width, bg_height = bg_image.get_width(), bg_image.get_height()

TAMANHO_DO_AZULEJO = bg_height

# ----------------- Funções de UI / Menu / Tutorial -----------------

def load_and_scale(img_path, W, H, keep_aspect=True):
    # ... (código da função permanece)
    if not os.path.exists(img_path):
        return None
    img = pygame.image.load(img_path).convert_alpha()
    if keep_aspect:
        iw, ih = img.get_size()
        scale = min(W/iw, H/ih)
        return pygame.transform.smoothscale(img, (int(iw*scale), int(ih*scale)))
    return pygame.transform.smoothscale(img, (W, H))

def draw_button(surface, rect, text, font, hovered=False,
                bg_color=BUTTON_BG, hover_bg=BUTTON_HOVER_BG,
                border_color=BUTTON_BORDER, text_color=BUTTON_TEXT):
    # ... (código da função permanece)
    bg_used = hover_bg if hovered else bg_color
    pygame.draw.rect(surface, bg_used, rect, border_radius=12)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=12)
    txt = font.render(text, True, text_color)
    tx = rect.x + (rect.w - txt.get_width())//2
    ty = rect.y + (rect.h - txt.get_height())//2
    surface.blit(txt, (tx, ty))

def show_tutorial_interactive(screen, clock, W, H, image_paths):
    # ... (código da função permanece)
    imgs = [load_and_scale(p, int(W*0.8), int(H*0.75)) for p in image_paths]
    index = 0
    running = True
    small_font = pygame.font.Font(None, 28)

    NAV_COOLDOWN = 0.25
    last_nav_time = 0.0
    last_axis_dir = 0

    while running:
        dt = clock.tick(60) / 1000.0
        now = pygame.time.get_ticks() / 1000.0

        for ev in pygame.event.get():
             # ... (código de eventos permanece)
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    index = min(index + 1, len(imgs)-1)
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    index = max(index - 1, 0)
            # ... (mais eventos)
            if ev.type == pygame.JOYAXISMOTION:
                axis_idx = getattr(ev, "axis", None)
                val = getattr(ev, "value", 0.0)
                AXIS_THRESHOLD = 0.6
                if axis_idx == 0:
                    dir_now = 0
                    if val > AXIS_THRESHOLD: dir_now = 1
                    elif val < -AXIS_THRESHOLD: dir_now = -1
                    if dir_now != 0 and dir_now != last_axis_dir and (now - last_nav_time >= NAV_COOLDOWN):
                        if dir_now > 0: index = min(index+1, len(imgs)-1)
                        else: index = max(index-1, 0)
                        last_nav_time = now
                    last_axis_dir = dir_now
        
        # ... (código de desenho permanece)
        overlay = pygame.Surface((W, H))
        overlay.fill((8, 8, 12))
        screen.blit(overlay, (0, 0))

        img = imgs[index]
        if img:
            ix = (W - img.get_width())//2
            iy = (H - img.get_height())//2
            screen.blit(img, (ix, iy))
        else:
            placeholder = small_font.render(f"Imagem {index+1} ausente: {image_paths[index]}", True, (220,220,220))
            screen.blit(placeholder, ((W-placeholder.get_width())//2, H//2))
            
        left_arrow = small_font.render("◀", True, (240,240,240))
        right_arrow = small_font.render("▶", True, (240,240,240))
        screen.blit(left_arrow, (W*0.08 - left_arrow.get_width()/2, H//2 - left_arrow.get_height()/2))
        screen.blit(right_arrow, (W*0.92 - right_arrow.get_width()/2, H//2 - right_arrow.get_height()/2))

        page_text = small_font.render(f"{index+1} / {len(imgs)}  (← → / D-pad / stick)  ESC: fechar", True, (200,200,220))
        screen.blit(page_text, ((W-page_text.get_width())//2, int(H*0.9)))
        
        pygame.display.flip()

def menu(screen, clock, W, H):
    # ... (código da função permanece)
    bg = load_and_scale(MENU_BG_PATH, W, H, keep_aspect=False)
    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 52)

    btn_w, btn_h = 420, 86
    btn_play = pygame.Rect((W//2 - btn_w//2, int(H*0.5 - btn_h - 10), btn_w, btn_h))
    btn_tutorial = pygame.Rect((W//2 - btn_w//2, int(H*0.5 + 10), btn_w, btn_h))

    # --- Tocar música do menu (se existir) ---
    if os.path.exists(MENU_MUSIC_PATH):
        try:
            pygame.mixer.music.load(MENU_MUSIC_PATH)
            pygame.mixer.music.set_volume(0.25) 
            pygame.mixer.music.play(-1) 
        except Exception as e:
            print("Erro ao tocar música do menu:", e)

    running = True
    start_game = False
    while running:
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
             # ... (código de eventos permanece)
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    start_game = True; running = False
                if ev.key == pygame.K_t:
                    show_tutorial_interactive(screen, clock, W, H, TUTORIAL_PATHS)
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_play.collidepoint(ev.pos):
                    start_game = True; running = False
                elif btn_tutorial.collidepoint(ev.pos):
                    show_tutorial_interactive(screen, clock, W, H, TUTORIAL_PATHS)
            if ev.type == pygame.JOYBUTTONDOWN:
                if ev.button == 0:
                    start_game = True; running = False
                elif ev.button == 1:
                    show_tutorial_interactive(screen, clock, W, H, TUTORIAL_PATHS)

        # desenha fundo do menu
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((18, 18, 40))

        draw_button(screen, btn_play, "JOGAR", btn_font, hovered=btn_play.collidepoint(mx, my))
        draw_button(screen, btn_tutorial, "TUTORIAL", btn_font, hovered=btn_tutorial.collidepoint(mx, my))

        pygame.display.flip()
        clock.tick(60)

    try:
        pygame.mixer.music.fadeout(500)
    except Exception:
        try:
            pygame.mixer.music.stop()
        except:
            pass

    return start_game

def mostrar_quadrinhos(screen, clock, W, H):
    """
    Mostra os quadrinhos em sequência, cada um por 15 segundos.
    Permite pular com ESC, Enter, ou Botão A do controle.
    """
    quadrinhos = [
        path.join('assets', 'img', 'quadrinho3.png'),
        path.join('assets', 'img', 'quadrinho4.png'),
        path.join('assets', 'img', 'quadrinho5.png')
    ]
    # Duração aumentada para 15 segundos (15000 ms) - CORREÇÃO DO LOOP APLICADA AQUI
    DURACAO = 15000  # 15 segundos por quadrinho
    
    BUTTON_A = 0
    
    imgs = []

    for p in quadrinhos:
        if os.path.exists(p):
            img = pygame.image.load(p).convert_alpha()
            iw, ih = img.get_size()
            scale = min(W / iw, H / ih)
            new_img = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
            imgs.append(new_img)
        else:
            imgs.append(None)

    for i, img in enumerate(imgs):
        start_time = pygame.time.get_ticks()
        running = True
        while running:
            dt = clock.tick(60)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        return 
                
                elif ev.type == pygame.JOYBUTTONDOWN:
                    if ev.button == BUTTON_A:
                        return 
                        
            screen.fill((0, 0, 0))
            if img:
                ix = (W - img.get_width()) // 2
                iy = (H - img.get_height()) // 2
                screen.blit(img, (ix, iy))
            else:
                font = pygame.font.Font(None, 48)
                msg = f"Imagem {i+1} não encontrada: {quadrinhos[i]}"
                t = font.render(msg, True, (255, 255, 255))
                screen.blit(t, ((W - t.get_width()) // 2, H // 2))

            small_font = pygame.font.Font(None, 28)
            skip_text = small_font.render("Pular: ESC / ENTER / Botão A", True, (200, 200, 220))
            screen.blit(skip_text, ((W - skip_text.get_width() - 20), int(H * 0.95)))


            pygame.display.flip()

            if pygame.time.get_ticks() - start_time >= DURACAO:
                running = False
                
def draw_health_bar(surface, player, x, y):
    """Desenha a barra de vida de um jogador (ADICIONADA)."""
    if player.dead:
        return
        
    BAR_WIDTH = 100
    BAR_HEIGHT = 10
    BORDER_COLOR = (255, 255, 255)
    EMPTY_COLOR = (50, 50, 50)
    HEALTH_COLOR = (0, 255, 0)
    INVULN_COLOR = (255, 255, 0) # Amarelo piscante

    health_ratio = max(0.0, min(1.0, float(player.health) / float(player.max_health)))
    fill_width = int(BAR_WIDTH * health_ratio)

    fill_color = HEALTH_COLOR
    if player._invuln_timer > 0.0:
        if (pygame.time.get_ticks() // 100) % 2 == 0:
            fill_color = INVULN_COLOR
        else:
            fill_color = HEALTH_COLOR
            
    outline_rect = pygame.Rect(x, y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(surface, EMPTY_COLOR, outline_rect)
    
    fill_rect = pygame.Rect(x, y, fill_width, BAR_HEIGHT)
    pygame.draw.rect(surface, fill_color, fill_rect)

    pygame.draw.rect(surface, BORDER_COLOR, outline_rect, 2)


# ----------------- FIM MENU / INICIO DO JOGO -----------------

entrar_menu = menu(window, clock, LARGURA, ALTURA)
if not entrar_menu:
    pygame.quit()
    sys.exit(0)

mostrar_quadrinhos(window, clock, LARGURA, ALTURA) # CORREÇÃO DE DURAÇÃO APLICADA

if os.path.exists(GAME_MUSIC_PATH):
    try:
        if pygame.mixer.music.get_busy():
              pygame.mixer.music.stop()
              
        pygame.mixer.music.load(GAME_MUSIC_PATH)
        pygame.mixer.music.set_volume(0.20) 
        pygame.mixer.music.play(-1) 
    except Exception as e:
        print("Erro ao tocar música do jogo:", e)
else:
    print(f"Atenção: música do jogo não encontrada em {GAME_MUSIC_PATH}")

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
Alien = sprites.Alien
OVNI = sprites.OVNI
EnemyLaser = sprites.EnemyLaser

# Grupos e sprite
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
platforms = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()    # Grupo para TODOS os inimigos
enemy_lasers_group = pygame.sprite.Group() # Grupo para TODOS os lasers inimigos

# JOGADOR 1
astronauta = Astronauta(all_sprites, assets,row = 0 , column = 0, platforms = platform_rects)
all_sprites.add(astronauta)
# JOGADOR 2
astronauta2 = Astronauta(all_sprites, assets,row = 0 , column = 0, platforms = platform_rects)
all_sprites.add(astronauta2)

# Dicionário de grupos para passar para os inimigos
all_groups = {
    'all_sprites': all_sprites,
    'enemies': enemies_group,
    'enemy_lasers': enemy_lasers_group
}

# --- Lista de Spawns dos Inimigos ---
ENEMY_SPAWN_DATA = [
    ('alien', 1000, ALTURA - 40, 900, 1300), 
    ('ovni',  1500, 200, 1400, 1800),
    ('alien', 2400, 520, 2350, 2600), 
    ('alien', 4000, 360, 3900, 4200),
    ('ovni',  4500, 250, 4300, 4800),
]

player1 = astronauta
player2 = astronauta2

# Loop para criar os inimigos
for data in ENEMY_SPAWN_DATA:
    e_type, x, y, p_left, p_right = data
    
    enemy = None
    if e_type == 'alien':
        enemy = Alien(x, y, assets, p_left, p_right, player1, player2, all_groups) 
    elif e_type == 'ovni':
        enemy = OVNI(x, y, assets, p_left, p_right, player1, player2, all_groups)
    
    if enemy:
        all_sprites.add(enemy)
        enemies_group.add(enemy)

# reposiciona para o início (ou centro) do mapa:
astronauta.rect.centerx = LARGURA // 2 - 50 
astronauta.rect.bottom  = ALTURA - 40
astronauta2.rect.centerx = LARGURA // 2 + 50 
astronauta2.rect.bottom  = ALTURA - 40

# === Camera / scrolling variables ===
camera_x = 0
camera_speed_smooth = 0.5
left_deadzone = LARGURA // 3
right_deadzone = (LARGURA * 2) // 3
max_camera_x = max(0, bg_width - LARGURA)

# tiro / cooldown
SHOT_COOLDOWN_MS = 150
last_shot_time1 = 0
last_shot_time2 = 0

LEFT_BACKTRACK_MARGIN = 8
CAMERA_ONLY_FORWARD = False

# === CONSTANTES E FUNÇÕES DO JOYSTICK ===
JOY_DEADZONE = 0.1
AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_RT = 5
BUTTON_A = 0 

def get_stick_input(joystick, axis_x, axis_y, deadzone=JOY_DEADZONE):
    # ... (código da função permanece)
    if joystick is None:
        return 0, 0
    dx = joystick.get_axis(axis_x)
    dy = joystick.get_axis(axis_y)
    if abs(dx) < deadzone: dx = 0
    if abs(dy) < deadzone: dy = 0
    norm_x = 0
    if dx > 0: norm_x = 1
    elif dx < 0: norm_x = -1
    norm_y = 0
    if dy > 0: norm_y = 1
    elif dy < 0: norm_y = -1
    return norm_x, norm_y

from pygame import K_LEFT, K_RIGHT, K_UP, K_DOWN

def get_shot_direction_from_arrows(joystick):
    # ... (código da função permanece)
    keys = pygame.key.get_pressed()
    dx = 0; dy = 0
    if joystick == joystick1:
        if keys[K_RIGHT]: dx += 1
        if keys[K_LEFT]: dx -= 1
        if keys[K_DOWN]: dy += 1
        if keys[K_UP]: dy -= 1
    if dx != 0 or dy != 0:
        return dx, dy
    if joystick is not None:
        dir_x, dir_y = get_stick_input(joystick, AXIS_RIGHT_X, AXIS_RIGHT_Y)
        if dir_x != 0 or dir_y != 0:
            return dir_x, dir_y
    return 0, 0

def reconfigure_display(fullscreen):
    # ... (código da função permanece)
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

def process_player_input(astronauta, joystick, last_shot_time, dt, is_keyboard_player=False):
    # ... (código da função permanece)
    is_rt_pulled = False
    joystick_x_dir = 0
    joystick_y_dir = 0
    if joystick is not None:
        joystick_x_dir, joystick_y_dir = get_stick_input(joystick, AXIS_LEFT_X, AXIS_LEFT_Y)
        rt_value = joystick.get_axis(AXIS_RT) if joystick.get_numaxes() > AXIS_RT else 0
        if rt_value > 0.5:
            is_rt_pulled = True
    keys = pygame.key.get_pressed()
    if is_keyboard_player:
        if keys[K_LEFT]:
            astronauta.speedx = -7
        elif keys[K_RIGHT]:
            astronauta.speedx = 7
        elif joystick_x_dir == 0:
            astronauta.speedx = 0
    if joystick_x_dir != 0:
        astronauta.speedx = joystick_x_dir * 7
    elif not is_keyboard_player and joystick_x_dir == 0:
        astronauta.speedx = 0
    if joystick_y_dir > 0 and astronauta.on_ground:
        astronauta.drop_through_timer = astronauta.drop_through_duration
        astronauta.on_ground = False
        if astronauta.speedy <= 0:
            astronauta.speedy = 1
    now = pygame.time.get_ticks()
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
    now = pygame.time.get_ticks()
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
            if event.key == pygame.K_LEFT:
                astronauta.speedx = -7
            if event.key == pygame.K_RIGHT:
                astronauta.speedx = 7
            if event.key == pygame.K_c:
                if hasattr(astronauta, "pular"):
                    astronauta.pular()
            if event.key == pygame.K_x:
                if now - last_shot_time1 >= SHOT_COOLDOWN_MS:
                    j1_shot_by_keyboard = True
            if event.key == pygame.K_DOWN:
                if astronauta.on_ground:
                    astronauta.drop_through_timer = astronauta.drop_through_duration
                    astronauta.on_ground = False
                    if astronauta.speedy <= 0:
                        astronauta.speedy = 1
        if event.type == pygame.KEYUP :
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                if joystick1 is None or get_stick_input(joystick1, AXIS_LEFT_X, AXIS_LEFT_Y)[0] == 0:
                    astronauta.speedx = 0
        if event.type == pygame.JOYBUTTONDOWN:
            if event.joy == 0 and event.button == BUTTON_A:
                if hasattr(astronauta, "pular"):
                    astronauta.pular()
            if event.joy == 1 and event.button == BUTTON_A:
                if hasattr(astronauta2, "pular"):
                    if not astronauta2.dead: # ADICIONADO: Pular só se não estiver morto
                        astronauta2.pular()
        if event.type == pygame.VIDEORESIZE:
            LARGURA, ALTURA = event.w, event.h
            reconfigure_display(fullscreen=False)
    
    # PROCESSAMENTO CONTÍNUO DOS JOGADORES (mantido)
    j1_rt_pulled = False
    if joystick1 is not None and joystick1.get_numaxes() > AXIS_RT:
        if joystick1.get_axis(AXIS_RT) > 0.5:
            j1_rt_pulled = True
    if j1_shot_by_keyboard:
        j1_rt_pulled = True

    last_shot_time1 = process_player_input(astronauta, joystick1, last_shot_time1, dt, is_keyboard_player=True)
    if j1_rt_pulled and not astronauta.dead: # ADICIONADO: Não atira se morto
        if now - last_shot_time1 >= SHOT_COOLDOWN_MS:
            dir_x, dir_y = get_shot_direction_from_arrows(joystick1)
            if dir_x != 0 or dir_y != 0:
                last_shot_time1 = now
                if hasattr(astronauta, "get_gun_tip"):
                    gun_x, gun_y = astronauta.get_gun_tip()
                else:
                    gun_x, gun_y = astronauta.rect.centerx + 20, astronauta.rect.centery
                b = Bullet(gun_x, gun_y, dir_x, dir_y, speed=900, world_w=bg_width, world_h=bg_height)
                bullets.add(b)
                all_sprites.add(b)

    j2_rt_pulled = False
    if joystick2 is not None and joystick2.get_numaxes() > AXIS_RT:
        if joystick2.get_axis(AXIS_RT) > 0.5:
            j2_rt_pulled = True

    last_shot_time2 = process_player_input(astronauta2, joystick2, last_shot_time2, dt, is_keyboard_player=False)
    if j2_rt_pulled and not astronauta2.dead: # ADICIONADO: Não atira se morto
        if now - last_shot_time2 >= SHOT_COOLDOWN_MS:
            dir_x, dir_y = get_shot_direction_from_arrows(joystick2)
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

    # LÓGICA DE COLISÃO: Balas inimigas vs. Jogadores (ADICIONADA)
    if not astronauta.dead:
        hits1 = pygame.sprite.spritecollide(astronauta, enemy_lasers_group, True) # True mata o laser inimigo
        for hit in hits1:
            astronauta.take_damage(1) # Causa 1 de dano
            
    if not astronauta2.dead:
        hits2 = pygame.sprite.spritecollide(astronauta2, enemy_lasers_group, True) # True mata o laser inimigo
        for hit in hits2:
            astronauta2.take_damage(1) # Causa 1 de dano


    # Lógica de Câmera (Focando no Jogador 1) (mantida)
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

    min_allowed_x = int(camera_x) + LEFT_BACKTRACK_MARGIN
    if astronauta.rect.left < min_allowed_x:
        astronauta.rect.left = min_allowed_x
        if astronauta.speedx < 0:
            astronauta.speedx = 0
    if astronauta2.rect.left < min_allowed_x:
        astronauta2.rect.left = min_allowed_x
        if astronauta2.speedx < 0:
            astronauta2.speedx = 0

    window.fill((0, 0, 0))
    window.blit(bg_image, (-int(camera_x), 0))

    # desenha sprites subtraindo camera_x
    for sprite in all_sprites:
        draw_x = sprite.rect.x - int(camera_x)
        draw_y = sprite.rect.y
        # Se for o astronauta e estiver invulnerável, faz piscar
        if isinstance(sprite, Astronauta) and sprite._invuln_timer > 0.0:
             if (pygame.time.get_ticks() // 100) % 2 == 0:
                 continue # Pula o desenho para simular o piscar
                 
        window.blit(sprite.image, (draw_x, draw_y))

    # Desenha os retângulos de plataforma (debug) - comentado
    for r in platform_rects:
        screen_rect = pygame.Rect(r.x - int(camera_x), r.y, r.w, r.h)
        # pygame.draw.rect(window, (207,181,59, 100), screen_rect, 1)

    # Desenha as barras de vida (ADICIONADA)
    draw_health_bar(window, astronauta, 10, ALTURA - 30)  # P1 - Canto inferior esquerdo
    draw_health_bar(window, astronauta2, LARGURA - 110, ALTURA - 30) # P2 - Canto inferior direito


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
sys.exit(0)