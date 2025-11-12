# main.py  -- Jogo unificado: menu -> Boss1 -> Boss2 -> Fase final
import pygame
import os
import math
import sys
import random
from typing import Tuple, List, Optional

# ---------------- utilidades ----------------
def load_frames_from_folder(folder: str, keep_alpha=True) -> List[pygame.Surface]:
    frames = []
    if not folder or not os.path.exists(folder):
        return frames
    names = sorted(os.listdir(folder))
    for n in names:
        fp = os.path.join(folder, n)
        if os.path.isfile(fp):
            img = pygame.image.load(fp)
            img = img.convert_alpha() if keep_alpha else img.convert()
            frames.append(img)
    return frames

def load_and_scale(img_path, W, H, keep_aspect=True):
    if not os.path.exists(img_path):
        return None
    img = pygame.image.load(img_path).convert_alpha()
    if keep_aspect:
        iw, ih = img.get_size()
        scale = min(W/iw, H/ih)
        return pygame.transform.smoothscale(img, (int(iw*scale), int(ih*scale)))
    return pygame.transform.smoothscale(img, (W, H))

def show_quadrinho(screen, clock, W, H, img_path, ms=5000):
    if not os.path.exists(img_path):
        return
    img = pygame.image.load(img_path).convert_alpha()
    img = pygame.transform.smoothscale(img, (W, H))
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < ms:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                return
        screen.blit(img, (0,0))
        pygame.display.flip()
        clock.tick(60)

