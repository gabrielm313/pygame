import pygame
import os
import math
import sys
import subprocess
from typing import Tuple, List, Optional

# ---------------- Utilidade: carregar frames de uma pasta ----------------
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

# ---------------- Player (animação legs+torso/full) ----------------
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

        # animação
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
        """
        Cria e retorna uma Bullet com owner=self.
        Retorna None se não puder atirar.
        """
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w // 2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h // 2
        
        # Ajuste o ponto de disparo com base na direção de mira
        if direction == (0, -1):  # Mirando para cima
            spawn_x = self.rect.centerx
            spawn_y = self.rect.top
        elif direction == (0, 1): # Mirando para baixo
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
        print(f"Player hit! HP: {self.health}/{self.max_health}")
        if self.health <= 0:
            self.die()
        return True

    def die(self):
        if self.dead:
            return
        self.dead = True
        print("Player morreu!")

    def is_alive(self) -> bool:
        return (self.health > 0) and (not self.dead)

    def draw(self, surface):
        if self.dead:
            return

        # --- desenho do player (jump/full ou legs+torso) ---
        if self.state == 'jump' and self.full_jump:
            frame = self.full_jump[0]
            frame_to_draw = frame
            if not self.facing_right:
                frame_to_draw = pygame.transform.flip(frame, True, False)
            surface.blit(frame_to_draw, (self.rect.x, self.rect.y))
        else:
            legs_frames = self.legs_walk if (self.state == 'walk' and self.legs_walk) else (self.legs_idle if self.legs_idle else [])
            if legs_frames:
                leg_frame = legs_frames[self.legs_index % len(legs_frames)]
                if not self.facing_right:
                    leg_frame = pygame.transform.flip(leg_frame, True, False)
                surface.blit(leg_frame, (self.rect.x, self.rect.y))

            key = self._choose_torso_key()
            torso_frames = self.torso_anims.get(key) or self.torso_anims.get('neutral') or []
            if torso_frames:
                torso_frame = torso_frames[self.torso_index % len(torso_frames)]
                if not self.facing_right:
                    torso_frame = pygame.transform.flip(torso_frame, True, False)
                surface.blit(torso_frame, (self.rect.x, self.rect.y))
            else:
                if self.image:
                    frame = self.image
                    if not self.facing_right:
                        frame = pygame.transform.flip(frame, True, False)
                    surface.blit(frame, (self.rect.x, self.rect.y))
                else:
                    pygame.draw.rect(surface, (200, 30, 30), self.rect)

        # --- barra de vida azul acima da cabeça ---
        bar_w = max(40, self.w)
        bar_h = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - (bar_h + 6)

        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 30, 50), bg_rect)

        hp_ratio = max(0.0, min(1.0, float(self.health) / float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

        if hasattr(self, "_invuln_timer") and self._invuln_timer > 0.0:
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                fill_color = (120, 180, 255)
            else:
                fill_color = (80, 130, 220)
        else:
            fill_color = (40, 140, 255)

        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, fill_rect)

        pygame.draw.rect(surface, (200, 200, 220), bg_rect, 1)

# ---------------- Bullet (com owner) ----------------
class Bullet:
    SPEED = 900.0
    RADIUS = 6  # reduzido para 6 por padrão (player)
    COLOR = (255, 105, 180)  # rosa por padrão para player
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

        # choose color based on owner
        # owner == 'boss' -> boss color (green)
        # owner is Boss instance -> boss color
        # owner is Player -> player pink
        if owner == 'boss' or getattr(owner, '__class__', None).__name__ == 'Boss':
            self.color = (0, 220, 60)  # verde para boss
            # make bullet slightly smaller than before but still distinct
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

# ---------------- SlimePatch (gosma no chão) ----------------
class SlimePatch:
    def __init__(self, x, y, width, height, dps=6.0, duration=8.0):
        # x,y in world coords -> patch rectangle (top-left)
        self.rect = pygame.Rect(int(x), int(y), int(width), int(height))
        self.dps = float(dps)   # dano por segundo
        self.duration = float(duration)
        self.time = 0.0
        self.alive = True
        # surface para desenhar (semi-transparente verde)
        self.surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.surface.fill((20, 200, 40, 130))

    def update(self, dt):
        self.time += dt
        if self.time >= self.duration:
            self.alive = False

    def collides_player(self, player: Player) -> bool:
        # considera jogador "em cima" se o retângulo do jogador intersecta a parte superior da gosma
        if not player or player.dead:
            return False
        # usamos colisão AABB simples
        return self.rect.colliderect(player.rect)

    def draw(self, surface):
        surface.blit(self.surface, (self.rect.x, self.rect.y))

# ---------------- Boss (agora solta gosma) ----------------
class Boss:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, scale_height_ratio=0.35,
                 bullet_image_path=None):
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
        self.max_health = 120  # reduzido para 120
        self.health = float(self.max_health)

        # slime drop (boss mechanic)
        self.slime_cooldown = 2.5   # drop every 2.5s (tune)
        self._time_since_last_slime = 0.0
        self.slime_width = int(self.w * 0.5)
        self.slime_height = 36
        self.slime_duration = 10.0
        self.slime_dps = 8.0

        # bullet image kept for compatibility (players might reuse)
        self.bullet_image = None
        if bullet_image_path and os.path.exists(bullet_image_path):
            self.bullet_image = pygame.image.load(bullet_image_path).convert_alpha()

        # voice / speech (optional)
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

        # movement horizontal patrol
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1
        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

    def try_drop_slime(self):
        """
        Retorna um SlimePatch se o boss puder dropar agora, caso contrario None.
        Ajuste: spawn_y agora é colado ao chão (self.screen_h) para que a gosma fique no chão.
        """
        if self._time_since_last_slime < self.slime_cooldown:
            return None
        # spawn slime centered at boss feet but aligned to ground (bottom of screen)
        spawn_x = int(self.rect.centerx - self.slime_width // 2)
        # colocar gosma no chão (top da gosma = ground_y - slime_height)
        spawn_y = int(self.screen_h - self.slime_height)
        patch = SlimePatch(spawn_x, spawn_y, self.slime_width, self.slime_height,
                           dps=self.slime_dps, duration=self.slime_duration)
        self._time_since_last_slime = 0.0
        return patch

    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        # health bar
        pygame.draw.rect(surface, (40, 40, 40), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20), (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))

