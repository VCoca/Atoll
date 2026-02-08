from collections import deque

INF = 10 ** 9
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]


def heuristic(board, player):
    """Glavna funkcija za evaluaciju pozicije."""
    if board.isGoal():
        # ako je trenutni igrač upravo pobedio
        return 100000 if board.winner == player else -100000

    opponent = 2 if player == 1 else 1

    # blize pretnje (pobeda u 1 potezu)
    player_wins = _count_immediate_wins(board, player)
    opponent_wins = _count_immediate_wins(board, opponent)
    if player_wins > 0:
        return 90000 + player_wins * 1000
    if opponent_wins > 0:
        return -90000 - opponent_wins * 1000

    score = 0

    # povezanost sa segmentima korena
    p_best_pairs, p_total_segments = _count_connected_segments(board, player)
    o_best_pairs, o_total_segments = _count_connected_segments(board, opponent)
    score += p_best_pairs * 600
    score -= o_best_pairs * 700
    score += p_total_segments * 40
    score -= o_total_segments * 50

    # lokalni potencijal spajanja preko praznih polja
    score += _connection_potential(board, player) * 40
    score -= _connection_potential(board, opponent) * 50
    
    # pretnja "prave linije": dugi lanci koji prave direktan prolaz
    score += _straight_line_threat(board, player) * 60
    score -= _straight_line_threat(board, opponent) * 90
    
    # detekcija mostova koji su skoro gotovi (spojeni suprotni ivice)
    score += _evaluate_bridge_progress(board, player) * 150
    score -= _evaluate_bridge_progress(board, opponent) * 200
    
    # blokiraj DESTINACIJU gde protivnik zavrašava most, ne početak
    score += _block_bridge_completion(board, player, opponent) * 300

    # kazna za "lepljenje" uz korene bez razvijanja lanca
    if board.moveCount < 8:
        score -= _edge_hugging_penalty(board, player) * 120
        score += _edge_hugging_penalty(board, opponent) * 120

    # prepoznaj "pravu liniju" (kratak put izmedju segmenata)
    if board.moveCount < 12:
        p_min_dist = _min_connection_distance(board, player)
        o_min_dist = _min_connection_distance(board, opponent)
        if p_min_dist is not None:
            score += (max(0, 16 - p_min_dist) ** 3) * 10
        if o_min_dist is not None:
            score -= (max(0, 16 - o_min_dist) ** 4) * 15

    # fork detekcija
    score -= _detect_opponent_forks(board, opponent)

    # odbrana
    o_center_pressure = _center_pressure(board, opponent)
    score += _block_root_adjacency(board, player) * (15 + o_center_pressure * 2)
    score += _targeted_edge_blocking(board, player) * 40

    # pretnje za pristup root
    opp_root_connected, opp_connect_in_one, opp_entry_cells = _root_access_threats(board, opponent)
    score -= opp_root_connected * 80  # Smanjeno sa 180
    score -= opp_connect_in_one * 100  # Smanjeno sa 220
    score -= opp_entry_cells * 15  # Smanjeno sa 35
    score += _root_entry_blocking(board, player) * 60  # Smanjeno sa 160

    # blaga preferencija za centar (bolja kontrola)
    score += _evaluate_center_control(board, player) * 0.05
    score -= _evaluate_center_control(board, opponent) * 0.05

    return score

def _count_connected_segments(board, player):
    """Broji validne konekcije između segmenata (ne-susedni segmenti spojeni lancima)."""
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

                # broji validne parove
                if len(touched_segments) > 1:
                    valid_pairs = 0
                    segments_list = list(touched_segments)
                    for idx, s1 in enumerate(segments_list):
                        for s2 in segments_list[idx+1:]:
                            if s2 not in board.segment_neighbors.get(s1, set()):
                                valid_pairs += 1
                    best_connection_value = max(best_connection_value, valid_pairs)
                elif len(touched_segments) == 1:
                    best_connection_value = max(best_connection_value, 0.5)
                total_segments_touched += len(touched_segments)

    return best_connection_value, total_segments_touched


def _connection_potential(board, player):
    """Evaluira potencijal za kreiranje konekcija na praznim poljima."""
    if not board.moves:
        return 0
    
    opponent = 2 if player == 1 else 1
    total = 0
    
    for x, y in _get_candidate_moves(board):
        segs = set()
        friendly_adj = 0
        
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
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
        
        # nagrada za spajanje ne-susednih segmenata
        if len(segs) >= 2:
            segs_list = list(segs)
            for i in range(len(segs_list)):
                for j in range(i + 1, len(segs_list)):
                    s1, s2 = segs_list[i], segs_list[j]
                    if s2 not in board.segment_neighbors.get(s1, set()):
                        total += 3
        elif len(segs) == 1 and friendly_adj > 1:
            total += 1
    
    return total

