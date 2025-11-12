# jogo.py - integrado (menu + boss1 + boss2 + faroeste) + ranking/names + botão Y para ranking
import pygame
import sys
import os
import math
import random
import json
import datetime
from os import path

# ---------------- Paths / Config ----------------
INTRO_QUADRINHOS = [
    path.join('assets', 'img', 'quadrinho3.png'),
    path.join('assets', 'img', 'quadrinho4.png'),
    path.join('assets', 'img', 'quadrinho5.png'),
    path.join('assets', 'img', 'procurado1.png')
]
POST_BOSS1_QUADRINHO = path.join('assets', 'img', 'procurado2.png')
POST_BOSS2_QUADRINHOS = [
    path.join('assets', 'img', 'quadrinho1.png'),
    path.join('assets', 'img', 'quadrinho2.png')
]
TUTORIAL_PATHS = [path.join('assets', 'img', 'tutorial1.png'),
                  path.join('assets', 'img', 'tutorial2.png')]

QUADRINHO_DURATION_MS = 10000
JOYSTICK_SKIP_BUTTON_A = 0   # botão A -> pular / confirmar (xbox)
JOYSTICK_TUTORIAL_BUTTON_B = 1   # botão B -> tutorial
JOYSTICK_RANKING_BUTTON_Y = 3  # botão Y -> abrir ranking (xbox)
MOUSE_LEFT = 1

RANKING_FILE = "ranking.json"
MAX_RANKING = 10

# default boss bullet speed constant (you can change)
BOSS_HAND_BULLET_SPEED = 500.0

# ---------------- Utilities ----------------
def load_and_scale(img_path, W, H, keep_aspect=True):
    if not os.path.exists(img_path):
        return None
    img = pygame.image.load(img_path).convert_alpha()
    if keep_aspect:
        iw, ih = img.get_size()
        scale = min(W/iw, H/ih)
        return pygame.transform.smoothscale(img, (int(iw*scale), int(ih*scale)))
    return pygame.transform.smoothscale(img, (W, H))

