import pygame
from config import LARGURA , ALTURA , PLAYER_LARG , PLAYER_ALTU
from assets import PLAYER_IMG , IMG_DIR

class Alien(pygame.sprite.Sprite):
    def __init__(self , groups , assets):
        # Construtor da classe mãe (Sprite).
        pygame.sprite.Sprite.__init__(self)

        self.image = assets[PLAYER_IMG]
        self.react = self.image.get_react()
        self.rect.centerx = LARGURA / 2
        self.rect.bottom = ALTURA - 10
        self.speedx = 5
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