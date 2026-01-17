class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        # matrica je dimenzija 2*size-1 za spoljna
        # minimalan broj poteza pre zavrsetka igre je 4(size-1)-2
        # sto je oba igraca po 2(n-1)-1 poteza

        dim = 2 * size - 1
        matrix = [
            [0 for _ in range(dim)]
            for _ in range(dim)
        ]

    def X(x):
        return x + 1
    
    def Y(y):
        return chr(ord('A') + y)
    
    def checkRoots(self):
        roots = []
        # TODO: implementiraj f-ju koja nalazi sve korene koordinate

    def checkNeighbors(self, x, y):
        neighbors = []
        if (x > 0):
            if (y > 0):
                if (self.matrix[x - 1][y - 1] == self.matrix[x][y]):
                    neighbors.add(x - 1 + "," + y - 1)
                if (self.matrix[x][y - 1] == self.matrix[x][y]):
                    neighbors.add(x + "," + y - 1)

            if (self.matrix[x - 1][y] == self.matrix[x][y]):
                neighbors.add(x - 1 + "," + y)

        if (x < self.dim - 1):
            if (y < self.dim - 1):
                if (self.matrix[x + 1][y + 1] == self.matrix[x][y]):
                    neighbors.add(x + 1 + "," + y + 1)
                if (self.matrix[x][y + 1] == self.matrix[x][y]):
                    neighbors.add(x + "," + y + 1)

            if (self.matrix[x + 1][y] == self.matrix[x][y]):
                neighbors.add(x + 1 + "," + y)
            
        return neighbors