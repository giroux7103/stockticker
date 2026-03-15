from app.domain.engine import (
    InvalidMoveError,
    apply_trade,
    build_standings,
    close_game,
    create_game,
    generate_game_code,
    join_game,
    mark_done_and_advance_if_ready,
    start_game,
)
from app.domain.models import GameState, GameView, TradeSide
from app.repositories.game_repository import GameRepository


class NotFoundError(ValueError):
    pass


class GameService:
    def __init__(self, repository: GameRepository) -> None:
        self.repository = repository

    def create(
        self,
        owner_name: str,
        total_rounds: int,
        rolls_per_round: int,
    ) -> tuple[GameState, str]:
        game_code = self._unique_game_code()
        game = create_game(
            owner_name=owner_name,
            total_rounds=total_rounds,
            rolls_per_round=rolls_per_round,
            game_code=game_code,
        )
        self.repository.insert(game)
        return game, game.owner_player_id

    def get(self, game_id: str) -> GameState:
        game = self.repository.get(game_id)
        if game is None:
            raise NotFoundError("Game not found")
        return game

    def get_by_code(self, game_code: str) -> GameState:
        game = self.repository.get_by_code(game_code.upper())
        if game is None:
            raise NotFoundError("Game not found")
        return game

    def get_view(self, game_id: str) -> GameView:
        game = self.get(game_id)
        return self._to_view(game)

    def get_view_by_code(self, game_code: str) -> GameView:
        game = self.get_by_code(game_code)
        return self._to_view(game)

    def list_games(self) -> list[GameView]:
        return [self._to_view(game) for game in self.repository.list_all()]

    def join(self, game_code: str, player_name: str) -> tuple[GameView, str]:
        game = self.get_by_code(game_code)
        updated, new_player = join_game(game, player_name)
        self.repository.update(updated)
        return self._to_view(updated), new_player.player_id

    def start(self, game_id: str, owner_player_id: str) -> GameView:
        game = self.get(game_id)
        updated = start_game(game, requester_player_id=owner_player_id)
        self.repository.update(updated)
        return self._to_view(updated)

    def trade(
        self,
        game_id: str,
        player_id: str,
        symbol: str,
        quantity: int,
        side: TradeSide,
    ) -> GameView:
        game = self.get(game_id)
        updated = apply_trade(
            state=game,
            player_id=player_id,
            symbol=symbol,
            quantity=quantity,
            side=side,
        )
        self.repository.update(updated)
        return self._to_view(updated)

    def mark_done(self, game_id: str, player_id: str) -> GameView:
        game = self.get(game_id)
        updated = mark_done_and_advance_if_ready(game, player_id=player_id)
        self.repository.update(updated)
        return self._to_view(updated)

    def close(self, game_id: str, owner_player_id: str) -> GameView:
        game = self.get(game_id)
        updated = close_game(game, requester_player_id=owner_player_id)
        self.repository.update(updated)
        return self._to_view(updated)

    def _unique_game_code(self) -> str:
        for _ in range(20):
            code = generate_game_code()
            if not self.repository.code_exists(code):
                return code
        raise RuntimeError("Failed to generate a unique game code")

    def _to_view(self, game: GameState) -> GameView:
        standings = build_standings(game)
        winner = standings[0] if game.is_closed and standings else None
        return GameView(game=game, standings=standings, winner=winner)


service = GameService(repository=GameRepository())
__all__ = ["GameService", "service", "NotFoundError", "InvalidMoveError"]
