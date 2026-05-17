from app.models.validation import ValidationResult


class ColumnConstraint:
    def __init__(self, n: int):
        self.n = n

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        return [(r, col) for r in range(self.n) if r != row]

    def get_units(self) -> list[list[tuple[int, int]]]:
        return [[(r, c) for r in range(self.n)] for c in range(self.n)]

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
