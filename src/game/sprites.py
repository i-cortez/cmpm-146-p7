import pygame as pg
from settings import *
# from tilemap import collide_hit_rect

img_path = './pixel_art/link_'
w_img_path = './pixel_art/wolf_'
f_path = img_path + 'f'
b_path = img_path + 'b'
r_path = img_path + 'r'
l_path = img_path + 'l'

f_images = [f_path + str(f) + '.png' for f in range(16)]
b_images = [b_path + str(b) + '.png' for b in range(16)]
r_images = [r_path + str(r) + '.png' for r in range(16)]
l_images = [l_path + str(l) + '.png' for l in range(16)]

f_w_path = w_img_path + 'f'
b_w_path = w_img_path + 'b'
r_w_path = w_img_path + 'r'
l_w_path = w_img_path + 'l'

f_wolf = [f_w_path + str(f) + '.png' for f in range(21)]
b_wolf = [b_w_path + str(b) + '.png' for b in range(21)]
r_wolf = [r_w_path + str(r) + '.png' for r in range(12)]
l_wolf = [l_w_path + str(l) + '.png' for l in range(12)]


def collide_with_walls(sprite, group, dir):
    if dir == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            if sprite.vx > 0:
                sprite.x = hits[0].rect.left - sprite.rect.width
            if sprite.vx < 0:
                sprite.x = hits[0].rect.right
            sprite.vx = 0
            sprite.rect.x = sprite.x
    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False)
        if hits:
            if sprite.vy > 0:
                sprite.y = hits[0].rect.top - sprite.rect.height
            if sprite.vy < 0:
                sprite.y = hits[0].rect.bottom
            sprite.vy = 0
            sprite.rect.y = sprite.y

def collide_with_door(sprite, group, dir):
    if sprite.door_key == False:
        if dir == 'x':
            hits = pg.sprite.spritecollide(sprite, group, False)
            if hits:
                if sprite.vx > 0:
                    sprite.x = hits[0].rect.left - sprite.rect.width
                if sprite.vx < 0:
                    sprite.x = hits[0].rect.right
                sprite.vx = 0
                sprite.rect.x = sprite.x
        if dir == 'y':
            hits = pg.sprite.spritecollide(sprite, group, False)
            if hits:
                if sprite.vy > 0:
                    sprite.y = hits[0].rect.top - sprite.rect.height
                if sprite.vy < 0:
                    sprite.y = hits[0].rect.bottom
                sprite.vy = 0
                sprite.rect.y = sprite.y

class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/1.6, TILESIZE/1.6))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/link_b0.png'), (TILESIZE/1.6, TILESIZE/1.6))
        self.rect = self.image.get_rect()
        self.hit_rect = self.image.get_rect()
        self.hit_rect.center = self.rect.center
        self.vx, self.vy = 0, 0
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.counter = 0
        self.last_shot = 0
        self.last_slash = 0
        self.last_hit = 0
        self.last_swap = 0
        self.dir = 'U'
        self.door_key = False
        self.wand = False
        self.wand_eq = False
        self.sword_eq = True
        self.health = PLAYER_HEALTH
        self.wand_count = 0

    def get_keys(self):
        self.vx, self.vy = 0, 0
        if self.counter > 16:
            self.counter = 0
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.image = pygame.transform.scale(pygame.image.load(l_images[self.counter]),
                                                (TILESIZE / 1.6, TILESIZE / 1.6))
            self.counter = (self.counter + 1) % len(l_images)
            self.vx = -PLAYER_SPEED
            self.dir = 'L'
        elif keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.image = pygame.transform.scale(pygame.image.load(r_images[self.counter]),
                                                (TILESIZE / 1.6, TILESIZE / 1.6))
            self.counter = (self.counter + 1) % len(r_images)
            self.vx = PLAYER_SPEED
            self.dir = 'R'
        elif keys[pg.K_DOWN] or keys[pg.K_s]:
            self.image = pygame.transform.scale(pygame.image.load(f_images[self.counter]),
                                                (TILESIZE / 1.6, TILESIZE / 1.6))
            self.counter = (self.counter + 1) % len(f_images)
            self.vy = PLAYER_SPEED
            self.dir = 'D'
        elif keys[pg.K_UP] or keys[pg.K_w]:
            self.image = pygame.transform.scale(pygame.image.load(b_images[self.counter]),
                                                (TILESIZE / 1.6, TILESIZE / 1.6))
            self.counter = (self.counter + 1) % len(b_images)
            self.vy = -PLAYER_SPEED
            self.dir = 'U'
        if keys[pg.K_x]:
            now = pg.time.get_ticks()
            if now - self.last_swap > SWAP_RATE:
                if self.wand == True:
                    if self.sword_eq == True:
                        self.sword_eq = False
                        self.wand_eq = True
                    else:
                        self.sword_eq = True
                        self.wand_eq = False
        elif keys[pg.K_SPACE]:
            now = pg.time.get_ticks()
            if self.sword_eq == True:
                if now - self.last_slash > SWORD_RATE:
                    self.last_slash = now
                    Sword(self.game, self.x, self.y, self.dir)
            elif self.wand_eq == True:
                if now - self.last_shot > ORB_RATE:
                    self.last_shot = now
                    Orb(self.game, self.x, self.y, self.dir)

    def collide_with_key(self):
        if self.door_key == False:
            hits = pg.sprite.spritecollide(self, self.game.keys_door, False)
            if hits:
                self.door_key = True

    # def collide_with_wand(self):
    #     if self.wand == False:
    #         hits = pg.sprite.spritecollide(self, self.game.wands, False)
    #         if hits:
    #             self.wand = True
    #             self.wand_count += 1

    def update(self):
        self.get_keys()
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        self.collide_with_key()
        # self.collide_with_wand()
        collide_with_door(self, self.game.doors, 'x')
        collide_with_walls(self, self.game.walls, 'x')
        self.rect.y = self.y
        collide_with_walls(self, self.game.walls, 'y')
        collide_with_door(self, self.game.doors, 'y')

