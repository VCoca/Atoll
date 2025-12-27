import pygame

from ui.renderer import draw_board, get_clicked_edge
from game.board import Board
from constants import COLORS

# pygame setup
pygame.init()
board = Board(size=5)
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Atoll")
clock = pygame.time.Clock()

# igrač red počinje prvi (1 = crveno, 2 = zeleno)
current_player = 1

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # pronađi kliknut tile
            edge_id = get_clicked_edge(event.pos)
            if edge_id is not None and edge_id not in board.edges:
                # taj tile je slobodan, zauzmi ga
                board.edges[edge_id] = current_player
                # promeni igrača
                current_player = 2 if current_player == 1 else 1
    
    screen.fill(COLORS["bg"])
    draw_board(screen, board)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()