import chess
from engine.Eval import Eval

class Agent:
    def __init__(self, engine_color: chess.Color = chess.BLACK):
        self.evaluator = Eval(engine_color)

    def alpha_beta(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool) -> tuple[float, chess.Move | None]:
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board, depth), None

        best_move = None
        legal_moves = list(board.legal_moves)
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval, _ = self.alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval > max_eval:
                    best_move = move
                    max_eval = eval
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval, _ = self.alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                if eval < min_eval:
                    best_move = move
                    min_eval = eval
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def alpha_beta_with_trace(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool
                   ) -> tuple[float, chess.Move | None, list[chess.Move]]:
        if depth == 0 or board.is_game_over():
            return self.evaluator.evaluate(board, depth), None, []

        best_move = None
        best_line: list[chess.Move] = []

        legal_moves = list(board.legal_moves)
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval, _, line = self.alpha_beta_with_trace(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                    best_line = [move] + line
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move, best_line
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval, _, line = self.alpha_beta_with_trace(board, depth - 1, alpha, beta, True)
                board.pop()
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                    best_line = [move] + line
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move, best_line

    def test_with_stack_trace(self, board: chess.Board):
        score, move, line = self.alpha_beta_with_trace(board, 4, float('-inf'), float('inf'), True)
        print(f"Best Move: {move}")
        print(f"Principal Variation:")
        for ply in line:
            print(board.san(ply))
            board.push(ply)