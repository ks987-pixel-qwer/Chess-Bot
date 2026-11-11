import logging
import math

import chess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from chessbot.evaluation import evaluate
from chessbot.alpha_beta import alpha_beta_search


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Chess Bot API",
    description=(
        "Backend API for a chess engine supporting board operations, "
        "position evaluation, and future Minimax, Alpha-Beta Pruning, "
        "and Monte Carlo Tree Search implementations."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Request Models
# --------------------------------------------------

DEFAULT_FEN = (
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
)


class PositionRequest(BaseModel):
    fen: str = Field(
        default=DEFAULT_FEN,
        description="Chess position in FEN notation.",
    )

class BestMoveRequest(BaseModel):
    fen: str = Field(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )
    depth: int = Field(default=3, ge=1, le=5)

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def load_board(fen: str) -> chess.Board:
    """
    Create a chess board from FEN notation.

    Raises:
        HTTPException: If the FEN is malformed or the position is invalid.
    """

    try:
        board = chess.Board(fen)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid FEN position."
        )

    if not board.is_valid():
        raise HTTPException(
            status_code=400,
            detail="Invalid chess position.",
        )

    return board


def get_game_status(board: chess.Board) -> dict:
    """Return the current game's status."""

    outcome = board.outcome()

    if outcome is None:
        result = None
        termination = None
    else:
        result = outcome.result()
        termination = outcome.termination.name.lower()

    return {
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "is_game_over": board.is_game_over(),
        "result": result,
        "termination": termination,
    }


# --------------------------------------------------
# Basic Routes
# --------------------------------------------------

@app.get("/")
def home():
    """Check whether the Chess-Bot API is running."""

    return {
        "message": "Chess Bot API is running!",
        "status": "online",
        "version": app.version,
    }


@app.get("/health")
def health():
    """Health check endpoint."""

    return {
        "status": "healthy",
    }


# --------------------------------------------------
# Board Endpoint
# --------------------------------------------------

@app.post("/board")
def get_board(request: PositionRequest):
    """
    Return the board representation and current game status.
    """

    board = load_board(request.fen)

    return {
        "fen": board.fen(),
        "board": str(board),
        "turn": "white" if board.turn else "black",
        **get_game_status(board),
    }


# --------------------------------------------------
# Legal Moves Endpoint
# --------------------------------------------------

@app.post("/legal-moves")
def get_legal_moves(request: PositionRequest):
    """
    Return all legal moves in UCI notation.
    """

    board = load_board(request.fen)

    legal_moves = [move.uci() for move in board.legal_moves]

    return {
        "fen": board.fen(),
        "side_to_move": "white" if board.turn else "black",
        "legal_moves": legal_moves,
        "count": len(legal_moves),
    }


# --------------------------------------------------
# Position Evaluation Endpoint
# --------------------------------------------------

@app.post("/evaluate")
def evaluate_position(request: PositionRequest):
    """
    Evaluate a chess position.

    Assumes evaluate(board) returns a numeric score.
    The score's perspective depends on your evaluation.py.
    """

    board = load_board(request.fen)

    try:
        score = evaluate(board)

        # Convert NumPy scalar values to native Python values.
        if hasattr(score, "item"):
            score = score.item()

        # Reject Boolean, non-numeric, NaN, and infinite scores.
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError("Evaluation must return a numeric score.")

        if not math.isfinite(score):
            raise ValueError("Evaluation must be finite.")

        return {
            "fen": board.fen(),
            "evaluation": score,
            "score_perspective": "defined by evaluation.py",
            "side_to_move": "white" if board.turn else "black",
        }

    except Exception as error:
        logger.exception("Evaluation failed")

        raise HTTPException(
            status_code=500,
            detail="Evaluation failed due to an internal error.",
        ) from error


# --------------------------------------------------
# Game Status Endpoint
# --------------------------------------------------

@app.post("/game-status")
def game_status(request: PositionRequest):
    """
    Return check, checkmate, stalemate, and game result information.
    """

    board = load_board(request.fen)

    return {
        "fen": board.fen(),
        "turn": "white" if board.turn else "black",
        **get_game_status(board),
    }

#--------------------------------------------------
#Best Move Endpoint
#--------------------------------------------------

@app.post("/best-move")
def get_best_move(request: BestMoveRequest):

    board = load_board(request.fen)

    if board.is_game_over(claim_draw=True):
        raise HTTPException(
            status_code=400,
            detail="Game is already over."
        )

    result = alpha_beta_search(board, depth=request.depth)

    return {
        "best_move": result.best_move.uci(),
        "score": result.score,
        "depth": request.depth,
        "nodes_searched": result.nodes_searched,
        "leaves_evaluated": result.leaves_evaluated,
        "cutoffs": result.cutoffs
    }