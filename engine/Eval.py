import chess
from engine import consts


class Eval:
    def __init__(self, engine_color: chess.Color = chess.WHITE, board: chess.Board | None = None):
        self.piece_scores = consts.piece_scores
        self.engine_color = engine_color
        self.mg_tables = consts.MG_TABLES
        self.eg_tables = consts.EG_TABLES
        self.phase_weights = consts.PHASE_WEIGHT
        self.total_phase = consts.TOTAL_PHASE_WEIGHT
        self.piece_scores = consts.piece_scores
        if board is not None:
            self.piece_map = board.piece_map()
            self.white_pawns = board.pieces(chess.PAWN, chess.WHITE)
            self.black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        else:
            self.white_pawns: chess.SquareSet | None = None
            self.black_pawns: chess.SquareSet | None = None
            self.piece_map: dict[chess.Square, chess.Piece] | None = None

    def evaluate_(self, board: chess.Board):
        return 0

    def setup(self, board: chess.Board):
        self.piece_map = board.piece_map()
        self.white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        self.black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    def evaluate(self, board: chess.Board, depth: int) -> float:
        side_to_evaluate = self.engine_color

        if board.is_checkmate():
            # if it is the engine's turn, and it is checkmate, it means the engine has lost
            # give priority to mates that appear earlier in the search
            return -consts.MATE_SCORE + depth if board.turn == side_to_evaluate \
                else consts.MATE_SCORE + depth

        if board.is_game_over():
            # if the game is over and there is no checkmate then it must be a draw
            return 0

        score = 0
        subclasses = Eval.__subclasses__()
        for sub in subclasses:
            a = sub(self.engine_color)
            a.setup(board)
            score += a.evaluate_(board)

        return score

class EvalRooks(Eval):
    def evaluate_(self, board: chess.Board):
        return self.evaluate_rook_files(board)

    def evaluate_rook_files(self, board: chess.Board) -> int:
        # open file is when there are no pawns on the file
        # semi open file is when there are only opposing pawns on the file
        score = 0
        pawn_files = {file: {'white': 0, 'black': 0} for file in range(8)}

        for pawn_square in self.white_pawns:
            pawn_files[chess.square_file(pawn_square)]['white'] += 1
        for pawn_square in self.black_pawns:
            pawn_files[chess.square_file(pawn_square)]['black'] += 1

        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == self.engine_color else -1
            for rook_square in board.pieces(chess.ROOK, color_):
                file = chess.square_file(rook_square)
                if pawn_files[file]['white'] == 0 and pawn_files[file]['black'] == 0:
                    score += 20 * sign  # open
                elif pawn_files[file][chess.COLOR_NAMES[color_]] == 0:
                    score += 10 * sign  # semi open

        return score


class EvalPieces(Eval):
    def evaluate_(self, board: chess.Board):
        return self.evaluate_center_control(board) + \
            self.evaluate_development(board) + \
            self.evaluate_material() + \
            self.evaluate_board() + \
            self.evaluate_progress_when_winning(board)

    def _is_endgame(self, board: chess.Board) -> bool:
        # not the most accurate way to label endgames, but it works
        total_pieces = len(self.piece_map)
        queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))

        return total_pieces <= 10 or queens == 0

    def evaluate_center_control(self, board: chess.Board):
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        score = 0
        for square in center_squares:
            attackers = board.attackers(self.engine_color, square)
            defenders = board.attackers(not self.engine_color, square)
            score += len(attackers) - len(defenders)
        return score * 5

    def evaluate_development(self, board: chess.Board) -> int:
        # evaluates knights, bishops, rooks
        score = 0
        if board.fullmove_number > 16:
            return 0

        undeveloped_squares = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8]
        }

        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == self.engine_color else -1
            for sq in undeveloped_squares[color_]:
                piece = board.piece_at(sq)
                if piece and piece.piece_type in [chess.BISHOP, chess.KNIGHT]:
                    score -= 20 * sign

        bad_rook_squares = {
            chess.WHITE: {chess.B1, chess.G1},
            chess.BLACK: {chess.B8, chess.G8},
        }

        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == self.engine_color else -1
            for sq in bad_rook_squares[color_]:
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.ROOK:
                    score -= 30 * sign

        return score

    def evaluate_material(self) -> float:
        score = 0
        for piece in self.piece_map.values():
            score += self.piece_scores[piece.piece_type] if piece.color == self.engine_color \
                else -self.piece_scores[piece.piece_type]
        return score

    def evaluate_board(self) -> float:
        # ref https://www.chessprogramming.org/PeSTO%27s_Evaluation_Function
        mg_score = 0
        eg_score = 0
        material_score = 0
        phase = 0

        for square, piece in self.piece_map.items():
            piece_type = piece.piece_type
            piece_color = piece.color

            index = square if piece_color == chess.WHITE else chess.square_mirror(square)
            sign = 1 if piece_color == self.engine_color else -1
            material_score += sign * self.piece_scores[piece_type]

            mg_score += sign * self.mg_tables[piece_type][index] * 0.2
            eg_score += sign * self.eg_tables[piece_type][index] * 0.2

            phase += self.phase_weights[piece_type]

        phase = min(phase, self.total_phase)
        score = ((phase * mg_score + (24 - phase) * eg_score) / self.total_phase)
        total_score = score + material_score
        return total_score

    def evaluate_progress_when_winning(self, board: chess.Board) -> int:

        engine_material = 0
        opponent_material = 0

        for piece in self.piece_map.values():
            value = self.piece_scores[piece.piece_type]
            if piece.color == self.engine_color:
                engine_material += value
            else:
                opponent_material += value

        material_advantage = engine_material - opponent_material

        if material_advantage < 330:
            return 0

        score = 0

        # encourage king to move towards center
        if self._is_endgame(board):
            king_square = board.king(self.engine_color)
            if king_square:
                file = chess.square_file(king_square)
                rank = chess.square_rank(king_square)
                file_dist = abs(file - 3)
                rank_dist = abs(rank - 3)
                center_bonus = (6 - (file_dist + rank_dist)) * 10
                score += max(0, center_bonus)

        # advance pawns
        pawns = board.pieces(chess.PAWN, self.engine_color)
        for pawn_square in pawns:
            rank = chess.square_rank(pawn_square)
            if self.engine_color == chess.WHITE:
                advancement_bonus = rank * 5
            else:
                advancement_bonus = (7 - rank) * 5
            score += advancement_bonus

        # move pieces closer to opponent's king
        opponent_king = board.king(not self.engine_color)
        if opponent_king:
            for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                pieces = board.pieces(piece_type, self.engine_color)
                for piece_square in pieces:
                    distance = chess.square_distance(piece_square, opponent_king)
                    score += (8 - distance) * 3

        return score