# ---------------- Player (usado nas fases do boss) ----------------
class Player:
    def __init__(self, x, ground_y, screen_height,
                 image_path=None, scale_height_ratio=0.3,
                 anim_root='assets/img/player'):
        self.ground_y = ground_y
        self.screen_height = screen_height
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_height * scale_height_ratio)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 64
        self.h = self.image.get_height() if self.image else 128
        self.rect = pygame.Rect(x, ground_y - self.h, self.w, self.h)

        # física
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.SPEED = 700.0
        self.JUMP_VELOCITY = -1500.0
        self.GRAVITY = 3000.0
        self.grounded = True

        # tiro
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.gun_offset = (self.w // 2, self.h // 2)

        self.shot_sound = None
        shot_path = os.path.join('assets', 'sounds', 'som6.mp3')
        if os.path.exists(shot_path):
            self.shot_sound = pygame.mixer.Sound(shot_path)
            self.shot_sound.set_volume(0.2)

        # vida / invuln / morte
        self.max_health = 8
        self.health = float(self.max_health)
        self.invuln_time = 0.8
        self._invuln_timer = 0.0
        self.dead = False

        # animação (opcional)
        self.anim_root = anim_root
        self.legs_walk = load_frames_from_folder(os.path.join(anim_root, 'legs', 'walk'))
        self.legs_idle = load_frames_from_folder(os.path.join(anim_root, 'legs', 'idle'))
        self.torso_anims = {
            'neutral': load_frames_from_folder(os.path.join(anim_root, 'torso', 'neutral')),
            'up': load_frames_from_folder(os.path.join(anim_root, 'torso', 'up')),
            'down': load_frames_from_folder(os.path.join(anim_root, 'torso', 'down')),
            'upleft': load_frames_from_folder(os.path.join(anim_root, 'torso', 'upleft')),
            'upright': load_frames_from_folder(os.path.join(anim_root, 'torso', 'upright')),
            'downleft': load_frames_from_folder(os.path.join(anim_root, 'torso', 'downleft')),
            'downright': load_frames_from_folder(os.path.join(anim_root, 'torso', 'downright')),
        }
        self.full_jump = load_frames_from_folder(os.path.join(anim_root, 'full', 'jump'))
        self.full_crouch = load_frames_from_folder(os.path.join(anim_root, 'full', 'crouch'))

        self.legs_index = 0
        self.torso_index = 0
        self.legs_timer = 0.0
        self.torso_timer = 0.0
        self.legs_fps = 12.0
        self.torso_fps = 12.0
        self.state = 'idle'
        self.facing_right = True
        self.aim = (1, 0)

        self._apply_anim_dims()

    def _apply_anim_dims(self):
        src = None
        if self.torso_anims.get('neutral'):
            lst = self.torso_anims['neutral']
            if lst:
                src = lst[0]
        if not src and self.image:
            src = self.image
        if not src and self.full_jump:
            src = self.full_jump[0]
        if src:
            self.w = src.get_width()
            self.h = src.get_height()
            self.rect.w = self.w
            self.rect.h = self.h
            self.rect.y = self.ground_y - self.h

    def handle_input_keyboard(self, keys, left_key, right_key, look_up_key, aim_keys):
        if self.dead:
            self.vel_x = 0.0
            return
        vx = 0.0
        if keys[left_key]:
            vx = -self.SPEED
        if keys[right_key]:
            vx = self.SPEED
        self.vel_x = vx
        if self.vel_x > 0:
            self.facing_right = True
        elif self.vel_x < 0:
            self.facing_right = False

        if look_up_key and keys[look_up_key]:
            self.aim = (0, -1)
        else:
            ax = 0; ay = 0
            for k, vec in aim_keys.items():
                if keys[k]:
                    ax += vec[0]
                    ay += vec[1]
            if ax != 0 or ay != 0:
                ax = max(-1, min(1, ax))
                ay = max(-1, min(1, ay))
                self.aim = (ax, ay)

    def try_jump(self):
        if self.dead:
            return
        if self.grounded:
            self.vel_y = self.JUMP_VELOCITY
            self.grounded = False

    def update(self, dt, screen_width):
        if self.dead:
            return
        self._time_since_last_shot += dt
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0.0
            self.grounded = True
        else:
            self.grounded = False

        if not self.grounded:
            self.state = 'jump'
        else:
            if abs(self.vel_x) > 1:
                self.state = 'walk'
            else:
                self.state = 'idle'

        self._update_legs_anim(dt)
        self._update_torso_anim(dt)

    def _update_legs_anim(self, dt):
        if self.state == 'walk' and self.legs_walk:
            self.legs_timer += dt
            frame_dur = 1.0 / self.legs_fps
            while self.legs_timer >= frame_dur:
                self.legs_timer -= frame_dur
                self.legs_index = (self.legs_index + 1) % len(self.legs_walk)
        else:
            self.legs_index = 0
            self.legs_timer = 0.0

    def _choose_torso_key(self):
        ax, ay = self.aim
        if not self.grounded:
            if ay < 0:
                return 'up'
            if ay > 0:
                return 'down'
            return 'neutral'
        if ax == 0 and ay == 0:
            return 'neutral'
        if ay < 0:
            return 'up' if ax == 0 else ('upleft' if ax < 0 else 'upright')
        if ay > 0:
            return 'down' if ax == 0 else ('downleft' if ax < 0 else 'downright')
        return 'neutral'

    def _update_torso_anim(self, dt):
        key = self._choose_torso_key()
        frames = self.torso_anims.get(key, [])
        if not frames:
            frames = self.torso_anims.get('neutral', [])
        if frames:
            self.torso_timer += dt
            frame_dur = 1.0 / self.torso_fps
            while self.torso_timer >= frame_dur:
                self.torso_timer -= frame_dur
                self.torso_index = (self.torso_index + 1) % len(frames)
        else:
            self.torso_index = 0
            self.torso_timer = 0.0

    def can_shoot(self) -> bool:
        return (not self.dead) and (self._time_since_last_shot >= self.fire_cooldown)

    def shoot(self, direction: Tuple[float, float], bullet_image=None) -> Optional["Bullet"]:
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w // 2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h // 2
        if direction == (0, -1):
            spawn_x = self.rect.centerx
            spawn_y = self.rect.top
        elif direction == (0, 1):
            spawn_x = self.rect.centerx
            spawn_y = self.rect.bottom
        b = Bullet(spawn_x, spawn_y, direction, image=bullet_image, owner=self)
        if self.shot_sound:
            self.shot_sound.play()
        return b

    def take_damage(self, amount: int):
        if self._invuln_timer > 0.0 or self.dead:
            return False
        self.health -= amount
        self._invuln_timer = self.invuln_time
        if self.health <= 0:
            self.die()
        return True

    def die(self):
        if self.dead:
            return
        self.dead = True

    def is_alive(self) -> bool:
        return (self.health > 0) and (not self.dead)

    def draw(self, surface):
        if self.dead:
            return
        # simple draw (image or rect)
        if self.image:
            frame = self.image if self.facing_right else pygame.transform.flip(self.image, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200,30,30), self.rect)
        # health bar
        bar_w = max(40, self.w)
        bar_h = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - (bar_h + 6)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30,30,50), bg_rect)
        hp_ratio = max(0.0, min(1.0, float(self.health) / float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        if hasattr(self, "_invuln_timer") and self._invuln_timer > 0.0:
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                fill_color = (120,180,255)
            else:
                fill_color = (80,130,220)
        else:
            fill_color = (40,140,255)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, fill_rect)
        pygame.draw.rect(surface, (200,200,220), bg_rect, 1)

# ---------------- Bullet (usado nas fases do boss) ----------------
class Bullet:
    SPEED = 900.0
    RADIUS = 6
    LIFETIME = 3.5

    def __init__(self, x, y, direction: Tuple[float, float], image: pygame.Surface = None, owner: Optional[object] = None):
        self.x = float(x)
        self.y = float(y)
        dx, dy = direction
        if dx == 0 and dy == 0:
            dx = 1.0
        length = math.hypot(dx, dy) or 1.0
        self.dir_x = dx / length
        self.dir_y = dy / length
        self.speed = Bullet.SPEED
        self.radius = Bullet.RADIUS
        self.life = Bullet.LIFETIME
        self.alive = True
        self.image = image
        self.owner = owner

        if owner == 'boss' or getattr(owner, '__class__', None).__name__ == 'Boss':
            self.color = (0, 220, 60)
            self.radius = 8
            self.speed = 300.0
        else:
            self.color = (255, 105, 180)
            self.radius = 6
            self.speed = 700.0

    def update(self, dt, screen_w, screen_h):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
        if self.x < -50 or self.x > screen_w + 50 or self.y < -50 or self.y > screen_h + 50:
            self.alive = False

    def draw(self, surface):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def collides_rect(self, rect) -> bool:
        closest_x = max(rect.left, min(int(self.x), rect.right))
        closest_y = max(rect.top, min(int(self.y), rect.bottom))
        dx = int(self.x) - closest_x
        dy = int(self.y) - closest_y
        return (dx*dx + dy*dy) <= (self.radius * self.radius)

# ---------------- SlimePatch ----------------
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

    def collides_player(self, player: Player) -> bool:
        if not player or player.dead:
            return False
        return self.rect.colliderect(player.rect)

    def draw(self, surface):
        surface.blit(self.surface, (self.rect.x, self.rect.y))

# ---------------- Boss 1 (gosma) ----------------
class Boss1:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, scale_height_ratio=0.35, bullet_image_path=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * scale_height_ratio)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 200
        self.h = self.image.get_height() if self.image else 150
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.speed = 140.0
        self.direction = 1
        self.patrol_min_x = 50
        self.patrol_max_x = screen_w - 50 - self.w
        self.bob_amplitude = 10.0
        self.bob_frequency = 0.6
        self._time = 0.0
        self.max_health = 120  # reduzido como você pediu
        self.health = float(self.max_health)

        self.slime_cooldown = 2.5
        self._time_since_last_slime = 0.0
        self.slime_width = int(self.w * 0.5)
        self.slime_height = 36
        self.slime_duration = 10.0
        self.slime_dps = 8.0

        self.bullet_image = None
        if bullet_image_path and os.path.exists(bullet_image_path):
            self.bullet_image = pygame.image.load(bullet_image_path).convert_alpha()

        # roar sound handled externally (main loop)
        self.speech_sounds = []
        speech7 = os.path.join('assets', 'sounds', 'som7.mp3')
        if os.path.exists(speech7):
            snd7 = pygame.mixer.Sound(speech7)
            snd7.set_volume(0.3)
            self.speech_sounds.append(snd7)
        self._speech_timer = 0.0

    def update(self, dt):
        self._time += dt
        self._time_since_last_slime += dt
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1
        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

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
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200,20,20), (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))

