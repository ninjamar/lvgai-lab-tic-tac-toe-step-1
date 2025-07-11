import argparse
import asyncio
import json
import httpx
import redis.asyncio as redis
import os
from dotenv import load_dotenv
import websockets


load_dotenv()

rd = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True,
)

WS_BASE_URL = os.environ["WS_BASE_URL"]
BASE_URL = os.environ["BASE_URL"]
PREFIX = os.environ["PREFIX"]
KEY = os.environ["KEY"]
PUB_SUB_KEY = os.environ["PUB_SUB_KEY"]
WS_BASE_URL = os.environ["WS_BASE_URL"]



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
    response = await client.post(
        f"{BASE_URL}/move", json={"player": player, "position": position}
    )
    return response.json()


async def reset(client: httpx.AsyncClient):
    response = await client.post(f"{BASE_URL}/reset")
    return response.json()


async def handle_board_state(ws, client: httpx.AsyncClient, i_am_playing: str):
    t = await get_state(client)
    print("Player turn: ", t["player_turn"])

    # print(board.format_board())
    print(json.dumps(t, indent=2))

    if t["state"] == "is_won":
        print("Player ", t["winner"], " won!")
        return True

    if t["state"] == "is_draw":
        print("The game is a draw!")
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
                
        await send_to_ws(ws, move)
        await rd.publish(PUB_SUB_KEY, "Yay!")


async def listen_for_updates(ws, client: httpx.AsyncClient, i_am_playing: str):
    pubsub = rd.pubsub()
    await pubsub.subscribe(PUB_SUB_KEY)

    try:
        result = await handle_board_state(ws, client, i_am_playing)

        if result:
            return

        print("Waiting for other player...")

        async for message in pubsub.listen():
            if message["type"] == "message":
                result = await handle_board_state(ws, client, i_am_playing)
                if result:
                    return
                print("Waiting for other player...")

    finally:
        await pubsub.aclose()

async def send_to_ws(websocket, message):
    await websocket.send(json.dumps(message))

async def main(args):
    async with websockets.connect(f"{WS_BASE_URL}/ws") as ws, httpx.AsyncClient() as client:
        if args.reset:
            await reset(client)
            return
        await listen_for_updates(ws, client, args.player.lower())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()
    asyncio.run(main(args))
