import chess
from chess import STARTING_FEN
from ui.Game import Game

if __name__ == '__main__':
    game = Game(fen=STARTING_FEN)
    # NOTE:
    # if playing with black or a starting fen where it is the engine's turn
    # wait ~5s before making the very first move (due to ui bug)
    game.start_game(engine_color=chess.BLACK, with_fen=False)
