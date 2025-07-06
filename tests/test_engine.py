import unittest
import chess
from chess import STARTING_FEN
import chess.engine

from engine.Agent import Agent, Eval

class TestEngine(unittest.TestCase):
    def test_engine_1(self):
        board = chess.Board(fen=STARTING_FEN)
        board.push_uci("d2d4")
        board.push_uci("g8h6")
        board.push_uci("c1h6")
        agent = Agent(engine_color=chess.BLACK)
        best_move, a = agent.alpha_beta(board, depth=1, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
        # self.assertIsNotNone(best_move)
        # self.assertTrue(best_move == chess.Move.from_uci("g7h6"))

    def test_engine_m1(self):
        board = chess.Board(fen="3q2k1/8/8/8/8/1P6/P6r/K7 b - - 0 1")
        agent = Agent(engine_color=chess.BLACK)
        best_move = agent.alpha_beta(board, depth=3, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)[1]
        self.assertIsNotNone(best_move)
        if best_move: board.push(best_move)
        self.assertTrue(board.is_checkmate())

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
        self.assertTrue(board.is_checkmate())

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

class TestEval(unittest.TestCase):
    def test_eval_board(self):
        eval_black = Eval(engine_color=chess.BLACK)
        eval_white = Eval(engine_color=chess.WHITE)
        board = chess.Board(fen="N2K3N/8/8/4n3/2n5/8/8/3k4 w - - 0 1")
        black_score = eval_black.evaluate_board(board, color=chess.BLACK)
        white_score = eval_white.evaluate_board(board, color=chess.WHITE)
        self.assertGreater(black_score, white_score)

    def test_pawn_structure(self):
        board = chess.Board(fen=STARTING_FEN)
        ev_black = Eval()
        ev_white = Eval()
        score_black = ev_black.check_pawn_structure(board, chess.BLACK)
        score_white = ev_white.check_pawn_structure(board, chess.WHITE)
        print(score_white)
        print(score_black)
        self.assertEqual(score_black, -score_white)
        self.assertEqual(score_black, 0)

    def test_pawn_structure2(self):
        board = chess.Board(fen="8/5k2/3p4/1P6/8/8/3P4/4K3 w - - 0 1")
        ev_white = Eval()
        score_white = ev_white.check_pawn_structure(board, chess.WHITE)
        self.assertGreater(score_white, 0)

    def test_pawn_structure3(self):
        board = chess.Board(fen="8/5k2/3p4/8/3P4/3p4/8/4K3 w - - 0 1")
        ev_white = Eval()
        score_white = ev_white.check_pawn_structure(board, chess.WHITE)
        self.assertLess(score_white, 0)

    def test_king_safety_helper(self):
        board = chess.Board(fen="rnbq1bnr/ppppkppp/8/4p3/8/2NP4/PPP1PPPP/R1BQKBNR b KQ - 0 1")
        ev = Eval()
        self.assertEqual(ev._calculate_king_safety_for_color(board, chess.WHITE), 0)
        self.assertLess(ev._calculate_king_safety_for_color(board, chess.BLACK), 0)

    def test_king_safety(self):
        board = chess.Board(fen="r1bk1br1/ppp1qppp/n2p1n2/4p3/2B5/1P2PN2/P1PP1PPP/RNBQ1RK1 w - - 0 1")
        ev = Eval(engine_color=chess.BLACK)
        ev_white = ev.check_king_safety(board, chess.WHITE)
        ev_black = ev.check_king_safety(board, chess.BLACK)
        self.assertGreater(ev_white, ev_black)