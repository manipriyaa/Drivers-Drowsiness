import numpy as np
from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

class TemporalLSTM:
    def __init__(self, sequence_length=20):

        self.sequence_length = sequence_length
        self.buffer = deque(maxlen=sequence_length)

        self.model = self.build_model()

    def build_model(self):

        model = Sequential([
            LSTM(32, input_shape=(self.sequence_length, 1)),
            Dense(1, activation="sigmoid")
        ])

        model.compile(
            optimizer="adam",
            loss="binary_crossentropy"
        )

        return model

    def update(self, value):

        self.buffer.append([value])

        if len(self.buffer) < self.sequence_length:
            return value

        seq = np.array(self.buffer).reshape(1, self.sequence_length, 1)

        pred = self.model.predict(seq, verbose=0)[0][0]

        return pred
