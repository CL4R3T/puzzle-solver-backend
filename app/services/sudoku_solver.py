"""
数独求解服务（约束传播 + 回溯）
"""

import copy

from app.models import ValidationResult

ALL_VALUES = frozenset(range(1, 10))


def _init_possibilities(board: list[list[int]]) -> list[list[set[int]]]:
    """根据初始棋盘构建可能性矩阵，已填格子为单元素集"""
    pos = [[set() for _ in range(9)] for _ in range(9)]
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                pos[r][c] = {board[r][c]}
            else:
                pos[r][c] = set(ALL_VALUES)
    return pos


def _get_peers(row: int, col: int) -> list[tuple[int, int]]:
    """返回 (row, col) 所在行、列、宫格内的所有其他格子（不含自身）"""
    peers: set[tuple[int, int]] = set()
    for c in range(9):
        peers.add((row, c))
    for r in range(9):
        peers.add((r, col))
    box_r, box_c = row // 3 * 3, col // 3 * 3
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            peers.add((r, c))
    peers.discard((row, col))
    return list(peers)


def _eliminate(
    board: list[list[int]],
    pos: list[list[set[int]]],
    row: int,
    col: int,
    val: int,
) -> bool:
    """
    从格子 (row, col) 中移除 val。
    若该格因此变为裸单，则递归传播到其 peers。
    返回是否成功（无矛盾）。
    """
    if val not in pos[row][col]:
        return True
    pos[row][col].discard(val)
    if len(pos[row][col]) == 0:
        return False
    if len(pos[row][col]) == 1:
        d2 = next(iter(pos[row][col]))
        board[row][col] = d2
        for r, c in _get_peers(row, col):
            if not _eliminate(board, pos, r, c, d2):
                return False
    return True


def _assign(
    board: list[list[int]],
    pos: list[list[set[int]]],
    row: int,
    col: int,
    val: int,
) -> bool:
    """将 val 赋给 (row, col)，并传播约束。返回是否成功。"""
    others = pos[row][col] - {val}
    for d in others:
        if not _eliminate(board, pos, row, col, d):
            return False
    board[row][col] = val
    for r, c in _get_peers(row, col):
        if not _eliminate(board, pos, r, c, val):
            return False
    return True


def _find_hidden_single(
    pos: list[list[set[int]]], unit: list[tuple[int, int]]
) -> tuple[int, int, int] | None:
    """
    在 unit 内查找 hidden single：某个数字只在一个格子的可能性中出现。
    返回 (row, col, val) 或 None。
    """
    for val in range(1, 10):
        cells_with_val = [(r, c) for r, c in unit if val in pos[r][c]]
        if len(cells_with_val) == 1:
            r, c = cells_with_val[0]
            if len(pos[r][c]) > 1:
                return (r, c, val)
    return None


def _propagate(board: list[list[int]], pos: list[list[set[int]]]) -> bool:
    """
    约束传播：裸单 + hidden single，直到无变化。
    返回是否成功（无矛盾）。
    """
    changed = True
    while changed:
        changed = False
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0 and len(pos[r][c]) == 1:
                    val = next(iter(pos[r][c]))
                    if not _assign(board, pos, r, c, val):
                        return False
                    changed = True

        # Hidden singles: 行、列、宫
        for i in range(9):
            row_unit = [(i, c) for c in range(9) if board[i][c] == 0]
            col_unit = [(r, i) for r in range(9) if board[r][i] == 0]
            for unit in (row_unit, col_unit):
                h = _find_hidden_single(pos, unit)
                if h:
                    r, c, val = h
                    if not _assign(board, pos, r, c, val):
                        return False
                    changed = True

        for br in range(0, 9, 3):
            for bc in range(0, 9, 3):
                box_unit = [
                    (r, c)
                    for r in range(br, br + 3)
                    for c in range(bc, bc + 3)
                    if board[r][c] == 0
                ]
                h = _find_hidden_single(pos, box_unit)
                if h:
                    r, c, val = h
                    if not _assign(board, pos, r, c, val):
                        return False
                    changed = True

    return True


def _find_min_cell(pos: list[list[set[int]]]) -> tuple[int, int] | None:
    """找到可能性最少的空格（MRV），用于回溯时的猜测"""
    best: tuple[int, int] | None = None
    min_size = 10
    for r in range(9):
        for c in range(9):
            s = len(pos[r][c])
            if s > 1 and s < min_size:
                min_size = s
                best = (r, c)
    return best


def _solve_with_cp(board: list[list[int]], pos: list[list[set[int]]]) -> bool:
    """
    约束传播 + 回溯求解。
    有解返回 True，无解返回 False。
    """
    if not _propagate(board, pos):
        return False

    cell = _find_min_cell(pos)
    if cell is None:
        return True  # 已解完

    row, col = cell
    for val in list(pos[row][col]):
        board_cpy = copy.deepcopy(board)
        pos_cpy = copy.deepcopy(pos)
        if _assign(board_cpy, pos_cpy, row, col, val):
            if _solve_with_cp(board_cpy, pos_cpy):
                board[:] = [row[:] for row in board_cpy]
                return True
    return False


def solve_sudoku(board: list[list[int]]) -> list[list[int]] | None:
    """
    求解数独（约束传播 + 回溯）

    Args:
        board: 9x9 棋盘，0 表示空格

    Returns:
        解出的棋盘，无解时返回 None
    """
    board_copy = copy.deepcopy(board)
    pos = _init_possibilities(board_copy)
    # 传播初始已填格子的约束
    for r in range(9):
        for c in range(9):
            if board_copy[r][c] != 0:
                if not _assign(board_copy, pos, r, c, board_copy[r][c]):
                    return None
    if _solve_with_cp(board_copy, pos):
        return board_copy
    return None


def validate_board(board: list[list[int]]) -> ValidationResult:
    """
    校验数独棋盘是否合法（无行/列/宫格内重复）

    Args:
        board: 9x9 棋盘

    Returns:
        校验结果
    """
    # TODO: 实现合法性校验逻辑
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0:
                if board[r][c] not in range(1, 10):
                    return ValidationResult(valid=False, message="格子值必须在1-9之间")
                for r1,c1 in _get_peers(r,c):
                    if board[r1][c1] == board[r][c]:
                        return ValidationResult(valid=False, message="格子值重复")
    return ValidationResult(valid=True, message="校验通过")
