import datetime
from os import path


# Paths / constantes globais
BASE_ASSETS = path.join('assets')
INTRO_QUADRINHOS = [
path.join(BASE_ASSETS, 'img', 'quadrinho3.png'),
path.join(BASE_ASSETS, 'img', 'quadrinho4.png'),
path.join(BASE_ASSETS, 'img', 'quadrinho5.png'),
path.join(BASE_ASSETS, 'img', 'procurado1.png'),
]
POST_BOSS1_QUADRINHO = path.join(BASE_ASSETS, 'img', 'procurado2.png')
POST_BOSS2_QUADRINHOS = [
path.join(BASE_ASSETS, 'img', 'quadrinho1.png'),
path.join(BASE_ASSETS, 'img', 'quadrinho2.png'),
]
TUTORIAL_PATHS = [path.join(BASE_ASSETS, 'img', 'tutorial1.png'), path.join(BASE_ASSETS, 'img', 'tutorial2.png')]
QUADRINHO_DURATION_MS = 10000


# joystick mapping
JOYSTICK_SKIP_BUTTON_A = 0
JOYSTICK_TUTORIAL_BUTTON_B = 1
JOYSTICK_RANKING_BUTTON_Y = 3
MOUSE_LEFT = 1


# ranking
RANKING_FILE = "ranking.json"
MAX_RANKING = 10


# boss constants
BOSS_HAND_BULLET_SPEED = 500.0


# misc
DATE_NOW = lambda: datetime.datetime.utcnow().isoformat() + 'Z'