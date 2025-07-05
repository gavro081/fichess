import chess
from chess import STARTING_BOARD_FEN

from ui.Game import Game

if __name__ == '__main__':
    game = Game(fen=chess.STARTING_FEN)
    game.start_game(engine_color=chess.BLACK)

