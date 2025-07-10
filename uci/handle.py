import chess
import sys
from engine.Agent import Agent


def handle(board: chess.Board, message: str):
    message = message.strip()
    parts = message.split(" ")

    if message == "quit":
        sys.exit()

    if message == "uci":
        print("id name fichess")
        print("id author Filip Gavrilovski")
        print("uciok")
        return

    if message == "isready":
        print("readyok")
        return

    if message == "ucinewgame":
        return

    if message.startswith("position"):
        if len(parts) < 2:
            return

        if parts[1] == "startpos":
            board.reset()
            moves_index = 2
        elif parts[1] == "fen":
            fen = " ".join(parts[2:8])
            board.set_fen(fen)
            moves_index = 8
        else:
            return

        if len(parts) <= moves_index or parts[moves_index] != "moves":
            return

        for move in parts[(moves_index + 1):]:
            board.push_uci(move)
            print(f"made move: {move}")

    if message == "d":
        print(board)
        print(board.fen())

    if message[0:2] == "go":
        agent = Agent(engine_color=board.turn)
        move = agent.find_best_move(board, 4)[0]
        if move:
            print(f"bestmove {move.uci()}")
        else:
            print("no move")