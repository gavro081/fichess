import chess
from engine import consts

class Eval:
    def __init__(self, engine_color: chess.Color = chess.WHITE):
        self.max_depth = 3 # not used rn
        self.engine_color = engine_color
        self.mg_tables = consts.MG_TABLES
        self.eg_tables = consts.EG_TABLES
        self.phase_weights = consts.PHASE_WEIGHT
        self.total_phase = consts.TOTAL_PHASE_WEIGHT
        self.piece_scores = consts.piece_scores

    def check_pawn_structure(self, board: chess.Board) -> int:
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == self.engine_color else -1
            pawns = board.pieces(chess.PAWN, color)
            opp_pawns = board.pieces(chess.PAWN, not color)

            files = [0] * 8
            for square in pawns:
                files[chess.square_file(square)] += 1
            for square in pawns:
                file = chess.square_file(square)
                rank = chess.square_rank(square)

                # double pawns
                if files[file] > 1:
                    score -= sign * 20
                # isolated pawns
                has_left = (file > 0 and files[file - 1] > 0)
                has_right = (file < 7 and files[file + 1] > 0)
                if not has_left and not has_right:
                    score -= sign * 15
                # backward pawns
                direction = 1 if color == chess.WHITE else -1
                is_backward = True
                for df in [-1, 1]:
                    adj_file = file + df
                    if 0 <= adj_file < 8:
                        for r in range(rank + direction, 8 if color == chess.WHITE else -1, direction):
                            if chess.square(adj_file, r) in pawns:
                                is_backward = False
                                break
                if is_backward:
                    score -= sign * 10

                # passed pawns
                direction = 1 if color == chess.WHITE else -1
                is_passed = True
                for df in [-1, 0, 1]:
                    adj_file = file + df
                    if 0 <= adj_file < 8:
                        for r in range(rank + direction, 8 if color == chess.WHITE else -1, direction):
                            if chess.square(adj_file, r) in opp_pawns:
                                is_passed = False
                                break
                if is_passed:
                    score += sign * 30

        return score

    # def check_center_control(self, board: chess.Board) -> int:
    #     """
    #     Bonus for controlling central squares (e4, d4, e5, d5)
    #     """
    #     center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    #     score = 0
    #
    #     for square in center_squares:
    #         attackers = board.attackers(self.engine_color, square)
    #         score += len(attackers) * 3  # tunable weight
    #
    #         opponents = board.attackers(not self.engine_color, square)
    #         score -= len(opponents) * 3
    #
    #     return score

    def check_king_safety(self, board: chess.Board) -> int:
        raise NotImplementedError

    def legal_moves_count(self, board: chess.Board) -> int:
        raise NotImplementedError

    def check_piece_coordination(self, board: chess.Board) -> int:
        # double rooks, queen and bishop battery, Knight outposts protected by pawns
        raise NotImplementedError

    def evaluate_development(self, board: chess.Board) -> int:
        score = 0
        if board.fullmove_number > 10:
            return 0

        pieces = [chess.BISHOP, chess.KNIGHT, chess.PAWN]
        start_squares = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1, chess.C2, chess.D2, chess.E2, chess.F2],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8, chess.C7, chess.D7, chess.E7, chess.F7]
        }

        for sq in start_squares[self.engine_color]:
            piece = board.piece_at(sq)
            if piece and piece.piece_type in pieces and piece.color == self.engine_color:
                # TODO: find decent weights
                # score -= 30
                score -= 10

        return score

    # def check_opening(self, board: chess.Board) -> int:
    #     score = 0
    #     opening_phase = board.fullmove_number <= 10
    #     if not opening_phase: return 0
    #     # white
    #     for square in [chess.E4, chess.D4, chess.C4]:
    #         if board.piece_at(square) == chess.Piece(chess.PAWN, chess.WHITE):
    #             score += 15
    #     for square in [chess.B1, chess.G1]:
    #         if board.piece_at(square) == chess.Piece(chess.KNIGHT, chess.WHITE):
    #             score -= 10
    #     for square in [chess.C1, chess.F1]:
    #         if board.piece_at(square) == chess.Piece(chess.BISHOP, chess.WHITE):
    #             score -= 10
    #
    #     # black
    #     for square in [chess.E5, chess.D5, chess.C5]:
    #         if board.piece_at(square) == chess.Piece(chess.PAWN, chess.WHITE):
    #             score -= 15
    #     for square in [chess.B8, chess.G8]:
    #         if board.piece_at(square) == chess.Piece(chess.KNIGHT, chess.WHITE):
    #             score += 10
    #     for square in [chess.C8, chess.F8]:
    #         if board.piece_at(square) == chess.Piece(chess.BISHOP, chess.WHITE):
    #             score += 10

        # return score if self.engine_color == chess.WHITE else -score

    def check_mobility(self, board: chess.Board) -> int:
        # count legal moves per piece
        raise NotImplementedError

    def score_material(self, board: chess.Board) -> float:
        """
        calculate the material score of the board.
        the score is positive for the engine's pieces and negative for the opponent's pieces.
        :param board: chess.Board object representing the current state of the game
        :return: score of the board
        """
        # currently not used
        score = 0
        for piece in board.piece_map().values():
            score += consts.piece_scores[piece.piece_type] if piece.color == self.engine_color \
                else -consts.piece_scores[piece.piece_type]

        return score

    def evaluate_board(self, board: chess.Board) -> int:
        # ref https://www.chessprogramming.org/PeSTO%27s_Evaluation_Function
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

    def evaluate(self, board: chess.Board, depth: int) -> float:
        if board.is_checkmate():
            # if it is the engine's turn and it is checkmate, it means the engine has lost
            # give priority to mates that appear earlier in the search
            return -consts.MATE_SCORE + depth if board.turn == self.engine_color \
                else consts.MATE_SCORE + depth

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0
        e = self.evaluate_board(board)
        c = self.check_pawn_structure(board)
        d = self.evaluate_development(board)
        print(f"Eval: {e}, Pawn Structure: {c}, Development: {d}, Depth: {depth}")
        return e + c + d

        # score = self.evaluate_board(board)
        # score += self.check_pawn_structure(board)
        # score += self.evaluate_development(board)
        # return score



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