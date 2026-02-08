from collections import deque

INF = 10 ** 9
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]


def heuristic(board, player):
    if board.isGoal():
        # Ako je trenutni igrač upravo pobedio
        return 100000 if board.winner == player else -100000

    opponent = 2 if player == 1 else 1

    # Kratkorocne pretnje (pobeda u 1 potezu)
    player_wins = _count_immediate_wins(board, player)
    opponent_wins = _count_immediate_wins(board, opponent)
    if player_wins > 0:
        return 90000 + player_wins * 1000
    if opponent_wins > 0:
        return -90000 - opponent_wins * 1000

    score = 0

    # Povezanost sa segmentima korena
    p_best_pairs, p_total_segments = count_connected_segments(board, player)
    o_best_pairs, o_total_segments = count_connected_segments(board, opponent)

    score += p_best_pairs * 600
    score -= o_best_pairs * 700

    # Dodirivanje segmenata je korisno, ali ne sme da dominira pocetnu igru
    score += p_total_segments * 40
    score -= o_total_segments * 50

    # Lokalni potencijal spajanja preko praznih polja
    score += _connection_potential(board, player) * 40
    score -= _connection_potential(board, opponent) * 50

    # Pretnja "prave linije": dugi, otvoreni lanci koji prave direktan prolaz
    score += _straight_line_threat(board, player) * 60
    score -= _straight_line_threat(board, opponent) * 90

    # Rani game: kazna za "lepljenje" uz korene bez razvijanja lanca
    if board.moveCount < 8:
        score -= _edge_hugging_penalty(board, player) * 120
        score += _edge_hugging_penalty(board, opponent) * 120

    # Rani game: prepoznaj "pravu liniju" (kratak put izmedju segmenata)
    if board.moveCount < 12:
        p_min_dist = _min_connection_distance(board, player)
        o_min_dist = _min_connection_distance(board, opponent)

        if p_min_dist is not None:
            score += (max(0, 16 - p_min_dist) ** 3) * 10
        if o_min_dist is not None:
            score -= (max(0, 16 - o_min_dist) ** 4) * 15

    score -= _detect_opponent_forks(board, opponent)

    # Adaptivna odbrana:
    # - Ako protivnik gura centar, vise vrednujemo blokadu njihovih root-ova
    # - Ako protivnik gradi po ivicama, kaznjavamo njihov edge progres
    o_center_pressure = _center_pressure(board, opponent)
    score += _block_root_adjacency(board, player) * (30 + o_center_pressure * 4)
    score += _targeted_edge_blocking(board, player) * 90
    score -= _edge_pressure_total(board, opponent) * 60
    score += _edge_pressure_total(board, player) * 20

    # Prioritet: blokiranje pristupa protivnika ka ivicama (root-ovima),
    # i kada nisu povezani sa drugim root-om.
    opp_root_connected, opp_connect_in_one, opp_entry_cells = _root_access_threats(board, opponent)
    score -= opp_root_connected * 180
    score -= opp_connect_in_one * 220
    score -= opp_entry_cells * 35
    score += _root_entry_blocking(board, player) * 160

    # Blaga preferencija ka centru (manja tezina)
    center = board.dim // 2
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player:
                dist_to_center = abs(i - center) + abs(j - center)
                score += (board.size - dist_to_center) * 0.05
            elif board.matrix[i][j] == opponent:
                dist_to_center = abs(i - center) + abs(j - center)
                score -= (board.size - dist_to_center) * 0.05

    return score



