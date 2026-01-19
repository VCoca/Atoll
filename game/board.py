class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        self.game_over = False

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
        self.moves.append(x, y) # da cuva koordinate; bitno zbog algoritma
        return [self.X(x), self.Y(y)] # za prikaz

    def modifyArray(self, x, y, player):
        # pretpostavlja da su x i y dobri, proverava se van
        self.matrix[x+1][y+1]=player


    def checkNeighbors(self, x, y):
        """
        Vraca listu susednih koordinata koje su povezane sa trenutnim poljem.
        Povezano znaci:
          - ista apsolutna vrednost root-a (-1/-2)
          - ili ista vrednost igrača (1/2)
        """
        neighbors = []
        val = self.matrix[x][y]
        if val == 0 or val == ' ':
            return []

        # sve moguce susedne pozicije (horizontalno, vertikalno, dijagonalno)
        directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.dim and 0 <= ny < self.dim:
                nval = self.matrix[nx][ny]
                if nval != 0 and nval != ' ':
                    # dozvoljeno: ista apsolutna vrednost ili ista vrednost igrača
                    if abs(nval) == abs(val) or nval == val:
                        neighbors.append((nx, ny))
        return neighbors

    # vraca koordinate
    "NE VALJA"
    def checkNeighbors2(self, x, y):
        neighbors = []
        if self.matrix[x][y] == 0 or self.matrix[x][y] == ' ':
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
                val = self.matrix[i][j]

                # prvo proveravamo da li je int
                if isinstance(val, int) and val < 0:
                    roots.append((i, j))   # tuple koordinata
        
        return roots

     # da li je endRoot dozvoljen kraj
    
    def isRealEndRoot(self, x1, y1, x2, y2):
        # end root NE SME biti sused početnom root-u
        if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:
            return False
        return True


    "NE VALJA"
    def isRealEndRoot2(self, x1, y1, x2, y2):
        if (((x1 + 1) != x2) and (x1 != (x2 + 1)) and
            ((y1 + 1) != y2) and (y1 != (y2 + 1)) and
            ((x1 < x2) or (y1 < y2) or (x1 > x2) or y1 > y2)):
            return True

        return False

    def isRoot(self, x, y):
        if (self.matrix[x][y] < 0):
            return True
        return False

    # provera da li je kraj igre - DPS
    def isGoal(self):
        # prerano za proveru
        if self.moveCount <= (2 * (self.size - 1) - 1):
            return False

        roots = self.getRoots()  # lista svih root koordinata
        visited_global = set()   # da ne pokrećemo DFS više puta iz iste komponente

        for (rx, ry) in roots:
            if (rx, ry) in visited_global:
                continue

            stack = [(rx, ry)]
            visited_local = set()
            visited_local.add((rx, ry))

            while stack:
                x, y = stack.pop()

                # prolazimo kroz sve komšije trenutnog polja
                #print(f"Susedi polja: {x,y}:")
                for (nx, ny) in self.checkNeighbors(x, y):
                    #print(f"({nx}, {ny})", end=" ")
                    if (nx, ny) in visited_local:
                        continue

                    visited_local.add((nx, ny))
                    visited_global.add((nx, ny))

                    # PROVERA: da li je root i nije početni root
                    if self.isRoot(nx, ny) and (nx, ny) != (rx, ry):
                        if self.isRealEndRoot(rx, ry, nx, ny):
                            print()
                            print(f"----------KRAJ IGRE----------")
                            print(f"Pocetni root: {(rx, ry)}, End root: {(nx, ny)}")
                            return True

                    # dodajemo suseda u stack za dalji DFS
                    stack.append((nx, ny))
                #print()

        # ako nijedna komponenta nije dala kraj igre
        return False


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