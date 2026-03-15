import json
from typing import Iterable

from app.db import db
from app.domain.models import GameState


class GameRepository:
    def __init__(self) -> None:
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                game_id VARCHAR PRIMARY KEY,
                game_code VARCHAR UNIQUE,
                game_name VARCHAR NOT NULL,
                is_closed BOOLEAN NOT NULL,
                state_json JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
        )
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_games_game_code ON games(game_code)")

    def insert(self, game: GameState) -> GameState:
        db.execute(
            """
            INSERT INTO games (game_id, game_code, game_name, is_closed, state_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?::JSON, ?::TIMESTAMP, ?::TIMESTAMP)
            """,
            (
                game.game_id,
                game.game_code,
                game.name,
                game.is_closed,
                json.dumps(game.model_dump()),
                game.created_at,
                game.updated_at,
            ),
        )
        return game

    def update(self, game: GameState) -> GameState:
        db.execute(
            """
            UPDATE games
            SET game_code = ?, game_name = ?, is_closed = ?, state_json = ?::JSON, updated_at = ?::TIMESTAMP
            WHERE game_id = ?
            """,
            (
                game.game_code,
                game.name,
                game.is_closed,
                json.dumps(game.model_dump()),
                game.updated_at,
                game.game_id,
            ),
        )
        return game

    def get(self, game_id: str) -> GameState | None:
        result = db.execute(
            "SELECT state_json::VARCHAR FROM games WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        if result is None:
            return None
        return GameState.model_validate_json(result[0])

    def get_by_code(self, game_code: str) -> GameState | None:
        result = db.execute(
            "SELECT state_json::VARCHAR FROM games WHERE game_code = ?",
            (game_code.upper(),),
        ).fetchone()
        if result is None:
            return None
        return GameState.model_validate_json(result[0])

    def code_exists(self, game_code: str) -> bool:
        result = db.execute(
            "SELECT 1 FROM games WHERE game_code = ?",
            (game_code.upper(),),
        ).fetchone()
        return result is not None

    def list_all(self) -> Iterable[GameState]:
        rows = db.execute(
            "SELECT state_json::VARCHAR FROM games ORDER BY updated_at DESC"
        ).fetchall()
        return [GameState.model_validate_json(row[0]) for row in rows]
