import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

class Linear_QNet (nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.linear1(x)) #activation funktion
        x = self.linear2(x)
        return x

    # Speichert das Model mit dem Namen model.pth in einem neuen Ordner model
    def save(self, file_name='model.pth'):
        model_folder_path = './model'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)

    def load(self, file_name='model.pth'):
        model_folder_path = './model'
        file_name = os.path.join(model_folder_path, file_name)

        if os.path.isfile(file_name):
            self.load_state_dict(torch.load(file_name))
            self.eval()
            print('Lädt bestehendes Python File')
            return True

        print('Keine Existierendes File gefunden!')
        return False

class QTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr) # PyTorch Optimierer Adam
        self.criterion = nn.MSELoss()

    # Übergabewert kann eine Liste, ein Tupel oder ein Element sein
    def train_step(self, state, action, reward, next_state, done):

        # mit torch.tensor zu einem float umgewandelt werden
        # Muss nicht mit Done bzw. der GameOver variabel gemacht werden,
        # da diese nicht als tensor variabel gebrauch wird
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)
        # (n, x)

        # Handle mit verschiedenen Größen bzw. Übergabeparameter (Tulpel, Liste, Element)
        if len(state.shape) == 1: # (1, x)
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, ) # Konvertiert die Done Variabel zu einem Tupel

        # Schritt 1: vorhergesagte Q-Werte mit dem aktuellen Zustand
        # Schritt 2: Q-Formel anwenden: Q_new = r + y * max(nächster vorhergesagter Q Wert)
        # pred.clone() um daraus 3 Werte zu machen -> 3 Finale Zustände (Geradeaus, Links, rechts)
        # preds[argmax(action)] = Q_new
        pred = self.model(state) # state -> alter Zustand
        target = pred.clone()
        for index in range(len(done)):
            Q_new = reward[index]
            if not done [index]:
                Q_new = reward[index] + self.gamma * torch.max(self.model(next_state[index]))

            target[index][torch.argmax(action[index]).item()] = Q_new

        self.optimizer.zero_grad()
        loss = self.criterion(target, pred)
        loss.backward()

        self.optimizer.step()



