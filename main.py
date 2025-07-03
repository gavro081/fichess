import chess

from fichess.consts import ENDGAME_FEN, MIDDLE_GAME_FEN
from ui.Game import Game 

if __name__ == '__main__':
    game = Game(fen=chess.STARTING_BOARD_FEN)
    game.start_game()

