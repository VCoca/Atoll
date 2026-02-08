class Board:
    def __init__(self, size=5):
        self.size = size
        self.grid = [[0]*size for _ in range(size)]
        # prati stanja grana: 0 = slobodno, 1 = crveno, 2 = zeleno
        self.edges = {}

        self.game_over = False
        self.winner = None

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
        self._history = []

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

        self.root_segments = {}  # (x, y) -> segment_id
        self.segment_order = []  # lista segmenata po redosledu (kazaljka na satu)
        self.segment_neighbors = {}
        self.group_roots()

        # Cache playable positions that map to UI edge ids
        self.playable_positions = []
        i = 0
        while True:
            r, c = number_to_position(i, self.size)
            if r == -1 and c == -1:
                break
            self.playable_positions.append((r, c))
            i += 1

    def group_roots(self):
        roots = self.getRoots()
        self.root_segments = {}
        visited = set()
        segment_id = 0

        # 1. Grupisanje: tražimo korenove iste boje koji su spojeni na jednoj ivici
        for r_pos in roots:
            if r_pos not in visited:
                segment_id += 1
                color = self.matrix[r_pos[0]][r_pos[1]]
                stack = [r_pos]
                visited.add(r_pos)

                while stack:
                    curr = stack.pop()
                    self.root_segments[curr] = segment_id

                    # Šetamo po rubu: koren se spaja sa drugim korenom
                    # ako su udaljeni max 2 polja (preskačemo praznine)
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            nx, ny = curr[0] + dx, curr[1] + dy
                            if (nx, ny) in roots and (nx, ny) not in visited:
                                if self.matrix[nx][ny] == color:
                                    visited.add((nx, ny))
                                    stack.append((nx, ny))

        # 2. Susedstvo: Definišemo koji segmenti su "zabranjeni" za spajanje
        # To su segmenti ISTE BOJE koji se nalaze na susednim pozicijama na rubu
        self.segment_neighbors = {}
        all_segments = list(set(self.root_segments.values()))

        for sid in all_segments:
            self.segment_neighbors[sid] = set()

        # Logika: Dva segmenta su "susedi" ako su iste boje
        # i ako između njih nema drugog segmenta iste boje
        for r_pos, seg_id in self.root_segments.items():
            color = self.matrix[r_pos[0]][r_pos[1]]

            # Gledamo malo dalje (povećavamo range na npr. 4 ili 5)
            # da preskočimo segment suprotne boje na ćošku
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    nx, ny = r_pos[0] + dx, r_pos[1] + dy
                    if (nx, ny) in self.root_segments:
                        other_id = self.root_segments[(nx, ny)]
                        other_color = self.matrix[nx][ny]

                        # Ako je iste boje, a različit segment -> to je "susedna" ivica
                        if other_id != seg_id and color == other_color:
                            self.segment_neighbors[seg_id].add(other_id)


    def drawMatrix(self):
        for i in range(self.dim):
            for j in range(self.dim):
                print(f"{self.matrix[i][j]:3}", end=" ")

            print()

    def X(self, x):
        return x + 1
    
    def Y(self, y):
        return chr(ord('A') + y)
    
    def move(self, x, y):
        self.moveCount += 1
        self.moves.append((x, y)) # da cuva koordinate; bitno zbog algoritma
        return [self.X(x), self.Y(y)] # za prikaz

    def modifyArray(self, x, y, player):
        # pretpostavlja da su x i y dobri, proverava se van
        if 0 <= x < self.dim and 0 <= y < self.dim:
            self.matrix[x][y] = player

    def apply_move(self, x, y, player):
        if not (0 <= x < self.dim and 0 <= y < self.dim):
            return False
        if self.matrix[x][y] != 0:
            return False

        prev_val = self.matrix[x][y]
        prev_game_over = self.game_over
        prev_winner = self.winner
        prev_move_count = self.moveCount
        prev_moves_len = len(self.moves)

        self._history.append((x, y, prev_val, prev_game_over, prev_winner, prev_move_count, prev_moves_len))
        self.matrix[x][y] = player
        self.moveCount += 1
        self.moves.append((x, y))
        self.game_over = False
        self.winner = None
        return True

    def undo_move(self):
        if not self._history:
            return False

        x, y, prev_val, prev_game_over, prev_winner, prev_move_count, prev_moves_len = self._history.pop()
        self.matrix[x][y] = prev_val
        self.game_over = prev_game_over
        self.winner = prev_winner
        self.moveCount = prev_move_count
        if len(self.moves) > prev_moves_len:
            del self.moves[prev_moves_len:]
        return True


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

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.dim and 0 <= ny < self.dim:
                nval = self.matrix[nx][ny]

                if nval == 0 or nval == ' ':
                    continue

                # LOGIKA POVEZIVANJA:
                # 1. Ako je trenutno polje KOREN (negativno):
                if val < 0:
                    # Može se povezati SAMO sa IGRAČEM iste boje
                    if nval == abs(val):
                        neighbors.append((nx, ny))

                # 2. Ako je trenutno polje IGRAČ (pozitivno):
                else:
                    # Može se povezati sa drugim IGRAČEM iste boje
                    if nval == val:
                        neighbors.append((nx, ny))
                    # ILI sa KORENOM iste boje (nval je negativan, npr. -1 za igrača 1)
                    elif nval < 0 and abs(nval) == val:
                        neighbors.append((nx, ny))

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
        id1 = self.root_segments.get((x1, y1))
        id2 = self.root_segments.get((x2, y2))

        if id1 is None or id2 is None:
            return False

            # ako su susedni segmenti, NE sme biti kraj igre
        if id2 in self.segment_neighbors.get(id1, set()):
            return False

        # Pobeda je ako su koreni iz različitih grupa (segmenata)
        return id1 != id2

    def isRoot(self, x, y):
        val = self.matrix[x][y]
        # Proveravamo da li je int i da li je negativan
        return isinstance(val, int) and val < 0

    # provera da li je kraj igre - DPS
    def isGoal(self):
        # prerano za proveru
        #if self.moveCount <= (2 * (self.size - 1) - 1):
            #return False

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

                    # PROVERA: da li je root i nije početni root
                    if self.isRoot(nx, ny) and (nx, ny) != (rx, ry):
                        # Proveri da li su susedni po matrici – ako jesu, ne može kraj

                        if self.isRealEndRoot(rx, ry, nx, ny):
                            self.game_over = True
                            self.winner = abs(self.matrix[x][y])
                            return True
                        visited_global.add((nx, ny))
                        continue

                    # dodajemo suseda u stack za dalji DFS
                    stack.append((nx, ny))
                #print()

        # ako nijedna komponenta nije dala kraj igre
        return False

    def get_valid_moves(self):
        """Vraća listu (x, y) za sva slobodna polja u matrici (gde je 0)."""
        moves = []
        for i, j in self.playable_positions:
            if self.matrix[i][j] == 0:
                moves.append((i, j))
        return moves

    def hash(self):
        return hash(str(self.matrix))

