import random
import string
from uuid import uuid4

from app.domain.models import GamePhase, GameState, PlayerStanding, PlayerState, RollResult, TradeSide
from app.utils import utc_now_iso

DEFAULT_STOCKS = {
    "GLD": 100,
    "SIL": 100,
    "IND": 100,
    "BON": 100,
    "OIL": 100,
    "GRA": 100,
}
ROLL_ACTION_DIE = ["UP", "UP", "DOWN", "DOWN", "DIVIDEND", "DIVIDEND"]
ROLL_AMOUNT_DIE = [5, 5, 10, 10, 20, 20]


class InvalidMoveError(ValueError):
    pass


def generate_game_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def create_game(
    owner_name: str,
    total_rounds: int,
    rolls_per_round: int,
    game_code: str,
) -> GameState:
    owner_clean = owner_name.strip()
    if not owner_clean:
        raise InvalidMoveError("Owner name is required")
    if total_rounds <= 0:
        raise InvalidMoveError("Number of rounds must be positive")
    if rolls_per_round <= 0:
        raise InvalidMoveError("Number of rolls per round must be positive")

    timestamp = utc_now_iso()
    owner = PlayerState(player_id=str(uuid4()), name=owner_clean)

    return GameState(
        game_id=str(uuid4()),
        game_code=game_code,
        name="Stock Ticker Game",
        owner_player_id=owner.player_id,
        created_at=timestamp,
        updated_at=timestamp,
        players=[owner],
        total_rounds=total_rounds,
        rolls_per_round=rolls_per_round,
        stock_prices=DEFAULT_STOCKS.copy(),
    )


def join_game(state: GameState, player_name: str) -> tuple[GameState, PlayerState]:
    if state.phase != GamePhase.LOBBY:
        raise InvalidMoveError("Cannot join after game has started")

    clean = player_name.strip()
    if not clean:
        raise InvalidMoveError("Player name is required")

    for player in state.players:
        if player.name.lower() == clean.lower():
            raise InvalidMoveError("Name already used in this game")

    new_player = PlayerState(player_id=str(uuid4()), name=clean)
    state.players.append(new_player)
    state.updated_at = utc_now_iso()
    return state, new_player


def start_game(state: GameState, requester_player_id: str) -> GameState:
    if state.phase != GamePhase.LOBBY:
        raise InvalidMoveError("Game is already started")
    if requester_player_id != state.owner_player_id:
        raise InvalidMoveError("Only owner can start the game")
    if len(state.players) < 2:
        raise InvalidMoveError("At least 2 players are required to start")

    for player in state.players:
        player.is_done = False

    state.phase = GamePhase.TRADING
    state.current_round = 1
    state.updated_at = utc_now_iso()
    return state


def apply_trade(
    state: GameState,
    player_id: str,
    symbol: str,
    quantity: int,
    side: TradeSide,
) -> GameState:
    if state.phase != GamePhase.TRADING:
        raise InvalidMoveError("Trades are only allowed during trading phase")
    if quantity <= 0:
        raise InvalidMoveError("Trade quantity must be positive")
    if symbol not in state.stock_prices:
        raise InvalidMoveError(f"Unknown stock symbol: {symbol}")

    player = _find_player(state, player_id)
    price = state.stock_prices[symbol]
    gross_value = price * quantity

    if quantity % 500 != 0:
        raise InvalidMoveError("Trades must be in increments of 500 shares")

    if side == TradeSide.BUY:
        if player.cash < gross_value:
            raise InvalidMoveError("Insufficient cash for BUY")
        player.cash -= gross_value
        player.holdings[symbol] = player.holdings.get(symbol, 0) + quantity
    else:
        owned = player.holdings.get(symbol, 0)
        if owned < quantity:
            raise InvalidMoveError("Insufficient shares for SELL")
        player.holdings[symbol] = owned - quantity
        if player.holdings[symbol] == 0:
            player.holdings.pop(symbol)
        player.cash += gross_value

    player.is_done = False
    state.updated_at = utc_now_iso()
    return state


def mark_done_and_advance_if_ready(state: GameState, player_id: str) -> GameState:
    if state.phase != GamePhase.TRADING:
        raise InvalidMoveError("Not in trading phase")

    player = _find_player(state, player_id)
    player.is_done = True

    if all(current.is_done for current in state.players):
        _run_round_rolls(state)
        if state.current_round >= state.total_rounds:
            state.phase = GamePhase.COMPLETE
            state.is_closed = True
        else:
            state.current_round += 1
            for current in state.players:
                current.is_done = False

    state.updated_at = utc_now_iso()
    return state


def close_game(state: GameState, requester_player_id: str) -> GameState:
    if requester_player_id != state.owner_player_id:
        raise InvalidMoveError("Only owner can close the game")
    state.phase = GamePhase.COMPLETE
    state.is_closed = True
    state.updated_at = utc_now_iso()
    return state


def build_standings(state: GameState) -> list[PlayerStanding]:
    standings: list[PlayerStanding] = []
    for player in state.players:
        holdings_value = 0
        for symbol, quantity in player.holdings.items():
            holdings_value += state.stock_prices.get(symbol, 0) * quantity
        net_worth = player.cash + holdings_value
        standings.append(
            PlayerStanding(
                player_id=player.player_id,
                name=player.name,
                cash=player.cash,
                holdings_value=holdings_value,
                net_worth=net_worth,
            )
        )
    standings.sort(key=lambda entry: entry.net_worth, reverse=True)
    return standings


def _run_round_rolls(state: GameState) -> None:
    symbols = list(state.stock_prices.keys())
    for roll_number in range(1, state.rolls_per_round + 1):
        symbol = random.choice(symbols)
        action = random.choice(ROLL_ACTION_DIE)
        amount = random.choice(ROLL_AMOUNT_DIE)

        if action == "UP":
            state.stock_prices[symbol] += amount
        elif action == "DOWN":
            state.stock_prices[symbol] -= amount
        else:
            if state.stock_prices[symbol] >= 100:
                for player in state.players:
                    quantity = player.holdings.get(symbol, 0)
                    if quantity > 0:
                        # Dividend die value is a percent payout of owned units.
                        # Example: 1000 shares at 10% pays $100 (10,000 cents).
                        player.cash += quantity * amount

        if state.stock_prices[symbol] >= 200:
            for player in state.players:
                quantity = player.holdings.get(symbol, 0)
                if quantity > 0:
                    player.holdings[symbol] = quantity * 2
            state.stock_prices[symbol] = 100
        elif state.stock_prices[symbol] <= 0:
            for player in state.players:
                if symbol in player.holdings:
                    player.holdings.pop(symbol)
            state.stock_prices[symbol] = 100

        state.roll_history.append(
            RollResult(
                round_number=state.current_round,
                roll_number=roll_number,
                symbol=symbol,
                action=action,
                amount=amount,
            )
        )


def _find_player(state: GameState, player_id: str) -> PlayerState:
    for player in state.players:
        if player.player_id == player_id:
            return player
    raise InvalidMoveError("Player not found")
