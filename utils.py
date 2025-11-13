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


# ---------------------- helpers de imagem ----------------------

def load_and_scale(img_path, W, H, keep_aspect=True):
    """
    Carrega uma imagem de disco e escala para caber em W x H.

    O que faz:
        - Verifica se o arquivo existe; se não existir retorna None.
        - Carrega com pygame.image.load(...).convert_alpha() (mantém canal alpha).
        - Se keep_aspect for True, preserva proporção e escala para caber em W x H.
        - Se keep_aspect for False, escala exatamente para (W, H).
    Recebe:
        - img_path: caminho do arquivo de imagem (str).
        - W: largura destino (int).
        - H: altura destino (int).
        - keep_aspect: bool (padrão True) — manter proporção ou não.
    Retorna:
        - pygame.Surface escalada ou None se o arquivo não existir.
    Observações:
        - Usa pygame.transform.smoothscale para qualidade melhor.
        - Lança exceção se ocorrer erro de leitura/decodificação — deixamos propagar,
          mas no código chamador geralmente se verifica existência antes.
    """
    if not os.path.exists(img_path):
        return None
    img = pygame.image.load(img_path).convert_alpha()
    if keep_aspect:
        iw, ih = img.get_size()
        scale = min(W / iw, H / ih)
        return pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
    return pygame.transform.smoothscale(img, (W, H))


# ---------------------- sequência de 'quadrinhos' / tutoriais ----------------------

def show_quadrinhos_sequence(screen, clock, W, H, image_paths, duration_ms=QUADRINHO_DURATION_MS):
    """
    Mostra uma sequência de imagens (quadrinhos/tutorial) uma a uma.

    O que faz:
        - Carrega (via load_and_scale) cada imagem da lista image_paths (mantendo
          a escala definida pelo chamador).
        - Exibe cada imagem por duration_ms milissegundos.
        - Permite pular a imagem atual com teclado (ENTER/SPACE), com o mouse (MOUSE_LEFT),
          ou com joystick A (JOYSTICK_SKIP_BUTTON_A).
        - Durante a exibição, pressionar o botão configurado para tutorial (JOYSTICK_TUTORIAL_BUTTON_B)
          abre recursivamente a sequência definida em TUTORIAL_PATHS.
        - ESC cancela toda a sequência (retorna False).
    Recebe:
        - screen: pygame.Surface onde desenhar.
        - clock: pygame.time.Clock para controlar FPS.
        - W, H: dimensão da tela (int).
        - image_paths: lista de caminhos para imagens a exibir.
        - duration_ms: duração em ms para cada imagem (padrão vem de config).
    Retorna:
        - True  -> terminou a sequência normalmente.
        - False -> usuário pressionou ESC (ou saiu).
    Observações de implementação:
        - Faz uso de load_and_scale(..., keep_aspect=False) na chamada original neste projeto,
          mas aqui usamos o parâmetro recebido (o chamador passa keep_aspect=False normalmente).
        - A função é síncrona e bloqueante — o loop interno consome eventos até a sequência terminar.
    """
    imgs = [load_and_scale(p, W, H, keep_aspect=False) for p in image_paths]
    idx = 0
    num = len(imgs)
    while idx < num:
        img = imgs[idx]
        start = pygame.time.get_ticks()
        exited_early = False
        # tempo de exibição para a imagem atual
        while pygame.time.get_ticks() - start < duration_ms:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    # fechar janela encerra completamente a aplicação
                    pygame.quit()
                    sys.exit(0)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        # cancelar toda a sequência
                        return False
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # pular para a próxima imagem
                        exited_early = True
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == MOUSE_LEFT:
                    # clique do mouse pula para a próxima imagem
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_SKIP_BUTTON_A:
                    # botão A do joystick pula
                    exited_early = True
                if ev.type == pygame.JOYBUTTONDOWN and ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    # abertura do tutorial enquanto outra sequência está sendo exibida:
                    # chama recursivamente a sequência principal do tutorial (TUTORIAL_PATHS).
                    # Note que isso empilha chamadas; comportamento intencional no projeto.
                    show_quadrinhos_sequence(screen, clock, W, H, TUTORIAL_PATHS, duration_ms=6000)
            # desenha a imagem atual (ou fallback)
            if img:
                screen.blit(img, (0, 0))
            else:
                # fallback visual caso a imagem esteja ausente
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


# ---------------------- entrada de nomes dos jogadores ----------------------

