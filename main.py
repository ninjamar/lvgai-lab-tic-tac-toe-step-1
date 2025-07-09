from dataclasses import dataclass, field


WIN_COMBINATIONS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]

@dataclass
class TicTacToeBoard:
    state: str = field(default="is_playing")
    winner: str = field(default=None)
    player_turn: str = field(default="x")
    positions: list[str] = field(default_factory=lambda: ["" for _ in range(9)])

    
    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am

    def make_move(self, position: int) -> bool:
        # Return True is move is valid and successful
        if self.check_winner() is None:
            return False
        if not (0 <= position < 9):
            return False
        if self.positions[position]:
            return False
        self.positions[position] = self.player_turn

        if (winner:=self.check_winner()):
            self.state = "is_won"
            self.winner = winner
        elif self.check_draw():
            self.state = "is_draw"
        else:
            self.state = "is_playing"
        return True

    def check_winner(self):
        # Returns the winning player if there is one
        for combination in WIN_COMBINATIONS:
            # If the player holds all positions in the combination needed to win
            player = self.positions[combination[0]]
            if all(self.positions[i] == player for i in combination):
                return player
        return None
    
    def check_draw(self):
        # Returns True if the board is full and no player has won
        return all(self.positions) and self.check_winner() is None

    def switch_turn(self):
        self.player_turn = "o" if self.player_turn == "x" else "x"

    def format_board(self):
        return "\n".join(" ".join(self.positions[i:i+3]) for i in range(0, 9, 3))