# ---------------- Boss 2 (nave / lasers) ----------------
class Boss2:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, scale_height_ratio=0.35, bullet_image_path=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * scale_height_ratio)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 200
        self.h = self.image.get_height() if self.image else 150
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.speed = 140.0
        self.direction = 1
        self.patrol_min_x = 50
        self.patrol_max_x = screen_w - 50 - self.w
        self.bob_amplitude = 30.0
        self.bob_frequency = 0.8
        self._time = 0.0
        self.max_health = 60
        self.health = float(self.max_health)

        self.hand_offsets = [int(self.w * 0.22), int(self.w * 0.78) - 12]
        self.hand_bullet_cooldowns = [1.2, 1.2]
        self._time_since_last_bullet = [0.0 for _ in self.hand_offsets]
        self.hand_laser_cooldowns = [6.0, 6.0]
        self._time_since_last_laser = [0.0 for _ in self.hand_offsets]
        self.laser_width = 120
        self.laser_height = int(screen_h * 0.55)
        self.laser_duration = 1.2
        self.laser_damage_per_second = 3.0

        self.bullet_image = None
        if bullet_image_path and os.path.exists(bullet_image_path):
            self.bullet_image = pygame.image.load(bullet_image_path).convert_alpha()

        # speech
        self.speech_sounds = []
        speech7 = os.path.join('assets', 'sounds', 'som7.mp3')
        speech8 = os.path.join('assets', 'sounds', 'som8.mp3')
        if os.path.exists(speech7):
            snd7 = pygame.mixer.Sound(speech7); snd7.set_volume(0.3); self.speech_sounds.append(snd7)
        if os.path.exists(speech8):
            snd8 = pygame.mixer.Sound(speech8); snd8.set_volume(0.3); self.speech_sounds.append(snd8)

        self.speech_interval_base = 4.0
        self._speech_timer = 0.0
        self._speech_index = 0

    def update(self, dt):
        self._time += dt
        if self.speech_sounds and self.health > 0:
            self._speech_timer += dt
            current_interval = 10
            if self._speech_timer >= current_interval:
                snd = self.speech_sounds[self._speech_index % len(self.speech_sounds)]
                snd.play()
                self._speech_index += 1
                self._speech_timer = 0.0

        for i in range(len(self._time_since_last_bullet)):
            self._time_since_last_bullet[i] += dt
        for i in range(len(self._time_since_last_laser)):
            self._time_since_last_laser[i] += dt
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1
        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

    def try_shoot_hands_at_players(self, player_centers: List[Tuple[int,int]]):
        bullets = []
        if not player_centers:
            return bullets
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_bullet[i] < self.hand_bullet_cooldowns[i]:
                continue
            spawn_x = int(self.rect.x + offset)
            spawn_y = draw_y + self.h - 10
            best = None; best_dist = None
            for c in player_centers:
                dx = c[0] - spawn_x
                dy = c[1] - spawn_y
                d = dx*dx + dy*dy
                if best is None or d < best_dist:
                    best = (dx, dy); best_dist = d
            if best is None:
                continue
            dx, dy = best
            length = math.hypot(dx, dy) or 1.0
            b = Bullet(spawn_x, spawn_y, (dx/length, dy/length), image=self.bullet_image, owner='boss')
            bullets.append(b)
            self._time_since_last_bullet[i] = 0.0
        return bullets

    def try_fire_lasers(self):
        lasers = []
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_laser[i] < self.hand_laser_cooldowns[i]:
                continue
            laser = BossLaser(self, offset - (self.laser_width // 2) + 6,
                              self.laser_width, self.laser_height,
                              duration=self.laser_duration,
                              damage_per_second=self.laser_damage_per_second)
            lasers.append(laser)
            self._time_since_last_laser[i] = 0.0
        return lasers

    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (80,80,80), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200,20,20), (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))

