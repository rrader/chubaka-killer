from math import log
from random import random
import time
import pygame
from pygame.locals import *
from models.chubaka import Chubaka
from models.fireball import Fireball
from models.trooper import Trooper

from faces import Detector


class Clock(object):
    def __init__(self):
        self.last_time = time.time()
        self.events = {}
        self._id = 0
        self.scheduled = []
        self.trooper_lambda = 0.1

    def set_interval(self, func, args, interval, distribution="UNIFORM"):
        self._id += 1
        self.events[self._id] = (func, args, interval, distribution)
        self.schedule(self._id)
        return self._id

    def unset_interval(self, _id):
        if _id in self.events:
            del self.events[_id]

    def schedule(self, _id):
        func, args, parameter, distribution = self.events[_id]
        scheduled = self.scheduled[:]
        if distribution == "UNIFORM":
            next_time = time.time() + parameter
        elif distribution == "EXPONENTIAL":
            next_time = time.time() + ((-1)/parameter)*log(random())
        elif distribution == "ONCE":
            next_time = time.time() + parameter
        else:
            raise Exception("something wrong")
        scheduled.append((next_time, func, args, _id))
        self.scheduled = sorted(scheduled, key=lambda x: x[0])

    def tick(self):
        new_time = time.time()
        # delta = new_time - self.last_time
        while self.scheduled and self.scheduled[0][0] < new_time:
            self.scheduled[0][1](*self.scheduled[0][2])
            if self.scheduled[0][3] in self.events and self.events[self.scheduled[0][3]][3] != "ONCE":
                self.schedule(self.scheduled[0][3])
            del self.scheduled[0]

        self.last_time = new_time


class App(object):
    def __init__(self):
        self._running = True
        self._display = None
        self.size = self.width, self.height = 640, 100
        self.clock = Clock()

    def on_init(self):
        pygame.init()
        self._display = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        self._gameover = False
        self.chubaka = Chubaka()
        self.fireballs = []
        self.last_fireball = 0
        self.troopers = []
        self.explosion = pygame.image.load("4Explosion2.png").convert_alpha()
        self.gameover = pygame.image.load("5GAMEOVER.jpg")
        self.explosions = []
        self.detector = Detector(self.detector_ready, self.throw)
        self._ready = False
        self.countdown_value = -1
        # self.detector_ready()

    def detector_ready(self):
        self.clock.set_interval(self.countdown, [], 1, "ONCE")
        self.countdown_value = 3

    def countdown(self):
        print("ONCE SCHEDULED")
        self.countdown_value -= 1
        if self.countdown_value <= 0:
            self._ready = True
            self.start()
            return
        self.clock.set_interval(self.countdown, [], 1, "ONCE")

    def start(self):
        self.troopers_timer = self.clock.set_interval(self.generate_trooper, [], 0.8, "EXPONENTIAL")
        self.explosions_timer = self.clock.set_interval(self.do_explosion, [], 0.1, "UNIFORM")
        self.fireball_timer = self.clock.set_interval(self.do_fireball_roll, [], 0.07, "UNIFORM")

    def do_explosion(self):
        explosions = []
        for exp in self.explosions:
            left, stage = exp
            if stage < 7:
                explosions.append((left, stage+1))
        self.explosions = explosions

    def do_fireball_roll(self):
        for fb in self.fireballs:
            fb.stage_inc()

    def generate_trooper(self):
        trooper = Trooper()
        trooper.position = [self.width, 10]
        _id = self.clock.set_interval(self.move_trooper, [trooper], 0.1)
        trooper.id = _id
        self.troopers.append(trooper)

    def throw(self):
        if time.time() - self.last_fireball < 0.2:
            return
        self.last_fireball = time.time()
        if not self._ready:
            return
        fireball = Fireball()
        fireball.position = [70, 10]
        _id = self.clock.set_interval(self.move_fireball, [fireball], 0.05)
        fireball.id = _id
        self.fireballs.append(fireball)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.throw()

    def kill_fireball(self, fireball):
        self.clock.unset_interval(fireball.id)
        if fireball not in self.fireballs:
            return
        del self.fireballs[self.fireballs.index(fireball)]

    def move_fireball(self, fireball):
        if fireball.position[0] > self.width:
            self.kill_fireball(fireball)
        fireball.move(12, 0)

    def move_trooper(self, trooper):
        if trooper.position[0] < self.chubaka.position[0] + self.chubaka.rect.width:
            self.kill_trooper(trooper)
        trooper.move(-7, 0)

    def on_loop(self):
        self.clock.tick()
        if self._gameover:
            self._display.fill((0, 0, 0))
            self._display.blit(self.gameover, (250, 0))
        elif self._ready:
            self._display.fill((150, 150, 150))
            self._display.blit(self.chubaka.image, self.chubaka.position)
            self.check_collisions()
            for fb in self.fireballs:
                self._display.blit(fb.get_image(), fb.position)
            for tp in self.troopers:
                self._display.blit(tp.image, tp.position)
            for exp in self.explosions:
                left, stage = exp
                img = self.explosion.subsurface((67*stage, 0, 67, 67))
                self._display.blit(img, (left, 10))
        elif self.countdown_value >= 0:
            self._display.fill((0, 0, 0))
            font = pygame.font.Font(None, 36)
            text = font.render("READY... COUNTDOWN " + str(self.countdown_value),
                               1, (255, 10, 10))
            textpos = text.get_rect()
            textpos.centerx = self._display.get_rect().centerx
            self._display.blit(text, textpos)
        else:
            self._display.fill((255, 255, 255))
            font = pygame.font.Font(None, 36)
            text = font.render("Sit still... and keep blinking", 1, (255, 10, 10))
            textpos = text.get_rect()
            textpos.centerx = self._display.get_rect().centerx
            self._display.blit(text, textpos)

        pygame.display.update()

    def kill_trooper(self, trooper):
        self.clock.unset_interval(trooper.id)
        if trooper not in self.troopers:
            return
        del self.troopers[self.troopers.index(trooper)]

    def check_collisions(self):
        # while True:
            # fireballs = [f.rect.x + f.rect.width/2 for f in self.fireballs]
            # troopers = [f.rect.x + f.rect.width/2 for f in self.troopers]
        if not self.troopers:
            return
        l_trooper = self.troopers[0].rect
        if self.chubaka.rect.x + self.chubaka.rect.width > l_trooper.x:
            self._gameover = True
            return
        if not self.fireballs:
            return
        l_fireball = self.fireballs[0].rect
        if l_fireball.x + l_fireball.width > l_trooper.x:
            self.explosions.append((l_trooper.x, 0))
            self.kill_trooper(self.troopers[0])
            self.kill_fireball(self.fireballs[0])

    def on_render(self):
        pass

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()