def _straight_line_threat(board, player):
    """
    Detektuje pozicije blizu pobede gde igrač ima put koji skoro spaja dve ne-susedne ivice.
    Ovo je kritično za prepoznavanje napada ravnom linijom u Atollu.
    """
    threat_score = 0
    
    # nadje sve segmente za ovog igrača
    player_segments = {}
    for pos, seg_id in board.root_segments.items():
        val = board.matrix[pos[0]][pos[1]]
        if isinstance(val, int) and val < 0 and abs(val) == player:
            if seg_id not in player_segments:
                player_segments[seg_id] = []
            player_segments[seg_id].append(pos)
    
    # za svaki lanac, nadje koje segmente spaja
    chains_connecting_segments = []
    visited = set()
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player and (i, j) not in visited:
                # BFS
                chain = set()
                touched_segments = set()
                queue = deque([(i, j)])
                visited.add((i, j))
                
                while queue:
                    cx, cy = queue.popleft()
                    chain.add((cx, cy))
                    
                    for nx, ny in board.checkNeighbors(cx, cy):
                        val = board.matrix[nx][ny]
                        
                        if isinstance(val, int) and val < 0 and abs(val) == player:
                            seg_id = board.root_segments.get((nx, ny))
                            if seg_id is not None:
                                touched_segments.add(seg_id)
                        
                        elif val == player and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                
                if len(touched_segments) >= 2:
                    chains_connecting_segments.append((chain, touched_segments))
    
    for chain, segments in chains_connecting_segments:
        segments_list = list(segments)
        
        for i in range(len(segments_list)):
            for j in range(i + 1, len(segments_list)):
                s1, s2 = segments_list[i], segments_list[j]
                
                # Zanima nas samo ne-susedni segmenti
                if s2 in board.segment_neighbors.get(s1, set()):
                    continue
                
                min_dist = _min_dist_between_segments(board, player,
                                                       player_segments[s1],
                                                       player_segments[s2])
                
                if min_dist is not None:
                    # dodatna pretnja zavisi koliko je daleko od pobede
                    if min_dist <= 1.0:
                        threat_score += 50 
                    elif min_dist <= 2.0:
                        threat_score += 20 
                    elif min_dist <= 3.0:
                        threat_score += 8
                    elif min_dist <= 5.0:
                        threat_score += 3
    
    return threat_score


def _count_immediate_wins(board, player):
    """Broji broj pobedničkih poteza koji su dostupni. Proverava SVE poteze da ne propusti pobedu."""
    wins = 0
    # koristi SVE validne poteze, ne samo kandidate
    # malo neoptimizovano, može se unaprediti
    all_moves = board.get_valid_moves()
    
    for move in all_moves:
        board.apply_move(move[0], move[1], player)
        try:
            if board.isGoal() and board.winner == player:
                wins += 1
        finally:
            board.undo_move()
    return wins


