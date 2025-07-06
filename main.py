import chess
from chess import Board
from chess import STARTING_BOARD_FEN
from engine.Agent import Agent, Eval
from engine.consts import MG_TABLES, EG_TABLES

from ui.Game import Game

if __name__ == '__main__':
    game = Game(fen=chess.STARTING_FEN)
    game.start_game(engine_color=chess.BLACK, with_fen=False)

