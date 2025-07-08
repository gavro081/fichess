import unittest
import chess
from chess import STARTING_FEN
import chess.engine
import time

from engine.Agent import Agent

class TestEngine(unittest.TestCase):
    agent_black = Agent(engine_color=chess.BLACK)

    # def test_is_castling(self):
    #     # za ovoj board, ne castlenuva
    #     board = chess.Board(fen="r3k2r/pppppppp/3n4/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
    #     # za ovoj board, castlenuva
    #     # board = chess.Board(fen="r3k2r/pppppppp/8/8/2n5/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
    #     is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
    #     move = self.agent_black.alpha_beta(board, 3, alpha=float('-inf'), beta=float('inf'),
    #                                        maximizing_player=is_maximizing_player)[1]
    #     print(move)
    #     self.assertIsNotNone(move, "Expected a castling move, but got None")

    def test_engine_1(self):
        board = chess.Board(fen=STARTING_FEN)
        board.push_uci("d2d4")
        board.push_uci("g8h6")
        board.push_uci("c1h6")
        is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
        move1 = self.agent_black.alpha_beta(board, depth=1, alpha=float('-inf'), beta=float('inf'), maximizing_player = is_maximizing_player)[1]
        move2 = self.agent_black.alpha_beta(board, depth=2, alpha=float('-inf'), beta=float('inf'), maximizing_player = is_maximizing_player)[1]
        move3 = self.agent_black.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player = is_maximizing_player)[1]
        move4 = self.agent_black.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player = is_maximizing_player)[1]

        self.assertTrue(move1 == move2 == move3 == move4, f"moves are not the same across all depths, right move is g7h6")

    def test_engine_m1(self):
        board = chess.Board(fen="3q2k1/8/8/8/8/1P6/P6r/K7 b - - 0 1")
        is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
        move = self.agent_black.alpha_beta(board, 4, alpha=float('-inf'), beta=float('inf'),
                                           maximizing_player=is_maximizing_player)[1]
        self.assertIsNotNone(move)
        if move: board.push(move)
        self.assertTrue(board.is_checkmate(), "can't find trivial mate in 1")

    def test_engine_m2(self):
        board = chess.Board(fen="8/8/8/8/8/1r6/K7/3k4 b - - 0 1")
        is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
        move = self.agent_black.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'),
                                           maximizing_player=is_maximizing_player)[1]
        self.assertIsNotNone(move)
        if move: board.push(move)
        board.push_uci("a2a1")
        is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
        move = self.agent_black.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player = is_maximizing_player)[1]
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
                is_maximizing_player = board.turn == self.agent_black.evaluator.engine_color
                move = self.agent_black.alpha_beta(board, 3, alpha=float('-inf'), beta=float('inf'),
                                                   maximizing_player=is_maximizing_player)[1]
                with chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish") as engine:
                    result = engine.play(board, chess.engine.Limit(time=0.4))
                    self.assertTrue(move == result.move, f"Expected move {result.move}, got {move}, fen: {fen}")

    def test_quiescence_1(self):
        board = chess.Board(fen="rnb1kbnr/pppp1ppp/4p3/8/6Pq/P1N5/1PPPPP1P/R1BQKBNR b KQkq - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        best_move1 = agent.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        board = chess.Board(fen="rnb1kbnr/pppp1ppp/4p3/8/6Pq/P1N5/1PPPPP1P/R1BQKBNR b KQkq - 0 1")
        best_move2 = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertEqual(best_move1, best_move2, "quiescence gives wrong result on either odd or even depths")

    # def test_engine_move_sorting(self):
    #     board = chess.Board(fen="r2qk2r/p1p2ppp/1pb1pn2/2bp4/4P3/1PNB1N2/PBPPQPPP/R4RK1 b - - 0 1")
    #     agent = Agent(engine_color=chess.BLACK)
    #     # Test without sorting
    #     start_time = time.time()
    #     _, move = agent.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player = (board.turn == agent.evaluator.engine_color),
    #                                sorted=False)
    #     end_time = time.time()
    #     print(f"Time without sorting: {end_time - start_time:.4f} seconds, move: {move}")
    #     start_time = time.time()
    #     _, move = agent.alpha_beta(board, depth=4, alpha=float('-inf'), beta=float('inf'), maximizing_player = (board.turn == agent.evaluator.engine_color), sorted=True)
    #     end_time = time.time()
    #     print(f"Time with sorting: {end_time - start_time:.4f} seconds, move: {move}")
