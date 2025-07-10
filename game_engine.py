import argparse
from tictactoe import TicTacToeBoard


def game(args):
    if args.reset:
        print("Resetting board")
        board = TicTacToeBoard()
        board.reset()
        board.save_to_redis()
        return
    else:
        board = TicTacToeBoard.load_from_redis()
    print(board.format_board())

    args.player = args.player.lower()
    if board.state == "is_playing":
        if not board.is_my_turn(args.player):
            print("It's not your turn.")
            return

        position = int(input(f"Player {args.player}, enter the position to play: "))
        if not board.make_move(position):
            print("Invalid move.")
            return

        print(board.format_board())

    if board.state == "is_won":
        print(f"Player {board.winner.upper()} wins!")
    elif board.state == "is_draw":
        print("The game is a draw!")

    board.save_to_redis()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()
    game(args)
