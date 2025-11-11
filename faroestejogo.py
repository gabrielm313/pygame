import pygame
import os
import random

pygame.init()
pygame.joystick.init()

# ----- Tela -----
window = pygame.display.set_mode((1920, 1090))
pygame.display.set_caption('Duelo Faroeste - Melhor de 5')

# ----- Assets -----
# após criar a janela (já tem W,H definidos)
fundo = pygame.image.load(os.path.join('assets', 'img', 'faroeste.png')).convert_alpha()
W, H = window.get_width(), window.get_height()
fundo = pygame.transform.smoothscale(fundo, (W, H))
clock = pygame.time.Clock()
FPS = 60

asset = {}
tiro_animacao = []
for i in range(4):
    img = pygame.image.load(os.path.join('assets', 'img', f'efeito{i}.png')).convert_alpha()
    img = pygame.transform.scale(img, (32, 32))
    tiro_animacao.append(img)
asset['tiro_animacao'] = tiro_animacao

tiros_group = pygame.sprite.Group()

pygame.mixer.music.load(os.path.join('assets', 'sounds', 'som1.mp3'))
pygame.mixer.music.set_volume(1)
asset['som_tiro'] = pygame.mixer.Sound(os.path.join('assets', 'sounds', 'som2.mp3'))
asset['som_tiro'].set_volume(0.6)

# ----- Configurações -----
GUN_TIP_POS_P1 = (420, 700)
GUN_TIP_POS_P2 = (1100, 700)
KEY_P1 = pygame.K_a
KEY_P2 = pygame.K_l
BUTTON_A = 0
BEST_OF = 5
PREP_TIME = 1.0
POINT_TIME = 1.0
MIN_RANDOM_DELAY = 1.0
MAX_RANDOM_DELAY = 3.0
FLASH_DURATION_MS = 140
RECOIL_DURATION_MS = 140
ROUND_END_PAUSE = 1.0

font = pygame.font.Font(os.path.join('assets', 'font', 'escrita1.ttf'), 56)
font2 = pygame.font.Font(os.path.join('assets', 'font', 'escrita2.ttf'), 70)
small_font = pygame.font.Font(os.path.join('assets', 'font', 'escrita1.ttf'), 36)
small_font2 = pygame.font.Font(os.path.join('assets', 'font', 'escrita2.ttf'), 30)

# ----- Estado do jogo -----
score_p1 = 0
score_p2 = 0
round_number = 1
game_over = False
state = "idle"
state_time = 0.0
waiting_target_time = 0.0
winner_this_round = None
last_shot_time_p1 = -9999
last_shot_time_p2 = -9999

# ----- Joysticks -----
joysticks = []
for i in range(pygame.joystick.get_count()):
    j = pygame.joystick.Joystick(i)
    j.init()
    joysticks.append(j)

print(f"{len(joysticks)} controle(s) detectado(s).")
for j in joysticks:
    print(f"- {j.get_name()} com {j.get_numbuttons()} botões.")

def start_round():
    global state, state_time, waiting_target_time, winner_this_round
    winner_this_round = None
    state = "preparar"
    state_time = pygame.time.get_ticks()
    waiting_target_time = None

def set_to_point_phase():
    global state, state_time, waiting_target_time
    state = "apontar"
    state_time = pygame.time.get_ticks()
    delay = random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
    waiting_target_time = pygame.time.get_ticks() + int(delay * 1000)

def trigger_ja():
    global state, state_time
    state = "ja"
    state_time = pygame.time.get_ticks()

def end_round(winner):
    global state, state_time, score_p1, score_p2, winner_this_round
    winner_this_round = winner
    state = "resultado"
    state_time = pygame.time.get_ticks()
    if winner == 1:
        score_p1 += 1
    elif winner == 2:
        score_p2 += 1

