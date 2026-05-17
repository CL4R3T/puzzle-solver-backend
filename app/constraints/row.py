from app.models.validation import ValidationResult


class RowConstraint:
    def __init__(self, n: int):
        self.n = n

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        return [(row, c) for c in range(self.n) if c != col]

    def get_units(self) -> list[list[tuple[int, int]]]:
        return [[(r, c) for c in range(self.n)] for r in range(self.n)]

    def validate(self, board: list[list[int]]) -> ValidationResult:
        for r in range(self.n):
            seen = set()
            for c in range(self.n):
                v = board[r][c]
                if v != 0:
                    if v in seen:
                        return ValidationResult(valid=False, message=f"第{r}行有重复值{v}")
                    seen.add(v)
        return ValidationResult(valid=True, message="行约束合法")
