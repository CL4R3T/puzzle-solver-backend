from app.models.validation import ValidationResult
from app.constraints.base import _propagate_units


class DiagonalConstraint:
    def __init__(self, n: int):
        self.n = n
        self._units: list[list[tuple[int, int]]] = [
            [(i, i) for i in range(n)],
            [(i, n - 1 - i) for i in range(n)],
        ]

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        return _propagate_units(self.n, board, pos, self._units)

    def validate(self, board: list[list[int]]) -> ValidationResult:
        # 主对角线
        seen = set()
        for i in range(self.n):
            v = board[i][i]
            if v != 0:
                if v in seen:
                    return ValidationResult(valid=False, message="主对角线有重复值")
                seen.add(v)
        # 副对角线
        seen = set()
        for i in range(self.n):
            v = board[i][self.n - 1 - i]
            if v != 0:
                if v in seen:
                    return ValidationResult(valid=False, message="副对角线有重复值")
                seen.add(v)
        return ValidationResult(valid=True, message="对角线约束合法")
