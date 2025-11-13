# campaign.py
import pygame

from utils import show_quadrinhos_sequence
from config import INTRO_QUADRINHOS, QUADRINHO_DURATION_MS
from boss1 import run_boss1
from boss2 import run_boss2
from faroeste import run_faroeste


def campaign(screen, clock, W, H, player_names):
    """
    Orquestra a sequência de fases da campanha do jogo.

    Fluxo:
      1. Exibe os quadrinhos/intro (INTRO_QUADRINHOS).
      2. Executa o estágio Boss 1 (run_boss1).
      3. Executa o estágio Boss 2 (run_boss2).
      4. Executa o duelo final (run_faroeste).
      5. Mede o tempo total decorrido entre o início (após os quadrinhos) e o fim do duelo.

    Parâmetros:
      - screen (pygame.Surface):
          Superfície principal onde os estágios desenham (passada às funções de fase).
      - clock (pygame.time.Clock):
          Objeto Clock usado para controlar o frame rate e fornecer delta time.
      - W (int):
          Largura da tela (pixels). Passado para os estágios para posicionamento/escalas.
      - H (int):
          Altura da tela (pixels). Passado para os estágios para posicionamento/escalas.
      - player_names (tuple|list):
          Tupla/lista com os nomes dos jogadores, e.g. ("Nome1", "Nome2").
          Observação: neste módulo os nomes apenas são recebidos para compatibilidade/possível uso
          downstream — as funções individuais de fase não dependem diretamente deles aqui.

    Retorno:
      tuple (completed_bool, winner_id, elapsed_seconds)
        - completed_bool (bool):
            True  -> campanha completada (todas as fases rodaram até o fim);
            False -> abortada / cancelada em algum ponto (ESC ou falha).
        - winner_id (int|None):
            1 -> Jogador 1 venceu o duelo final
            2 -> Jogador 2 venceu o duelo final
            0 -> Empate no duelo final
            None -> A campanha foi cancelada/abortada antes do fim (ex.: ESC)
        - elapsed_seconds (float):
            Tempo total em segundos entre o início da campanha (após os quadrinhos)
            e o término do duelo (ou momento do cancelamento). Se a campanha abortar
            antes do início (por exemplo, se o jogador fechar os quadrinhos), retorna 0.0.

    Observações de comportamento:
      - Se a função show_quadrinhos_sequence retornar False (usuário apertou ESC durante os
        quadrinhos), a campanha termina imediatamente retornando (False, None, 0.0).
      - Se run_boss1 ou run_boss2 retornarem False (jogadores morreram ou pressionaram ESC),
        a campanha termina retornando (False, None, 0.0).
      - Se o duelo final (run_faroeste) retornar None significa cancelamento durante o duelo;
        a função então retorna (False, None, elapsed_seconds) onde elapsed_seconds é o tempo
        acumulado até o cancelamento.
    """
    # Mostra os quadrinhos iniciais e permite pular/voltar com ESC.
    ok = show_quadrinhos_sequence(screen, clock, W, H, INTRO_QUADRINHOS, duration_ms=QUADRINHO_DURATION_MS)
    if not ok:
        # jogador cancelou durante os quadrinhos
        return (False, None, 0.0)

    # marca início do tempo da campanha (após os quadrinhos)
    start_ticks = pygame.time.get_ticks()

    # Fase 1 - Boss 1
    # run_boss1(screen, clock, W, H) -> bool (True se fase vencida, False se abortada/derrota)
    res1 = run_boss1(screen, clock, W, H)
    if not res1:
        # abortado ou derrota na fase 1
        return (False, None, 0.0)

    # Fase 2 - Boss 2
    # run_boss2(screen, clock, W, H) -> bool (True se fase vencida, False se abortada/derrota)
    res2 = run_boss2(screen, clock, W, H)
    if not res2:
        # abortado ou derrota na fase 2
        return (False, None, 0.0)

    # Fase final - duelo faroeste
    # run_faroeste(screen, clock, W, H) -> 1 | 2 | 0 | None
    #   1 -> player1 venceu, 2 -> player2 venceu, 0 -> empate, None -> cancelado (ESC)
    winner_final = run_faroeste(screen, clock, W, H)

    # registra fim e calcula tempo decorrido (mesmo se winner_final for None -> cancelado durante duelo)
    end_ticks = pygame.time.get_ticks()
    elapsed = (end_ticks - start_ticks) / 1000.0

    if winner_final is None:
        # cancelado no duelo final: campanha não é considerada "completada"
        return (False, None, elapsed)

    # campanha completada com resultado do duelo final
    return (True, winner_final, elapsed)
