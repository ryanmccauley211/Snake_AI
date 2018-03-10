import random
from collections import deque

from keras.models import Sequential
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Flatten
from keras.layers import Dense
from skimage.transform import resize
from skimage.color import rgb2grey
from skimage.exposure import rescale_intensity
from skimage import data
from skimage.viewer import ImageViewer
import numpy as np

batch_size = 1000

class Agent:

    def __init__(self, model, action_space, mem_capacity=1000, learning_rate=0.01, epsilon=0.9,
                 epsilon_decay=0.99, epsilon_min=0.005, gamma=0.99, name="agent_snake"):
        self.name          = name
        self.model         = model
        self.mem_capacity  = mem_capacity
        self.memory = deque(maxlen=mem_capacity)
        self.learning_rate = learning_rate
        self.epsilon       = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min   = epsilon_min
        self.gamma         = gamma
        self.action_space  = action_space

        self.short_mem     = None


    def store_memory(self, state, action, reward, next_state, done):
        state = preprocess_image(state)
        self.memory.append((state, action, reward, next_state, done))


    def learn(self):
        sample = random.sample(self.memory, batch_size)

        for memory in sample:
            state, action, reward, next_state, done = memory

            if done:
                pred_next_reward = reward
            else:
                pred_next_reward = reward + self.gamma * np.argmax(self.model.predict(next_state)[0])

            pred_current_rewards = self.model.predict(state)[0]
            pred_current_rewards[action] = pred_next_reward
            self.model.fit(state, pred_current_rewards, epochs=1, verbose=0)


    def act(self, state):
        state = preprocess_image(state)

        if self.epsilon < np.random.rand():
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            return random.randrange(self.action_space)
        else:
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            pred_rewards = self.model.predict(state)
            action = np.argmax(pred_rewards)
            return np.argmax(self.action_space[action])


def create_model(img_sample, actions):
    global agent
    img_sample = preprocess_image(img_sample)
    rows = img_sample.shape[0]
    cols = img_sample.shape[1]
    action_space = len(actions)

    return build_cnn(1, rows, cols, action_space)


def preprocess_image(img):
    img = rgb2grey(img)
    img = resize(img, (80, 80))
    return img


def build_cnn(channels, rows, cols, action_space):
    model = Sequential()
    model.add(Conv2D(filters=32, kernel_size=(8, 8), input_shape=(rows, cols, channels), activation='relu'))

    model.add(Dense(units=64, activation='relu'))
    model.add(Dense(units=action_space, activation='sigmoid'))

    model.compile(optimizer='adam', loss='mse', metrics=['accuracy'])
    return model