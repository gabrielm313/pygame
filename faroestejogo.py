import pygame
import os
import random
import time

pygame.init()
window = pygame.display.set_mode((1536, 1090))
pygame.display.set_caption('Duelo Faroeste - Melhor de 3')

# ----- Assets -----
fundo = os.path.join('assets', 'img', 'faroeste.png')
fundo_image = pygame.image.load(fundo).convert()
W, H = window.get_width(), window.get_height()
clock = pygame.time.Clock()
FPS = 60

# ----- Configuráveis -----
# Coordenadas da ponta do cano: ajuste conforme o seu fundo (x, y)
GUN_TIP_POS_P1 = (420, 700)   # jogador da esquerda
GUN_TIP_POS_P2 = (1100, 700)  # jogador da direita

# teclas de tiro (mude se quiser)
KEY_P1 = pygame.K_a  # jogador 1 aperta 'F'
KEY_P2 = pygame.K_l   # jogador 2 aperta 'J'

BEST_OF = 3  # melhor de 3

# tempos (em segundos / ms)
PREP_TIME = 1.0
POINT_TIME = 1.0
MIN_RANDOM_DELAY = 1.0
MAX_RANDOM_DELAY = 3.0
FLASH_DURATION_MS = 140
RECOIL_DURATION_MS = 140
ROUND_END_PAUSE = 1.0

font = pygame.font.SysFont(None, 56)
small_font = pygame.font.SysFont(None, 36)

# estado do jogo
score_p1 = 0
score_p2 = 0
round_number = 1
game_over = False

# estado da rodada
state = "idle"  # "idle", "preparar", "esperando", "ja", "resultado"
state_time = 0.0
waiting_target_time = 0.0
winner_this_round = None

# efeitos de tiro (tempo em ms)
last_shot_time_p1 = -9999
last_shot_time_p2 = -9999

def start_round():
    global state, state_time, waiting_target_time, winner_this_round
    winner_this_round = None
    state = "preparar"
    state_time = pygame.time.get_ticks()
    # sequência: PREP -> POINT -> espera aleatória -> JA
    # calculamos quando o "ja" vai ocorrer (só usado em fluxo)
    waiting_target_time = None

def set_to_point_phase():
    global state, state_time, waiting_target_time
    state = "apontar"
    state_time = pygame.time.get_ticks()
    # escolhe o momento aleatório para o "JÁ"
    delay = random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
    waiting_target_time = pygame.time.get_ticks() + int(delay * 1000)

def trigger_ja():
    global state, state_time
    state = "ja"
    state_time = pygame.time.get_ticks()

def end_round(winner):
    global state, state_time, score_p1, score_p2, round_number, winner_this_round
    winner_this_round = winner
    state = "resultado"
    state_time = pygame.time.get_ticks()
    if winner == 1:
        score_p1 += 1
    elif winner == 2:
        score_p2 += 1
    round_number += 1

