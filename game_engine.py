from main import TicTacToeBoard


def game():
    board = TicTacToeBoard()
    print(board.format_board())

    while board.state == "is_playing":
        player = input("Which player is playing? (x/o): ")
        if not board.is_my_turn(player):
            continue

        position = int(input("Enter the position to play: "))
        if not board.make_move(position):
            continue

        print(board.format_board())

    if board.state == "is_won":
        print(f"Player {board.winner} wins!")
    elif board.state == "is_draw":
        print("The game is a draw!")


if __name__ == "__main__":
    game()
