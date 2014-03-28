import pygame


class Fireball(pygame.sprite.Sprite):
    def __init__(self):
        super(Fireball, self).__init__()
        self.position = [10, 10]
        self.image = pygame.image.load("3Fireball.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position
        self.stage = -1
        self.stage_inc()

    def stage_inc(self):
        self.stage += 1
        if self.stage >= 12:
            self.stage = 0
        col = self.stage % 3
        row = self.stage // 3
        self.cur_image = self.image.subsurface((32*col, 32*row, 32, 32))

    def get_image(self):
        return self.cur_image

    def move(self, x, y):
        self.position[0] = self.position[0] + x
        self.position[1] = self.position[1] + y
        self.rect.topleft = self.position