def check_match_over():
    # vence quem primeiro chegar a ceil(BEST_OF/2)
    target = (BEST_OF // 2) + 1
    if score_p1 >= target or score_p2 >= target:
        return True
    return False

# inicia a primeira rodada
start_round()

game = True
while game:
    dt_ms = clock.tick(FPS)
    now_ms = pygame.time.get_ticks()

    # ---------- eventos ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game = False
                
        # detectar tecla de tiro apenas quando o estado permite (após "ja")
        if event.type == pygame.KEYDOWN and not game_over:
            if state == "ja":
                if event.key == KEY_P1 and winner_this_round is None:
                    # jogador 1 atirou primeiro
                    last_shot_time_p1 = now_ms
                    end_round(1)
                elif event.key == KEY_P2 and winner_this_round is None:
                    last_shot_time_p2 = now_ms
                    end_round(2)
            # se alguém apertar antes do "ja", penalidade opcional:
            elif state in ("preparar", "apontar") and winner_this_round is None:
                # apertou cedo -> perde a rodada automaticamente
                if event.key == KEY_P1:
                    end_round(2)
                elif event.key == KEY_P2:
                    end_round(1)

    # ---------- lógica de estado ----------
    if not game_over:
        if state == "preparar":
            # depois do PREP_TIME, vai para "apontar"
            if now_ms - state_time >= int(PREP_TIME * 1000):
                set_to_point_phase()
        elif state == "apontar":
            # mostra "apontar" apenas POINT_TIME, depois espera aleatória
            if now_ms - state_time >= int(POINT_TIME * 1000):
                # aguarda o momento aleatório para "ja"
                if waiting_target_time is None:
                    # safety (não deveria acontecer)
                    waiting_target_time = now_ms + int(random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)*1000)
                elif now_ms >= waiting_target_time:
                    trigger_ja()
        elif state == "ja":
            # aguarda resultado; se ninguém apertar por 3s consideramos empate e reiniciamos
            if now_ms - state_time >= 3000 and winner_this_round is None:
                # empate -> sem pontuação, apenas termina a rodada
                winner_this_round = 0
                state = "resultado"
                state_time = now_ms
        elif state == "resultado":
            # espera um tempinho e inicia próxima rodada ou finaliza partida
            if (now_ms - state_time) >= int(ROUND_END_PAUSE * 1000):
                if check_match_over() or round_number > BEST_OF:
                    game_over = True
                else:
                    start_round()

    # ---------- render ----------
    window.fill((0,0,0))
    window.blit(fundo_image, (0,0))

    # HUD básico
    title = font.render('Duelo - Melhor de {}'.format(BEST_OF), True, (240,240,240))
    window.blit(title, (W//2 - title.get_width()//2, 20))
    score_text = small_font.render(f'P1: {score_p1}   P2: {score_p2}   Rodada: {round_number}/{BEST_OF}', True, (255,255,255))
    window.blit(score_text, (20, 20 + title.get_height()))

    # desenha as pontas da arma (debug - só para ajuste)
    pygame.draw.circle(window, (0,200,0), (int(GUN_TIP_POS_P1[0]), int(GUN_TIP_POS_P1[1])), 6)
    pygame.draw.circle(window, (200,0,0), (int(GUN_TIP_POS_P2[0]), int(GUN_TIP_POS_P2[1])), 6)

    # desenha texto de estado no centro
    if game_over:
        # mostra vencedor da partida
        if score_p1 > score_p2:
            msg = "Jogador 1 venceu a partida!"
        elif score_p2 > score_p1:
            msg = "Jogador 2 venceu a partida!"
        else:
            msg = "Empate!"
        big = font.render(msg, True, (255, 220, 120))
        window.blit(big, (W//2 - big.get_width()//2, H//2 - 50))
        hint = small_font.render("Pressione ESC para sair", True, (200,200,200))
        window.blit(hint, (W//2 - hint.get_width()//2, H//2 + 30))
    else:
        if state == "preparar":
            t_left = max(0, PREP_TIME - (now_ms - state_time)/1000.0)
            text = font.render("Preparar...", True, (255,255,255))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))
        elif state == "apontar":
            text = font.render("Apontar...", True, (255,255,255))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))
        elif state == "ja":
            text = font.render("JÁ!", True, (255,30,30))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))
        elif state == "resultado":
            if winner_this_round == 1:
                t = "Jogador 1 venceu a rodada!"
            elif winner_this_round == 2:
                t = "Jogador 2 venceu a rodada!"
            else:
                t = "Empate!"
            text = font.render(t, True, (255,255,180))
            window.blit(text, (W//2 - text.get_width()//2, H//2 - 80))

    # efeitos de tiro: flash + recuo
    # jogador 1
    if now_ms - last_shot_time_p1 <= FLASH_DURATION_MS:
        age = (now_ms - last_shot_time_p1) / FLASH_DURATION_MS
        rad = int(20 * (1 - age) + 6)
        # flash
        pygame.draw.circle(window, (255, 220, 80), (int(GUN_TIP_POS_P1[0]), int(GUN_TIP_POS_P1[1])), rad)
        # recuo - um pequeno círculo deslocado para trás
        if now_ms - last_shot_time_p1 <= RECOIL_DURATION_MS:
            recoil_offset = int(10 * (1 - (now_ms - last_shot_time_p1) / RECOIL_DURATION_MS))
            pygame.draw.line(window, (255,255,255),
                             (GUN_TIP_POS_P1[0], GUN_TIP_POS_P1[1]),
                             (GUN_TIP_POS_P1[0] - recoil_offset, GUN_TIP_POS_P1[1]), 4)
    # jogador 2
    if now_ms - last_shot_time_p2 <= FLASH_DURATION_MS:
        age = (now_ms - last_shot_time_p2) / FLASH_DURATION_MS
        rad = int(20 * (1 - age) + 6)
        pygame.draw.circle(window, (255, 220, 80), (int(GUN_TIP_POS_P2[0]), int(GUN_TIP_POS_P2[1])), rad)
        if now_ms - last_shot_time_p2 <= RECOIL_DURATION_MS:
            recoil_offset = int(10 * (1 - (now_ms - last_shot_time_p2) / RECOIL_DURATION_MS))
            pygame.draw.line(window, (255,255,255),
                             (GUN_TIP_POS_P2[0], GUN_TIP_POS_P2[1]),
                             (GUN_TIP_POS_P2[0] + recoil_offset, GUN_TIP_POS_P2[1]), 4)

    pygame.display.flip()

pygame.quit()