# ---------------- BossLaser for Boss2 ----------------
class BossLaser:
    def __init__(self, boss_ref, offset_x, width, height, duration=1.0, damage_per_second=2.0):
        self.boss = boss_ref
        self.offset_x = offset_x
        self.w = width
        self.h = height
        self.duration = duration
        self._time = 0.0
        self.alive = True
        self.damage_per_second = damage_per_second
        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.surface.fill((255,80,80,160))

    def update(self, dt):
        self._time += dt
        if self._time >= self.duration:
            self.alive = False

    def current_rect(self):
        draw_y = int(self.boss.rect.y + getattr(self.boss, '_y_offset', 0))
        x = int(self.boss.rect.x + self.offset_x)
        y = draw_y + self.boss.h
        return pygame.Rect(x, y, self.w, self.h)

    def draw(self, surface):
        r = self.current_rect()
        surface.blit(self.surface, (r.x, r.y))

    def collides_rect(self, rect):
        return self.current_rect().colliderect(rect)

    def damage_amount_this_frame(self, dt):
        return self.damage_per_second * dt

# ------------------ Menu (adaptado do seu jogo.py) ------------------
BUTTON_BG = (120, 40, 40)
BUTTON_HOVER_BG = (70, 70, 120)
BUTTON_BORDER = (255, 255, 255)
BUTTON_TEXT = (245, 245, 245)
MENU_BG_PATH = os.path.join('assets', 'img', 'inicio.png')
TUTORIAL_PATHS = [os.path.join('assets', 'img', 'tutorial1.png'),
                  os.path.join('assets', 'img', 'tutorial2.png')]
MENU_MUSIC_PATH = os.path.join('assets', 'sounds', 'som9.mp3')

