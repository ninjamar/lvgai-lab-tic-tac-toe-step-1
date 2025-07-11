import argparse
import asyncio
import json
import httpx
import redis.asyncio as redis
import os
from dotenv import load_dotenv

load_dotenv()

rd = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)
BASE_URL = "http://localhost:8000"
PREFIX = "NM:4:"  # Team 4
KEY = PREFIX + "tictactoe:game_state"
PUB_SUB_KEY = PREFIX + "tictactoe:pubsub"

def ensure_input(prompt: str, allowed: list, t: type = str):
    ipt = t(input(prompt))
    while ipt not in allowed:
        try:
            ipt = t(input(prompt))
        except:
            continue
    return ipt

async def get_state(client: httpx.AsyncClient):
    response = await client.get(f"{BASE_URL}/state")
    return response.json()

async def make_move(client: httpx.AsyncClient, player: str, position: int):
    response = await client.post(f"{BASE_URL}/move", json={"player": player, "position": position})
    return response.json()

async def reset(client: httpx.AsyncClient):
    response = await client.post(f"{BASE_URL}/reset")
    return response.json()

async def handle_board_state(client: httpx.AsyncClient, i_am_playing: str):
    t = await get_state(client)
    print("Player turn: ", t["player_turn"])

    # print(board.format_board())
    print(json.dumps(t, indent=2))

    if t["state"] == "is_won" or t["state"] == "is_draw":
        print(t["message"])
        return True

    if t["player_turn"] == i_am_playing:
        making_move = True
        while making_move:
            move = ensure_input("Make a move:", range(9), int)
            move = await make_move(client, i_am_playing, move)
            print(move["message"])

            if not move["success"]:
                continue
            else:
                making_move = False

        await rd.publish(PUB_SUB_KEY, "Yay!")


async def listen_for_updates(client: httpx.AsyncClient, i_am_playing: str):
    pubsub = rd.pubsub()
    await pubsub.subscribe(PUB_SUB_KEY)

    try:
        result = await handle_board_state(client, i_am_playing)

        if result:
            return

        print("Waiting for other player...")

        async for message in pubsub.listen():
            if message["type"] == "message":
                result = await handle_board_state(client, i_am_playing)
                if result:
                    return
                print("Waiting for other player...")

    finally:
        await pubsub.close()


async def main(args):
    client = httpx.AsyncClient()
    if args.reset:
        await reset(client)
        return
    await listen_for_updates(client, args.player.lower())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()
    asyncio.run(main(args))
