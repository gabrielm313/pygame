# campaign.py
import pygame

from utils import show_quadrinhos_sequence
from config import INTRO_QUADRINHOS, QUADRINHO_DURATION_MS
from boss1 import run_boss1
from boss2 import run_boss2
from faroeste import run_faroeste


def campaign(screen, clock, W, H, player_names):
    """
    Executa a campanha completa:
    - Mostra quadrinhos de introdução
    - Roda Boss 1
    - Roda Boss 2
    - Roda duelo final (faroeste)
    
    Retorna uma tupla:
        (completed_bool, winner_id, elapsed_seconds)
    
    winner_id:
        1 -> Jogador 1 venceu
        2 -> Jogador 2 venceu
        0 -> Empate
        None -> Cancelou / abortou
    """
    # quadrinhos iniciais
    ok = show_quadrinhos_sequence(screen, clock, W, H, INTRO_QUADRINHOS, duration_ms=QUADRINHO_DURATION_MS)
    if not ok:
        return (False, None, 0.0)

    start_ticks = pygame.time.get_ticks()

    # fase 1 - boss slime
    res1 = run_boss1(screen, clock, W, H)
    if not res1:
        return (False, None, 0.0)

    # fase 2 - boss nave
    res2 = run_boss2(screen, clock, W, H)
    if not res2:
        return (False, None, 0.0)

    # fase final - duelo faroeste
    winner_final = run_faroeste(screen, clock, W, H)
    end_ticks = pygame.time.get_ticks()
    elapsed = (end_ticks - start_ticks) / 1000.0

    if winner_final is None:
        # cancelou no faroeste
        return (False, None, elapsed)

    # completou tudo
    return (True, winner_final, elapsed)
