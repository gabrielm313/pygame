import pygame
from config import LARGURA , ALTURA , GRAVIDADE 
from assets import ASTRONAUTA_IMG 


class Astronauta(pygame.sprite.Sprite):
    def __init__(self , groups , assets):
        # Construtor da classe mãe (Sprite).
        super().__init__()
        self.groups = groups
        self.assets = assets

        # frames carregados no assets (lista)
        self.frames = assets['astronauta1']

        self.anim = {
            'parado': [0],
            'andando_d': list(range(0, 5)),      # frames 0..4
            'andando_e': list(range(5,10)), # frames 5..9 (apenas se seu sheet tiver)
            'agachando': [10],                 # exemplo
        }

        # Padrões
        self.state = 'parado'
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_delay = 45  # ms entre frames, ajuste para velocidade de animação

        self.image_original = self.frames[self.anim['parado'][0]]
        self.image = self.image_original.copy()
        self.rect = self.image.get_rect()
        self.rect.centerx = LARGURA // 2
        self.rect.bottom = ALTURA - 40

        self.speedx = 0
        self.speedy = 0
        self.no_chao = True  # controla se está no chão
        self.agachado = False

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0
            self.frame_timer = 0

    def update(self , dt=0):
        # dt = tempo em ms do clock.tick() ou calculado em loop principal

         # Movimento horizontal
        self.rect.x += self.speedx

        # Movimento vertical (pulo e gravidade)
        self.rect.y += self.speedy

        # Aplica gravidade
        if not self.no_chao:
            self.speedy += GRAVIDADE

        # escolhe animação com base no estado / velocidade
        if self.agachado:
            anim_key = 'agachando'
        elif self.speedx != 0:
            anim_key = 'andando_d'
        else:
            anim_key = 'parado'
        
        # se mudou de animação, reinicia frame
        if anim_key != self.state:
            self.set_state(anim_key)

        # avança frames de animação
        self.frame_timer += dt
        frames_idx_list = self.anim.get(anim_key, [0])
        if self.frame_timer >= self.frame_delay:
            self.frame_timer = 0
            self.frame_index = (self.frame_index + 1) % len(frames_idx_list)

        current_frame_number = frames_idx_list[self.frame_index]
        self.image = self.frames[current_frame_number]
        # se precisar ajustar rect (manter bottom/midpoint)
        # exemplo para manter midbottom:
        midbottom = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = midbottom
        
        # Mantém dentro da tela
        if self.rect.right > LARGURA:
            self.rect.right = LARGURA
        if self.rect.left < 0:
            self.rect.left = 0

        # Limite inferior (chão)
        if self.rect.bottom >= ALTURA - 40:  # 10 é a margem do chão
            self.rect.bottom = ALTURA - 40
            self.speedy = 0
            self.no_chao = True

        # Limite superior (teto)
        if self.rect.top <= 0:
            self.rect.top = 0
            self.speedy = 0

    #adicionando funções para os movimentos do personagem
    def pular(self):
        if self.no_chao:  # só pula se estiver no chão
            self.speedy = -82
            self.no_chao = False

    #aqui(agachar) ainda está dando erro
    def agachar(self):
         # já está agachado → não faz nada
        if self.agachado:
            return
        # exemplo simples: trocar a flag e animação
        self.agachado = True
        self.set_state('agachando')

    def levantar(self):
        if not self.agachado:
            return
        self.agachado = False
        self.set_state('parado')