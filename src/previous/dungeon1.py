# graph.py
# By: Ismael Cortez, Carl Vincent Cuyos, Nelson Norman, Kaixin Yu
# Adapted from: James Spencer <jamessp [at] gmail.com>.
#
# A simple python dungeon generator by James Spencer
#
# To the extent possible under law, the person who associated CC0 with
# pathfinder.py has waived all copyright and related or neighboring rights
# to pathfinder.py.

# You should have received a copy of the CC0 legalcode along with this
# work. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.

from __future__ import print_function
import copy
import heapq
import metrics
import multiprocessing.pool as mpool
import os
import random
import shutil
import time
import math

CHARACTER_TILES = {'stone': '*',
                   'floor': '.',
                   'wall': '#',
                   'boss': 'B',
                   'item': 'M',
                   'enemy': 'E',
                   'ranged': 'R',
                   'trap': 'T',
                   'door': '/',
                   'key': 'K',
                   'player': 'P'
                   }

WIDTH = 64
HEIGHT = 64
MAX_ROOMS = 15
MIN_ROOM_XY = 5
MAX_ROOM_XY = 15
ROOMS_OVERLAP = False
RANDOM_CONNECTIONS = 1
RANDOM_SPURS = 3
TILES = CHARACTER_TILES

class Generator():
    __slots__ = ["genome", "_fitness"]

    def __init__(self, genome):
        self.level = []
        self.genome = []
        # self.genome = copy.deepcopy(genome)
        self.corridor_list = []
        self.tiles_level = []
        
        self._fitness = None

    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Print out the possible measurements or look at the implementation of metrics.py for other keys:
        # print(measurements.keys())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.

        # difficulty curve
        coefficients = dict(
            negativeSpace=0.6,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-0.5, # possibly remove
            solvability=2.0
        )

        # for y in
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients))
        return self
    
    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        # this is the heuristic
        if self._fitness is None:
            # self.calculate_fitness()
            self._fitness = 1
        return self._fitness

    @classmethod
    def empty_dungeon(cls):
        # build an empty dungeon, blank the room and corridor lists
        #g = [['floor' for col in range(WIDTH)] for row in range(HEIGHT)]
        g = []
        return cls(g)
    
    def gen_room(self):
        x, y, w, h, xx, yy = 0, 0, 0, 0, 0, 0
        tile = 'floor'

        w = random.randint(MIN_ROOM_XY, MAX_ROOM_XY)
        h = random.randint(MIN_ROOM_XY, MAX_ROOM_XY)
        x = random.randint(1, (WIDTH - w - 1))
        y = random.randint(1, (HEIGHT - h - 1))
        xx = random.randint(x, (x + w - 1))
        yy = random.randint(y, (y + h - 1))
        # tile = random.choice(self.tiles)
        tile = random.choice(['floor', 'item', 'enemy', 'ranged', 'key', 'trap'])

        return [[x, y, w, h], [xx, yy, tile]]

    def room_overlapping(self, room, room_list):

        x = room[0][0]
        y = room[0][1]
        w = room[0][2]
        h = room[0][3]

        for current_room in room_list:

            # The rectangles don't overlap if
            # one rectangle's minimum in some dimension
            # is greater than the other's maximum in
            # that dimension.
            if (x < (current_room[0][0] + current_room[0][2]) and
                current_room[0][0] < (x + w) and
                y < (current_room[0][1] + current_room[0][3]) and
                current_room[0][1] < (y + h)):

                return True

        return False


    def corridor_between_points(self, x1, y1, x2, y2, join_type='either'):
        if x1 == x2 and y1 == y2 or x1 == x2 or y1 == y2:
            return [(x1, y1), (x2, y2)]
        else:
            # 2 Corridors
            # NOTE: Never randomly choose a join that will go out of bounds
            # when the walls are added.
            join = None
            if join_type is 'either' and set([0, 1]).intersection(
                 set([x1, x2, y1, y2])):

                join = 'bottom'
            elif join_type is 'either' and set([WIDTH - 1,
                 WIDTH - 2]).intersection(set([x1, x2])) or set(
                 [HEIGHT - 1, HEIGHT - 2]).intersection(
                 set([y1, y2])):

                join = 'top'
            elif join_type is 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join is 'top':
                return [(x1, y1), (x1, y2), (x2, y2)]
            elif join is 'bottom':
                return [(x1, y1), (x2, y1), (x2, y2)]

    def join_rooms(self, room_1, room_2, join_type='either'):
        # sort by the value of x
        sorted_room = [room_1, room_2]
        sorted_room.sort(key=lambda x_y: x_y[0])

        x1 = sorted_room[0][0]
        y1 = sorted_room[0][1]
        w1 = sorted_room[0][2]
        h1 = sorted_room[0][3]
        x1_2 = x1 + w1 - 1
        y1_2 = y1 + h1 - 1

        x2 = sorted_room[1][0]
        y2 = sorted_room[1][1]
        w2 = sorted_room[1][2]
        h2 = sorted_room[1][3]
        x2_2 = x2 + w2 - 1
        y2_2 = y2 + h2 - 1

        # overlapping on x
        if x1 < (x2 + w2) and x2 < (x1 + w1):
            jx1 = random.randint(x2, x1_2)
            jx2 = jx1
            tmp_y = [y1, y2, y1_2, y2_2]
            tmp_y.sort()
            jy1 = tmp_y[1] + 1
            jy2 = tmp_y[2] - 1

            corridors = self.corridor_between_points(jx1, jy1, jx2, jy2)
            self.corridor_list.append(corridors)

        # overlapping on y
        elif y1 < (y2 + h2) and y2 < (y1 + h1):
            if y2 > y1:
                jy1 = random.randint(y2, y1_2)
                jy2 = jy1
            else:
                jy1 = random.randint(y1, y2_2)
                jy2 = jy1
            tmp_x = [x1, x2, x1_2, x2_2]
            tmp_x.sort()
            jx1 = tmp_x[1] + 1
            jx2 = tmp_x[2] - 1

            corridors = self.corridor_between_points(jx1, jy1, jx2, jy2)
            self.corridor_list.append(corridors)

        # no overlap
        else:
            join = None
            if join_type is 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join is 'top':
                if y2 > y1:
                    jx1 = x1_2 + 1
                    jy1 = random.randint(y1, y1_2)
                    jx2 = random.randint(x2, x2_2)
                    jy2 = y2 - 1
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'bottom')
                    self.corridor_list.append(corridors)
                else:
                    jx1 = random.randint(x1, x1_2)
                    jy1 = y1 - 1
                    jx2 = x2 - 1
                    jy2 = random.randint(y2, y2_2)
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'top')
                    self.corridor_list.append(corridors)

            elif join is 'bottom':
                if y2 > y1:
                    jx1 = random.randint(x1, x1_2)
                    jy1 = y1_2 + 1
                    jx2 = x2 - 1
                    jy2 = random.randint(y2, y2_2)
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'top')
                    self.corridor_list.append(corridors)
                else:
                    jx1 = x1_2 + 1
                    jy1 = random.randint(y1, y1_2)
                    jx2 = random.randint(x2, x2_2)
                    jy2 = y2_2 + 1
                    corridors = self.corridor_between_points(
                        jx1, jy1, jx2, jy2, 'bottom')
                    self.corridor_list.append(corridors)

    def gen_level(self):
        global HEIGHT, WIDTH
        # build an empty dungeon, blank the room and corridor lists
        for i in range(HEIGHT):
            self.level.append(['stone'] * WIDTH)
        self.genome = []
        self.corridor_list = []

        max_iters = MAX_ROOMS * 5

        for a in range(max_iters):
            tmp_room = self.gen_room()

            if ROOMS_OVERLAP or not self.genome:
                self.genome.append(tmp_room)
            else:
                tmp_room = self.gen_room()
                tmp_room_list = self.genome[:]

                if self.room_overlapping(tmp_room, tmp_room_list) is False:
                    self.genome.append(tmp_room)

            if len(self.genome) >= MAX_ROOMS:
                break

        # connect the rooms
        for a in range(len(self.genome) - 1):
            self.join_rooms(self.genome[a][0], self.genome[a + 1][0])

        # do the random joins
        for a in range(RANDOM_CONNECTIONS):
            room_1 = self.genome[random.randint(0, len(self.genome) - 1)][0]
            room_2 = self.genome[random.randint(0, len(self.genome) - 1)][0]
            self.join_rooms(room_1, room_2)

        # do the spurs
        for a in range(RANDOM_SPURS):
            room_1 = [random.randint(2, WIDTH - 2), random.randint(
                     2, HEIGHT - 2), 1, 1]
            room_2 = self.genome[random.randint(0, len(self.genome) - 1)][0]
            self.join_rooms(room_1, room_2)

        # fill the map
        # paint rooms
        for room_num, room in enumerate(self.genome):
            for b in range(room[0][2]):
                for c in range(room[0][3]):
                    self.level[room[0][1] + c][room[0][0] + b] = 'floor'

        # paint corridors
        for corridor in self.corridor_list:
            x1, y1 = corridor[0]
            x2, y2 = corridor[1]
            for WIDTH in range(abs(x1 - x2) + 1):
                for HEIGHT in range(abs(y1 - y2) + 1):
                    self.level[min(y1, y2) + HEIGHT][
                        min(x1, x2) + WIDTH] = 'floor'

            if len(corridor) == 3:
                x3, y3 = corridor[2]

                for WIDTH in range(abs(x2 - x3) + 1):
                    for HEIGHT in range(abs(y2 - y3) + 1):
                        self.level[min(y2, y3) + HEIGHT][
                            min(x2, x3) + WIDTH] = 'floor'

        # paint the walls
        for row in range(1, HEIGHT - 1):
            for col in range(1, WIDTH - 1):
                if self.level[row][col] == 'floor':
                    if self.level[row - 1][col - 1] == 'stone':
                        self.level[row - 1][col - 1] = 'wall'

                    if self.level[row - 1][col] == 'stone':
                        self.level[row - 1][col] = 'wall'

                    if self.level[row - 1][col + 1] == 'stone':
                        self.level[row - 1][col + 1] = 'wall'

                    if self.level[row][col - 1] == 'stone':
                        self.level[row][col - 1] = 'wall'

                    if self.level[row][col + 1] == 'stone':
                        self.level[row][col + 1] = 'wall'

                    if self.level[row + 1][col - 1] == 'stone':
                        self.level[row + 1][col - 1] = 'wall'

                    if self.level[row + 1][col] == 'stone':
                        self.level[row + 1][col] = 'wall'

                    if self.level[row + 1][col + 1] == 'stone':
                        self.level[row + 1][col + 1] = 'wall'

        for room_nums, rooms in enumerate(self.genome):
            self.level[rooms[1][1]][rooms[1][0]] = rooms[1][2]

    def gen_tiles_level(self):

        for row_num, row in enumerate(self.level):
            tmp_tiles = []

            for col_num, col in enumerate(row):
                if col == 'stone':
                    tmp_tiles.append(TILES['stone'])
                if col == 'floor':
                    tmp_tiles.append(TILES['floor'])
                if col == 'wall':
                    tmp_tiles.append(TILES['wall'])
                if col == 'key':
                    tmp_tiles.append(TILES['key'])
                if col == 'enemy':
                    tmp_tiles.append(TILES['enemy'])
                if col == 'ranged':
                    tmp_tiles.append(TILES['ranged'])
                if col == 'boss':
                    tmp_tiles.append(TILES['boss'])
                if col == 'player':
                    tmp_tiles.append(TILES['player'])
                if col == 'trap':
                    tmp_tiles.append(TILES['trap'])
                if col == 'item':
                    tmp_tiles.append(TILES['item'])
                if col == 'door':
                    tmp_tiles.append(TILES['door'])

            self.tiles_level.append(''.join(tmp_tiles))

        print('Room List: ', self.genome)
        print('\nCorridor List: ', self.corridor_list)

        [print(row) for row in self.tiles_level]