def get_player_names(screen, clock, W, H):
    """
    Interface simples para digitar nomes de dois jogadores.

    O que faz:
        - Mostra duas caixas de texto para digitar "Nome do Jogador 1" e "Nome do Jogador 2".
        - Suporta teclado, mouse e joystick para entrada e navegação:
            - Enter/KP_ENTER: confirma o campo atual (avança para o próximo ou finaliza se no segundo).
            - BACKSPACE: apaga último caractere.
            - Click numa caixa ativa muda o campo ativo.
            - Joystick: A (JOYSTICK_SKIP_BUTTON_A) avança/confirmar; B (JOYSTICK_TUTORIAL_BUTTON_B) alterna o campo.
        - Não permite confirmar com segundo nome vazio.
        - ESC retorna None (cancelamento).
    Recebe:
        - screen: pygame.Surface para renderizar.
        - clock: pygame.time.Clock para controlar FPS.
        - W, H: dimensões da tela (int).
    Retorna:
        - Tuple (name1, name2) com strings (trimadas) ou None se o usuário cancelar.
    Observações:
        - Valores padrão "Player1"/"Player2" são usados se o campo for deixado em branco
          apenas no momento de confirmação (o código atual exige nome2 não vazio).
        - Limite de caracteres por campo: max_len (20).
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
                    # cancelar entrada de nomes
                    return None
                if ev.key == pygame.K_BACKSPACE:
                    # apagar último caractere do campo ativo
                    if len(input_boxes[active]) > 0:
                        input_boxes[active] = input_boxes[active][:-1]
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    # confirmar campo atual: se for o primeiro avança, se for o segundo tenta retornar nomes
                    if active == 0:
                        active = 1
                    else:
                        # não aceita segundo nome vazio
                        if input_boxes[1].strip() == "":
                            # simplesmente ignora (permanece no campo 1)
                            pass
                        else:
                            # retorna nomes com fallback caso algum campo esteja vazio ao confirmar
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                else:
                    # inserir caractere Unicode (respeita limite e caracteres imprimíveis)
                    ch = ev.unicode
                    if ch and len(input_boxes[active]) < max_len and ord(ch) >= 32:
                        input_boxes[active] += ch
            if ev.type == pygame.MOUSEBUTTONDOWN:
                # clique nas áreas predefinidas altera o campo ativo
                mx, my = ev.pos
                box1 = pygame.Rect(W // 2 - 280, H // 2 - 20, 560, 48)
                box2 = pygame.Rect(W // 2 - 280, H // 2 + 60, 560, 48)
                if box1.collidepoint(mx, my):
                    active = 0
                if box2.collidepoint(mx, my):
                    active = 1
            if ev.type == pygame.JOYBUTTONDOWN:
                # joystick A: confirmar/avançar
                if ev.button == JOYSTICK_SKIP_BUTTON_A:
                    if active == 0:
                        active = 1
                    else:
                        if input_boxes[1].strip() != "":
                            return (input_boxes[0].strip() or "Player1", input_boxes[1].strip() or "Player2")
                # joystick B: alterna active (funcionalidade prática em gamepads)
                if ev.button == JOYSTICK_TUTORIAL_BUTTON_B:
                    active = 1 - active

        # renderização do formulário
        screen.fill((12, 12, 28))
        title = title_font.render("Digite os nomes", True, (255, 255, 200))
        screen.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 180))
        p1 = font.render(prompt1, True, (220, 220, 220))
        p2 = font.render(prompt2, True, (220, 220, 220))
        screen.blit(p1, (W // 2 - p1.get_width() // 2, H // 2 - 80))
        screen.blit(p2, (W // 2 - p2.get_width() // 2, H // 2))
        # caixas de entrada
        box1 = pygame.Rect(W // 2 - 280, H // 2 - 20, 560, 48)
        box2 = pygame.Rect(W // 2 - 280, H // 2 + 60, 560, 48)
        color_active = (200, 200, 240)
        color_inactive = (80, 80, 110)
        pygame.draw.rect(screen, color_active if active == 0 else color_inactive, box1, border_radius=6)
        pygame.draw.rect(screen, color_active if active == 1 else color_inactive, box2, border_radius=6)
        # mostra texto dos campos (ou placeholders)
        txt1 = font.render(input_boxes[0] or "Player1", True, (10, 10, 20))
        txt2 = font.render(input_boxes[1] or "Player2", True, (10, 10, 20))
        screen.blit(txt1, (box1.x + 12, box1.y + 8))
        screen.blit(txt2, (box2.x + 12, box2.y + 8))
        info_s = font.render(info, True, (180, 180, 180))
        screen.blit(info_s, (W // 2 - info_s.get_width() // 2, H // 2 + 140))
        pygame.display.flip()
        clock.tick(30)
