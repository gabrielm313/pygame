# boss1.py
import os
import sys
import math
import pygame

from player import PlayerSimple, SimpleBullet
from utils import show_quadrinhos_sequence
from config import (
    POST_BOSS1_QUADRINHO,
    TUTORIAL_PATHS,
    QUADRINHO_DURATION_MS,
    JOYSTICK_TUTORIAL_BUTTON_B,
)


class SlimePatch:
    """
    Representa uma poça/área de slime que causa dano ao jogador ao ficar em contato.

    Atributos principais:
      - rect: pygame.Rect com a área ocupada pelo slime (x, y, width, height)
      - dps: float, dano por segundo aplicado a qualquer jogador que estiver colidindo
      - duration: float, duração em segundos que a poça permanece ativa
      - time: float, tempo acumulado desde a criação (usado para expirar)
      - alive: bool, se a poça ainda está ativa
      - surface: Surface semi-transparente usada para desenhar a poça

    Métodos:
      - update(dt)
          Recebe delta time em segundos (float). Atualiza o timer interno e define alive=False
          quando o tempo excede duration.
          Parâmetros:
            dt (float): tempo em segundos desde o último frame.
          Retorno: None

      - collides_player(player)
          Verifica colisão simples entre a poça e um objeto player que possua `rect` e `dead`.
          Parâmetros:
            player: objeto jogador (espera-se ter atributos .rect e .dead)
          Retorno:
            bool -> True se colidir e o player não estiver morto, False caso contrário.

      - draw(surface)
          Desenha a superfície do slime na tela.
          Parâmetros:
            surface: pygame.Surface onde desenhar.
          Retorno: None
    """
    def __init__(self, x, y, width, height, dps=6.0, duration=8.0):
        self.rect = pygame.Rect(int(x), int(y), int(width), int(height))
        self.dps = float(dps)
        self.duration = float(duration)
        self.time = 0.0
        self.alive = True
        self.surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        self.surface.fill((20, 200, 40, 130))

    def update(self, dt):
        """
        Atualiza o timer da poça.
        Parâmetros:
          dt (float): tempo em segundos desde o último frame.
        Efeito:
          Incrementa self.time; se self.time >= self.duration, define self.alive = False.
        Retorno: None
        """
        self.time += dt
        if self.time >= self.duration:
            self.alive = False

    def collides_player(self, player):
        """
        Verifica colisão entre a poça e um jogador.

        Parâmetros:
          player: objeto com atributos `rect` (pygame.Rect) e `dead` (bool).

        Retorno:
          bool -> True se o player não for None, não estiver morto e houver interseção entre
                  player.rect e self.rect; False caso contrário.
        """
        if not player or getattr(player, "dead", False):
            return False
        return self.rect.colliderect(player.rect)

    def draw(self, surface):
        """
        Desenha a poça na surface fornecida.

        Parâmetros:
          surface: pygame.Surface onde desenhar.
        Retorno: None
        """
        surface.blit(self.surface, (self.rect.x, self.rect.y))


