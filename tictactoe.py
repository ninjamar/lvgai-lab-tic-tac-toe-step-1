import redis.asyncio as redis
import dataclasses
import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Any

load_dotenv()

rd = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

PREFIX = "NM:4:"  # Team 4
KEY = PREFIX + "tictactoe:game_state"
PUB_SUB_KEY = PREFIX + "tictactoe:pubsub"

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


def ensure_input(prompt: str, allowed: list, t: type = str):
    ipt = t(input(prompt))
    while ipt not in allowed:
        try:
            ipt = t(input(prompt))
        except:
            continue
    return ipt

class ClientResponse(BaseModel):
    success: bool
    message: str
    board: list | None

@dataclasses.dataclass
class TicTacToeBoard:
    state: str = dataclasses.field(default="is_playing")
    winner: str | None = dataclasses.field(default=None)
    player_turn: str = dataclasses.field(default="x")
    positions: list[str] = dataclasses.field(default_factory=lambda: ["" for _ in range(9)])

    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am and self.state == "is_playing"

    def make_move(self, position: int) -> ClientResponse:
        # Return True is move is valid and successful
        if self.state != "is_playing":
            return ClientResponse(success=False, message="Game is not in progress", board=None)
        if not (0 <= position < 9):
            return ClientResponse(success=False, message="Invalid position", board=None)
        if self.positions[position]:
            return ClientResponse(success=False, message="Position already taken", board=None)
        self.positions[position] = self.player_turn

        if winner := self.check_winner():
            self.state = "is_won"
            self.winner = winner
        elif self.check_draw():
            self.state = "is_draw"
        else:
            self.state = "is_playing"

        self.switch_turn()

        return ClientResponse(success=True, message="Move successful", board=self.positions)
    
    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

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
        out = "-" * 13 + "\n"
        for row_idx in range(0, 9, 3):
            buf = ""
            for spot_idx, spot in enumerate(self.positions[row_idx : row_idx + 3]):
                char = str(row_idx + spot_idx) if spot == "" else spot
                buf += f"| {char} "
            buf = f"{buf}|" + "\n"
            out += buf
            out += "-" * 13 + "\n"
        return out

    def serialize(self) -> str:
        return json.dumps(
            {
                "state": self.state,
                "winner": self.winner,
                "player_turn": self.player_turn,
                "positions": self.positions,
            }
        )

    async def save_to_redis(self) -> None:
        data = self.serialize()
        await rd.json().set(KEY, ".", data)

    @classmethod
    async def load_from_redis(cls) -> "TicTacToeBoard":
        data = json.loads(await rd.json().get(KEY))
        if not data:
            return cls()
        return cls(**data)

    def reset(self) -> None:
        # TODO: In the future, call fields(self) and dynamically reset the board
        self.state = "is_playing"
        self.winner = None
        self.player_turn = "x"
        self.positions = ["" for _ in range(9)]


async def handle_board_state(i_am_playing: str):
    board = await TicTacToeBoard.load_from_redis()
    print("Player turn: ", board.player_turn)

    # print(board.format_board())
    print(json.dumps(board.to_dict(), indent=2))

    if board.state == "is_won":
        print(f"Player {board.winner.upper()} wins!")
        return True
    elif board.state == "is_draw":
        print("The game is a draw!")
        return True

    if board.is_my_turn(i_am_playing):
        making_move = True
        while making_move:
            move = ensure_input("Make a move:", range(9), int)
            move = board.make_move(move)
            print(move.message)

            if not move.success:
                continue
            else:
                making_move = False

        await board.save_to_redis()
        await rd.publish(PUB_SUB_KEY, "Yay!")


async def listen_for_updates(i_am_playing: str):
    pubsub = rd.pubsub()
    await pubsub.subscribe(PUB_SUB_KEY)

    try:
        result = await handle_board_state(i_am_playing)

        if result:
            return

        print("Waiting for other player...")

        async for message in pubsub.listen():
            if message["type"] == "message":
                result = await handle_board_state(i_am_playing)
                if result:
                    return
                print("Waiting for other player...")

    finally:
        await pubsub.close()
