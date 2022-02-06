import pygame
import random
from enum import Enum
from collections import namedtuple

# Methode, sodass alle Module korrekt initialisiert werden
pygame.init()

# Font Laden
font = pygame.font.Font('OpenSans-VariableFont_wdth,wght.ttf', 25)

# Bewegungsrichtungen als Konstanten
# Aufgrund, das es bei der Initialisierung des GameState durch Strings zu Problemen kommen kann
# wird hier auf Nummern zurückgegriffen
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

# Point Object (ähnlich wie eine Klasse nur lightweight)
# zuständig, sodass der Schlangenkopf in der Mitte startet
Point = namedtuple('Point', 'x, y')

# Konstanten für RGB-Farben
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN1 = (46, 120, 0)
GREEN2 = (98, 252, 3)
BLACK = (0, 0, 0)

# Konstante Blockgröße
BLOCK_SIZE = 20

#  Spielgeschwindigkeit
SPEED = 10

class SnakeGame:
    # Display Größe des Spiels Breite x Höhe
    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h

        # Initialisierung des Displays
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake AI')
        self.clock = pygame.time.Clock()

        # Initialisierung GameState
        # Schlange bewegt sich automatisch bei Spielstart nach rechts
        self.direction = Direction.RIGHT

        # Start des Schlangenkopfes in der Mitte
        self.head = Point(self.w/2, self.h/2)
        self.snake = [self.head,
                      Point(self.head.x-BLOCK_SIZE, self.head.y),
                      Point(self.head.x-(2*BLOCK_SIZE), self.head.y)]

        # Game Score auf 0 setzen
        self.score = 0

        self.speed = 10

        # Food wird zufällig platziert bei Start des Spieles
        self.item = None
        self._random_item_place()

    # Hilfs-Funktion: Das Food-Item wird hierdurch zufällig im Display platziert
    def _random_item_place(self):

        # Zufälliger Integer zwischen 0 und der Höhe minus Item-Größe und dies Geteilt durch die Item-Größe und das
        # insgesamt mal der Item-Größe. Hierdurch bekommt man zufällige Positionen des Food-Item, welche Multiple des
        # Blockes sind und so innerhalb des Rasters sind
        x = random.randint(0, int(self.w / BLOCK_SIZE - 1)) * BLOCK_SIZE
        y = random.randint(0, int(self.h / BLOCK_SIZE - 1)) * BLOCK_SIZE
        self.item = Point (x,y)

        # Check ob Food dort platziert wird wo sich die Schlange befindet, falls Ja wird ein neuer Ort gesucht
        if self.item in self.snake:
            self._random_item_place()

    def play_step(self):

        for event in pygame.event.get():
            #Quit Game
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            # Richtung User-Input Schlange
            if event.type == pygame.KEYDOWN:
                if event.key == (pygame.K_LEFT or event.key == pygame.K_a) and self.direction is not Direction.RIGHT:
                    self.direction = Direction.LEFT
                elif event.key == (pygame.K_RIGHT or event.key == pygame.K_d) and self.direction is not Direction.LEFT:
                    self.direction = Direction.RIGHT
                elif event.key == (pygame.K_UP or event.key == pygame.K_w) and self.direction is not Direction.DOWN:
                    self.direction = Direction.UP
                elif event.key == (pygame.K_DOWN or event.key == pygame.K_s) and self.direction is not Direction.UP:
                    self.direction = Direction.DOWN

        # Snake Movement
        self._move(self.direction) # Update Schlangenkopf
        self.snake.insert(0, self.head)

        # Game Over Check
        gameOver = False
        if self._is_collision():
            gameOver = True
            return gameOver, self.score

        # New Item-Food or Move
        if self.head == self.item:
            self.score += 1
            self.speed += 2
            self._random_item_place()
        else:
            self.snake.pop()


        # Update UI and Game Clock
        self._update_ui()
        self.clock.tick(self.speed)
        # Rückgabe von GameOver und des Scores zum Auswerten, wie gut die KI das Spiel löst
        gameOver = False
        return gameOver, self.score

    # Hilfs-Funktion für Kollisionen, die die Schlange verursacht
    def _is_collision(self):
        # Display Grenze
        if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
            return True
        # Schlange trifft sich selbst
        if self.head in self.snake[1:]:
            return True

        return False

    # Hilfs-Funktion: Update des User Interface
    # Reihenfolge der Farben ist wichtig!
    def _update_ui(self):
        self.display.fill(BLACK)

        # Schlange
        for pt in self.snake:
            pygame.draw.rect(self.display, GREEN1, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, GREEN2, pygame.Rect(pt.x+4, pt.y+4, 12, 12))

        # Food-Item
        pygame.draw.rect(self.display, RED, pygame.Rect(self.item.x, self.item.y, BLOCK_SIZE, BLOCK_SIZE))

        # Score Text
        text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(text, [0, 0])
        pygame.display.flip()

    # Hilfs-Funktion: Bewegungen der Schlange
    def _move(self, direction):
        x = self.head.x
        y = self.head.y
        if direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif direction == Direction.UP:
            y-= BLOCK_SIZE

        self.head = Point (x, y)

# Main-Process Skript
if __name__ == '__main__':
    game = SnakeGame()

    # Game Loop: Spiel startet immer wieder neu
    while True:

        gameOver, score = game.play_step()

        # Exit aus Endloss Schleife
        if gameOver == True:
            break

    print('Final Score: ', score)

    pygame.quit()