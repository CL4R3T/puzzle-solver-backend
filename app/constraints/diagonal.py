from app.models.validation import ValidationResult


class DiagonalConstraint:
    def __init__(self, n: int):
        self.n = n

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        peers = []
        # 主对角线: row == col
        if row == col:
            peers.extend((i, i) for i in range(self.n) if i != row)
        # 副对角线: row + col == n - 1
        if row + col == self.n - 1:
            peers.extend((i, self.n - 1 - i) for i in range(self.n) if i != row)
        return peers

    def get_units(self) -> list[list[tuple[int, int]]]:
        main_diag = [(i, i) for i in range(self.n)]
        anti_diag = [(i, self.n - 1 - i) for i in range(self.n)]
        return [main_diag, anti_diag]

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
