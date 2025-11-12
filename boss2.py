# boss2.py
import os
import sys
import math
import pygame

from player import PlayerSimple, SimpleBullet
from utils import show_quadrinhos_sequence
from config import (
    POST_BOSS2_QUADRINHOS,
    TUTORIAL_PATHS,
    QUADRINHO_DURATION_MS,
    JOYSTICK_TUTORIAL_BUTTON_B,
    BOSS_HAND_BULLET_SPEED,
)


class Boss2:
    """
    Chefe 2: nave com duas 'mãos' que atiram balas e disparam lasers.
    """
    def __init__(self, x, y, screen_w, screen_h, image_path=None, bullet_image_path=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * 0.35)
            scale = target_h / img.get_height()
            self.image = pygame.transform.rotozoom(img, 0, scale)

        self.w = self.image.get_width() if self.image else 200
        self.h = self.image.get_height() if self.image else 150
        self.rect = pygame.Rect(x, y, self.w, self.h)

        self.speed = 140.0
        self.direction = 1
        self.patrol_min_x = 50
        self.patrol_max_x = screen_w - 50 - self.w
        self.bob_amplitude = 30.0
        self.bob_frequency = 0.8
        self._time = 0.0

        self.max_health = 60
        self.health = float(self.max_health)

        # mãos offsets (posição relativa em x)
        self.hand_offsets = [int(self.w * 0.22), int(self.w * 0.78) - 12]
        self.hand_bullet_cooldowns = [1.2, 1.2]
        self._time_since_last_bullet = [0.0, 0.0]
        self.hand_laser_cooldowns = [6.0, 6.0]
        self._time_since_last_laser = [0.0, 0.0]

        self.laser_width = 120
        self.laser_height = int(screen_h * 0.55)
        self.laser_duration = 1.2
        self.laser_damage_per_second = 3.0

    def update(self, dt):
        self._time += dt
        for i in range(len(self._time_since_last_bullet)):
            self._time_since_last_bullet[i] += dt
        for i in range(len(self._time_since_last_laser)):
            self._time_since_last_laser[i] += dt

        self.rect.x += int(self.direction * self.speed * dt)
        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1

        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

    def try_shoot_hands_at_players(self, player_centers):
        """
        Atira das mãos direcionadas ao jogador mais próximo.
        Retorna lista de SimpleBullet.
        """
        bullets = []
        if not player_centers:
            return bullets

        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_bullet[i] < self.hand_bullet_cooldowns[i]:
                continue
            spawn_x = int(self.rect.x + offset)
            spawn_y = draw_y + self.h - 10

            # escolher player mais próximo
            best = None
            best_dist = None
            for c in player_centers:
                dx = c[0] - spawn_x
                dy = c[1] - spawn_y
                d = dx * dx + dy * dy
                if best is None or d < best_dist:
                    best = (dx, dy)
                    best_dist = d
            if best is None:
                continue
            dx, dy = best
            l = math.hypot(dx, dy) or 1.0
            # usar velocidade configurável via BOSS_HAND_BULLET_SPEED
            b = SimpleBullet(spawn_x, spawn_y, dx / l, dy / l, speed=BOSS_HAND_BULLET_SPEED, color=(0, 255, 60), radius=8)
            bullets.append(b)
            self._time_since_last_bullet[i] = 0.0
        return bullets

    def try_fire_lasers(self):
        """
        Retorna lista de dicionários representando lasers ativos (offset,w,h,time).
        Cada laser gerenciado por run_boss2 (tempo/dano).
        """
        lasers = []
        for i, offset in enumerate(self.hand_offsets):
            if self._time_since_last_laser[i] < self.hand_laser_cooldowns[i]:
                continue
            laser = {'offset': offset - (self.laser_width // 2) + 6, 'w': self.laser_width, 'h': self.laser_height, 'time': 0.0}
            lasers.append(laser)
            self._time_since_last_laser[i] = 0.0
        return lasers

    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (80, 80, 80), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20), (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))


