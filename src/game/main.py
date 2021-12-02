import pygame as pg
import sys
from os import path
from settings import *
from sprites import *
from tilemap import *

def draw_player_health(surf, x, y, pct):
    if pct < 0:
        pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 20
    fill = pct * BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    if pct > 0.6:
        col = GREEN
    elif pct > 0.3:
        col = YELLOW
    else:
        col = RED
    pg.draw.rect(surf, col, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.load_data()

    def load_data(self):
        game_folder = path.dirname(__file__)
        self.map = Map(path.join(game_folder, 'level_1.txt'))

    def new(self):
        # initialize all variables and do all the setup for a new game
        self.all_sprites = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.stones = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.ranged = pg.sprite.Group()
        self.keys_door = pg.sprite.Group()
        self.doors = pg.sprite.Group()
        self.orbs = pg.sprite.Group()
        self.webs = pg.sprite.Group()
        self.swords = pg.sprite.Group()
        self.wands = pg.sprite.Group()
        self.chests = pg.sprite.Group()
        self.bosses = pg.sprite.Group()
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '#':
                    Wall(self, col, row)
                if tile == 'M':
                    Chest(self, col, row)
                if tile == 'R':
                    Range(self, col, row)
                if tile == 'W':
                    Wand(self, col, row)
                if tile == '*':
                    Stone(self, col, row)
                if tile == '/':
                    Door(self, col, row)
                if tile == 'K':
                    Key_Door(self, col, row)
                if tile == 'E':
                    Enemy(self, col, row)
                if tile == 'B':
                    Boss(self, col, row)
                if tile == 'P':
                    self.player = Player(self, col, row)
        self.camera = Camera(self.map.width, self.map.height)

    def run(self):
        # game loop - set self.playing = False to end the game
        self.playing = True
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def quit(self):
        pg.quit()
        sys.exit()

    def update(self):
        # update portion of the game loop
        self.all_sprites.update()
        self.camera.update(self.player)
        #enemy hit player
        now = pg.time.get_ticks()
        if now - self.player.last_hit > DAMAGE_RATE:
            self.player.last_hit = now
            hits = pg.sprite.spritecollide(self.player, self.ranged, False)
            for hit in hits:
                self.player.health -= RANGED_DAMAGE
                if self.player.health <= 0:
                    self.playing = False
            hits = pg.sprite.spritecollide(self.player, self.enemies, False)
            for hit in hits:
                self.player.health -= ENEMY_DAMAGE
                if self.player.health <= 0:
                    self.playing = False
            hits = pg.sprite.spritecollide(self.player, self.bosses, False)
            for hit in hits:
                self.player.health -= BOSS_DAMAGE
                if self.player.health <= 0:
                    self.playing = False
            hits = pg.sprite.spritecollide(self.player, self.webs, False)
            for hit in hits:
                hit.kill()
                self.player.health -= BOSS_WEB_DAMAGE
                if self.player.health <= 0:
                    self.playing = False
        # orbs hit mobs
        hits = pg.sprite.groupcollide(self.ranged, self.orbs, False, True)
        for hit in hits:
            hit.health -= ORB_DAMAGE + (2 * self.player.wand_count) - 2
        hits = pg.sprite.groupcollide(self.bosses, self.orbs, False, True)
        for hit in hits:
            hit.health -= ORB_DAMAGE + (2 * self.player.wand_count) - 2
        hits = pg.sprite.groupcollide(self.enemies, self.orbs, False, True)
        for hit in hits:
            hit.health -= ORB_DAMAGE + (2 * self.player.wand_count) - 2
        hits = pg.sprite.groupcollide(self.enemies, self.swords, False, True)
        for hit in hits:
            hit.health -= SWORD_DAMAGE
            if self.player.dir == 'U':
                hit.y -= ENEMY_KNOCKBACK
            elif self.player.dir == 'D':
                hit.y += ENEMY_KNOCKBACK
            elif self.player.dir == 'R':
                hit.x += ENEMY_KNOCKBACK
            elif self.player.dir == 'L':
                hit.x -= ENEMY_KNOCKBACK
        hits = pg.sprite.groupcollide(self.ranged, self.swords, False, True)
        for hit in hits:
            hit.health -= SWORD_DAMAGE
            if self.player.dir == 'U':
                hit.y -= ENEMY_KNOCKBACK
            elif self.player.dir == 'D':
                hit.y += ENEMY_KNOCKBACK
            elif self.player.dir == 'R':
                hit.x += ENEMY_KNOCKBACK
            elif self.player.dir == 'L':
                hit.x -= ENEMY_KNOCKBACK
        hits = pg.sprite.groupcollide(self.bosses, self.swords, False, True)
        for hit in hits:
            hit.health -= SWORD_DAMAGE
            if self.player.dir == 'U':
                hit.y -= ENEMY_KNOCKBACK
            elif self.player.dir == 'D':
                hit.y += ENEMY_KNOCKBACK
            elif self.player.dir == 'R':
                hit.x += ENEMY_KNOCKBACK
            elif self.player.dir == 'L':
                hit.x -= ENEMY_KNOCKBACK
        hits = pg.sprite.spritecollide(self.player, self.wands, False)
        for hit in hits:
            self.player.wand_count += 1
            self.player.wand = True
            hit.health -= SWORD_DAMAGE

    def draw_grid(self):
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y), (WIDTH, y))

    def draw(self):
        pg.display.set_caption("{:.2f}".format(self.clock.get_fps()))
        self.screen.fill(BGCOLOR)
        # self.draw_grid()
        for sprite in self.all_sprites:
            if isinstance(sprite, Enemy):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if isinstance(sprite, Boss):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if isinstance(sprite, Range):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))
        draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
        pg.display.flip()

    def events(self):
        # catch all events here
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.quit()

    def show_start_screen(self):
        pass

    def show_go_screen(self):
        pass

# create the game object
g = Game()
g.show_start_screen()
while True:
    g.new()
    g.run()
    g.show_go_screen()