# player.py
import os
import math
import pygame


class SimpleBullet:
    """
    Projétil simples, usado tanto por jogadores quanto por chefes.

    O que faz:
        - Mantém posição (x, y) e direção normalizada (dx, dy).
        - Move-se a uma velocidade constante multiplicada pelo delta time (dt).
        - Possui vida útil (life) em segundos; quando chega a 0 marca alive = False.
        - Pode desenhar-se como um círculo e testar colisão circular contra um rect.

    Recebe (construtor __init__):
        - x, y: posição inicial (pixeis).
        - dir_x, dir_y: vetor de direção (não precisa ser normalizado).
        - speed: velocidade em pixels por segundo (float, padrão 300.0).
        - color: cor do projétil (tupla RGB, padrão (255, 100, 180)).
        - radius: raio do projétil em pixels (int, padrão 6).

    Atributos públicos importantes:
        - x, y: posição em float.
        - dx, dy: direção unitária normalizada.
        - speed: velocidade em px/s.
        - color, radius: aparência.
        - alive: bool indicando se o projétil deve ser mantido.
        - life: tempo restante em segundos.

    Métodos:
        - update(dt): atualiza posição e decrementa vida.
        - draw(surf): desenha o projétil na surface passada.
        - collides_rect(rect): checa colisão do círculo com um pygame.Rect.
    """

    def __init__(self, x, y, dir_x, dir_y, speed=300.0, color=(255, 100, 180), radius=6):
        self.x = float(x)
        self.y = float(y)
        # normaliza o vetor de direção; evita divisão por zero
        l = math.hypot(dir_x, dir_y) or 1.0
        self.dx = dir_x / l
        self.dy = dir_y / l
        self.speed = speed
        self.color = color
        self.radius = radius
        self.alive = True
        # tempo de vida em segundos — após expirar o projétil morre (alive=False)
        self.life = 4.0  # segundos

    def update(self, dt):
        """
        Atualiza posição do projétil.

        Recebe:
            - dt: delta time em segundos (float).
        Efeitos:
            - Move a bala por dx * speed * dt, dy * speed * dt.
            - Decrementa self.life por dt; se <= 0, marca alive = False.

        Retorna:
            - None (efeitos colaterais nos atributos).
        """
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        """
        Desenha o projétil como um círculo preenchido na surface fornecida.

        Recebe:
            - surf: pygame.Surface onde desenhar.

        Retorna:
            - None.
        """
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)

    def collides_rect(self, rect):
        """
        Testa colisão entre o círculo do projétil e um pygame.Rect (AABB).
        Usa projeção do centro do círculo no retângulo para calcular distância mínima.

        Recebe:
            - rect: pygame.Rect com o qual testar colisão.

        Retorna:
            - True se houver interseção (colisão), False caso contrário.
        """
        closest_x = max(rect.left, min(int(self.x), rect.right))
        closest_y = max(rect.top, min(int(self.y), rect.bottom))
        dx = int(self.x) - closest_x
        dy = int(self.y) - closest_y
        return (dx * dx + dy * dy) <= (self.radius * self.radius)


