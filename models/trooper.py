import pygame


class Trooper(pygame.sprite.Sprite):
    def __init__(self):
        super(Trooper, self).__init__()
        self.position = [610, 10]
        self.image = pygame.image.load("2Stormtrooper.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

    def move(self, x, y):
        self.position[0] = self.position[0] + x
        self.position[1] = self.position[1] + y
        self.rect.topleft = self.position
