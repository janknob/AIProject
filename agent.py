import torch
import random
import numpy as np
from collections import deque # Datenstruktur um Speicher zu verwalten
from snake_game import SnakeGameAI, Direction, Point
from model import Linear_QNet, QTrainer
from plot import plot

MAX_MEMORY = 100_000 # Maximaler Speicher der verwendet werden soll
BATCH_SIZE = 1000 # Anzahl an Trainingseinheiten
LEARNING_RATE = 0.001 # Rate wie schnell die KI lernen soll

class Agent:

    # Initialisierung
    def __init__(self):
        self.n_games = 0 # Anzahl der Spiele
        self.epsilon = 0 # Zufälligkeitsgrad

        # Discount Rate: Muss eine Zahl sein, die kleiner als 1 ist, meist 0.8 oder 0.9
        self.gamma = 0.9

        self.memory = deque(maxlen=MAX_MEMORY) # popleft() wird aufgerufen, sodass Speicher freigegeben wird

        # Erste Zahl ist die größe der möglichen Zustände (Funktion get_state()), zweite Zahl sind die Hidden Layer,
        # diese Zahl kann angepasst und die 3 sind die möglichen States die die Schlange nehmen kann: Geradeaus, Links
        # oder rechts. Z.b. geradeaus [1, 0, 0]
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=LEARNING_RATE, gamma=self.gamma)

    # Methode um den aktuellen Zustand der Schlange abzugreifen (Position, Item-Food, Gefahr, etc)
    def get_state(self, game):
        """"""
        head = game.snake[0]

        # Richtungen und Winkel im Uhrzeigersinn
        clock_wise_directions = [
            Direction.RIGHT == game.direction,
            Direction.DOWN == game.direction,
            Direction.LEFT == game.direction,
            Direction.UP == game.direction
        ]
        clock_wise_angles = np.array([0, np.pi / 2, np.pi, -np.pi / 2])

        # Position - vorne: 0, rechts: 1, links: -1; BLOCK_SIZE = 20 (Definiert im Code von snake_game.py)
        getPoint = lambda pos: Point(
            head.x + 20 * np.cos(clock_wise_angles[(clock_wise_directions.index(True) + pos) % 4]),
            head.y + 20 * np.sin(clock_wise_angles[(clock_wise_directions.index(True) + pos) % 4]))

        state = [
            # Gefahr
            game.is_collision(getPoint(0)),
            game.is_collision(getPoint(1)),
            game.is_collision(getPoint(-1)),

            # Bewegungsrichtung der Schlange
            clock_wise_directions[2],
            clock_wise_directions[0],
            clock_wise_directions[3],
            clock_wise_directions[1],

            # Food-Item Ort
            game.item.x < head.x,
            game.item.x > head.x,
            game.item.y < head.y,
            game.item.y > head.y
        ]

        # normalerweise hat State nur True oder False Werte, mit dtype = int können
        # diese zu 0 und 1 umgewandelt werden
        return np.array(state, dtype=int)

    # In dieser Methode werden alle  Faktoren für unsere KI gespeichert, der Zustand in dem die KI sich befindet,
    # die Aktion (Richtung) die gemacht wurde, der aktuelle Stand der Belohnung, der nächste Zustand und ob ein
    # Game Over vorgefallen ist
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done)) # popleft() wenn Max. an Speicher erreicht wurde
        # Doppelte Klammern: Wird als ein Element gespeichert

    # Multiple
    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE: # Genügend Trainingseinheiten im Speicher?
            mini_sample = random.sample(self.memory, BATCH_SIZE) # Liste aus Tulpen
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample) # packt alle Elemente zusammen
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    # Schrittweises trainieren der KI
    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    # Die KI soll Anfangs die Umgebung kennen lernen (Wände, Display Länge, Gefahren, Foot-Item), im späteren
    # Verlauf soll dies aber immer weniger gemacht werden
    # Tradeoff Exploration / Exploitation
    def get_action(self, state):
        self.epsilon = 80 - self.n_games # Je mehr Spiele gemacht werden, desto kleiner wird epsilon
        final_move = [0, 0, 0]

        # Je kleiner Epsilon bekommt, desto weniger besteht die Chance das durch die If Abfrage ein zufälliger Zug
        # ausgeführt wird
        if random.randint(0, 200) < self.epsilon: #zufälliger Integer zwischen 0 und 200
            move = random.randint(0, 2) # Zufällige Variabel von 0, 1, 2 -> Geradeaus, Links, Rechts
            final_move[move] = 1
        else:
            # Hier wird ein Float Wert erzeugt z.B. [3.1, 5.2, 1,4]. Die Funktion nimmt daraus den maximalen Wert
            # und setzt diesen im Move Array auf 1 z.B. [0, 1, 0]. In diese Richtung bewegt sich dann die Schlange
            state0 = torch.tensor(state, dtype=torch.float) # Konvertierung zu Tensor
            prediction = self.model(state0) # Führt in agent.py die Forward Funktion aus
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

# Trainingsmethode, die unsere KI trainiert
def train ():
    plot_scores = [] # Plot
    plot_mean_scores = [] # Durchschnitt Score
    total_score = 0 # Gesamt Score
    record = 0 # Bester Score
    agent = Agent()
    # agent.model.load() # Lädt eine bereits existierende KI
    game = SnakeGameAI()
    while True:
        # alten Zustand der Schlange bekommen
        state_old = agent.get_state(game)

        # Bewegung der Schlange im aktuellen Zug
        final_move = agent.get_action(state_old)

        # Neue Bewegung durchführen und wiederrum einen neuen Zustand
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short_memory (Schrittweise)
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # Speichern dem Trainingsvorgang
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory (Experience Memory) KI lernt von den Short-Memory Trainingsvorgängen und baut auf
            # diesen auf
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            # Neuer Rekord, aktueller Score höher als bisherige Rekorde
            if score > record:
                record = score
                agent.model.save()

            print('Game:', agent.n_games, ' Score: ', score, ' Record: ', record)

            plot_scores.append(score) # Fügt der Liste den aktuellen Wert hinzu
            total_score += score # Addiert die Scores aufeinander
            mean_score = total_score / agent.n_games # Berechnet den Durchschnitts Score
            plot_mean_scores.append(mean_score) # Fügt den Durchschnittswert der Liste hinzu
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()