# player.py
import os
import math
import pygame


class SimpleBullet:
    """Projétil simples, usado tanto por jogadores quanto por chefes."""
    def __init__(self, x, y, dir_x, dir_y, speed=300.0, color=(255, 100, 180), radius=6):
        self.x = float(x)
        self.y = float(y)
        l = math.hypot(dir_x, dir_y) or 1.0
        self.dx = dir_x / l
        self.dy = dir_y / l
        self.speed = speed
        self.color = color
        self.radius = radius
        self.alive = True
        self.life = 4.0  # segundos

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
        dx = int(self.x) - closest_x
        dy = int(self.y) - closest_y
        return (dx * dx + dy * dy) <= (self.radius * self.radius)


class PlayerSimple:
    """
    Classe do jogador com suporte a animação de caminhada.
    Pode usar sprite único ou sequência de frames ('walk_frames_paths').
    """
    def __init__(self, x, ground_y, screen_height, image_path=None, walk_frames_paths=None, walk_frame_interval=0.10):
        self.ground_y = ground_y
        self.image = None
        self.walk_frames = []
        self.walk_frame_idx = 0
        self.walk_frame_time = 0.0
        self.walk_frame_interval = walk_frame_interval
        self.use_walk = False

        # carregar frames de caminhada
        if walk_frames_paths:
            frames = []
            for p in walk_frames_paths:
                if os.path.exists(p):
                    try:
                        img = pygame.image.load(p).convert_alpha()
                        frames.append(img)
                    except Exception:
                        pass
            if frames:
                target_h = int(screen_height * 0.25)
                scaled = []
                for img in frames:
                    scale = target_h / img.get_height()
                    scaled.append(pygame.transform.rotozoom(img, 0, scale))
                self.walk_frames = scaled
                self.use_walk = True

        # se não tiver frames, tenta imagem estática
        if not self.use_walk and image_path and os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path).convert_alpha()
                target_h = int(screen_height * 0.25)
                scale = target_h / img.get_height()
                self.image = pygame.transform.rotozoom(img, 0, scale)
            except Exception:
                self.image = None

        if self.use_walk and self.walk_frames:
            first = self.walk_frames[0]
            self.w = first.get_width()
            self.h = first.get_height()
        else:
            self.w = self.image.get_width() if self.image else 64
            self.h = self.image.get_height() if self.image else 128

        self.rect = pygame.Rect(x, ground_y - self.h, self.w, self.h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.SPEED = 700.0
        self.JUMP_VELOCITY = -1500.0
        self.GRAVITY = 3000.0
        self.grounded = True
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.gun_offset = (self.w // 2, self.h // 2)

        # som de tiro
        shot_path = os.path.join('assets', 'sounds', 'som6.mp3')
        self.shot_sound = None
        if os.path.exists(shot_path):
            try:
                self.shot_sound = pygame.mixer.Sound(shot_path)
                self.shot_sound.set_volume(0.2)
            except Exception:
                self.shot_sound = None

        self.max_health = 8
        self.health = float(self.max_health)
        self.invuln_time = 0.8
        self._invuln_timer = 0.0
        self.dead = False
        self.aim = (1, 0)
        self.facing_right = True

    # ------------------------ CONTROLES ------------------------

    def handle_input_keyboard(self, keys, left_key, right_key, look_up_key, aim_keys):
        if self.dead:
            self.vel_x = 0
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
            ax = 0
            ay = 0
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

    # ------------------------ LÓGICA ------------------------

    def update(self, dt, screen_width):
        if self.dead:
            return
        self._time_since_last_shot += dt
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        # movimento horizontal
        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

        # gravidade / salto
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0.0
            self.grounded = True
        else:
            self.grounded = False

        # animação de caminhada
        if self.use_walk and self.walk_frames:
            moving = (abs(self.vel_x) > 5.0) and self.grounded
            if moving:
                self.walk_frame_time += dt
                if self.walk_frame_time >= self.walk_frame_interval:
                    steps = int(self.walk_frame_time / self.walk_frame_interval)
                    self.walk_frame_idx = (self.walk_frame_idx + steps) % len(self.walk_frames)
                    self.walk_frame_time -= steps * self.walk_frame_interval
            else:
                self.walk_frame_idx = 0
                self.walk_frame_time = 0.0

    def can_shoot(self):
        return (not self.dead) and (self._time_since_last_shot >= self.fire_cooldown)

    def shoot(self, direction):
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx
        spawn_y = self.rect.centery
        dx, dy = direction
        if dx == 0 and dy == 0:
            dx = 1.0 if self.facing_right else -1.0
        b = SimpleBullet(spawn_x, spawn_y, dx, dy, speed=700.0, color=(255, 105, 180), radius=6)
        if self.shot_sound:
            try:
                self.shot_sound.play()
            except Exception:
                pass
        return b

    def take_damage(self, amount):
        if self._invuln_timer > 0.0 or self.dead:
            return False
        self.health -= amount
        self._invuln_timer = self.invuln_time
        if self.health <= 0:
            self.dead = True
        return True

    # ------------------------ DESENHO ------------------------

    def draw(self, surface):
        if self.dead:
            return

        # sprite animado ou imagem estática
        if self.use_walk and self.walk_frames:
            frame = self.walk_frames[self.walk_frame_idx]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        elif self.image:
            frame = self.image
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200, 30, 30), self.rect)

        # barra de vida
        bar_w = max(40, self.w)
        bar_h = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - (bar_h + 6)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 30, 50), bg_rect)

        hp_ratio = max(0.0, min(1.0, float(self.health) / float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

        if self._invuln_timer > 0.0:
            # pisca azul claro durante invulnerabilidade
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                fill_color = (120, 180, 255)
            else:
                fill_color = (80, 130, 220)
        else:
            fill_color = (40, 140, 255)

        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, fill_rect)

        pygame.draw.rect(surface, (200, 200, 220), bg_rect, 1)