def _detect_opponent_forks(board, opponent):
    """Detektuje pozicije gde protivnik može da kreira vise pretnji."""
    fork_score = 0
    
    for x, y in _get_candidate_moves(board):
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

                    d = _min_dist_between_segments(
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

def _block_root_adjacency(board, player):
    """Skor za blokiranje protivničkog pristupa njihovim root segmentima."""
    opponent = 2 if player == 1 else 1
    score = 0
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            for dx, dy in DIRECTIONS:
                nx, ny = i + dx, j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if isinstance(val, int) and val < 0 and abs(val) == opponent:
                    score += 1
    
    return score


def _targeted_edge_blocking(board, player):
    """
    Blokira najugroženije protivnikove segmente, ali SAMO ako su deo pobedničke pretnje.
    Ne troši poteze na blokiranje segmenata susednih onima koje su vec spojili.
    """
    opponent = 2 if player == 1 else 1
    opp_pressure = _calculate_edge_pressure(board, opponent)
    
    if not opp_pressure:
        return 0
    
    connected_segments = set()
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == opponent:
                for nx, ny in board.checkNeighbors(i, j):
                    val = board.matrix[nx][ny]
                    if isinstance(val, int) and val < 0 and abs(val) == opponent:
                        seg_id = board.root_segments.get((nx, ny))
                        if seg_id is not None:
                            connected_segments.add(seg_id)
    
    # filtrira mapu pritiska na samo pobednicke pretnje
    winning_pressure = {}
    for seg_id, pressure in opp_pressure.items():
        is_winning_threat = False
        for connected_seg in connected_segments:
            if connected_seg != seg_id and seg_id not in board.segment_neighbors.get(connected_seg, set()):
                is_winning_threat = True
                break
        
        # takođe je pretnja ako protivnik jos nije spojio nijedan segment
        if len(connected_segments) == 0 or is_winning_threat:
            winning_pressure[seg_id] = pressure
    
    if not winning_pressure:
        return 0

    top_segments = sorted(winning_pressure.items(), key=lambda kv: kv[1], reverse=True)[:3] # 3 najugroženija protivnička segmenta
    top_ids = set(seg_id for seg_id, _ in top_segments)

    block_score = 0
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            for dx, dy in DIRECTIONS:
                nx, ny = i + dx, j + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                val = board.matrix[nx][ny]
                if isinstance(val, int) and val < 0 and abs(val) == opponent:
                    seg_id = board.root_segments.get((nx, ny))
                    if seg_id in top_ids:
                        block_score += 1

    # kazna ako je pritisak visok a nismo blokirali te segmente
    total_pressure = sum(v for _, v in top_segments)
    if total_pressure > 0:
        block_score -= max(0, total_pressure - block_score)

    return block_score


def _root_access_threats(board, player):
    """Analizira protivnikov pristup root segmentima."""
    connected = set()
    entry_cells = set()

    for (rx, ry) in board.root_segments.keys():
        val = board.matrix[rx][ry]
        if not (isinstance(val, int) and val < 0 and abs(val) == player):
            continue
        
        for dx, dy in DIRECTIONS:
            nx, ny = rx + dx, ry + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            nval = board.matrix[nx][ny]
            if nval == player:
                connected.add((nx, ny))
            elif nval == 0:
                entry_cells.add((nx, ny))

    # broji polja gde se protivnik moze spojiti u jednom potezu
    connect_in_one = 0
    for ex, ey in entry_cells:
        for dx, dy in DIRECTIONS:
            nx, ny = ex + dx, ey + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            if board.matrix[nx][ny] == player:
                connect_in_one += 1
                break

    return len(connected), connect_in_one, len(entry_cells)


def _root_entry_blocking(board, player):
    """
    Skor za blokiranje ulaznih tacaka protivnika ka root-ovima.
    Broji SAMO blokade koje spreacavaju konekcije ka ne-susednim segmentima.
    """
    opponent = 2 if player == 1 else 1
    blocked = set()
    
    # nadje pozicije segmenata protivnika
    opp_segment_positions = {}
    for pos, seg_id in board.root_segments.items():
        val = board.matrix[pos[0]][pos[1]]
        if isinstance(val, int) and val < 0 and abs(val) == opponent:
            if seg_id not in opp_segment_positions:
                opp_segment_positions[seg_id] = []
            opp_segment_positions[seg_id].append(pos)
    
    # nadje koje segmente je protivnik vec spojio
    connected_segments = set()
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == opponent:
                for nx, ny in board.checkNeighbors(i, j):
                    val = board.matrix[nx][ny]
                    if isinstance(val, int) and val < 0 and abs(val) == opponent:
                        seg_id = board.root_segments.get((nx, ny))
                        if seg_id is not None:
                            connected_segments.add(seg_id)
    
    # blokira samo ulaze ka segmentima koji bi kreirali pobednicke konekcije
    for (rx, ry) in board.root_segments.keys():
        val = board.matrix[rx][ry]
        if not (isinstance(val, int) and val < 0 and abs(val) == opponent):
            continue
        
        seg_id = board.root_segments.get((rx, ry))
        
        # proverava da li blokiranje ovog segmenta sprečava pobednicku konekciju
        is_winning_threat = False
        for connected_seg in connected_segments:
            if connected_seg != seg_id and seg_id not in board.segment_neighbors.get(connected_seg, set()):
                is_winning_threat = True
                break
        
        # broji samo blokove na pobednickim pretnjama
        if is_winning_threat:
            for dx, dy in DIRECTIONS:
                nx, ny = rx + dx, ry + dy
                if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                    continue
                if board.matrix[nx][ny] == player:
                    blocked.add((nx, ny))
    
    return len(blocked)

def _edge_hugging_penalty(board, player):
    """Kazna za kamenove koji samo dodiruju root-ove bez proširivanja lanca."""
    penalty = 0
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            
            root_adj = 0
            friendly_adj = 0
            
            for dx, dy in DIRECTIONS:
                nx, ny = i + dx, j + dy
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


def _min_connection_distance(board, player):
    """Nadje minimalnu distancu između bilo koja dva ne-susedna segmenta."""
    player_segments = {}
    for pos, seg_id in board.root_segments.items():
        val = board.matrix[pos[0]][pos[1]]
        if isinstance(val, int) and val < 0 and abs(val) == player:
            if seg_id not in player_segments:
                player_segments[seg_id] = []
            player_segments[seg_id].append(pos)

    min_dist = None
    seg_ids = list(player_segments.keys())
    
    for i in range(len(seg_ids)):
        for j in range(i + 1, len(seg_ids)):
            s1, s2 = seg_ids[i], seg_ids[j]
            if s2 in board.segment_neighbors.get(s1, set()):
                continue
            
            d = _min_dist_between_segments(board, player,
                                           player_segments[s1],
                                           player_segments[s2])
            if d is not None:
                min_dist = d if min_dist is None else min(min_dist, d)

    return min_dist

def _center_pressure(board, player):
    """Broji kamenove igrača u centralnoj regiji."""
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


def _evaluate_center_control(board, player):
    """Evaluira kontrolu centralnih polja."""
    center = board.dim // 2
    score = 0
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player:
                dist_to_center = abs(i - center) + abs(j - center)
                score += (board.size - dist_to_center)
    
    return score


def _calculate_edge_pressure(board, player):
    """Kalkulise pritisak na svaki root segment."""
    pressure = {}
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] != player:
                continue
            
            for dx, dy in DIRECTIONS:
                for step in (1, 2):
                    nx, ny = i + dx * step, j + dy * step
                    if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                        continue
                    
                    val = board.matrix[nx][ny]
                    if isinstance(val, int) and val < 0 and abs(val) == player:
                        seg_id = board.root_segments.get((nx, ny))
                        if seg_id is not None:
                            weight = 2 if step == 1 else 1
                            pressure[seg_id] = pressure.get(seg_id, 0) + weight
    
    return pressure


