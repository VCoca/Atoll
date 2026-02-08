def heuristic(board, player):
    if board.isGoal():
        # Ako je trenutni igrač upravo pobedio
        # (ovde treba biti pažljiv ko je odigrao poslednji potez)
        return 1000 if board.winner == player else -1000

    score = 0
    opponent = 2 if player == 1 else 1

    # Jednostavna heuristika: koliko različitih segmenata dodiruju figure igrača
    # Možeš meriti i dužinu najdužeg lanca.
    score += count_connected_segments(board, player) * 50
    score -= count_connected_segments(board, opponent) * 80  # Prioritet na blokiranju

    # promena od board.size zbog konzistencije
    center = board.dim // 2

    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player:
                dist_to_center = abs(i - center) + abs(j - center)
                score += (board.size - dist_to_center) * 0.1

    return score


def count_connected_segments(board, player):
    visited_cells = set()
    best_connection_value = 0

    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player and (i, j) not in visited_cells:
                queue = [(i, j)]
                visited_cells.add((i, j))
                touched_segments = set()

                while queue:
                    cx, cy = queue.pop(0)
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

    return best_connection_value