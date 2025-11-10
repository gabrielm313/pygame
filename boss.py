import pygame
import os

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

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        else:
            pygame.draw.rect(surface, (200, 30, 30), self.rect)


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
ground_y = H 
player = Player(W // 2, ground_y, H, image_path=os.path.join('assets', 'img', 'astronauta1.png'))

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 20)

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

    keys = pygame.key.get_pressed()
    player.handle_input(keys)

    # update
    player.update(dt, W)

    # draw
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((20, 20, 40))

    pygame.draw.rect(window, (50, 30, 10), (0, ground_y, W, H - ground_y))
    player.draw(window)

    # debug info
    info = f"Pos: ({player.rect.x},{player.rect.y}) VelY: {player.vel_y:.1f} Grounded: {player.grounded}"
    text_surf = font.render(info, True, (255, 255, 255))
    window.blit(text_surf, (10, 10))

    pygame.display.flip()

pygame.quit()
