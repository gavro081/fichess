import unittest
import chess
from chess import STARTING_FEN
import chess.engine

from engine.Agent import Eval


class TestEval(unittest.TestCase):
    evaluator = Eval()
    def test_eval_board(self):
        board = chess.Board(fen="N2K3N/8/8/4n3/2n5/8/8/3k4 w - - 0 1")
        black_score = self.evaluator.evaluate_board(board, color=chess.BLACK)
        white_score = self.evaluator.evaluate_board(board, color=chess.WHITE)
        self.assertGreater(black_score, white_score, "knights in the middle aren't worth more than knights in corners.")

    def test_pawn_development(self):
        board = chess.Board(fen="rnbqkbnr/pp1pp1pp/2p5/5p2/3P4/4P3/PPP2PPP/RNBQKBNR w KQkq f6 0 1")
        score = self.evaluator.evaluate_pawn_development(board, color=chess.WHITE)
        self.assertGreater(score, 0, "white doesn't have an advantage even though his pawns are better developed.")

    def test_pawn_structure(self):
        board = chess.Board(fen=STARTING_FEN)
        score_black = self.evaluator.evaluate_pawn_structure(board, chess.BLACK)
        score_white = self.evaluator.evaluate_pawn_structure(board, chess.WHITE)
        self.assertEqual(score_black, score_white, "the pawn related penalties are not equal to the benefits for both sides.")
        self.assertEqual(score_black, 0, "the score for the pawn structure is not 0 in the start")

    def test_pawn_structure2(self):
        board = chess.Board(fen="8/5k2/3p4/1P6/8/8/3P4/4K3 w - - 0 1")
        score_white = self.evaluator.evaluate_pawn_structure(board, chess.WHITE)
        self.assertGreater(score_white, 0, "white has an isolated, passed pawn; boost is not greater then the penalty")

    def test_pawn_structure3(self):
        board = chess.Board(fen="8/5k2/3p4/8/3P4/3p4/8/4K3 w - - 0 1")
        score_white = self.evaluator.evaluate_pawn_structure(board, chess.WHITE)
        self.assertLess(score_white, 0, "black has a passed pawn, white's should be losing.")

    def test_king_safety_helper(self):
        board = chess.Board(fen="rnbq1bnr/ppppkppp/8/4p3/8/2NP4/PPP1PPPP/R1BQKBNR b KQ - 0 1")
        white_safety = self.evaluator.helper.king_safety_for_color(board, chess.WHITE)
        black_safety = self.evaluator.helper.king_safety_for_color(board, chess.BLACK)
        self.assertEqual(white_safety, 0, "white hasn't castled but can castle; no penalty should be given!")
        self.assertLess(black_safety, 0, "black can't castle and doesn't have pawn shield; penalty should be given!")

    def test_king_safety(self):
        board = chess.Board(fen="r1bk1br1/ppp1qppp/n2p1n2/4p3/2B5/1P2PN2/P1PP1PPP/RNBQ1RK1 w - - 0 1")
        ev_white = self.evaluator.evaluate_king_safety(board, chess.WHITE)
        ev_black = self.evaluator.evaluate_king_safety(board, chess.BLACK)
        self.assertGreater(ev_white, ev_black, "white has castled; black hasn't and can't; white should be safer.")

    def test_development(self):
        board = chess.Board(fen="rnb1kb1r/pppqpppp/3p1n2/8/4P3/2N2N2/PPPP1PPP/R1BQKB1R b KQkq e3 0 1")
        score = self.evaluator.evaluate_development(board, color=chess.WHITE)
        self.assertGreater(score, 0, "white has better piece development but is calculated as worse.")

    def test_score_material(self):
        board = chess.Board(fen="rnbqk2r/pppppppp/8/8/8/8/PP3PPP/RNBQKB1R w KQkq - 0 1")
        score = self.evaluator.evaluate_material(board, chess.WHITE)
        self.assertGreater(score, 0, "white should be winning; check consts.")

    def test_development_2(self):
        board = chess.Board(fen="r1bqkbr1/ppppp1pp/2n2p1n/8/7N/2NPP3/PPP2PPP/R1BQKB1R w KQkq - 0 1")
        score = self.evaluator.evaluate_development(board, chess.WHITE)
        self.assertGreater(score, 0, "rook g8 is not being penalized")

    def test_rook_files(self):
        board = chess.Board(fen="r1bqkb2/pppppp1p/7r/n7/8/N7/P1PP1P2/R2QK2R w - - 0 1")
        score = self.evaluator.evaluate_rook_files(board, chess.WHITE)
        self.assertEqual(score, 10, "white doesn't get an advantage for a semi open file that black doesn't have.")

    def test_center_control(self):
        board = chess.Board(fen="r1bqkb2/ppp1pp1p/8/n2p3r/8/3Q1N2/P1PP1P2/R3K2R w - - 0 1")
        score = self.evaluator.evaluate_center_control(board, chess.WHITE)
        self.assertGreater(score, 0, "center control advantage isn't evaluated properly")