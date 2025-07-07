import chess

from engine import consts

class EvalHelper:
    @staticmethod
    def king_is_castled(board: chess.Board, color: chess.Color) -> bool:
        king_square = board.king(color)
        if (color == chess.WHITE and king_square in [chess.G1, chess.C1]) or \
                (color == chess.BLACK and king_square in [chess.G8, chess.C8]): return True
        return False

    @staticmethod
    def king_has_pawn_shield(board: chess.Board, color: chess.Color) -> bool:
        king_square = board.king(color)
        if not king_square:
            return False

        king_file = chess.square_file(king_square)

        if king_file < 3:
            pawn_files = [0, 1, 2]  # a, b, c files
        elif king_file > 4:
            pawn_files = [5, 6, 7]  # f, g, h files
        else:
            return False

        pawn_rank = chess.square_rank(king_square) + (1 if color == chess.WHITE else -1)
        if not (0 < pawn_rank < 7):
            return False

        shield_count = 0
        for file in pawn_files:
            pawn = board.piece_at(chess.square(file, pawn_rank))
            if pawn and pawn.piece_type == chess.PAWN and pawn.color == color:
                shield_count += 1

        return shield_count >= 2

    def king_safety_for_color(self, board: chess.Board, color: chess.Color):
        king = board.king(color)
        if not king:
            return 0
        king_rank = chess.square_rank(king)

        if self.king_has_pawn_shield(board, color) and king_rank == (0 if color == chess.WHITE else 7):
            return 50

        if not board.has_castling_rights(color):
            return -75

        return 0

class Eval:
    def __init__(self, engine_color: chess.Color = chess.WHITE):
        self.max_depth = 3 # not used rn
        self.engine_color = engine_color
        self.mg_tables = consts.MG_TABLES
        self.eg_tables = consts.EG_TABLES
        self.phase_weights = consts.PHASE_WEIGHT
        self.total_phase = consts.TOTAL_PHASE_WEIGHT
        self.piece_scores = consts.piece_scores
        self.helper = EvalHelper()

    def check_piece_coordination(self, board: chess.Board) -> int:
        # double rooks, queen and bishop battery, Knight outposts protected by pawns
        raise NotImplementedError

    def evaluate_rook_files(self, board: chess.Board, color: chess.Color) -> int:
        # open file is when there are no pawns on the file
        # semi open file is when there are only opposing pawns on the file
        score = 0
        for color_ in [chess.WHITE, chess.BLACK]:
            for square in board.pieces(chess.ROOK, color_):
                sign = 1 if color_ == color else -1
                file = chess.square_file(square)
                open_file = True
                semi_open = True
                for rank in range(8):
                    piece = board.piece_at(chess.square(file, rank))
                    if piece and piece.piece_type == chess.PAWN:
                        if piece.color == color_:
                            open_file = False
                            semi_open = False
                            break
                        else:
                            open_file = False
                if open_file:
                    score += 20 * sign
                elif semi_open:
                    score += 10 * sign

        return score

    def evaluate_center_control(self, board: chess.Board, color: chess.Color):
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        score = 0
        for square in center_squares:
            attackers = board.attackers(color, square)
            defenders = board.attackers(not color, square)
            score += len(attackers) - len(defenders)
        return score * 5

    def evaluate_legal_moves(self, board: chess.Board) -> int:
        board_ = board.copy()
        score = 0
        score += len(list(board_.legal_moves))
        board_.turn = not board_.turn
        score -= len(list(board_.legal_moves))
        return score * 2

    def evaluate_pawn_structure(self, board: chess.Board, color: chess.Color) -> int:
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

    def evaluate_pawn_development(self, board: chess.Board, color: chess.Color) -> int:
        if board.fullmove_number > 16:
            return 0
        score = 0
        important_files = [3,4]
        less_important_files = [2,5]
        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == color else -1
            if color_ == chess.WHITE:
                second_rank, third_rank, fourth_rank = 1, 2, 3
            else:
                second_rank, third_rank, fourth_rank = 6, 5, 4

            pawns = board.pieces(chess.PAWN, color_)
            for square in pawns:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                if file in important_files:
                    if rank == second_rank:
                        score -= 15 * sign
                    elif rank == third_rank:
                        score += 10 * sign
                    elif rank == fourth_rank:
                        score += 20 * sign
                elif file in less_important_files:
                    if rank == second_rank:
                        score -= 5 * sign
                    elif rank == third_rank:
                        score += 5 * sign
                    elif rank == fourth_rank:
                        score += 10 * sign
        return score

    def evaluate_king_safety(self, board: chess.Board, color: chess.Color) -> int:
        engine_ks_score = self.helper.king_safety_for_color(board, color)
        opp_ks_score = self.helper.king_safety_for_color(board, not color)

        return engine_ks_score - opp_ks_score

    def evaluate_development(self, board: chess.Board, color: chess.Color) -> int:
        # evaluates knights, bishops, rooks
        score = 0
        if board.fullmove_number > 16:
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
                    score -= 20 * sign

        bad_rook_squares = {
            chess.WHITE: {chess.B1, chess.G1},
            chess.BLACK: {chess.B8, chess.G8},
        }

        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == color else -1
            for sq in bad_rook_squares[color_]:
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.ROOK:
                    score -= 30 * sign

        return score

    def evaluate_material(self, board: chess.Board, color: chess.Color) -> float:
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

            # TODO: find better weights
            mg_score += sign * self.mg_tables[piece_type][index] * 0.5
            eg_score += sign * self.eg_tables[piece_type][index] * 0.5

            phase += self.phase_weights[piece_type]

        phase = min(phase, self.total_phase)
        score = ((phase * mg_score + (24 - phase) * eg_score) / self.total_phase)
        # print(f"Phase: {phase}, MG Score: {mg_score}, EG Score: {eg_score}, Material Score: {material_score}")
        # print(f"Score: {score}, Material Score: {material_score}")
        total_score = score + material_score
        return total_score

    def evaluate(self, board: chess.Board, depth: int, color: chess.Color | None = None) -> float:
        side_to_evaluate = self.engine_color if not color else color
        if board.is_checkmate():
            # if it is the engine's turn and it is checkmate, it means the engine has lost
            # give priority to mates that appear earlier in the search
            return -consts.MATE_SCORE + depth if board.turn == side_to_evaluate \
                else consts.MATE_SCORE + depth

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0

        e = self.evaluate_board(board, side_to_evaluate) if board.fullmove_number > 10 else self.evaluate_material(board, side_to_evaluate)
        c = self.evaluate_pawn_structure(board, side_to_evaluate)
        d = self.evaluate_development(board, side_to_evaluate)
        k = self.evaluate_king_safety(board, side_to_evaluate)
        p = self.evaluate_pawn_development(board, side_to_evaluate)
        m = self.evaluate_legal_moves(board)
        cc = self.evaluate_center_control(board, side_to_evaluate)
        r = self.evaluate_rook_files(board, side_to_evaluate)
        score = e + c + d + k + p + m + cc + r

        return score
