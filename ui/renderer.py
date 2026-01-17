import pygame
import math
from constants import TILE_SIZE, MARGIN, COLORS, TILE_RADIUS

WALL_MARGIN = TILE_RADIUS + MARGIN
SPACE_BETWEEN = TILE_SIZE + MARGIN

# globalna mapa za pracenje pozicija svih srednjih plocica
middle_tiles_map = {}

# dugmad menija
buttons = {
    # veličina table
    "5": pygame.Rect(80, 60, 60, 40),
    "7": pygame.Rect(150, 60, 60, 40),
    "9": pygame.Rect(220, 60, 60, 40),

    # protivnik
    "covek": pygame.Rect(80, 130, 200, 40),
    "racunar": pygame.Rect(80, 180, 200, 40),

    # boja
    "crvena": pygame.Rect(80, 250, 200, 40),
    "zelena": pygame.Rect(80, 300, 200, 40),

    # start
    "start": pygame.Rect(110, 370, 140, 50)
}

# selektovane opcije
selected = {
    "size": 5,
    "opponent": "covek",
    "color": "crvena"
}

def get_font(size=32):
    return pygame.font.SysFont(None, size)

def draw_menu(screen):
    screen.fill((20, 20, 20))
    font = get_font(36)

    for key, rect in buttons.items():
        active = (
            (key.isdigit() and int(key) == selected["size"]) or
            (key == selected["opponent"]) or
            (key == selected["color"])
        )
        border_color = (0, 200, 0) if active else (180, 180, 180)
        pygame.draw.rect(screen, border_color, rect, 3)
        label = font.render(key.upper(), True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=rect.center))

    pygame.display.flip()

def handle_menu_click(pos):
    """
    Obradi klik na meni.
    Vraca True ako je kliknut START, inace False
    """
    for key, rect in buttons.items():
        if rect.collidepoint(pos):
            if key.isdigit():
                selected["size"] = int(key)
            elif key in ("covek", "racunar"):
                selected["opponent"] = key
            elif key in ("crvena", "zelena"):
                selected["color"] = key
            elif key == "start":
                return True
    return False

def draw_board(screen, board):
    global middle_tiles_map
    middle_tiles_map.clear()
    
    # Calculate n based on board size
    n = (board.size - 1) // 2
    
    # Generate patterns dynamically
    top_bottom_pattern = ([1, 2] * n) + ([2, 1] * n)
    left_right_pattern = ([2] * n) + ([1] * (n * 2)) + ([2] * n)
    
    col_size = board.size + 1
    num_of_cols = board.size * 2 + 1
    half = 0
    corner_positions = set()
    
    temp_col_size = board.size + 1
    temp_half = 0
    widest_col = -1
    max_col_size = 0
    
    for col in range(num_of_cols):
        if temp_col_size > max_col_size:
            max_col_size = temp_col_size
            widest_col = col
        if col == 0 or col == num_of_cols - 1:
            corner_positions.add((col, 0))
            corner_positions.add((col, temp_col_size - 1))
        if temp_col_size == num_of_cols:
            temp_half = 1
        if temp_half == 0:
            temp_col_size += 1
        else:
            temp_col_size -= 1
    
    corner_positions.add((widest_col, 0))
    corner_positions.add((widest_col, max_col_size - 1))
    
    top_bottom_count = 0
    left_right_count = 0
    middle_id = 0
    
    for col in range(num_of_cols):
        for tile in range(col_size):
            if (col, tile) in corner_positions:
                continue
            
            cy = WALL_MARGIN + (num_of_cols - col_size) * TILE_SIZE + tile * SPACE_BETWEEN
            cx = WALL_MARGIN + col * SPACE_BETWEEN

            is_left_right_edge = (col == 0 or col == num_of_cols - 1)
            is_top_bottom_edge = (tile == 0 or tile == col_size - 1)
            is_edge = is_left_right_edge or is_top_bottom_edge
            
            if is_edge:
                if is_left_right_edge and not is_top_bottom_edge:
                    pattern_value = left_right_pattern[left_right_count % len(left_right_pattern)]
                    left_right_count += 1
                else:
                    pattern_value = top_bottom_pattern[top_bottom_count % len(top_bottom_pattern)]
                    top_bottom_count += 1
                color = "rTile" if pattern_value == 2 else "gTile"
            else:
                if middle_id in board.edges:
                    state = board.edges[middle_id]
                    color = "rTile" if state == 1 else "gTile"
                else:
                    color = "wTile"
                
                middle_tiles_map[middle_id] = (cx, cy)
                middle_id += 1
            
            draw_tile(screen, cx, cy, color)

        if col_size == num_of_cols:
            half = 1
        if half == 0:
            col_size += 1
        else:
            col_size -= 1

def get_clicked_edge(mouse_pos):
    mx, my = mouse_pos
    for middle_id, (cx, cy) in middle_tiles_map.items():
        distance = math.sqrt((mx - cx) ** 2 + (my - cy) ** 2)
        if distance <= TILE_RADIUS:
            return middle_id
    return None

def draw_tile(screen, cx, cy, color):
    pygame.draw.circle(screen, COLORS[color], (cx, cy), TILE_RADIUS)