def number_to_position(number, board_size):
        column_lengths = []
        
        for i in range(board_size):
            column_lengths.append(board_size + i)
        
        for i in range(board_size - 2, -1, -1):
            column_lengths.append(board_size + i)

        remaining = number

        j=1
        for col in range(len(column_lengths)):
            col_length = column_lengths[col]
            if remaining < col_length:
                # col je X, row je Y
                # Pomeraj (offset) je ključan da bi matrica bila centrirana
                row_offset = max(0, col - (board_size - 1))
                row = remaining + row_offset

                # Dodajemo +1 da bismo izbegli same ivice gde su koreni (0-ti red/kolona)
                # ali pazimo da ne preskočimo susedstvo
                return (row + 1, col + 1)
            remaining -= col_length
        return (-1, -1)


def position_to_edge_id(row, col, board_size):
    """Vraća edge_id na osnovu (row, col) koordinata matrice."""
    # Ovo je malo teže izračunati inverzno, pa je najlakše pretražiti:
    # (Pošto broj polja nije velik, ovo je prihvatljivo)

    # Maksimalni mogući ID zavisi od veličine table.
    # Formula za ukupan broj polja u heksagonu (Atoll): 3*n*(n-1) + 1 ?
    # Jednostavnije: prođemo kroz sve moguće ID-eve dok ne nađemo onaj koji daje (row, col)

    # Gruba procena max ID-a (size=9 ima manje od 300 polja)
    max_id = 400
    for i in range(max_id):
        r, c = number_to_position(i, board_size)
        if r == row and c == col:
            return i
    return None

def debug_segments(self):
    print("\n--- MAPA SEGMENATA (Koreni na rubu) ---")
    for i in range(self.dim):
        row_str = ""
        for j in range(self.dim):
            val = self.matrix[i][j]
            if (i, j) in self.root_segments:
                # Ispisujemo ID segmenta (npr. S1, S2...)
                row_str += f"S{self.root_segments[(i, j)]:<2}"
            elif val == ' ':
                row_str += " . "
            elif val == 0:
                row_str += " 0 "
            else:
                # Igrači (1 ili 2)
                row_str += f" P{val}"
        print(row_str)
    print("Susedstva:", self.segment_neighbors)
    print("---------------------------------------\n")
