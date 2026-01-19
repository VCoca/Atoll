import pygame
from ui.renderer import draw_board, get_clicked_edge, draw_menu, handle_menu_click, selected
from game.board import Board, number_to_position
from constants import COLORS

pygame.init()
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Atoll")
clock = pygame.time.Clock()

MENU = 0
GAME = 1
game_state = MENU
board = None
# 1 je crveni, 2 je zeleni
current_player = 1

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == MENU:
                start_clicked = handle_menu_click(event.pos)
                if start_clicked:
                    board = Board(size=selected["size"])

                    # POCETNA MATRICA:
                    board.drawMatrix()

                    current_player = 1 if selected["color"] == "crvena" else 2
                    game_state = GAME

            elif game_state == GAME:
                if not board.game_over:
                    edge_id = get_clicked_edge(event.pos)
                    if edge_id is not None and edge_id not in board.edges:
                        board.edges[edge_id] = current_player
                        row, col = number_to_position(edge_id, board.size)
                        board.modifyArray(row, col, current_player)

                        board.moveCount += 1
                        if (board.isGoal()):
                            board.game_over = True
                            #pygame.quit()

                        else:
                            board.drawMatrix()
                            current_player = 2 if current_player == 1 else 1

    screen.fill(COLORS["bg"])

    if game_state == MENU:
        draw_menu(screen)
    elif game_state == GAME:
        draw_board(screen, board)
        pygame.display.flip()

    clock.tick(60)

pygame.quit()