# ------------------ suporte multi-mapeamento por joystick ------------------
AXIS_DEADZONE = 0.25

GAMEPAD_MAPS = [
    {
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "trigger_axis": 5,
    },
    {
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "trigger_axis": 5,
    }
]

joysticks: List[pygame.joystick.Joystick] = []
joystick_instance_ids: List[int] = []
joystick_to_player_index = {}

def get_map_for_joystick_physical_index(i: int) -> dict:
    if i is None:
        return GAMEPAD_MAPS[0]
    if i < len(GAMEPAD_MAPS):
        return GAMEPAD_MAPS[i]
    return GAMEPAD_MAPS[0]

def init_joysticks():
    global joysticks, joystick_instance_ids, joystick_to_player_index
    pygame.joystick.init()
    joysticks = []
    joystick_instance_ids = []
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        instance_id = j.get_instance_id() if hasattr(j, "get_instance_id") else i
        joysticks.append(j)
        joystick_instance_ids.append(instance_id)
        print(f"Joystick {i}: name='{j.get_name()}' instance_id={instance_id} axes={j.get_numaxes()} buttons={j.get_numbuttons()} hats={j.get_numhats()}")
    joystick_to_player_index = {i: i for i in range(len(joysticks))}
    return joysticks, joystick_instance_ids

def read_axis_with_deadzone(joy, axis_idx):
    if axis_idx is None or axis_idx < 0 or axis_idx >= joy.get_numaxes():
        return 0.0
    val = joy.get_axis(axis_idx)
    if abs(val) < AXIS_DEADZONE:
        return 0.0
    return val

