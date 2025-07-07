import unittest
import chess
from chess import STARTING_FEN
import chess.engine

from engine.Agent import Agent

class TestEngine(unittest.TestCase):
    def test_engine_1(self):
        board = chess.Board(fen=STARTING_FEN)
        board.push_uci("d2d4")
        board.push_uci("g8h6")
        board.push_uci("c1h6")
        agent = Agent(engine_color=chess.BLACK)
        _, move1 = agent.alpha_beta(board, depth=1, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        _, move2 = agent.alpha_beta(board, depth=2, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        _, move3 = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        _, move4 = agent.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)

        self.assertTrue(move1 == move2 == move3 == move4, f"moves are not the same across all depths, right move is g7h6")

    def test_engine_m1(self):
        board = chess.Board(fen="3q2k1/8/8/8/8/1P6/P6r/K7 b - - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        best_move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(best_move)
        if best_move: board.push(best_move)
        self.assertTrue(board.is_checkmate(), "can't find trivial mate in 1")

    def test_engine_m2(self):
        board = chess.Board(fen="8/8/8/8/8/1r6/K7/3k4 b - - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(move)
        if move: board.push(move)
        board.push_uci("a2a1")
        move = agent.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(move)
        if move: board.push(move)
        self.assertTrue(board.is_checkmate(), "can't find trivial mate in 2")

    def test_engine_against_stockfish(self):
        fen1 = "1r2k2r/pp3ppp/8/3R1n2/2P2P2/P5PP/2R4K/2B5 b - - 0 14"
        fen2 = "1r6/pp3pp1/1k6/3RRP2/2P3Kp/P2rB2P/8/8 b - - 0 14"
        fens = [fen1, fen2]
        for fen in fens:
            with self.subTest(fen=fen):
                board = chess.Board(fen=fen)
                agent = Agent(engine_color=chess.BLACK)
                _, move = agent.alpha_beta(board, 3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
                with chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish") as engine:
                    result = engine.play(board, chess.engine.Limit(time=0.4))
                    self.assertTrue(move == result.move, f"Expected move {result.move}, got {move}, fen: {fen}")

