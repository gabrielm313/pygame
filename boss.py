import pygame
import os
import math
from typing import Tuple

# --- classe Player ---
class Player:
    def __init__(self, x, ground_y, screen_height, image_path=None, scale_height_ratio=0.3):
        self.ground_y = ground_y
        self.screen_height = screen_height

        # tenta carregar imagem
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_height * scale_height_ratio)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)

        # dimensões
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
        self.fire_cooldown = 0.25  # segundos entre tiros
        self._time_since_last_shot = 0.0

        # ajuste do ponto onde a bala sai (offset relativo ao rect)
        # se a arma estiver na mão direita do sprite, aumente offset_x positivo
        self.gun_offset = (self.w // 2, self.h // 2)  # por padrão centro; ajuste conforme a imagem

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
        # atualiza timer de tiro
        self._time_since_last_shot += dt

        # movimento horizontal
        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

        # gravidade
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)

        # chão
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0.0
            self.grounded = True

    def can_shoot(self) -> bool:
        return self._time_since_last_shot >= self.fire_cooldown

    def shoot(self, direction: Tuple[float, float]):
        """
        direction: tupla (dx, dy) que já deve estar normalizada (ou zero).
        Retorna um objeto Bullet (ou None se não puder atirar).
        """
        if not self.can_shoot():
            return None

        # reset cooldown
        self._time_since_last_shot = 0.0

        # ponto de spawn: centro do jogador + gun_offset rotacionado (simplificado)
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w//2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h//2

        # cria bullet
        b = Bullet(spawn_x, spawn_y, direction)
        return b

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200, 30, 30), self.rect)


# --- classe Bullet ---
class Bullet:
    SPEED = 900.0       # pixels por segundo (mude se quiser)
    RADIUS = 7          # raio para desenhar a bala
    COLOR = (255, 0, 255)
    LIFETIME = 3.5      # segundos antes de desaparecer

    def __init__(self, x, y, direction: Tuple[float, float]):
        # posição como float para movimento suave
        self.x = float(x)
        self.y = float(y)

        # direction deve ser normalizado; se for (0,0), seta pra direita por padrão
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
        # move
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

        # decrementa vida
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return

        # se sair da tela, mata
        if self.x < -50 or self.x > screen_w + 50 or self.y < -50 or self.y > screen_h + 50:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


# --- código principal ---
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

# chão e jogador
ground_y = H  # como no seu código original
player = Player(W // 2, ground_y, H, image_path=os.path.join('assets', 'img', 'astronauta1.png'))

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 20)

# lista de balas
bullets = []

game = True
while game:
    dt_ms = clock.tick(FPS)
    dt = dt_ms / 1000.0

    # eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
            elif event.key == pygame.K_SPACE:
                player.try_jump()

            # --- atirar com setas: formamos a direção lendo o estado atual das teclas ---
            # se pressionou uma seta, vamos usar o estado atual para permitir diagonais
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

                # se houver direção, normalizamos e criamos bala
                if dx != 0 or dy != 0:
                    # cria direction (dx,dy) e dispara
                    b = player.shoot((dx, dy))
                    if b:
                        bullets.append(b)

    # entrada de movimento contínuo
    keys = pygame.key.get_pressed()
    player.handle_input(keys)

    # update do player
    player.update(dt, W)

    # update de balas (e remoção das mortas)
    for b in bullets[:]:
        b.update(dt, W, H)
        if not b.alive:
            bullets.remove(b)

    # draw
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((20, 20, 40))

    # desenha "chão" (se quiser ver)
    pygame.draw.rect(window, (50, 30, 10), (0, ground_y, W, H - ground_y))

    # desenha jogador e balas
    player.draw(window)
    for b in bullets:
        b.draw(window)

    # debug info
    info = f"Pos: ({player.rect.x},{player.rect.y}) VelY: {player.vel_y:.1f} Grounded: {player.grounded} Bullets: {len(bullets)}"
    text_surf = font.render(info, True, (255, 255, 255))
    window.blit(text_surf, (10, 10))

    pygame.display.flip()

pygame.quit()