def handle_joystick_event(event, players_list, bullets_list):
    jid = getattr(event, "instance_id", getattr(event, "joy", None))
    player_index = None
    joy_physical_index = None
    if jid is not None:
        try:
            joy_physical_index = joystick_instance_ids.index(jid)
            player_index = joystick_to_player_index.get(joy_physical_index, None)
        except ValueError:
            player_index = None
            joy_physical_index = None

    if event.type == pygame.JOYBUTTONDOWN and player_index is not None and player_index < len(players_list):
        btn = event.button
        player = players_list[player_index]
        pad_map = get_map_for_joystick_physical_index(joy_physical_index)

        if btn == pad_map.get("button_jump"):
            player.try_jump()
            return

        hat_idx = pad_map.get("dpad_hat", 0)
        joy = joysticks[joy_physical_index] if (joy_physical_index is not None and joy_physical_index < len(joysticks)) else None
        if joy is not None and hat_idx is not None and joy.get_numhats() > hat_idx:
            hat = joy.get_hat(hat_idx)
            if hat != (0, 0):
                hx, hy = hat
                player.aim = (hx, -hy)
                return

    if event.type == pygame.JOYHATMOTION and player_index is not None and player_index < len(players_list):
        hat_x, hat_y = event.value
        players_list[player_index].aim = (hat_x, -hat_y)

def poll_joysticks(players_list, bullets_list, boss_bullet_image):
    for i, joy in enumerate(joysticks):
        player_idx = joystick_to_player_index.get(i, None)
        if player_idx is None or player_idx >= len(players_list):
            continue
        player = players_list[player_idx]
        pad_map = get_map_for_joystick_physical_index(i)

        move_ax = pad_map.get("move_axis_x", None)
        if move_ax is not None:
            ax = read_axis_with_deadzone(joy, move_ax)
            player.vel_x = ax * player.SPEED

        if player.vel_x > 0:
            player.facing_right = True
        elif player.vel_x < 0:
            player.facing_right = False

        aim_ax = pad_map.get("aim_axis_x", None)
        aim_ay = pad_map.get("aim_axis_y", None)
        if aim_ax is not None and aim_ay is not None and joy.get_numaxes() > max(aim_ax, aim_ay):
            raw_ax = joy.get_axis(aim_ax)
            raw_ay = joy.get_axis(aim_ay)
            dead_ax = raw_ax if abs(raw_ax) >= AXIS_DEADZONE else 0.0
            dead_ay = raw_ay if abs(raw_ay) >= AXIS_DEADZONE else 0.0
            if dead_ax != 0.0 or dead_ay != 0.0:
                length = math.hypot(dead_ax, dead_ay) or 1.0
                nx = dead_ax / length
                ny = dead_ay / length
                player.aim = (nx, ny)
        else:
            hat_idx = pad_map.get("dpad_hat", None)
            if hat_idx is not None and joy.get_numhats() > hat_idx:
                hat = joy.get_hat(hat_idx)
                if hat != (0, 0):
                    player.aim = (hat[0], -hat[1])

        trigger_ax = pad_map.get("trigger_axis", None)
        if trigger_ax is not None and trigger_ax < joy.get_numaxes():
            val = joy.get_axis(trigger_ax)
            # Gatilho pressionado (valor positivo > 0.5)
            if val > 0.5:
                dx, dy = player.aim
                # Se não estiver mirando (aim = (0,0)), atira na direção que o player está virado
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                length = math.hypot(dx, dy) or 1.0
                b = player.shoot((dx/length, dy/length), bullet_image=boss_bullet_image)
                if b:
                    bullets_list.append(b)

# ---------------- helper: mostrar imagens e abrir faroeste.py ----------------
def show_image_for(ms, img_path, screen, clock_ref, W, H):
    if not os.path.exists(img_path):
        return
    img = pygame.image.load(img_path).convert_alpha()
    img = pygame.transform.smoothscale(img, (W, H))
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < ms:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock_ref.tick(60)

