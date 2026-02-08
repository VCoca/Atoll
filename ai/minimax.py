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


def _board_key(board):
    return tuple(tuple(row) for row in board.matrix)


def _check_time(start_time, time_limit_s):
    if time_limit_s is None:
        return
    if (time.perf_counter() - start_time) >= time_limit_s:
        raise SearchTimeout


def _generate_candidate_moves(board):
    if not board.moves:
        return board.get_valid_moves()

    roots = board.getRoots()
    seeds = list(board.moves) + roots
    candidates = set()
    radius = 2

    for x, y in seeds:
        for dx, dy in DIRECTIONS:
            for step in range(1, radius + 1):
                nx = x + dx * step
                ny = y + dy * step
                if 0 <= nx < board.dim and 0 <= ny < board.dim:
                    if board.matrix[nx][ny] == 0:
                        candidates.add((nx, ny))

    if not candidates:
        return board.get_valid_moves()

    return list(candidates)


def _move_order_score(board, move, player):
    x, y = move
    center = board.dim // 2
    dist = abs(x - center) + abs(y - center)
    score = -dist

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


def minimax(
    board,
    depth,
    alpha,
    beta,
    maximizing_player,
    player_ai,
    tt=None,
    start_time=None,
    time_limit_s=None,
):
    if start_time is None:
        start_time = time.perf_counter()
    _check_time(start_time, time_limit_s)

    if board.isGoal():
        if board.winner == player_ai:
            return WIN_SCORE + depth, None
        return -WIN_SCORE - depth, None

    if depth == 0:
        return heuristic(board, player_ai), None

    if tt is None:
        tt = {}

    key = (maximizing_player, _board_key(board))
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        if entry.flag == EXACT:
            return entry.value, entry.best_move
        if entry.flag == LOWER:
            alpha = max(alpha, entry.value)
        elif entry.flag == UPPER:
            beta = min(beta, entry.value)
        if alpha >= beta:
            return entry.value, entry.best_move

    alpha_orig = alpha
    beta_orig = beta

    best_move = None
    opponent = 2 if player_ai == 1 else 1
    current_player = player_ai if maximizing_player else opponent

    valid_moves = _generate_candidate_moves(board)
    if not valid_moves:
        return heuristic(board, player_ai), None

    valid_moves.sort(
        key=lambda m: _move_order_score(board, m, current_player),
        reverse=maximizing_player,
    )

    if maximizing_player:
        value = -INF
        for move in valid_moves:
            _check_time(start_time, time_limit_s)
            board.apply_move(move[0], move[1], player_ai)
            try:
                eval_score, _ = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    player_ai,
                    tt,
                    start_time,
                    time_limit_s,
                )
            finally:
                board.undo_move()

            if eval_score > value:
                value = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
    else:
        value = INF
        for move in valid_moves:
            _check_time(start_time, time_limit_s)
            board.apply_move(move[0], move[1], opponent)
            try:
                eval_score, _ = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    True,
                    player_ai,
                    tt,
                    start_time,
                    time_limit_s,
                )
            finally:
                board.undo_move()

            if eval_score < value:
                value = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break

    if value <= alpha_orig:
        flag = UPPER
    elif value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT
    tt[key] = TTEntry(depth, value, flag, best_move)

    return value, best_move


def find_best_move(board, player_ai, max_depth, time_limit_s=0.9):
    start_time = time.perf_counter()
    best_move = None
    best_score = -INF
    tt = {}

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
                start_time,
                time_limit_s,
            )
            if move is not None:
                best_move = move
                best_score = score
        except SearchTimeout:
            break

    return best_score, best_move