class Boss1:
    """
    Classe que representa o Boss1 (um inimigo que patrulha e solta poças de slime).

    Uso:
      boss = Boss1(x, y, screen_w, screen_h, image_path=None)

    Parâmetros do construtor:
      x (int): posição x inicial do chefe.
      y (int): posição y inicial do chefe.
      screen_w (int): largura da tela/arena (usado para limites de patrulha).
      screen_h (int): altura da tela/arena (usado para spawn do slime).
      image_path (str|None): caminho para a imagem do chefe (opcional).

    Atributos principais:
      - rect: pygame.Rect representando a posição e tamanho do chefe
      - speed: float velocidade horizontal
      - direction: int, 1 ou -1
      - patrol_min_x / patrol_max_x: limites de deslocamento no eixo x
      - _time, bob_amplitude, bob_frequency: usados para efeito de bob (movimento vertical oscilante)
      - max_health / health: vida do chefe
      - slime_*: parâmetros para criação de SlimePatch (cooldown, tamanho, dano, duração)

    Métodos:
      - update(dt)
          Atualiza posição e timers do chefe.
          Parâmetros:
            dt (float): delta time em segundos.
          Retorno: None

      - try_drop_slime()
          Tenta criar uma SlimePatch se o cooldown já tiver passado.
          Parâmetros: nenhum
          Retorno:
            SlimePatch | None -> novo objeto SlimePatch se spawnar, caso contrário None

      - draw(surface)
          Desenha o chefe (imagem se disponível) e a barra de vida.
          Parâmetros:
            surface: pygame.Surface onde desenhar.
          Retorno: None
    """
    def __init__(self, x, y, screen_w, screen_h, image_path=None):
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
        self._time = 0.0
        self.bob_amplitude = 10.0
        self.bob_frequency = 0.6

        self.max_health = 60
        self.health = float(self.max_health)

        self.slime_cooldown = 2.5
        self._time_since_last_slime = 0.0
        self.slime_width = int(self.w * 0.5)
        self.slime_height = 36
        self.slime_duration = 10.0
        self.slime_dps = 8.0

    def update(self, dt):
        """
        Atualiza o estado do chefe:
          - incrementa timers,
          - move horizontalmente aplicando limites de patrulha,
          - calcula offset vertical oscilante (bob).

        Parâmetros:
          dt (float): tempo em segundos desde o último frame.

        Retorno: None
        """
        self._time += dt
        self._time_since_last_slime += dt
        self.rect.x += int(self.direction * self.speed * dt)

        if self.rect.x < self.patrol_min_x:
            self.rect.x = self.patrol_min_x
            self.direction = 1
        elif self.rect.x > self.patrol_max_x:
            self.rect.x = self.patrol_max_x
            self.direction = -1

        self._y_offset = math.sin(2 * math.pi * self.bob_frequency * self._time) * self.bob_amplitude

    def try_drop_slime(self):
        """
        Tenta instanciar uma SlimePatch se o cooldown tiver expirado.

        Parâmetros: nenhum

        Retorno:
          SlimePatch -> se uma nova poça for criada
          None -> se o cooldown ainda não terminou
        """
        if self._time_since_last_slime < self.slime_cooldown:
            return None
        spawn_x = int(self.rect.centerx - self.slime_width // 2)
        spawn_y = int(self.screen_h - self.slime_height)
        patch = SlimePatch(
            spawn_x, spawn_y,
            self.slime_width, self.slime_height,
            dps=self.slime_dps, duration=self.slime_duration
        )
        self._time_since_last_slime = 0.0
        return patch

    def draw(self, surface):
        """
        Desenha o chefe (imagem se existir) e sua barra de vida.

        Parâmetros:
          surface: pygame.Surface onde desenhar.

        Retorno: None
        """
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        # desenha barra de vida acima do chefe
        pygame.draw.rect(surface, (40, 40, 40), (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20), (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))


def run_boss1(screen, clock, W, H):
    """
    Loop principal do estágio Boss1.

    Comportamento:
      - configura background, jogadores, chefe, sons e joysticks;
      - processa eventos de teclado e joystick (movimento, salto, tiro, mostrar tutorial);
      - atualiza entidades (jogadores, chefe, projéteis, poças de slime);
      - checa colisões (balas no chefe, jogadores nas poças);
      - termina retornando True se o jogador(s) derrotar o chefe,
        False se ambos os jogadores morrerem, ou False se ESC for pressionado para cancelar.

    Parâmetros:
      screen (pygame.Surface): superfície principal onde desenhar.
      clock (pygame.time.Clock): relógio usado para controlar FPS / delta time.
      W (int): largura da tela (em pixels).
      H (int): altura da tela (em pixels).

    Retorno:
      bool:
        True  -> chefe derrotado (fase vencida)
        False -> fase abortada (ESC) ou ambos os jogadores mortos
    """
    fundo_path = os.path.join('assets', 'img', 'fundo2.png')
    fundo_image = None
    if os.path.exists(fundo_path):
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))

    # carregar sprites dos jogadores (sequências de caminhada, se existirem)
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

    boss = Boss1(W // 2 - 200, 60, W, H, image_path=os.path.join('assets', 'img', 'boss2.png'))

    bullets = []
    boss_bullets = []
    slime_patches = []

    # som do rugido (opcional)
    roar_path = os.path.join('assets', 'sounds', 'som11.mp3')
    roar_sound = None
    if os.path.exists(roar_path):
        try:
            roar_sound = pygame.mixer.Sound(roar_path)
            roar_sound.set_volume(0.55)
        except Exception:
            pass
    ROAR_INTERVAL = 10.0
    _roar_timer = 0.0

    # música de fundo do estágio (opcional)
    boss1_music_path = os.path.join('assets', 'sounds', 'som10.mp3')
    if os.path.exists(boss1_music_path):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(boss1_music_path)
            pygame.mixer.music.set_volume(0.18)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    # configurar joysticks presentes (se houver)
    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        joysticks.append(j)
    trigger_prev = [False] * len(joysticks)
    TRIGGER_THRESHOLD = 0.5

    font = pygame.font.Font(None, 24)

    # loop principal do chefe
    while True:
        dt = clock.tick(60) / 1000.0

        # eventos do Pygame (teclado, mouse, joystick)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if ev.type == pygame.KEYDOWN:
                # ESC cancela o estágio e retorna False
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return False
                # comandos de salto e tiro para teclado
                if ev.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                    player1.try_jump()
                if ev.key == pygame.K_i:
                    player2.try_jump()
                if ev.key == pygame.K_x:
                    dx, dy = player1.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player1.facing_right else -1.0
                    b = player1.shoot((dx, dy))
                    if b:
                        bullets.append(b)
                if ev.key == pygame.K_RALT:
                    dx, dy = player2.aim
                    if dx == 0 and dy == 0:
                        dx = 1.0 if player2.facing_right else -1.0
                    b = player2.shoot((dx, dy))
                    if b:
                        bullets.append(b)

            if ev.type == pygame.JOYBUTTONDOWN:
                # botão A (index 0) usado para pular (por convenção)
                if ev.button == 0:
                    if ev.joy == 0:
                        player1.try_jump()
                    elif ev.joy == 1:
                        player2.try_jump()
                # botão B abre tutorial (mostra quadrinhos)
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)

        # leitura contínua dos joysticks para movimento, mira e gatilho (rising edge)
        for i, j in enumerate(joysticks):
            axis0 = j.get_axis(0) if j.get_numaxes() > 0 else 0.0
            player = player1 if i == 0 else player2
            player.vel_x = axis0 * player.SPEED
            if player.vel_x > 0:
                player.facing_right = True
            elif player.vel_x < 0:
                player.facing_right = False

            # mira analógica pelo stick direito (eixos 2 e 3)
            aim_ax = j.get_axis(2) if j.get_numaxes() > 2 else 0.0
            aim_ay = j.get_axis(3) if j.get_numaxes() > 3 else 0.0
            DEAD = 0.25
            if abs(aim_ax) >= DEAD or abs(aim_ay) >= DEAD:
                length = math.hypot(aim_ax, aim_ay) or 1.0
                player.aim = (aim_ax / length, aim_ay / length)

            # gatilho analógico (axis 4 ou 5) usado para atirar; detectar borda de subida para
            # evitar disparos contínuos enquanto o gatilho permanece pressionado
            trigger_val = 0.0
            if j.get_numaxes() > 5:
                trigger_val = j.get_axis(5)
            elif j.get_numaxes() > 4:
                trigger_val = j.get_axis(4)
            pressed_now = abs(trigger_val) > TRIGGER_THRESHOLD

            if pressed_now and not trigger_prev[i]:
                dx, dy = player.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                b = player.shoot((dx, dy))
                if b:
                    bullets.append(b)

            trigger_prev[i] = pressed_now

        # atualizações de lógica
        player1.update(dt, W)
        player2.update(dt, W)
        boss.update(dt)

        # som de rugido periódico
        _roar_timer += dt
        if _roar_timer >= ROAR_INTERVAL and roar_sound and boss.health > 0:
            roar_sound.play()
            _roar_timer = 0.0

        # boss tenta soltar poça de slime
        patch = boss.try_drop_slime()
        if patch:
            slime_patches.append(patch)

        # filtrar listas por entidades vivas
        bullets = [b for b in bullets if b.alive]
        boss_bullets = [b for b in boss_bullets if b.alive]
        slime_patches = [s for s in slime_patches if s.alive]

        # atualizar projéteis dos jogadores e checar colisão com o chefe
        for b in bullets:
            b.update(dt)
            if b.collides_rect(boss.rect):
                boss.health -= 1
                b.alive = False

        # atualizar poças e aplicar dano contínuo a jogadores que estiverem em contato
        for s in slime_patches:
            s.update(dt)
            for p in (player1, player2):
                if p.health > 0 and s.collides_player(p):
                    dmg = s.dps * dt
                    p.health = max(0.0, p.health - dmg)
                    if p.health <= 0:
                        p.dead = True

        # verificar condições de término:
        # - chefe derrotado -> retornar True
        if boss.health <= 0:
            pygame.mixer.music.fadeout(600)
            show_quadrinhos_sequence(screen, clock, W, H, [POST_BOSS1_QUADRINHO], duration_ms=QUADRINHO_DURATION_MS)
            return True

        # - todos os jogadores mortos -> retornar False
        if not any((not p.dead and p.health > 0) for p in (player1, player2)):
            pygame.mixer.music.fadeout(600)
            return False

        # desenhar cena
        if fundo_image:
            screen.blit(fundo_image, (0, 0))
        else:
            screen.fill((10, 10, 12))

        boss.draw(screen)
        for s in slime_patches:
            s.draw(screen)
        for b in bullets:
            b.draw(screen)
        for b in boss_bullets:
            b.draw(screen)

        player1.draw(screen)
        player2.draw(screen)

        hud = font.render(
            f"P1 HP: {int(player1.health)}   P2 HP: {int(player2.health)}   Boss: {int(boss.health)}",
            True, (255, 255, 255)
        )
        screen.blit(hud, (12, 12))
        pygame.display.flip()
