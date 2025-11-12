import pygame
import os
import math
import sys
import subprocess
from typing import Tuple, List, Optional

# ---------------- Utilidade: carregar frames de uma pasta ----------------
def load_frames_from_folder(folder: str, keep_alpha=True) -> List[pygame.Surface]:
    frames = []
    if not folder or not os.path.exists(folder):
        return frames
    names = sorted(os.listdir(folder))
    for n in names:
        fp = os.path.join(folder, n)
        if os.path.isfile(fp):
            try:
                img = pygame.image.load(fp)
            except Exception:
                continue
            img = img.convert_alpha() if keep_alpha else img.convert()
            frames.append(img)
    return frames

# Ajustado para onde os arquivos de animação (andar_0.png, andar_1.png) devem estar
# Se as imagens estiverem em 'assets/img/player_custom/', use isso.
ASSETS_DIR = 'assets/img/' 

# ---------------- Player (animação legs+torso/full) ----------------
class Player:
    def __init__(self, x, ground_y, screen_height,
                 image_path=None, scale_height_ratio=0.3,
                 anim_root='assets/img/'):
        self.ground_y = ground_y
        self.screen_height = screen_height
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_height * scale_height_ratio)
            scale = target_h / img.get_height() if img.get_height() != 0 else 1.0
            self.image = pygame.transform.rotozoom(img, 0, scale)
        self.w = self.image.get_width() if self.image else 64
        self.h = self.image.get_height() if self.image else 128
        self.rect = pygame.Rect(x, ground_y - self.h, self.w, self.h)

        # física
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.SPEED = 700.0
        self.JUMP_VELOCITY = -1500.0
        self.GRAVITY = 3000.0
        self.grounded = True

        # tiro
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.gun_offset = (self.w // 2, self.h // 2)

        self.shot_sound = None
        shot_path = os.path.join('assets', 'sounds', 'som6.mp3')
        if os.path.exists(shot_path):
            try:
                self.shot_sound = pygame.mixer.Sound(shot_path)
                self.shot_sound.set_volume(0.2 )
            except Exception:
                pass

        # vida / invuln / morte
        self.max_health = 5
        self.health = self.max_health
        self.invuln_time = 0.8
        self._invuln_timer = 0.0
        self.dead = False

        # animação (Original legs/torso)
        self.anim_root = anim_root
        self.legs_walk = load_frames_from_folder(os.path.join(anim_root, 'legs', 'walk'))
        self.legs_idle = load_frames_from_folder(os.path.join(anim_root, 'legs', 'idle'))
        self.torso_anims = {
             'neutral': load_frames_from_folder(os.path.join(anim_root, 'torso', 'neutral')),
             'up': load_frames_from_folder(os.path.join(anim_root, 'torso', 'up')),
             'down': load_frames_from_folder(os.path.join(anim_root, 'torso', 'down')),
             'upleft': load_frames_from_folder(os.path.join(anim_root, 'torso', 'upleft')),
             'upright': load_frames_from_folder(os.path.join(anim_root, 'torso', 'upright')),
             'downleft': load_frames_from_folder(os.path.join(anim_root, 'torso', 'downleft')),
             'downright': load_frames_from_folder(os.path.join(anim_root, 'torso', 'downright')),
        }
        self.full_jump = load_frames_from_folder(os.path.join(anim_root, 'full', 'jump'))
        self.full_crouch = load_frames_from_folder(os.path.join(anim_root, 'full', 'crouch'))

        self.legs_index = 0
        self.torso_index = 0
        self.legs_timer = 0.0
        self.torso_timer = 0.0
        self.legs_fps = 12.0
        self.torso_fps = 12.0
        self.state = 'parado'
        self.facing_right = True
        self.aim = (1, 0)

        self._apply_anim_dims()
        
        # --- Campos para Animação Customizada ---
        self.animations = {}           # Dicionário de animações customizadas (andar_N.png)
        self.current_animation = 'parado'
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_fps = 8.0     # FPS para animações customizadas
        
        # CHAMA O NOVO MÉTODO DE CARREGAMENTO
        self._load_custom_animation()

        # tiro
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        # Offset onde a bala deve spawnar (ajustado de acordo com a imagem/largura do player)
        self.gun_offset = (self.w // 2, self.h // 2)

        self.shot_sound = None
        # ... lógica para carregar self.shot_sound ...


    def _load_custom_animation(self):
        """
        Carrega a animação customizada (andar_N.png) do ASSETS_DIR global.
        """
        if not os.path.isdir(ASSETS_DIR):
            return

        animations = {}
        
        # parado (andar_0.png)
        p0 = os.path.join(ASSETS_DIR, 'andar_0.png')
        if os.path.exists(p0):
            try:
                animations['parado'] = [pygame.image.load(p0).convert_alpha()]
            except Exception:
                animations['parado'] = []

        # andando (procura por arquivos numerados andar_1..andar_N)
        walk_frames = []
        for i in range(1, 20):
            p = os.path.join(ASSETS_DIR, f'andar_{i}.png')
            if os.path.exists(p):
                try:
                    walk_frames.append(pygame.image.load(p).convert_alpha())
                except Exception:
                    pass
        
        if walk_frames:
             animations['andando'] = walk_frames

        # Aplica escala para combinar com player.h
        if animations and self.h > 0:
             for k, frames in animations.items():
                 scaled = []
                 for fr in frames:
                     if fr.get_height() != 0 and self.h:
                         scale = self.h / fr.get_height()
                         scaled.append(pygame.transform.rotozoom(fr, 0, scale))
                     else:
                         scaled.append(fr)
                 self.animations[k] = scaled
        
        # Define a animação inicial se carregada
        if 'parado' in self.animations:
            self.current_animation = 'parado'
        elif 'andando' in self.animations:
            self.current_animation = 'andando'

        if self.animations:
            print(f"[INFO] Player: Animações customizadas carregadas: {list(self.animations.keys())}")


    def set_animation(self, animation_name):
        """
        Alterna a animação customizada.
        """
        if self.current_animation != animation_name and animation_name in self.animations:
            self.current_animation = animation_name
            self.frame_index = 0
            self.animation_timer = 0.0
    
    def _apply_anim_dims(self):
        # ... (lógica existente para ajustar dimensões do rect)
        src = None
        if self.torso_anims.get('neutral'):
            lst = self.torso_anims['neutral']
            if lst:
                src = lst[0]
        if not src and self.image:
            src = self.image
        if not src and self.full_jump:
            src = self.full_jump[0]
        if src:
            try:
                self.w = src.get_width()
                self.h = src.get_height()
                self.rect.w = self.w
                self.rect.h = self.h
                self.rect.y = self.ground_y - self.h
            except Exception:
                pass


    def handle_input_keyboard(self, keys, left_key, right_key, look_up_key, aim_keys):
    
        # 1. Movimento Horizontal
        if keys[right_key] and not keys[left_key]:
            self.vel = self.run_speed
            self.direction = 1 # Direita
            self.anim_state = "andando"
            
        elif keys[left_key] and not keys[right_key]:
            self.vel = -self.run_speed
            self.direction = -1 # Esquerda
            self.anim_state = "andando"
            
        else:
            self.vel = 0
            self.anim_state = "parado"
        
        # Atualiza a posição X (movimento)
        self.rect.x += self.vel
        
        # 2. Pular (Se você tiver a lógica de pulo)
        # Exemplo:
        # if keys[pygame.K_SPACE] and not self.is_jumping:
        #     self.is_jumping = True
        #     self.y_vel = -self.jump_power
            
        # 3. Visar/Atirar (Se você tiver a lógica de mira/tiro)
        # if keys[aim_keys[0]]: # O primeiro item na lista P1_AIMS é geralmente a tecla de atirar
        #     self.shoot() 
        
        # Se nenhuma outra animação for definida, garante que o estado é "parado"
        if self.anim_state not in ["andando", "pulando", "atirando"]:
            self.anim_state = "parado"

    # ESTES MÉTODOS DEVEM ESTAR DENTRO DA CLASSE PLAYER

    def _update_legs_anim(self, dt):
        # Corrigindo a lógica para usar 'andando' em vez de 'walk' para sincronizar com o update
        if self.state == 'andando' and self.legs_walk:
            self.legs_timer += dt
            frame_dur = 1.0 / self.legs_fps
            while self.legs_timer >= frame_dur:
                self.legs_timer -= frame_dur
                self.legs_index = (self.legs_index + 1) % len(self.legs_walk)
        else:
            self.legs_index = 0
            self.legs_timer = 0.0

    def _choose_torso_key(self):
        ax, ay = self.aim
        if not self.grounded:
            if ay < 0:
                return 'up'
            if ay > 0:
                return 'down'
            return 'neutral'
        if ax == 0 and ay == 0:
            return 'neutral'
        if ay < 0:
            return 'up' if ax == 0 else ('upleft' if ax < 0 else 'upright')
        if ay > 0:
            return 'down' if ax == 0 else ('downleft' if ax < 0 else 'downright')
        return 'neutral'

    def _update_torso_anim(self, dt):
        key = self._choose_torso_key()
        frames = self.torso_anims.get(key) or self.torso_anims.get('neutral') or []
        if frames:
            self.torso_timer += dt
            frame_dur = 1.0 / self.torso_fps
            while self.torso_timer >= frame_dur:
                self.torso_timer -= frame_dur
                self.torso_index = (self.torso_index + 1) % len(frames)
        else:
            self.torso_index = 0
            self.torso_timer = 0.0


    def update(self, dt, screen_width):
        if self.dead:
            return
        self._time_since_last_shot += dt
        if self._invuln_timer > 0:
            self._invuln_timer -= dt
            if self._invuln_timer < 0:
                self._invuln_timer = 0.0

        self.rect.x += int(self.vel_x * dt)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        self.vel_y += self.GRAVITY * dt
        self.rect.y += int(self.vel_y * dt)
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0.0
            self.grounded = True
        else:
            self.grounded = False

        # Define o estado (usado tanto para legs/torso quanto para animação customizada)
        if not self.grounded:
            self.state = 'jump'
        else:
            if abs(self.vel_x) > 1:
                self.state = 'andando'
            else:
                self.state = 'parado'

        # Atualiza animação de legs/torso (se estiverem sendo usados)
        self._update_legs_anim(dt)
        self._update_torso_anim(dt)
        
        # --- Lógica de Animação Customizada (Andando/Parado) ---
        if self.animations:
            # 1. Sincroniza a animação atual com o estado
            if self.state == 'andando' and 'andando' in self.animations:
                self.set_animation('andando')
            elif self.state == 'parado' and 'parado' in self.animations:
                self.set_animation('parado')
            else:
                 # Se estiver pulando ou o estado não tiver animação customizada, 
                 # mantém o último estado válido, mas não avança.
                 pass

            # 2. Avança os frames da animação customizada (se ela tiver frames)
            if self.current_animation in self.animations and self.animations[self.current_animation]:
                frames = self.animations[self.current_animation]
                self.animation_timer += dt
                frame_dur = 1.0 / max(1.0, self.animation_fps)

                while self.animation_timer >= frame_dur:
                    self.animation_timer -= frame_dur
                    self.frame_index = (self.frame_index + 1) % len(frames)


    def _update_legs_anim(self, dt):
        # Corrigido: Para animação customizada ser priorizada, essa lógica só 
        # precisa rodar se não houver animação customizada OU se estiver usando 
        # o sistema legs/torso. Vamos manter a sua lógica original para este método,
        # mas lembre que ela usa 'walk' no seu código original, mas o 'state' 
        # acima foi corrigido para 'andando'.
        if self.state == 'andando' and self.legs_walk: # Usando 'andando'
            self.legs_timer += dt
            frame_dur = 1.0 / self.legs_fps
            while self.legs_timer >= frame_dur:
                self.legs_timer -= frame_dur
                self.legs_index = (self.legs_index + 1) % len(self.legs_walk)
        else:
            self.legs_index = 0
            self.legs_timer = 0.0

    # ... (_choose_torso_key e _update_torso_anim não precisam de alteração) ...

    # ... (can_shoot, shoot, take_damage, die, is_alive não precisam de alteração) ...

    def draw(self, surface):
        if self.dead:
            return

        drew_custom = False
        # --- PRIORIADE 1: Desenhar Animação Customizada (andar_N.png) ---
        if self.current_animation in self.animations and self.animations[self.current_animation]:
            frames = self.animations[self.current_animation]
            frame = frames[self.frame_index % len(frames)]
            frame_to_draw = frame
            if not self.facing_right:
                frame_to_draw = pygame.transform.flip(frame, True, False)
            
            # Desenha o frame customizado
            surface.blit(frame_to_draw, (self.rect.x, self.rect.y))
            drew_custom = True


        # --- PRIORIADE 2: Desenho do player (jump/full ou legs+torso) ---
        if not drew_custom:
            if self.state == 'jump' and self.full_jump:
                frame = self.full_jump[0]
                frame_to_draw = frame
                if not self.facing_right:
                    frame_to_draw = pygame.transform.flip(frame, True, False)
                surface.blit(frame_to_draw, (self.rect.x, self.rect.y))
            else:
                legs_frames = self.legs_walk if (self.state == 'andando' and self.legs_walk) else (self.legs_idle if self.legs_idle else []) # Corrigido para 'andando'
                if legs_frames:
                    leg_frame = legs_frames[self.legs_index % len(legs_frames)]
                    if not self.facing_right:
                        leg_frame = pygame.transform.flip(leg_frame, True, False)
                    surface.blit(leg_frame, (self.rect.x, self.rect.y))

                key = self._choose_torso_key()
                torso_frames = self.torso_anims.get(key) or self.torso_anims.get('neutral') or []
                if torso_frames:
                    torso_frame = torso_frames[self.torso_index % len(torso_frames)]
                    if not self.facing_right:
                        torso_frame = pygame.transform.flip(torso_frame, True, False)
                    surface.blit(torso_frame, (self.rect.x, self.rect.y))
                else:
                    if self.image:
                        frame = self.image
                        if not self.facing_right:
                            frame = pygame.transform.flip(frame, True, False)
                        surface.blit(frame, (self.rect.x, self.rect.y))
                    else:
                        pygame.draw.rect(surface, (200, 30, 30), self.rect)

        # --- barra de vida azul acima da cabeça ---
        # ... (lógica da barra de vida)
        bar_w = max(40, self.w)
        bar_h = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - (bar_h + 6)
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 30, 50), bg_rect)
        hp_ratio = max(0.0, min(1.0, float(self.health) / float(self.max_health)))
        fill_w = int(bar_w * hp_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
        if hasattr(self, "_invuln_timer") and self._invuln_timer > 0.0:
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                fill_color = (120, 180, 255)
            else:
                fill_color = (80, 130, 220)
        else:
            fill_color = (40, 140, 255)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, fill_rect)
        pygame.draw.rect(surface, (200, 200, 220), bg_rect, 1)

    def can_shoot(self) -> bool:
        """Verifica se o cooldown de tiro terminou."""
        return (not self.dead) and (self._time_since_last_shot >= self.fire_cooldown)

    def shoot(self, direction: Tuple[float, float], bullet_image=None) -> Optional["Bullet"]:
        """
        Cria e retorna uma Bullet com owner=self.
        Retorna None se não puder atirar.
        """
        # 1. Verifica se pode atirar (cooldown)
        if not self.can_shoot():
            return None
            
        self._time_since_last_shot = 0.0
        
        # 2. Define a posição de spawn do tiro
        # Note: Você precisará da classe Bullet definida no seu script.
        spawn_x = self.rect.centerx + self.gun_offset[0] - self.w // 2
        spawn_y = self.rect.centery + self.gun_offset[1] - self.h // 2
        
        # 3. Cria a bala (assumindo que a classe Bullet existe)
        b = Bullet(spawn_x, spawn_y, direction, image=bullet_image, owner=self)

        # 4. Toca o som de tiro (se houver)
        if self.shot_sound:
            try:
                self.shot_sound.play()
            except Exception:
                pass

        return b

    def try_jump(self):
        """
        Inicia o salto do jogador se ele estiver no chão.
        """
        if self.dead:
            return
            
        # Verifica se o jogador está no chão (grounded)
        if self.grounded:
            self.vel_y = self.JUMP_VELOCITY # Aplica velocidade de pulo (negativa, para cima)
            self.grounded = False # Não está mais no chão

    def take_damage(self, amount: int):
        # Verifica se está invulnerável ou já morreu
        if self._invuln_timer > 0.0 or self.dead:
            return False
            
        self.health -= amount
        self._invuln_timer = self.invuln_time # Reseta o timer de invulnerabilidade
        print(f"Player hit! HP: {self.health}/{self.max_health}")
        
        if self.health <= 0:
            self.die()
        return True
    def die(self):
        if self.dead:
            return
        self.dead = True
        print("Player morreu!")

    def is_alive(self) -> bool:
        """Retorna True se o jogador tem vida > 0 e não está morto."""
        return (self.health > 0) and (not self.dead)

