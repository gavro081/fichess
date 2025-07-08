import chess

from ui.Game import Game

if __name__ == '__main__':
    game = Game(fen=chess.STARTING_FEN)
    # NOTE:
    # if playing with black, wait ~5s before making the very first move
    game.start_game(engine_color=chess.BLACK, with_fen=False)
