import pygame
import os
import math
from typing import Tuple, List, Optional

pygame.init()

# =================== CONFIGURAÇÕES =====================
FPS = 60
clock = pygame.time.Clock()

info = pygame.display.Info()
LARGURA, ALTURA = info.current_w, info.current_h
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Joguinho")

# =================== FUNÇÕES AUXILIARES =====================
def load_frames_from_folder(folder: str, keep_alpha=True) -> List[pygame.Surface]:
    frames = []
    if not os.path.exists(folder):
        return frames
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            img = pygame.image.load(path)
            img = img.convert_alpha() if keep_alpha else img.convert()
            frames.append(img)
    return frames

# =================== CLASSE BULLET =====================
class Bullet:
    SPEED = 900.0
    RADIUS = 6
    COLOR = (255, 220, 0)
    LIFETIME = 3.5

    def __init__(self, x, y, direction: Tuple[float, float], owner=None, image=None):
        self.x = float(x)
        self.y = float(y)
        dx, dy = direction
        length = math.hypot(dx, dy) or 1
        self.dir_x = dx / length
        self.dir_y = dy / length
        self.speed = Bullet.SPEED
        self.life = Bullet.LIFETIME
        self.image = image
        self.owner = owner
        self.alive = True

    def update(self, dt, world_w, world_h):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.life -= dt
        if self.life <= 0 or self.x < -50 or self.x > world_w + 50 or self.y < -50 or self.y > world_h + 50:
            self.alive = False

    def draw(self, surface, camera_x):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x - camera_x), int(self.y)))
            surface.blit(self.image, rect)
        else:
            pygame.draw.circle(surface, self.COLOR, (int(self.x - camera_x), int(self.y)), self.RADIUS)

# =================== CLASSE PLAYER =====================
class Player:
    def __init__(self, x, ground_y, screen_height, image_path: Optional[str] = None):
        # carregar imagem do jogador (se existir)
        self.image = None
        if image_path and os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
            except Exception:
                self.image = None

        # se houver imagem, usar o rect dela; senão, usar rect padrão
        if self.image:
            self.rect = self.image.get_rect(midbottom=(x, ground_y))
        else:
            self.rect = pygame.Rect(x, ground_y - 100, 60, 100)

        self.vel_x = 0
        self.vel_y = 0
        self.grounded = False
        self.SPEED = 600
        self.GRAVITY = 3000
        # Aumentei a velocidade de salto para pular mais alto:
        self.JUMP_VEL = -2100  # antes estava -1500
        self.facing_right = True
        self.aim = (1, 0)
        self.cooldown = 0.25
        self.time_since_shot = 0
        self.health = 5

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vel_x = self.SPEED
            self.facing_right = True
        if keys[pygame.K_UP]:
            self.aim = (0, -1)
        elif keys[pygame.K_DOWN]:
            self.aim = (0, 1)
        else:
            self.aim = (1 if self.facing_right else -1, 0)

    def jump(self):
        if self.grounded:
            self.vel_y = self.JUMP_VEL
            self.grounded = False

    def update(self, dt, plataformas):
        self.rect.x += int(self.vel_x * dt)
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)

        # colisão com plataformas invisíveis
        self.grounded = False
        for p in plataformas:
            if self.rect.colliderect(p):
                # só colide se estiver caindo e vindo de cima
                if self.vel_y >= 0 and self.rect.bottom - self.vel_y * dt <= p.top:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.grounded = True

        # chão limite
        if self.rect.bottom >= ALTURA - 40:
            self.rect.bottom = ALTURA - 40
            self.vel_y = 0
            self.grounded = True

        self.time_since_shot += dt

    def can_shoot(self):
        return self.time_since_shot >= self.cooldown

    def shoot(self):
        if self.can_shoot():
            self.time_since_shot = 0
            dir_x, dir_y = self.aim
            spawn_x = self.rect.centerx + dir_x * 30
            spawn_y = self.rect.centery + dir_y * 10
            return Bullet(spawn_x, spawn_y, (dir_x, dir_y))
        return None

    def draw(self, surface, camera_x):
        if self.image:
            # desenha a imagem levando em conta a câmera
            blit_rect = self.image.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery))
            surface.blit(self.image, blit_rect)
        else:
            pygame.draw.rect(surface, (100, 200, 255), (self.rect.x - camera_x, self.rect.y, self.rect.w, self.rect.h))

# =================== CLASSE PLATAFORMA INVISÍVEL =====================
class Platform(pygame.Rect):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
    def draw(self, surface, camera_x):
        # desenha invisível, mas pode ativar visualização:
        # pygame.draw.rect(surface, (255, 0, 0), (self.x - camera_x, self.y, self.w, self.h), 1)
        pass


# =================== FUNDO E MUNDO =====================
bg_path = os.path.join('assets', 'img', 'fundo_pg.png')
bg = pygame.image.load(bg_path).convert()
# mantenho escala dupla por padrão, você pode ajustar o *2 para o que preferir
bg = pygame.transform.scale(bg, (bg.get_width() * 3, ALTURA))
bg_width = bg.get_width()

plataformas = [
    Platform(50 +150 , 300+100, 1080, 15),
    Platform(400 + 1000, 600, 700, 15),
    Platform(1400 + 820, 400, 800, 15),
    Platform(2200 + 2400, 400, 1080, 15),
    Platform(4600 + 2400, 400, 900, 15),
    Platform(7000 + 1000, 600, 550, 15),
]

# =================== PLAYER (agora carrega imagem se existir) =====================
player_img_path = os.path.join('assets', 'img', 'astronauta1.png')  # ajuste se seu arquivo estiver em outro caminho
player = Player(200, ALTURA - 40, ALTURA, image_path=player_img_path)

bullets: List[Bullet] = []

camera_x = 0
max_camera_x = bg_width - LARGURA

# =================== LOOP PRINCIPAL =====================
running = True
while running:
    dt = clock.tick(FPS) / 1000
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_c:
                player.jump()
            if event.key == pygame.K_x:
                b = player.shoot()
                if b:
                    bullets.append(b)

    player.handle_input(keys)
    player.update(dt, plataformas)

    # atualizar balas
    for b in bullets:
        b.update(dt, bg_width, ALTURA)
    bullets = [b for b in bullets if b.alive]

    # rolagem da câmera
    player_screen_x = player.rect.centerx - camera_x
    left_deadzone = LARGURA // 3
    right_deadzone = (LARGURA * 2) // 3

    if player_screen_x > right_deadzone:
        camera_x += (player_screen_x - right_deadzone)
    elif player_screen_x < left_deadzone:
        camera_x -= (left_deadzone - player_screen_x)

    camera_x = max(0, min(camera_x, max_camera_x))

    # desenhar
    window.fill((0, 0, 0))
    window.blit(bg, (-int(camera_x), 0))

    for p in plataformas:
        p.draw(window, camera_x)
    player.draw(window, camera_x)
    for b in bullets:
        b.draw(window, camera_x)

    pygame.display.flip()

pygame.quit()
