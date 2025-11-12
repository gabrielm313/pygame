# ranking.py
import os
import json
import datetime
import pygame

from config import RANKING_FILE, MAX_RANKING, JOYSTICK_SKIP_BUTTON_A, JOYSTICK_RANKING_BUTTON_Y

def load_ranking():
    """
    Carrega o arquivo de ranking (lista de entradas) ou retorna lista vazia.
    Cada entrada esperada: {"name": str, "time_seconds": float, "date": ISO8601}
    """
    if not os.path.exists(RANKING_FILE):
        return []
    try:
        with open(RANKING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        # em caso de erro de leitura/parse, ignora e retorna lista vazia
        pass
    return []

def save_ranking_entry(name, time_seconds):
    """
    Adiciona uma entrada ao ranking e grava o arquivo, mantendo apenas os MAX_RANKING melhores (menor tempo).
    """
    ranking = load_ranking()
    entry = {
        "name": str(name),
        "time_seconds": float(time_seconds),
        "date": datetime.datetime.utcnow().isoformat() + "Z"
    }
    ranking.append(entry)
    # ordenar ascendente por tempo (melhor = menor)
    ranking = sorted(ranking, key=lambda e: e.get('time_seconds', float('inf')))
    ranking = ranking[:MAX_RANKING]
    try:
        with open(RANKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(ranking, f, indent=2, ensure_ascii=False)
    except Exception:
        # falha ao salvar — não levanta exceção para não travar o jogo
        pass

def show_ranking_screen(screen, clock, W, H):
    """
    Mostra a tela de ranking com os melhores tempos.
    Fecha com ESC / ENTER / SPACE / clique do mouse / botão A ou Y do joystick.
    """
    # fontes
    title_font = pygame.font.Font(None, 64)
    item_font = pygame.font.Font(None, 36)
    hint_font = pygame.font.Font(None, 28)

    ranking = load_ranking()
    showing = True

    while showing:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    showing = False
            if ev.type == pygame.MOUSEBUTTONDOWN:
                showing = False
            if ev.type == pygame.JOYBUTTONDOWN and ev.button in (JOYSTICK_SKIP_BUTTON_A, JOYSTICK_RANKING_BUTTON_Y):
                showing = False

        # background
        screen.fill((10, 10, 20))

        # título
        title = title_font.render("RANKING - MELHORES TEMPOS", True, (255, 215, 0))
        screen.blit(title, (W // 2 - title.get_width() // 2, 40))

        y = 140
        if not ranking:
            no_txt = item_font.render("Nenhum registro ainda.", True, (220, 220, 220))
            screen.blit(no_txt, (W // 2 - no_txt.get_width() // 2, y))
        else:
            for i, e in enumerate(ranking):
                # formatar tempo mm:ss.mmm
                total = float(e.get('time_seconds', 0.0))
                minutes = int(total) // 60
                seconds = int(total) % 60
                ms = int((total - int(total)) * 1000)
                timestr = f"{minutes:d}:{seconds:02d}.{ms:03d}"
                name = e.get('name', '---')
                text = f"{i+1}. {name} — {timestr}"
                it = item_font.render(text, True, (230, 230, 230))
                screen.blit(it, (W // 2 - it.get_width() // 2, y))
                y += 44
                # evita desenhar fora da tela
                if y > H - 140:
                    break

        hint = hint_font.render("Pressione ESC/ENTER/Y/A para voltar", True, (180, 180, 180))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 80))

        pygame.display.flip()
        clock.tick(30)
