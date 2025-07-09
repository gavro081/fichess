from collections import defaultdict

import chess
from engine.Eval import Eval
from enum import Enum
from collections import namedtuple


class NodeType(Enum):
    EXACT = 1
    LOWER_BOUND = 2
    UPPER_BOUND = 3

TTEntry = namedtuple('TTEntry', ['value', 'depth', 'flag', 'best_move'])

# TODO
MAX_QS_DEPTH = 6

MAX_SEARCH_DEPTH = 4

class Agent:
    def __init__(self, engine_color: chess.Color = chess.BLACK):
        self.evaluator = Eval(engine_color)
        self.killer_moves: dict[int, list[chess.Move]] = defaultdict(list)
        self.history_heuristic = defaultdict(int)
        self.transposition_table: dict[int, TTEntry] = {}

        random.seed(2025)
        self.zobrist_piece = [[[random.getrandbits(64) for _ in range(64)] for _ in range(2)] for _ in range(6)]
        self.zobrist_castling = [random.getrandbits(64) for _ in range(16)] # 4 bits: KQkq
        self.zobrist_ep_file = [random.getrandbits(64) for _ in range(8)]
        self.zobrist_turn = random.getrandbits(64)

        self.counter = 0

    def zobrist_hash(self, board: chess.Board) -> int:
        # ref https://www.chessprogramming.org/Zobrist_Hashing
        h = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_index = piece.piece_type - 1
                color_index = 0 if piece.color == chess.WHITE else 1
                h ^= self.zobrist_piece[piece_index][color_index][square]

        castling_rights = 0
        if board.has_kingside_castling_rights(chess.WHITE): castling_rights |= 1 << 3
        if board.has_queenside_castling_rights(chess.WHITE): castling_rights |= 1 << 2
        if board.has_kingside_castling_rights(chess.BLACK): castling_rights |= 1 << 1
        if board.has_queenside_castling_rights(chess.BLACK): castling_rights |= 1 << 0

        if board.ep_square is not None:
            ep_file = chess.square_file(board.ep_square)
            h ^= self.zobrist_ep_file[ep_file]

        if board.turn == chess.BLACK:
            h ^= self.zobrist_turn

        return h

    def score_move(self, board: chess.Board, move: chess.Move, depth: int) -> int:
        score = 0

        # killer moves
        if move in self.killer_moves.get(depth, []):
            return 8_000

        # MVV-LVA
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if captured and attacker:
                score += 10_000 + (self.evaluator.piece_scores[captured.piece_type] -
                                   self.evaluator.piece_scores[attacker.piece_type])

        # promotion
        if move.promotion:
            score += 9_000 + self.evaluator.piece_scores[move.promotion]

        # history heuristic
        # score += self.history_heuristic[(move.from_square, move.to_square)] // 10

        # checks
        if board.gives_check(move):
            score += 100

        # castling
        if board.is_castling(move):
            score += 200

        # center control
        if move.to_square in {chess.D4, chess.E4, chess.D5, chess.E5}:
            score += 100

        # development (early game)
        if board.fullmove_number <= 10:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                start_rank = 0 if piece.color == chess.WHITE else 7
                if chess.square_rank(move.from_square) == start_rank:
                    score += 100

        return score

    def alpha_beta(
            self,
            board: chess.Board,
            depth: int,
            alpha: float,
            beta: float,
            maximizing_player: bool,
            last_move_was_check: bool = False
            ) -> tuple[float, chess.Move | None]:
        if depth == 0 or board.is_game_over():
            return self.quiescence_minimax(board, depth, 0, alpha, beta, maximizing_player), None
            # return self.evaluator.evaluate(board, depth), None

        key = self.zobrist_hash(board)
        alpha_original = alpha

        if key in self.transposition_table:
            value, stored_depth, flag, stored_move = self.transposition_table[key]
            if stored_depth >= depth:
                if flag == NodeType.EXACT:
                    return value, stored_move
                elif flag == NodeType.LOWER_BOUND and value >= beta:
                    return value, stored_move
                elif flag == NodeType.UPPER_BOUND and value <= alpha:
                    return value, stored_move

        best_move = None
        legal_moves = list(board.legal_moves)

        if key in self.transposition_table:
            _, _, _, tt_move = self.transposition_table[key]
            if tt_move in legal_moves:
                legal_moves.remove(tt_move)
                legal_moves.insert(0, tt_move)

        move_scores = [(self.score_move(board, move, depth), move) for move in legal_moves]
        move_scores.sort(key=lambda x: x[0], reverse=maximizing_player)
        sorted_moves = [move for _, move in move_scores]

        if maximizing_player:
            max_score = float('-inf')
            for move in sorted_moves:
                is_check = board.gives_check(move)

                if is_check:
                    eval_before = self.evaluator.evaluate(board, depth)

                board.push(move)
                score, _ = self.alpha_beta(board, depth - 1, alpha, beta, False, is_check)
                board.pop()

                if is_check and last_move_was_check:
                    eval_gain = score - eval_before
                    if eval_gain < 50:
                        score -= 50

                if score > max_score:
                    best_move = move
                    max_score = score
                alpha = max(alpha, score)
                if beta <= alpha:
                    if depth not in self.killer_moves:
                        self.killer_moves[depth] = []
                    if move not in self.killer_moves[depth]:
                        self.killer_moves[depth].append(move)
                    break
            if max_score <= alpha_original:
                flag = NodeType.UPPER_BOUND
            elif max_score >= beta:
                flag = NodeType.LOWER_BOUND
            else:
                flag = NodeType.EXACT
            self.transposition_table[key] = TTEntry(max_score, depth, flag, best_move)
            return max_score, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                is_check = board.gives_check(move)

                if is_check:
                    eval_before = self.evaluator.evaluate(board, depth)

                board.push(move)
                score, _ = self.alpha_beta(board, depth - 1, alpha, beta, True, is_check)
                board.pop()

                if is_check and last_move_was_check:
                    eval_gain = eval_before - score
                    if eval_gain < 50:
                        score += 50

                if score < min_eval:
                    best_move = move
                    min_eval = score
                beta = min(beta, score)
                if beta <= alpha:
                    if depth not in self.killer_moves:
                        self.killer_moves[depth] = []
                    if move not in self.killer_moves[depth]:
                        self.killer_moves[depth].append(move)
                    break
            if min_eval <= alpha_original:
                flag = NodeType.UPPER_BOUND
            elif min_eval >= beta:
                flag = NodeType.LOWER_BOUND
            else:
                flag = NodeType.EXACT
            self.transposition_table[key] = TTEntry(min_eval, depth, flag, best_move)
            return min_eval, best_move

    def quiescence_minimax(self, board: chess.Board, main_depth: int, qs_depth: int, alpha: float, beta: float,
                           maximizing_player: bool) -> float:
        # ref https://www.chessprogramming.org/Quiescence_Search
        # implemented using minimax instead of negamax for consistency

        eval_depth = main_depth + qs_depth

        static_eval = self.evaluator.evaluate(board, eval_depth)

        if board.is_game_over() or qs_depth >= MAX_QS_DEPTH:
            return static_eval

        if maximizing_player:
            if static_eval >= beta:
                return beta
            if static_eval > alpha:
                alpha = static_eval
        else:
            if static_eval <= alpha:
                return alpha
            if static_eval < beta:
                beta = static_eval

        moves = []
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion:
                moves.append(move)

        if qs_depth < 3:
            for move in board.legal_moves:
                if board.gives_check(move) and move not in moves:
                    moves.append(move)

        if len(moves) > 8:
            move_scores = [(self.score_move(board, move, eval_depth), move) for move in moves]
            move_scores.sort(key=lambda x: x[0], reverse=maximizing_player)
            moves = [move for _, move in move_scores[:8]]

        if maximizing_player:
            for move in moves:
                board.push(move)
                score = self.quiescence_minimax(board, main_depth, qs_depth + 1, alpha, beta, False)
                board.pop()

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            return alpha
        else:
            for move in moves:
                board.push(move)
                score = self.quiescence_minimax(board, main_depth, qs_depth + 1, alpha, beta, True)
                board.pop()

                if score <= alpha:
                    return alpha
                if score < beta:
                    beta = score
            return beta

    def find_best_move(self, board: chess.Board, max_depth: int = MAX_SEARCH_DEPTH) -> tuple[chess.Move | None, float]:
        best_move, best_score = None, 0
        for depth in range(1, max_depth + 1):
            score, move = self.alpha_beta(board, depth, float('-inf'), float('inf'), board.turn == self.evaluator.engine_color)
            # if abs(score) > MATE_SCORE:
            #     print("Mate found, stopping early.")
            #     break
            if move is not None:
                best_move = move
                best_score = score

        return best_move, best_score
    


    
    # -----------------------------------------------------------------------------------------------------------
    # functions only for debugging
    # -----------------------------------------------------------------------------------------------------------
    def alpha_beta_with_trace(self, board: chess.Board, depth: int, alpha: float, beta: float, maximizing_player: bool,
                                last_move_was_check: bool = False, quiescence: bool = True
                   ) -> tuple[float, chess.Move | None, list[chess.Move]]:
        if depth == 0 or board.is_game_over():
            if quiescence:
                a = self.quiescence_minimax(board, depth, 0, alpha, beta, maximizing_player), None, []
                return a

            return self.evaluator.evaluate(board, depth), None, []

        best_move = None
        best_line: list[chess.Move] = []
        legal_moves = list(board.legal_moves)

        move_scores = [(self.score_move(board, move, depth), move) for move in legal_moves]
        move_scores.sort(key=lambda x: x[0], reverse=maximizing_player)
        sorted_moves = [move for _, move in move_scores]

        if maximizing_player:
            max_score = float('-inf')
            for move in sorted_moves:
                is_check = board.gives_check(move)

                if is_check:
                    eval_before = self.evaluator.evaluate(board, depth)

                board.push(move)
                score, _, line = self.alpha_beta_with_trace(board, depth - 1, alpha, beta, not maximizing_player, quiescence)
                board.pop()

                if is_check and last_move_was_check:
                    eval_gain = score - eval_before
                    if eval_gain < 50:
                        score -= 50

                if score > max_score:
                    max_score = score
                    best_move = move
                    best_line = [move] + line
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score, best_move, best_line
        else:
            min_score = float('inf')
            for move in legal_moves:
                is_check = board.gives_check(move)

                if is_check:
                    eval_before = self.evaluator.evaluate(board, depth)

                board.push(move)
                score, _, line = self.alpha_beta_with_trace(board, depth - 1, alpha, beta, not maximizing_player, quiescence)
                board.pop()

                if is_check and last_move_was_check:
                    eval_gain = eval_before - score
                    if eval_gain < 50:
                        score += 50

                if score < min_score:
                    min_score = score
                    best_move = move
                    best_line = [move] + line
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score, best_move, best_line

    def test_with_stack_trace(self, board: chess.Board, quiescence: bool = True, depth: int = 3):
        score, move, line = self.alpha_beta_with_trace(board, 4, float('-inf'), float('inf'), True, quiescence = quiescence)
        print(f"Score: {score}")
        print(f"Best Move: {move}")
        print(f"Principal Variation:")
        for ply in line:
            print(board.san(ply))
            board.push(ply)