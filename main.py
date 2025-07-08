#!/usr/bin/env python3
import chess
from uci.handle import handle

def main():
    board = chess.Board()
    while True:
        message = input()
        handle(board, message)

if __name__ == '__main__':
    main()