class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        # matrica je dimenzija 2*size+1
        # minimalan broj poteza pre zavrsetka igre je 4(size-1)-2
        # sto je oba igraca po 2(n-1)-1 poteza

        self.dim = 2 * size + 1
        self.matrix = [
            [0 for _ in range(self.dim)]
            for _ in range(self.dim)
        ]

        # brojac koraka
        # nakon 2*(size-1)-1 poteza jednog igraca ima smisla pozivati f-ju za proveru
        # da li je cilj igre ispunjen; isto f-ja checkRoots tek kad vrati nesto treba proveravati da li je igra gotova
        # i to da li je vratila 1 bar koren i jos jedan i to ne susedni
        self.moveCount: int = 0

        self.moves = []

        # punjenje rubova
        # -1 crvena, -2 zelena
        for i in range(1, size):
            if (i <= ((size - 1) / 2)):
                self.matrix[0][i] = -2
                self.matrix[i][0] = -1
            else:
                self.matrix[0][i] = -1
                self.matrix[i][0] = -2

        for i in range(size + 1, 2 * size):
            if (i <= (size + (size - 1) / 2)):
                self.matrix[2 * size][i] = -1
                self.matrix[i][2 * size] = -2
            else:
                self.matrix[2 * size][i] = -2
                self.matrix[i][2 * size] = -1

        for i in range(1, size):
            # druga koordinata je size+i
            if (i <= ((size - 1) / 2)):
                self.matrix[i][size + i] = -2
                self.matrix[size + i][i] = -1
            else:
                self.matrix[i][size + i] = -1
                self.matrix[size + i][i] = -2

        filler = ' '

        # popunjavanje nepostojecih polja
        # opsti slucajevi
        for i in range (1, size):
            for j in range (size + 1 + i, 2 * size + 1):
                self.matrix[i][j] = filler
        
        for i in range(size + 1, 2 * size):
            for j in range(i - size):
                self.matrix[i][j] = filler

        #specijalni slucajevi
        for i in range(size, 2 * size + 1):
            self.matrix[0][i] = filler

        for i in range(0, size + 1):
            self.matrix[2*size][i] = filler

        self.matrix[0][0] = filler
        self.matrix[size][0] = filler
        self.matrix[size][2*size] = filler
        self.matrix[2*size][2*size] = filler



    def drawMatrix(self):
        for i in range(self.dim):
            for j in range(self.dim):
                print(f"{self.matrix[i][j]:3}", end=" ")

            print()

    def X(x):
        return x + 1
    
    def Y(y):
        return chr(ord('A') + y)
    
    def move(self, x, y):
        self.moveCount += 1
        self.moves.add(x, y) # da cuva koordinate; bitno zbog algoritma
        return [self.X(x), self.Y(y)] # za prikaz

    # vraca koordinate
    # TODO: proveriti checkRoots
    # def checkRoots(self):
    #     n = self.size
    #     roots_coords = [
    #         (0, 0),
    #         (0, n-1),
    #         (2*(n-1), n-1),
    #         (2*(n-1), 2*(n-1)),
    #         (n-1, 2*(n-1)),
    #         (0, n-1) ## duplikat?
    #     ]
    #     #roots = [f"{x},{y}" for x, y in roots_coords]
    #     #return roots
    #     return roots_coords

    def checkRootNeighbor(self, x, y):
        rootNeighbors = [] # lista komsija

    def modifyArray(self, x, y, player):
        # pretpostavlja da su x i y dobri, proverava se van
        self.matrix[x+1][y+1]=player

    # vraca koordinate
    def checkNeighbors(self, x, y):
        neighbors = []
        if self.matrix[x][y] == 0 or self.matrix[x][y] == ' ' or self.matrix[x][y]:
            return [] # vraca prazno jer ne uzimamo u obzir prazna polja
        
        # da bi radilo za korena polja da ne nalazi susede koji su korena polja
        # radimo proveru prvo je l koreno i ako jeste onda proveravamo je l
        # ima istu vrednost kao abs(koreno); ako nije nije bitno

        # provera da li je root
        if (self.matrix[x][y] < 0):
            if (x > 0):
                if (y > 0):
                    if (self.matrix[x - 1][y - 1] == abs(self.matrix[x][y])):
                        neighbors.append((x - 1, y - 1))
                    if (self.matrix[x][y - 1] == abs(self.matrix[x][y])):
                        neighbors.append((x, y - 1))

            if (self.matrix[x - 1][y] == abs(self.matrix[x][y])):
                neighbors.append((x - 1, y))

            if (x < self.dim - 1):
                if (y < self.dim - 1):
                    if (self.matrix[x + 1][y + 1] == abs(self.matrix[x][y])):
                        neighbors.append((x + 1, y + 1))
                    if (self.matrix[x][y + 1] == abs(self.matrix[x][y])):
                        neighbors.append((x, y + 1))

                if (self.matrix[x + 1][y] == abs(self.matrix[x][y])):
                    neighbors.append((x + 1, y))

        # ako nije root
        else:
            if (x > 0):
                if (y > 0):
                    if (self.matrix[x - 1][y - 1] == self.matrix[x][y]):
                        neighbors.append((x - 1, y - 1))
                    if (self.matrix[x][y - 1] == self.matrix[x][y]):
                        neighbors.append((x, y - 1))

            if (self.matrix[x - 1][y] == self.matrix[x][y]):
                neighbors.append((x - 1, y))

            if (x < self.dim - 1):
                if (y < self.dim - 1):
                    if (self.matrix[x + 1][y + 1] == self.matrix[x][y]):
                        neighbors.append((x + 1, y + 1))
                    if (self.matrix[x][y + 1] == self.matrix[x][y]):
                        neighbors.append((x, y + 1))

                if (self.matrix[x + 1][y] == self.matrix[x][y]):
                    neighbors.append((x + 1, y))
            
        return neighbors
    
    def getRoots(self):
        roots = []
        for i in range(self.dim):
            for j in range(self.dim):
                if (self.matrix[i][j] < 0):
                    roots.append(i, j)

        return roots
     # da li je endRoot dozvoljen kraj
    def isRealEndRoot(self, root1X, root1Y):
        # TODO: napravi haha

        return False

    # provera da li je kraj igre - DPS
    def isGoal(self):
        # minimalan br. poteza za kraj igre
        if (self.moveCount > (2 * (self.size - 1) - 1)):
            visitedRoots = set()    # skup ima jedinstvene elemente
            roots = self.getRoots()
            for i, (nx, ny) in enumerate(roots):
                # i = indeks, (nx, ny) = koordinata korena
                if (nx, ny) in visitedRoots:
                    continue

                # lista komsija trenutnog root polja
                currRootNeighbors = self.checkNeighbors(nx, ny)
                if (currRootNeighbors):
                    for neighbor in currRootNeighbors:
                        if neighbor in visitedRoots:
                            continue
                            
                        visitedRoots.add(neighbor)
    # TODO: nisam siguran za ovu f-ju, treba je proveriti
    def checkNonNeighborRoots(self):
        roots = self.checkRoots()
        non_neighbors = []
        for i, (x, y) in enumerate(roots):
            # zanemari prazna polja
            if self.matrix[x][y] == 0:
                continue
            # proveri da li je bilo koji drugi koren susedan (geometrijski)
            is_neighbor = False
            for j, (x2, y2) in enumerate(roots):
                if i == j:
                    continue
                if max(abs(x - x2), abs(y - y2)) <= 1:
                    is_neighbor = True
                    break
            if not is_neighbor:
                non_neighbors.append((x, y))
        return non_neighbors
    
    # TODO: TREBA DORADITI PROVERU DA LI JE NEKI OD SUSEDA NONNEIGHBORROOT TRENUTNOG KORENA
    # STO ZNACI KRAJ IGRE!!!
    # ovde implementacija DPS algoritma za proveru da li je igra gotova
    def isGoal(self):
        # TODO: da odlucimo da li cemo ovde proveru za susedne korene ili u posebnoj f-ji;
        # za sad neka ga da bude posebna f-ja cisto da imamo logiku za to
        # (jer ako su susedni koreni onda sigurno nije kraj igre)

        moveCount = self.moveCount
        roots = self.checkRoots()
        nonNeighborRoots = self.checkNonNeighborRoots()
        
        # TODO: isto treba odluciti o definiciji poteza; da li je potez kad oba igraca igraju ili kad
        # je igrao samo jedan
        if (moveCount > (2 * (self.dim - 1) - 1) and roots and nonNeighborRoots):
            visitedRoots = set() # prazan skup (jedinstveni elementi)
            # da ne odemo npr. u kruzno ispitivanje
            for (x, y) in roots:
                if (x, y) in visitedRoots:
                    continue
                # preskoci prazne (0) korene — samo 1 i 2 su validne za cilj
                original = self.matrix[x][y]
                if original == 0:
                    continue

                visitedRoots.add((x, y))
                stack = [(x, y)]
                while stack:
                    cx, cy = stack.pop()
                    for nx, ny in self.checkNeighbors(cx, cy):
                        # ako sused nema istu vrednost kao original -> izlaz
                        if self.matrix[nx][ny] != original:
                            return False
                        if (nx, ny) not in visitedRoots:
                            visitedRoots.add((nx, ny))
                            stack.append((nx, ny))
            return True
        return False
    
    # ...existing code...
    # OVO MI JE COPILOT PISAO; NEKA GA OVDE A VIDECEMO DA LI JE DOBRO
    # SVAKAKO OCU OVU GORE VERZIJU RADIJE DA MODIFIKUJEM NEGO DA KORISTIMO OVU
    def isGoal2(self):
        moveCount = self.moveCount
        roots = self.checkRoots()
        nonNeighborRoots = self.checkNonNeighborRoots()
        
        # minimalni threshold pre provere cilja
        if not (moveCount > (2 * (self.dim - 1) - 1) and roots and nonNeighborRoots):
            return False

        non_set = set(nonNeighborRoots)

        # za svaki nesusedni koren pokreni DFS po regionu iste boje;
        # ako tokom pretrage naletimo na drugi nesusedni koren -> povezano
        for x, y in nonNeighborRoots:
            original = self.matrix[x][y]
            if original == 0:
                continue
            visited = {(x, y)}
            stack = [(x, y)]
            while stack:
                cx, cy = stack.pop()
                for nx, ny in self.checkNeighbors(cx, cy):
                    # ako smo naleteli na drugi nesusedni koren, cilj je dostignut
                    if (nx, ny) in non_set and (nx, ny) != (x, y):
                        return True
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        stack.append((nx, ny))
        return False
# ...existing code...

def number_to_position(number, board_size):
    column_lengths = []
        
    for i in range(board_size):
        column_lengths.append(board_size + i)
        
    for i in range(1, board_size):
        column_lengths.append(2 * board_size - 1 - i)
        
        remaining = number

    j=1
    for col in range(len(column_lengths)):
        col_length = column_lengths[col]
        if remaining < col_length:
            row = remaining
            return (row+max(0,j-board_size), col)
        remaining -= col_length
        j+=1
        
    return (-1, -1)