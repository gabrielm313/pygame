# main.py
# Arquivo principal que inicia o jogo, cria a janela/área de desenho e controla o fluxo:
# - mostra o menu
# - obtém nomes dos jogadores
# - executa a campanha
# - salva/mostra ranking
#
# Este arquivo importa as funções de interface (menu, campaign, ranking, utils) e
# contém helpers para inicializar o pygame de forma tolerante a falhas.

import sys
import pygame

from menu import menu
from utils import get_player_names
from campaign import campaign
from ranking import save_ranking_entry, show_ranking_screen


def safe_init_pygame():
    """
    Inicializa pygame, o mixer de áudio e o sistema de joysticks com tolerância a falhas.

    O que faz:
        - Chama pygame.init() para inicializar os subsistemas básicos do Pygame.
        - Tenta inicializar pygame.mixer; se falhar (por exemplo, sem dispositivo de áudio),
          ignora o erro e continua — isso evita que a aplicação quebre em ambientes sem som.
        - Tenta inicializar pygame.joystick; se falhar, ignora o erro.
        - Percorre joysticks detectados e chama init() em cada um, ignorando exceções.

    Recebe:
        - Nada.

    Retorna:
        - None. (Efeitos colaterais: subsistemas do pygame inicializados quando possível.)
    """
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        # mixer pode falhar se não houver dispositivo de áudio; seguir mesmo assim
        pass
    try:
        pygame.joystick.init()
    except Exception:
        pass
    # inicializar joysticks existentes
    try:
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
    except Exception:
        pass


def create_screen():
    """
    Cria a superfície de exibição (screen).

    O que faz:
        - Tenta ativar o modo fullscreen nativo usando as resoluções atuais do display.
        - Se a tentativa de fullscreen falhar (por exemplo, em ambientes sem suporte),
          faz fallback para uma janela de 1280x720.

    Recebe:
        - Nada.

    Retorna:
        - Tupla (screen, W, H)
            - screen: pygame.Surface retornada por pygame.display.set_mode(...)
            - W: largura escolhida (int)
            - H: altura escolhida (int)
    """
    try:
        info = pygame.display.Info()
        W, H = info.current_w, info.current_h
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return screen, W, H
    except Exception:
        # fallback
        W, H = 1280, 720
        screen = pygame.display.set_mode((W, H))
        return screen, W, H


def main():
    """
    Função principal do programa — organiza o loop principal de navegação entre menu,
    obtenção de nomes, execução da campanha e exibição/salvamento do ranking.

    O que faz (detalhado):
        - Inicializa Pygame de forma tolerante via safe_init_pygame().
        - Cria a tela (screen) e o clock.
        - Entra num loop principal que:
            1. Chama menu(screen, clock, W, H). Se o menu lançar uma exceção, encerra o jogo
               imprimindo o erro no stderr.
            2. Se o menu retornar falsy (usuário escolheu sair), encerra o programa.
            3. Pede nomes dos jogadores com get_player_names(...). Se o jogador cancelar (None),
               volta ao menu.
            4. Executa campaign(...). Em caso de exceção durante a campanha, mostra o ranking
               e volta ao menu.
            5. Se a campanha foi completada e há um vencedor válido (1 ou 2), salva o ranking
               com save_ranking_entry(nome_do_vencedor, tempo) (com tratamento de exceções).
            6. Exibe uma tela de parabéns com o tempo do vencedor (até qualquer tecla/clique),
               depois mostra a tela de ranking.
            7. Se a campanha foi abortada/empatada/sem vencedor, mostra o ranking mesmo assim.

    Recebe:
        - Nada.

    Retorna:
        - None (a função termina apenas quando o usuário sai do programa ou ocorre sys.exit).
    """
    safe_init_pygame()
    screen, W, H = create_screen()
    pygame.display.set_caption('Joguinho Integrado')
    clock = pygame.time.Clock()

    while True:
        try:
            entrar = menu(screen, clock, W, H)
        except Exception as e:
            # se o menu travar inesperadamente, encerra com erro visível no console
            print("Erro no menu:", e, file=sys.stderr)
            pygame.quit()
            sys.exit(1)

        if not entrar:
            # usuário escolheu sair no menu
            pygame.quit()
            sys.exit(0)

        # pedir nomes dos jogadores
        names = get_player_names(screen, clock, W, H)
        if names is None:
            # cancelou -> volta ao menu
            continue

        # rodar campanha
        try:
            completed, winner_id, elapsed = campaign(screen, clock, W, H, player_names=names)
        except Exception as e:
            print("Erro durante a campanha:", e, file=sys.stderr)
            # em caso de erro, mostra ranking e volta ao menu
            try:
                show_ranking_screen(screen, clock, W, H)
            except Exception:
                pass
            continue

        # se completou e houve vencedor (1 ou 2), salvar no ranking
        if completed and winner_id in (1, 2):
            winner_name = names[winner_id - 1]
            try:
                save_ranking_entry(winner_name, elapsed)
            except Exception as e:
                print("Falha ao salvar ranking:", e, file=sys.stderr)

            # mostrar tela simples de parabéns antes do ranking
            try:
                font = pygame.font.Font(None, 56)
                small = pygame.font.Font(None, 36)
                showing = True
                show_time_str = f"{int(elapsed)//60}:{int(elapsed)%60:02d}.{int((elapsed-int(elapsed))*1000):03d}"
                message = f"Parabéns {winner_name}! Tempo: {show_time_str}"
                # exibe até qualquer tecla / clique
                while showing:
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            pygame.quit(); sys.exit(0)
                        if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN or (ev.type == pygame.JOYBUTTONDOWN and ev.button in (0,3)):
                            showing = False
                    screen.fill((8,8,12))
                    tx = font.render(message, True, (220,220,120))
                    screen.blit(tx, (W//2 - tx.get_width()//2, H//2 - 50))
                    info = small.render("Pressione qualquer tecla ou Y/A para ver o ranking", True, (200,200,200))
                    screen.blit(info, (W//2 - info.get_width()//2, H//2 + 30))
                    pygame.display.flip()
                    clock.tick(30)
            except Exception:
                # falhas aqui não devem quebrar o fluxo principal
                pass

            # mostrar ranking
            try:
                show_ranking_screen(screen, clock, W, H)
            except Exception:
                pass
        else:
            # abortou, empate ou sem vencedor -> mostrar ranking mesmo assim
            try:
                show_ranking_screen(screen, clock, W, H)
            except Exception:
                pass


if __name__ == "__main__":
    main()
