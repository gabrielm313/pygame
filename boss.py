import pygame
import os
import math
from typing import Tuple

# --- classe Player (igual ao seu) ---
class Player:
    def __init__(self, x, ground_y, screen_height, image_path=None, scale_height_ratio=0.3):
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

    def handle_input(self, keys):
        self.vel_x = 0.0
        if keys[pygame.K_a]:
            self.vel_x = -self.SPEED
        if keys[pygame.K_d]:
            self.vel_x = self.SPEED

    def try_jump(self):
        if self.grounded:
            self.vel_y = self.JUMP_VELOCITY
            self.grounded = False

    def update(self, dt, screen_width):
        self._time_since_last_shot += dt
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

    def can_shoot(self) -> bool:
        return self._time_since_last_shot >= self.fire_cooldown

    def shoot(self, direction: Tuple[float, float]):
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w//2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h//2
        b = Bullet(spawn_x, spawn_y, direction)
        return b

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200, 30, 30), self.rect)


# --- classe Bullet (igual ao anterior) ---
class Bullet:
    SPEED = 900.0
    RADIUS = 6
    COLOR = (255, 220, 0)
    LIFETIME = 3.5

    def __init__(self, x, y, direction: Tuple[float, float]):
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

    def update(self, dt, screen_w, screen_h):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        if self.x < -50 or self.x > screen_w + 50 or self.y < -50 or self.y > screen_h + 50:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def collides_rect(self, rect) -> bool:
        # colisão círculo-retângulo aproximada
        closest_x = max(rect.left, min(int(self.x), rect.right))
        closest_y = max(rect.top, min(int(self.y), rect.bottom))
        dx = int(self.x) - closest_x
        dy = int(self.y) - closest_y
        return (dx*dx + dy*dy) <= (self.radius * self.radius)


# --- classe Boss (nova) ---
class Boss:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, scale_height_ratio=0.35):
        """
        x,y = posição inicial do boss (top-left)
        screen_w/screen_h = para dimensionamento/patrol
        image_path = caminho da imagem do boss
        scale_height_ratio = fração da altura da tela para altura do boss
        """
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

        # movimento horizontal automático
        self.speed = 200.0            # pixels/s (mude para mais/menos)
        self.direction = 1            # 1 = para a direita, -1 = para a esquerda
        self.patrol_min_x = 50        # limite esquerdo do patrulhamento
        self.patrol_max_x = screen_w - 50 - self.w  # limite direito
        # opções: pode ajustar patrol_min_x / patrol_max_x para restringir área

        # movimento vertical (voo) - bobbing usando seno
        self.bob_amplitude = 30.0     # amplitude em pixels
        self.bob_frequency = 1.0      # ciclos por segundo
        self._time = 0.0

        # vida do boss
        self.max_health = 30
        self.health = self.max_health

    def update(self, dt):
        # atualiza timer para bob
        self._time += dt

        # horizontal: move e inverte direção nos limites
        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = int(self.patrol_min_x)
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = int(self.patrol_max_x)
            self.direction = -1

        # vertical: aplica bob em relação a y base (top)
        bob = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude
        # o y_base é fixa; aqui vamos centralizar o bob em y inicial
        base_y = self.rect.y
        # para manter consistência sem acumular, definimos um "y_offset" temporário:
        self._y_offset = bob

    def draw(self, surface):
        draw_x = self.rect.x
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (draw_x, draw_y))
        else:
            pygame.draw.rect(surface, (80, 20, 20), (draw_x, draw_y, self.w, self.h))

        # draw health bar
        bar_w = self.w
        bar_h = 8
        bar_x = draw_x
        bar_y = draw_y - 12
        # fundo da barra
        pygame.draw.rect(surface, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h))
        # vida atual
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))


# ------------------ código principal (integra Player, Bullets e Boss) ------------------
pygame.init()
window = pygame.display.set_mode((1920, 1090))
pygame.display.set_caption('Duelo Boss')
W, H = window.get_width(), window.get_height()

# fundo
fundo_path = os.path.join('assets', 'img', 'fundo_boss.png')
fundo_image = None
if os.path.exists(fundo_path):
    fundo_image = pygame.image.load(fundo_path).convert()
    fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

ground_y = H
player = Player(W // 2, ground_y, H, image_path=os.path.join('assets', 'img', 'astronauta1.png'))

# cria boss (ajuste o caminho da imagem)
boss_image_path = os.path.join('assets', 'img', 'nave boss.png')  # coloque aqui a sua imagem
boss = Boss(W//4, 80, W, H, image_path=boss_image_path, scale_height_ratio=0.3)

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 20)
bullets = []

game = True
while game:
    dt_ms = clock.tick(FPS)
    dt = dt_ms / 1000.0

    # --- eventos ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
            elif event.key == pygame.K_SPACE:
                player.try_jump()
            # atirar com setas (permite diagonais)
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                keys = pygame.key.get_pressed()
                dx = 0
                dy = 0
                if keys[pygame.K_LEFT]:
                    dx -= 1
                if keys[pygame.K_RIGHT]:
                    dx += 1
                if keys[pygame.K_UP]:
                    dy -= 1
                if keys[pygame.K_DOWN]:
                    dy += 1
                if dx != 0 or dy != 0:
                    b = player.shoot((dx, dy))
                    if b:
                        bullets.append(b)

    # entrada contínua
    keys = pygame.key.get_pressed()
    player.handle_input(keys)

    # updates
    player.update(dt, W)
    boss.update(dt)
    for b in bullets[:]:
        b.update(dt, W, H)
        # colisão bala -> boss
        # usamos draw_y do boss para checar colisão aproximada
        boss_draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
        boss_rect_draw = pygame.Rect(boss.rect.x, boss_draw_y, boss.w, boss.h)
        if b.alive and b.collides_rect(boss_rect_draw):
            b.alive = False
            boss.health -= 1  # dano por bala (ajuste)
            # opcional: quando a vida acabar, faça algo
            if boss.health <= 0:
                print("Boss derrotado!")
                # você pode trocar por uma animação, remover o boss, etc.

        if not b.alive:
            bullets.remove(b)

    # draw
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((20, 20, 40))

    pygame.draw.rect(window, (50, 30, 10), (0, ground_y, W, H - ground_y))
    player.draw(window)
    boss.draw(window)
    for b in bullets:
        b.draw(window)

    # debug
    info = f"Pos: ({player.rect.x},{player.rect.y}) VelY: {player.vel_y:.1f} Grounded: {player.grounded} Bullets: {len(bullets)} BossHP: {boss.health}"
    text_surf = font.render(info, True, (255, 255, 255))
    window.blit(text_surf, (10, 10))

    pygame.display.flip()

pygame.quit()
