class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        # matrica je dimenzija 2*size-1 za spoljna
        # minimalan broj poteza pre zavrsetka igre je 4(size-1)-2
        # sto je oba igraca po 2(n-1)-1 poteza

        self.dim = 2 * size - 1
        self.matrix = [
            [0 for _ in range(self.dim)]
            for _ in range(self.dim)
        ]

    def X(x):
        return x + 1
    
    def Y(y):
        return chr(ord('A') + y)
    
    def checkRoots(self):
        n = self.size
        roots_coords = [
            (0, 0),
            (0, n-1),
            (2*(n-1), n-1),
            (2*(n-1), 2*(n-1)),
            (n-1, 2*(n-1)),
            (0, n-1)
        ]
        roots = [f"{x},{y}" for x, y in roots_coords]
        return roots

    def checkNeighbors(self, x, y):
        neighbors = []
        if (x > 0):
            if (y > 0):
                if (self.matrix[x - 1][y - 1] == self.matrix[x][y]):
                    neighbors.append(str(x - 1) + "," + str(y - 1))
                if (self.matrix[x][y - 1] == self.matrix[x][y]):
                    neighbors.append(str(x) + "," + str(y - 1))

            if (self.matrix[x - 1][y] == self.matrix[x][y]):
                neighbors.append(str(x - 1) + "," + str(y))

        if (x < self.dim - 1):
            if (y < self.dim - 1):
                if (self.matrix[x + 1][y + 1] == self.matrix[x][y]):
                    neighbors.append(str(x + 1) + "," + str(y + 1))
                if (self.matrix[x][y + 1] == self.matrix[x][y]):
                    neighbors.append(str(x) + "," + str(y + 1))

            if (self.matrix[x + 1][y] == self.matrix[x][y]):
                neighbors.append(str(x + 1) + "," + str(y))
            
        return neighbors