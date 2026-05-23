from app.models.validation import ValidationResult
from app.constraints.base import _propagate_units


class ColumnConstraint:
    def __init__(self, n: int):
        self.n = n
        self._units: list[list[tuple[int, int]]] = [
            [(r, c) for r in range(n)] for c in range(n)
        ]

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        return _propagate_units(self.n, board, pos, self._units)

    def validate(self, board: list[list[int]]) -> ValidationResult:
        for c in range(self.n):
            seen = set()
            for r in range(self.n):
                v = board[r][c]
                if v != 0:
                    if v in seen:
                        return ValidationResult(valid=False, message=f"第{c}列有重复值{v}")
                    seen.add(v)
        return ValidationResult(valid=True, message="列约束合法")
