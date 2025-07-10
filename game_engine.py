import argparse
import asyncio
from tictactoe import *


async def main(args):
    if args.reset:
        print("Resetting board")
        board = TicTacToeBoard()
        board.reset()
        await board.save_to_redis()
        return
    await listen_for_updates(args.player.lower())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()
    asyncio.run(main(args))
