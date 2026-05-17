"""
数独求解器：PuzzleSolver 的便捷子类，自动配置行+列+宫格约束
"""
from typing import List, Tuple

from app.models import ValidationResult
from app.services.number_puzzle_solver import PuzzleSolver
from app.constraints import RowConstraint, ColumnConstraint, BoxConstraint


class SudokuSolver(PuzzleSolver):
    """数独求解器，支持自定义长方形宫格 (block_rows, block_cols)

    要求 block_rows * block_cols == n。
    """

    def __init__(self, board: List[List[int]], block_shape: Tuple[int, int] = (3, 3)):
        n = len(board)
        constraints = [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, block_shape),
        ]
        super().__init__(board, constraints)
        self.block_rows, self.block_cols = block_shape

    @staticmethod
    def validate_board(board: List[List[int]], block_shape: Tuple[int, int] = (3, 3)) -> ValidationResult:
        n = len(board)
        for constraint in [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, block_shape),
        ]:
            result = constraint.validate(board)
            if not result.valid:
                return result
        return ValidationResult(valid=True, message="棋盘合法")
