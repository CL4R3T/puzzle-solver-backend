from app.models.validation import ValidationResult
from app.constraints.base import _propagate_units


class BoxConstraint:
    def __init__(self, n: int, box_shape: tuple[int, int]):
        br, bc = box_shape
        if br * bc != n:
            raise ValueError("box_shape 的面积必须等于棋盘边长 n")
        self.n = n
        self.box_rows = br
        self.box_cols = bc

        # 预计算所有宫格 unit
        units: list[list[tuple[int, int]]] = []
        for box_r in range(0, n, br):
            for box_c in range(0, n, bc):
                units.append([
                    (r, c)
                    for r in range(box_r, box_r + br)
                    for c in range(box_c, box_c + bc)
                ])
        self._units = units

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        return _propagate_units(self.n, board, pos, self._units)

    def validate(self, board: list[list[int]]) -> ValidationResult:
        br = self.box_rows
        bc = self.box_cols
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
