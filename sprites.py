import pygame
import math
from config import LARGURA , ALTURA , GRAVIDADE 
from assets import ASTRONAUTA_IMG , ALIEN_IMG , OVNI_IMG , ENEMY_LASER_IMG

# Define estados possíveis do jogador
STILL = 0
JUMPING = 1
FALLING = 2

# Cores para os lasers inimigos (ajuste conforme necessário)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

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

        # --- Variáveis de Vida / Dano ADICIONADAS ---
        self.max_health = 5
        self.health = self.max_health
        self.invuln_time = 1.0  # 1 segundo de invulnerabilidade
        self._invuln_timer = 0.0
        self.dead = False
        
        # offsets da arma (relativos a rect.center)
        self.gun_offset_right = (20, -10) 
        self.gun_offset_left  = (-20, -10) 
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

        self.drop_through_timer = 0.0      # tempo restante (segundos) em que pode atravessar plataformas
        self.drop_through_duration = 0.15  # duração curta (0.15s) — ajuste se quiser

    def get_gun_tip(self):
        """Retorna (x, y) da ponta da arma em coordenadas do mundo."""
        cx, cy = self.rect.centerx, self.rect.centery
        ox, oy = getattr(self, "gun_offset", (100, -100))

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
        if self.dead:
            return

        prev_bottom = self.rect.bottom

        # decrementa timer de "drop through"
        if self.drop_through_timer > 0:
            self.drop_through_timer -= dt
            if self.drop_through_timer <= 0:
                self.drop_through_timer = 0.0
        
        # decrementa timer de invulnerabilidade ADICIONADO
        if self._invuln_timer > 0.0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        # movimento horizontal (mantive sua escala com dt*60)
        self.rect.x += int(self.speedx * dt * 60)
        
        # ... (restante da lógica de chão, gravidade e colisão)
        if self.on_ground and self.drop_through_timer == 0:
            probe = self.rect.copy()
            probe.y += 1
            still_on = False
            for plat in self.platforms:
                if probe.colliderect(plat):
                    still_on = True
                    break
            if probe.bottom >= ALTURA - 40:
                still_on = True
                
            if not still_on:
                self.on_ground = False
                if self.speedy <= 0:
                    self.speedy = 1

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

    def pular(self):
        if self.on_ground:
            self.speedy = -92 # ajuste este valor (px/s) para corresponder à sua escala; experimente
            self.on_ground = False
            self.state = JUMPING

    def take_damage(self, amount: int) -> bool:
        """Aplica dano e inicia timer de invulnerabilidade. Retorna True se o dano foi aplicado."""
        if self._invuln_timer > 0.0 or self.dead:
            return False # Já invulnerável ou morto
        
        self.health -= amount
        self._invuln_timer = self.invuln_time
        
        if self.health <= 0:
            self.health = 0
            self.die()
        
        return True

    def die(self):
        self.dead = True
        self.kill() # Remove o sprite dos grupos
        print("Astronauta Morreu!")


class Bullet(pygame.sprite.Sprite):
    # Classe Bullet (permanece inalterada para balas do jogador)
    def __init__(self, x, y, dir_x, dir_y, speed=500, world_w=2000, world_h=1000):
        super().__init__()
        self.image = pygame.Surface((15, 8), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255,0,255), self.image.get_rect())
        self.orig_image = self.image

        self.x = float(x) + 55
        self.y = float(y)- 64.5
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        length = math.hypot(dir_x, dir_y)
        if length == 0:
            self.dir_x, self.dir_y = 1.0, 0.0
        else:
            self.dir_x, self.dir_y = dir_x / length, dir_y / length

        self.speed = speed

        self.world_w = world_w
        self.world_h = world_h

        angle_deg = -math.degrees(math.atan2(self.dir_y, self.dir_x))
        self.image = pygame.transform.rotate(self.orig_image, angle_deg)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))

        if (self.rect.right < 0 or self.rect.left > self.world_w or
            self.rect.bottom < 0 or self.rect.top > self.world_h):
            self.kill()