class PlayerSimple:
    """
    Classe do jogador com suporte a animação de caminhada e mecânicas básicas.

    O que faz (resumo):
        - Gerencia posição/retângulo do jogador, movimento horizontal, salto (velocidade vertical),
          gravidade, animação de caminhada (frames), mira e disparo.
        - Controla vida, invulnerabilidade temporária (pisca na barra), som de tiro e estado de "dead".
        - Fornece métodos para entrada via teclado, pular, atirar, tomar dano e desenhar.

    Construtor (__init__) — parâmetros:
        - x: posição inicial X (int) — coordenada esquerda do jogador.
        - ground_y: coordenada Y do chão (int) — usado para posicionar bottom do rect.
        - screen_height: altura da tela (int) — usada para dimensionar sprites.
        - image_path: caminho para imagem estática (str) — usado se não houver frames.
        - walk_frames_paths: lista de caminhos para frames de caminhada (list[str]) — opcional.
        - walk_frame_interval: intervalo entre frames de caminhada em segundos (float).

    Atributos públicos notáveis:
        - rect: pygame.Rect representando caixa do jogador (posição e tamanho).
        - vel_x, vel_y: velocidades em px/s (float).
        - SPEED: velocidade de corrida horizontal (px/s).
        - JUMP_VELOCITY: velocidade inicial do pulo (px/s negativa para subir).
        - GRAVITY: aceleração gravitacional (px/s^2).
        - grounded: bool se o jogador está no chão.
        - fire_cooldown: tempo mínimo entre tiros em segundos.
        - _time_since_last_shot: tempo acumulado desde último tiro.
        - shot_sound: pygame.mixer.Sound ou None.
        - health, max_health: vida atual e máxima (float / int).
        - invuln_time: tempo de invulnerabilidade após tomar dano.
        - _invuln_timer: timer atual de invulnerabilidade.
        - dead: bool indicando se está morto.
        - aim: tupla (ax, ay) direção de mira normalizada por componente (-1..1).
        - facing_right: bool — orientação para flip do sprite.
        - use_walk, walk_frames, walk_frame_idx, walk_frame_time: controle de animação.
    """

    def __init__(self, x, ground_y, screen_height, image_path=None, walk_frames_paths=None, walk_frame_interval=0.10):
        # posição vertical do chão (y de onde o jogador "pisa")
        self.ground_y = ground_y
        self.image = None
        self.walk_frames = []
        self.walk_frame_idx = 0
        self.walk_frame_time = 0.0
        self.walk_frame_interval = walk_frame_interval
        self.use_walk = False

        # carregar frames de caminhada se fornecidos (tenta abrir cada caminho)
        if walk_frames_paths:
            frames = []
            for p in walk_frames_paths:
                if os.path.exists(p):
                    try:
                        img = pygame.image.load(p).convert_alpha()
                        frames.append(img)
                    except Exception:
                        # ignora frames que falharem ao carregar
                        pass
            if frames:
                # dimensiona os frames para ocupar ~25% da altura da tela
                target_h = int(screen_height * 0.25)
                scaled = []
                for img in frames:
                    # escala preservando proporção usando rotozoom (sem rotação)
                    scale = target_h / img.get_height()
                    scaled.append(pygame.transform.rotozoom(img, 0, scale))
                self.walk_frames = scaled
                self.use_walk = True

        # se não há animação, tenta carregar imagem estática
        if not self.use_walk and image_path and os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path).convert_alpha()
                target_h = int(screen_height * 0.25)
                scale = target_h / img.get_height()
                self.image = pygame.transform.rotozoom(img, 0, scale)
            except Exception:
                self.image = None

        # determina largura/altura do sprite com base nos frames ou imagem; usa valores default caso não existam
        if self.use_walk and self.walk_frames:
            first = self.walk_frames[0]
            self.w = first.get_width()
            self.h = first.get_height()
        else:
            self.w = self.image.get_width() if self.image else 64
            self.h = self.image.get_height() if self.image else 128

        # rect posicionado de modo que bottom coincida com ground_y
        self.rect = pygame.Rect(x, ground_y - self.h, self.w, self.h)
        self.vel_x = 0.0
        self.vel_y = 0.0
        # constantes de movimento (px/s e px/s^2)
        self.SPEED = 700.0
        self.JUMP_VELOCITY = -1500.0
        self.GRAVITY = 3000.0
        self.grounded = True
        # controle de tiro
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.gun_offset = (self.w // 2, self.h // 2)

        # som de tiro (opcional)
        shot_path = os.path.join('assets', 'sounds', 'som6.mp3')
        self.shot_sound = None
        if os.path.exists(shot_path):
            try:
                self.shot_sound = pygame.mixer.Sound(shot_path)
                self.shot_sound.set_volume(0.2)
            except Exception:
                self.shot_sound = None

        # vida / invulnerabilidade
        self.max_health = 8
        self.health = float(self.max_health)
        self.invuln_time = 0.8
        self._invuln_timer = 0.0
        self.dead = False

        # mira e orientação
        self.aim = (1, 0)  # mira inicial apontando para a direita
        self.facing_right = True

    # ------------------------ CONTROLES ------------------------

    def handle_input_keyboard(self, keys, left_key, right_key, look_up_key, aim_keys):
        """
        Processa entrada de teclado para mover e mirar o jogador.

        Recebe:
            - keys: resultado de pygame.key.get_pressed() (sequência booleana).
            - left_key, right_key: códigos pygame para mover esquerda/direita.
            - look_up_key: tecla para mirar pra cima (pode ser None/False se não houver).
            - aim_keys: dicionário {tecla: (ax, ay)} para controlar a mira por teclas.

        Efeitos:
            - Ajusta self.vel_x com base nas teclas de movimento.
            - Atualiza self.facing_right conforme velocidade horizontal.
            - Se look_up_key estiver pressionada, seta mira para (0, -1).
            - Caso contrário, acumula vetores de aim das teclas em aim_keys e normaliza por componente
              (mantém componentes dentro de -1..1).

        Retorna:
            - None (modifica atributos do objeto).
        """
        if self.dead:
            self.vel_x = 0
            return
        vx = 0.0
        if keys[left_key]:
            vx = -self.SPEED
        if keys[right_key]:
            vx = self.SPEED
        self.vel_x = vx
        if self.vel_x > 0:
            self.facing_right = True
        elif self.vel_x < 0:
            self.facing_right = False
        if look_up_key and keys[look_up_key]:
            # prioridade para mirar para cima
            self.aim = (0, -1)
        else:
            ax = 0
            ay = 0
            # soma componentes das teclas de mira
            for k, vec in aim_keys.items():
                if keys[k]:
                    ax += vec[0]
                    ay += vec[1]
            if ax != 0 or ay != 0:
                # limita cada componente a -1..1 (não normaliza vetorialmente; é intencional)
                ax = max(-1, min(1, ax))
                ay = max(-1, min(1, ay))
                self.aim = (ax, ay)

    def try_jump(self):
        """
        Tenta fazer o jogador pular.

        Condições:
            - Não faz nada se self.dead for True.
            - Só pula (aplica velocidade vertical) se estiver no chão (self.grounded == True).

        Efeitos:
            - Define self.vel_y para JUMP_VELOCITY (valor negativo para subir) e marca grounded=False.

        Retorna:
            - None.
        """
        if self.dead:
            return
        if self.grounded:
            self.vel_y = self.JUMP_VELOCITY
            self.grounded = False

    # ------------------------ LÓGICA ------------------------

    def update(self, dt, screen_width):
        """
        Atualiza lógica física e de animação do jogador.

        Recebe:
            - dt: delta time em segundos (float).
            - screen_width: largura da tela (int) usada para limitar movimento horizontal.

        Efeitos observáveis:
            - Atualiza temporizadores (tiro e invulnerabilidade).
            - Move o rect horizontalmente segundo vel_x * dt e limita dentro da tela.
            - Aplica gravidade incrementando vel_y por GRAVITY * dt e atualiza rect.y.
            - Se o jogador atingir ground_y, ajusta rect.bottom e zera vel_y (fica grounded = True).
            - Atualiza animação de caminhada (walk_frames) quando se move no chão:
                - walk_frame_time acumula dt; avança frames quando excede walk_frame_interval.
                - Caso não se mova, reseta para frame 0.

        Retorna:
            - None (modifica atributos como rect, vel_y, walk_frame_idx, etc).
        """
        if self.dead:
            return
        # tempo desde o último tiro
        self._time_since_last_shot += dt
        # invulnerabilidade
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        # movimento horizontal e clamp à tela
        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

        # gravidade / salto
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0.0
            self.grounded = True
        else:
            self.grounded = False

        # animação de caminhada (se configurada)
        if self.use_walk and self.walk_frames:
            moving = (abs(self.vel_x) > 5.0) and self.grounded
            if moving:
                self.walk_frame_time += dt
                if self.walk_frame_time >= self.walk_frame_interval:
                    # pode avançar mais de 1 frame caso dt seja grande; calcula quantos passos
                    steps = int(self.walk_frame_time / self.walk_frame_interval)
                    self.walk_frame_idx = (self.walk_frame_idx + steps) % len(self.walk_frames)
                    self.walk_frame_time -= steps * self.walk_frame_interval
            else:
                # parada -> volta ao primeiro frame
                self.walk_frame_idx = 0
                self.walk_frame_time = 0.0

    def can_shoot(self):
        """
        Indica se o jogador pode atirar agora (não morto e cooldown expirado).

        Retorna:
            - True se pode atirar, False caso contrário.
        """
        return (not self.dead) and (self._time_since_last_shot >= self.fire_cooldown)

    def shoot(self, direction):
        """
        Tenta disparar um projétil na direção passada.

        Recebe:
            - direction: tupla (dx, dy) com direção desejada; se (0,0) usa self.facing_right.

        Efeitos:
            - Se puder atirar (can_shoot), reseta o timer de tiro e instancia um SimpleBullet
              partindo do centro do jogador. Toca som de tiro se disponível.

        Retorna:
            - instância de SimpleBullet criada se o tiro ocorreu.
            - None se não pôde atirar (cooldown ou morto).
        """
        if not self.can_shoot():
            return None
        self._time_since_last_shot = 0.0
        spawn_x = self.rect.centerx
        spawn_y = self.rect.centery
        dx, dy = direction
        # se direção vazia, atira para frente segundo orientação atual
        if dx == 0 and dy == 0:
            dx = 1.0 if self.facing_right else -1.0
        b = SimpleBullet(spawn_x, spawn_y, dx, dy, speed=700.0, color=(255, 105, 180), radius=6)
        if self.shot_sound:
            try:
                self.shot_sound.play()
            except Exception:
                # problemas com mixer são ignorados para não travar o jogo
                pass
        return b

    def take_damage(self, amount):
        """
        Aplica dano ao jogador levando em conta invulnerabilidade temporária.

        Recebe:
            - amount: valor numérico de dano a subtrair da vida.

        Efeitos:
            - Se _invuln_timer > 0 ou dead == True, ignora (retorna False).
            - Caso contrário subtrai health, reinicia _invuln_timer = invuln_time.
            - Se health <= 0 marca dead = True.

        Retorna:
            - True se o dano foi aplicado.
            - False se o dano foi ignorado (invulnerável ou já morto).
        """
        if self._invuln_timer > 0.0 or self.dead:
            return False
        self.health -= amount
        self._invuln_timer = self.invuln_time
        if self.health <= 0:
            self.dead = True
        return True

    # ------------------------ DESENHO ------------------------

    def draw(self, surface):
        """
        Desenha o jogador na surface passada:
            - Sprite animado (walk_frames) se disponível; ou imagem estática; ou retângulo fallback.
            - Barra de vida acima do jogador com indicação de invulnerabilidade (pisca azul).
            - Não desenha nada se dead == True.

        Recebe:
            - surface: pygame.Surface onde desenhar.

        Retorna:
            - None (desenha diretamente na surface).
        """
        if self.dead:
            return

        # sprite animado ou imagem estática
        if self.use_walk and self.walk_frames:
            frame = self.walk_frames[self.walk_frame_idx]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        elif self.image:
            frame = self.image
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            surface.blit(frame, (self.rect.x, self.rect.y))
        else:
            # fallback: desenha um retângulo simples representando o jogador
            pygame.draw.rect(surface, (200, 30, 30), self.rect)

        # barra de vida (background + preenchimento proporcional)
        bar_w = max(40, self.w)
        bar_h = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - (bar_h + 6)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 30, 50), bg_rect)

        # razão atual de HP (0.0 a 1.0)
        hp_ratio = max(0.0, min(1.0, float(self.health) / float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

        # cor de preenchimento muda durante invulnerabilidade (efeito de piscar)
        if self._invuln_timer > 0.0:
            # pisca azul claro durante invulnerabilidade (usa tempo do sistema)
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                fill_color = (120, 180, 255)
            else:
                fill_color = (80, 130, 220)
        else:
            fill_color = (40, 140, 255)

        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, fill_rect)

        # borda da barra
        pygame.draw.rect(surface, (200, 200, 220), bg_rect, 1)
