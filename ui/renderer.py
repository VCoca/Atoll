import pygame
import math
from constants import TILE_SIZE, MARGIN, COLORS, TILE_RADIUS

WALL_MARGIN = TILE_RADIUS + MARGIN
SPACE_BETWEEN = TILE_SIZE + MARGIN

# globalna mapa za prati pozicije svih pločica u sredini
middle_tiles_map = {}

def draw_board(screen, board):
    global middle_tiles_map
    middle_tiles_map.clear()
    
    num_of_player_tiles = (board.size - 1) / 2
    col_size = board.size + 1
    num_of_cols = board.size * 2 + 1
    half = 0
    corner_positions = set()
    
    # pronađi najširu kolonu i uglove
    temp_col_size = board.size + 1
    temp_half = 0
    widest_col = -1
    max_col_size = 0
    
    for col in range(num_of_cols):
        # prati maksimalnu veličinu kolone
        if temp_col_size > max_col_size:
            max_col_size = temp_col_size
            widest_col = col
        
        # dodaj uglove sa strane
        if col == 0 or col == num_of_cols - 1:
            corner_positions.add((col, 0))
            corner_positions.add((col, temp_col_size - 1))
        
        # prilagodi veličinu kolone
        if temp_col_size == num_of_cols:
            temp_half = 1
        if temp_half == 0:
            temp_col_size += 1
        else:
            temp_col_size -= 1
    
    corner_positions.add((widest_col, 0))
    corner_positions.add((widest_col, max_col_size - 1))
    
    top_bottom_pattern = [1, 2, 1, 2, 2, 1, 2, 1]
    left_right_pattern = [2, 2, 1, 1, 1, 1, 2, 2]
    top_bottom_count = 0
    left_right_count = 0
    middle_id = 0
    
    for col in range(num_of_cols):
        for tile in range(col_size):
            # preskoči uglove
            if (col, tile) in corner_positions:
                continue
            
            cy = WALL_MARGIN + (num_of_cols - col_size) * TILE_SIZE + tile * SPACE_BETWEEN
            cx = WALL_MARGIN + col * SPACE_BETWEEN

            is_left_right_edge = (col == 0 or col == num_of_cols - 1)
            is_top_bottom_edge = (tile == 0 or tile == col_size - 1)
            is_edge = is_left_right_edge or is_top_bottom_edge
            
            if is_edge:
                # obriši šablon za grana
                if is_left_right_edge and not is_top_bottom_edge:
                    pattern_value = left_right_pattern[left_right_count % len(left_right_pattern)]
                    left_right_count += 1
                else:
                    pattern_value = top_bottom_pattern[top_bottom_count % len(top_bottom_pattern)]
                    top_bottom_count += 1
                color = "rTile" if pattern_value == 2 else "gTile"
            else:
                # srednja pločica - proveri da li je zauzeta
                if middle_id in board.edges:
                    state = board.edges[middle_id]
                    if state == 1:
                        color = "rTile"
                    else:
                        color = "gTile"
                else:
                    color = "wTile"
                
                # sačuvaj poziciju za kasnije detektovanje klika
                middle_tiles_map[middle_id] = (cx, cy)
                middle_id += 1
            
            draw_tile(screen, cx, cy, color)

        # prilagodi veličinu kolone za sledeću iteraciju
        if col_size == num_of_cols:
            half = 1
        if half == 0:
            col_size += 1
        else:
            col_size -= 1

def get_clicked_edge(mouse_pos):
    """pronađi koju je srednju pločicu kliknut"""
    mx, my = mouse_pos
    for middle_id, (cx, cy) in middle_tiles_map.items():
        # proveri da li je klik bio u krugu tile-a
        distance = math.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
        if distance <= TILE_RADIUS:
            return middle_id
    return None

def draw_tile(screen, cx, cy, color):
    pygame.draw.circle(
        screen,
        COLORS[color],
        (cx, cy),
        TILE_RADIUS
    )