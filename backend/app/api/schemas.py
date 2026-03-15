from pydantic import BaseModel, Field

from app.domain.models import GameView, TradeSide


class CreateGameRequest(BaseModel):
    owner_name: str
    total_rounds: int = Field(default=5, gt=0)
    rolls_per_round: int = Field(default=20, gt=0)


class CreateGameResponse(BaseModel):
    game_id: str
    game_code: str
    owner_player_id: str


class JoinGameRequest(BaseModel):
    game_code: str = Field(min_length=4, max_length=12)
    player_name: str


class JoinGameResponse(BaseModel):
    game_id: str
    game_code: str
    player_id: str


class StartGameRequest(BaseModel):
    owner_player_id: str


class MarkDoneRequest(BaseModel):
    player_id: str


class CloseGameRequest(BaseModel):
    owner_player_id: str


class TradeRequest(BaseModel):
    player_id: str
    symbol: str
    quantity: int = Field(gt=0)
    side: TradeSide


class GameListResponse(BaseModel):
    games: list[GameView]


class GameViewResponse(BaseModel):
    game_view: GameView
