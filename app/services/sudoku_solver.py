"""
数独求解器：NumberPuzzleSolver 的便捷子类，自动配置行+列+宫格约束
"""
from typing import List, Tuple

from app.services.number_puzzle_solver import NumberPuzzleSolver
from app.constraints import RowConstraint, ColumnConstraint, BoxConstraint


class SudokuSolver(NumberPuzzleSolver):
    """数独求解器，支持自定义长方形宫格 (box_rows, box_cols)

    要求 box_rows * box_cols == n。
    """

    def __init__(self, board: List[List[int]], box_shape: Tuple[int, int] = (3, 3)):
        n = len(board)
        constraints = [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, box_shape),
        ]
        super().__init__(board, constraints)
        self.box_rows, self.box_cols = box_shape
