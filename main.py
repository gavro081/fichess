import chess
from ui.Game import Game

if __name__ == '__main__':
    game = Game(fen=chess.STARTING_BOARD_FEN)
    game.start_game(engine_color=chess.BLACK)

