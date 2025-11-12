# utils.py
import os
import sys
import math
import pygame

from config import (
    QUADRINHO_DURATION_MS,
    TUTORIAL_PATHS,
    JOYSTICK_SKIP_BUTTON_A,
    JOYSTICK_TUTORIAL_BUTTON_B,
    MOUSE_LEFT,
)


def load_and_scale(img_path, W, H, keep_aspect=True):
    """
    Carrega uma imagem (se existir) e escala para caber em W x H.
    Se keep_aspect for True, a imagem mantém a proporção.
    Retorna None se o arquivo não existir.
    """
    if not os.path.exists(img_path):
        return None
    img = pygame.image.load(img_path).convert_alpha()
    if keep_aspect:
        iw, ih = img.get_size()
        scale = min(W / iw, H / ih)
        return pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
    return pygame.transform.smoothscale(img, (W, H))


def show_quadrinhos_sequence(screen, clock, W, H, image_paths, duration_ms=QUADRINHO_DURATION_MS):
    """
    Mostra sequência de 'quadrinhos' (telas / imagens) um a um.
    Pode-se pular com teclado, mouse ou joystick A; durante exibição,
    pressionar B (ou o botão configurado) abre o tutorial (TUTORIAL_PATHS).
    Retorna True se a sequência terminou normalmente, False se ESC foi pressionado.
    """
    imgs = [load_and_scale(p, W, H, keep_aspect=False) for p in image_paths]
    idx = 0
    num = len(imgs)
    while idx < num:
        img = imgs[idx]
        start = pygame.time.get_ticks()
        exited_early = False
        while pygame.time.get_ticks() - start < duration_ms:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return False
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        exited_early = True
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == MOUSE_LEFT:
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_SKIP_BUTTON_A:
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    # abrir tutorial sobrepor enquanto
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
            # desenha (imagem ou fallback)
            if img:
                screen.blit(img, (0, 0))
            else:
                screen.fill((0, 0, 0))
                f = pygame.font.Font(None, 36)
                txt = f.render(f"Imagem ausente: {image_paths[idx]}", True, (255, 255, 255))
                screen.blit(txt, ((W - txt.get_width()) // 2, H // 2))
            pygame.display.flip()
            clock.tick(60)
            if exited_early:
                break
        idx += 1
    return True


def get_player_names(screen, clock, W, H):
    """
    Tela simples para digitar nomes de 2 jogadores.
    Retorna (name1, name2) ou None se cancelar (ESC).
    - Enter/KP_ENTER confirma campo (vai para próximo).
    - BACKSPACE apaga.
    - Click nas caixas muda o campo ativo.
    - Joystick: A (JOYSTICK_SKIP_BUTTON_A) avança/confirmar, B (JOYSTICK_TUTORIAL_BUTTON_B) troca campo.
    """
    font = pygame.font.Font(None, 40)
    title_font = pygame.font.Font(None, 64)
    input_boxes = ["", ""]
    active = 0
    max_len = 20
    prompt1 = "Nome do Jogador 1:"
    prompt2 = "Nome do Jogador 2:"
    info = "Enter para confirmar cada nome. ESC para cancelar."
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key == pygame.K_BACKSPACE:
                    if len(input_boxes[active]) > 0:
                        input_boxes[active] = input_boxes[active][:-1]
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if active == 0:
                        active = 1
                    else:
                        if input_boxes[1].strip() == "":
                            # não aceita segundo nome vazio
                            pass
                        else:
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                else:
                    ch = ev.unicode
                    if ch and len(input_boxes[active]) < max_len and ord(ch) >= 32:
                        input_boxes[active] += ch
            if ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                box1 = pygame.Rect(W // 2 - 280, H // 2 - 20, 560, 48)
                box2 = pygame.Rect(W // 2 - 280, H // 2 + 60, 560, 48)
                if box1.collidepoint(mx, my):
                    active = 0
                if box2.collidepoint(mx, my):
                    active = 1
            if ev.type == pygame.JOYBUTTONDOWN:
                # A para confirmar / próximo
                if ev.button == JOYSTICK_SKIP_BUTTON_A:
                    if active == 0:
                        active = 1
                    else:
                        if input_boxes[1].strip() != "":
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                # B para alternar active
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    active = 1 - active

        # render
        screen.fill((12, 12, 28))
        title = title_font.render("Digite os nomes", True, (255, 255, 200))
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 180))
        p1 = font.render(prompt1, True, (220, 220, 220))
        p2 = font.render(prompt2, True, (220, 220, 220))
        screen.blit(p1, (W // 2 - p1.get_width() // 2, H // 2 - 80))
        screen.blit(p2, (W // 2 - p2.get_width() // 2, H // 2))
        # boxes
        box1 = pygame.Rect(W // 2 - 280, H // 2 - 20, 560, 48)
        box2 = pygame.Rect(W // 2 - 280, H // 2 + 60, 560, 48)
        color_active = (200, 200, 240)
        color_inactive = (80, 80, 110)
        pygame.draw.rect(screen, color_active if active == 0 else color_inactive, box1, border_radius=6)
        pygame.draw.rect(screen, color_active if active == 1 else color_inactive, box2, border_radius=6)
        txt1 = font.render(input_boxes[0] or "Player1", True, (10, 10, 20))
        txt2 = font.render(input_boxes[1] or "Player2", True, (10, 10, 20))
        screen.blit(txt1, (box1.x + 12, box1.y + 8))
        screen.blit(txt2, (box2.x + 12, box2.y + 8))
        info_s = font.render(info, True, (180, 180, 180))
        screen.blit(info_s, (W // 2 - info_s.get_width() // 2, H // 2 + 140))
        pygame.display.flip()
        clock.tick(30)
