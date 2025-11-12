# faroeste.py
import os
import random
import sys
import pygame


def run_faroeste(screen, clock, W, H):
    """
    Fase final: duelo faroeste entre Jogador 1 e Jogador 2.
    Retorna:
        1 -> Jogador 1 venceu
        2 -> Jogador 2 venceu
        0 -> Empate
        None -> Cancelado (ESC)
    """

    fundo_path = os.path.join('assets', 'img', 'faroeste.png')
    fundo = None
    if os.path.exists(fundo_path):
        fundo = pygame.image.load(fundo_path).convert_alpha()
        fundo = pygame.transform.smoothscale(fundo, (W, H))

    # carregar sprites de tiro
    tiro_animacao = []
    for i in range(4):
        fp = os.path.join('assets', 'img', f'efeito{i}.png')
        if os.path.exists(fp):
            img = pygame.image.load(fp).convert_alpha()
            img = pygame.transform.scale(img, (32, 32))
            tiro_animacao.append(img)

    asset = {'tiro_animacao': tiro_animacao}

    # sons
    sound_path_music = os.path.join('assets', 'sounds', 'som1.mp3')
    sound_path_shot = os.path.join('assets', 'sounds', 'som2.mp3')

    if os.path.exists(sound_path_music):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(sound_path_music)
            pygame.mixer.music.set_volume(0.6)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    if os.path.exists(sound_path_shot):
        try:
            asset['som_tiro'] = pygame.mixer.Sound(sound_path_shot)
            asset['som_tiro'].set_volume(0.6)
        except Exception:
            asset['som_tiro'] = None
    else:
        asset['som_tiro'] = None

    # posições e constantes
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
    ROUND_END_PAUSE = 1.0

    # fontes
    font1_path = os.path.join('assets', 'font', 'escrita1.ttf')
    font2_path = os.path.join('assets', 'font', 'escrita2.ttf')
    font = pygame.font.Font(font1_path if os.path.exists(font1_path) else None, 56)
    font2 = pygame.font.Font(font2_path if os.path.exists(font2_path) else None, 70)
    small_font = pygame.font.Font(font1_path if os.path.exists(font1_path) else None, 36)

    score_p1 = 0
    score_p2 = 0
    round_number = 1
    game_over = False
    state = "preparar"
    state_time = pygame.time.get_ticks()
    waiting_target_time = None
    winner_this_round = None
    last_shot_time_p1 = -9999
    last_shot_time_p2 = -9999

    # joystick setup
    joysticks = []
    pygame.joystick.init()
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        j.init()
        joysticks.append(j)
    prev_buttons = [[0 for _ in range(j.get_numbuttons())] for j in joysticks]

    tiros_group = pygame.sprite.Group()

    class Tiro(pygame.sprite.Sprite):
        def __init__(self, center, assets, offset=(0, -15)):
            super().__init__()
            self.frames = assets.get('tiro_animacao', [])
            self.frame = 0
            self.image = self.frames[self.frame] if self.frames else pygame.Surface((32, 32))
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

    # funções internas -----------------------------

    def start_round():
        nonlocal state, state_time, waiting_target_time, winner_this_round
        winner_this_round = None
        state = "preparar"
        state_time = pygame.time.get_ticks()
        waiting_target_time = None

    def set_to_point_phase():
        nonlocal state, state_time, waiting_target_time
        state = "apontar"
        state_time = pygame.time.get_ticks()
        waiting_target_time = None

    def trigger_ja():
        nonlocal state, state_time
        state = "ja"
        state_time = pygame.time.get_ticks()

    def end_round(winner):
        nonlocal state, state_time, score_p1, score_p2, winner_this_round
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

    start_round()

    # loop principal --------------------------------
    while True:
        dt_ms = clock.tick(60)
        now = pygame.time.get_ticks()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(400)
                    return None

        # leitura de joystick (para disparo)
        for idx, j in enumerate(joysticks):
            for b in range(j.get_numbuttons()):
                val = j.get_button(b)
                if val and not prev_buttons[idx][b]:
                    player = 1 if idx == 0 else 2
                    if state == "ja" and winner_this_round is None and b == BUTTON_A:
                        if player == 1:
                            last_shot_time_p1 = now
                            tiros_group.add(Tiro(GUN_TIP_POS_P1, asset, offset=(+250, -60)))
                        else:
                            last_shot_time_p2 = now
                            tiros_group.add(Tiro(GUN_TIP_POS_P2, asset, offset=(+125, -40)))
                        if asset.get('som_tiro'):
                            asset['som_tiro'].play()
                        end_round(player)
                    elif state in ("preparar", "apontar") and winner_this_round is None and b == BUTTON_A:
                        end_round(2 if player == 1 else 1)
                prev_buttons[idx][b] = val

        # teclado (mesma lógica)
        keys = pygame.key.get_pressed()
        if not game_over:
            if state == "ja" and winner_this_round is None:
                if keys[KEY_P1]:
                    last_shot_time_p1 = now
                    tiros_group.add(Tiro(GUN_TIP_POS_P1, asset, offset=(+250, -60)))
                    if asset.get('som_tiro'):
                        asset['som_tiro'].play()
                    end_round(1)
                elif keys[KEY_P2]:
                    last_shot_time_p2 = now
                    tiros_group.add(Tiro(GUN_TIP_POS_P2, asset, offset=(+125, -40)))
                    if asset.get('som_tiro'):
                        asset['som_tiro'].play()
                    end_round(2)
            elif state in ("preparar", "apontar") and winner_this_round is None:
                if keys[KEY_P1]:
                    end_round(2)
                elif keys[KEY_P2]:
                    end_round(1)

        # controle de fases do duelo
        if not game_over:
            if state == "preparar" and now - state_time >= PREP_TIME * 1000:
                set_to_point_phase()
            elif state == "apontar" and now - state_time >= POINT_TIME * 1000:
                if waiting_target_time is None:
                    delay = random.uniform(MIN_RANDOM_DELAY, MAX_RANDOM_DELAY)
                    waiting_target_time = now + int(delay * 1000)
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

        # renderização --------------------------------
        if fundo:
            screen.blit(fundo, (0, 0))
        else:
            screen.fill((0, 0, 0))

        title = font2.render('DUELO', True, (255, 255, 255))
        screen.blit(title, (W // 2 - title.get_width() // 2, 20))

        if game_over:
            msg = "EMPATE!"
            if score_p1 > score_p2:
                msg = "JOGADOR 1 VENCEU O JOGO!"
            elif score_p2 > score_p1:
                msg = "JOGADOR 2 VENCEU O JOGO!"
            text = font.render(msg, True, (255, 0, 0))
            screen.blit(text, (W // 2 - text.get_width() // 2, H // 2 - 50))
            hint = small_font.render("PRESSIONE ESC PARA SAIR", True, (200, 200, 200))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 30))
        else:
            if state == "preparar":
                s = font.render("PREPARAR...", True, (255, 255, 255))
                screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 - 80))
            elif state == "apontar":
                s = font.render("APONTAR...", True, (255, 255, 255))
                screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 - 80))
            elif state == "ja":
                s = font.render("JA!", True, (10, 255, 10))
                screen.blit(s, (W // 2 - s.get_width() // 2, H // 2 - 80))
            elif state == "resultado":
                round_msg = (
                    "EMPATE!"
                    if winner_this_round == 0
                    else ("JOGADOR 1 VENCEU A RODADA!" if winner_this_round == 1 else "JOGADOR 2 VENCEU A RODADA!")
                )
                tr = font.render(round_msg, True, (255, 255, 255))
                screen.blit(tr, (W // 2 - tr.get_width() // 2, H // 2 - 100))
                score_msg = f"{score_p1}  x  {score_p2}"
                ts = font2.render(score_msg, True, (0, 255, 0))
                screen.blit(ts, (W // 2 - ts.get_width() // 2, H // 2))

        # efeitos de tiro
        if now - last_shot_time_p1 <= FLASH_DURATION_MS:
            age = (now - last_shot_time_p1) / FLASH_DURATION_MS
            rad = int(20 * (1 - age) + 6)
            pygame.draw.circle(screen, (255, 220, 80), (520, 750), rad)
        if now - last_shot_time_p2 <= FLASH_DURATION_MS:
            age = (now - last_shot_time_p2) / FLASH_DURATION_MS
            rad = int(20 * (1 - age) + 6)
            pygame.draw.circle(screen, (255, 220, 80), (1375, 775), rad)

        tiros_group.update()
        tiros_group.draw(screen)

        pygame.display.flip()

        # fim do jogo
        if game_over:
            pygame.mixer.music.fadeout(600)
            if score_p1 > score_p2:
                return 1
            elif score_p2 > score_p1:
                return 2
            else:
                return 0
