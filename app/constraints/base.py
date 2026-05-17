from typing import Protocol
from app.models.validation import ValidationResult


class Constraint(Protocol):
    n: int

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        """返回 (row, col) 在此约束下关联的所有格子（不含自身）"""
        ...

    def get_units(self) -> list[list[tuple[int, int]]]:
        """返回此约束下所有单元，每个单元为一个格子列表，用于 hidden single 检测"""
        ...

    def validate(self, board: list[list[int]]) -> ValidationResult:
        """在此约束下校验棋盘是否合法"""
        ...