def show_images_and_launch_next(img1_path, img2_path, screen, clock_ref, W, H,
                                 next_script='faroestejogo.py', ms_each=5000, fadeout_ms=1000):
    # Faz fadeout/stop da música (sem try/except)
    if pygame.mixer.get_init():
        if fadeout_ms and fadeout_ms > 0:
            pygame.mixer.music.fadeout(int(fadeout_ms))
        else:
            pygame.mixer.music.stop()

    # mostra a primeira imagem por ms_each ms (100% usando ia)
    if os.path.exists(img1_path):
        img = pygame.image.load(img1_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (W, H))
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < int(ms_each):
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
            screen.blit(img, (0, 0))
            pygame.display.flip()
            clock_ref.tick(60)

    # mostra a segunda imagem por ms_each ms (feito com chatgpt)
    if os.path.exists(img2_path):
        img = pygame.image.load(img2_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (W, H))
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < int(ms_each):
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
            screen.blit(img, (0, 0))
            pygame.display.flip()
            clock_ref.tick(60)

    # fecha o pygame e inicia o outro script
    pygame.display.quit()
    pygame.quit()
    next_game = os.path.join(os.path.dirname(__file__), next_script)
    
    # Verifica se o script existe
    if os.path.exists(next_game):
        print(f"Lançando o próximo jogo: {next_game}")
        subprocess.Popen([sys.executable, next_game])
    else:
        print(f"ERRO: Não foi possível encontrar o script: {next_game}")

    sys.exit(0)


# ---------------- Main game loop (feito com chat )----------------
pygame.init()
pygame.mixer.init()

# --- Som de fundo e rugido config ---
bg_music_path = os.path.join('assets', 'sounds', 'som10.mp3')   # tocar em loop
roar_path = os.path.join('assets', 'sounds', 'som11.mp3')       # tocar a cada 10s

bg_music_loaded = False
roar_sound = None
if os.path.exists(bg_music_path):
    pygame.mixer.music.load(bg_music_path)
    pygame.mixer.music.set_volume(0.18)
    pygame.mixer.music.play(-1)  # loop
    bg_music_loaded = True

if os.path.exists(roar_path):
    roar_sound = pygame.mixer.Sound(roar_path)
    roar_sound.set_volume(0.55)

# roar timer (em segundos)
ROAR_INTERVAL = 10.0
_roar_timer = 0.0

joysticks, joystick_instance_ids = init_joysticks()

window = pygame.display.set_mode((1280, 720))
pygame.display.set_caption('Boss Slime Duel - Gamepad multi (RT to fire)')
W, H = window.get_width(), window.get_height()

# fundo e boss conforme pedido: fundo2.png e boss2.png
fundo_image = None
fundo_path = os.path.join('assets', 'img', 'fundo2.png')
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

boss = Boss(W//2 - 200, 60, W, H, image_path=os.path.join('assets', 'img', 'boss2.png'),
            bullet_image_path=None)

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 24)
bullets, boss_bullets, boss_lasers = [], [], []   # boss_bullets/lasers not used but kept
slime_patches: List[SlimePatch] = []
game = True
all_players = [player1, player2]

# Mapeamento de Teclas (P2_AIMS CORRIGIDO)
P1_LEFT = pygame.K_a; P1_RIGHT = pygame.K_d; P1_LOOK_UP = pygame.K_o; P1_JUMP = pygame.K_w
P1_AIMS = {pygame.K_i:(0,-1), pygame.K_k:(0,1), pygame.K_j:(-1,0), pygame.K_l:(1,0)}
P2_LEFT = pygame.K_LEFT; P2_RIGHT = pygame.K_RIGHT; P2_LOOK_UP = pygame.K_RCTRL; P2_JUMP = pygame.K_RSHIFT
P2_AIMS = {pygame.K_u:(0,-1), pygame.K_m:(0,1), pygame.K_h:(-1,0), pygame.K_l:(1,0)}

# caminhos das imagens de quadrinho (ajuste se necessário)
img1_path = os.path.join('assets', 'img', 'quadrinho1.png')
img2_path = os.path.join('assets', 'img', 'quadrinho2.png')

