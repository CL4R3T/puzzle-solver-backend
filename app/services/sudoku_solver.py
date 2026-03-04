"""
数独求解器：基于 NumberPuzzleSolver 的子类，支持自定义长方形宫格
"""
from typing import List, Tuple, Optional

from app.models import ValidationResult
from app.services import NumberPuzzleSolver


class SudokuSolver(NumberPuzzleSolver):
    """数独求解器，支持自定义长方形宫格 (block_rows, block_cols)

    要求 block_rows * block_cols == n。
    """

    def __init__(self, board: List[List[int]], block_shape: Tuple[int, int] = (3, 3)):
        super().__init__(board)
        br, bc = block_shape
        if br * bc != self.n:
            raise ValueError("block_shape 的面积必须等于棋盘边长 n")
        self.block_rows = br
        self.block_cols = bc

    def _get_peers(self, row: int, col: int) -> List[Tuple[int, int]]:
        """返回 (row,col) 在同一行、列和宫内的其他格子（不包含自身）。"""
        peers = set(super()._get_peers(row, col))

        box_r = row // self.block_rows * self.block_rows
        box_c = col // self.block_cols * self.block_cols
        for r in range(box_r, box_r + self.block_rows):
            for c in range(box_c, box_c + self.block_cols):
                if (r, c) != (row, col):
                    peers.add((r, c))

        return list(peers)

    def _propagate(self) -> bool:
        """扩展父类的传播，在行、列、宫内查找 hidden singles。"""
        changed = True
        while changed:
            changed = False
            # 裸单处理（复用父类逻辑）
            for r in range(self.n):
                for c in range(self.n):
                    if self.board[r][c] == 0 and self._count_bits(self.pos[r][c]) == 1:
                        val = next(self._mask_to_values(self.pos[r][c]))
                        if not self._assign(r, c, val):
                            return False
                        changed = True

            # hidden singles：行与列
            for i in range(self.n):
                row_unit = [(i, c) for c in range(self.n) if self.board[i][c] == 0]
                col_unit = [(r, i) for r in range(self.n) if self.board[r][i] == 0]
                for unit in (row_unit, col_unit):
                    h = self._find_hidden_single(unit)
                    if h:
                        r, c, val = h
                        if not self._assign(r, c, val):
                            return False
                        changed = True

            # hidden singles：宫格
            for br in range(0, self.n, self.block_rows):
                for bc in range(0, self.n, self.block_cols):
                    box_unit = [
                        (r, c)
                        for r in range(br, br + self.block_rows)
                        for c in range(bc, bc + self.block_cols)
                        if self.board[r][c] == 0
                    ]
                    h = self._find_hidden_single(box_unit)
                    if h:
                        r, c, val = h
                        if not self._assign(r, c, val):
                            return False
                        changed = True

        return True

    def validate_board(board: List[List[int]], block_shape: Tuple[int, int] = (3, 3)) -> ValidationResult:
        super_result = NumberPuzzleSolver.validate_board(board)
        if not super_result.valid:
            return super_result
        # 额外验证宫内无重复
        n = len(board)
        br, bc = block_shape
        if br * bc != n:
            return ValidationResult(valid=False, message="block_shape 的面积必须等于棋盘边长 n")

        for r in range(0, n, br):
            for c in range(0, n, bc):
                box_values = set()
                for r1 in range(r, r + br):
                    for c1 in range(c, c + bc):
                        if board[r1][c1] != 0:
                            if board[r1][c1] in box_values:
                                return ValidationResult(valid=False, message="宫内有重复值")
                            box_values.add(board[r1][c1])
        return ValidationResult(valid=True, message="棋盘合法")