# ---------------- Bullet e Boss (Sem Alterações) ----------------
# ... (O restante do código Bullet, BossLaser, Boss, e Game Loop continua inalterado)

# ---------------- Bullet (com owner) ----------------
class Bullet:
    SPEED = 900.0
    RADIUS = 6
    COLOR = (255, 220, 0)
    LIFETIME = 3.5

    def __init__(self, x, y, direction: Tuple[float, float], image: pygame.Surface = None, owner: Optional[object] = None):
        self.x = float(x)
        self.y = float(y)
        dx, dy = direction
        if dx == 0 and dy == 0:
            dx = 1.0
        length = math.hypot(dx, dy) or 1.0
        self.dir_x = dx / length
        self.dir_y = dy / length
        self.speed = Bullet.SPEED
        self.radius = Bullet.RADIUS
        self.color = Bullet.COLOR
        self.life = Bullet.LIFETIME
        self.alive = True
        self.image = image
        if self.image:
            diameter = max(6, self.radius * 2)
            self.image = pygame.transform.smoothscale(self.image, (diameter, diameter))
        self.owner = owner

    def update(self, dt, screen_w, screen_h):
        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False
        if self.x < -50 or self.x > screen_w + 50 or self.y < -50 or self.y > screen_h + 50:
            self.alive = False

    def draw(self, surface):
        if self.image:
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def collides_rect(self, rect) -> bool:
        closest_x = max(rect.left, min(int(self.x), rect.right))
        closest_y = max(rect.top, min(int(self.y), rect.bottom))
        dx = int(self.x) - closest_x
        dy = int(self.y) - closest_y
        return (dx*dx + dy*dy) <= (self.radius * self.radius)