def show_quadrinhos_sequence(screen, clock, W, H, image_paths, duration_ms=10000):
    imgs = [load_and_scale(p, W, H, keep_aspect=False) for p in image_paths]
    idx = 0
    num = len(imgs)
    while idx < num:
        img = imgs[idx]
        start = pygame.time.get_ticks()
        exited_early = False
        while pygame.time.get_ticks() - start < duration_ms:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return False
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        exited_early = True
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == MOUSE_LEFT:
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_SKIP_BUTTON_A:
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    # open tutorial while viewing quadrinho
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
            if img:
                screen.blit(img, (0,0))
            else:
                screen.fill((0,0,0))
                f = pygame.font.Font(None, 36)
                txt = f.render(f"Imagem ausente: {image_paths[idx]}", True, (255,255,255))
                screen.blit(txt, ((W-txt.get_width())//2, H//2))
            pygame.display.flip()
            clock.tick(60)
            if exited_early:
                break
        idx += 1
    return True

# ---------------- Ranking (load/save/show) ----------------
def load_ranking():
    if not os.path.exists(RANKING_FILE):
        return []
    try:
        with open(RANKING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def save_ranking_entry(name, time_seconds):
    ranking = load_ranking()
    entry = {
        "name": name,
        "time_seconds": float(time_seconds),
        "date": datetime.datetime.utcnow().isoformat() + "Z"
    }
    ranking.append(entry)
    # order ascending by time (best = menor tempo)
    ranking = sorted(ranking, key=lambda e: e['time_seconds'])
    ranking = ranking[:MAX_RANKING]
    try:
        with open(RANKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(ranking, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def show_ranking_screen(screen, clock, W, H):
    font_title = pygame.font.Font(None, 64)
    font_item = pygame.font.Font(None, 36)
    ranking = load_ranking()
    showing = True
    while showing:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    showing = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                showing = False
            if ev.type == pygame.JOYBUTTONDOWN and ev.button in (JOYSTICK_SKIP_BUTTON_A, JOYSTICK_RANKING_BUTTON_Y):
                showing = False
        screen.fill((10,10,20))
        title = font_title.render("RANKING - MELHORES TEMPOS", True, (255, 215, 0))
        screen.blit(title, (W//2 - title.get_width()//2, 40))
        y = 140
        if not ranking:
            no = font_item.render("Nenhum registro ainda.", True, (220,220,220))
            screen.blit(no, (W//2 - no.get_width()//2, y))
        else:
            for i, e in enumerate(ranking):
                minutes = int(e['time_seconds'])//60
                seconds = int(e['time_seconds'])%60
                ms = int((e['time_seconds'] - int(e['time_seconds']))*1000)
                timestr = f"{minutes:d}:{seconds:02d}.{ms:03d}"
                text = f"{i+1}. {e['name']} — {timestr}"
                it = font_item.render(text, True, (230,230,230))
                screen.blit(it, (W//2 - it.get_width()//2, y))
                y += 44
        hint = font_item.render("Pressione ESC/ENTER/Y/A para voltar", True, (180,180,180))
        screen.blit(hint, (W//2 - hint.get_width()//2, H - 80))
        pygame.display.flip()
        clock.tick(30)

# ---------------- Simple name input screen ----------------
def get_player_names(screen, clock, W, H):
    # returns tuple (name1, name2) or None if cancelled
    font = pygame.font.Font(None, 40)
    title_font = pygame.font.Font(None, 64)
    input_boxes = ["", ""]
    active = 0
    max_len = 20
    prompt1 = "Nome do Jogador 1:"
    prompt2 = "Nome do Jogador 2:"
    info = "Enter para confirmar cada nome. ESC para cancelar."
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key == pygame.K_BACKSPACE:
                    if len(input_boxes[active])>0:
                        input_boxes[active] = input_boxes[active][:-1]
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # if currently on first field, move to second; if on second and non-empty return
                    if active == 0:
                        active = 1
                    else:
                        if input_boxes[1].strip() == "":
                            # don't accept empty second name; keep active
                            pass
                        else:
                            # both filled -> return
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                else:
                    ch = ev.unicode
                    if ch and len(input_boxes[active]) < max_len and ord(ch) >= 32:
                        input_boxes[active] += ch
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx,my = ev.pos
                # clicking roughly switch box; simple layout detection
                box1 = pygame.Rect(W//2-280, H//2-20, 560, 48)
                box2 = pygame.Rect(W//2-280, H//2+60, 560, 48)
                if box1.collidepoint(mx,my): active = 0
                if box2.collidepoint(mx,my): active = 1
            if ev.type == pygame.JOYBUTTONDOWN:
                # A to confirm / next
                if ev.button == JOYSTICK_SKIP_BUTTON_A:
                    if active == 0:
                        active = 1
                    else:
                        if input_boxes[1].strip() != "":
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                # B to toggle active
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    active = 1 - active

        screen.fill((12, 12, 28))
        title = title_font.render("Digite os nomes", True, (255,255,200))
        screen.blit(title, (W//2 - title.get_width()//2, H//2 - 180))
        p1 = font.render(prompt1, True, (220,220,220))
        p2 = font.render(prompt2, True, (220,220,220))
        screen.blit(p1, (W//2 - p1.get_width()//2, H//2 - 80))
        screen.blit(p2, (W//2 - p2.get_width()//2, H//2))
        # draw boxes
        box1 = pygame.Rect(W//2-280, H//2-20, 560, 48)
        box2 = pygame.Rect(W//2-280, H//2+60, 560, 48)
        color_active = (200,200,240); color_inactive = (80,80,110)
        pygame.draw.rect(screen, color_active if active==0 else color_inactive, box1, border_radius=6)
        pygame.draw.rect(screen, color_active if active==1 else color_inactive, box2, border_radius=6)
        txt1 = font.render(input_boxes[0] or "Player1", True, (10,10,20))
        txt2 = font.render(input_boxes[1] or "Player2", True, (10,10,20))
        screen.blit(txt1, (box1.x+12, box1.y+8))
        screen.blit(txt2, (box2.x+12, box2.y+8))
        info_s = font.render(info, True, (180,180,180))
        screen.blit(info_s, (W//2 - info_s.get_width()//2, H//2 + 140))
        pygame.display.flip()
        clock.tick(30)

# ---------------- Menu ----------------
def menu(screen, clock, W, H):
    pygame.mouse.set_visible(True)
    MENU_BG_PATH = path.join('assets', 'img', 'inicio.png')
    MENU_MUSIC_PATH = path.join('assets', 'sounds', 'som9.mp3')

    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 52)
    btn_w, btn_h = 420, 86
    btn_play = pygame.Rect((W//2 - btn_w//2, int(H*0.5 - btn_h - 10), btn_w, btn_h))
    btn_tutorial = pygame.Rect((W//2 - btn_w//2, int(H*0.5 + 10), btn_w, btn_h))
    btn_ranking = pygame.Rect((W//2 - btn_w//2, int(H*0.5 + 110), btn_w, btn_h))

    # Start menu music (fade from previous if needed)
    if os.path.exists(MENU_MUSIC_PATH):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(400)
        pygame.mixer.music.load(MENU_MUSIC_PATH)
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)

    bg = load_and_scale(MENU_BG_PATH, W, H, keep_aspect=False)
    running = True
    start_game = False
    while running:
        mx,my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    start_game = True; running = False
                if ev.key == pygame.K_t:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                if ev.key == pygame.K_r:
                    show_ranking_screen(screen, clock, W, H)
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_play.collidepoint(ev.pos):
                    start_game = True; running = False
                elif btn_tutorial.collidepoint(ev.pos):
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                elif btn_ranking.collidepoint(ev.pos):
                    show_ranking_screen(screen, clock, W, H)
            if ev.type == pygame.JOYBUTTONDOWN:
                if ev.button == JOYSTICK_SKIP_BUTTON_A:
                    start_game = True; running = False
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                if ev.button == JOYSTICK_RANKING_BUTTON_Y:
                    show_ranking_screen(screen, clock, W, H)

        if bg:
            screen.blit(bg, (0,0))
        else:
            screen.fill((18,18,40))

        def draw_button(surface, rect, text, font, hovered=False):
            BUTTON_BG = (120,40,40)
            BUTTON_HOVER_BG = (70,70,120)
            BUTTON_BORDER = (255,255,255)
            BUTTON_TEXT = (245,245,245)
            bgc = BUTTON_HOVER_BG if hovered else BUTTON_BG
            pygame.draw.rect(surface, bgc, rect, border_radius=12)
            pygame.draw.rect(surface, BUTTON_BORDER, rect, 2, border_radius=12)
            txt = font.render(text, True, BUTTON_TEXT)
            tx = rect.x + (rect.w - txt.get_width())//2
            ty = rect.y + (rect.h - txt.get_height())//2
            surface.blit(txt, (tx, ty))

        draw_button(screen, btn_play, "JOGAR", btn_font, hovered=btn_play.collidepoint(mx,my))
        draw_button(screen, btn_tutorial, "TUTORIAL", btn_font, hovered=btn_tutorial.collidepoint(mx,my))
        draw_button(screen, btn_ranking, "RANKING", btn_font, hovered=btn_ranking.collidepoint(mx,my))
        pygame.display.flip()
        clock.tick(60)
    pygame.mixer.music.fadeout(500)
    return start_game

# ---------------- Boss1 stage classes ----------------
class SlimePatch:
    def __init__(self, x, y, width, height, dps=6.0, duration=8.0):
        self.rect = pygame.Rect(int(x), int(y), int(width), int(height))
        self.dps = float(dps)
        self.duration = float(duration)
        self.time = 0.0
        self.alive = True
        self.surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.surface.fill((20,200,40,130))
    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False
    def collides_player(self, player):
        if not player or getattr(player, "dead", False):
            return False
        return self.rect.colliderect(player.rect)
    def draw(self, surface):
        surface.blit(self.surface, (self.rect.x, self.rect.y))

class SimpleBullet:
    def __init__(self, x, y, dir_x, dir_y, speed=300.0, color=(255,100,180), radius=6):
        self.x = float(x); self.y = float(y)
        l = math.hypot(dir_x, dir_y) or 1.0
        self.dx = dir_x / l; self.dy = dir_y / l
        self.speed = speed
        self.color = color
        self.radius = radius
        self.alive = True
        self.life = 4.0
    def update(self, dt):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
    def collides_rect(self, rect):
        closest_x = max(rect.left, min(int(self.x), rect.right))
        closest_y = max(rect.top, min(int(self.y), rect.bottom))
        dx = int(self.x) - closest_x; dy = int(self.y) - closest_y
        return (dx*dx + dy*dy) <= (self.radius*self.radius)

class PlayerSimple:
    def __init__(self, x, ground_y, screen_height, image_path=None):
        self.ground_y = ground_y
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_height * 0.25)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 64
        self.h = self.image.get_height() if self.image else 128
        self.rect = pygame.Rect(x, ground_y - self.h, self.w, self.h)
        self.vel_x = 0.0; self.vel_y = 0.0
        self.SPEED = 700.0; self.JUMP_VELOCITY = -1500.0; self.GRAVITY = 3000.0
        self.grounded = True
        self.fire_cooldown = 0.25; self._time_since_last_shot=0.0
        self.gun_offset=(self.w//2, self.h//2)
        shot_path = os.path.join('assets','sounds','som6.mp3')
        self.shot_sound = None
        if os.path.exists(shot_path):
            self.shot_sound = pygame.mixer.Sound(shot_path); self.shot_sound.set_volume(0.2)
        self.max_health = 8; self.health = float(self.max_health)
        self.invuln_time = 0.8; self._invuln_timer=0.0; self.dead=False
        self.aim=(1,0); self.facing_right=True
    def handle_input_keyboard(self, keys, left_key, right_key, look_up_key, aim_keys):
        if self.dead: self.vel_x=0; return
        vx=0.0
        if keys[left_key]: vx=-self.SPEED
        if keys[right_key]: vx=self.SPEED
        self.vel_x=vx
        if self.vel_x>0: self.facing_right=True
        elif self.vel_x<0: self.facing_right=False
        if look_up_key and keys[look_up_key]:
            self.aim=(0,-1)
        else:
            ax=0; ay=0
            for k,vec in aim_keys.items():
                if keys[k]:
                    ax+=vec[0]; ay+=vec[1]
            if ax!=0 or ay!=0:
                ax=max(-1,min(1,ax)); ay=max(-1,min(1,ay)); self.aim=(ax,ay)
    def try_jump(self):
        if self.dead: return
        if self.grounded:
            self.vel_y = self.JUMP_VELOCITY; self.grounded=False
    def update(self, dt, screen_width):
        if self.dead: return
        self._time_since_last_shot += dt
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
            if self._invuln_timer<0: self._invuln_timer=0.0
        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0: self.rect.left=0
        if self.rect.right>screen_width: self.rect.right=screen_width
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y; self.vel_y=0.0; self.grounded=True
        else: self.grounded=False
    def can_shoot(self):
        return (not self.dead) and (self._time_since_last_shot >= self.fire_cooldown)
    def shoot(self, direction):
        if not self.can_shoot(): return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx
        spawn_y = self.rect.centery
        dx,dy=direction
        if dx==0 and dy==0:
            dx = 1.0 if self.facing_right else -1.0
        b = SimpleBullet(spawn_x, spawn_y, dx, dy, speed=700.0, color=(255,105,180), radius=6)
        if self.shot_sound:
            self.shot_sound.play()
        return b
    def take_damage(self, amount):
        if self._invuln_timer>0.0 or self.dead: return False
        self.health -= amount; self._invuln_timer = self.invuln_time
        if self.health <= 0:
            self.dead = True
        return True
    def draw(self, surface):
        if self.dead: return
        if self.image:
            frame = self.image
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200,30,30), self.rect)
        bar_w = max(40, self.w); bar_h = 8
        bar_x = self.rect.x; bar_y = self.rect.y - (bar_h+6)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30,30,50), bg_rect)
        hp_ratio = max(0.0, min(1.0, float(self.health)/float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        if hasattr(self, "_invuln_timer") and self._invuln_timer>0.0:
            if (pygame.time.get_ticks()//120)%2==0:
                fill_color=(120,180,255)
            else:
                fill_color=(80,130,220)
        else:
            fill_color=(40,140,255)
        if fill_w>0:
            pygame.draw.rect(surface, fill_color, fill_rect)
        pygame.draw.rect(surface, (200,200,220), bg_rect, 1)

class Boss1:
    def __init__(self, x, y, screen_w, screen_h, image_path=None):
        self.screen_w = screen_w; self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * 0.35)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 200
        self.h = self.image.get_height() if self.image else 150
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.speed = 140.0; self.direction = 1
        self.patrol_min_x = 50; self.patrol_max_x = screen_w - 50 - self.w
        self._time = 0.0
        self.bob_amplitude = 10.0; self.bob_frequency = 0.6
        self.max_health = 120; self.health = float(self.max_health)
        self.slime_cooldown = 2.5; self._time_since_last_slime = 0.0
        self.slime_width = int(self.w*0.5); self.slime_height = 36
        self.slime_duration = 10.0; self.slime_dps = 8.0
    def update(self, dt):
        self._time += dt; self._time_since_last_slime += dt
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x; self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x; self.direction = -1
        self._y_offset = math.sin(2*math.pi*self.bob_frequency*self._time) * self.bob_amplitude
    def try_drop_slime(self):
        if self._time_since_last_slime < self.slime_cooldown:
            return None
        spawn_x = int(self.rect.centerx - self.slime_width // 2)
        spawn_y = int(self.screen_h - self.slime_height)
        patch = SlimePatch(spawn_x, spawn_y, self.slime_width, self.slime_height,
                           dps=self.slime_dps, duration=self.slime_duration)
        self._time_since_last_slime = 0.0
        return patch
    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (40,40,40), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health/self.max_health)
        pygame.draw.rect(surface, (200,20,20), (self.rect.x, draw_y - 12, int(self.w*hp_ratio), 8))

def run_boss1(screen, clock, W, H):
    fundo_path = os.path.join('assets','img','fundo2.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W,H))
    player1 = PlayerSimple(W//4, H, H, image_path=os.path.join('assets','img','astronauta1.png'))
    player2 = PlayerSimple(3*W//4, H, H, image_path=os.path.join('assets','img','astronauta1.png'))
    boss = Boss1(W//2 - 200, 60, W, H, image_path=os.path.join('assets','img','boss2.png'))
    bullets = []
    boss_bullets = []
    slime_patches = []
    roar_path = os.path.join('assets','sounds','som11.mp3')
    roar_sound = None
    if os.path.exists(roar_path):
        roar_sound = pygame.mixer.Sound(roar_path); roar_sound.set_volume(0.55)
    ROAR_INTERVAL=10.0; _roar_timer=0.0

    # música de fundo do boss1
    boss1_music_path = os.path.join('assets','sounds','som10.mp3')
    if os.path.exists(boss1_music_path):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(400)
        pygame.mixer.music.load(boss1_music_path)
        pygame.mixer.music.set_volume(0.18)
        pygame.mixer.music.play(-1)

    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i); j.init(); joysticks.append(j)
    # trigger previous state per joystick for rising-edge detection
    trigger_prev = [False] * len(joysticks)
    TRIGGER_THRESHOLD = 0.5
    font = pygame.font.Font(None, 24)
    while True:
        dt = clock.tick(60)/1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return False
                if ev.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                    player1.try_jump()
                if ev.key == pygame.K_i:
                    player2.try_jump()
                if ev.key == pygame.K_x:
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player1.shoot((dx/length, dy/length))
                    if b: bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player2.shoot((dx/length, dy/length))
                    if b: bullets.append(b)
            if ev.type == pygame.JOYBUTTONDOWN:
                if ev.button == 0:
                    if ev.joy == 0:
                        player1.try_jump()
                    elif ev.joy == 1:
                        player2.try_jump()
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)

        # joystick poll: movement, right stick aim, trigger fire (with rising-edge detection)
        for i in range(len(joysticks)):
            j = joysticks[i]
            axis0 = j.get_axis(0) if j.get_numaxes()>0 else 0.0
            if i == 0:
                player1.vel_x = axis0 * player1.SPEED
                if player1.vel_x > 0: player1.facing_right = True
                elif player1.vel_x < 0: player1.facing_right = False
            else:
                player2.vel_x = axis0 * player2.SPEED
                if player2.vel_x > 0: player2.facing_right = True
                elif player2.vel_x < 0: player2.facing_right = False

            # aim from right stick
            aim_ax = j.get_axis(2) if j.get_numaxes() > 2 else 0.0
            aim_ay = j.get_axis(3) if j.get_numaxes() > 3 else 0.0
            DEAD = 0.25
            if abs(aim_ax) >= DEAD or abs(aim_ay) >= DEAD:
                length = math.hypot(aim_ax, aim_ay) or 1.0
                nx, ny = aim_ax / length, aim_ay / length
                if i == 0:
                    player1.aim = (nx, ny)
                else:
                    player2.aim = (nx, ny)

            # trigger axis -> detect rising edge (press event)
            trigger_val = 0.0
            if j.get_numaxes() > 5:
                trigger_val = j.get_axis(5)
            elif j.get_numaxes() > 4:
                trigger_val = j.get_axis(4)
            pressed_now = abs(trigger_val) > TRIGGER_THRESHOLD

            # only fire on rising edge (was not pressed before, now pressed)
            if pressed_now and not trigger_prev[i]:
                player = player1 if i == 0 else player2
                dx, dy = player.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                    dy = 0.0
                length = math.hypot(dx, dy) or 1.0
                b = player.shoot((dx/length, dy/length))
                if b:
                    bullets.append(b)

            # update previous state for next frame
            trigger_prev[i] = pressed_now

        # updates
        player1.update(dt, W); player2.update(dt, W); boss.update(dt)
        _roar_timer += dt
        if _roar_timer >= ROAR_INTERVAL and roar_sound and boss.health>0:
            roar_sound.play(); _roar_timer = 0.0
        patch = boss.try_drop_slime()
        if patch: slime_patches.append(patch)
        bullets = [b for b in bullets if b.alive]; boss_bullets = [b for b in boss_bullets if b.alive]
        for b in bullets: b.update(dt)
        for b in boss_bullets: b.update(dt)
        slime_patches = [s for s in slime_patches if s.alive]
        for s in slime_patches: s.update(dt)
        for b in bullets[:]:
            if b.collides_rect(boss.rect):
                boss.health -= 1; b.alive=False
                if b in bullets: bullets.remove(b)
        for s in slime_patches:
            for p in (player1, player2):
                if p.health>0 and s.collides_player(p):
                    dmg = s.dps * dt
                    p.health = max(0.0, p.health - dmg)
                    if p.health <= 0:
                        p.dead=True
        if boss.health <= 0:
            pygame.mixer.music.fadeout(600)
            show_quadrinhos_sequence(screen, clock, W, H, [POST_BOSS1_QUADRINHO], duration_ms=QUADRINHO_DURATION_MS)
            return True
        if not any((not p.dead and p.health>0) for p in (player1, player2)):
            pygame.mixer.music.fadeout(600)
            return False
        if fundo_image: screen.blit(fundo_image, (0,0))
        else: screen.fill((10,10,12))
        boss.draw(screen)
        for s in slime_patches: s.draw(screen)
        for b in bullets: b.draw(screen)
        for b in boss_bullets: b.draw(screen)
        player1.draw(screen); player2.draw(screen)
        hud = font.render(f"P1 HP: {int(player1.health)}   P2 HP: {int(player2.health)}   Boss: {int(boss.health)}", True, (255,255,255))
        screen.blit(hud, (12,12))
        pygame.display.flip()

# ---------------- Boss2 stage classes ----------------
class Boss2:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, bullet_image_path=None):
        self.screen_w = screen_w; self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * 0.35)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 200
        self.h = self.image.get_height() if self.image else 150
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.speed = 140.0; self.direction = 1
        self.patrol_min_x = 50; self.patrol_max_x = screen_w - 50 - self.w
        self.bob_amplitude = 30.0; self.bob_frequency = 0.8
        self._time = 0.0
        self.max_health = 60; self.health = self.max_health
        self.hand_offsets = [int(self.w * 0.22), int(self.w * 0.78) - 12]
        self.hand_bullet_cooldowns = [1.2, 1.2]; self._time_since_last_bullet = [0.0, 0.0]
        self.hand_laser_cooldowns = [6.0, 6.0]; self._time_since_last_laser = [0.0, 0.0]
        self.laser_width = 120; self.laser_height = int(screen_h * 0.55)
        self.laser_duration = 1.2; self.laser_damage_per_second = 3.0
    def update(self, dt):
        self._time += dt
        for i in range(len(self._time_since_last_bullet)): self._time_since_last_bullet[i] += dt
        for i in range(len(self._time_since_last_laser)): self._time_since_last_laser[i] += dt
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x; self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x; self.direction = -1
        self._y_offset = math.sin(2*math.pi*self.bob_frequency*self._time) * self.bob_amplitude
    def try_shoot_hands_at_players(self, player_centers):
        bullets = []
        if not player_centers: return bullets
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_bullet[i] < self.hand_bullet_cooldowns[i]: continue
            spawn_x = int(self.rect.x + offset); spawn_y = draw_y + self.h - 10
            best=None; best_dist=None
            for c in player_centers:
                dx = c[0]-spawn_x; dy = c[1]-spawn_y; d=dx*dx+dy*dy
                if best is None or d<best_dist:
                    best=(dx,dy); best_dist=d
            if best is None: continue
            dx,dy = best; l = math.hypot(dx,dy) or 1.0
            # use configurable BOSS_HAND_BULLET_SPEED
            b = SimpleBullet(spawn_x, spawn_y, dx/l, dy/l, speed=BOSS_HAND_BULLET_SPEED, color=(0,255,60), radius=8)
            bullets.append(b); self._time_since_last_bullet[i]=0.0
        return bullets
    def try_fire_lasers(self):
        lasers=[]
        for i,offset in enumerate(self.hand_offsets):
            if self._time_since_last_laser[i] < self.hand_laser_cooldowns[i]: continue
            laser = {'offset': offset - (self.laser_width//2)+6, 'w': self.laser_width, 'h': self.laser_height, 'time':0.0}
            lasers.append(laser); self._time_since_last_laser[i]=0.0
        return lasers
    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self,'_y_offset',0))
        if self.image: surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (80,80,80), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health/self.max_health)
        pygame.draw.rect(surface, (200,20,20), (self.rect.x, draw_y-12, int(self.w*hp_ratio), 8))

def run_boss2(screen, clock, W, H):
    fundo_path = os.path.join('assets','img','fundo_boss.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W,H))

    # music for boss2
    boss2_music_path = os.path.join('assets','sounds','som4.mp3')
    if os.path.exists(boss2_music_path):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(400)
        pygame.mixer.music.load(boss2_music_path)
        pygame.mixer.music.set_volume(0.18)
        pygame.mixer.music.play(-1)

    player1 = PlayerSimple(W//4, H, H, image_path=os.path.join('assets','img','astronauta1.png'))
    player2 = PlayerSimple(3*W//4, H, H, image_path=os.path.join('assets','img','astronauta1.png'))
    boss = Boss2(W//4, 80, W, H, image_path=os.path.join('assets','img','nave boss.png'),
                 bullet_image_path=os.path.join('assets','img','bala.png'))
    bullets = []; boss_bullets = []; boss_lasers = []
    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i); j.init(); joysticks.append(j)
    # trigger previous state per joystick for rising-edge detection
    trigger_prev = [False] * len(joysticks)
    TRIGGER_THRESHOLD = 0.5
    while True:
        dt = clock.tick(60)/1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return False
                if ev.key == pygame.K_w: player1.try_jump()
                if ev.key == pygame.K_i: player2.try_jump()
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player1.shoot((dx/length, dy/length))
                    if b: bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player2.shoot((dx/length, dy/length))
                    if b: bullets.append(b)
            if ev.type == pygame.JOYBUTTONDOWN:
                if ev.button == 0:
                    if ev.joy == 0: player1.try_jump()
                    elif ev.joy == 1: player2.try_jump()
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)

        # joystick poll (movement + aim + trigger with rising-edge)
        for i in range(len(joysticks)):
            j = joysticks[i]
            ax = j.get_axis(0) if j.get_numaxes()>0 else 0.0
            if i==0:
                player1.vel_x = ax * player1.SPEED
                if player1.vel_x>0: player1.facing_right=True
                elif player1.vel_x<0: player1.facing_right=False
            else:
                player2.vel_x = ax * player2.SPEED
                if player2.vel_x>0: player2.facing_right=True
                elif player2.vel_x<0: player2.facing_right=False

            aim_ax = j.get_axis(2) if j.get_numaxes()>2 else 0.0
            aim_ay = j.get_axis(3) if j.get_numaxes()>3 else 0.0
            DEAD = 0.25
            if abs(aim_ax) >= DEAD or abs(aim_ay) >= DEAD:
                length = math.hypot(aim_ax, aim_ay) or 1.0
                nx, ny = aim_ax/length, aim_ay/length
                if i==0: player1.aim = (nx, ny)
                else: player2.aim = (nx, ny)

            trigger_val = 0.0
            if j.get_numaxes() > 5:
                trigger_val = j.get_axis(5)
            elif j.get_numaxes() > 4:
                trigger_val = j.get_axis(4)
            pressed_now = abs(trigger_val) > TRIGGER_THRESHOLD

            if pressed_now and not trigger_prev[i]:
                player = player1 if i==0 else player2
                dx, dy = player.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                    dy = 0.0
                length = math.hypot(dx, dy) or 1.0
                b = player.shoot((dx/length, dy/length))
                if b: bullets.append(b)

            trigger_prev[i] = pressed_now

        # updates
        player1.update(dt, W); player2.update(dt, W); boss.update(dt)
        player_centers = [p.rect.center for p in (player1, player2) if p.health>0]
        if player_centers:
            new_bullets = boss.try_shoot_hands_at_players(player_centers)
            if new_bullets: boss_bullets.extend(new_bullets)
        new_lasers = boss.try_fire_lasers()
        for l in new_lasers: l['time']=0.0; boss_lasers.append(l)
        bullets = [b for b in bullets if b.alive]; boss_bullets = [b for b in boss_bullets if b.alive]
        for b in bullets: b.update(dt)
        for b in boss_bullets: b.update(dt)
        for l in boss_lasers[:]:
            l['time'] += dt
            if l['time'] >= boss.laser_duration:
                boss_lasers.remove(l)
        for b in bullets[:]:
            if b.collides_rect(boss.rect):
                boss.health -= 1; b.alive=False; 
                if b in bullets: bullets.remove(b)
        for b in boss_bullets[:]:
            for p in (player1, player2):
                if p.health>0 and b.collides_rect(p.rect):
                    if p.take_damage(1):
                        b.alive=False
                        if b in boss_bullets: boss_bullets.remove(b)
                        break
        for l in boss_lasers:
            draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
            x = int(boss.rect.x + l['offset']); y = draw_y + boss.h
            laser_rect = pygame.Rect(x, y, l['w'], l['h'])
            for p in (player1, player2):
                if p.health>0 and laser_rect.colliderect(p.rect):
                    dmg = boss.laser_damage_per_second * dt
                    p.health = max(0.0, p.health - dmg)
                    if p.health <= 0:
                        p.dead=True
        if boss.health <= 0:
            pygame.mixer.music.fadeout(600)
            show_quadrinhos_sequence(screen, clock, W, H, POST_BOSS2_QUADRINHOS, duration_ms=QUADRINHO_DURATION_MS)
            return True
        if not any((not p.dead and p.health>0) for p in (player1, player2)):
            pygame.mixer.music.fadeout(600)
            return False
        if fundo_image: screen.blit(fundo_image, (0,0))
        else: screen.fill((0,0,0))
        boss.draw(screen)
        for l in boss_lasers:
            draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0)); x = int(boss.rect.x + l['offset']); y = draw_y + boss.h
            surf = pygame.Surface((l['w'], l['h']), pygame.SRCALPHA); surf.fill((255,80,80,160))
            screen.blit(surf, (x,y))
        for b in bullets: b.draw(screen)
        for b in boss_bullets: b.draw(screen)
        player1.draw(screen); player2.draw(screen)
        pygame.display.flip()

# ---------------- Faroeste stage (duelo final) ----------------
def run_faroeste(screen, clock, W, H):
    """
    Modified to return winner id:
      returns 1 if player1 wins, 2 if player2 wins, 0 for tie/draw, None if cancelled/escape
    """
    fundo_path = os.path.join('assets','img','faroeste.png')
    fundo = None
    if os.path.exists(fundo_path):
        fundo = pygame.image.load(fundo_path).convert_alpha()
        fundo = pygame.transform.smoothscale(fundo, (W,H))
    asset = {}
    tiro_animacao = []
    for i in range(4):
        fp = os.path.join('assets','img', f'efeito{i}.png')
        if os.path.exists(fp):
            img = pygame.image.load(fp).convert_alpha()
            img = pygame.transform.scale(img, (32,32))
            tiro_animacao.append(img)
    asset['tiro_animacao'] = tiro_animacao
    sound_path_music = os.path.join('assets','sounds','som1.mp3')
    sound_path_shot = os.path.join('assets','sounds','som2.mp3')
    if os.path.exists(sound_path_music):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(400)
        pygame.mixer.music.load(sound_path_music)
        pygame.mixer.music.set_volume(0.6); pygame.mixer.music.play(-1)
    if os.path.exists(sound_path_shot):
        asset['som_tiro'] = pygame.mixer.Sound(sound_path_shot); asset['som_tiro'].set_volume(0.6)
    GUN_TIP_POS_P1 = (420, 700); GUN_TIP_POS_P2 = (1100, 700)
    KEY_P1 = pygame.K_a; KEY_P2 = pygame.K_l
    BUTTON_A = 0; BEST_OF = 5
    PREP_TIME = 1.0; POINT_TIME = 1.0
    MIN_RANDOM_DELAY = 1.0; MAX_RANDOM_DELAY = 3.0
    FLASH_DURATION_MS = 140; RECOIL_DURATION_MS = 140; ROUND_END_PAUSE = 1.0
    font = pygame.font.Font(os.path.join('assets','font','escrita1.ttf') if os.path.exists(os.path.join('assets','font','escrita1.ttf')) else None, 56)
    font2 = pygame.font.Font(os.path.join('assets','font','escrita2.ttf') if os.path.exists(os.path.join('assets','font','escrita2.ttf')) else None, 70)
    small_font = pygame.font.Font(os.path.join('assets','font','escrita1.ttf') if os.path.exists(os.path.join('assets','font','escrita1.ttf')) else None, 36)
    score_p1 = 0; score_p2 = 0; round_number = 1; game_over=False
    state = "preparar"; state_time = pygame.time.get_ticks(); waiting_target_time = None; winner_this_round=None
    last_shot_time_p1 = -9999; last_shot_time_p2 = -9999
    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i); j.init(); joysticks.append(j)
    prev_buttons = [[0 for _ in range(j.get_numbuttons())] for j in joysticks]
    tiros_group = pygame.sprite.Group()
    class Tiro(pygame.sprite.Sprite):
        def __init__(self, center, assets, offset=(0,-15)):
            super().__init__()
            self.frames = assets.get('tiro_animacao', [])
            self.frame = 0
            self.image = self.frames[self.frame] if self.frames else pygame.Surface((32,32))
            self.rect = self.image.get_rect()
            self.rect.centerx = center[0] + offset[0]; self.rect.centery = center[1] + offset[1]
            self.last_update = pygame.time.get_ticks(); self.frame_ticks = 50
        def update(self):
            now = pygame.time.get_ticks()
            if now - self.last_update > self.frame_ticks:
                self.last_update = now; self.frame += 1
                if self.frame >= len(self.frames): self.kill()
                else:
                    center = self.rect.center; self.image = self.frames[self.frame]; self.rect = self.image.get_rect(); self.rect.center = center
    def start_round():
        nonlocal state, state_time, waiting_target_time, winner_this_round
        winner_this_round = None; state = "preparar"; state_time = pygame.time.get_ticks(); waiting_target_time=None
    def set_to_point_phase():
        nonlocal state, state_time, waiting_target_time
        state = "apontar"; state_time = pygame.time.get_ticks(); waiting_target_time = None
    def trigger_ja():
        nonlocal state, state_time
        state = "ja"; state_time = pygame.time.get_ticks()
    def end_round(winner):
        nonlocal state, state_time, score_p1, score_p2, winner_this_round
        winner_this_round = winner; state = "resultado"; state_time = pygame.time.get_ticks()
        if winner == 1: score_p1 += 1
        elif winner == 2: score_p2 += 1
    def check_match_over():
        alvo = (BEST_OF // 2) + 1
        return score_p1 >= alvo or score_p2 >= alvo
    start_round()
    while True:
        dt_ms = clock.tick(60); now = pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return None
        for idx, j in enumerate(joysticks):
            for b in range(j.get_numbuttons()):
                val = j.get_button(b)
                if val and not prev_buttons[idx][b]:
                    player = 1 if idx == 0 else 2
                    if state == "ja" and winner_this_round is None and b == BUTTON_A:
                        if player == 1:
                            last_shot_time_p1 = now; tiros_group.add(Tiro(GUN_TIP_POS_P1, asset, offset=(+250,-60)))
                        else:
                            last_shot_time_p2 = now; tiros_group.add(Tiro(GUN_TIP_POS_P2, asset, offset=(+125,-40)))
                        if 'som_tiro' in asset and asset['som_tiro']: asset['som_tiro'].play()
                        end_round(player)
                    elif state in ("preparar","apontar") and winner_this_round is None and b == BUTTON_A:
                        end_round(2 if player == 1 else 1)
                prev_buttons[idx][b] = val
        keys = pygame.key.get_pressed()
        if not game_over:
            if state == "ja" and winner_this_round is None:
                if keys[KEY_P1]:
                    last_shot_time_p1 = now; tiros_group.add(Tiro(GUN_TIP_POS_P1, asset, offset=(+250,-60))); asset.get('som_tiro',None) and asset['som_tiro'].play(); end_round(1)
                elif keys[KEY_P2]:
                    last_shot_time_p2 = now; tiros_group.add(Tiro(GUN_TIP_POS_P2, asset, offset=(+125,-40))); asset.get('som_tiro',None) and asset['som_tiro'].play(); end_round(2)
            elif state in ("preparar","apontar") and winner_this_round is None:
                if keys[KEY_P1]:
                    end_round(2)
                elif keys[KEY_P2]:
                    end_round(1)
        if not game_over:
            if state == "preparar" and now - state_time >= PREP_TIME*1000:
                set_to_point_phase()
            elif state == "apontar" and now - state_time >= POINT_TIME*1000:
                if waiting_target_time is None:
                    delay = random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
                    waiting_target_time = now + int(delay*1000)
                elif now >= waiting_target_time:
                    trigger_ja()
            elif state == "ja" and now - state_time >= 3000 and winner_this_round is None:
                winner_this_round = 0; state="resultado"; state_time = now
            elif state == "resultado" and now - state_time >= ROUND_END_PAUSE*1000:
                if check_match_over() or round_number > BEST_OF:
                    game_over = True
                else:
                    round_number += 1; start_round()
        if fundo: screen.blit(fundo, (0,0))
        else: screen.fill((0,0,0))
        title = font2.render('DUELO', True, (255,255,255)) if font2 else None
        if title: screen.blit(title, (W//2 - title.get_width()//2, 20))
        if game_over:
            msg = "EMPATE!"
            if score_p1 > score_p2: msg = "JOGADOR 1 VENCEU O JOGO!"
            elif score_p2 > score_p1: msg = "JOGADOR 2 VENCEU O JOGO!"
            text = font.render(msg, True, (255,0,0)) if font else None
            if text: screen.blit(text, (W//2 - text.get_width()//2, H//2 - 50))
            hint = small_font.render("PRESSIONE ESC PARA SAIR", True, (200,200,200)) if small_font else None
            if hint: screen.blit(hint, (W//2 - hint.get_width()//2, H//2 + 30))
        else:
            if state == "preparar":
                s = font.render("PREPARAR...", True, (255,255,255)) if font else None
                if s: screen.blit(s, (W//2 - s.get_width()//2, H//2 - 80))
            elif state == "apontar":
                s = font.render("APONTAR...", True, (255,255,255)) if font else None
                if s: screen.blit(s, (W//2 - s.get_width()//2, H//2 - 80))
            elif state == "ja":
                s = font.render("JA!", True, (10,255,10)) if font else None
                if s: screen.blit(s, (W//2 - s.get_width()//2, H//2 - 80))
            elif state == "resultado":
                round_msg = "EMPATE!" if winner_this_round==0 else ("JOGADOR 1 VENCEU A RODADA!" if winner_this_round==1 else "JOGADOR 2 VENCEU A RODADA!")
                tr = font.render(round_msg, True, (255,255,255)) if font else None
                if tr: screen.blit(tr, (W//2 - tr.get_width()//2, H//2 - 100))
                score_msg = f"{score_p1}  x  {score_p2}"
                ts = font2.render(score_msg, True, (0,255,0)) if font2 else None
                if ts: screen.blit(ts, (W//2 - ts.get_width()//2, H//2))
        if now - last_shot_time_p1 <= FLASH_DURATION_MS:
            age = (now - last_shot_time_p1) / FLASH_DURATION_MS
            rad = int(20*(1-age)+6)
            pygame.draw.circle(screen, (255,220,80), (520,750), rad)
        if now - last_shot_time_p2 <= FLASH_DURATION_MS:
            age = (now - last_shot_time_p2) / FLASH_DURATION_MS
            rad = int(20*(1-age)+6)
            pygame.draw.circle(screen, (255,220,80), (1375,775), rad)
        tiros_group.update(); tiros_group.draw(screen)
        pygame.display.flip()
        if game_over:
            pygame.mixer.music.fadeout(600)
            # determine winner id
            if score_p1 > score_p2:
                return 1
            elif score_p2 > score_p1:
                return 2
            else:
                return 0

# ---------------- Campaign orchestration ----------------
def campaign(screen, clock, W, H, player_names):
    """
    Start time is measured here; after campaign finishes, return a tuple:
      (completed_bool, winner_id, elapsed_seconds)
    """
    ok = show_quadrinhos_sequence(screen, clock, W, H, INTRO_QUADRINHOS, duration_ms=QUADRINHO_DURATION_MS)
    if not ok: return (False, None, 0.0)
    start_ticks = pygame.time.get_ticks()
    res1 = run_boss1(screen, clock, W, H)
    if not res1: return (False, None, 0.0)
    res2 = run_boss2(screen, clock, W, H)
    if not res2: return (False, None, 0.0)
    winner_final = run_faroeste(screen, clock, W, H)  # returns 1,2,0 or None
    end_ticks = pygame.time.get_ticks()
    elapsed = (end_ticks - start_ticks) / 1000.0
    if winner_final is None:
        return (False, None, elapsed)
    return (True, winner_final, elapsed)

# ---------------- Main ----------------
def main():
    pygame.init(); pygame.mixer.init(); pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i); j.init()
    info = pygame.display.Info(); W,H = info.current_w, info.current_h
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    pygame.display.set_caption('Joguinho Integrado')
    clock = pygame.time.Clock()
    while True:
        entrar = menu(screen, clock, W, H)
        if not entrar:
            pygame.quit(); sys.exit(0)
        # ask for names
        names = get_player_names(screen, clock, W, H)
        if names is None:
            # cancelled -> back to menu
            continue
        # start campaign and measure time; names passed for ranking decision
        completed, winner_id, elapsed = campaign(screen, clock, W, H, player_names=names)
        if completed and winner_id in (1,2):
            winner_name = names[winner_id - 1]
            save_ranking_entry(winner_name, elapsed)
            # show a simple "congrats + ranking" screen
            font = pygame.font.Font(None, 56)
            small = pygame.font.Font(None, 36)
            showing = True
            show_time_str = f"{int(elapsed)//60}:{int(elapsed)%60:02d}.{int((elapsed-int(elapsed))*1000):03d}"
            message = f"Parabéns {winner_name}! Tempo: {show_time_str}"
            t0 = pygame.time.get_ticks()
            while showing:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit(); sys.exit(0)
                    if ev.type == pygame.KEYDOWN:
                        showing = False
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        showing = False
                    if ev.type == pygame.JOYBUTTONDOWN and ev.button in (JOYSTICK_SKIP_BUTTON_A, JOYSTICK_RANKING_BUTTON_Y):
                        showing = False
                screen.fill((8,8,12))
                tx = font.render(message, True, (220,220,120))
                screen.blit(tx, (W//2 - tx.get_width()//2, H//2 - 50))
                info = small.render("Pressione qualquer tecla ou Y/A para ver o ranking", True, (200,200,200))
                screen.blit(info, (W//2 - info.get_width()//2, H//2 + 30))
                pygame.display.flip()
                clock.tick(30)
            show_ranking_screen(screen, clock, W, H)
        else:
            # either aborted or tie/no winner -> show ranking anyway
            show_ranking_screen(screen, clock, W, H)

if __name__ == "__main__":
    main()