def generate_successors(population):
    results= []
    # STUDENT Design and implement this
    # Hint: Call generate_children() on some individuals and fill up results.

    best_fit = sorted(population, key=lambda x: x.fitness(), reverse=True)

    # ----- Elitism Selection ------
    elitism_percentage = 0.01
    elitism_size = max(1, int(len(best_fit) * elitism_percentage))
    elitism_selection = best_fit[:elitism_size]

    print("== Elitism {} getting {}".format(len(population), elitism_size))

    results += elitism_selection
    results.sort(key=lambda x: x.fitness(), reverse=True)
    over_count = len(results) - 480
    if over_count > 0:
        print("== {} individuals over limit".format(over_count))
        results = results[:-over_count]

    return results

def dungeon():
    # STUDENT Feel free to play with this parameter
    pop_limit = 480
    # Code to parallelize some computations
    batches = os.cpu_count()
    if pop_limit % batches != 0:
        print("It's ideal if pop_limit divides evenly into " + str(batches) + " batches.")
    batch_size = int(math.ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time.time()
        # STUDENT (Optional) change population initialization - can get to better results quicker
        population = [Generator.empty_dungeon()
                      for _g in range(pop_limit)]
        # But leave this line alone; we have to reassign to population because we get a new population that has more cached stuff in it.
        population = pool.map(Generator.calculate_fitness,
                              population,
                              batch_size)
        init_done = time.time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")
        generation = 0
        start = time.time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")
        try:
            while True:
                now = time.time()
                # Print out statistics
                if generation > 0:
                    best = max(population, key=Generator.fitness)
                    print("Generation:", str(generation))
                    print("Max fitness:", str(best.fitness()))
                    print("Average generation time:", (now - start) / generation)
                    print("Net time:", now - start)
                    with open("../levels/last.txt", 'w') as f:
                        for row in best.to_level():
                            f.write("".join(row) + "\n")
                generation += 1
                # STUDENT Determine stopping condition - creates a folder called levels and puts the gen levels in folder
                stop_condition = False
                if stop_condition:
                    break
                # STUDENT Also consider using FI-2POP as in the Sorenson & Pasquier paper
                gentime = time.time()
                next_population = generate_successors(population)
                gendone = time.time()
                print("Generated successors in:", gendone - gentime, "seconds")
                # Calculate fitness in batches in parallel -  a good place to mod
                next_population = pool.map(Generator.calculate_fitness,
                                           next_population,
                                           batch_size)
                popdone = time.time()
                print("Calculated fitnesses in:", popdone - gendone, "seconds")
                population = next_population
        except KeyboardInterrupt:
            pass
    return population

if __name__ == '__main__':
    final_gen = sorted(dungeon(), key=Generator.fitness, reverse=True)
    best = final_gen[0]
    print("Best fitness: " + str(best.fitness()))
    now = time.strftime("%m_%d_%H_%M_%S")
    # STUDENT You can change this if you want to blast out the whole generation, or ten random samples, or...
    for k in range(0, 10):
        with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
            for row in final_gen[k].to_level():
                f.write("".join(row) + "\n")


    # gen = Generator(128)
    # gen.gen_level()
    # gen.gen_tiles_level()

