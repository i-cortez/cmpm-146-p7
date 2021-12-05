# graph.py
# By: Ismael Cortez, Carl Vincent Cuyos, Nelson Norman, Kaixin Yu
# Adapted from: James Spencer <jamessp [at] gmail.com>.
# and Gaming AI P5
# A simple python dungeon generator by James Spencer
#
# To the extent possible under law, the person who associated CC0 with
# pathfinder.py has waived all copyright and related or neighboring rights
# to pathfinder.py.

# You should have received a copy of the CC0 legalcode along with this
# work. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#
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
                   'player': 'P',
                   'weapon': 'W'
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

class Generator(object):
    __slots__ = ["genome", "_fitness", "room_list", "corridor_list"]

    def __init__(self, room_list):
        self.room_list = copy.deepcopy(room_list)
        self.genome = []
        self.corridor_list = []
        
        self._fitness = None

    def calculate_fitness(self):
        if self.genome != []:
            measurements = metrics.metrics(self.to_level(), self.room_list)
            # Print out the possible measurements or look at the implementation of metrics.py for other keys:
            # print(measurements.keys())
            # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
            # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.

            # difficulty curve
            coefficients = dict(
                freeSpace=0.6,
                leniency=0.5,
                freePercentage=0.6,
                decorationPercentage = 0.5,
                roomCount = 1,
                legalPieces = 5
            )
            self._fitness = sum(map(lambda m: coefficients[m] * measurements[m], coefficients))
        else:
            self._fitness = 0
        return self
    
    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        # this is the heuristic
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness
    
    ############################################################################
    # MUTATE
    def mutate(self, room_list):
        global HEIGHT, WIDTH
        self.corridor_list = []
        genome = []
        weapon_count = 0
        MAX_WEAPON_COUNT = 3
        weapon_positions = [()]
        for i in range(HEIGHT):
            genome.append([TILES['stone']] * WIDTH)

        max_iters = random.randint(0, 2)

        for a in range(max_iters):
            if len(room_list) >= MAX_ROOMS:
                break

            tmp_room = self.gen_room()

            if room_list == []:
                room_list.append(tmp_room)
            else:
                tmp_room = self.gen_room()
                tmp_room_list = room_list[:]

                if self.room_overlapping(tmp_room, tmp_room_list) is False:
                    room_list.append(tmp_room)
        
        # connect the rooms
        for a in range(len(room_list) - 1):
            self.join_rooms(room_list[a][0], room_list[a + 1][0])

        # do the random joins
        for a in range(RANDOM_CONNECTIONS):
            if len(room_list) > 1:
                room_1 = room_list[random.randint(0, len(room_list) - 1)][0]
                room_2 = room_list[random.randint(0, len(room_list) - 1)][0]
                self.join_rooms(room_1, room_2)

        # do the spurs
        for a in range(RANDOM_SPURS):
            if len(room_list) > 1:
                room_1 = [random.randint(2, WIDTH - 2), random.randint(2, HEIGHT - 2), 1, 1]
                room_2 = room_list[random.randint(0, len(room_list) - 1)][0]
                self.join_rooms(room_1, room_2)

        # fill the map, paint rooms
        for room_num, room in enumerate(room_list):
            for b in range(room[0][2]):
                for c in range(room[0][3]):
                    genome[room[0][1] + c][room[0][0] + b] = TILES['floor']

        # paint corridors
        corridor_list = self.corridor_list
        for corridor in corridor_list:
            x1, y1 = corridor[0]
            x2, y2 = corridor[1]
            for width in range(abs(x1 - x2) + 1):
                for height in range(abs(y1 - y2) + 1):
                    genome[min(y1, y2) + height][
                        min(x1, x2) + width] = TILES['floor']

            if len(corridor) == 3:
                x3, y3 = corridor[2]

                for width in range(abs(x2 - x3) + 1):
                    for height in range(abs(y2 - y3) + 1):
                        genome[min(y2, y3) + height][
                            min(x2, x3) + width] = TILES['floor']

        # paint the walls
        for row in range(1, HEIGHT - 1):
            for col in range(1, WIDTH - 1):
                if genome[row][col] == TILES['floor']:
                    if genome[row - 1][col - 1] == TILES['stone']:
                        genome[row - 1][col - 1] = TILES['wall']

                    if genome[row - 1][col] == TILES['stone']:
                        genome[row - 1][col] = TILES['wall']

                    if genome[row - 1][col + 1] == TILES['stone']:
                        genome[row - 1][col + 1] = TILES['wall']

                    if genome[row][col - 1] == TILES['stone']:
                        genome[row][col - 1] = TILES['wall']

                    if genome[row][col + 1] == TILES['stone']:
                        genome[row][col + 1] = TILES['wall']

                    if genome[row + 1][col - 1] == TILES['stone']:
                        genome[row + 1][col - 1] = TILES['wall']

                    if genome[row + 1][col] == TILES['stone']:
                        genome[row + 1][col] = TILES['wall']

                    if genome[row + 1][col + 1] == TILES['stone']:
                        genome[row + 1][col + 1] = TILES['wall']

        # mutate the boss room to meet certain conditions
        for room in room_list:
            x = room[0][0]
            y = room[0][1]
            w = room[0][2]
            h = room[0][3]
            row_start = y - 1
            row_end = y + h
            col_start = x - 1
            col_end = x + w
            
            if 'B' in room[1]:
                # make sure all corners of room are a wall tile
                if genome[row_start][col_start] != TILES['wall']:
                    genome[row_start][col_start] == TILES['wall']
                if genome[row_start][col_end] != TILES['wall']:
                    genome[row_start][col_end] == TILES['wall']
                if genome[row_end][col_start] != TILES['wall']:
                    genome[row_end][col_start] == TILES['wall']
                if genome[row_end][col_end] != TILES['wall']:
                    genome[row_end][col_end] == TILES['wall']
                
                # make sure boundary rows have the appropriate number of walls
                for x in range(col_start + 1, col_end, 1):
                    if genome[row_start][x] == TILES['floor']:
                        if genome[row_start][x - 1] == TILES['wall'] and genome[row_start][x + 1] == TILES['wall']:
                            continue
                        elif genome[row_start][x - 1] == TILES['wall'] and genome[row_start][x + 1] != TILES['wall']:
                            genome[row_start][x + 1] = TILES['wall']
                        else:
                            genome[row_start][x - 1] = TILES['wall']
                for x in range(col_start + 1, col_end, 1):
                    if genome[row_end][x] == TILES['floor']:
                        if genome[row_end][x - 1] == TILES['wall'] and genome[row_end][x + 1] == TILES['wall']:
                            continue
                        elif genome[row_end][x - 1] == TILES['wall'] and genome[row_end][x + 1] != TILES['wall']:
                            genome[row_end][x + 1] = TILES['wall']
                        else:
                            genome[row_end][x - 1] = TILES['wall']
                
                # make sure boundary columns have the appropriate number of walls
                for y in range(row_start + 1, row_end, 1):
                    if genome[y][col_start] == TILES['floor']:
                        if genome[y - 1][col_start] == TILES['wall'] and genome[y + 1][col_start] == TILES['wall']:
                            continue
                        elif genome[y - 1][col_start] == TILES['wall'] and genome[y + 1][col_start] != TILES['wall']:
                            genome[y + 1][col_start] = TILES['wall']
                        else:
                            genome[y - 1][col_start] != TILES['wall']
                for y in range(row_start + 1, row_end, 1):
                    if genome[y][col_end] == TILES['floor']:
                        if genome[y - 1][col_end] == TILES['wall'] and genome[y + 1][col_end] == TILES['wall']:
                            continue
                        elif genome[y - 1][col_end] == TILES['wall'] and genome[y + 1][col_end] != TILES['wall']:
                            genome[y + 1][col_end] = TILES['wall']
                        else:
                            genome[y - 1][col_end] != TILES['wall']

        # place doors on boss room, weapons in rooms with enemies
        for room in room_list:
            x = room[0][0]
            y = room[0][1]
            w = room[0][2]
            h = room[0][3]
            row_start = y - 1
            row_end = y + h
            col_start = x - 1
            col_end = x + w

            if 'B' in room[1]:
                for y in range(row_start, row_end, 1):
                    if genome[y][col_start] == TILES['floor']:
                        genome[y][col_start] = TILES['door']
                    if genome[y][col_end] == TILES['floor']:
                        genome[y][col_end] = TILES['door']
                for x in range(col_start, col_end, 1):
                    if genome[row_start][x] == TILES['floor']:
                        genome[row_start][x] = TILES['door']
                    if genome[row_end][x] == TILES['floor']:
                        genome[row_end][x] = TILES['door']
            
            if ('E' in room[1] or 'R' in room[1]) and (weapon_count < MAX_WEAPON_COUNT):
                weapon_positions.append((y, x))
                weapon_positions.append((row_end - 1, x))
                weapon_positions.append((y, col_end - 1))
                weapon_positions.append((row_end - 1, col_end - 1))
                pos = ()
                while pos == ():
                    pos = random.choice(weapon_positions)
                if genome[pos[0]][pos[1]] == TILES['floor']:
                    genome[pos[0]][pos[1]] = 'W'
                    weapon_count += 1

        for room_nums, rooms in enumerate(room_list):
            genome[rooms[1][1]][rooms[1][0]] = rooms[1][2]

        self.genome = genome

        return room_list

    def generate_children(self, other):
        new_room_list = copy.deepcopy(self.room_list)

        if len(new_room_list) > 1 and len(other.room_list) > 1:
            split = random.randint(1, len(new_room_list)-1)
            i = split
            while i < len(self.room_list):
                cur_room = new_room_list[random.randint(0, len(new_room_list)-1)]
                if 'P' in cur_room[1] or 'B' in cur_room[1] or 'K' in cur_room[1]:
                    i += 1
                    continue
                else:
                    del new_room_list[random.randint(0, len(new_room_list)-1)]
                    i += 1
            i = split
            while i < len(other.room_list):
                cur_room = other.room_list[random.randint(0, len(other.room_list) - 1)]
                if 'P' in cur_room[1] or 'B' in cur_room[1] or 'K' in cur_room[1]:
                    i += 1
                    continue
                else:
                    del other.room_list[random.randint(0, len(other.room_list) - 1)]
                    i += 1
            chance = random.random()
            if chance > .5:
                for temp in other.room_list:
                    if self.room_overlapping(temp, new_room_list) == False:
                        new_room_list.append(temp)
            else:
                for temp in new_room_list:
                    if self.room_overlapping(temp, other.room_list) == False:
                        other.room_list.append(temp)
                new_room_list = other.room_list
        else:
            if len(other.room_list) > 0:
                for temp in other.room_list:
                    if self.room_overlapping(temp, new_room_list) == False:
                        new_room_list.append(temp)
                # new_room_list.append(other.room_list[0])
        # do mutation
        return Generator(self.mutate(new_room_list))

    def to_level(self):
        return self.genome

    @classmethod
    def empty_dungeon(cls):
        # build an empty dungeon, blank the room and corridor lists
        # g = [['stone' for col in range(WIDTH)] for row in range(HEIGHT)]
        r = []
        return cls(r)


    def gen_room(self):
        x, y, w, h, xx, yy = 0, 0, 0, 0, 0, 0
        tile = TILES['floor']

        w = random.randint(MIN_ROOM_XY, MAX_ROOM_XY)
        h = random.randint(MIN_ROOM_XY, MAX_ROOM_XY)
        x = random.randint(1, (WIDTH - w - 1))
        y = random.randint(1, (HEIGHT - h - 1))
        xx = random.randint(x, (x + w - 1))
        yy = random.randint(y, (y + h - 1))
        tile = random.choice([TILES['player'], TILES['boss'], TILES['item'], TILES['enemy'], TILES['ranged'], TILES['key'], TILES['trap']])

        return [[x, y, w, h], [xx, yy, tile]]

    def room_overlapping(self, room, room_list):

        x = room[0][0]
        y = room[0][1]
        w = room[0][2]
        h = room[0][3]

        #print("x: ", x, "y: ", y, "w: ", w, "h: ", h)
        #print("room list: ", room_list)

        for current_room in room_list:
            #print("current room: ", current_room)
            # The rectangles don't overlap if
            # one rectangle's minimum in some dimension
            # is greater than the other's maximum in
            # that dimension.
            if (x < (current_room[0][0] + current_room[0][2]) and current_room[0][0] < (x + w + 1) and y < (current_room[0][1] + current_room[0][3]) and current_room[0][1] < (y + h + 1)):
                #print("x: ", x, "y: ", y, "w: ", w, "h: ", h)
                #print("room list: ", room_list)
                #print("current room: ", current_room)
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
            if join_type == 'either' and set([0, 1]).intersection(
                 set([x1, x2, y1, y2])):

                join = 'bottom'
            elif join_type == 'either' and set([WIDTH - 1, WIDTH - 2]).intersection(set([x1, x2])) or set([HEIGHT - 1, HEIGHT - 2]).intersection(set([y1, y2])):
                join = 'top'
            elif join_type == 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join == 'top':
                return [(x1, y1), (x1, y2), (x2, y2)]
            elif join == 'bottom':
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
            if join_type == 'either':
                join = random.choice(['top', 'bottom'])
            else:
                join = join_type

            if join == 'top':
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

            elif join == 'bottom':
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

def generate_successors(population):
    results = []

    best_fit = sorted(population, key=lambda x: x.fitness(), reverse=True)

    # # ----- Elitism Selection ------
    # elitism_percentage = 0.01
    # elitism_size = max(1, int(len(best_fit) * elitism_percentage))
    # elitism_selection = best_fit[:elitism_size]
    #
    # print("== Elitism {} getting {}".format(len(population), elitism_size))
    #
    # results += elitism_selection

    # ----- Steady State Selection ------
    steady_state_percentage = 0.25
    steady_state_size = max(1, int(len(best_fit) * steady_state_percentage))
    print("== steady state {} getting {}".format(len(population), steady_state_size))

    steady_state_high = best_fit[:steady_state_size]
    steady_state_low = best_fit[-steady_state_size:]

    # remove low percentage
    steady_state_results = list(set(best_fit) - set(steady_state_low))

    for i in steady_state_high:
        steady_state_results.append(i.generate_children(random.choice(steady_state_high)))

    results += steady_state_results

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
                    # Generator.gen_tiles_level()
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
    # for k in range(0, 10):
    #     with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
    #         for row in final_gen[k].to_level():
    #             f.write("".join(row) + "\n")


