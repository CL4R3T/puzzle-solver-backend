from app.models.validation import ValidationResult


class BoxConstraint:
    def __init__(self, n: int, block_shape: tuple[int, int]):
        br, bc = block_shape
        if br * bc != n:
            raise ValueError("block_shape 的面积必须等于棋盘边长 n")
        self.n = n
        self.block_rows = br
        self.block_cols = bc

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        br = self.block_rows
        bc = self.block_cols
        box_r = row // br * br
        box_c = col // bc * bc
        return [
            (r, c)
            for r in range(box_r, box_r + br)
            for c in range(box_c, box_c + bc)
            if (r, c) != (row, col)
        ]

    def get_units(self) -> list[list[tuple[int, int]]]:
        br = self.block_rows
        bc = self.block_cols
        units = []
        for box_r in range(0, self.n, br):
            for box_c in range(0, self.n, bc):
                units.append([
                    (r, c)
                    for r in range(box_r, box_r + br)
                    for c in range(box_c, box_c + bc)
                ])
        return units

    def validate(self, board: list[list[int]]) -> ValidationResult:
        br = self.block_rows
        bc = self.block_cols
        for box_r in range(0, self.n, br):
            for box_c in range(0, self.n, bc):
                seen = set()
                for r in range(box_r, box_r + br):
                    for c in range(box_c, box_c + bc):
                        v = board[r][c]
                        if v != 0:
                            if v in seen:
                                return ValidationResult(valid=False, message="宫内有重复值")
                            seen.add(v)
        return ValidationResult(valid=True, message="宫格约束合法")
