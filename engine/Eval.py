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

    def check_center_control(self, board: chess.Board) -> int:
        raise NotImplementedError

    def legal_moves_count(self, board: chess.Board) -> int:
        raise NotImplementedError

    def check_piece_coordination(self, board: chess.Board) -> int:
        # double rooks, queen and bishop battery, Knight outposts protected by pawns
        raise NotImplementedError

    def check_mobility(self, board: chess.Board) -> int:
        # count legal moves per piece
        raise NotImplementedError

    def check_pawn_structure(self, board: chess.Board, color: chess.Color) -> int:
        # TODO: clean up
        score = 0
        # doubled pawns
        pawns = board.pieces(chess.PAWN, color)
        opp_pawns = board.pieces(chess.PAWN, not color)
        file_rank_pawns = {}
        file_rank_opp_pawns = {}
        opp_files = [0] * 8
        files = [0] * 8
        for square in pawns:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            files[file] += 1
            if file not in file_rank_pawns:
                file_rank_pawns[file] = []
            file_rank_pawns[file].append(rank)
            if files[file] > 1: score -= 20

        for square in opp_pawns:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            opp_files[file] += 1
            if file not in file_rank_opp_pawns:
                file_rank_opp_pawns[file] = []
            file_rank_opp_pawns[file].append(rank)
            if opp_files[file] > 1: score += 20

        # isolated pawn
        for file in range(8):
            has_left = (file > 0 and files[file - 1] > 0)
            has_right = (file < 7 and files[file + 1] > 0)
            if not has_left and not has_right:
                score -= 15
            opp_has_left = (file > 0 and opp_files[file - 1] > 0)
            opp_has_right = (file < 7 and opp_files[file + 1] > 0)
            if not opp_has_left and not opp_has_right:
                score += 15

        # passed pawn
        for file in range(8):
            if files[file] == 0:
                continue
            passed = True
            for delta in [-1, 0, 1]:
                if not passed: continue
                adj_file = file + delta
                if 0 <= adj_file < 8 and adj_file in file_rank_opp_pawns:
                    for opp_rank in file_rank_opp_pawns[adj_file]:
                        if color == chess.WHITE and opp_rank >= max(file_rank_pawns[file]):
                            passed = False
                        elif color == chess.BLACK and opp_rank <= min(file_rank_pawns[file]):
                            passed = False
            if passed:
                score += 30

        for file in range(8):
            if opp_files[file] == 0:
                continue
            passed = True
            for delta in [-1, 0, 1]:
                if not passed: continue
                adj_file = file + delta
                if 0 <= adj_file < 8 and adj_file in file_rank_pawns:
                    for my_rank in file_rank_pawns[adj_file]:
                        if not color == chess.WHITE and my_rank >= max(file_rank_opp_pawns[file]):
                            passed = False
                        elif not color == chess.BLACK and my_rank <= min(file_rank_opp_pawns[file]):
                            passed = False
            if passed:
                score -= 30

        return score

    def _king_is_castled(self, board: chess.Board, color: chess.Color) -> bool:
        king_square = board.king(color)
        if not king_square:
            return False
        if color == chess.WHITE:
            if king_square == chess.G1 and (board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE) or
                                            board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE)):
                return True
            if king_square == chess.C1 and (board.piece_at(chess.D1) == chess.Piece(chess.ROOK, chess.WHITE) or
                                            board.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE)):
                return True
        else:
            if king_square == chess.G8 and (board.piece_at(chess.F8) == chess.Piece(chess.ROOK, chess.BLACK) or
                                            board.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK)):
                return True
            if king_square == chess.C8 and (board.piece_at(chess.D8) == chess.Piece(chess.ROOK, chess.BLACK) or
                                            board.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.BLACK)):
                return True
        return False

    def check_king_safety(self, board: chess.Board, color: chess.Color) -> int:
        engine_ks_score = self._calculate_king_safety_for_color(board, color)
        opp_ks_score = self._calculate_king_safety_for_color(board, not color)

        # a positive score means the evaluated color's king is safer than the opponent's
        return engine_ks_score - opp_ks_score

    def _calculate_king_safety_for_color(self, board: chess.Board, color: chess.Color):
        if not board.has_castling_rights(color) and not self._king_is_castled(board, color):
            # TODO: find ok weight
            return -100
        return 0

    def evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        # only looks at minor pieces, TODO: handle pawns
        score = 0
        if board.fullmove_number > 10:
            return 0

        undeveloped_squares = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8]
        }

        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == color else -1
            for sq in undeveloped_squares[color_]:
                piece = board.piece_at(sq)
                if piece and piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                    score -= 15 * sign

        return score

    def score_material(self, board: chess.Board, color: chess.Color) -> float:
        score = 0
        for piece in board.piece_map().values():
            score += self.piece_scores[piece.piece_type] if piece.color == color \
                else -self.piece_scores[piece.piece_type]
        return score

    def evaluate_board(self, board: chess.Board, color: chess.Color) -> float:
        # ref https://www.chessprogramming.org/PeSTO%27s_Evaluation_Function
        mg_score = 0
        eg_score = 0
        material_score = 0
        phase = 0

        for square, piece in board.piece_map().items():
            piece_type = piece.piece_type
            piece_color = piece.color

            index = square if piece_color == chess.WHITE else chess.square_mirror(square)
            sign = 1 if piece_color == color else -1
            material_score += sign * self.piece_scores[piece_type]

            mg_score += sign * self.mg_tables[piece_type][index]
            eg_score += sign * self.eg_tables[piece_type][index]

            phase += self.phase_weights[piece_type]

        phase = min(phase, self.total_phase)
        score = ((phase * mg_score + (24 - phase) * eg_score) / self.total_phase) * 0.50
        # print(f"Phase: {phase}, MG Score: {mg_score}, EG Score: {eg_score}, Material Score: {material_score}")
        # print(f"Score: {score}, Material Score: {material_score}")
        total_score = score + material_score
        return total_score

    def evaluate(self, board: chess.Board, depth: int) -> float:
        if board.is_checkmate():
            # if it is the engine's turn and it is checkmate, it means the engine has lost
            # give priority to mates that appear earlier in the search
            return -consts.MATE_SCORE + depth if board.turn == self.engine_color \
                else consts.MATE_SCORE + depth

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0
        side_to_evaluate = board.turn
        e = self.evaluate_board(board, side_to_evaluate) if board.fullmove_number > 6 else self.score_material(board, side_to_evaluate)
        c = self.check_pawn_structure(board, side_to_evaluate)
        d = self.evaluate_development(board, side_to_evaluate)
        k = self.check_king_safety(board, side_to_evaluate)
        score = e + c + d + k
        return score
