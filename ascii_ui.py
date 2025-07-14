from dotenv import load_dotenv
import os
import asyncio
import websockets
import json

load_dotenv()

PREFIX = os.getenv("PREFIX")
KEY = os.getenv("KEY")
PUB_SUB_KEY = os.getenv("PUB_SUB_KEY")

WS_BASE_URL = os.environ["WS_BASE_URL"]

# Incoming message format: whatever board.to_dict() returns


def format_board(board: list[str]):
    out = "-" * 13 + "\n"
    for row_idx in range(0, 9, 3):
        buf = ""
        for spot_idx, spot in enumerate(board[row_idx : row_idx + 3]):
            char = str(row_idx + spot_idx) if spot == "" else spot
            buf += f"| {char} "
        buf = f"{buf}|" + "\n"
        out += buf
        out += "-" * 13 + "\n"
    return out


async def listen_for_updates():
    try:
        async with websockets.connect(f"{WS_BASE_URL}/ws") as ws:
            async for message in ws:
                os.system("cls" if os.name == "nt" else "clear")

                board = json.loads(message)
                print(format_board(board["positions"]))
    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed")


async def main():
    await listen_for_updates()


if __name__ == "__main__":
    asyncio.run(main())
