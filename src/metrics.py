import pathfinding
import numpy as np
import sys
from scipy import stats


def metrics(levelStr, roomList):
    maxY = len(levelStr)
    maxX = len(levelStr[0])
    rooms = len(roomList)

    visited = set()
    curX = 2
    curY = 0
    solids = set(['*', '.', '#', 'B', 'M', 'E', 'R', 'T', '/', 'K', 'P'])
    

    def isSolid(tile):
        return tile in solids
    for yy in range(maxY - 2, -1, -1):
        if (levelStr[yy][curX] == '-' or levelStr[yy][curX] == '*') and isSolid(levelStr[yy + 1][curX]):
            curY = yy
            break

    visited = set()

    totalSize = maxX * maxY
    enemies = 0
    key = 0
    floor = 0
    door = 0
    boss = 0
    stone = 0
    item = 0
    trap = 0
    player = 0
    for row in levelStr:
        enemies += row.count('E') + row.count('R')
        floor += row.count('.') + row.count('E') + row.count('M') + row.count('R') + row.count('T') + row.count('B') + row.count('/') + row.count('K')
        key += row.count('K')
        door += row.count('/')
        boss += row.count('B')
        item += row.count('M')
        stone += row.count('*') + row.count('#')
        trap += row.count('T')
        player += row.count('P')

    if floor != 0:
        freeSpace = float(len(visited)) / float(floor)
    else:
        freeSpace = 0
    if totalSize != 0: 
        freePercentage = float(floor) / float(totalSize)
        decorationPercentage = (float(item) + float(trap) + float(enemies)) / float(totalSize)
    else:
        freePercentage = 0
        decorationPercentage = 0
    leniency = enemies + trap * 0.5 - item * 0.5
    legalPieces = 0
    if player > 1 or boss > 1 or key > 1:
        legalPieces = -5
    elif player == 1 and boss == 1 and key == 1:
        legalPieces = 10
    elif player == 1 or boss == 1 or key == 1:
        legalPieces = 5
    roomCount = 0
    if rooms > 5:
        roomCount = rooms / 15
    
    solidX = []
    solidY = []
    yy = 0
    for yy in range(maxY):
        xx = 0
        if yy > 0:
            for c in levelStr[yy]:
                if isSolid(c) and not isSolid(levelStr[yy - 1][xx]):
                    solidX.append(xx)
                    solidY.append(yy)
                xx += 1
        yy += 1
    x = np.array(solidX)
    y = np.array(solidY)
    return {
            'length': maxX,
            'freeSpace': freeSpace,
            'freePercentage': freePercentage,
            'decorationPercentage': decorationPercentage,
            'leniency': leniency,
            'legalPieces': legalPieces,
            'roomCount': roomCount
            }

if __name__ == "__main__":
    name = sys.argv[1]
    with open(name, 'r') as openFile:
        lines = openFile.readlines()
    print(len(lines), len(lines[0]))
    print(metrics(lines))