def draw_button(surface, rect, text, font, hovered=False,
                bg_color=BUTTON_BG, hover_bg=BUTTON_HOVER_BG,
                border_color=BUTTON_BORDER, text_color=BUTTON_TEXT):
    bg_used = hover_bg if hovered else bg_color
    pygame.draw.rect(surface, bg_used, rect, border_radius=12)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=12)
    txt = font.render(text, True, text_color)
    tx = rect.x + (rect.w - txt.get_width()) // 2
    ty = rect.y + (rect.h - txt.get_height()) // 2
    surface.blit(txt, (tx, ty))

def show_tutorial_interactive(screen, clock, W, H, image_paths):
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
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    index = min(index + 1, len(imgs)-1)
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    index = max(index - 1, 0)
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
        page_text = small_font.render(f"{index+1} / {len(imgs)}  (← →)  ESC: fechar", True, (200,200,220))
        screen.blit(page_text, ((W-page_text.get_width())//2, int(H*0.9)))
        pygame.display.flip()

def menu(screen, clock, W, H):
    bg = load_and_scale(MENU_BG_PATH, W, H, keep_aspect=False)
    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 52)
    btn_w, btn_h = 420, 86
    btn_play = pygame.Rect((W//2 - btn_w//2, int(H*0.5 - btn_h - 10), btn_w, btn_h))
    btn_tutorial = pygame.Rect((W//2 - btn_w//2, int(H*0.5 + 10), btn_w, btn_h))

    if os.path.exists(MENU_MUSIC_PATH):
        pygame.mixer.music.load(MENU_MUSIC_PATH)
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)

    running = True
    start_game = False
    while running:
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
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
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((18, 18, 40))
        draw_button(screen, btn_play, "JOGAR", btn_font, hovered=btn_play.collidepoint(mx, my))
        draw_button(screen, btn_tutorial, "TUTORIAL", btn_font, hovered=btn_tutorial.collidepoint(mx, my))
        pygame.display.flip()
        clock.tick(60)
    pygame.mixer.music.fadeout(500)
    return start_game

# ---------------- Run First Boss (Boss1) ----------------
def run_boss1(screen, clock, W, H):
    # setup
    fundo_path = os.path.join('assets', 'img', 'fundo2.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

    ground_y = H
    player1 = Player(W//4, ground_y, H,
                     image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                     anim_root=os.path.join('assets', 'img', 'player1'))
    player2 = Player(3*W//4, ground_y, H,
                     image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                     anim_root=os.path.join('assets', 'img', 'player2'))
    boss = Boss1(W//2 - 200, 60, W, H, image_path=os.path.join('assets', 'img', 'boss2.png'),
                 bullet_image_path=None)

    # audio: background som10 + roar som11 every 10s
    bg_music_path = os.path.join('assets', 'sounds', 'som10.mp3')
    roar_path = os.path.join('assets', 'sounds', 'som11.mp3')
    bg_music_loaded = False
    roar_sound = None
    if os.path.exists(bg_music_path):
        pygame.mixer.music.load(bg_music_path)
        pygame.mixer.music.set_volume(0.18)
        pygame.mixer.music.play(-1)
        bg_music_loaded = True
    if os.path.exists(roar_path):
        roar_sound = pygame.mixer.Sound(roar_path)
        roar_sound.set_volume(0.55)

    ROAR_INTERVAL = 10.0
    _roar_timer = 0.0

    clock_fps = 60
    FPS = 60
    font = pygame.font.Font(None, 24)
    bullets = []
    slime_patches: List[SlimePatch] = []
    all_players = [player1, player2]

    # key mapping
    P1_LEFT = pygame.K_a; P1_RIGHT = pygame.K_d; P1_LOOK_UP = pygame.K_o; P1_JUMP = pygame.K_w
    P1_AIMS = {pygame.K_i:(0,-1), pygame.K_k:(0,1), pygame.K_j:(-1,0), pygame.K_l:(1,0)}
    P2_LEFT = pygame.K_LEFT; P2_RIGHT = pygame.K_RIGHT; P2_LOOK_UP = pygame.K_RCTRL; P2_JUMP = pygame.K_RSHIFT
    P2_AIMS = {pygame.K_u:(0,-1), pygame.K_m:(0,1), pygame.K_h:(-1,0), pygame.K_l:(1,0)}

    game = True
    while game:
        dt = clock.tick(FPS) / 1000.0

        # roar timer increment while boss alive
        if boss and boss.health > 0:
            _roar_timer += dt
        if _roar_timer >= ROAR_INTERVAL and boss and boss.health > 0:
            if roar_sound:
                roar_sound.play()
            _roar_timer = 0.0

        # input
        keys = pygame.key.get_pressed()
        player1.handle_input_keyboard(keys, P1_LEFT, P1_RIGHT, P1_LOOK_UP, P1_AIMS)
        player2.handle_input_keyboard(keys, P2_LEFT, P2_RIGHT, P2_LOOK_UP, P2_AIMS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if ev.key == P1_JUMP: player1.try_jump()
                if ev.key == P2_JUMP: player2.try_jump()
                if ev.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player1.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                    if b: bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player2.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                    if b: bullets.append(b)

        # updates
        player1.update(dt, W); player2.update(dt, W); boss.update(dt)
        patch = boss.try_drop_slime()
        if patch: slime_patches.append(patch)

        bullets = [b for b in bullets if b.alive]
        for b in bullets:
            b.update(dt, W, H)
        for s in slime_patches:
            s.update(dt)

        # collisions: player bullets -> boss
        for b in bullets[:]:
            if b.collides_rect(boss.rect):
                boss.health -= 1
                b.alive = False
                bullets.remove(b)  # removed try/except as requested

        # slime damage
        for s in slime_patches:
            for p in all_players:
                if p.is_alive() and s.collides_player(p):
                    dmg = s.dps * dt
                    p.health = max(0.0, p.health - dmg)
                    if p.health <= 0 and not p.dead:
                        p.die()

        # victory
        if boss.health <= 0:
            pygame.mixer.music.fadeout(500)
            return True  # boss defeated -> next phase

        if not any(p.is_alive() for p in all_players):
            # both players dead -> game over
            return False

        # draw
        if fundo_image:
            screen.blit(fundo_image, (0, 0))
        else:
            screen.fill((10,10,12))
        boss.draw(screen)
        for s in slime_patches: s.draw(screen)
        for b in bullets: b.draw(screen)
        player1.draw(screen); player2.draw(screen)
        hud = font.render(f"P1 HP: {int(player1.health)}   P2 HP: {int(player2.health)}   Boss: {int(boss.health)}", True, (255,255,255))
        screen.blit(hud, (12,12))
        pygame.display.flip()

# ---------------- Run Second Boss (Boss2) ----------------
def run_boss2(screen, clock, W, H):
    fundo_path = os.path.join('assets', 'img', 'fundo_boss.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

    player1 = Player(W//4, H, H,
                     image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                     anim_root=os.path.join('assets', 'img', 'player1'))
    player2 = Player(3*W//4, H, H,
                     image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                     anim_root=os.path.join('assets', 'img', 'player2'))
    boss = Boss2(W//4, 80, W, H, image_path=os.path.join('assets', 'img', 'nave boss.png'),
                 bullet_image_path=os.path.join('assets', 'img', 'bala.png'))

    clock_fps = 60
    FPS = 60
    bullets = []
    boss_bullets = []
    boss_lasers = []
    all_players = [player1, player2]
    font = pygame.font.Font(None, 24)

    P1_LEFT = pygame.K_a; P1_RIGHT = pygame.K_d; P1_LOOK_UP = pygame.K_o; P1_JUMP = pygame.K_w
    P1_AIMS = {pygame.K_i:(0,-1), pygame.K_k:(0,1), pygame.K_j:(-1,0), pygame.K_l:(1,0)}
    P2_LEFT = pygame.K_LEFT; P2_RIGHT = pygame.K_RIGHT; P2_LOOK_UP = pygame.K_RCTRL; P2_JUMP = pygame.K_RSHIFT
    P2_AIMS = {pygame.K_u:(0,-1), pygame.K_m:(0,1), pygame.K_h:(-1,0), pygame.K_l:(1,0)}

    # optional music for boss2 (you can reuse som10 or som4)
    music2 = os.path.join('assets', 'sounds', 'som4.mp3')
    if os.path.exists(music2):
        pygame.mixer.music.load(music2)
        pygame.mixer.music.set_volume(0.18)
        pygame.mixer.music.play(-1)

    game = True
    while game:
        dt = clock.tick(FPS) / 1000.0

        # input
        keys = pygame.key.get_pressed()
        player1.handle_input_keyboard(keys, P1_LEFT, P1_RIGHT, P1_LOOK_UP, P1_AIMS)
        player2.handle_input_keyboard(keys, P2_LEFT, P2_RIGHT, P2_LOOK_UP, P2_AIMS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if ev.key == P1_JUMP: player1.try_jump()
                if ev.key == P2_JUMP: player2.try_jump()
                if ev.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player1.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                    if b: bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player2.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                    if b: bullets.append(b)

        # updates
        player1.update(dt, W); player2.update(dt, W); boss.update(dt)
        player_centers = [p.rect.center for p in all_players if p.is_alive()]
        if player_centers:
            boss_bullets.extend(boss.try_shoot_hands_at_players(player_centers))
        boss_lasers.extend(boss.try_fire_lasers())

        bullets = [b for b in bullets if b.alive]
        boss_bullets = [b for b in boss_bullets if b.alive]
        boss_lasers = [l for l in boss_lasers if l.alive]
        for b in bullets: b.update(dt, W, H)
        for b in boss_bullets: b.update(dt, W, H)
        for l in boss_lasers: l.update(dt)

        # collisions: player bullets -> boss
        for b in bullets[:]:
            if b.collides_rect(boss.rect):
                boss.health -= 1
                b.alive = False
                bullets.remove(b)

        # boss bullets -> players
        for b in boss_bullets[:]:
            for p in all_players:
                if p.is_alive() and b.collides_rect(p.rect):
                    if p.take_damage(1):
                        b.alive = False
                        boss_bullets.remove(b)
                        break

        # boss lasers -> players
        for l in boss_lasers:
            for p in all_players:
                if p.is_alive() and l.collides_rect(p.rect):
                    damage = l.damage_amount_this_frame(dt)
                    if p.health > 0:
                        p.health = max(0, p.health - damage)
                        if p.health == 0:
                            p.die()

        # victory
        if boss.health <= 0:
            pygame.mixer.music.fadeout(500)
            return True
        if not any(p.is_alive() for p in all_players):
            return False

        # draw
        if fundo_image:
            screen.blit(fundo_image, (0,0))
        else:
            screen.fill((0,0,0))
        boss.draw(screen)
        for l in boss_lasers: l.draw(screen)
        for b in bullets: b.draw(screen)
        for b in boss_bullets: b.draw(screen)
        player1.draw(screen); player2.draw(screen)
        pygame.display.flip()

# ---------------- Fase Final (Duelo Faroeste) ----------------
def run_fase_final(screen, clock, W, H):
    # uses your final stage code but simplified to fit here
    # load assets
    fundo_path = os.path.join('assets', 'img', 'faroeste.png')
    if os.path.exists(fundo_path):
        fundo = pygame.image.load(fundo_path).convert_alpha()
        fundo = pygame.transform.smoothscale(fundo, (W, H))
    else:
        fundo = pygame.Surface((W,H)); fundo.fill((0,0,0))

    clock = pygame.time.Clock()
    FPS = 60
    # sonido
    try:
        pygame.mixer.music.load(os.path.join('assets', 'sounds', 'som1.mp3'))
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)
    except Exception:
        pass
    som_tiro_path = os.path.join('assets', 'sounds', 'som2.mp3')
    som_tiro = None
    if os.path.exists(som_tiro_path):
        som_tiro = pygame.mixer.Sound(som_tiro_path); som_tiro.set_volume(0.6)

    # minimal duel loop (keeps original behavior)
    score_p1 = 0; score_p2 = 0
    BEST_OF = 5
    state = "preparar"
    state_time = pygame.time.get_ticks()
    waiting_target_time = None
    winner_this_round = None
    last_shot_time_p1 = -9999
    last_shot_time_p2 = -9999
    PREP_TIME = 1.0; MIN_RANDOM_DELAY=1.0; MAX_RANDOM_DELAY=3.0
    FLASH_DURATION_MS = 140; RECOIL_DURATION_MS = 140
    BUTTON_A = 0

    # positions like your original
    GUN_TIP_POS_P1 = (420, 700); GUN_TIP_POS_P2 = (1100, 700)
    font = pygame.font.Font(os.path.join('assets', 'font', 'escrita1.ttf') if os.path.exists(os.path.join('assets','font','escrita1.ttf')) else None, 56)
    font2 = pygame.font.Font(os.path.join('assets', 'font', 'escrita2.ttf') if os.path.exists(os.path.join('assets','font','escrita2.ttf')) else None, 70)
    small_font = pygame.font.Font(os.path.join('assets','font','escrita1.ttf') if os.path.exists(os.path.join('assets','font','escrita1.ttf')) else None, 36)
    small_font2 = pygame.font.Font(os.path.join('assets','font','escrita2.ttf') if os.path.exists(os.path.join('assets','font','escrita2.ttf')) else None, 30)

    # simple input mapping: keyboard X and L (like original)
    while True:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit(0)
        keys = pygame.key.get_pressed()
        if state == "preparar" and now - state_time >= PREP_TIME*1000:
            state = "apontar"; state_time = pygame.time.get_ticks(); waiting_target_time = None
        elif state == "apontar" and waiting_target_time is None:
            waiting_target_time = now + int(random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY) * 1000)
        elif state == "apontar" and now >= waiting_target_time:
            state = "ja"; state_time = pygame.time.get_ticks()
        elif state == "ja" and now - state_time >= 3000 and winner_this_round is None:
            winner_this_round = 0; state = "resultado"; state_time = now
        elif state == "resultado" and now - state_time >= 1000:
            # end condition simplified: break to exit final
            if score_p1 > score_p2:
                msg = "JOGADOR 1 VENCEU O JOGO!"
            elif score_p2 > score_p1:
                msg = "JOGADOR 2 VENCEU O JOGO!"
            else:
                msg = "EMPATE!"
            # show result for 3s then return to menu (end)
            screen.blit(fundo, (0,0))
            t = font.render(msg, True, (255,0,0)) if font else None
            if t: screen.blit(t, (W//2 - t.get_width()//2, H//2 - 50))
            pygame.display.flip()
            pygame.time.delay(3000)
            return

        # input shooting
        if state == "ja" and winner_this_round is None:
            if keys[pygame.K_x]:
                winner_this_round = 1; score_p1 += 1; state = "resultado"; state_time = now
                if som_tiro: som_tiro.play()
            elif keys[pygame.K_l]:
                winner_this_round = 2; score_p2 += 1; state = "resultado"; state_time = now
                if som_tiro: som_tiro.play()
        elif state in ("preparar", "apontar") and winner_this_round is None:
            if keys[pygame.K_x]:
                winner_this_round = 2; score_p2 += 1; state = "resultado"; state_time = now
            elif keys[pygame.K_l]:
                winner_this_round = 1; score_p1 += 1; state = "resultado"; state_time = now

        # draw
        screen.blit(fundo, (0,0))
        title = font2.render('DUELO', True, (255,255,255)) if font2 else None
        if title: screen.blit(title, (W//2 - title.get_width()//2, 20))
        if state == "preparar":
            t = font.render("PREPARAR...", True, (255,255,255)) if font else None
            if t: screen.blit(t, (W//2 - t.get_width()//2, H//2 - 80))
        elif state == "apontar":
            t = font.render("APONTAR...", True, (255,255,255)) if font else None
            if t: screen.blit(t, (W//2 - t.get_width()//2, H//2 - 80))
        elif state == "ja":
            t = font.render("JA!", True, (10,255,10)) if font else None
            if t: screen.blit(t, (W//2 - t.get_width()//2, H//2 - 80))
        elif state == "resultado":
            if winner_this_round == 1:
                round_msg = "JOGADOR 1 VENCEU A RODADA!"
            elif winner_this_round == 2:
                round_msg = "JOGADOR 2 VENCEU A RODADA!"
            else:
                round_msg = "EMPATE!"
            t = font.render(round_msg, True, (255,255,255)) if font else None
            if t: screen.blit(t, (W//2 - t.get_width()//2, H//2 - 100))
            score_msg = f"{score_p1}  x  {score_p2}"
            s = font2.render(score_msg, True, (0,255,0)) if font2 else None
            if s: screen.blit(s, (W//2 - s.get_width()//2, H//2))

        pygame.display.flip()
        clock.tick(FPS)

# ---------------- Main: inicialização e fluxo ----------------
def main():
    pygame.init()
    pygame.mixer.init()
    # screen size (use a common resolution)
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Jogo Unificado - Menu -> Boss1 -> Boss2 -> Final")
    W, H = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()

    # show menu
    entrar_menu = menu(screen, clock, W, H)
    if not entrar_menu:
        pygame.quit(); sys.exit(0)

    # Run Boss1
    boss1_ok = run_boss1(screen, clock, W, H)
    if not boss1_ok:
        # game over (players died) -> exit
        print("Game Over after Boss1")
        pygame.quit(); sys.exit(0)

    # show quadrinho after boss1
    show_quadrinho(screen, clock, W, H, os.path.join('assets','img','quadrinho3.png'), ms=5000)

    # Run Boss2
    boss2_ok = run_boss2(screen, clock, W, H)
    if not boss2_ok:
        print("Game Over after Boss2")
        pygame.quit(); sys.exit(0)

    # show quadrinho after boss2
    show_quadrinho(screen, clock, W, H, os.path.join('assets','img','quadrinho4.png'), ms=5000)

    # run final phase
    run_fase_final(screen, clock, W, H)

    # end
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