def run_boss2(screen, clock, W, H):
    """Executa a arena do Boss2 (tiros das mãos + lasers)."""
    fundo_path = os.path.join('assets', 'img', 'fundo_boss.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

    # música do chefe
    boss2_music_path = os.path.join('assets', 'sounds', 'som4.mp3')
    if os.path.exists(boss2_music_path):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(boss2_music_path)
            pygame.mixer.music.set_volume(0.18)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    # carregar frames de caminhada (se existirem)
    walk_frames_p1 = [os.path.join('assets', 'img', f'andar_{i}.png') for i in range(4)]
    walk_frames_p2 = [os.path.join('assets', 'img', f'andarv_{i}.png') for i in range(4)]

    player1 = PlayerSimple(
        W // 4, H, H,
        image_path=os.path.join('assets', 'img', 'astronauta1.png'),
        walk_frames_paths=walk_frames_p1,
        walk_frame_interval=0.10
    )
    player2 = PlayerSimple(
        3 * W // 4, H, H,
        image_path=os.path.join('assets', 'img', 'astronauta1.png'),
        walk_frames_paths=walk_frames_p2,
        walk_frame_interval=0.10
    )

    boss = Boss2(W // 4, 80, W, H, image_path=os.path.join('assets', 'img', 'nave boss.png'),
                 bullet_image_path=os.path.join('assets', 'img', 'bala.png'))

    bullets = []
    boss_bullets = []
    boss_lasers = []

    # configurar joysticks
    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        joysticks.append(j)
    trigger_prev = [False] * len(joysticks)
    TRIGGER_THRESHOLD = 0.5

    while True:
        dt = clock.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return False
                if ev.key == pygame.K_w:
                    player1.try_jump()
                if ev.key == pygame.K_i:
                    player2.try_jump()
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player1.shoot((dx / length, dy / length))
                    if b:
                        bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                        dy = 0.0
                    length = math.hypot(dx, dy) or 1.0
                    b = player2.shoot((dx / length, dy / length))
                    if b:
                        bullets.append(b)
            if ev.type == pygame.JOYBUTTONDOWN:
                if ev.button == 0:
                    if ev.joy == 0:
                        player1.try_jump()
                    elif ev.joy == 1:
                        player2.try_jump()
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)

        # joystick poll (movement + aim + trigger rising-edge)
        for i, j in enumerate(joysticks):
            ax = j.get_axis(0) if j.get_numaxes() > 0 else 0.0
            if i == 0:
                player1.vel_x = ax * player1.SPEED
                if player1.vel_x > 0:
                    player1.facing_right = True
                elif player1.vel_x < 0:
                    player1.facing_right = False
            else:
                player2.vel_x = ax * player2.SPEED
                if player2.vel_x > 0:
                    player2.facing_right = True
                elif player2.vel_x < 0:
                    player2.facing_right = False

            aim_ax = j.get_axis(2) if j.get_numaxes() > 2 else 0.0
            aim_ay = j.get_axis(3) if j.get_numaxes() > 3 else 0.0
            DEAD = 0.25
            if abs(aim_ax) >= DEAD or abs(aim_ay) >= DEAD:
                length = math.hypot(aim_ax, aim_ay) or 1.0
                nx, ny = aim_ax / length, aim_ay / length
                if i == 0:
                    player1.aim = (nx, ny)
                else:
                    player2.aim = (nx, ny)

            # trigger axis -> detect rising edge
            trigger_val = 0.0
            if j.get_numaxes() > 5:
                trigger_val = j.get_axis(5)
            elif j.get_numaxes() > 4:
                trigger_val = j.get_axis(4)
            pressed_now = abs(trigger_val) > TRIGGER_THRESHOLD

            if pressed_now and not trigger_prev[i]:
                player = player1 if i == 0 else player2
                dx, dy = player.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                    dy = 0.0
                length = math.hypot(dx, dy) or 1.0
                b = player.shoot((dx / length, dy / length))
                if b:
                    bullets.append(b)

            trigger_prev[i] = pressed_now

        # updates
        player1.update(dt, W)
        player2.update(dt, W)
        boss.update(dt)

        # boss mira e dispara nas mãos
        player_centers = [p.rect.center for p in (player1, player2) if p.health > 0]
        if player_centers:
            new_bullets = boss.try_shoot_hands_at_players(player_centers)
            if new_bullets:
                boss_bullets.extend(new_bullets)

        # lasers
        new_lasers = boss.try_fire_lasers()
        for l in new_lasers:
            l['time'] = 0.0
            boss_lasers.append(l)

        # atualizar listas e físicas
        bullets = [b for b in bullets if b.alive]
        boss_bullets = [b for b in boss_bullets if b.alive]

        for b in bullets:
            b.update(dt)

        for b in boss_bullets:
            b.update(dt)

        for l in boss_lasers[:]:
            l['time'] += dt
            if l['time'] >= boss.laser_duration:
                boss_lasers.remove(l)

        # colisões: tiros nos chefes
        for b in bullets[:]:
            if b.collides_rect(boss.rect):
                boss.health -= 1
                b.alive = False
                if b in bullets:
                    bullets.remove(b)

        # colisões: tiros do chefe nos jogadores
        for b in boss_bullets[:]:
            for p in (player1, player2):
                if p.health > 0 and b.collides_rect(p.rect):
                    if p.take_damage(1):
                        b.alive = False
                        if b in boss_bullets:
                            boss_bullets.remove(b)
                        break

        # lasers causam dano contínuo
        for l in boss_lasers:
            draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
            x = int(boss.rect.x + l['offset'])
            y = draw_y + boss.h
            laser_rect = pygame.Rect(x, y, l['w'], l['h'])
            for p in (player1, player2):
                if p.health > 0 and laser_rect.colliderect(p.rect):
                    dmg = boss.laser_damage_per_second * dt
                    p.health = max(0.0, p.health - dmg)
                    if p.health <= 0:
                        p.dead = True

        # verificar fim
        if boss.health <= 0:
            pygame.mixer.music.fadeout(600)
            show_quadrinhos_sequence(screen, clock, W, H, POST_BOSS2_QUADRINHOS, duration_ms=QUADRINHO_DURATION_MS)
            return True

        if not any((not p.dead and p.health > 0) for p in (player1, player2)):
            pygame.mixer.music.fadeout(600)
            return False

        # desenhar
        if fundo_image:
            screen.blit(fundo_image, (0, 0))
        else:
            screen.fill((0, 0, 0))

        boss.draw(screen)

        # desenhar lasers (overlay semi-transparente)
        for l in boss_lasers:
            draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
            x = int(boss.rect.x + l['offset'])
            y = draw_y + boss.h
            surf = pygame.Surface((l['w'], l['h']), pygame.SRCALPHA)
            surf.fill((255, 80, 80, 160))
            screen.blit(surf, (x, y))

        for b in bullets:
            b.draw(screen)
        for b in boss_bullets:
            b.draw(screen)

        player1.draw(screen)
        player2.draw(screen)

        pygame.display.flip()