def _get_candidate_moves(board):
    """Uzima poteze blizu postojećih kamenova (skraćena lista poteza)."""
    moves = board.get_valid_moves()
    if not board.moves:
        return moves
    
    filtered = []
    for x, y in moves:
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < board.dim and 0 <= ny < board.dim:
                val = board.matrix[nx][ny]
                if val != 0 and val != ' ':
                    filtered.append((x, y))
                    break
    
    return filtered


def _min_dist_between_segments(board, player, seg1_positions, seg2_positions):
    """
    Kalkulise minimalnu ponderisanu distancu između dva seta segmenata.
    Koristi BFS sa cenama: 0 za igraca, 0.6 za prijateljsko prazno, 1 za neprijateljsko.
    """
    opponent = 2 if player == 1 else 1
    
    # Niz distanci
    dist = [[INF] * board.dim for _ in range(board.dim)]
    dq = deque()
    
    # Inicijalizuje od prvog segmenta
    for x, y in seg1_positions:
        dist[x][y] = 0
        dq.append((x, y))
    
    # BFS sa ponderisanim ivicama
    while dq:
        x, y = dq.popleft()
        
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                continue
            
            val = board.matrix[nx][ny]
            
            # Kalkulise cenu
            if val == player or (isinstance(val, int) and val < 0 and abs(val) == player):
                cost = 0
            elif val == opponent or (isinstance(val, int) and val < 0 and abs(val) == opponent):
                cost = 1.0
            else:  # prazno
                # Proverava prijateljske komšije da smanji cenu
                friendly_neighbors = 0
                for dx2, dy2 in DIRECTIONS:
                    nx2, ny2 = nx + dx2, ny + dy2
                    if 0 <= nx2 < board.dim and 0 <= ny2 < board.dim:
                        v = board.matrix[nx2][ny2]
                        if v == player or (isinstance(v, int) and v < 0 and abs(v) == player):
                            friendly_neighbors += 1
                
                cost = 0.6 if friendly_neighbors >= 2 else 1.0
            
            nd = dist[x][y] + cost
            if nd < dist[nx][ny]:
                dist[nx][ny] = nd
                if cost == 0:
                    dq.appendleft((nx, ny))
                else:
                    dq.append((nx, ny))
    
    # Nadje minimalnu distancu do drugog segmenta
    min_dist = None
    for x, y in seg2_positions:
        if dist[x][y] < INF:
            min_dist = dist[x][y] if min_dist is None else min(min_dist, dist[x][y])
    
    return min_dist


