from ai.heuristics import heuristic
import time
from dataclasses import dataclass
from typing import Optional, Tuple

INF = 10 ** 9
WIN_SCORE = 100000
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]

EXACT = 0
LOWER = 1
UPPER = 2


class SearchTimeout(Exception):
    pass


@dataclass
class TTEntry:
    depth: int
    value: float
    flag: int
    best_move: Optional[Tuple[int, int]]


def _check_time(start_time, time_limit_s):
    if time_limit_s is None:
        return
    if (time.perf_counter() - start_time) >= time_limit_s:
        raise SearchTimeout


# ---------- FAST HEURISTIC ----------
def fast_heuristic(board, player):
    if board.isGoal():
        return WIN_SCORE if board.winner == player else -WIN_SCORE

    opponent = 2 if player == 1 else 1
    score = 0
    center = board.dim // 2

    for i in range(board.dim):
        for j in range(board.dim):
            if board.matrix[i][j] == player:
                score += 5 - abs(i - center) - abs(j - center)
            elif board.matrix[i][j] == opponent:
                score -= 5 - abs(i - center) - abs(j - center)
    return score


# ---------- MOVE GENERATION ----------
def _move_order_score(board, move, player):
    x, y = move
    center = board.dim // 2
    score = -abs(x - center) - abs(y - center)

    for dx, dy in DIRECTIONS:
        nx = x + dx
        ny = y + dy
        if 0 <= nx < board.dim and 0 <= ny < board.dim:
            val = board.matrix[nx][ny]
            if val == player:
                score += 3
            elif isinstance(val, int) and val < 0 and abs(val) == player:
                score += 2
            elif val not in (0, ' '):
                score += 1
    return score


def _generate_candidate_moves(board, limit=12):
    if not board.moves:
        return board.get_valid_moves()

    roots = board.getRoots()
    seeds = list(board.moves[-8:]) + roots
    candidates = set()

    for x, y in seeds:
        for dx, dy in DIRECTIONS:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < board.dim and 0 <= ny < board.dim:
                if board.matrix[nx][ny] == 0:
                    candidates.add((nx, ny))

    if not candidates:
        return board.get_valid_moves()

    ordered = sorted(
        candidates,
        key=lambda m: _move_order_score(board, m, 1),
        reverse=True
    )
    return ordered[:limit]


# ---------- MINIMAX ----------
def _order_moves(moves, tt_move, killers_for_depth):
    if not moves:
        return moves

    ordered = []
    seen = set()

    if tt_move is not None and tt_move in moves:
        ordered.append(tt_move)
        seen.add(tt_move)

    for km in killers_for_depth:
        if km is not None and km in moves and km not in seen:
            ordered.append(km)
            seen.add(km)

    for m in moves:
        if m not in seen:
            ordered.append(m)

    return ordered


def minimax(
    board,
    depth,
    alpha,
    beta,
    maximizing_player,
    player_ai,
    tt,
    killers,
    start_time,
    time_limit_s,
):
    _check_time(start_time, time_limit_s)

    if board.isGoal():
        if board.winner == player_ai:
            return WIN_SCORE + depth, None
        return -WIN_SCORE - depth, None

    if depth == 0:
        return heuristic(board, player_ai), None

    key = (maximizing_player, board.hash())
    entry = tt.get(key)
    if entry and entry.depth >= depth:
        if entry.flag == EXACT:
            return entry.value, entry.best_move
        elif entry.flag == LOWER:
            alpha = max(alpha, entry.value)
        elif entry.flag == UPPER:
            beta = min(beta, entry.value)
        if alpha >= beta:
            return entry.value, entry.best_move

    alpha_orig = alpha
    beta_orig = beta

    opponent = 2 if player_ai == 1 else 1
    current_player = player_ai if maximizing_player else opponent

    moves = _generate_candidate_moves(board)
    if not moves:
        return fast_heuristic(board, player_ai), None

    moves = _order_moves(moves, entry.best_move if entry else None, killers.get(depth, []))

    best_move = None

    if maximizing_player:
        value = -INF
        for move in moves:
            board.apply_move(move[0], move[1], current_player)
            try:
                eval_score, _ = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    player_ai,
                    tt,
                    killers,
                    start_time,
                    time_limit_s,
                )
            finally:
                board.undo_move()

            if eval_score > value:
                value = eval_score
                best_move = move

            alpha = max(alpha, value)
            if alpha >= beta:
                if best_move is not None:
                    killers.setdefault(depth, [])
                    km = killers[depth]
                    if best_move not in km:
                        km.append(best_move)
                        if len(km) > 2:
                            km.pop(0)
                break
    else:
        value = INF
        for move in moves:
            board.apply_move(move[0], move[1], current_player)
            try:
                eval_score, _ = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    True,
                    player_ai,
                    tt,
                    killers,
                    start_time,
                    time_limit_s,
                )
            finally:
                board.undo_move()

            if eval_score < value:
                value = eval_score
                best_move = move

            beta = min(beta, value)
            if beta <= alpha:
                if best_move is not None:
                    killers.setdefault(depth, [])
                    km = killers[depth]
                    if best_move not in km:
                        km.append(best_move)
                        if len(km) > 2:
                            km.pop(0)
                break

    if value <= alpha_orig:
        flag = UPPER
    elif value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    tt[key] = TTEntry(depth, value, flag, best_move)
    return value, best_move


# ---------- ROOT SEARCH ----------
def find_best_move(board, player_ai, max_depth=7, time_limit_s=1.0):
    start_time = time.perf_counter()
    best_move = None
    best_score = -INF
    tt = {}
    killers = {}

    for depth in range(1, max_depth + 1):
        try:
            score, move = minimax(
                board,
                depth,
                -INF,
                INF,
                True,
                player_ai,
                tt,
                killers,
                start_time,
                time_limit_s,
            )
            if move is not None:
                best_move = move
                best_score = score
        except SearchTimeout:
            break

    return best_score, best_move
