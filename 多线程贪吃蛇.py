import random, pygame, sys, threading
from pygame.locals import *


STEPS = ((1, 0), (0, 1), (-1, 0), (0, -1))

# Setting up constats
NUM_WORMS = 5  # the number of worms in the grid
FPS = 60        # frames per second that the program runs
CELLS_SIZE = 20  # how many pixels wide and high each "cell" in the grid is
CELLS_WIDE = 64  # how many cells wide the grid is
CELLS_HIGH = 36  # how many cells high the grid is

GRID = [[None for i in range(CELLS_HIGH)] for j in range(CELLS_WIDE)]

GRID_LOCK = threading.Lock() # pun was not intended

# Constants for some colors.
#   R   G   B
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGRAY = (40, 40, 40)
BGCOLOR = BLACK # color to use for the background of the grid
GRID_LINES_COLOR = DARKGRAY # color to use for the lines of the grid

# Calculate total pixels wide and high that the full window is
WINDOWWIDTH = CELLS_SIZE * CELLS_WIDE
WINDOWHEIGHT = CELLS_SIZE * CELLS_HIGH

HEAD = 0
BUTT = -1 # negative indexes count from the end, so -1 will always be the last index

# A global variable that the Worm threads check to see if they should exit.
WORMS_RUNNING = True

FOOD_EXIST = True
FOOD_LOCK = threading.Lock()
FOOD = (random.randint(0, CELLS_WIDE - 1), random.randint(0, CELLS_HIGH - 1))
GRID[FOOD[0]][FOOD[1]] = WHITE


class Worm(threading.Thread): # "Thread" is a class in the "threading" module.
    def __init__(self, name='Worm', maxsize=None, color=None, speed=None):
        threading.Thread.__init__(
            self) # since we are overriding the Thread class, we need to first call its __init__() method.

        self.name = name
        # Set the maxsize to the parameter, or to a random maxsize.
        if maxsize is None:
            self.maxsize = random.randint(4, 10)

            # Have a small chance of a super long worm.
            if random.randint(0, 4) == 0:
                self.maxsize += random.randint(10, 20)
        else:
            self.maxsize = maxsize

        # Set the color to the parameter, or to a random color.
        if color is None:
            self.color = (random.randint(60, 255), random.randint(60, 255), random.randint(60, 255))
        else:
            self.color = color

        # Set the speed to the parameter, or to a random number.
        if speed is None:
            self.speed = random.randint(20, 500) # wait time before movements will be between 0.02 and 0.5 seconds
        else:
            self.speed = speed

        GRID_LOCK.acquire() # block until this thread can acquire the lock

        while True:
            startx = random.randint(0, CELLS_WIDE - 1)
            starty = random.randint(0, CELLS_HIGH - 1)
            if GRID[startx][starty] is None:
                break # we've found an unoccupied cell in the grid

        GRID[startx][starty] = self.color # modify the shared data structure

        GRID_LOCK.release()

        self.body = [{'x': startx, 'y': starty}]

    def run(self):
        while True:
            if not WORMS_RUNNING:
                return # A thread terminates when run() returns.

            FOOD_LOCK.acquire()
            GRID_LOCK.acquire()
            global FOOD_EXIST
            global FOOD
            if not FOOD_EXIST:
                x = random.randint(0, CELLS_WIDE - 1)
                y = random.randint(0, CELLS_HIGH - 1)
                while GRID[x][y] is not None:
                    x = random.randint(0, CELLS_WIDE - 1)
                    y = random.randint(0, CELLS_HIGH - 1)

                FOOD = (x, y)
                FOOD_EXIST = True
                GRID[x][y] = WHITE

            theNextPosition = self.getNextPosition()
            if theNextPosition is None:
                for item in self.body:
                    GRID[item['x']][item['y']] = None
                while len(self.body) > 0:
                    self.body.pop()

                FOOD_LOCK.release()
                GRID_LOCK.release()
                return

            (nextx, nexty) = theNextPosition

            if FOOD == (nextx, nexty):
                self.maxsize = self.maxsize + 1
                FOOD_EXIST = False

            GRID[nextx][nexty] = self.color # update the GRID state
            self.body.insert(0, {'x': nextx, 'y': nexty}) # update this worm's own state

            # Check is we've grown too long, and cut off tail if we have.
            # This gives the illusion of the worm moving.
            if len(self.body) > self.maxsize:
                GRID[self.body[BUTT]['x']][self.body[BUTT]['y']] = None # update the GRID state
                del self.body[BUTT] # update this worm's own state (heh heh, worm butt)

            FOOD_LOCK.release()
            GRID_LOCK.release()
            pygame.time.wait(self.speed)

    def getNextPosition(self):
        # Figure out the x and y of where the worm's head would be next, based
        # on the current postition of its "head" and direction member.

        endNode = {
            'current': FOOD,
            'value_f': 0,
            'value_h': 0,
            'value_g': 0,
            'parent': None
        }
        startNode = {
            'current': (self.body[HEAD]['x'], self.body[HEAD]['y']),
            'value_f': 0,
            'value_h': 0,
            'value_g': 0,
            'parent': None
        }
        self.A_Star_Search(startNode, endNode)

        result = endNode
        if result["parent"] == None:
            return None
        while (result["parent"]["parent"] != None):
            result = result["parent"]
        return result["current"]

    def NextNode(self, step, parent, end):
        currentNode = {
            'current': (parent["current"][0] + step[0], parent["current"][1] + step[1]),
            'value_f': 0,
            'value_h': 0,
            'value_g': parent["value_g"] + 1,
            'parent': parent
        }
        currentNode["value_h"] = abs(end["current"][0] - currentNode["current"][0]) + \
                                 abs(end["current"][1] - currentNode["current"][1])

        currentNode["value_f"] = currentNode["value_h"] + currentNode["value_g"]

        if 0 <= currentNode['current'][0] < CELLS_WIDE and \
                                0 <= currentNode['current'][1] < CELLS_HIGH:
            if GRID[currentNode['current'][0]][currentNode['current'][1]] == None or \
                            GRID[currentNode['current'][0]][currentNode['current'][1]] == WHITE:
                return currentNode
        else:
            return None

    def A_Star_Search(self, start, end):
        visited = [[False for i in range(CELLS_HIGH)] for j in range(CELLS_WIDE)]
        start["value_h"] = abs(end["current"][0] - start["current"][0]) + abs(end["current"][1] - start["current"][1])
        start["value_f"] = start["value_h"] + start["value_g"]
        openList = []
        openList.append(start)

        while len(openList) != 0:
            openList.sort(key=lambda node: node["value_f"])
            current = openList.pop(0)

            for step in STEPS:
                next = self.NextNode(step, current, end)

                if next != None and visited[next["current"][0]][next["current"][1]] == False:
                    flag = False
                    for item in openList:
                        if item["current"] == next["current"]:
                            flag = True

                            if item["value_g"] < next["value_g"]:
                                item["value_f"] = next["value_f"]
                                item["value_h"] = next["value_h"]
                                item["value_g"] = next["value_g"]
                                item["parent"] = next["parent"]
                            break

                    if flag == False:
                        openList.append(next)

            if current["current"] == end["current"]:
                end["parent"] = current["parent"]
                return

            visited[current["current"][0]][current["current"][1]] = True
        return None


