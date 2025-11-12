# sprites.py
import pygame
import math
from config import LARGURA, ALTURA, GRAVIDADE
from assets import ASTRONAUTA_IMG, ALIEN_IMG, OVNI_IMG

STILL = 0
JUMPING = 1
FALLING = 2

RED = (255, 0, 0)
YELLOW = (255, 255, 0)

class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_img, row, column):
        super().__init__()

class Astronauta(pygame.sprite.Sprite):
    def __init__(self, groups, assets, row, column, platforms):
        super().__init__()
        self.groups = groups
        self.assets = assets

        self.max_health = 5
        self.health = self.max_health
        self.invuln_time = 1.0
        self._invuln_timer = 0.0
        self.dead = False

        self.gun_offset_right = (20, -10)
        self.gun_offset_left = (-20, -10)
        self.facing = "right"

        self.image = assets[ASTRONAUTA_IMG]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()

        self.rect.centerx = LARGURA // 2 * column
        self.rect.bottom = ALTURA - 40 * row

        self.speedx = 0
        self.speedy = 0
        self.on_ground = True
        self.agachado = False

        self.platforms = platforms
        self.state = STILL
        self.drop_through_timer = 0.0
        self.drop_through_duration = 0.15

    def get_gun_tip(self):
        cx, cy = self.rect.centerx, self.rect.centery
        if getattr(self, "facing", "right") == "right":
            ox, oy = self.gun_offset_right
        else:
            ox, oy = self.gun_offset_left
        return cx + ox, cy + oy

    def update(self, dt):
        if self.dead:
            return

        prev_bottom = self.rect.bottom

        if self.drop_through_timer > 0:
            self.drop_through_timer -= dt
            if self.drop_through_timer <= 0:
                self.drop_through_timer = 0.0

        if self._invuln_timer > 0.0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        self.rect.x += int(self.speedx * dt * 60)

        # verifica plataformas one-way
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

        if self.rect.bottom >= ALTURA - 40:
            self.rect.bottom = ALTURA - 40
            self.speedy = 0
            self.on_ground = True

        if self.rect.left < 0:
            self.rect.left = 0

    def pular(self):
        if self.on_ground:
            self.speedy = -92
            self.on_ground = False

    def take_damage(self, amount: int) -> bool:
        if self._invuln_timer > 0.0 or self.dead:
            return False
        self.health -= amount
        self._invuln_timer = self.invuln_time
        if self.health <= 0:
            self.health = 0
            self.die()
        return True

    def die(self):
        self.dead = True
        self.kill()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dir_x, dir_y, speed=500, world_w=20000, world_h=20000):
        super().__init__()
        self.image = pygame.Surface((12, 6), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255,0,255), self.image.get_rect())
        self.orig_image = self.image

        self.x = float(x)
        self.y = float(y)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        length = math.hypot(dir_x, dir_y)
        if length == 0:
            self.dir_x, self.dir_y = 1.0, 0.0
        else:
            self.dir_x, self.dir_y = dir_x / length, dir_y / length

        self.speed = 700
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
    def __init__(self, x, y, target_dx, target_dy, speed=600, color=RED, width=8, height=22):
        super().__init__()
        self.speed = float(speed)
        length = math.hypot(target_dx, target_dy)
        if length == 0:
            self.direction = pygame.math.Vector2(0, 1)
        else:
            self.direction = pygame.math.Vector2(target_dx / length, target_dy / length)

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill(color)

        self.x = float(x)
        self.y = float(y)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        self.x += self.direction.x * self.speed * dt
        self.y += self.direction.y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))
        # marge grande para matar fora de mundo
        if (self.rect.bottom < -500 or self.rect.top > ALTURA + 500 or
            self.rect.right < -500 or self.rect.left > LARGURA + 500):
            self.kill()

class EnemyLaser(pygame.sprite.Sprite):
    def __init__(self, x, y, target_dx, target_dy, assets=None, speed=600, color=RED, width=10, height=30):
        """
        Laser inimigo: origin (x,y) em coordenadas do mundo,
        target_dx/dy = direção alvo (não precisa estar normalizada).
        assets é opcional (não usado aqui, mantido por compatibilidade).
        """
        super().__init__()
        self.speed = float(speed)
        self.color = color
        self.alive = True

        # Normaliza o vetor direção
        length = math.hypot(target_dx, target_dy)
        if length == 0:
            self.direction = pygame.math.Vector2(0, 1)
        else:
            self.direction = pygame.math.Vector2(target_dx / length, target_dy / length)

        # imagem do laser (retângulo rotacionado opcional)
        self.width = width
        self.height = height
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(self.color)

        # posição (usar floats para movimento suave)
        self.x = float(x)
        self.y = float(y)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    def update(self, dt):
        if not self.alive:
            self.kill()
            return
        # move usando direção normalizada * speed * dt
        self.x += self.direction.x * self.speed * dt
        self.y += self.direction.y * self.speed * dt
        self.rect.center = (int(self.x), int(self.y))

        # limite de desligamento (usar mundo/screen limits)
        if self.rect.bottom < -200 or self.rect.top > ALTURA + 200 or \
           self.rect.right < -200 or self.rect.left > LARGURA + 200:
            self.kill()