def _evaluate_bridge_progress(board, player):
    """
    Evaluira koliko je igrač blizu da završi pobednički most.
    Most je lanac koji spaja dve ne-susedne ivice.
    Ovo je KRITIČNO za detekciju pobedničkih strategija ravnom linijom.
    """
    # Nadje sve lance i segmente koje dodiruju
    visited = set()
    best_bridge_score = 0
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player and (i, j) not in visited:
                # BFS da nadje lanac i dotaknute segmente
                chain_cells = []
                touched_segments = set()
                queue = deque([(i, j)])
                visited.add((i, j))
                
                while queue:
                    cx, cy = queue.popleft()
                    chain_cells.append((cx, cy))
                    
                    for nx, ny in board.checkNeighbors(cx, cy):
                        val = board.matrix[nx][ny]
                        
                        if isinstance(val, int) and val < 0 and abs(val) == player:
                            seg_id = board.root_segments.get((nx, ny))
                            if seg_id is not None:
                                touched_segments.add(seg_id)
                        elif val == player and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                
                # Evaluira potencijal ovog lanca za most
                if len(touched_segments) >= 2:
                    segments_list = list(touched_segments)
                    
                    for idx1, s1 in enumerate(segments_list):
                        for s2 in segments_list[idx1 + 1:]:
                            # Zanima nas samo ne-susedni segmenti
                            if s2 in board.segment_neighbors.get(s1, set()):
                                continue
                            
                            # Ovaj lanac spaja dva ne-susedna segmenta!
                            # Skor na osnovu jake konekcije
                            chain_length = len(chain_cells)
                            
                            # Kalkulise "rupe" u lancu
                            seg1_positions = [p for p, sid in board.root_segments.items() if sid == s1]
                            seg2_positions = [p for p, sid in board.root_segments.items() if sid == s2]
                            
                            # Nadje najblize priblizavanje od lanca ka svakom segmentu
                            min_gap_to_s1 = _min_distance_from_chain_to_segment(board, chain_cells, seg1_positions)
                            min_gap_to_s2 = _min_distance_from_chain_to_segment(board, chain_cells, seg2_positions)
                            
                            total_gap = min_gap_to_s1 + min_gap_to_s2
                            
                            # Skor: duzi lanci sa manjim rupama su bolji
                            bridge_score = chain_length * 2
                            
                            if total_gap <= 0:  # Vec spojen sa oba!
                                bridge_score += 100
                            elif total_gap <= 1:  # Jedan potez od zavrsetka
                                bridge_score += 50
                            elif total_gap <= 2:
                                bridge_score += 20
                            elif total_gap <= 4:
                                bridge_score += 10
                            
                            best_bridge_score = max(best_bridge_score, bridge_score)
    
    return best_bridge_score


def _min_distance_from_chain_to_segment(board, chain_cells, segment_positions):
    """Kalkulise minimalnu distancu od bilo kog polja lanca do bilo kojeg polja segmenta."""
    min_dist = INF
    
    for cx, cy in chain_cells:
        for sx, sy in segment_positions:
            # Menhetn distanca (dovoljno dobra za proveru blizine)
            dist = abs(cx - sx) + abs(cy - sy)
            min_dist = min(min_dist, dist)
    
    # Ako su susedni (distanca 1), vec su spojeni
    return max(0, min_dist - 1)