def check_match_over():
    alvo = (BEST_OF // 2) + 1
    return score_p1 >= alvo or score_p2 >= alvo

class Tiro(pygame.sprite.Sprite):
    def __init__(self, center, assets, offset=(0, -15)):
        pygame.sprite.Sprite.__init__(self)
        self.frames = assets['tiro_animacao']
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect()
        self.rect.centerx = center[0] + offset[0]
        self.rect.centery = center[1] + offset[1]
        self.last_update = pygame.time.get_ticks()
        self.frame_ticks = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_ticks:
            self.last_update = now
            self.frame += 1
            if self.frame >= len(self.frames):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.frames[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

def shoot(player, now):
    global last_shot_time_p1, last_shot_time_p2
    if player == 1:
        last_shot_time_p1 = now
        tiros_group.add(Tiro(GUN_TIP_POS_P1, asset, offset=(+250, -60)))
    else:
        last_shot_time_p2 = now
        tiros_group.add(Tiro(GUN_TIP_POS_P2, asset, offset=(+125, -40)))
    asset['som_tiro'].play()
    end_round(player)

# Inicia primeira rodada
start_round()
pygame.mixer.music.play(-1)

# Controle de estado dos botões (polling)
prev_buttons = [[0 for _ in range(j.get_numbuttons())] for j in joysticks]

# ----- Loop principal -----
game = True
while game:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    # ---- Eventos de saída ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game = False

    # ---- Polling dos controles ----
    for idx, j in enumerate(joysticks):
        for b in range(j.get_numbuttons()):
            val = j.get_button(b)
            if val and not prev_buttons[idx][b]:
                print(f"Controle {idx} -> botão {b} pressionado.")
                player = 1 if idx == 0 else 2
                if state == "ja" and winner_this_round is None and b == BUTTON_A:
                    shoot(player, now)
                elif state in ("preparar", "apontar") and winner_this_round is None and b == BUTTON_A:
                    end_round(2 if player == 1 else 1)
            prev_buttons[idx][b] = val

    # ---- Teclado ----
    keys = pygame.key.get_pressed()
    if not game_over:
        if state == "ja" and winner_this_round is None:
            if keys[KEY_P1]:
                shoot(1, now)
            elif keys[KEY_P2]:
                shoot(2, now)
        elif state in ("preparar", "apontar") and winner_this_round is None:
            if keys[KEY_P1]:
                end_round(2)
            elif keys[KEY_P2]:
                end_round(1)

    # ---- Lógica de estado ----
    if not game_over:
        if state == "preparar" and now - state_time >= PREP_TIME * 1000:
            set_to_point_phase()
        elif state == "apontar" and now - state_time >= POINT_TIME * 1000:
            if waiting_target_time is None:
                waiting_target_time = now + random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY) * 1000
            elif now >= waiting_target_time:
                trigger_ja()
        elif state == "ja" and now - state_time >= 3000 and winner_this_round is None:
            winner_this_round = 0
            state = "resultado"
            state_time = now
        elif state == "resultado" and now - state_time >= ROUND_END_PAUSE * 1000:
            if check_match_over() or round_number > BEST_OF:
                game_over = True
            else:
                round_number += 1
                start_round()

    # ---- Renderização ----
    window.blit(fundo, (0, 0))
    title = font2.render('DUELO', True, (255, 255, 255))
    window.blit(title, (W//2 - title.get_width()//2, 20))
    pygame.draw.circle(window, (255,255,255), (520,750), 6)
    pygame.draw.circle(window, (200,0,0), (1375, 775), 6)
    # ----- Exibição de mensagens de rodada -----
    if game_over:
        # Tela final
        msg = "EMPATE!"
        if score_p1 > score_p2:
            msg = "JOGADOR 1 VENCEU O JOGO!"
        elif score_p2 > score_p1:
            msg = "JOGADOR 2 VENCEU O JOGO!"

        text = font.render(msg, True, (255, 0, 0))
        window.blit(text, (W//2 - text.get_width()//2, H//2 - 50))
        hint = small_font.render("PRESSIONE ESC PARA SAIR", True, (200, 200, 200))
        window.blit(hint, (W//2 - hint.get_width()//2, H//2 + 30))

    else:
        # Mostra instruções conforme o estado da rodada
        if state == "preparar":
            text = font.render("PREPARAR...", True, (255, 255, 255))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))

        elif state == "apontar":
            text = font.render("APONTAR...", True, (255, 255, 255))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))

        elif state == "ja":
            text = font.render("JA!", True, (10, 255, 10))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))

        elif state == "resultado":
            # Mostra o vencedor da rodada + placar
            if winner_this_round == 1:
                round_msg = "JOGADOR 1 VENCEU A RODADA!"
            elif winner_this_round == 2:
                round_msg = "JOGADOR 2 VENCEU A RODADA!"
            else:
                round_msg = "EMPATE!"

            text_round = font.render(round_msg, True, (255, 255, 255))
            window.blit(text_round, (W//2 - text_round.get_width()//2, H//2 - 100))

            score_msg = f"{score_p1}  x  {score_p2}"
            text_score = font2.render(score_msg, True, (0, 255, 0))
            window.blit(text_score, (W//2 - text_score.get_width()//2, H//2))

    # ---- Efeito de clarão e recuo do tiro ----
    # jogador 1
    if now - last_shot_time_p1 <= FLASH_DURATION_MS:
        age = (now - last_shot_time_p1) / FLASH_DURATION_MS
        rad = int(20 * (1 - age) + 6)
        # clarão amarelo
        pygame.draw.circle(window, (255, 220, 80), (520, 750), rad)
        # recuo da arma (linhazinha curta para trás)
        if now - last_shot_time_p1 <= RECOIL_DURATION_MS:
            recoil_offset = int(10 * (1 - (now - last_shot_time_p1) / RECOIL_DURATION_MS))
            pygame.draw.line(window, (255, 255, 255),
                             (520, 750),
                             (520 - recoil_offset, 750), 4)

    # jogador 2
    if now - last_shot_time_p2 <= FLASH_DURATION_MS:
        age = (now - last_shot_time_p2) / FLASH_DURATION_MS
        rad = int(20 * (1 - age) + 6)
        pygame.draw.circle(window, (255, 220, 80), (1375, 775), rad)
        if now - last_shot_time_p2 <= RECOIL_DURATION_MS:
            recoil_offset = int(10 * (1 - (now - last_shot_time_p2) / RECOIL_DURATION_MS))
            pygame.draw.line(window, (255, 255, 255),
                             (1375, 775),
                             (1375 + recoil_offset, 775), 4)

    tiros_group.update()
    tiros_group.draw(window)

    pygame.display.flip()

pygame.quit()
