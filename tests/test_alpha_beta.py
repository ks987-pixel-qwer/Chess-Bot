import chess

from chessbot.alpha_beta import alpha_beta_search


def test_returns_legal_move():
    board = chess.Board()

    result = alpha_beta_search(board, depth=2)

    assert result.best_move is not None
    assert result.best_move in board.legal_moves


def test_board_is_unchanged():
    board = chess.Board()
    original_fen = board.fen()

    alpha_beta_search(board, depth=2)

    assert board.fen() == original_fen


def test_search_statistics():
    board = chess.Board()

    result = alpha_beta_search(board, depth=2)

    assert result.nodes_searched > 0
    assert result.leaves_evaluated > 0
    assert result.cutoffs >= 0


def test_checkmate_position():
    board = chess.Board("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")

    result = alpha_beta_search(board, depth=2)

    assert result.best_move is None
    assert result.score == 100000