def _block_bridge_completion(board, player, opponent):
    """
    KRITIČNO: Identifikuje i blokira DESTINACIJU protivnikovog pokušaja mosta.
    Ovo sprečava AI da troši poteze blokirajući početnu ivicu kada
    protivnik hoće da stigne do destinacijske ivice.
    
    Vraca skor koliko dobro igrač blokira završetak protivnikovog mosta.
    """
    block_score = 0
    
    # Nadje sve protivničke lance i analizira koje segmente pokušavaju da spoje
    visited = set()
    
    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == opponent and (i, j) not in visited:
                # BFS da nadje ovaj lanac
                chain_cells = []
                touched_segments = {}  # seg_id -> distanca od lanca
                queue = deque([(i, j)])
                visited.add((i, j))
                
                while queue:
                    cx, cy = queue.popleft()
                    chain_cells.append((cx, cy))
                    
                    for nx, ny in board.checkNeighbors(cx, cy):
                        val = board.matrix[nx][ny]
                        
                        if isinstance(val, int) and val < 0 and abs(val) == opponent:
                            seg_id = board.root_segments.get((nx, ny))
                            if seg_id is not None:
                                # Kalkulise koliko je lanac blizu ovom segmentu
                                if seg_id not in touched_segments:
                                    touched_segments[seg_id] = 0  # vec spojen
                        elif val == opponent and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
                
                # Za segmente koji jos nisu dotaknuti, kalkulise distancu
                for seg_id, seg_positions in _get_segment_positions(board, opponent).items():
                    if seg_id not in touched_segments:
                        dist = _min_distance_from_chain_to_segment(board, chain_cells, seg_positions)
                        touched_segments[seg_id] = dist
                
                # Identifikuje da li ovaj lanac pokusava da spoji ne-susedne segmente
                segments_list = list(touched_segments.items())
                
                for i, (s1, dist1) in enumerate(segments_list):
                    for s2, dist2 in segments_list[i + 1:]:
                        # Zanima nas samo ne-susedni segmenti
                        if s2 in board.segment_neighbors.get(s1, set()):
                            continue
                        
                        # Ovaj lanac pokušava da spoji s1 i s2!
                        # Identifikuje koji je DESTINACIJA (dalji od lanca)
                        if dist1 == 0 and dist2 > 0:
                            # Lanac spojen sa s1, priblizava se s2
                            destination_seg = s2
                            approach_distance = dist2
                        elif dist2 == 0 and dist1 > 0:
                            # Lanac spojen sa s2, priblizava se s1
                            destination_seg = s1
                            approach_distance = dist1
                        else:
                            # Lanac se približava obema ili spojen sa obema
                            destination_seg = s1 if dist1 > dist2 else s2
                            approach_distance = max(dist1, dist2)
                        
                        # Ako je protivnik blizu završetka, blokiranje destinacije je KRITIČNO
                        if approach_distance <= 3:
                            # Uzmi pozicije destinacijskog segmenta
                            dest_positions = [p for p, sid in board.root_segments.items() 
                                            if sid == destination_seg and 
                                            abs(board.matrix[p[0]][p[1]]) == opponent]
                            
                            # Broji koliko naših kamenova blokira destinaciju
                            blocks_at_destination = 0
                            for dx, dy in dest_positions:
                                for ndx, ndy in DIRECTIONS:
                                    nx, ny = dx + ndx, dy + ndy
                                    if (0 <= nx < board.dim and 0 <= ny < board.dim and
                                        board.matrix[nx][ny] == player):
                                        blocks_at_destination += 1
                            
                            # Takođe broji blokiranje u blizini (kamenovi koji blokiraju put)
                            path_blocks = 0
                            for cx, cy in chain_cells:
                                # Gleda prazna polja blizu vodećeg kraja lanca
                                for dx, dy in DIRECTIONS:
                                    nx, ny = cx + dx, cy + dy
                                    if not (0 <= nx < board.dim and 0 <= ny < board.dim):
                                        continue
                                    
                                    # Ako je ovo prazno polje bliže destinaciji, blokiranje je vredno
                                    if board.matrix[nx][ny] == 0:
                                        dist_to_dest = _min_distance_from_chain_to_segment(
                                            board, [(nx, ny)], dest_positions
                                        )
                                        if dist_to_dest < approach_distance:
                                            # Proverava da li blokiramo ovaj put
                                            for dx2, dy2 in DIRECTIONS:
                                                nx2, ny2 = nx + dx2, ny + dy2
                                                if (0 <= nx2 < board.dim and 0 <= ny2 < board.dim and
                                                    board.matrix[nx2][ny2] == player):
                                                    path_blocks += 1
                                                    break
                            
                            # Skor na osnovu hitnosti
                            if approach_distance <= 1:
                                # KRITIČNO: Jedan potez od pobede!
                                block_score += (blocks_at_destination + path_blocks) * 50
                            elif approach_distance <= 2:
                                block_score += (blocks_at_destination + path_blocks) * 20
                            else:  # approach_distance <= 3
                                block_score += (blocks_at_destination + path_blocks) * 5
    
    return block_score


def _get_segment_positions(board, player):
    """Pomocna funkcija da uzme sve pozicije za svaki segment."""
    segments = {}
    for pos, seg_id in board.root_segments.items():
        val = board.matrix[pos[0]][pos[1]]
        if isinstance(val, int) and val < 0 and abs(val) == player:
            if seg_id not in segments:
                segments[seg_id] = []
            segments[seg_id].append(pos)
    return segments
