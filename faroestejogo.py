import pygame
import random
import sys
from pygame.locals import *

H, L = 1024, 768
FPS = 60

KEY_P1 = pygame.K_a  #tecla para apertar do jogador esquerdo A
KEY_P2 = pygame.K_l  #tecla para apertar do jogador direito L


#delay no erro do jogador (em milisegundos)
erro = 3000


#condição de vitória do jogo (melhor de 3)
condv = 2

#contagem regressiva aleatória
minimo = 1
máximo = 5

#cores texto
WHITE = (255,255,255)
RED = (200, 40, 40)
GREEN = (40, 200, 40)
YELLOW = (240, 180, 30)


#nova duração do contador
def new_countdown_duration():
    #parte feita com o chat
    #Retorna duração da contangem em ms (aleatória)
    s = random.uniform(minimo, máximo)
    return int(s*1000)

def draw_centered_text(surface, text, font, color, y): # desenha texto no meio da tela
    txt = font.render(text, True, color)
    rect = txt.get_rect(center=(L//2, y))
    surface.blit(txt, rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((L, H))
    pygame.display.set_caption("Duelo - Já!")
    clock = pygame.time.Clock()
    fundo = pygame.image.load('faroeste.png').convert()
    fundo = pygame.transform.scale(fundo, (L, H))
    clock = pygame.time.Clock()

    #fontes
    big_font = pygame.font.SysFont("consolas", 96)
    med_font = pygame.font.SysFont("consolas", 40)
    small_font = pygame.font.SysFont("consolas", 28)

    # Estados do round:
    # 'countdown' -> conta regressiva, aguardando "Já!"
    # 'ready' -> exibido "Já!", aceita quem apertar primeiro
    # 'penalty' -> exibe penalidade para quem apertou cedo (mas o round continua)
    # 'round_end' -> exibe vencedor da rodada e aguarda reinício automático
    # 'game_over' -> exibe vencedor do jogo

    state = 'countdown' #estado do jogo
    nextstate = 0 #próximo estado do tempo

    #temporizadores
    contador_dur = new_countdown_duration()
    contador_start = pygame.time.get_ticks()

    #penalidades 
    p1_falta = 0
    p2_falta = 0

    #placar
    pontuaçãoP1 = 0
    pontuaçãoP2 = 0

    #vencedor da rodada ('None', 'p1', 'p2')
    rodV = None

    # Caso não tenha imagens, desenharemos retângulos pixelizados
    game = True
    while game:
        now = pygame.time.get_ticks()
        dt =  clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                game = False 

            elif event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game = False  
                if state == 'ready':
                    #caso não esteja penalizado
                    if event.key == KEY_P1 and now >= p1_falta:
                        #se o jogador 1 apertou no momento certo, então vence a rodada
                        rodV = 'p1'
                        state = 'round_end'
                        nextstate = now + 1500 #mostra por 1,5s antes de reiniciar

                    elif event.key == KEY_P2 and now >= p2_falta:
                        rodV = 'p2'
                        state = 'round_end'
                        nextstate = now + 1500 
                elif state == 'countdown':
                    #penalidade pra quem acertou cedo
                    if event.key == KEY_P1:
                        p1_falta = max(p1_falta, now + erro)
                        state = 'penalty'
                        nextstate = now + 1500  # mostra alerta por 1.5s
                    elif event.key == KEY_P2:
                        p2_falta = max(p2_falta, now + erro)
                        state = 'penalty'
                        nextstate = now + 1500
                elif state == 'game_over':
                    # reinicia o jogo com R
                    if event.key == pygame.K_r:
                        pontuaçãoP1 = pontuaçãoP2 = 0
                        round_winner = None
                        state = 'countdown'
                        contador_dur = new_countdown_duration()
                        contador_start = now    

        #transições automáticas
        if state == 'countdown':
            elapsed = now - contador_start
            if elapsed >= contador_dur:
                state = 'ready'
                # quando entrar em 'ready' queremos registrar a hora de início (opcional)
                ready_start = now
        elif state == 'penalty':
            if now >= nextstate:
                # volta pro countdown (inicia uma nova contagem)
                state = 'countdown'
                contador_dur = new_countdown_duration()
                contador_start = now
        elif state == 'round_end':
            # conta placar e verifica fim de jogo
            if rodV == 'p1': #se o player 1 ganhou a rodada
                pontuaçãoP1 += 1
            elif rodV == 'p2': #se o player 2 ganhou a rodada
                pontuaçãoP2 += 1

                
            if pontuaçãoP1 >= condv or pontuaçãoP2 >= condv:
                state = 'game_over'
            else:
                # preparar novo round depois do tempo next_state_time
                if now >= nextstate:
                    rodV = None
                    state = 'countdown'
                    contador_dur = new_countdown_duration()
                    contador_start = now
        #estado game_over: espera o input 'r' para reiniciar

        #desenho

        screen.blit(fundo, (0, 0))
                
