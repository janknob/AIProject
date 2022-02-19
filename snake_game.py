import pygame
import random
import numpy as np
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

class SnakeGameAI:
    # Display Größe des Spiels Breite x Höhe
    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h

        self.gameNumber = 0

        # Initialisierung des Displays
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake AI')
        self.clock = pygame.time.Clock()
        self.reset()

    # Funktion um das Spiel automatisch zurückzusetzen
    def reset(self):
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

        # Schlangengeschwindigkeit
        self.speed = 40

        # Food wird zufällig platziert bei Start des Spieles
        self.item = None
        self._random_item_place()
        self.frame_iteration = 0

    # Hilfs-Funktion: Das Food-Item wird hierdurch zufällig im Display platziert
    def _random_item_place(self):

        # Zufälliger Integer zwischen 0 und der Höhe minus Item-Größe und dies Geteilt durch die Item-Größe und das
        # insgesamt mal der Item-Größe. Hierdurch bekommt man zufällige Positionen des Food-Item, welche Multiple des
        # Blockes sind und so innerhalb des Rasters sind
        x = random.randint(0, int(self.w / BLOCK_SIZE - 1)) * BLOCK_SIZE
        y = random.randint(0, int(self.h / BLOCK_SIZE - 1)) * BLOCK_SIZE
        self.item = Point(x, y)

        # Check ob Food dort platziert wird wo sich die Schlange befindet, falls Ja wird ein neuer Ort gesucht
        if self.item in self.snake:
            self._random_item_place()

    def play_step(self, action):

        # Schwellenwert, falls die AI nicht bessert wird und somit das Spiel abgebrochen wird
        self.frame_iteration += 1

        for event in pygame.event.get():
            #Quit Game
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Richtung User-Input Schlange
            # Checkt, ob der Input in gleiche Richtung zweimal eingegeben wurde
            # Checkt, ob ein Input eingegeben wurde, wenn der Schlangenkopf außerhalb des Displays ist
            """
            if event.type == pygame.KEYDOWN and 0 <= self.head.x <= self.w and 0 <= self.head.y <= self.h:
                if event.key == (pygame.K_LEFT or event.key == pygame.K_a) and self.direction is not Direction.RIGHT:
                    self.direction = Direction.LEFT
                elif event.key == (pygame.K_RIGHT or event.key == pygame.K_d) and self.direction is not Direction.LEFT:
                    self.direction = Direction.RIGHT
                elif event.key == (pygame.K_UP or event.key == pygame.K_w) and self.direction is not Direction.DOWN:
                    self.direction = Direction.UP
                elif event.key == (pygame.K_DOWN or event.key == pygame.K_s) and self.direction is not Direction.UP:
                    self.direction = Direction.DOWN
            """

        # Schlangen Bewegungen
        # In die Richtung in der die Schlange sich bewegt, wird immer wieder ein Körperteil hinzugefügt
        # Für User-Eingabe: self._move(self.direction)
        self._move(action) # Update Schlangenkopf
        self.snake.insert(0, self.head)

        reward = 0

        # Game Over Check bzw. Check, ob die AI keinen Fortschritt macht

        gameOver = False
        # Wenn die Schlange mit der Wand kollidiert oder wenn sie einen bestimmten Schwellenwert erreicht, der größer
        # als die Länge der Schlange ist -> Schlange macht keinen Fortschritt
        if self.is_collision() or self.frame_iteration > 100*len(self.snake):
            gameOver = True
            self.gameNumber += 1
            print('GameNumber: ', self.gameNumber)
            reward = -10
            return reward, gameOver, self.score

        # IF Abfrage falls deaktiviert wird, dass kein weiteres Teil an den Schlangenschwanz angefügt werden soll
        # Deaktiviert nach einer bestimmten Traininsspiel Zahl (+99 Spiele), den automatischen Spieleabbruch
        """
        if self.gameNumber < 100 and self.frame_iteration > 100*len(self.snake):
            gameOver = True
            self.gameNumber += 1
            ('GameNumber: ', self.gameNumber)
            reward = -10
            return reward, gameOver, self.score
        """

        # Wenn die Schlange etwas gegessen hat, dann soll die Schlange größer werden und das Item-Food als Körperteil
        # nehmen, der Score auf 1 erhöht werden, die Schlange soll schneller werden und ein neues Item-Food soll
        # zufällig platziert werden
        if self.head == self.item:
            self.score += 1
            self.speed += 1
            reward = 10
            self._random_item_place()
            #self.snake.pop() # Funktion die dazu führt das kein weiteres Stück am Schlangenschwanz anghängt wird
        else:
            self.snake.pop()


        # Update UI and Game Clock
        self._update_ui()
        self.clock.tick(self.speed)
        # Rückgabe von GameOver und des Scores zum Auswerten, wie gut die KI das Spiel löst
        gameOver = False
        return reward, gameOver, self.score

    # Hilfs-Funktion für Kollisionen, die die Schlange verursacht
    def is_collision(self, pt=None):

        # Die KI benötigt eine Gefahr, um die Border zu erkennen
        if pt is None:
            pt = self.head

        # IF-Abfrage für Display Grenze, sobald die Schlange eine Wand berührt, dann Game Over. Snake V1
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            return True

        # IF-Abfrage für Display Grenze, sobald die Schlange eine Wand berührt kehrt sie auf der anderen
        # Seite wieder heraus. Snake V2
        """
        if (self.head.x == self.w) and self.direction == Direction.RIGHT:
            self.head = Point(self.head.x-self.w-BLOCK_SIZE, self.head.y)
        elif (self.head.x < 0) and self.direction == Direction.LEFT:
            self.head = Point(self.head.x+self.w+BLOCK_SIZE, self.head.y)
        elif (self.head.y == self.h) and self.direction == Direction.DOWN:
            self.head = Point(self.head.x, self.head.y - self.h - BLOCK_SIZE)
        elif (self.head.y < 0) and self.direction == Direction.UP:
            self.head = Point (self.head.x, self.head.y + self.h+BLOCK_SIZE)
        """

        # Schlange trifft sich selbst
        if pt in self.snake[1:]:
            return True

        return False

    # Hilfs-Funktion: Update des Userinterface
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
    # Für Keyboard Tasten als Parameter direction anstatt action
    def _move(self, action):
        # [straight, right, left] -> Richtungen für unsere KI aus der Sicht der Schlange

        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        index = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_direction = clock_wise[index] # Nichts passiert Schlange bewegt sich weiter nach vorne
        elif np.array_equal(action, [0, 1, 0]):
            next_index = (index + 1) % 4 # nimmt aus clock_wise-Array die nächste Richtung, die immer nacht rechts geht
            new_direction = clock_wise[next_index] # Schlange macht eine Rechts-kurve (r -> d -> l -> u -> ...)
        else: # [0, 0, 1]
            next_index = (index - 1) % 4 # nimmt aus clock_wise-Array die nächste Richtung, die immer nacht links geht
            new_direction = clock_wise[next_index] # Schlange macht eine Links-kurve (r -> u -> l -> d -> ...)

        self.direction = new_direction

        x = self.head.x
        y = self.head.y
        # Hinweis: Für Tasteneingabe muss self. gelöscht werden und es darf nur direction dort stehen
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE

        self.head = Point(x, y)

# Main-Process Skript für Benutzer Eingaben
# wird für die KI nicht benötigt, da die Play-Funktion mithilfe der Agent-Klasse aufgerufen wird,
# die dann die KI steuert und einen Algorithmus implementiert
"""if __name__ == '__main__':
    game = SnakeGameAI()

    # Game Loop: Spiel startet immer wieder neu
    while True:

        gameOver, score = game.play_step()

        # Exit aus Endloss Schleife
        if gameOver == True:
            break

    print('Final Score: ', score)

    pygame.quit()
"""