def count_connected_segments(board, player):
    visited_cells = set()
    best_connection_value = 0
    total_segments_touched = 0

    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player and (i, j) not in visited_cells:
                queue = deque([(i, j)])
                visited_cells.add((i, j))
                touched_segments = set()

                while queue:
                    cx, cy = queue.popleft()
                    neighbors = board.checkNeighbors(cx, cy)
                    for nx, ny in neighbors:
                        val = board.matrix[nx][ny]
                        if isinstance(val, int) and val < 0 and abs(val) == player:
                            seg_id = board.root_segments.get((nx, ny))
                            if seg_id is not None:
                                touched_segments.add(seg_id)
                        elif val == player and (nx, ny) not in visited_cells:
                            visited_cells.add((nx, ny))
                            queue.append((nx, ny))

                # FILTRIRANJE: Proveravamo koliko 'validnih' segmenata ovaj lanac spaja
                if len(touched_segments) > 1:
                    valid_pairs = 0
                    segments_list = list(touched_segments)
                    for idx, s1 in enumerate(segments_list):
                        for s2 in segments_list[idx+1:]:
                            # Proveravamo tvoj novi rečnik susedstva!
                            # Ako s2 nije u susedstvu od s1, to je put ka pobedi
                            if s2 not in board.segment_neighbors.get(s1, set()):
                                valid_pairs += 1

                    best_connection_value = max(best_connection_value, valid_pairs)
                elif len(touched_segments) == 1:
                    # Stimulišemo AI da bar krene od nekog segmenta
                    best_connection_value = max(best_connection_value, 0.5)
                total_segments_touched += len(touched_segments)

    return best_connection_value, total_segments_touched


def _connection_potential(board, player):
    if not board.moves:
        return 0
    opponent = 2 if player == 1 else 1
    total = 0
    for x, y in _candidate_moves(board):
        segs = set()
        friendly_adj = 0
        for dx, dy in DIRECTIONS:
            nx = x + dx
            ny = y + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            val = board.matrix[nx][ny]
            if val == player:
                friendly_adj += 1
            elif isinstance(val, int) and val < 0 and abs(val) == player:
                seg_id = board.root_segments.get((nx, ny))
                if seg_id is not None:
                    segs.add(seg_id)
            elif val == opponent:
                friendly_adj -= 1
        if len(segs) >= 2:
            segs_list = list(segs)
            for i in range(len(segs_list)):
                for j in range(i + 1, len(segs_list)):
                    s1 = segs_list[i]
                    s2 = segs_list[j]
                    if s2 not in board.segment_neighbors.get(s1, set()):
                        total += 3
        elif len(segs) == 1 and friendly_adj > 1:
            total += 1
    return total


def _candidate_moves(board):
    moves = board.get_valid_moves()
    if not board.moves:
        return moves
    filtered = []
    for x, y in moves:
        near = False
        for dx, dy in DIRECTIONS:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < board.dim and 0 <= ny < board.dim:
                val = board.matrix[nx][ny]
                if val != 0 and val != ' ':
                    near = True
                    break
        if near:
            filtered.append((x, y))
    return filtered


def _count_immediate_wins(board, player):
    wins = 0
    for move in _candidate_moves(board):
        board.apply_move(move[0], move[1], player)
        try:
            if board.isGoal() and board.winner == player:
                wins += 1
        finally:
            board.undo_move()
    return wins


def _edge_hugging_penalty(board, player):
    penalty = 0
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            root_adj = 0
            friendly_adj = 0
            for dx, dy in DIRECTIONS:
                nx = i + dx
                ny = j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if isinstance(val, int) and val < 0 and abs(val) == player:
                    root_adj += 1
                elif val == player:
                    friendly_adj += 1
            if root_adj > 0 and friendly_adj <= 1:
                penalty += 1
    return penalty


def _straight_line_threat(board, player):
    # Detect long, open-ended straight chains that can become a fast win path.
    axis_dirs = [(1, 0), (0, 1), (1, 1)]
    total = 0

    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue

            for dx, dy in axis_dirs:
                # Only start counting if this is the beginning of the chain
                px, py = i - dx, j - dy
                if 0 <= px < board.dim and 0 <= py < board.dim:
                    if board.matrix[px][py] == player:
                        continue

                length = 0
                x, y = i, j
                while 0 <= x < board.dim and 0 <= y < board.dim and board.matrix[x][y] == player:
                    length += 1
                    x += dx
                    y += dy

                if length < 3:
                    continue

                end1 = (i - dx, j - dy)
                end2 = (x, y)  # first cell after the chain

                open1 = _is_open_or_root(board, player, end1)
                open2 = _is_open_or_root(board, player, end2)
                if not (open1 or open2):
                    continue

                open_ends = (1 if open1 else 0) + (1 if open2 else 0)
                access = 0
                if open1:
                    access += _root_proximity(board, player, end1)
                if open2:
                    access += _root_proximity(board, player, end2)

                base = length * length
                if open_ends == 2:
                    total += base * (1 + 0.5 * access)
                else:
                    total += base * 0.6 * (1 + 0.5 * access)

    return total


