
import { useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [game, setGame] = useState(new Chess());
  const [thinking, setThinking] = useState(false);
  const [engineInfo, setEngineInfo] = useState(null);
  const [error, setError] = useState("");

  async function getAIMove(currentGame) {
    setThinking(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/best-move`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fen: currentGame.fen(),
          depth: 3,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "AI request failed");
      }

      const move = data.best_move;

      const aiGame = new Chess(currentGame.fen());

      aiGame.move({
        from: move.substring(0, 2),
        to: move.substring(2, 4),
        promotion: move.length === 5 ? move[4] : "q",
      });

      setGame(aiGame);
      setEngineInfo(data);
    } catch (err) {
      setError(err.message || "Could not connect to the AI.");
    } finally {
      setThinking(false);
    }
  }

  function onPieceDrop({ sourceSquare, targetSquare }) {
    if (thinking || game.turn() !== "w" || game.isGameOver()) {
      return false;
    }

    const nextGame = new Chess(game.fen());

    try {
      const move = nextGame.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });

      if (!move) return false;

      setGame(nextGame);
      setEngineInfo(null);

      if (!nextGame.isGameOver()) {
        getAIMove(nextGame);
      }

      return true;
    } catch {
      return false;
    }
  }

  function resetGame() {
    setGame(new Chess());
    setThinking(false);
    setEngineInfo(null);
    setError("");
  }

  function undoMove() {
    if (thinking) return;

    const previousGame = new Chess(game.fen());

    if (previousGame.history().length >= 2) {
      previousGame.undo();
      previousGame.undo();
      setGame(previousGame);
      setEngineInfo(null);
      setError("");
    }
  }

  const status = game.isGameOver()
    ? game.isCheckmate()
      ? `Checkmate! ${game.turn() === "w" ? "Black" : "White"} wins.`
      : "Game drawn!"
    : thinking
      ? "AI is thinking..."
      : game.isCheck()
        ? `${game.turn() === "w" ? "White" : "Black"} is in check!`
        : "Your turn — White";

  return (
    <div className="app">
      <h1>CHESS BOT</h1>
      <p>Powered by Minimax + Alpha-Beta Pruning</p>

      <div className="board">
        <Chessboard
          options={{
            position: game.fen(),
            onPieceDrop,
            boardOrientation: "white",
          }}
        />
      </div>

      <h3>{status}</h3>

      <div className="controls">
        <button onClick={resetGame} disabled={thinking}>
          New Game
        </button>

        <button
          onClick={undoMove}
          disabled={thinking || game.history().length < 2}
        >
          Undo
        </button>
      </div>

      {error && <p className="error">Error: {error}</p>}

      {engineInfo && (
        <div className="engine-info">
          <h3>Engine Statistics</h3>
          <p>Best move: {engineInfo.best_move}</p>
          <p>Evaluation: {engineInfo.score}</p>
          <p>Search depth: {engineInfo.depth}</p>
          <p>Nodes searched: {engineInfo.nodes_searched}</p>
          <p>Leaves evaluated: {engineInfo.leaves_evaluated}</p>
          <p>Alpha-Beta cutoffs: {engineInfo.cutoffs}</p>
        </div>
      )}
    </div>
  );
}

export default App;
