import pygame


class Chubaka(pygame.sprite.Sprite):
    def __init__(self):
        super(Chubaka, self).__init__()
        self.position = [10, 10]
        self.image = pygame.image.load("1Chubaka.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position
