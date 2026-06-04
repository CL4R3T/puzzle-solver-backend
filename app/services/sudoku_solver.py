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
        SudokuSolver.register_extra_constraint(key, factory, name=..., description=..., param_schema=...)

    factory 签名为 (n: int, value: Any) -> list[Constraint]
    """

    _EXTRA_CONSTRAINTS: dict[str, dict] = {}

    @classmethod
    def register_extra_constraint(
        cls,
        key: str,
        factory: Callable,
        *,
        name: str = "",
        description: str = "",
        param_schema: dict | None = None,
    ) -> None:
        """注册额外约束工厂。

        key: extra_constraints 中的参数名
        factory: (n: int, value: Any) -> list[Constraint]
        name: 约束的显示名称
        description: 约束的描述
        param_schema: 参数的 JSON Schema
        """
        cls._EXTRA_CONSTRAINTS[key] = {
            "factory": factory,
            "name": name,
            "description": description,
            "param_schema": param_schema,
        }

    @classmethod
    def get_extra_constraints_info(cls) -> list[dict]:
        """获取所有已注册的额外约束信息"""
        return [
            {
                "key": key,
                "name": meta["name"],
                "description": meta["description"],
                "param_schema": meta["param_schema"],
            }
            for key, meta in cls._EXTRA_CONSTRAINTS.items()
        ]

    @classmethod
    def get_builtin_constraints_info(cls) -> list[dict]:
        """获取内置约束信息"""
        return [
            {
                "key": "row",
                "name": "行约束",
                "description": "每行数字不重复",
            },
            {
                "key": "column",
                "name": "列约束",
                "description": "每列数字不重复",
            },
            {
                "key": "box",
                "name": "宫格约束",
                "description": "宫格内数字不重复，可通过 box_shape 参数调整宫格形状",
                "param_schema": {
                    "box_shape": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                        "default": [3, 3],
                        "description": "宫格的行数和列数",
                    },
                },
            },
        ]

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
            entry = self._EXTRA_CONSTRAINTS.get(key)
            if entry is not None:
                constraints.extend(entry["factory"](n, value))

        super().__init__(board, constraints)
        self.box_rows, self.box_cols = box_shape
