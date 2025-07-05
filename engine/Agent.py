import chess
from engine import consts

MATE_SCORE = 1000000

class Eval:
    def __init__(self, engine_color: chess.Color = chess.WHITE):
        self.max_depth = 3 # not used rn
        self.engine_color = engine_color
        self.mg_tables = consts.MG_TABLES
        self.eg_tables = consts.EG_TABLES
        self.phase_weights = consts.PHASE_WEIGHT
        self.total_phase = consts.TOTAL_PHASE_WEIGHT
        self.piece_scores = consts.piece_scores
    # def count_material(self, board: chess.Board) -> int:
    #     material = 0
    #     for piece in board.piece_map().values():
    #         if piece.color == chess.WHITE:
    #             material += piece.piece_type
    #         else:
    #             material -= piece.piece_type
    #     return material

    def score_material(self, board: chess.Board) -> float:
        """
        calculate the material score of the board.
        the score is positive for the engine's pieces and negative for the opponent's pieces.
        :param board: chess.Board object representing the current state of the game
        :return: score of the board
        """
        score = 0
        for piece in board.piece_map().values():
            score += consts.piece_scores[piece.piece_type] if piece.color == self.engine_color \
                else -consts.piece_scores[piece.piece_type]

        return score

    def evaluate(self, board: chess.Board, depth: int) -> float:
        if board.is_checkmate():
            # if it is the engine's turn and it is checkmate, it means the engine has lost
            # give priority to mates that appear earlier in the search
            return -MATE_SCORE + depth if board.turn == self.engine_color else MATE_SCORE + depth

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0

        score = self.evaluate_board(board)
        return score

    def evaluate_board(self, board: chess.Board) -> int:
        mg_score = 0
        eg_score = 0
        material_score = 0
        phase = 0

        for square, piece in board.piece_map().items():
            piece_type = piece.piece_type
            color = piece.color

            index = square if color == chess.WHITE else chess.square_mirror(square)
            sign = 1 if color == chess.WHITE else -1
            material_score += sign * self.piece_scores[piece_type]

            mg_score += sign * self.mg_tables[piece_type][index]
            eg_score += sign * self.eg_tables[piece_type][index]

            phase += self.phase_weights[piece_type]

        phase = min(phase, self.total_phase)
        score = (phase * mg_score + (24 - phase) * eg_score) // self.total_phase
        total_score = score + material_score
        return total_score if self.engine_color == chess.WHITE else -total_score


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