def _is_open_or_root(board, player, pos):
    x, y = pos
    if not (0 <= x < board.dim and 0 <= y < board.dim):
        return False
    val = board.matrix[x][y]
    if val == 0:
        return True
    return isinstance(val, int) and val < 0 and abs(val) == player


def _root_proximity(board, player, pos):
    x, y = pos
    # If this is already a root cell, treat as strong access
    val = board.matrix[x][y] if (0 <= x < board.dim and 0 <= y < board.dim) else None
    if isinstance(val, int) and val < 0 and abs(val) == player:
        return 1

    # Check if any player root is within 2 steps
    for dx, dy in DIRECTIONS:
        for step in (1, 2):
            nx = x + dx * step
            ny = y + dy * step
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            nval = board.matrix[nx][ny]
            if isinstance(nval, int) and nval < 0 and abs(nval) == player:
                return 1
    return 0


def _min_connection_distance(board, player):
    segments = {}
    for (x, y), seg_id in board.root_segments.items():
        val = board.matrix[x][y]
        if isinstance(val, int) and val < 0 and abs(val) == player:
            segments.setdefault(seg_id, []).append((x, y))

    seg_ids = list(segments.keys())
    if len(seg_ids) < 2:
        return None

    best = None
    for i in range(len(seg_ids)):
        for j in range(i + 1, len(seg_ids)):
            s1 = seg_ids[i]
            s2 = seg_ids[j]
            if s2 in board.segment_neighbors.get(s1, set()):
                continue
            dist = _min_dist_between_sets(board, player, segments[s1], segments[s2])
            if dist is not None:
                if best is None or dist < best:
                    best = dist
    return best


def _min_dist_between_sets(board, player, starts, targets):
    from collections import deque
    opponent = 2 if player == 1 else 1
    target_set = set(targets)
    inf = 10 ** 9
    dist = [[inf for _ in range(board.dim)] for _ in range(board.dim)]
    dq = deque()

    for x, y in starts:
        dist[x][y] = 0
        dq.appendleft((x, y))

    while dq:
        x, y = dq.popleft()
        d = dist[x][y]
        if (x, y) in target_set:
            return d

        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim) or board.matrix[nx][ny] == ' ':
                continue

            val = board.matrix[nx][ny]
            if val == opponent or (isinstance(val, int) and val < 0 and abs(val) == opponent):
                continue

            # --- KLJUČNA IZMENA: CENA PRELASKA ---
            if val == player or (isinstance(val, int) and val < 0 and abs(val) == player):
                cost = 0
            else:
                # Proveravamo da li je ovo polje "Most" (povezuje dve tvoje figure)
                # Ako jeste, prelazak je "jeftiniji" jer je to kritična tačka
                friendly_neighbors = 0
                for ddx, ddy in DIRECTIONS:
                    nnx, nny = nx + ddx, ny + ddy
                    if 0 <= nnx < board.dim and 0 <= nny < board.dim:
                        if board.matrix[nnx][nny] == player:
                            friendly_neighbors += 1

                cost = 0.6 if friendly_neighbors >= 2 else 1.0

            nd = d + cost
            if nd < dist[nx][ny]:
                dist[nx][ny] = nd
                if cost == 0:
                    dq.appendleft((nx, ny))
                else:
                    dq.append((nx, ny))
    return None


