from pydantic import BaseModel
from fastapi import FastAPI
from tictactoe import TicTacToeBoard

app = FastAPI()

@app.get("/state")
async def get_state():
    board = await TicTacToeBoard.load_from_redis()
    return board.to_dict()

class MoveModel(BaseModel):
    player: str
    position: int

@app.post("/move")
async def make_move(move: MoveModel):
    board = await TicTacToeBoard.load_from_redis()
    move = board.make_move(move.player, move.position)
    await board.save_to_redis()
    return move

@app.post("/reset")
async def reset():
    board = await TicTacToeBoard.load_from_redis()
    board.reset()
    await board.save_to_redis()
    return True
    