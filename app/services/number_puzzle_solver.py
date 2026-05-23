import copy
from typing import List, Optional

from app.models import ValidationResult
from app.constraints import Constraint


class NumberPuzzleSolver:
    """通用填数谜题求解器。通过组合约束（而非继承）支持任意变体。

    使用 n 位的 int 作为每个格子的可能性掩码：最低位表示数字 1，
    次位表示数字 2，依此类推。已填的格子其掩码为单一位。

    约束传播采用固定点迭代：交替执行裸单检测和各约束的 propagate 方法，
    直到没有任何约束能进一步消除候选值。之后进入回溯搜索。
    """

    def __init__(self, board: List[List[int]], constraints: List[Constraint]):
        self.board: List[List[int]] = copy.deepcopy(board)
        self.n = len(self.board)
        if any(len(row) != self.n for row in self.board):
            raise ValueError("棋盘必须为正方形")

        self.constraints = constraints

        # 全可能位掩码，例如 n=4 时为 0b1111
        self.all_mask: int = (1 << self.n) - 1

        # pos[r][c] 为 int 掩码
        self.pos: List[List[int]] = [[0] * self.n for _ in range(self.n)]
        for r in range(self.n):
            for c in range(self.n):
                v = self.board[r][c]
                if v != 0:
                    if not (1 <= v <= self.n):
                        raise ValueError(f"格子值必须在1-{self.n}之间")
                    self.pos[r][c] = 1 << (v - 1)
                else:
                    self.pos[r][c] = self.all_mask

    # ---------- 辅助位运算 ----------
    def _mask_to_values(self, mask: int):
        """按从小到大的顺序生成 mask 中的所有数字值（1-based）。"""
        m = mask
        while m:
            lsb = m & -m
            idx = lsb.bit_length() - 1
            yield idx + 1
            m ^= lsb

    # ---------- 约束传播 ----------
    def _propagate(self) -> bool:
        """固定点迭代：裸单检测 → 各约束 propagate，直到无新发现。"""
        while True:
            made_progress = False

            # 裸单检测 & 矛盾检查
            for r in range(self.n):
                for c in range(self.n):
                    if self.board[r][c] == 0:
                        bits = self.pos[r][c].bit_count()
                        if bits == 0:
                            return False
                        if bits == 1:
                            val = next(self._mask_to_values(self.pos[r][c]))
                            self.board[r][c] = val
                            made_progress = True

            # 各约束消元
            for constraint in self.constraints:
                result = constraint.propagate(self.board, self.pos)
                if result == -1:
                    return False
                if result > 0:
                    made_progress = True

            if not made_progress:
                break

        return True

    # ---------- 回溯 ----------
    def _find_min_cell(self) -> Optional[tuple[int, int]]:
        best: Optional[tuple[int, int]] = None
        min_size = self.n + 1
        for r in range(self.n):
            for c in range(self.n):
                s = self.pos[r][c].bit_count()
                if s > 1 and s < min_size:
                    min_size = s
                    best = (r, c)
        return best

    def _solve_with_cp(self) -> bool:
        """约束传播 + 回溯求解。"""
        if not self._propagate():
            return False

        cell = self._find_min_cell()
        if cell is None:
            return True

        row, col = cell
        for val in list(self._mask_to_values(self.pos[row][col])):
            board_saved = copy.deepcopy(self.board)
            pos_saved = copy.deepcopy(self.pos)
            self.board[row][col] = val
            self.pos[row][col] = 1 << (val - 1)
            if self._solve_with_cp():
                return True
            self.board = board_saved
            self.pos = pos_saved
        return False

    def solve(self) -> Optional[List[List[int]]]:
        """尝试求解，失败返回 None，成功返回解盘（新的二维列表）。"""
        if self._solve_with_cp():
            return self.board
        return None

    def validate_board(self) -> ValidationResult:
        """委托各约束校验棋盘合法性。"""
        for constraint in self.constraints:
            result = constraint.validate(self.board)
            if not result.valid:
                return result
        return ValidationResult(valid=True, message="棋盘合法")