while game:
    dt = clock.tick(FPS) / 1000.0

    # atualiza contador do rugido (só se boss vivo)
    if boss and boss.health > 0:
        _roar_timer += dt

    # se tempo >= intervalo e som existe, tocar e resetar
    if _roar_timer >= ROAR_INTERVAL and boss and boss.health > 0:
        if roar_sound:
            roar_sound.play()
        _roar_timer = 0.0

    # 1. PROCESSAMENTO DE INPUT
    keys = pygame.key.get_pressed()
    
    # Input do Player 1
    player1.handle_input_keyboard(keys, P1_LEFT, P1_RIGHT, P1_LOOK_UP, P1_AIMS)
    # Input do Player 2
    player2.handle_input_keyboard(keys, P2_LEFT, P2_RIGHT, P2_LOOK_UP, P2_AIMS)
    
    # Input do Joystick (Movimento e Mira contínuos)
    poll_joysticks(all_players, bullets, boss.bullet_image)

    # Eventos (Pulo e Tiro com Teclado)
    for event in pygame.event.get():
        if event.type in (pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
            handle_joystick_event(event, all_players, bullets)

        if event.type == pygame.QUIT:
            game = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
            
            # Pulo
            if event.key == P1_JUMP:
                player1.try_jump()
            if event.key == P2_JUMP:
                player2.try_jump()
            
            # TIRO com Teclado (Baseado na mira atualizada pelo handle_input_keyboard)
            # Player 1 atira com ENTER/SPACE
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                dx, dy = player1.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player1.facing_right else -1.0
                length = math.hypot(dx, dy) or 1.0
                b = player1.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                if b:
                    bullets.append(b)

            # Player 2 atira com ALT direito
            if event.key == pygame.K_RALT:
                dx, dy = player2.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player2.facing_right else -1.0
                length = math.hypot(dx, dy) or 1.0
                b = player2.shoot((dx/length, dy/length), bullet_image=boss.bullet_image)
                if b:
                    bullets.append(b)

    # 2. ATUALIZAÇÕES
    player1.update(dt, W)
    player2.update(dt, W)
    boss.update(dt)

    # Boss drops slime occasionally
    patch = boss.try_drop_slime()
    if patch:
        slime_patches.append(patch)

    # Atualiza Balas
    bullets = [b for b in bullets if b.alive]
    boss_bullets = [b for b in boss_bullets if b.alive]
    boss_lasers = [l for l in boss_lasers if l.alive]
    for b in bullets:
        b.update(dt, W, H)
    for b in boss_bullets:
        b.update(dt, W, H)
    for l in boss_lasers:
        l.update(dt)

    # Atualiza gosma
    slime_patches = [s for s in slime_patches if s.alive]
    for s in slime_patches:
        s.update(dt)

    # 3. COLISÕES
    # Player Bullets vs Boss
    for b in bullets[:]:
        if b.collides_rect(boss.rect):
            boss.health -= 1
            b.alive = False
            try:
                bullets.remove(b)
            except ValueError:
                pass

    # Boss Bullets vs Players (not used in this boss design)
    for b in boss_bullets[:]:
        for p in all_players:
            if p.is_alive() and b.collides_rect(p.rect):
                if p.take_damage(1):
                    b.alive = False
                    try:
                        boss_bullets.remove(b)
                    except ValueError:
                        pass
                    break

    # Boss Lasers vs Players (not used)

    # Slime -> Players (continuous damage while standing on slime)
    for s in slime_patches:
        for p in all_players:
            if p.is_alive() and s.collides_player(p):
                dmg = s.dps * dt
                p.health = max(0.0, p.health - dmg)
                # se for atingir 0 mata o player
                if p.health <= 0 and not p.dead:
                    p.die()

    # 4. CHECAGEM DE VITÓRIA/GAMEOVER
    if boss.health <= 0:
        # parar rugido/efeitos: não tocar mais rugido após a morte
        _roar_timer = 0.0
        print("Boss Derrotado! Mostrando tela final...")
        show_images_and_launch_next(
            img1_path,
            img2_path,
            window, 
            clock, 
            W, 
            H,
            next_script='faroestejogo.py', 
            ms_each=5000, 
            fadeout_ms=1000
        )

    if not any(p.is_alive() for p in all_players):
        print("Game Over!")
        game = False
        
    # 5. DESENHO
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((10, 10, 12)) # fallback

    boss.draw(window)

    # draw slime patches under players/boss
    for s in slime_patches:
        s.draw(window)

    # draw bullets
    for b in bullets:
        b.draw(window)
    for b in boss_bullets:
        b.draw(window)

    # draw players
    player1.draw(window)
    player2.draw(window)

    # HUD - show numeric HP
    hud = font.render(f"P1 HP: {int(player1.health)}   P2 HP: {int(player2.health)}   Boss: {int(boss.health)}", True, (255,255,255))
    window.blit(hud, (12, 12))

    pygame.display.flip()

pygame.quit()
sys.exit(0)
