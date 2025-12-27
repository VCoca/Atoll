import pygame
import math
from constants import TILE_SIZE, MARGIN, COLORS, TILE_RADIUS

WALL_MARGIN = TILE_RADIUS + MARGIN
SPACE_BETWEEN = TILE_SIZE + MARGIN

def draw_board(screen, board):
    num_of_player_tiles = (board.size - 1) / 2
    col_size = board.size
    num_of_cols = board.size * 2 - 1
    half = 0
    for col in range(num_of_cols):
        for tile in range(col_size):
            cy = WALL_MARGIN + (num_of_cols - col_size) * TILE_SIZE + tile * SPACE_BETWEEN
            cx = WALL_MARGIN + col * SPACE_BETWEEN
            draw_tile(screen, cx, cy, "wTile")
        if col_size == num_of_cols:
            half = 1
        if half == 0:
            col_size += 1
        else:
            col_size -= 1

def draw_tile(screen, cx, cy, color):
    pygame.draw.circle(
        screen,
        COLORS[color],
        (cx, cy),
        TILE_RADIUS
    )