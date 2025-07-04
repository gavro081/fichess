import unittest
import chess
from chess import STARTING_FEN

from engine.Agent import Agent

class TestEngine(unittest.TestCase):
    def test_engine_1(self):
        board = chess.Board(fen=STARTING_FEN)
        board.push_uci("d2d4")
        board.push_uci("g8h6")
        board.push_uci("c1h6")
        agent = Agent(engine_color=chess.BLACK)
        best_move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(best_move)
        self.assertTrue(best_move == chess.Move.from_uci("g7h6"))

    def test_engine_m1(self):
        board = chess.Board(fen="3q2k1/8/8/8/8/1P6/P6r/K7 b - - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        best_move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(best_move)
        board.push(best_move)
        self.assertTrue(board.is_checkmate())

    def test_engine_m2(self):
        board = chess.Board(fen="8/8/8/8/8/1r6/K7/3k4 b - - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(move)
        board.push(move)
        board.push_uci("a2a1")
        move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(move)
        board.push(move)
        self.assertTrue(board.is_checkmate())