def _center_pressure(board, player):
    center = board.dim // 2
    radius = max(1, board.size // 2)
    count = 0
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player:
                dist = abs(i - center) + abs(j - center)
                if dist <= radius:
                    count += 1
    return count


def _block_root_adjacency(board, player):
    opponent = 2 if player == 1 else 1
    score = 0
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            for dx, dy in DIRECTIONS:
                nx = i + dx
                ny = j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if isinstance(val, int) and val < 0 and abs(val) == opponent:
                    score += 1
    return score


def _edge_progression(board, player):
    opponent = 2 if player == 1 else 1
    progress = 0
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            root_adj = 0
            empty_adj = 0
            for dx, dy in DIRECTIONS:
                nx = i + dx
                ny = j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if val == 0:
                    empty_adj += 1
                elif isinstance(val, int) and val < 0 and abs(val) == player:
                    root_adj += 1
                elif val == opponent or (isinstance(val, int) and val < 0 and abs(val) == opponent):
                    pass
            if root_adj > 0 and empty_adj > 0:
                progress += 1
    return progress


def _edge_pressure_map(board, player):
    pressure = {}
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            for dx, dy in DIRECTIONS:
                for step in (1, 2):
                    nx = i + dx * step
                    ny = j + dy * step
                    if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                        continue
                    val = board.matrix[nx][ny]
                    if isinstance(val, int) and val < 0 and abs(val) == player:
                        seg_id = board.root_segments.get((nx, ny))
                        if seg_id is not None:
                            weight = 2 if step == 1 else 1
                            pressure[seg_id] = pressure.get(seg_id, 0) + weight
    return pressure


def _edge_pressure_total(board, player):
    m = _edge_pressure_map(board, player)
    total = 0
    for v in m.values():
        total += v
    return total


def _targeted_edge_blocking(board, player):
    opponent = 2 if player == 1 else 1
    opp_pressure = _edge_pressure_map(board, opponent)
    if not opp_pressure:
        return 0

    # Focus on the top pressured segments (edges the opponent is going for)
    top_segments = sorted(opp_pressure.items(), key=lambda kv: kv[1], reverse=True)[:3]
    top_ids = set(seg_id for seg_id, _ in top_segments)

    block_score = 0
    # Reward our stones adjacent to those specific segments
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            for dx, dy in DIRECTIONS:
                nx = i + dx
                ny = j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if isinstance(val, int) and val < 0 and abs(val) == opponent:
                    seg_id = board.root_segments.get((nx, ny))
                    if seg_id in top_ids:
                        block_score += 1

    # Penalize if opponent pressure is high and we have not blocked those segments
    total_pressure = sum(v for _, v in top_segments)
    if total_pressure > 0:
        block_score -= max(0, total_pressure - block_score)

    return block_score


def _root_access_threats(board, player):
    connected = set()
    entry_cells = set()

    # Root polja su negativni int-ovi
    for (rx, ry) in board.root_segments.keys():
        val = board.matrix[rx][ry]
        if not (isinstance(val, int) and val < 0 and abs(val) == player):
            continue
        for dx, dy in DIRECTIONS:
            nx = rx + dx
            ny = ry + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            nval = board.matrix[nx][ny]
            if nval == player:
                connected.add((nx, ny))
            elif nval == 0:
                entry_cells.add((nx, ny))

    # Potez kojim protivnik može da se "priključi" root-u u 1 potezu
    connect_in_one = 0
    for ex, ey in entry_cells:
        for dx, dy in DIRECTIONS:
            nx = ex + dx
            ny = ey + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            if board.matrix[nx][ny] == player:
                connect_in_one += 1
                break

    return len(connected), connect_in_one, len(entry_cells)


def _root_entry_blocking(board, player):
    opponent = 2 if player == 1 else 1
    blocked = set()
    for (rx, ry) in board.root_segments.keys():
        val = board.matrix[rx][ry]
        if not (isinstance(val, int) and val < 0 and abs(val) == opponent):
            continue
        for dx, dy in DIRECTIONS:
            nx = rx + dx
            ny = ry + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            if board.matrix[nx][ny] == player:
                blocked.add((nx, ny))
    return len(blocked)


def _detect_opponent_forks(board, opponent):
    fork_score = 0
    candidate_moves = _candidate_moves(board)

    for x, y in candidate_moves:
        board.apply_move(x, y, opponent)
        try:
            threat_count = 0
            segments = board.root_segments
            player_segs = list(set(
                sid for pos, sid in segments.items()
                if abs(board.matrix[pos[0]][pos[1]]) == opponent
            ))

            for i in range(len(player_segs)):
                for j in range(i + 1, len(player_segs)):
                    s1, s2 = player_segs[i], player_segs[j]
                    if s2 in board.segment_neighbors.get(s1, set()):
                        continue

                    d = _min_dist_between_sets(
                        board, opponent,
                        [p for p, sid in segments.items() if sid == s1],
                        [p for p, sid in segments.items() if sid == s2]
                    )

                    if d is not None and d <= 1.5:
                        threat_count += 1
                        if threat_count >= 2:
                            fork_score += 5000
                            break
                if threat_count >= 2:
                    break
        finally:
            board.undo_move()

    return fork_score
