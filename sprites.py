import pygame
import math
from config import LARGURA , ALTURA , GRAVIDADE 
from assets import ASTRONAUTA_IMG , ALIEN_IMG , OVNI_IMG , ENEMY_LASER_IMG

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

class EnemyLaser(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_x, dir_y, assets, speed=400):
        super().__init__()
        self.image = assets[ENEMY_LASER_IMG]
        self.rect = self.image.get_rect()
        
        # Posição inicial (floats para precisão)
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (self.x, self.y)
        
        self.speed = speed
        self.dir_x = dir_x
        self.dir_y = dir_y

    def update(self, dt):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))
        
        # Mata o laser se sair da tela (limites simples)
        if self.rect.bottom < 0 or self.rect.top > ALTURA:
            self.kill()

class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player1, player2, all_groups):
        super().__init__()
        self.assets = assets
        self.image = self.assets[ALIEN_IMG]
        self.rect = self.image.get_rect(midbottom=(x, y))
        
        # Referências
        self.player1 = player1  # <-- MUDOU AQUI
        self.player2 = player2  # <-- MUDOU AQUI
        self.all_groups = all_groups # Dicionário com ('all_sprites', 'enemy_lasers')

        # Limites da patrulha (coordenadas do MUNDO)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        
        self.patrol_speed = 2 # Velocidade da patrulha
        self.speedx = self.patrol_speed

        # Lógica de tiro
        self.shoot_cooldown = 2000 # Cooldown em ms (2 segundos)
        self.last_shot = pygame.time.get_ticks()
        self.shoot_range = 600 # Distância (em pixels) para começar a atirar

    def get_closest_target(self):
        """Decide qual jogador está mais perto."""
        # Calcula a distância (ao quadrado) para o J1
        dist1_sq = (self.player1.rect.centerx - self.rect.centerx)**2 + (self.player1.rect.centery - self.rect.centery)**2
        # Calcula a distância (ao quadrado) para o J2
        dist2_sq = (self.player2.rect.centerx - self.rect.centerx)**2 + (self.player2.rect.centery - self.rect.centery)**2
        
        # Retorna o jogador com a menor distância
        if dist1_sq <= dist2_sq:
            return self.player1
        else:
            return self.player2

    def update(self, dt):
        # 1. Movimento de Patrulha
        self.rect.x += self.speedx
        # ... (lógica de patrulha) ...
            
        # 2. Lógica de Tiro
        now = pygame.time.get_ticks()
        
        # --- DECIDE O ALVO ANTES DE ATIRAR ---
        player_target = self.get_closest_target() # <-- MUDOU AQUI
        # -------------------------------------
        
        # Distância horizontal até o ALVO ESCOLHIDO
        dist_x = player_target.rect.centerx - self.rect.centerx
        
        # Verifica se o alvo está no alcance e o cooldown acabou
        if abs(dist_x) < self.shoot_range and now - self.last_shot > self.shoot_cooldown:
            self.last_shot = now
            
            # ... (resto do código de tiro, ele usará 'dist_x' do alvo correto) ...
            dir_x = 1 if dist_x > 0 else -1
            dir_y = 0 
            
            laser = EnemyLaser(self.rect.centerx, self.rect.centery, 
                               dir_x, dir_y, self.assets)
            
            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)

class OVNI(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player_target, all_groups):
        super().__init__()
        self.assets = assets
        self.image = self.assets[OVNI_IMG]
        self.rect = self.image.get_rect(center=(x, y))
        
        self.player = player_target
        self.all_groups = all_groups

        # Limites da patrulha (coordenadas do MUNDO)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        
        self.patrol_speed = 3
        self.speedx = self.patrol_speed
        
        # Lógica de flutuação
        self.base_y = y
        self.hover_range = 10 # Flutua 10px para cima e para baixo
        self.hover_speed = 0.5 

        # Lógica de tiro
        self.shoot_cooldown = 1500 # 1.5 segundos
        self.last_shot = pygame.time.get_ticks()
        self.shoot_range = 400 # Alcance horizontal
    
    def get_closest_target(self):
        """Decide qual jogador está mais perto."""
        # Calcula a distância (ao quadrado) para o J1
        dist1_sq = (self.player1.rect.centerx - self.rect.centerx)**2 + (self.player1.rect.centery - self.rect.centery)**2
        # Calcula a distância (ao quadrado) para o J2
        dist2_sq = (self.player2.rect.centerx - self.rect.centerx)**2 + (self.player2.rect.centery - self.rect.centery)**2
        
        # Retorna o jogador com a menor distância
        if dist1_sq <= dist2_sq:
            return self.player1
        else:
            return self.player2

    def update(self, dt):
        # 1. Movimento de Patrulha (Horizontal)
        self.rect.x += self.speedx
        
        if self.rect.right > self.patrol_right:
            self.speedx = -self.patrol_speed
        elif self.rect.left < self.patrol_left:
            self.speedx = self.patrol_speed
            
        # 2. Movimento de Flutuação (Vertical)
        # Usamos seno para criar um movimento suave de "bob"
        ticks = pygame.time.get_ticks()
        self.rect.centery = self.base_y + math.sin(ticks * self.hover_speed * dt) * self.hover_range

        # 3. Lógica de Tiro (Só atira para baixo)
        now = pygame.time.get_ticks()
        
        # --- DECIDE O ALVO ANTES DE ATIRAR ---
        player_target = self.get_closest_target() # Escolhe o alvo mais próximo
        # -------------------------------------
        
        # Distância horizontal do ALVO ESCOLHIDO
        dist_x = player_target.rect.centerx - self.rect.centerx
        
        # Verifica se:
        # 1. O alvo está no alcance horizontal (abs(dist_x))
        # 2. O alvo está ABAIXO do OVNI (player_target.rect.top > self.rect.bottom)
        # 3. O cooldown acabou
        if (abs(dist_x) < self.shoot_range and 
            player_target.rect.top > self.rect.bottom and 
            now - self.last_shot > self.shoot_cooldown):
            
            self.last_shot = now
            
            # Atira reto para baixo
            dir_x = 0
            dir_y = 1 
            
            # Cria o laser (saindo de 'midbottom')
            laser = EnemyLaser(self.rect.midbottom[0], self.rect.midbottom[1], 
                               dir_x, dir_y, self.assets, speed=500)
            
            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)