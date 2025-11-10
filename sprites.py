import pygame
import math
from config import LARGURA , ALTURA , GRAVIDADE 
from assets import ASTRONAUTA_IMG 


class Astronauta(pygame.sprite.Sprite):
    def __init__(self , groups , assets):
        # Construtor da classe mãe (Sprite).
        super().__init__()
        self.groups = groups
        self.assets = assets

        # (x_offset, y_offset) relativo a rect.center
        self.gun_offset = (20, -15) 
        # offsets da arma (relativos a rect.center)
        self.gun_offset_right = (20, -10)   # ajustar até a bala sair na ponta
        self.gun_offset_left  = (-20, -10)  # normalmente o X invertido da direita
        # garante facing padrão
        self.facing = "right"

        self.image = assets[ASTRONAUTA_IMG]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.centerx = LARGURA // 2
        self.rect.bottom = ALTURA - 40

        self.speedx = 0
        self.speedy = 0
        self.no_chao = True  # controla se está no chão
        # estado de agachar (inicial)
        self.agachado = False

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

    def update(self , dt=0):
        # dt = tempo em ms do clock.tick() ou calculado em loop principal

         # Movimento horizontal
        self.rect.x += self.speedx

        # Movimento vertical (pulo e gravidade)
        self.rect.y += self.speedy

        # Aplica gravidade
        if not self.no_chao:
            self.speedy += GRAVIDADE

        if self.speedx > 0:
            self.facing = "right"
        elif self.speedx < 0:
            self.facing = "left"

        midbottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = midbottom
        
        # Mantém dentro da tela

        if self.rect.left < 0:
            self.rect.left = 0

        # Limite inferior (chão)
        if self.rect.bottom >= ALTURA - 40:  # 40 é a margem do chão
            self.rect.bottom = ALTURA - 40
            self.speedy = 0
            self.no_chao = True

        # Limite superior (teto)
        if self.rect.top <= 0:
            self.rect.top = 0
            self.speedy = 0

    #adicionando funções para os movimentos do personagem
    def pular(self):
        if self.no_chao:  # só pula se estiver no chão
            self.speedy = -82
            self.no_chao = False

    #aqui(agachar) ainda está dando erro
    # def agachar(self):
    #      # já está agachado → não faz nada
    #     if self.agachado:
    #         return
    #     # exemplo simples: trocar a flag e animação
    #     self.agachado = True
    #     self.set_state('agachando')

    # def levantar(self):
    #     if not self.agachado:
    #         return
    #     self.agachado = False
    #     self.set_state('parado')



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
        self.x = float(x) + 40
        self.y = float(y)-64.5
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

