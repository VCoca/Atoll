import pygame
from ui.renderer import draw_board, get_clicked_edge, draw_menu, handle_menu_click, selected
from game.board import Board, number_to_position, position_to_edge_id, debug_segments
from constants import COLORS
from ai.minimax import find_best_move

pygame.init()
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Atoll")
clock = pygame.time.Clock()

MENU = 0
GAME = 1
GAME_OVER = 2
game_state = MENU
board = None

# Stanja igrača
# 1 je crveni, 2 je zeleni
current_player = 1
ai_player = 2 # Pretpostavimo da je AI uvek zeleni ako se izabere 'racunar'
game_mode = "covek" # ili "racunar"
winner_text = ""

running = True
ai_thinking = False # Zastavica da ne primamo input dok AI misli


def make_ai_move():
    global current_player, ai_thinking, game_state, winner_text

    # Prilagodi dubinu (iterativno do max_depth uz vremensko ogranicenje)
    max_depth = 4 if board.size <= 5 else 3
    if board.moveCount > (board.size * 2):
        max_depth += 1

    print("AI razmislja...")
    _, move = find_best_move(board, ai_player, max_depth, time_limit_s=2)

    if move:
        row, col = move

        # 1. Update logiku
        board.apply_move(row, col, ai_player)

        # 2. Update vizuelni deo (UI)
        edge_id = position_to_edge_id(row, col, board.size)
        if edge_id is not None:
            board.edges[edge_id] = ai_player

        print(f"AI odigrao: {row}, {col} (Edge ID: {edge_id})")

        # 3. Provera pobede
        if board.isGoal():
            print("AI POBEDIO!")
            winner_text = f"Pobednik: AI ({'Crveni' if ai_player == 1 else 'Zeleni'})"
            board.drawMatrix()
            game_state = GAME_OVER
        else:
            # ISPRAVKA: Vrati potez onome ko NIJE AI (tj. čoveku)
            current_player = 1 if ai_player == 2 else 2

    ai_thinking = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == MENU:
                start_clicked = handle_menu_click(event.pos)
                if start_clicked:
                    board = Board(size=selected["size"])
                    debug_segments(board)

                    game_mode = selected["opponent"]

                    if game_mode == "racunar":
                        if selected["color"] == "zelena":
                            current_player = 2  # Covek je 2
                            ai_player = 1  # AI je 1 (Crveni, igra prvi)
                        else:
                            current_player = 1
                            ai_player = 2

                    game_state = GAME
                    board.drawMatrix()

            elif game_state == GAME:
                # Klik coveka
                if not ai_thinking:
                    # Provera: da li je red na coveka?
                    is_human_turn = True
                    if game_mode == "racunar" and current_player == ai_player:
                        is_human_turn = False

                    if is_human_turn:
                        edge_id = get_clicked_edge(event.pos)
                        if edge_id is not None and edge_id not in board.edges:
                            # Odigraj potez
                            board.edges[edge_id] = current_player
                            row, col = number_to_position(edge_id, board.size)
                            board.apply_move(row, col, current_player)

                            if board.isGoal():
                                winner_text = f"Pobednik: Igrac {current_player}"
                                board.drawMatrix()
                                game_state = GAME_OVER
                            else:
                                # Promeni igraca
                                current_player = 2 if current_player == 1 else 1

    screen.fill(COLORS["bg"])

    if game_state == MENU:
        draw_menu(screen)
    elif game_state == GAME:
        draw_board(screen, board)

        # AI Logika (poziva se izvan event loop-a)
        if game_mode == "racunar" and current_player == ai_player and not ai_thinking and not board.game_over:
            ai_thinking = True
            # Pokrecemo u threadu da ne blokira UI (ili direktno ako ti ne smeta freeze)
            # Za jednostavnost ovde zovi direktno (zamrznuce prozor na 1-2 sec)
            make_ai_move()

    elif game_state == GAME_OVER:
        draw_board(screen, board)
        # Ispis pobednika preko ekrana
        font = pygame.font.SysFont(None, 60)
        text = font.render(winner_text, True, (0, 0, 0))
        rect = text.get_rect(center=(300, 300))
        pygame.draw.rect(screen, (255, 255, 255), rect.inflate(20, 20))
        screen.blit(text, rect)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
