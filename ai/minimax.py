import copy
from ai.heuristics import heuristic

def minimax(board, depth, alpha, beta, maximizing_player, player_ai):
    # Provera kraja igre ili dubine
    if board.isGoal():
        # Ako je goal, znači da je PRETHODNI igrač pobedio.
        # Ako je maximizing_player True, znači da je protivnik upravo odigrao i pobedio -> Loše za AI (-10000)
        # Ako je maximizing_player False, znači da je AI upravo odigrao i pobedio -> Dobro za AI (+10000)
        if board.winner == player_ai:
            return 10000, None
        else:
            return -10000, None

    if depth == 0:
        return heuristic(board, player_ai), None

    valid_moves = board.get_valid_moves()

    # Sortiranje poteza može ubrzati alpha-beta (opciono, npr. prvo potezi blizu centra)
    # valid_moves.sort(...)

    best_move = None

    if maximizing_player:
        max_eval = float('-inf')
        for move in valid_moves:
            # OPTIMIZACIJA: Umesto deepcopy, koristi modifyArray pa vrati nazad (backtrack)
            # Ali tvoj Board trenutno nema 'undo', pa koristimo deepcopy
            new_board = copy.deepcopy(board)
            new_board.modifyArray(move[0], move[1], player_ai)

            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, player_ai)

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        opponent = 2 if player_ai == 1 else 1
        for move in valid_moves:
            new_board = copy.deepcopy(board)
            new_board.modifyArray(move[0], move[1], opponent)

            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, player_ai)

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move