# config.py
import datetime
from os import path

"""
Arquivo de configuração global do jogo.

Contém constantes e caminhos (paths) usados por múltiplos módulos
(menu, boss1, boss2, faroeste, ranking, etc).
Centralizar essas variáveis evita repetição e facilita manutenção.

Cada seção possui explicação detalhada.
"""

# ===============================
# Caminhos base e recursos visuais
# ===============================

# Caminho base da pasta de assets (imagens, sons, fontes)
BASE_ASSETS = path.join('assets')

# Sequência de imagens exibidas no início da campanha (história introdutória)
INTRO_QUADRINHOS = [
    path.join(BASE_ASSETS, 'img', 'quadrinho3.png'),
    path.join(BASE_ASSETS, 'img', 'quadrinho4.png'),
    path.join(BASE_ASSETS, 'img', 'quadrinho5.png'),
    path.join(BASE_ASSETS, 'img', 'procurado1.png'),
]

# Imagem exibida após a vitória sobre o Boss 1
POST_BOSS1_QUADRINHO = path.join(BASE_ASSETS, 'img', 'procurado2.png')

# Sequência de imagens exibidas após derrotar o Boss 2 (antes do duelo final)
POST_BOSS2_QUADRINHOS = [
    path.join(BASE_ASSETS, 'img', 'quadrinho1.png'),
    path.join(BASE_ASSETS, 'img', 'quadrinho2.png'),
]

# Imagens do tutorial (mostradas quando o jogador pressiona o botão correspondente)
TUTORIAL_PATHS = [
    path.join(BASE_ASSETS, 'img', 'tutorial1.png'),
    path.join(BASE_ASSETS, 'img', 'tutorial2.png'),
]

# Duração padrão de exibição de cada "quadrinho" (em milissegundos)
QUADRINHO_DURATION_MS = 10000


# ===============================
# Controles de joystick e mouse
# ===============================
# Esses valores correspondem aos índices de botões no controle (ex: Xbox controller)

JOYSTICK_SKIP_BUTTON_A = 0      # botão A — usado para confirmar/pular
JOYSTICK_TUTORIAL_BUTTON_B = 1  # botão B — abre tutorial
JOYSTICK_RANKING_BUTTON_Y = 3   # botão Y — mostra ranking
MOUSE_LEFT = 1                  # clique esquerdo do mouse


# ===============================
# Sistema de ranking
# ===============================

RANKING_FILE = "ranking.json"  # nome do arquivo de ranking salvo em disco
MAX_RANKING = 10               # quantidade máxima de registros armazenados


# ===============================
# Parâmetros dos chefes
# ===============================

# Velocidade das balas disparadas pelas mãos do Boss 2 (pode ser ajustada para balanceamento)
BOSS_HAND_BULLET_SPEED = 500.0


# ===============================
# Utilitários diversos
# ===============================

# Função lambda para retornar data/hora atual em formato ISO 8601 UTC (ex: "2025-11-12T14:23:45.123Z")
DATE_NOW = lambda: datetime.datetime.utcnow().isoformat() + 'Z'
