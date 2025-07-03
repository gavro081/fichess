from chess import STARTING_BOARD_FEN
import pygame
import sys
import os

pygame.init()
window_size = 800
padding = 40
board_size = window_size - 2 * padding
square_size = board_size // 8
current_player = 'w'

screen = pygame.display.set_mode((window_size, window_size))
pygame.display.set_caption("Chess Board")

piece_files = {
    'K': 'king.png',
    'Q': 'queen.png',
    'R': 'rook.png',
    'B': 'bishop.png',
    'N': 'knight.png',
    'P': 'pawn.png'
}

WHITE = (255,255,255)
BROWN = (92, 73, 53)
BLACK = (0,0,0)

dragging = False
dragged_piece = None
dragged_from = (0, 0)
mouse_offset = (0, 0)
dragged_pos = (0, 0)

def load_piece_images():
    images = {}
    for color, folder in [('w', 'white'), ('b', 'black')]:
        for key, filename in piece_files.items():
            path = os.path.join('assets', folder, filename)
            image = pygame.image.load(path)
            image = pygame.transform.smoothscale(image, (square_size, square_size))
            key = key[0] if key != "knight" else "n"
            if color == 'b': key = key.lower()
            images[key] = image

    return images

piece_images = load_piece_images()
font = pygame.font.SysFont(None, 28)

# board as 2D array, using UCI notation, and None for empty squares
board = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p'] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    [None] * 8,
    ['P'] * 8,
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

def fen_to_board(fen: str):
    ranks = fen.split("/")
    board = []
    for rank in ranks:
        row = []
        for j, pos in enumerate(rank):
            if pos.isdigit():
                j += int(pos) - 1
                row += [None] * int(pos)
                continue
            row.append(pos)
        board.append(row)
    return board

def board_to_fen(board):
    fen_rows = []
    for row in board:
        empty = 0
        fen_row = ""
        for piece in row:
            if piece is None:
                empty += 1
            else:
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0
                fen_row += piece
        if empty > 0:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    return "/".join(fen_rows)

def render():
    files = "abcdefgh"
    turn_text = f"{'White' if current_player == 'w' else 'Black'}'s turn"
    turn_label = font.render(turn_text, True, BLACK)
    screen.blit(turn_label, (padding, padding // 2 - turn_label.get_height() // 2))
    for row in range(8):
        for col in range(8):
            color = WHITE if (row + col) % 2 == 0 else BROWN
            rect = pygame.Rect(
                padding + col * square_size,
                padding + row * square_size,
                square_size,
                square_size
            )
            pygame.draw.rect(screen, color, rect)
            piece = board[row][col]
            if piece and (not dragging or (row, col) != dragged_from):
                screen.blit(piece_images[piece], rect.topleft)
        # rank label
        label = font.render(str(8 - row), True, BLACK)
        screen.blit(label, (padding - 25, padding + row * square_size + square_size // 2 - label.get_height() // 2))
    # file labels
    for col in range(8):
        label = font.render(files[col], True, BLACK)
        screen.blit(label, (padding + col * square_size + square_size // 2 - label.get_width() // 2,
                            padding + 8 * square_size + 5))
    # dragged piece on top
    if dragging and dragged_piece:
        screen.blit(piece_images[dragged_piece], dragged_pos)

def get_square_under_mouse(pos):
    mx, my = pos
    x = (mx - padding) // square_size
    y = (my - padding) // square_size
    if 0 <= x < 8 and 0 <= y < 8:
        return int(y), int(x)
    return None, None

def is_player_piece(piece, player):
    if not piece:
        return False
    return (piece.isupper() and player == 'w') or (piece.islower() and player == 'b')

def start_game():
    global dragging, dragged_piece, dragged_from, mouse_offset, dragged_pos, current_player
    current_player = 'w'
    # fen = STARTING_BOARD_FEN
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                y, x = get_square_under_mouse(event.pos)
                if y is not None and is_player_piece(board[y][x], current_player):
                    dragging = True
                    dragged_piece = board[y][x]
                    dragged_from = (y, x)
                    mouse_x, mouse_y = event.pos
                    piece_x = padding + x * square_size
                    piece_y = padding + y * square_size
                    mouse_offset = (mouse_x - piece_x, mouse_y - piece_y)
                    dragged_pos = (piece_x, piece_y)
            elif event.type == pygame.MOUSEMOTION and dragging:
                mouse_x, mouse_y = event.pos
                dragged_pos = (mouse_x - mouse_offset[0], mouse_y - mouse_offset[1])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and dragging:
                y, x = get_square_under_mouse(event.pos)
                if y is not None:
                    if (y, x) == dragged_from:
                        dragging = False
                        dragged_piece = None
                        continue
                    board[dragged_from[0]][dragged_from[1]] = None
                    board[y][x] = dragged_piece
                    # fen = board_to_fen(board)
                    # print(fen)
                    current_player = 'b' if current_player == 'w' else 'w'
                dragging = False
                dragged_piece = None

        screen.fill((200, 200, 200))
        render()
        pygame.display.flip()

    pygame.quit()
    sys.exit()