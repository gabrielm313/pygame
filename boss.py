import pygame
import os
import math
from typing import Tuple, List

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
        self.JUMP_VELOCITY = -1200.0
        self.GRAVITY = 2500.0
        self.grounded = True

        # tiro
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.gun_offset = (self.w // 2, self.h // 2)

        # vida / invuln / morte
        self.max_health = 5
        self.health = self.max_health
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
        """
        fallback keyboard input per player:
        left_key/right_key = movement
        look_up_key = hold to aim up
        aim_keys = dict of keys -> aim vector (like {K_i:(0,-1), ...})
        """
        if self.dead:
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

        # look up override
        if look_up_key and keys[look_up_key]:
            self.aim = (0, -1)
        else:
            ax = 0; ay = 0
            for k, vec in aim_keys.items():
                if keys[k]:
                    ax += vec[0]
                    ay += vec[1]
            if ax != 0 or ay != 0:
                # normalize to -1/0/1 grid (keeps directional intent)
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

        # física
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

        # estado
        if not self.grounded:
            self.state = 'jump'
        else:
            if abs(self.vel_x) > 1:
                self.state = 'walk'
            else:
                self.state = 'idle'

        # animações
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
        return not self.dead and self._time_since_last_shot >= self.fire_cooldown

    def shoot(self, direction: Tuple[float, float], bullet_image=None):
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w // 2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h // 2
        b = Bullet(spawn_x, spawn_y, direction, image=bullet_image)
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
        return self.health > 0 and not self.dead

    def draw(self, surface):
        if self.dead:
            if self.image:
                surface.blit(self.image, (self.rect.x, self.rect.y))
            else:
                pygame.draw.rect(surface, (100, 100, 100), self.rect)
            return

        # full jump
        if self.state == 'jump' and self.full_jump:
            frame = self.full_jump[0]
            frame_to_draw = frame
            if not self.facing_right:
                frame_to_draw = pygame.transform.flip(frame, True, False)
            surface.blit(frame_to_draw, (self.rect.x, self.rect.y))
            return

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

# ---------------- Bullet ----------------
class Bullet:
    SPEED = 900.0
    RADIUS = 6
    COLOR = (255, 220, 0)
    LIFETIME = 3.5

    def __init__(self, x, y, direction: Tuple[float, float], image: pygame.Surface = None):
        self.x = float(x)
        self.y = float(y)
        dx, dy = direction
        if dx == 0 and dy == 0:
            dx = 1.0
        length = math.hypot(dx, dy)
        self.dir_x = dx / length
        self.dir_y = dy / length
        self.speed = Bullet.SPEED
        self.radius = Bullet.RADIUS
        self.color = Bullet.COLOR
        self.life = Bullet.LIFETIME
        self.alive = True
        self.image = image
        if self.image:
            diameter = max(6, self.radius * 2)
            self.image = pygame.transform.smoothscale(self.image, (diameter, diameter))

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

# ---------------- BossLaser ----------------
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
        self.surface.fill((255, 80, 80, 160))

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

# ---------------- Boss ----------------
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
        self.bob_amplitude = 30.0
        self.bob_frequency = 0.8
        self._time = 0.0
        self.max_health = 60
        self.health = self.max_health

        self.hand_offsets = [int(self.w * 0.22), int(self.w * 0.78) - 12]
        self.hand_bullet_cooldowns = [1.2, 1.2]
        self._time_since_last_bullet = [0.0, 0.0]
        self.hand_laser_cooldowns = [6.0, 6.0]
        self._time_since_last_laser = [0.0, 0.0]
        self.laser_width = 60
        self.laser_height = 260
        self.laser_duration = 1.2
        self.laser_damage_per_second = 3.0
        self.bullet_image = None
        if bullet_image_path and os.path.exists(bullet_image_path):
            self.bullet_image = pygame.image.load(bullet_image_path).convert_alpha()

    def update(self, dt):
        self._time += dt
        for i in range(2):
            self._time_since_last_bullet[i] += dt
            self._time_since_last_laser[i] += dt
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1
        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

    def try_shoot_hands(self, player_center):
        bullets = []
        px, py = player_center
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_bullet[i] < self.hand_bullet_cooldowns[i]:
                continue
            self._time_since_last_bullet[i] = 0.0
            spawn_x = int(self.rect.x + offset)
            spawn_y = draw_y + self.h - 10
            dx = px - spawn_x
            dy = py - spawn_y
            length = math.hypot(dx, dy)
            if length == 0:
                length = 1.0
            b = Bullet(spawn_x, spawn_y, (dx/length, dy/length), image=self.bullet_image)
            bullets.append(b)
        return bullets

    def try_fire_lasers_per_hand(self, player_rect):
        lasers = []
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_laser[i] < self.hand_laser_cooldowns[i]:
                continue
            self._time_since_last_laser[i] = 0.0
            laser = BossLaser(self, offset - (self.laser_width // 2) + 6,
                              self.laser_width, self.laser_height,
                              duration=self.laser_duration,
                              damage_per_second=self.laser_damage_per_second)
            lasers.append(laser)
        return lasers

    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (80, 80, 80),
                         (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20),
                         (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))

# ------------------ suporte multi-mapeamento por joystick ------------------
AXIS_DEADZONE = 0.25

# configure indexes for each joystick here (change GAMEPAD_MAPS[1] for controller 2 if needed)
GAMEPAD_MAPS = [
    {   # joystick 0 (controle 1)
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "button_fire": 1,
    },
    {   # joystick 1 (controle 2) - ajustável
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "button_fire": 1,
    }
]

joysticks: List[pygame.joystick.Joystick] = []
joystick_instance_ids: List[int] = []
joystick_to_player_index = {}  # physical joystick index -> player index (0->player1, 1->player2)

def get_map_for_joystick_physical_index(i: int) -> dict:
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
    # prints to help mapping - keep these while setting up your controllers
    if event.type == pygame.JOYAXISMOTION:
        print(f"JOY AXIS: joy={getattr(event,'joy',None)} axis={event.axis} value={event.value:.3f}")
    elif event.type == pygame.JOYBUTTONDOWN:
        print(f"JOY BUTTON DOWN: joy={getattr(event,'joy',None)} button={event.button}")
    elif event.type == pygame.JOYBUTTONUP:
        print(f"JOY BUTTON UP: joy={getattr(event,'joy',None)} button={event.button}")
    elif event.type == pygame.JOYHATMOTION:
        print(f"JOY HAT: joy={getattr(event,'joy',None)} hat={event.hat} value={event.value}")

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

        if btn == pad_map["button_jump"]:
            player.try_jump()
            return

        if btn == pad_map["button_fire"]:
            joy = joysticks[joy_physical_index] if (joy_physical_index is not None and joy_physical_index < len(joysticks)) else None
            aim_ax = pad_map.get("aim_axis_x", None)
            aim_ay = pad_map.get("aim_axis_y", None)
            if joy is not None and aim_ax is not None and aim_ay is not None and joy.get_numaxes() > max(aim_ax, aim_ay):
                raw_ax = joy.get_axis(aim_ax)
                raw_ay = joy.get_axis(aim_ay)
                ax = read_axis_with_deadzone(joy, aim_ax)
                ay = read_axis_with_deadzone(joy, aim_ay)
                if ax != 0.0 or ay != 0.0:
                    dir_x = raw_ax
                    dir_y = raw_ay
                    length = math.hypot(dir_x, dir_y)
                    if length == 0:
                        length = 1.0
                    dx = dir_x / length
                    dy = dir_y / length
                    b = Bullet(player.rect.centerx + player.gun_offset[0] - player.w//2,
                               player.rect.centery + player.gun_offset[1] - player.h//2,
                               (dx, dy), image=None)
                    if b:
                        bullets_list.append(b)
                    player.aim = (1 if dx > 0.2 else (-1 if dx < -0.2 else 0),
                                  1 if dy > 0.2 else (-1 if dy < -0.2 else 0))
                    return

            hat_idx = pad_map.get("dpad_hat", 0)
            if joy is not None and joy.get_numhats() > hat_idx:
                hat = joy.get_hat(hat_idx)
                if hat != (0, 0):
                    hx, hy = hat
                    dx = hx
                    dy = -hy
                    b = Bullet(player.rect.centerx + player.gun_offset[0] - player.w//2,
                               player.rect.centery + player.gun_offset[1] - player.h//2,
                               (dx, dy), image=None)
                    if b:
                        bullets_list.append(b)
                    player.aim = (dx, dy)
                    return

            dx, dy = player.aim
            if dx == 0 and dy == 0:
                dx = 1.0
            length = math.hypot(dx, dy)
            if length == 0:
                length = 1.0
            b = Bullet(player.rect.centerx + player.gun_offset[0] - player.w//2,
                       player.rect.centery + player.gun_offset[1] - player.h//2,
                       (dx/length, dy/length), image=None)
            if b:
                bullets_list.append(b)
            return

    if event.type == pygame.JOYHATMOTION and player_index is not None and player_index < len(players_list):
        hat_x, hat_y = event.value
        players_list[player_index].aim = (hat_x, -hat_y)

def poll_joysticks(players_list):
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
                length = math.hypot(dead_ax, dead_ay)
                if length == 0:
                    length = 1.0
                nx = dead_ax / length
                ny = dead_ay / length
                player.aim = (nx, ny)
                continue

        hat_idx = pad_map.get("dpad_hat", None)
        if hat_idx is not None and joy.get_numhats() > hat_idx:
            hat = joy.get_hat(hat_idx)
            if hat != (0, 0):
                player.aim = (hat[0], -hat[1])
                continue

# ---------------- Main game loop ----------------
pygame.init()
# initialize joysticks and print info
joysticks, joystick_instance_ids = init_joysticks()

window = pygame.display.set_mode((1280, 500))
pygame.display.set_caption('Duelo Boss - Gamepad multi')
W, H = window.get_width(), window.get_height()

# fundo opcional
fundo_image = None
fundo_path = os.path.join('assets', 'img', 'fundo_boss.png')
if os.path.exists(fundo_path):
    fundo_image = pygame.image.load(fundo_path).convert()
    fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

ground_y = H

# players (use pastas de animação separadas se quiser)
player1 = Player(W//4, ground_y, H,
                 image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                 anim_root=os.path.join('assets', 'img', 'player1'))

player2 = Player(3*W//4, ground_y, H,
                 image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                 anim_root=os.path.join('assets', 'img', 'player2'))

boss = Boss(W//4, 80, W, H, image_path=os.path.join('assets', 'img', 'nave boss.png'),
            bullet_image_path=os.path.join('assets', 'img', 'bala.png'))

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 24)
bullets, boss_bullets, boss_lasers = [], [], []
game = True