class EvalPawns(Eval):
    def evaluate_(self, board: chess.Board) -> float:
        return self.evaluate_pawn_structure() + self.evaluate_pawn_development(board)

    def _passed_pawn_for_color(self, pawns, opp_pawns, color) -> int:
        score = 0
        sign = 1 if self.engine_color == color else -1
        for pawn_square in pawns:
            is_passed = True
            pawn_file = chess.square_file(pawn_square)
            pawn_rank = chess.square_rank(pawn_square)

            for other_pawn_square in opp_pawns:
                other_pawn_file = chess.square_file(other_pawn_square)
                other_pawn_rank = chess.square_rank(other_pawn_square)

                if abs(pawn_file - other_pawn_file) <= 1:
                    if (color == chess.WHITE and other_pawn_rank > pawn_rank) or \
                            (color == chess.BLACK and other_pawn_rank < pawn_rank):
                        is_passed = False
                        break
            if is_passed:
                score += 30 * sign

        return score

    def evaluate_pawn_structure(self) -> int:
        score = 0
        if self.engine_color == chess.WHITE:
            pawns = self.white_pawns
            opp_pawns = self.black_pawns
        else:
            pawns = self.black_pawns
            opp_pawns = self.white_pawns

        files = [chess.square_file(sq) for sq in pawns]
        files_set = set(files)

        opp_files = [chess.square_file(sq) for sq in opp_pawns]
        opp_files_set = set(opp_files)

        # doubled pawns
        score -= (len(pawns) - len(files_set)) * 20
        score += (len(opp_pawns) - len(opp_files_set)) * 20

        # isolated pawn
        for file in files_set:
            if (file - 1) not in files_set and (file + 1) not in files_set:
                score -= 15
        for file in opp_files_set:
            if (file - 1) not in opp_files_set and (file + 1) not in opp_files_set:
                score += 15

        score += self._passed_pawn_for_color(pawns, opp_pawns, self.engine_color)
        score += self._passed_pawn_for_color(opp_pawns, pawns, not self.engine_color)

        return score


    def evaluate_pawn_development(self, board: chess.Board) -> int:
        if board.fullmove_number > 16:
            return 0
        score = 0
        important_files = [3, 4]
        less_important_files = [2, 5]
        for color_ in [chess.WHITE, chess.BLACK]:
            sign = 1 if color_ == self.engine_color else -1
            if color_ == chess.WHITE:
                second_rank, third_rank, fourth_rank = 1, 2, 3
                pawns = self.white_pawns
            else:
                second_rank, third_rank, fourth_rank = 6, 5, 4
                pawns = self.black_pawns

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


class EvalKing(Eval):
    def evaluate_(self, board: chess.Board):
        return self.evaluate_king_safety(board)

    def king_is_castled(self, board: chess.Board) -> bool:
        king_square = board.king(self.engine_color)
        if (self.engine_color == chess.WHITE and king_square in [chess.G1, chess.C1]) or \
                (self.engine_color == chess.BLACK and king_square in [chess.G8, chess.C8]): return True
        return False

    def _king_has_pawn_shield(self, board: chess.Board, color: chess.Color) -> bool:
        king_square = board.king(color)
        if not king_square:
            return False

        king_file = chess.square_file(king_square)

        if king_file < 2:
            pawn_files = [0, 1, 2]  # a, b, c files
        elif king_file > 5:
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

    def _king_safety_for_color(self, board: chess.Board, color: chess.Color):
        king = board.king(color)
        if not king:
            return 0
        king_rank = chess.square_rank(king)

        if self._king_has_pawn_shield(board, color) and king_rank == (0 if color == chess.WHITE else 7):
            return 50

        if not board.has_castling_rights(color):
            return -75

        return 0
    def evaluate_king_safety(self, board: chess.Board) -> int:
        engine_ks_score = self._king_safety_for_color(board, self.engine_color)
        opp_ks_score = self._king_safety_for_color(board, not self.engine_color)

        return engine_ks_score - opp_ks_score