def main():
    global FPSCLOCK, DISPLAYSURF

    # Draw some walls on the grid
    squares = """
        ...........................
        ...........................
        ...........................
        .H..H..EEE..L....L.....OO..
        .H..H..E....L....L....O..O.
        .HHHH..EE...L....L....O..O.
        .H..H..E....L....L....O..O.
        .H..H..EEE..LLL..LLL...OO..
        ...........................
        .W.....W...OO...RRR..MM.MM.
        .W.....W..O..O..R.R..M.M.M.
        .W..W..W..O..O..RR...M.M.M.
        .W..W..W..O..O..R.R..M...M.
        ..WW.WW....OO...R.R..M...M.
        ...........................
        ...........................
    """
    #setGridSquares(squares)

    # Pygame window set up.
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Threadworms')

    # Create the worm objects.
    worms = [] # a list that contains all the worm objects
    for i in range(NUM_WORMS):
        worms.append(Worm(speed=50))
        worms[-1].start() # Start the worm code in its own thread.
    while True: # main game loop
        handleEvents()
        drawGrid()

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def handleEvents():
    # The only event we need to handle in this program is when it terminates.
    global WORMS_RUNNING

    for event in pygame.event.get(): # event handling loop
        if (event.type == QUIT) or (event.type == KEYDOWN and event.key == K_ESCAPE):
            WORMS_RUNNING = False # Setting this to False tells the Worm threads to exit.
            pygame.quit()
            sys.exit()


def drawGrid():
    # Draw the grid lines.
    DISPLAYSURF.fill(BGCOLOR)

    for x in range(0, WINDOWWIDTH, CELLS_SIZE): # draw vertical lines
        pygame.draw.line(DISPLAYSURF, GRID_LINES_COLOR, (x, 0), (x, WINDOWHEIGHT))
    for y in range(0, WINDOWHEIGHT, CELLS_SIZE): # draw horizontal lines
        pygame.draw.line(DISPLAYSURF, GRID_LINES_COLOR, (0, y), (WINDOWWIDTH, y))

    # the main thread that stays int the main loop (which calls drawGrid) also
    # needs to acquire the GRID_LOCK lock before modifying the GRID variable

    GRID_LOCK.acquire()

    for x in range(0, CELLS_WIDE):
        for y in range(0, CELLS_HIGH):
            if GRID[x][y] is None:
                continue # No body segment at this cell to draw, so skip it
            color = GRID[x][y] # modify the GRID data structure

            # Draw the body segment on the screen
            darkerColor = (max(color[0] - 50, 0), max(color[1] - 50, 0), max(color[2] - 50, 0))
            pygame.draw.rect(DISPLAYSURF, darkerColor, (x * CELLS_SIZE, y * CELLS_SIZE, CELLS_SIZE, CELLS_SIZE))
            pygame.draw.rect(DISPLAYSURF, color,
                             (x * CELLS_SIZE + 4, y * CELLS_SIZE + 4, CELLS_SIZE - 8, CELLS_SIZE - 8))

    GRID_LOCK.release() # We're done messing with GRID, so release the lock


def setGridSquares(squares, color=(192, 192, 192)):
    squares = squares.split('\n')
    if squares[0] == '':
        del squares[0]
    if squares[-1] == '':
        del squares[-1]

    GRID_LOCK.acquire()
    for y in range(min(len(squares), CELLS_HIGH)):
        for x in range(min(len(squares[y]), CELLS_WIDE)):
            if squares[y][x] == ' ':
                GRID[x][y] = None
            elif squares[y][x] == '.':
                pass
            else:
                GRID[x][y] = color
    GRID_LOCK.release()


if __name__ == '__main__':
    main()

    