class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player1, player2, all_groups):
        super().__init__()
        self.assets = assets
        self.image = self.assets[ALIEN_IMG]
        self.rect = self.image.get_rect(midbottom=(x, y))

        self.player1 = player1
        self.player2 = player2
        self.all_groups = all_groups

        self.patrol_left = patrol_left
        self.patrol_right = patrol_right

        self.patrol_speed = 0
        self.speedx = 0

        # parâmetros de tiro ajustados
        self.shoot_cooldown = 1500  # ms entre tiros
        self.last_shot = pygame.time.get_ticks() - 2000
        self.shoot_range = 2500     # alcance efetivo (px) — AUMENTE conforme quiser
        self.laser_speed = 500      # velocidade do laser

        self.mask = pygame.mask.from_surface(self.image)

        # Vida do inimigo (exemplo)
        self.max_health = 10
        self.health = self.max_health
        self.dead = False

    def get_closest_target(self):
        candidates = [p for p in (self.player1, self.player2) if p is not None and not getattr(p, "dead", False)]
        if not candidates:
            return None
        return min(candidates, key=lambda p: (p.rect.centerx - self.rect.centerx)**2 + (p.rect.centery - self.rect.centery)**2)

    def take_damage(self, amount: int):
        if getattr(self, "dead", False):
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.die()

    def die(self):
        self.dead = True
        self.kill()

    def update(self, dt):
        # movimentação (se houver)
        self.rect.x += int(self.speedx * dt * 60)

        now = pygame.time.get_ticks()
        player_target = self.get_closest_target()
        if player_target is None:
            return

        # distância euclidiana
        dx = player_target.rect.centerx - self.rect.centerx
        dy = player_target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist <= self.shoot_range and (now - self.last_shot) >= self.shoot_cooldown:
            self.last_shot = now
            # cria laser apontando para o jogador
            laser = EnemyLaser(self.rect.centerx, self.rect.centery, dx, dy, speed=self.laser_speed, color=RED, width=4, height=15) # Exemplo: Fino e verticalizado (4x15)            # adiciona corretamente nos grupos passados pelo jogo
            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)


class OVNI(pygame.sprite.Sprite):
    def __init__(self, x, y, assets, patrol_left, patrol_right, player1, player2, all_groups):
        super().__init__()
        self.assets = assets
        self.image = self.assets[OVNI_IMG]
        self.rect = self.image.get_rect(center=(x, y))
        self.player1 = player1
        self.player2 = player2
        self.all_groups = all_groups

        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.patrol_speed = 3
        self.speedx = self.patrol_speed

        self.base_y = y
        self.hover_range = 10
        self.hover_speed = 0.006

        self.shoot_cooldown = 1200
        self.last_shot = pygame.time.get_ticks() - 2000
        self.shoot_range = 2500
        self.laser_speed = 450

        self.mask = pygame.mask.from_surface(self.image)

        # vida
        self.max_health = 15
        self.health = self.max_health
        self.dead = False

    def get_closest_target(self):
        candidates = [p for p in (self.player1, self.player2) if p is not None and not getattr(p, "dead", False)]
        if not candidates:
            return None
        return min(candidates, key=lambda p: (p.rect.centerx - self.rect.centerx)**2 + (p.rect.centery - self.rect.centery)**2)

    def take_damage(self, amount: int):
        if getattr(self, "dead", False):
            return
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.die()

    def die(self):
        self.dead = True
        self.kill()

    def update(self, dt):
        # patrulha horizontal
        self.rect.x += int(self.speedx * dt * 60)
        if self.rect.right > self.patrol_right:
            self.speedx = -abs(self.patrol_speed)
        elif self.rect.left < self.patrol_left:
            self.speedx = abs(self.patrol_speed)

        # flutuação vertical
        ticks = pygame.time.get_ticks()
        self.rect.centery = int(self.base_y + math.sin(ticks * self.hover_speed) * self.hover_range)

        now = pygame.time.get_ticks()
        player_target = self.get_closest_target()
        if player_target is None:
            return

        dx = player_target.rect.centerx - self.rect.centerx
        dy = player_target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        # o OVNI atira se o alvo estiver dentro do alcance (uso euclidiano)
        if dist <= self.shoot_range and (now - self.last_shot) >= self.shoot_cooldown:
            self.last_shot = now
            # opcional: apontar diretamente ao jogador (não só para baixo)
            laser = EnemyLaser(self.rect.midbottom[0], self.rect.midbottom[1], 0, 1, speed=self.laser_speed, color=YELLOW, width=20, height=80) # Exemplo: 20x80            self.all_groups['all_sprites'].add(laser)
            self.all_groups['enemy_lasers'].add(laser)