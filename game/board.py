class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]