import pygame
from config import LARGURA , ALTURA 
from assets import PLAYER_IMG 

class Jogador(pygame.sprite.Sprite):
    def __init__(self , groups , assets):
        # Construtor da classe mãe (Sprite).
        pygame.sprite.Sprite.__init__(self)

        self.image = assets[PLAYER_IMG]
        self.rect = self.image.get_rect()
        self.rect.centerx = LARGURA // 2
        self.rect.bottom = ALTURA - 10
        self.speedx = 0
        self.groups = groups
        self.assets = assets

    def update(self):
        # Atualização da posição da nave
        self.rect.x += self.speedx

        # Mantem dentro da tela
        if self.rect.right > LARGURA:
            self.rect.right = ALTURA
        if self.rect.left < 0:
            self.rect.left = 0