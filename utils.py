import pygame
import os
import consts

def get_square_under_mouse(pos):
    mx, my = pos
    x = (mx - consts.PADDING) // consts.SQUARE_SIZE
    y = (my - consts.PADDING) // consts.SQUARE_SIZE
    if 0 <= x < 8 and 0 <= y < 8:
        return y, x
    return None, None


piece_files = {
    'K': 'king.png',
    'Q': 'queen.png',
    'R': 'rook.png',
    'B': 'bishop.png',
    'N': 'knight.png',
    'P': 'pawn.png'
}

def load_piece_images():
    images = {}
    for color, folder in [('w', 'white'), ('b', 'black')]:
        for key, filename in piece_files.items():
            path = os.path.join('assets', folder, filename)
            image = pygame.image.load(path)
            image = pygame.transform.smoothscale(image, (consts.SQUARE_SIZE, consts.SQUARE_SIZE))
            key = key[0] if key != "knight" else "n"
            if color == 'b': key = key.lower()
            images[key] = image
    return images