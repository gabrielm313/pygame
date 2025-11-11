import pygame
import math
from config import LARGURA , ALTURA , GRAVIDADE 
from assets import ASTRONAUTA_IMG 

# Define estados possíveis do jogador
STILL = 0
JUMPING = 1
FALLING = 2

class Tile(pygame.sprite.Sprite):

    # Construtor da classe.
    def __init__(self, tile_img, row, column):
        # Construtor da classe pai (Sprite).
        pygame.sprite.Sprite.__init__(self)

class Astronauta(pygame.sprite.Sprite):
    def __init__(self , groups , assets, row , column, platforms):
        # Construtor da classe mãe (Sprite).
        super().__init__()
        self.groups = groups
        self.assets = assets

        
        # offsets da arma (relativos a rect.center)
        self.gun_offset_right = (20, -10)   # ajustar até a bala sair na ponta
        self.gun_offset_left  = (-20, -10)  # normalmente o X invertido da direita
        # garante facing padrão
        self.facing = "right"

        self.image = assets[ASTRONAUTA_IMG]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()

        #posição inicial do astronauta
        self.rect.centerx = LARGURA // 2 * column
        self.rect.bottom = ALTURA - 40 * row

        self.highest_y = self.rect.bottom  # guarda o y mais alto alcançado (inicialmente o chão)

        self.speedx = 0
        self.speedy = 0
        self.on_ground = True  # controla se está no chão
        self.agachado = False  # estado de agachar (inicial)

        # Guarda os grupos de sprites para tratar as colisões
        self.platforms = platforms

        # variáveis auxiliares
        self.state = STILL
        self.highest_y = self.rect.bottom

        self.drop_through_timer = 0.0       # tempo restante (segundos) em que pode atravessar plataformas
        self.drop_through_duration = 0.15   # duração curta (0.15s) — ajuste se quiser

    def get_gun_tip(self):
        """Retorna (x, y) da ponta da arma em coordenadas do mundo."""
        cx, cy = self.rect.centerx, self.rect.centery
         # offset padrão (defina em __init__: self.gun_offset = (20, -6))
        ox, oy = getattr(self, "gun_offset", (100, -100))

        # se tiver offsets específicos por lado, priorize eles

        if hasattr(self, "gun_offset_right") and hasattr(self, "gun_offset_left"):
            if getattr(self, "facing", "right") == "right":
                ox, oy = self.gun_offset_right 
            else:
                ox, oy = self.gun_offset_left
        else:
            # inverte X se estiver virado para a esquerda
            if getattr(self, "facing", "right") == "left":
                ox = -ox
        
        return cx + ox, cy + oy

    def update(self, dt):
        prev_bottom = self.rect.bottom

        # decrementa timer de "drop through"
        if self.drop_through_timer > 0:
            self.drop_through_timer -= dt
            if self.drop_through_timer <= 0:
                self.drop_through_timer = 0.0

        # movimento horizontal (mantive sua escala com dt*60)
        self.rect.x += int(self.speedx * dt * 60)

        # se estiver no chão e NÃO estivermos em modo drop_through, verifica se ainda há chão 1px abaixo
        if self.on_ground and self.drop_through_timer == 0:
            probe = self.rect.copy()
            probe.y += 1
            still_on = False
            for plat in self.platforms:
                if probe.colliderect(plat):
                    still_on = True
                    break
            # Verifica também se o "probe" está tocando o chão principal
            if probe.bottom >= ALTURA - 40:
                still_on = True
                
            if not still_on:
                self.on_ground = False
                if self.speedy <= 0:
                    self.speedy = 1

        # gravidade e movimento vertical
        if not self.on_ground:
            self.speedy += GRAVIDADE * dt * 60
        self.rect.y += int(self.speedy * dt * 60)

        # --- colisão one-way: somente se NÃO estivermos em modo drop_through ---
        if self.speedy > 0 and self.drop_through_timer == 0:
            TOL = 6
            for plat in self.platforms:
                if self.rect.colliderect(plat):
                    if prev_bottom <= plat.top + TOL:
                        self.rect.bottom = plat.top
                        self.speedy = 0
                        self.on_ground = True
                        break
        else:
            if self.speedy < 0:
                self.on_ground = False

        # chão limite
        if self.rect.bottom >= ALTURA - 40:
            self.rect.bottom = ALTURA - 40
            self.speedy = 0
            self.on_ground = True

        # manter dentro dos limites da tela (esquerda)
        if self.rect.left < 0:
            self.rect.left = 0


    #adicionando funções para os movimentos do personagem
    def pular(self):
        if self.on_ground:
            self.speedy = -92 # ajuste este valor (px/s) para corresponder à sua escala; experimente
            self.on_ground = False
            self.state = JUMPING


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_x, dir_y, speed=500, world_w=2000, world_h=1000):
        """
        speed: pixels por segundo
        """
        super().__init__()
        # visual simples; substitua por imagem / asset se quiser
        self.image = pygame.Surface((15, 8), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255,0,255), self.image.get_rect())
        self.orig_image = self.image

        # posição como floats para movimentação suave
        self.x = float(x) + 55
        self.y = float(y)- 64.5
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        # normaliza o vetor direção
        length = math.hypot(dir_x, dir_y)
        if length == 0:
            self.dir_x, self.dir_y = 1.0, 0.0
        else:
            self.dir_x, self.dir_y = dir_x / length, dir_y / length

        self.speed = speed

        # limites do mundo
        self.world_w = world_w
        self.world_h = world_h

        # rotaciona a imagem para apontar na direção do tiro (opcional)
        angle_deg = -math.degrees(math.atan2(self.dir_y, self.dir_x))
        self.image = pygame.transform.rotate(self.orig_image, angle_deg)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))

        # mata se sair dos limites do mundo
        if (self.rect.right < 0 or self.rect.left > self.world_w or
            self.rect.bottom < 0 or self.rect.top > self.world_h):
            self.kill()
