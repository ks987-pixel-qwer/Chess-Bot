#Uses both alpha beta and minimax search to find the best move for a given position.
from dataclasses import dataclass
import chess

from chessbot.evaluation import evaluate


@dataclass
class SearchResult:
    best_move: chess.Move | None
    score: int
    nodes_searched: int
    leaves_evaluated: int
    cutoffs: int


def alpha_beta_search(
    board: chess.Board,
    depth: int = 3
) -> SearchResult:

    if depth < 1:
        raise ValueError("Depth must be at least 1")

    stats = {
        "nodes": 0,
        "leaves": 0,
        "cutoffs": 0
    }

    def search(position, remaining_depth, alpha, beta):

        stats["nodes"] += 1

        # Handle terminal positions
        if position.is_game_over(claim_draw=True):
            stats["leaves"] += 1

            if position.is_checkmate():
                return evaluate(position), None

            return 0, None

        # Evaluate when depth reaches zero
        if remaining_depth == 0:
            stats["leaves"] += 1
            return evaluate(position), None

        maximizing = position.turn == chess.WHITE

        if maximizing:
            best_score = float("-inf")
        else:
            best_score = float("inf")

        best_move = None

        # Try captures and promotions first
        moves = list(position.legal_moves)

        moves.sort(
            key=lambda move: (
                position.is_capture(move),
                move.promotion is not None
            ),
            reverse=True
        )

        for move in moves:

            position.push(move)

            try:
                score, _ = search(
                    position,
                    remaining_depth - 1,
                    alpha,
                    beta
                )
            finally:
                position.pop()

            if maximizing:

                if score > best_score:
                    best_score = score
                    best_move = move

                alpha = max(alpha, best_score)

            else:

                if score < best_score:
                    best_score = score
                    best_move = move

                beta = min(beta, best_score)

            # Alpha-Beta pruning
            if alpha >= beta:
                stats["cutoffs"] += 1
                break

        return best_score, best_move

    score, best_move = search(
        board,
        depth,
        float("-inf"),
        float("inf")
    )

    return SearchResult(
        best_move=best_move,
        score=int(score),
        nodes_searched=stats["nodes"],
        leaves_evaluated=stats["leaves"],
        cutoffs=stats["cutoffs"]
    )