class Sword(pg.sprite.Sprite):
    def __init__(self, game, x, y, dir):
        self.groups = game.all_sprites, game.swords
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/1.8, TILESIZE/1.8))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/swordu.png'), (TILESIZE/1.8, TILESIZE/1.8))
        self.rect = self.image.get_rect()
        self.spawn_time = pg.time.get_ticks()
        self.vx, self.vy = 0, 0
        self.x = x
        self.y = y
        if dir == 'U':
            self.y = y - ((TILESIZE/1.8))
        elif dir == 'D':
            self.y = y + ((TILESIZE/1.8))
            self.image = pg.transform.scale(pg.image.load('./pixel_art/swordd.png'), (TILESIZE / 1.8, TILESIZE / 1.8))
        elif dir == 'R':
            self.x = x + ((TILESIZE/1.8))
            self.image = pg.transform.scale(pg.image.load('./pixel_art/sword.png'), (TILESIZE / 1.8, TILESIZE / 1.8))
        elif dir == 'L':
            self.x = x - ((TILESIZE/1.8))
            self.image = pg.transform.scale(pg.image.load('./pixel_art/swordl.png'), (TILESIZE / 1.8, TILESIZE / 1.8))
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

    def update(self):
        # self.x += self.vx * self.game.dt
        # self.y += self.vy * self.game.dt
        self.rect.x = self.x
        self.rect.y = self.y
        if pg.sprite.spritecollideany(self, self.game.walls):
            self.kill()
        if pg.time.get_ticks() - self.spawn_time > SWORD_LIFETIME:
            self.kill()

class Wand(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.wands
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/2.5, TILESIZE/2.5))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/wand.png'), (TILESIZE/2.5, TILESIZE/2.5))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE
        self.health = 1

    def update(self):
        if self.health <= 0:
            self.kill()

class Key_Door(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.keys_door
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/2.5, TILESIZE/2.5))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/key.png'), (TILESIZE/2.5, TILESIZE/2.5))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

    def update(self):
        if self.game.player.door_key == True:
            self.kill()

class Orb(pg.sprite.Sprite):
    def __init__(self, game, x, y, dir):
        self.groups = game.all_sprites, game.orbs
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/2, TILESIZE/2))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/orb.png'), (TILESIZE/2, TILESIZE/2))
        self.rect = self.image.get_rect()
        self.spawn_time = pg.time.get_ticks()
        self.vx, self.vy = 0, 0
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE
        if dir == 'U':
            self.vy = -ORB_SPEED
        elif dir == 'D':
            self.vy = ORB_SPEED
        elif dir == 'R':
            self.vx = ORB_SPEED
        elif dir == 'L':
            self.vx = -ORB_SPEED

    def update(self):
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        self.rect.y = self.y
        if pg.sprite.spritecollideany(self, self.game.walls):
            self.kill()
        if pg.time.get_ticks() - self.spawn_time > ORB_LIFETIME:
            self.kill()

