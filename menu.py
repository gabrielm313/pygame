# menu.py
import os
import sys
import pygame

from utils import load_and_scale, show_quadrinhos_sequence
from config import (
    JOYSTICK_SKIP_BUTTON_A,
    JOYSTICK_TUTORIAL_BUTTON_B,
    JOYSTICK_RANKING_BUTTON_Y,
    TUTORIAL_PATHS,
)
from ranking import show_ranking_screen


def menu(screen, clock, W, H):
    """
    Tela de menu principal.

    O que faz:
        - Exibe o background do menu e toca música de entrada (se disponível).
        - Mostra três botões interativos: JOGAR, TUTORIAL e RANKING.
        - Aceita entrada de teclado, mouse e joystick para navegar/acionar as opções.
        - Permite iniciar o jogo, abrir o tutorial (sequência de quadrinhos) ou ver o ranking.
        - Faz fadeout da música ao sair.

    Recebe:
        - screen: pygame.Surface onde tudo será desenhado.
        - clock: pygame.time.Clock para controlar FPS.
        - W: largura da tela (int).
        - H: altura da tela (int).

    Retorna:
        - True  -> jogador escolheu iniciar o jogo.
        - False -> jogador escolheu sair (ou não iniciou o jogo e fechou a janela).
    """
    pygame.mouse.set_visible(True)

    MENU_BG_PATH = os.path.join('assets', 'img', 'inicio.png')
    MENU_MUSIC_PATH = os.path.join('assets', 'sounds', 'som9.mp3')

    title_font = pygame.font.Font(None, 96)
    btn_font = pygame.font.Font(None, 52)

    btn_w, btn_h = 420, 86
    btn_play = pygame.Rect((W // 2 - btn_w // 2, int(H * 0.5 - btn_h - 10), btn_w, btn_h))
    btn_tutorial = pygame.Rect((W // 2 - btn_w // 2, int(H * 0.5 + 10), btn_w, btn_h))
    btn_ranking = pygame.Rect((W // 2 - btn_w // 2, int(H * 0.5 + 110), btn_w, btn_h))

    # start menu music (tenta tocar em loop; falhas são ignoradas para não crashar)
    if os.path.exists(MENU_MUSIC_PATH):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(400)
            pygame.mixer.music.load(MENU_MUSIC_PATH)
            pygame.mixer.music.set_volume(0.25)
            pygame.mixer.music.play(-1)
        except Exception:
            # ignora falhas no mixer para evitar crash
            pass

    # tenta carregar e escalar background; load_and_scale vem de utils
    bg = load_and_scale(MENU_BG_PATH, W, H, keep_aspect=False)

    running = True
    start_game = False

    while running:
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                # fechar a janela encerra o jogo
                pygame.quit()
                sys.exit(0)

            if ev.type == pygame.KEYDOWN:
                # ENTER / SPACE -> iniciar jogo
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    start_game = True
                    running = False
                # tecla 't' -> mostrar tutorial (sequência de quadrinhos)
                if ev.key == pygame.K_t:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                # tecla 'r' -> mostrar ranking
                if ev.key == pygame.K_r:
                    show_ranking_screen(screen, clock, W, H)
                # ESC -> sair do jogo
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # clique com botão esquerdo do mouse: verificar colisão com botões
                if btn_play.collidepoint(ev.pos):
                    start_game = True
                    running = False
                elif btn_tutorial.collidepoint(ev.pos):
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                elif btn_ranking.collidepoint(ev.pos):
                    show_ranking_screen(screen, clock, W, H)

            if ev.type == pygame.JOYBUTTONDOWN:
                # entrada via joystick (mapeamentos vindos de config):
                # botão A -> jogar
                if ev.button == JOYSTICK_SKIP_BUTTON_A:
                    start_game = True
                    running = False
                # botão B -> tutorial
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
                # botão Y -> ranking
                if ev.button == JOYSTICK_RANKING_BUTTON_Y:
                    show_ranking_screen(screen, clock, W, H)

        # desenho do background (se carregado usa imagem; senão preenche cor sólida)
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((18, 18, 40))

        def draw_button(surface, rect, text, font, hovered=False):
            """
            Desenha um botão estilizado.

            O que faz:
                - Renderiza um retângulo com background, borda e texto centralizado.
                - Usa cores diferentes se estiver hovered (com o mouse).

            Recebe:
                - surface: pygame.Surface onde desenhar.
                - rect: pygame.Rect definindo posição e tamanho.
                - text: string do rótulo.
                - font: pygame.font.Font para renderizar texto.
                - hovered: bool indicando se o botão está em estado "hover".

            Retorna:
                - None (efeito colateral: desenha no surface).
            """
            BUTTON_BG = (120, 40, 40)
            BUTTON_HOVER_BG = (70, 70, 120)
            BUTTON_BORDER = (255, 255, 255)
            BUTTON_TEXT = (245, 245, 245)
            bgc = BUTTON_HOVER_BG if hovered else BUTTON_BG
            pygame.draw.rect(surface, bgc, rect, border_radius=12)
            pygame.draw.rect(surface, BUTTON_BORDER, rect, 2, border_radius=12)
            txt = font.render(text, True, BUTTON_TEXT)
            tx = rect.x + (rect.w - txt.get_width()) // 2
            ty = rect.y + (rect.h - txt.get_height()) // 2
            surface.blit(txt, (tx, ty))

        # desenha os botões com detecção de hover usando a posição atual do mouse
        draw_button(screen, btn_play, "JOGAR", btn_font, hovered=btn_play.collidepoint(mx, my))
        draw_button(screen, btn_tutorial, "TUTORIAL", btn_font, hovered=btn_tutorial.collidepoint(mx, my))
        draw_button(screen, btn_ranking, "RANKING", btn_font, hovered=btn_ranking.collidepoint(mx, my))

        pygame.display.flip()
        clock.tick(60)

    # fade out music ao sair do menu (trato de exceção caso o mixer não esteja disponível)
    try:
        pygame.mixer.music.fadeout(500)
    except Exception:
        pass

    return start_game