# ---------------- BossLaser ----------------
class BossLaser:
    def __init__(self, boss_ref, offset_x, width, height, duration=1.0, damage_per_second=2.0):
        self.boss = boss_ref
        self.offset_x = offset_x
        self.w = width
        self.h = height
        self.duration = duration
        self._time = 0.0
        self.alive = True
        self.damage_per_second = damage_per_second
        self.surface = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.surface.fill((255, 80, 80, 160))

    def update(self, dt):
        self._time += dt
        if self._time >= self.duration:
            self.alive = False

    def current_rect(self):
        draw_y = int(self.boss.rect.y + getattr(self.boss, '_y_offset', 0))
        x = int(self.boss.rect.x + self.offset_x)
        y = draw_y + self.boss.h
        return pygame.Rect(x, y, self.w, self.h)

    def draw(self, surface):
        r = self.current_rect()
        surface.blit(self.surface, (r.x, r.y))

    def collides_rect(self, rect):
        return self.current_rect().colliderect(rect)

    def damage_amount_this_frame(self, dt):
        return self.damage_per_second * dt

# ---------------- Boss ----------------
class Boss:
    def __init__(self, x, y, screen_w, screen_h, image_path=None, scale_height_ratio=0.35,
                 bullet_image_path=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.image = None
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            target_h = int(screen_h * scale_height_ratio)
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
        self.health = self.max_health

        self.hand_offsets = [int(self.w * 0.22), int(self.w * 0.78) - 12]
        self.hand_bullet_cooldowns = [1.2, 1.2]
        self._time_since_last_bullet = [0.0 for _ in self.hand_offsets]
        self.hand_laser_cooldowns = [6.0, 6.0]
        self._time_since_last_laser = [0.0 for _ in self.hand_offsets]
        self.laser_width = 120
        self.laser_height = int(screen_h * 0.55)
        self.laser_duration = 1.2
        self.laser_damage_per_second = 3.0
        self.bullet_image = None
        if bullet_image_path and os.path.exists(bullet_image_path):
            self.bullet_image = pygame.image.load(bullet_image_path).convert_alpha()

        self.speech_sounds = []
        speech7 = os.path.join('assets', 'sounds', 'som7.mp3')
        speech8 = os.path.join('assets', 'sounds', 'som8.mp3')
        if os.path.exists(speech7):
            snd7 = pygame.mixer.Sound(speech7)
            snd7.set_volume(0.3)
            self.speech_sounds.append(snd7)
        if os.path.exists(speech8):
            snd8 = pygame.mixer.Sound(speech8)
            snd8.set_volume(0.3)
            self.speech_sounds.append(snd8)

        self.speech_interval_base = 4.0
        self._speech_timer = 0.0
        self._speech_index = 0

    def update(self, dt):
        self._time += dt

        if self.speech_sounds and self.health > 0:
            self._speech_timer += dt
            health_ratio = max(0.0, self.health / max(1, self.max_health))
            current_interval = 10
            if self._speech_timer >= current_interval:
                snd = self.speech_sounds[self._speech_index % len(self.speech_sounds)]
                try:
                    snd.play()
                except Exception:
                    pass
                self._speech_index += 1
                self._speech_timer = 0.0

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

    def try_shoot_hands_at_players(self, player_centers: List[Tuple[int, int]]):
        bullets = []
        if not player_centers:
            return bullets
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        for i, offset in enumerate(self.hand_offsets):
            if i >= len(self._time_since_last_bullet):
                continue
            if self._time_since_last_bullet[i] < self.hand_bullet_cooldowns[i]:
                continue
            spawn_x = int(self.rect.x + offset)
            spawn_y = draw_y + self.h - 10
            best = None
            best_dist = None
            for c in player_centers:
                dx = c[0] - spawn_x
                dy = c[1] - spawn_y
                d = dx*dx + dy*dy
                if best is None or d < best_dist:
                    best = (dx, dy)
                    best_dist = d
            if best is None:
                continue
            dx, dy = best
            length = math.hypot(dx, dy) or 1.0
            b = Bullet(spawn_x, spawn_y, (dx/length, dy/length), image=self.bullet_image, owner='boss')
            bullets.append(b)
            self._time_since_last_bullet[i] = 0.0
        return bullets

    def try_fire_lasers(self):
        lasers = []
        for i, offset in enumerate(self.hand_offsets):
            if i >= len(self._time_since_last_laser):
                continue
            if self._time_since_last_laser[i] < self.hand_laser_cooldowns[i]:
                continue
            laser = BossLaser(self, offset - (self.laser_width // 2) + 6,
                              self.laser_width, self.laser_height,
                              duration=self.laser_duration,
                              damage_per_second=self.laser_damage_per_second)
            lasers.append(laser)
            self._time_since_last_laser[i] = 0.0
        return lasers

    def draw(self, surface):
        draw_y = int(self.rect.y + getattr(self, '_y_offset', 0))
        if self.image:
            surface.blit(self.image, (self.rect.x, draw_y))
        pygame.draw.rect(surface, (80, 80, 80),
                         (self.rect.x, draw_y - 12, self.w, 8))
        hp_ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (200, 20, 20),
                         (self.rect.x, draw_y - 12, int(self.w * hp_ratio), 8))

# ------------------ suporte multi-mapeamento por joystick ------------------
AXIS_DEADZONE = 0.25

GAMEPAD_MAPS = [
    {
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "trigger_axis": 5,
    },
    {
        "move_axis_x": 0,
        "move_axis_y": 1,
        "aim_axis_x": 2,
        "aim_axis_y": 3,
        "dpad_hat": 0,
        "button_jump": 0,
        "trigger_axis": 5,
    }
]

joysticks: List[pygame.joystick.Joystick] = []
joystick_instance_ids: List[int] = []
joystick_to_player_index = {}

def get_map_for_joystick_physical_index(i: int) -> dict:
    if i is None:
        return GAMEPAD_MAPS[0]
    if i < len(GAMEPAD_MAPS):
        return GAMEPAD_MAPS[i]
    return GAMEPAD_MAPS[0]

def init_joysticks():
    global joysticks, joystick_instance_ids, joystick_to_player_index
    pygame.joystick.init()
    joysticks = []
    joystick_instance_ids = []
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        instance_id = j.get_instance_id() if hasattr(j, "get_instance_id") else i
        joysticks.append(j)
        joystick_instance_ids.append(instance_id)
        print(f"Joystick {i}: name='{j.get_name()}' instance_id={instance_id} axes={j.get_numaxes()} buttons={j.get_numbuttons()} hats={j.get_numhats()}")
    joystick_to_player_index = {i: i for i in range(len(joysticks))}
    return joysticks, joystick_instance_ids

def read_axis_with_deadzone(joy, axis_idx):
    if axis_idx is None or axis_idx < 0 or axis_idx >= joy.get_numaxes():
        return 0.0
    val = joy.get_axis(axis_idx)
    if abs(val) < AXIS_DEADZONE:
        return 0.0
    return val

def handle_joystick_event(event, players_list, bullets_list):
    print_event = False
    if event.type == pygame.JOYAXISMOTION:
        print_event = True
    elif event.type == pygame.JOYBUTTONDOWN:
        print_event = True
    elif event.type == pygame.JOYBUTTONUP:
        print_event = True
    elif event.type == pygame.JOYHATMOTION:
        print_event = True
    if print_event:
        print(event)

    jid = getattr(event, "instance_id", getattr(event, "joy", None))
    player_index = None
    joy_physical_index = None
    if jid is not None:
        try:
            joy_physical_index = joystick_instance_ids.index(jid)
            player_index = joystick_to_player_index.get(joy_physical_index, None)
        except ValueError:
            player_index = None
            joy_physical_index = None

    if event.type == pygame.JOYBUTTONDOWN and player_index is not None and player_index < len(players_list):
        btn = event.button
        player = players_list[player_index]
        pad_map = get_map_for_joystick_physical_index(joy_physical_index)

        if btn == pad_map.get("button_jump"):
            player.try_jump()
            return

        hat_idx = pad_map.get("dpad_hat", 0)
        joy = joysticks[joy_physical_index] if (joy_physical_index is not None and joy_physical_index < len(joysticks)) else None
        if joy is not None and hat_idx is not None and joy.get_numhats() > hat_idx:
            hat = joy.get_hat(hat_idx)
            if hat != (0, 0):
                hx, hy = hat
                player.aim = (hx, -hy)
                return

    if event.type == pygame.JOYHATMOTION and player_index is not None and player_index < len(players_list):
        hat_x, hat_y = event.value
        players_list[player_index].aim = (hat_x, -hat_y)

def poll_joysticks(players_list, bullets_list):
    for i, joy in enumerate(joysticks):
        player_idx = joystick_to_player_index.get(i, None)
        if player_idx is None or player_idx >= len(players_list):
            continue
        player = players_list[player_idx]
        pad_map = get_map_for_joystick_physical_index(i)

        move_ax = pad_map.get("move_axis_x", None)
        if move_ax is not None:
            ax = read_axis_with_deadzone(joy, move_ax)
            player.vel_x = ax * player.SPEED

        if player.vel_x > 0:
            player.facing_right = True
        elif player.vel_x < 0:
            player.facing_right = False

        aim_ax = pad_map.get("aim_axis_x", None)
        aim_ay = pad_map.get("aim_axis_y", None)
        if aim_ax is not None and aim_ay is not None and joy.get_numaxes() > max(aim_ax, aim_ay):
            raw_ax = joy.get_axis(aim_ax)
            raw_ay = joy.get_axis(aim_ay)
            dead_ax = raw_ax if abs(raw_ax) >= AXIS_DEADZONE else 0.0
            dead_ay = raw_ay if abs(raw_ay) >= AXIS_DEADZONE else 0.0
            if dead_ax != 0.0 or dead_ay != 0.0:
                length = math.hypot(dead_ax, dead_ay) or 1.0
                nx = dead_ax / length
                ny = dead_ay / length
                player.aim = (nx, ny)
        else:
            hat_idx = pad_map.get("dpad_hat", None)
            if hat_idx is not None and joy.get_numhats() > hat_idx:
                hat = joy.get_hat(hat_idx)
                if hat != (0, 0):
                    player.aim = (hat[0], -hat[1])

        trigger_ax = pad_map.get("trigger_axis", None)
        if trigger_ax is not None and trigger_ax < joy.get_numaxes():
            val = joy.get_axis(trigger_ax)
            if val > 0.5:
                dx, dy = player.aim
                if dx == 0 and dy == 0:
                    dx = 1.0 if player.facing_right else -1.0
                length = math.hypot(dx, dy) or 1.0
                b = player.shoot((dx/length, dy/length))
                if b:
                    bullets_list.append(b)

# ---------------- helper: mostrar imagens e abrir faroeste.py ----------------
def show_image_for(ms, img_path, screen, clock_ref, W, H):
    if not os.path.exists(img_path):
        return
    try:
        img = pygame.image.load(img_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (W, H))
    except Exception:
        return
        
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < ms:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock_ref.tick(60)

def show_images_and_launch_next(img1_path, img2_path, screen, clock_ref, W, H, next_script='faroestejogo.py'):
    # mostra primeira e segunda imagem (2s cada). ajustar ms se quiser.
    show_image_for(2000, img1_path, screen, clock_ref, W, H)
    show_image_for(2000, img2_path, screen, clock_ref, W, H)

    # fecha o pygame e inicia o outro script
    pygame.display.quit()
    pygame.quit()
    next_game = os.path.join(os.path.dirname(__file__), next_script)
    if os.path.exists(next_game):
        subprocess.Popen([sys.executable, next_game])
    sys.exit(0)

# ---------------- Main game loop ----------------
pygame.init()
pygame.mixer.init()

music_path = os.path.join('assets', 'sounds', 'som4.mp3')
if os.path.exists(music_path):
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
    except Exception:
        pass

joysticks, joystick_instance_ids = init_joysticks()

window = pygame.display.set_mode((1920, 1090))
pygame.display.set_caption('Duelo Boss - Gamepad multi (RT to fire)')
W, H = window.get_width(), window.get_height()

fundo_image = None
fundo_path = os.path.join('assets', 'img', 'fundo_boss.png')
if os.path.exists(fundo_path):
    try:
        fundo_image = pygame.image.load(fundo_path).convert()
        fundo_image = pygame.transform.smoothscale(fundo_image, (W, H))
    except Exception:
        fundo_image = None

ground_y = H

player1 = Player(W//4, ground_y, H,
                 image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                 anim_root=os.path.join('assets', 'img', 'player1'))

player2 = Player(3*W//4, ground_y, H,
                 image_path=os.path.join('assets', 'img', 'astronauta1.png'),
                 anim_root=os.path.join('assets', 'img', 'player2'))

boss = Boss(W//4, 80, W, H, image_path=os.path.join('assets', 'img', 'nave boss.png'),
            bullet_image_path=os.path.join('assets', 'img', 'bala.png'))

clock = pygame.time.Clock()
FPS = 60
font = pygame.font.Font(None, 24)
bullets, boss_bullets, boss_lasers = [], [], []
game = True

P1_LEFT = pygame.K_a; P1_RIGHT = pygame.K_d; P1_LOOK_UP = pygame.K_o; P1_JUMP = pygame.K_w
P1_AIMS = {pygame.K_i:(0,-1), pygame.K_k:(0,1), pygame.K_j:(-1,0), pygame.K_l:(1,0)}
P2_LEFT = pygame.K_LEFT; P2_RIGHT = pygame.K_RIGHT; P2_LOOK_UP = pygame.K_RCTRL; P2_JUMP = pygame.K_RSHIFT
P2_AIMS = {pygame.K_u:(0,-1), pygame.K_m:(0,1), pygame.K_h:(-1,0), pygame.K_k:(1,0)}

# caminhos das imagens de quadrinho (ajuste se necessário)
img1_path = os.path.join('assets', 'img', 'quadrinho1.png')
img2_path = os.path.join('assets', 'img', 'quadrinho2.png')

while game:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type in (pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYHATMOTION):
            handle_joystick_event(event, [player1, player2], bullets)

        if event.type == pygame.QUIT:
            game = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
            if event.key == P1_JUMP:
                player1.try_jump()
            if event.key == P2_JUMP:
                player2.try_jump()
            if event.key in P1_AIMS and player1.is_alive():
                dx, dy = P1_AIMS[event.key]
                b = player1.shoot((dx, dy))
                if b:
                    bullets.append(b)
                player1.aim = (dx, dy)
            if event.key in P2_AIMS and player2.is_alive():
                dx, dy = P2_AIMS[event.key]
                b = player2.shoot((dx, dy))
                if b:
                    bullets.append(b)
                player2.aim = (dx, dy)

    keys = pygame.key.get_pressed()
    player1.handle_input_keyboard(keys, P1_LEFT, P1_RIGHT, P1_LOOK_UP, P1_AIMS)
    player2.handle_input_keyboard(keys, P2_LEFT, P2_RIGHT, P2_LOOK_UP, P2_AIMS)

    poll_joysticks([player1, player2], bullets)

    player1.update(dt, W)
    player2.update(dt, W)
    boss.update(dt)

    boss_rect = pygame.Rect(boss.rect.x, boss.rect.y, boss.w, boss.h)
    for player in (player1, player2):
        if player.is_alive() and boss_rect.colliderect(player.rect):
            player.take_damage(1)

    alive_centers = []
    if player1.is_alive():
        alive_centers.append(player1.rect.center)
    if player2.is_alive():
        alive_centers.append(player2.rect.center)

    boss_bullets.extend(boss.try_shoot_hands_at_players(alive_centers))
    boss_lasers.extend(boss.try_fire_lasers())

    # update bullets (players' bullets)
    for b in bullets[:]:
        b.update(dt, W, H)
        boss_draw_y = int(boss.rect.y + getattr(boss, '_y_offset', 0))
        boss_rect_draw = pygame.Rect(boss.rect.x, boss_draw_y, boss.w, boss.h)
        if b.alive and b.collides_rect(boss_rect_draw):
            b.alive = False
            boss.health -= 1
            if boss.health <= 0:
                print("Boss derrotado!")
                # mostra as imagens e inicia faroeste.py
                show_images_and_launch_next(img1_path, img2_path, window, clock, W, H, next_script='faroestejogo.py')
        if not b.alive:
            try:
                bullets.remove(b)
            except ValueError:
                pass

    # update boss bullets -> players collision
    for bb in boss_bullets[:]:
        bb.update(dt, W, H)
        if bb.alive:
            if player1.is_alive() and bb.collides_rect(player1.rect):
                bb.alive = False
                player1.take_damage(1)
            elif player2.is_alive() and bb.collides_rect(player2.rect):
                bb.alive = False
                player2.take_damage(1)
        if not bb.alive:
            try:
                boss_bullets.remove(bb)
            except ValueError:
                pass

    # update lasers
    for laser in boss_lasers[:]:
        laser.update(dt)
        if laser.alive:
            if player1.is_alive() and laser.collides_rect(player1.rect):
                player1.take_damage(1)
            if player2.is_alive() and laser.collides_rect(player2.rect):
                player2.take_damage(1)
        if not laser.alive:
            try:
                boss_lasers.remove(laser)
            except ValueError:
                pass

    # draw
    if fundo_image:
        window.blit(fundo_image, (0, 0))
    else:
        window.fill((20, 20, 40))

    boss.draw(window)
    for laser in boss_lasers: laser.draw(window)
    for bb in boss_bullets: bb.draw(window)
    for b in bullets: b.draw(window)
    player1.draw(window)
    player2.draw(window)

    info = f"P1 HP: {player1.health}/{player1.max_health}   P2 HP: {player2.health}/{player2.max_health}   BossHP: {boss.health}"
    text_surf = font.render(info, True, (255, 255, 255))
    window.blit(text_surf, (10, 10))

    pygame.display.flip()

    if (not player1.is_alive()) and (not player2.is_alive()):
        big_font = pygame.font.Font(None, 96)
        text = big_font.render("Os dois jogadores morreram!", True, (220, 20, 20))
        tx = (W - text.get_width()) // 2
        ty = (H - text.get_height()) // 2
        window.blit(text, (tx, ty))
        pygame.display.flip()
        pygame.time.delay(1500)
        game = False

pygame.quit()