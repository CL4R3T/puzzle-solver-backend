"""杀手数独求解器：标准数独约束 + 笼子求和约束。"""
from typing import List

from app.services.number_puzzle_solver import NumberPuzzleSolver
from app.constraints import RowConstraint, ColumnConstraint, BoxConstraint, KillerCageConstraint


class KillerSudokuSolver(NumberPuzzleSolver):
    def __init__(self, board: List[List[int]], cages: List[dict], box_shape: tuple[int, int] = (3, 3)):
        n = len(board)
        constraints = [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, box_shape),
        ]
        for cage in cages:
            cells = [tuple(c) for c in cage["cells"]]
            constraints.append(KillerCageConstraint(n, cells, cage["sum"]))
        super().__init__(board, constraints)