# keyboard fallback mappings
P1_LEFT = pygame.K_a; P1_RIGHT = pygame.K_d; P1_LOOK_UP = pygame.K_o; P1_JUMP = pygame.K_w
P1_AIMS = {pygame.K_i:(0,-1), pygame.K_k:(0,1), pygame.K_j:(-1,0), pygame.K_l:(1,0)}
P2_LEFT = pygame.K_LEFT; P2_RIGHT = pygame.K_RIGHT; P2_LOOK_UP = pygame.K_RCTRL; P2_JUMP = pygame.K_RSHIFT
P2_AIMS = {pygame.K_u:(0,-1), pygame.K_m:(0,1), pygame.K_h:(-1,0), pygame.K_k:(1,0)}

while game:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        # joystick events handled (prints help you map)
        if event.type in (pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
            handle_joystick_event(event, [player1, player2], bullets)

        if event.type == pygame.QUIT:
            game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
            # keyboard jumps
            if event.key == P1_JUMP:
                player1.try_jump()
            if event.key == P2_JUMP:
                player2.try_jump()
            # keyboard fire (immediate on keydown)
            if event.key in P1_AIMS and not player1.dead:
                dx, dy = P1_AIMS[event.key]
                b = player1.shoot((dx, dy))
                if b:
                    bullets.append(b)
                player1.aim = (dx, dy)
            if event.key in P2_AIMS and not player2.dead:
                dx, dy = P2_AIMS[event.key]
                b = player2.shoot((dx, dy))
                if b:
                    bullets.append(b)
                player2.aim = (dx, dy)

    # continuous keyboard input (movement + aim hold)
    keys = pygame.key.get_pressed()
    player1.handle_input_keyboard(keys, P1_LEFT, P1_RIGHT, P1_LOOK_UP, P1_AIMS)
    player2.handle_input_keyboard(keys, P2_LEFT, P2_RIGHT, P2_LOOK_UP, P2_AIMS)

    # poll joysticks to override keyboard for connected controllers
    poll_joysticks([player1, player2])

    # update entities
    player1.update(dt, W)
    player2.update(dt, W)
    boss.update(dt)

    # boss actions (aims at both players)
    boss_bullets.extend(boss.try_shoot_hands(player1.rect.center))
    boss_bullets.extend(boss.try_shoot_hands(player2.rect.center))
    boss_lasers.extend(boss.try_fire_lasers_per_hand(player1.rect))
    boss_lasers.extend(boss.try_fire_lasers_per_hand(player2.rect))

    # update player bullets -> boss collision
    for b in bullets[:]:
        b.update(dt, W, H)
        boss_draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
        boss_rect_draw = pygame.Rect(boss.rect.x, boss_draw_y, boss.w, boss.h)
        if b.alive and b.collides_rect(boss_rect_draw):
            b.alive = False
            boss.health -= 1
            if boss.health <= 0:
                print("Boss derrotado!")
        if not b.alive:
            bullets.remove(b)

    # update boss bullets -> players collision
    for bb in boss_bullets[:]:
        bb.update(dt, W, H)
        if bb.alive:
            if bb.collides_rect(player1.rect) and not player1.dead:
                bb.alive = False
                player1.take_damage(1)
            elif bb.collides_rect(player2.rect) and not player2.dead:
                bb.alive = False
                player2.take_damage(1)
        if not bb.alive:
            boss_bullets.remove(bb)

    # update lasers
    for laser in boss_lasers[:]:
        laser.update(dt)
        if laser.alive:
            if laser.collides_rect(player1.rect) and not player1.dead:
                player1.take_damage(1)
            if laser.collides_rect(player2.rect) and not player2.dead:
                player2.take_damage(1)
        if not laser.alive:
            boss_lasers.remove(laser)

    # draw
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((20, 20, 40))

    boss.draw(window)
    for laser in boss_lasers: laser.draw(window)
    for bb in boss_bullets: bb.draw(window)
    for b in bullets: b.draw(window)
    player1.draw(window)
    player2.draw(window)

    # HUD
    info = f"P1 HP: {player1.health}/{player1.max_health}   P2 HP: {player2.health}/{player2.max_health}   BossHP: {boss.health}"
    text_surf = font.render(info, True, (255, 255, 255))
    window.blit(text_surf, (10, 10))

    pygame.display.flip()

    # end game checks
    if player1.dead and player2.dead:
        big_font = pygame.font.Font(None, 96)
        text = big_font.render("BOTH PLAYERS DIED", True, (220, 20, 20))
        tx = (W - text.get_width()) // 2
        ty = (H - text.get_height()) // 2
        window.blit(text, (tx, ty))
        pygame.display.flip()
        pygame.time.delay(1500)
        game = False
pygame.quit()