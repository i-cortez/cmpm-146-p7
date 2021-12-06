# CMPM 146 Final Project - Dungeon Crawler Procedural Generation Through Genetic Algorithm
## Team
Nelson Norman, Kaixin Yu, Carl Cuyos, Ismael Cortez
## Project Overview  
A genetic algorithm-based 2D top-down Dungeon Generator that focuses on creating beatable levels for developer reference. It will arrange opponents, a boss, a key, doors, traps, and objects in each level according to constraints inside a txt file that can be runned using PyGame for gameplay.
## Theme  
AI acts as a Level Design Assistant.
## Problem Statement
Developing unique and interesting levels, finding interesting mechanics, and gameplay based on the design elements takes time. Our team created an AI to assist developers through level generation by altering its layout based on the given design elements and configurable constraints.
## Technical Solution
Our objective is to simulate a method of procedural generation through the use of genetic algorithms based on the set design elements and constraints. The use of genetic algorithms allows us to obtain a variety of levels based on a given genome, represented as a sequence of symbols in a text file.
### Usage
1. In the `src/` directory, run `python dungeon.py`
2. Let the program run for a moment (~30 sec)
3. In the parent directory of `src/` look for the `levels/` directory.
4. Copy the file `last.txt` into `src/game/`.
5. In the `src/game/` directory run `python main.py`.
6. A pop up window should open with the playable level.
### How to Play
- Movement: W, A, S, D or Arrow Keys
- Attack: Space Bar
- Switch Weapons (after acquiring second weapon): X
- 
