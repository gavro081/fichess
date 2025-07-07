import pygame
import chess
import os
from engine.Agent import Agent

WHITE = (255, 255, 255)
BROWN = (92, 73, 53)
BLACK = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 252, 166)

WINDOW_SIZE = 800
PADDING = 40
BOARD_SIZE = WINDOW_SIZE - 2 * PADDING
SQUARE_SIZE = BOARD_SIZE // 8

MIDDLE_GAME_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
ENDGAME_FEN = "8/5pk1/6p1/7p/7P/5K2/6P1/6R1 w - - 0 45"

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
            image = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
            key = key[0] if key != "knight" else "n"
            if color == 'b': key = key.lower()
            images[key] = image

    return images


def get_square_under_mouse(pos):
    mx, my = pos
    if not (PADDING <= mx < PADDING + BOARD_SIZE and PADDING <= my < PADDING + BOARD_SIZE):
        return None, None

    col = (mx - PADDING) // SQUARE_SIZE
    row = (my - PADDING) // SQUARE_SIZE
    return row, col


class Game:
    def __init__(self, fen=chess.STARTING_BOARD_FEN):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Chess Engine")

        self.font = pygame.font.SysFont("Arial", 28, bold=True)
        self.board = chess.Board(fen)
        self.images = load_piece_images()

        self.dragging = False
        self.dragged_piece = None
        self.dragged_from_square = None
        self.dragged_pos = (0, 0)
        self.mouse_offset = (0, 0)
        self.last_move = None
        self.flipped = False

    def _square_to_screen_coords(self, square: chess.Square):
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        if not self.flipped:
            row = 7 - rank
            col = file
        else:
            row = rank
            col = 7 - file
        return row, col

    def _screen_coords_to_square(self, row: int, col: int) -> chess.Square:
        if not self.flipped:
            return chess.square(col, 7 - row)
        else:
            return chess.square(7 - col, row)

    def is_player_piece(self, square: chess.Square) -> bool:
        piece = self.board.piece_at(square)
        return piece and piece.color == self.board.turn

    def render(self):
        # Draw turn indicator
        turn_text = f"{'White' if self.board.turn == chess.WHITE else 'Black'}'s turn"
        turn_label = self.font.render(turn_text, True, BLACK)
        self.screen.blit(turn_label, (PADDING, PADDING // 2 - turn_label.get_height() // 2))

        files = "abcdefgh" if not self.flipped else "hgfedcba"

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

                square = self._screen_coords_to_square(row, col)
                piece = self.board.piece_at(square)
                if piece and (not self.dragging or square != self.dragged_from_square):
                    symbol = piece.symbol()
                    self.screen.blit(self.images[symbol], rect.topleft)

            rank_label_text = str(8 - row) if not self.flipped else str(row + 1)
            label = self.font.render(rank_label_text, True, BLACK)
            label_rect = label.get_rect(center=(PADDING - 20, PADDING + row * SQUARE_SIZE + SQUARE_SIZE // 2))
            self.screen.blit(label, label_rect)

        if self.last_move:
            for square in [self.last_move.from_square, self.last_move.to_square]:
                row, col = self._square_to_screen_coords(square)
                rect = pygame.Rect(
                    PADDING + col * SQUARE_SIZE,
                    PADDING + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect, 6)

        for col in range(8):
            label = self.font.render(files[col], True, BLACK)
            label_rect = label.get_rect(
                center=(PADDING + col * SQUARE_SIZE + SQUARE_SIZE // 2, PADDING + BOARD_SIZE + 20))
            self.screen.blit(label, label_rect)

        if self.dragging and self.dragged_piece:
            self.screen.blit(self.images[self.dragged_piece], self.dragged_pos)

    def print_text(self, text: str):
        self.screen.fill((200, 200, 200))
        self.render()
        pygame.display.flip()

        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        label = pygame.font.SysFont("Arial", 64, bold=True).render(text, True, WHITE)
        label_rect = label.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2))
        self.screen.blit(label, label_rect)
        pygame.display.flip()
        pygame.time.wait(3000)

    def start_game(self, engine_color: chess.Color = chess.BLACK, with_fen: bool = False):
        self.flipped = (engine_color == chess.WHITE)
        agent = Agent(engine_color=engine_color)
        running = True

        while running:
            if self.board.is_checkmate():
                winner = "White" if self.board.turn == chess.BLACK else "Black"
                self.print_text(f"Checkmate! {winner} wins!")
                running = False
                continue
            if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition():
                self.print_text("Stalemate!")
                running = False
                continue

            if self.board.turn == engine_color:
                best_move = \
                agent.alpha_beta(self.board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
                if best_move:
                    self.board.push(best_move)
                    self.last_move = best_move
                    if with_fen: print(self.board.fen())
                self.screen.fill((200, 200, 200))
                self.render()
                pygame.display.flip()
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    row, col = get_square_under_mouse(event.pos)
                    if row is not None:
                        square = self._screen_coords_to_square(row, col)
                        if self.is_player_piece(square):
                            piece = self.board.piece_at(square)
                            self.dragging = True
                            self.dragged_piece = piece.symbol()
                            self.dragged_from_square = square

                            mouse_x, mouse_y = event.pos
                            piece_x = PADDING + col * SQUARE_SIZE
                            piece_y = PADDING + row * SQUARE_SIZE
                            self.mouse_offset = (mouse_x - piece_x, mouse_y - piece_y)
                            self.dragged_pos = (mouse_x - self.mouse_offset[0], mouse_y - self.mouse_offset[1])

                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    mouse_x, mouse_y = event.pos
                    self.dragged_pos = (mouse_x - self.mouse_offset[0], mouse_y - self.mouse_offset[1])

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
                    row, col = get_square_under_mouse(event.pos)
                    if row is not None:
                        from_square = self.dragged_from_square
                        to_square = self._screen_coords_to_square(row, col)

                        piece = self.board.piece_at(from_square)
                        is_promotion = (piece.piece_type == chess.PAWN and chess.square_rank(to_square) in [0, 7])

                        move = chess.Move(from_square, to_square, promotion=chess.QUEEN if is_promotion else None)

                        if move in self.board.legal_moves:
                            self.board.push(move)
                            self.last_move = move
                            if with_fen: print(self.board.fen())

                    self.dragging = False
                    self.dragged_piece = None
                    self.dragged_from_square = None

            self.screen.fill((200, 200, 200))
            self.render()
            pygame.display.flip()

        pygame.quit()
