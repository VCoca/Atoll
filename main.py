import pygame

from ui.renderer import draw_board
from game.board import Board
from constants import COLORS

# pygame setup
pygame.init()
board = Board(size=5)
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Atoll")
clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(COLORS["bg"])
    draw_board(screen, board)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()