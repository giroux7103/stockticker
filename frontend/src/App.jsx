import { useEffect, useMemo, useRef, useState } from "react";
import {
  createGame,
  getGame,
  getGameByCode,
  joinGame,
  markDone,
  startGame,
  submitTrade,
} from "./api";

const COOKIE_GAME_CODE = "stockticker_game_code";
const COOKIE_PLAYER_NAME = "stockticker_player_name";

function setCookie(name, value, days = 30) {
  const expires = new Date(Date.now() + days * 24 * 60 * 60 * 1000).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function getCookie(name) {
  const prefix = `${name}=`;
  const parts = document.cookie.split(";").map((part) => part.trim());
  const found = parts.find((part) => part.startsWith(prefix));
  if (!found) {
    return "";
  }
  return decodeURIComponent(found.slice(prefix.length));
}

function clearCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

function clearSessionCookies() {
  clearCookie(COOKIE_GAME_CODE);
  clearCookie(COOKIE_PLAYER_NAME);
}

function loadSessionFromCookies() {
  const gameCode = getCookie(COOKIE_GAME_CODE);
  const playerName = getCookie(COOKIE_PLAYER_NAME);
  if (!gameCode || !playerName) {
    return null;
  }
  return { gameCode: gameCode.trim().toUpperCase(), playerName: playerName.trim() };
}

function saveSessionToCookies(session) {
  setCookie(COOKIE_GAME_CODE, session.gameCode);
  setCookie(COOKIE_PLAYER_NAME, session.playerName);
}

const BUY_QUANTITY = 500;
const STOCK_COLORS = {
  GLD: "#d4af37",
  SIL: "#c0c0c0",
  IND: "#ff69b4",
  BON: "#2e8b57",
  OIL: "#1b1b1b",
  GRA: "#ffd84d",
};
const ROLL_ANIMATION_MS = 550;
const GRAPH_MAX_CENTS = 200;

function formatCents(value) {
  return `$${(Number(value || 0) / 100).toFixed(2)}`;
}

function formatRollAmount(roll) {
  if (roll.action === "DIVIDEND") {
    return `${roll.amount}%`;
  }
  return formatCents(roll.amount);
}

function applyRollToPrices(prices, roll) {
  const next = { ...prices };
  const current = next[roll.symbol] ?? 0;
  let price = current;

  if (roll.action === "UP") {
    price += roll.amount;
  } else if (roll.action === "DOWN") {
    price -= roll.amount;
  }

  if (price >= 200) {
    price = 100;
  } else if (price <= 0) {
    price = 100;
  }

  next[roll.symbol] = price;
  return next;
}

export default function App() {
  const [session, setSession] = useState(null);
  const [sessionBootstrapping, setSessionBootstrapping] = useState(true);
  const [gameView, setGameView] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [createForm, setCreateForm] = useState({
    ownerName: "",
    totalRounds: 5,
    rollsPerRound: 20,
  });
  const [joinForm, setJoinForm] = useState({ gameCode: "", playerName: "" });
  const [tradeForm, setTradeForm] = useState({ symbol: "GLD" });
  const [animatedStockPrices, setAnimatedStockPrices] = useState(null);
  const [activeAnimatedRoll, setActiveAnimatedRoll] = useState(null);
  const animationTimerRef = useRef(null);
  const previousRollCountRef = useRef(0);
  const previousStockPricesRef = useRef(null);

  const game = gameView?.game;
  const standings = gameView?.standings || [];
  const me = useMemo(
    () => game?.players.find((player) => player.player_id === session?.playerId),
    [game, session]
  );
  const ownerPlayerName = useMemo(
    () => game?.players.find((player) => player.player_id === game?.owner_player_id)?.name || "Unknown",
    [game]
  );
  const isOwner = session && game && session.playerId === game.owner_player_id;
  const selectedPrice = game?.stock_prices?.[tradeForm.symbol] ?? 0;
  const tradeValue = selectedPrice * BUY_QUANTITY;
  const isAnimatingRolls = animatedStockPrices !== null;
  const graphStockPrices = animatedStockPrices || game?.stock_prices || {};
  const graphEntries = Object.entries(graphStockPrices);

  const latestRound = useMemo(() => {
    if (!game || game.roll_history.length === 0) {
      return 0;
    }
    return Math.max(...game.roll_history.map((roll) => roll.round_number));
  }, [game]);

  const latestRoundRolls = useMemo(() => {
    if (!game || latestRound === 0) {
      return [];
    }
    return game.roll_history.filter((roll) => roll.round_number === latestRound);
  }, [game, latestRound]);

  const myNetWorth = useMemo(() => {
    if (!me || !game) {
      return 0;
    }
    const holdingsValue = Object.entries(me.holdings).reduce((sum, [symbol, shares]) => {
      const price = game.stock_prices[symbol] || 0;
      return sum + (shares * price);
    }, 0);
    return (me.cash || 0) + holdingsValue;
  }, [game, me]);

  const otherPlayersNetWorth = useMemo(() => {
    if (!session) {
      return [];
    }
    return standings.filter((entry) => entry.player_id !== session.playerId);
  }, [session, standings]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapSession() {
      const cookieSession = loadSessionFromCookies();
      if (!cookieSession) {
        if (!cancelled) {
          setSessionBootstrapping(false);
        }
        return;
      }

      try {
        const byCode = await getGameByCode(cookieSession.gameCode);
        const gameByCode = byCode.game_view.game;
        const existingPlayer = gameByCode.players.find(
          (player) => player.name.toLowerCase() === cookieSession.playerName.toLowerCase()
        );

        if (existingPlayer) {
          const nextSession = {
            gameId: gameByCode.game_id,
            playerId: existingPlayer.player_id,
            gameCode: gameByCode.game_code,
            playerName: existingPlayer.name,
          };
          if (!cancelled) {
            setSession(nextSession);
          }
          saveSessionToCookies(nextSession);
        } else {
          const joined = await joinGame({
            game_code: cookieSession.gameCode,
            player_name: cookieSession.playerName,
          });
          const nextSession = {
            gameId: joined.game_id,
            playerId: joined.player_id,
            gameCode: joined.game_code,
            playerName: cookieSession.playerName,
          };
          if (!cancelled) {
            setSession(nextSession);
          }
          saveSessionToCookies(nextSession);
        }
      } catch (err) {
        clearSessionCookies();
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setSessionBootstrapping(false);
        }
      }
    }

    bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!session?.gameId) {
      return;
    }

    let cancelled = false;

    async function refresh() {
      try {
        const response = await getGame(session.gameId);
        if (!cancelled) {
          setGameView(response.game_view);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      }
    }

    refresh();
    const intervalId = window.setInterval(refresh, 2000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [session]);

  useEffect(() => {
    if (!game) {
      return;
    }
    if (tradeForm.symbol && game.stock_prices[tradeForm.symbol] !== undefined) {
      return;
    }
    const firstSymbol = Object.keys(game.stock_prices)[0];
    if (firstSymbol) {
      setTradeForm({ symbol: firstSymbol });
    }
  }, [game, tradeForm.symbol]);

  useEffect(() => {
    if (!game) {
      return;
    }

    const currentRollCount = game.roll_history.length;
    const hasNewRolls = currentRollCount > previousRollCountRef.current;
    const canAnimate = game.phase === "TRADING" && latestRoundRolls.length > 0 && previousStockPricesRef.current;

    if (hasNewRolls && canAnimate) {
      if (animationTimerRef.current) {
        window.clearTimeout(animationTimerRef.current);
      }

      const roundRolls = [...latestRoundRolls];
      let prices = { ...previousStockPricesRef.current };
      let index = 0;

      setAnimatedStockPrices(prices);
      setActiveAnimatedRoll(null);

      const step = () => {
        if (index >= roundRolls.length) {
          setAnimatedStockPrices(null);
          setActiveAnimatedRoll(null);
          animationTimerRef.current = null;
          return;
        }
        const roll = roundRolls[index];
        prices = applyRollToPrices(prices, roll);
        setAnimatedStockPrices(prices);
        setActiveAnimatedRoll(roll);
        index += 1;
        animationTimerRef.current = window.setTimeout(step, ROLL_ANIMATION_MS);
      };

      animationTimerRef.current = window.setTimeout(step, ROLL_ANIMATION_MS);
    }

    previousRollCountRef.current = currentRollCount;
    previousStockPricesRef.current = { ...game.stock_prices };
  }, [game, latestRoundRolls]);

  useEffect(() => {
    return () => {
      if (animationTimerRef.current) {
        window.clearTimeout(animationTimerRef.current);
      }
    };
  }, []);

  async function onCreateGame(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      const created = await createGame({
        owner_name: createForm.ownerName,
        total_rounds: Number(createForm.totalRounds),
        rolls_per_round: Number(createForm.rollsPerRound),
      });

      const nextSession = {
        gameId: created.game_id,
        playerId: created.owner_player_id,
        gameCode: created.game_code,
        playerName: createForm.ownerName,
      };
      saveSessionToCookies(nextSession);
      setSession(nextSession);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onJoinGame(event) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      const joined = await joinGame({
        game_code: joinForm.gameCode.trim().toUpperCase(),
        player_name: joinForm.playerName,
      });
      const nextSession = {
        gameId: joined.game_id,
        playerId: joined.player_id,
        gameCode: joined.game_code,
        playerName: joinForm.playerName,
      };
      saveSessionToCookies(nextSession);
      setSession(nextSession);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onStartGame() {
    if (!session || !game) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const response = await startGame(game.game_id, session.playerId);
      setGameView(response.game_view);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onTrade(side) {
    if (!session || !game) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const response = await submitTrade(game.game_id, {
        player_id: session.playerId,
        symbol: tradeForm.symbol,
        quantity: BUY_QUANTITY,
        side,
      });
      setGameView(response.game_view);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onAllDone() {
    if (!session || !game) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const response = await markDone(game.game_id, session.playerId);
      setGameView(response.game_view);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function onReturnToMainScreen() {
    clearSessionCookies();
    setSession(null);
    setGameView(null);
    setError("");
  }

  if (sessionBootstrapping) {
    return (
      <div className="page">
        <h1>Reconnecting...</h1>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="page">
        <p className="subtitle">Choose how you want to enter the game.</p>
        {error && <div className="error">{error}</div>}

        <div className="cards">
          <form className="card" onSubmit={onJoinGame}>
            <h2>Join Game</h2>
            <label>
              Game Code
              <input
                value={joinForm.gameCode}
                onChange={(event) => setJoinForm((prev) => ({ ...prev, gameCode: event.target.value }))}
                required
              />
            </label>
            <label>
              Your Name
              <input
                value={joinForm.playerName}
                onChange={(event) => setJoinForm((prev) => ({ ...prev, playerName: event.target.value }))}
                required
              />
            </label>
            <button disabled={busy} type="submit">Join</button>
          </form>

          <form className="card" onSubmit={onCreateGame}>
            <h2>Create Game</h2>
            <label>
              Your Name
              <input
                value={createForm.ownerName}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, ownerName: event.target.value }))}
                required
              />
            </label>
            <label>
              Number of Rounds
              <input
                type="number"
                min="1"
                value={createForm.totalRounds}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, totalRounds: event.target.value }))}
              />
            </label>
            <label>
              Rolls per Round
              <input
                type="number"
                min="1"
                value={createForm.rollsPerRound}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, rollsPerRound: event.target.value }))}
              />
            </label>
            <button disabled={busy} type="submit">Create</button>
          </form>
        </div>
      </div>
    );
  }

  if (!game) {
    return (
      <div className="page">
        <h1>Loading game...</h1>
        {error && <div className="error">{error}</div>}
      </div>
    );
  }

  return (
    <div className="page">
      <header className="header">
        <p>
          Code: <strong>{game.game_code}</strong> | Owner {ownerPlayerName} | Round {game.current_round}/{game.total_rounds} | Phase {game.phase}
        </p>
      </header>

      {error && <div className="error">{error}</div>}

      {game.phase === "LOBBY" ? (
        <section className="panel">
          <h2>Players</h2>
          <ul className="list">
            {game.players.map((player) => (
              <li key={player.player_id}>
                {player.name}
                {player.player_id === game.owner_player_id ? " (Owner)" : ""}
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <section className="panel chart-panel">
          <h2>Stock Values</h2>
          {isAnimatingRolls && activeAnimatedRoll && (
            <p className="muted">
              Animating roll: {activeAnimatedRoll.symbol} {activeAnimatedRoll.action} {formatRollAmount(activeAnimatedRoll)}
            </p>
          )}
          <div className="stock-graph-shell">
            <div className="stock-y-axis">
              <div className="y-tick y-top">$2</div>
              <div className="y-tick y-mid">$1</div>
              <div className="y-tick y-bottom">$0</div>
            </div>
            <div className="stock-plot">
              <div className="stock-reference-line" />
              <div
                className="stock-graph"
                style={{ gridTemplateColumns: `repeat(${Math.max(graphEntries.length, 1)}, minmax(0, 1fr))` }}
              >
                {graphEntries.map(([symbol, price]) => {
                  const scaledHeight = Math.round((Number(price || 0) / GRAPH_MAX_CENTS) * 100);
                  const heightPct = Math.max(6, Math.min(100, scaledHeight));
                  const valueClass = price >= 100 ? "stock-value up" : "stock-value down";
                  const ownedShares = me?.holdings?.[symbol] || 0;
                  const isSelected = symbol === tradeForm.symbol;
                  return (
                    <button
                      className={`stock-column ${isSelected ? "selected" : ""}`}
                      key={symbol}
                      onClick={() => setTradeForm({ symbol })}
                      type="button"
                    >
                      <div className={valueClass}>{formatCents(price)}</div>
                      <div className="stock-bar-wrap">
                        <div
                          className="stock-bar"
                          style={{
                            height: `${heightPct}%`,
                            backgroundColor: STOCK_COLORS[symbol] || "#4a5b6a",
                          }}
                        />
                      </div>
                      <div className="stock-symbol">{symbol}</div>
                      <div className="stock-owned">{ownedShares}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          {me && (
            <p className="stock-summary">
              Cash {formatCents(me.cash)} | Net Worth {formatCents(myNetWorth)}
            </p>
          )}
        </section>
      )}

      {game.phase === "LOBBY" && (
        <section className="panel">
          <h2>Lobby</h2>
          <p>Players can join with the game code until the owner starts.</p>
          {isOwner ? (
            <button disabled={busy} onClick={onStartGame}>Start Game</button>
          ) : (
            <p>Waiting for owner to start...</p>
          )}
        </section>
      )}

      {game.phase === "TRADING" && (
        <section className="panel">
          <div>
            <h2>Trade</h2>
            <div className="trade-form">
              <p className="muted">Selected stock: <strong>{tradeForm.symbol}</strong></p>
              <p className="muted">
                Order value for 500 shares: {formatCents(tradeValue)}
              </p>
              <div className="trade-actions">
                <button disabled={busy || isAnimatingRolls} type="button" onClick={() => onTrade("BUY")}>
                  Buy 500
                </button>
                <button disabled={busy || isAnimatingRolls} type="button" onClick={() => onTrade("SELL")}>
                  Sell 500
                </button>
                <button className="done" disabled={busy || me?.is_done || isAnimatingRolls} onClick={onAllDone}>
                  {me?.is_done ? "Waiting For Others" : "All Done"}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {me && (
        <section className="panel">
          <h2>Other Players Net Worth</h2>
          <ul className="list">
            {otherPlayersNetWorth.map((entry) => (
              <li key={entry.player_id}>
                {entry.name}: {formatCents(entry.net_worth)}
              </li>
            ))}
          </ul>
        </section>
      )}

      {(latestRound > 0 || game.phase === "COMPLETE") && (
        <section className="panel">
          <h2>Last Roll Results (Round {latestRound})</h2>
          <ul className="list roll-list">
            {latestRoundRolls.map((roll) => (
              <li key={`${roll.round_number}-${roll.roll_number}`}>
                Roll {roll.roll_number}: {roll.symbol} {roll.action} {formatRollAmount(roll)}
              </li>
            ))}
          </ul>
        </section>
      )}

      {game.phase === "COMPLETE" && (
        <section className="panel">
          <h2>Final Standings</h2>
          <ol className="list">
            {standings.map((entry) => (
              <li key={entry.player_id}>
                {entry.name}: Net {formatCents(entry.net_worth)} (Cash {formatCents(entry.cash)}, Holdings {formatCents(entry.holdings_value)})
              </li>
            ))}
          </ol>
          {gameView.winner && <p className="winner">Winner: {gameView.winner.name}</p>}
          <button onClick={onReturnToMainScreen} type="button">Return To Main Screen</button>
        </section>
      )}
    </div>
  );
}
