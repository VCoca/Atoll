class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        # matrica je dimenzija 2*size-1 za spoljna
        # minimalan broj poteza pre zavrsetka igre je 4(size-1)-2
        # sto je oba igraca po 2(n-1)-1 poteza

        self.matrix = [
            [0 for _ in range(2 * size - 1)]
            for _ in range(2 * size - 1)
        ]

    def X(n):
        return chr(ord('A') + n)

    def Y(y):
        return y  + 1