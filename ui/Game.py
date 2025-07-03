import pygame
import chess
from chess import STARTING_BOARD_FEN
from fichess.utils import get_square_under_mouse, load_piece_images
from fichess.consts import *

class Game:
    def __init__(self, fen = STARTING_BOARD_FEN):
        pygame.init()
        self.font = pygame.font.SysFont(None, 28)
        self.board = chess.Board(fen)
        self.images = load_piece_images()
        self.dragging = False
        self.dragged_piece = None
        self.dragged_from = None
        self.dragged_pos = (0, 0)
        self.mouse_offset = (0, 0)
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        # self.legal_moves =
        pygame.display.set_caption("Chess Board")

    def is_player_piece(self, square):
        piece = self.board.piece_at(square)
        if piece is None:
            return False
        return (piece.color == chess.WHITE and self.board.turn == chess.WHITE) or \
            (piece.color == chess.BLACK and self.board.turn == chess.BLACK)

    def render(self):
        files = "abcdefgh"
        turn_text = f"{'White' if self.board.turn == chess.WHITE else 'Black'}'s turn"
        turn_label = self.font.render(turn_text, True, BLACK)
        self.screen.blit(turn_label, (PADDING, PADDING // 2 - turn_label.get_height() // 2))
        for row in range(8):
            for col in range(8):
                color = WHITE if (row + col) % 2 == 0 else BROWN
                rect = pygame.Rect(
                    PADDING + col * SQUARE_SIZE,
                    PADDING + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, color, rect)
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                if piece and (not self.dragging or (row, col) != self.dragged_from):
                    key = piece.symbol()
                    self.screen.blit(self.images[key], rect.topleft)
            label = self.font.render(str(8 - row), True, BLACK)
            self.screen.blit(label, (PADDING - 25, PADDING + row * SQUARE_SIZE + SQUARE_SIZE // 2 - label.get_height() // 2))
        for col in range(8):
            label = self.font.render(files[col], True, BLACK)
            self.screen.blit(label, (PADDING + col * SQUARE_SIZE + SQUARE_SIZE // 2 - label.get_width() // 2,
                                PADDING + 8 * SQUARE_SIZE + 5))
        if self.dragging and self.dragged_piece:
            self.screen.blit(self.images[self.dragged_piece], self.dragged_pos)

    def start_game(self):
        running = True
        while running:
            if self.board.is_checkmate():
                print("Checkmate!")
                print("Result:", self.board.result())
                text = f"{'White' if self.board.turn == chess.BLACK else 'Black'} wins!"
                label = pygame.font.SysFont(None, 64).render(text, True, BLACK)
                self.screen.blit(label, (WINDOW_SIZE // 2 - label.get_width() // 2, WINDOW_SIZE // 2 - label.get_height() // 2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
                break

            if self.board.is_stalemate():
                print("Stalemate!")
                print("Result:", self.board.result())
                break

            if self.board.is_game_over():
                print("Game Over")
                print("Result:", self.board.result())
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    y, x = get_square_under_mouse(event.pos)
                    if y is not None:
                        square = chess.square(x, 7 - y)
                        piece = self.board.piece_at(square)
                        if piece and self.is_player_piece(square):
                            self.dragging = True
                            self.dragged_piece = piece.symbol()
                            self.dragged_from = (y, x)
                            mouse_x, mouse_y = event.pos
                            piece_x = PADDING + x * SQUARE_SIZE
                            piece_y = PADDING + y * SQUARE_SIZE
                            self.mouse_offset = (mouse_x - piece_x, mouse_y - piece_y)
                            self.dragged_pos = (piece_x, piece_y)
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    mouse_x, mouse_y = event.pos
                    self.dragged_pos = (mouse_x - self.mouse_offset[0], mouse_y - self.mouse_offset[1])
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
                    y, x = get_square_under_mouse(event.pos)
                    if y is not None:
                        from_square = chess.square(self.dragged_from[1], 7 - self.dragged_from[0])
                        to_square = chess.square(x, 7 - y)
                        if (y, x) == self.dragged_from:
                            self.dragging = False
                            self.dragged_piece = None
                            continue
                        move = chess.Move(from_square, to_square)
                        if move in self.board.legal_moves:
                            self.board.push(move)
                    self.dragging = False
                    self.dragged_piece = None

            self.screen.fill((200, 200, 200))
            self.render()
            pygame.display.flip()