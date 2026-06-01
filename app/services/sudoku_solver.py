"""
数独求解器：NumberPuzzleSolver 的便捷子类，自动配置行+列+宫格约束。
额外约束通过注册机制注入，新增约束类型无需修改本文件。
"""
from collections.abc import Callable
from typing import Any, List, Tuple

from app.services.number_puzzle_solver import NumberPuzzleSolver
from app.constraints import RowConstraint, ColumnConstraint, BoxConstraint


class SudokuSolver(NumberPuzzleSolver):
    """数独求解器，支持自定义长方形宫格 (box_rows, box_cols)

    box_rows * box_cols == n。

    额外约束通过类级注册表 _EXTRA_CONSTRAINTS 管理：
        SudokuSolver.register_extra_constraint(key, factory)

    factory 签名为 (n: int, value: Any) -> list[Constraint]
    """

    _EXTRA_CONSTRAINTS: dict[str, Callable] = {}

    @classmethod
    def register_extra_constraint(cls, key: str, factory: Callable) -> None:
        """注册额外约束工厂。

        key: extra_constraints 中的参数名
        factory: (n: int, value: Any) -> list[Constraint]
        """
        cls._EXTRA_CONSTRAINTS[key] = factory

    def __init__(
        self,
        board: List[List[int]],
        box_shape: Tuple[int, int] = (3, 3),
        extra_constraints: dict[str, Any] | None = None,
    ):
        n = len(board)
        constraints = [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, box_shape),
        ]

        for key, value in (extra_constraints or {}).items():
            factory = self._EXTRA_CONSTRAINTS.get(key)
            if factory is not None:
                constraints.extend(factory(n, value))

        super().__init__(board, constraints)
        self.box_rows, self.box_cols = box_shape