class Door(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.doors
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/closed.png'), (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

    def update(self):
        if self.game.player.door_key == True:
            self.image = pg.transform.scale(pg.image.load('./pixel_art/open.png'), (TILESIZE, TILESIZE))

class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/wall.png'), (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.vx, self.vy = 0, 0
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Stone(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.stones
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/bricks.png'), (TILESIZE, TILESIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Enemy(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.enemies
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/0.95, TILESIZE/0.95))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/wolf_b0.png'), (TILESIZE/0.95, TILESIZE/0.95))
        self.rect = self.image.get_rect()
        self.hit_rect = self.image.get_rect()
        self.hit_rect_center = self.rect.center
        self.vx, self.vy = 0, 0
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.counter = 0
        self.playerx = self.game.player.x
        self.playery = self.game.player.y
        self.health = ENEMY_HEALTH

    def move(self):
        self.playerx = self.game.player.x
        self.playery = self.game.player.y
        self.vx, self.vy = 0, 0
        if self.counter > 20:
            self.counter = 0
        if self.playerx < self.x:
            distance_x = self.x - self.playerx
            if self.playery > self.y:
                distance_y = self.playery - self.y
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(l_wolf[self.counter]),
                                                        (TILESIZE/0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(l_wolf)
                    self.vx = -ENEMY_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(f_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(f_wolf)
                    self.vy = ENEMY_SPEED
            elif self.playery < self.y:
                distance_y = self.y - self.playery
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(l_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(l_wolf)
                    self.vx = -ENEMY_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(b_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(b_wolf)
                    self.vy = -ENEMY_SPEED
        elif self.playerx > self.x:
            distance_x = self.playerx - self.x
            if self.playery > self.y:
                distance_y = self.playery - self.y
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(r_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(r_wolf)
                    self.vx = ENEMY_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(f_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(f_wolf)
                    self.vy = ENEMY_SPEED
            elif self.playery < self.y:
                distance_y = self.y - self.playery
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(r_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(r_wolf)
                    self.vx = ENEMY_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(b_wolf[self.counter]),
                                                        (TILESIZE / 0.95, TILESIZE / 0.95))
                    self.counter = (self.counter + 1) % len(b_wolf)
                    self.vy = -ENEMY_SPEED

    def update(self):
        self.move()
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        collide_with_walls(self, self.game.walls, 'x')
        self.rect.y = self.y
        collide_with_walls(self, self.game.walls, 'y')
        if self.health <= 0:
            self.kill()

    def draw_health(self):
        if self.health > 20:
            col = GREEN
        elif self.health > 10:
            col = YELLOW
        else:
            col = RED
        width = int(self.rect.width * self.health / ENEMY_HEALTH)
        self.health_bar = pg.Rect(0, 0, width, 7)
        if self.health < ENEMY_HEALTH:
            pg.draw.rect(self.image, col, self.health_bar)

class Range(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.ranged
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/2, TILESIZE/2))
        self.image = pg.transform.scale(pg.image.load('./pixel_art/wolf_b0.png'), (TILESIZE/2, TILESIZE/2))
        self.rect = self.image.get_rect()
        self.hit_rect = self.image.get_rect()
        self.hit_rect_center = self.rect.center
        self.vx, self.vy = 0, 0
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.counter = 0
        self.playerx = self.game.player.x
        self.playery = self.game.player.y
        self.health = ENEMY_HEALTH

    def move(self):
        self.playerx = self.game.player.x
        self.playery = self.game.player.y
        self.vx, self.vy = 0, 0
        if self.counter > 20:
            self.counter = 0
        if self.playerx < self.x:
            distance_x = self.x - self.playerx
            if self.playery > self.y:
                distance_y = self.playery - self.y
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(l_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(l_wolf)
                    self.vx = -RANGED_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(f_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(f_wolf)
                    self.vy = RANGED_SPEED
            elif self.playery < self.y:
                distance_y = self.y - self.playery
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(l_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(l_wolf)
                    self.vx = -RANGED_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(b_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(b_wolf)
                    self.vy = -RANGED_SPEED
        elif self.playerx > self.x:
            distance_x = self.playerx - self.x
            if self.playery > self.y:
                distance_y = self.playery - self.y
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(r_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(r_wolf)
                    self.vx = RANGED_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(f_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(f_wolf)
                    self.vy = RANGED_SPEED
            elif self.playery < self.y:
                distance_y = self.y - self.playery
                if distance_x > distance_y:
                    if self.counter > 11:
                        self.counter = 0
                    self.image = pygame.transform.scale(pygame.image.load(r_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(r_wolf)
                    self.vx = RANGED_SPEED
                else:
                    self.image = pygame.transform.scale(pygame.image.load(b_wolf[self.counter]), (TILESIZE/2, TILESIZE/2))
                    self.counter = (self.counter + 1) % len(b_wolf)
                    self.vy = -RANGED_SPEED

    def update(self):
        self.move()
        self.x += self.vx * self.game.dt
        self.y += self.vy * self.game.dt
        self.rect.x = self.x
        collide_with_walls(self, self.game.walls, 'x')
        self.rect.y = self.y
        collide_with_walls(self, self.game.walls, 'y')
        if self.health <= 0:
            self.kill()

    def draw_health(self):
        if self.health > 20:
            col = GREEN
        elif self.health > 10:
            col = YELLOW
        else:
            col = RED
        width = int(self.rect.width * self.health / ENEMY_HEALTH)
        self.health_bar = pg.Rect(0, 0, width, 7)
        if self.health < ENEMY_HEALTH:
            pg.draw.rect(self.image, col, self.health_bar)