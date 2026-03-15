from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class GamePhase(str, Enum):
    LOBBY = "LOBBY"
    TRADING = "TRADING"
    COMPLETE = "COMPLETE"


class PlayerState(BaseModel):
    player_id: str
    name: str
    cash: int = 500_000
    holdings: Dict[str, int] = Field(default_factory=dict)
    is_done: bool = False


class RollResult(BaseModel):
    round_number: int
    roll_number: int
    symbol: str
    action: str
    amount: int


class PlayerStanding(BaseModel):
    player_id: str
    name: str
    cash: int
    holdings_value: int
    net_worth: int


class GameState(BaseModel):
    game_id: str
    game_code: str
    name: str
    owner_player_id: str
    created_at: str
    updated_at: str
    phase: GamePhase = GamePhase.LOBBY
    current_round: int = 0
    total_rounds: int = 5
    rolls_per_round: int = 20
    players: List[PlayerState]
    stock_prices: Dict[str, int]
    roll_history: List[RollResult] = Field(default_factory=list)
    price_floor: int = 10
    price_ceiling: int = 500
    is_closed: bool = False


class GameView(BaseModel):
    game: GameState
    standings: List[PlayerStanding]
    winner: PlayerStanding | None = None
