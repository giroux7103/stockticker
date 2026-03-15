from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    CloseGameRequest,
    CreateGameRequest,
    CreateGameResponse,
    GameListResponse,
    GameViewResponse,
    JoinGameRequest,
    JoinGameResponse,
    MarkDoneRequest,
    StartGameRequest,
    TradeRequest,
)
from app.services.game_service import InvalidMoveError, NotFoundError, service

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=CreateGameResponse)
def create_game(request: CreateGameRequest) -> CreateGameResponse:
    try:
        game, owner_player_id = service.create(
            owner_name=request.owner_name,
            total_rounds=request.total_rounds,
            rolls_per_round=request.rolls_per_round,
        )
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CreateGameResponse(
        game_id=game.game_id,
        game_code=game.game_code,
        owner_player_id=owner_player_id,
    )


@router.post("/join", response_model=JoinGameResponse)
def join_game(request: JoinGameRequest) -> JoinGameResponse:
    try:
        game_view, player_id = service.join(
            game_code=request.game_code,
            player_name=request.player_name,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JoinGameResponse(
        game_id=game_view.game.game_id,
        game_code=game_view.game.game_code,
        player_id=player_id,
    )


@router.get("", response_model=GameListResponse)
def list_games() -> GameListResponse:
    return GameListResponse(games=service.list_games())


@router.get("/code/{game_code}", response_model=GameViewResponse)
def get_game_by_code(game_code: str) -> GameViewResponse:
    try:
        game_view = service.get_view_by_code(game_code)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)


@router.get("/{game_id}", response_model=GameViewResponse)
def get_game(game_id: str) -> GameViewResponse:
    try:
        game_view = service.get_view(game_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)


@router.post("/{game_id}/start", response_model=GameViewResponse)
def start_game(game_id: str, request: StartGameRequest) -> GameViewResponse:
    try:
        game_view = service.start(game_id=game_id, owner_player_id=request.owner_player_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)


@router.post("/{game_id}/trades", response_model=GameViewResponse)
def submit_trade(game_id: str, request: TradeRequest) -> GameViewResponse:
    try:
        game_view = service.trade(
            game_id=game_id,
            player_id=request.player_id,
            symbol=request.symbol.upper(),
            quantity=request.quantity,
            side=request.side,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)


@router.post("/{game_id}/done", response_model=GameViewResponse)
def mark_done(game_id: str, request: MarkDoneRequest) -> GameViewResponse:
    try:
        game_view = service.mark_done(game_id=game_id, player_id=request.player_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)


@router.post("/{game_id}/close", response_model=GameViewResponse)
def close_game(game_id: str, request: CloseGameRequest) -> GameViewResponse:
    try:
        game_view = service.close(game_id=game_id, owner_player_id=request.owner_player_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameViewResponse(game_view=game_view)
