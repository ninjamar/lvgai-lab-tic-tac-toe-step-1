import redis
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

load_dotenv()

rd = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD")
)

KEY = "tictactoe:game_state:4" # Team 4

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
    winner: str | None = field(default=None)
    player_turn: str = field(default="x")
    positions: list[str] = field(default_factory=lambda: ["" for _ in range(9)])

    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am and self.state == "is_playing"

    def make_move(self, position: int) -> bool:
        # Return True is move is valid and successful
        if self.state != "is_playing":
            return False
        if not (0 <= position < 9):
            return False
        if self.positions[position]:
            return False
        self.positions[position] = self.player_turn

        if (winner := self.check_winner()):
            self.state = "is_won"
            self.winner = winner
        elif self.check_draw():
            self.state = "is_draw"
        else:
            self.state = "is_playing"
        
        self.switch_turn()

        return True

    def check_winner(self) -> str | None:
        # Returns the winning player if there is one
        for combination in WIN_COMBINATIONS:
            # If the player holds all positions in the combination needed to win
            player = self.positions[combination[0]]
            if player == "":
                continue
            if all(self.positions[i] == player for i in combination):
                return player
        return None

    def check_draw(self) -> bool:
        # Returns True if the board is full and no player has won
        return all(self.positions) and self.check_winner() is None

    def switch_turn(self) -> None:
        self.player_turn = "o" if self.player_turn == "x" else "x"

    def format_board(self) -> str:
        out = ""
        for row_idx in range(0, 9, 3):
            buf = ""
            for spot_idx, spot in enumerate(self.positions[row_idx : row_idx + 3]):
                buf += str(row_idx + spot_idx) if spot == "" else spot
            out += buf + "\n"
        return out

    def serialize(self) -> str:
        return {
                "state": self.state,
                "winner": self.winner,
                "player_turn": self.player_turn,
                "positions": self.positions,
            }
        

    def save_to_redis(self) -> None:
        data = self.serialize()
        rd.json().set(KEY, ".", data)


    @classmethod
    def load_from_redis(cls) -> "TicTacToeBoard":
        data = rd.json().get(KEY)
        if not data:
            return cls()
        return cls(**data)

    def reset(self) -> None:
        # TODO: In the future, call fields(self) and dynamically reset the board
        self.state = "is_playing"
        self.winner = None
        self.player_turn = "x"
        self.positions = ["" for _ in range(9)]