class EnemyLaser(pygame.sprite.Sprite):
    def __init__(self, x, y, target_dx, target_dy, assets, speed=600, color=RED, width=10, height=30):
        """
        Laser inimigo desenhado como um Rect.
        target_dx/dy: direção (não precisa ser normalizada).
        """
        super().__init__()
        
        self.speed = speed 
        self.color = color
        self.alive = True

        # Normaliza o vetor de direção
        length = math.hypot(target_dx, target_dy)
        if length == 0:
            self.direction = pygame.math.Vector2(0, 1)
        else:
            self.direction = pygame.math.Vector2(target_dx, target_dy).normalize()
        
        # Cria a superfície do Rect
        self.width = width
        self.height = height
        # Criamos o image com o tamanho máximo (incluindo rotação, se for o caso),
        # mas aqui vamos usar o tamanho simples e deixar o Pygame cuidar do Rect
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(self.color)
        
        # Posição inicial (floats para precisão)
        self.x = float(x)
        self.y = float(y)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        
        # Se for movimento diagonal, você pode querer rotacionar a imagem aqui
        # (mas para laser simples reto, não é estritamente necessário)

    def update(self, dt):
        if not self.alive:
            self.kill()
            return
            
        self.x += self.direction.x * self.speed * dt
        self.y += self.direction.y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))
        
        # Mata o laser se sair da tela (limites simples)
        if self.rect.bottom < -100 or self.rect.top > ALTURA + 100:
             self.kill()
        elif self.rect.right < -100 or self.rect.left > LARGURA + 100:
             self.kill()


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player1, player2, all_groups):
        super().__init__()

        # assets MUST contain ALIEN_IMG
        self.assets = assets
        self.image = self.assets[ALIEN_IMG]
        self.rect = self.image.get_rect(midbottom=(x, y))

        # referências aos jogadores
        self.player1 = player1
        self.player2 = player2

        # referência aos grupos (dicionário)
        self.all_groups = all_groups  # espera chaves: 'all_sprites', 'enemy_lasers', ...

        # limites de patrulha (não usados neste Alien parado, mas mantidos)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right

        # Alien PARADO: speed 0
        self.patrol_speed = 0
        self.speedx = 0

        # parâmetros de tiro
        self.shoot_cooldown = 2000  # ms
        self.last_shot = pygame.time.get_ticks()
        self.shoot_range = 600  # px

        # máscara opcional (sem try/except - assume surface correta)
        self.mask = pygame.mask.from_surface(self.image)

    def get_closest_target(self):
        """Retorna jogador válido mais próximo (player1 ou player2) ou None."""
        candidates = [p for p in (self.player1, self.player2) if p is not None and not getattr(p, "dead", False)]
        if not candidates:
            return None
        return min(candidates, key=lambda p: (p.rect.centerx - self.rect.centerx)**2 + (p.rect.centery - self.rect.centery)**2)

    def update(self, dt):
        # Alien parado: deslocamento horizontal zero por padrão
        self.rect.x += int(self.speedx * dt * 60)

        now = pygame.time.get_ticks()
        player_target = self.get_closest_target()
        if player_target is None:
            return

        dist_x = player_target.rect.centerx - self.rect.centerx

        if abs(dist_x) < self.shoot_range and now - self.last_shot > self.shoot_cooldown:
            self.last_shot = now

            # mira diretamente no jogador (dx, dy)
            dx = player_target.rect.centerx - self.rect.centerx
            dy = player_target.rect.centery - self.rect.centery

            laser = EnemyLaser(self.rect.centerx, self.rect.centery, dx, dy, self.assets)
            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)



class OVNI(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player1, player2, all_groups):
        super().__init__()

        # assets MUST contain OVNI_IMG
        self.assets = assets
        self.image = self.assets[OVNI_IMG]
        self.rect = self.image.get_rect(center=(x, y))

        self.player1 = player1
        self.player2 = player2
        self.all_groups = all_groups

        # limites da patrulha (coordenadas do MUNDO)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right

        self.patrol_speed = 3
        self.speedx = self.patrol_speed

        # flutuação vertical
        self.base_y = y
        self.hover_range = 10
        self.hover_speed = 0.006  # ajuste para velocidade de "bob"

        # tiro
        self.shoot_cooldown = 1500
        self.last_shot = pygame.time.get_ticks()
        self.shoot_range = 1000

        # máscara (assume imagem válida)
        self.mask = pygame.mask.from_surface(self.image)

    def get_closest_target(self):
        candidates = [p for p in (self.player1, self.player2) if p is not None and not getattr(p, "dead", False)]
        if not candidates:
            return None
        return min(candidates, key=lambda p: (p.rect.centerx - self.rect.centerx)**2 + (p.rect.centery - self.rect.centery)**2)

    def update(self, dt):
        # patrulha horizontal entre limites
        self.rect.x += int(self.speedx * dt * 60)
        if self.rect.right > self.patrol_right:
            self.speedx = -abs(self.patrol_speed)
        elif self.rect.left < self.patrol_left:
            self.speedx = abs(self.patrol_speed)

        # flutuação vertical suave (seno)
        ticks = pygame.time.get_ticks()
        self.rect.centery = int(self.base_y + math.sin(ticks * self.hover_speed) * self.hover_range)

        now = pygame.time.get_ticks()
        player_target = self.get_closest_target()
        if player_target is None:
            return

        dist_x = player_target.rect.centerx - self.rect.centerx

        # só atira se alvo estiver dentro do alcance HORIZONTAL e estiver abaixo do OVNI
        if (abs(dist_x) < self.shoot_range and
            player_target.rect.top > self.rect.bottom and
            now - self.last_shot > self.shoot_cooldown):
            self.last_shot = now

            # tiro vertical para baixo (dir_x=0, dir_y=1)
            laser = EnemyLaser(self.rect.midbottom[0], self.rect.midbottom[1], 0, 1, self.assets, speed=500)
            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)
