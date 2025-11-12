from os import path

#RESOLUÇÃO DA TELA
LARGURA = 1920
ALTURA = 1080

# Estabelece a pasta que contem as figuras.
IMG_DIR = path.join(path.dirname(__file__), 'assets', 'img')

# BG_PATH = "assets/img/fundo_pg.png"

#ESTADOS POSSÍVEIS SPRITE JOGADOR
ANDANDO = 0
PARADO = 1
ATIRANDO = 2
CIMA = 3
BAIXO = 4 
CIMAESQ = 5
CIMADIR = 6
BAIXOESQ = 7
BAIXODIR = 8
MORRENDO = 9

#TAMANHOS
PLAYER_LARG = 200
PLAYER_ALTU = 300

#ESTADOS DO JOGO
INIT = 0
ESCOLHE = 1
JOGO = 2 
MORTO = 3
QUIT = 4

#FPS
FPS = 60

#GRAVIDADE
GRAVIDADE = 5
