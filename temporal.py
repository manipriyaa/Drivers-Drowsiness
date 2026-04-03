from collections import deque
import numpy as np

class TemporalModel:
    def __init__(self, size=15):
        self.buffer = deque(maxlen=size)

    def update(self, value):
        self.buffer.append(value)
        if len(self.buffer) < self.buffer.maxlen:
            return 0
        return np.mean(self.buffer)
