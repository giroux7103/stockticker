import os
from dataclasses import dataclass, field
from pathlib import Path


def _parse_cors_allowed_origins() -> tuple[str, ...]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    if not raw.strip():
        return (
            "http://localhost:5173",
            "https://localhost:5173",
            "http://127.0.0.1:5173",
            "https://127.0.0.1:5173",
            "http://173.59.126.226",
            "https://173.59.126.226",
            "http://173.59.126.226:8000",
            "https://173.59.126.226:8000",
        )

    origins = tuple(
        origin.strip().rstrip("/")
        for origin in raw.split(",")
        if origin.strip()
    )
    return origins


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("data/stockticker.duckdb")
    cors_allowed_origins: tuple[str, ...] = field(default_factory=_parse_cors_allowed_origins)


settings = Settings()
print(f"Using settings: {settings}")
