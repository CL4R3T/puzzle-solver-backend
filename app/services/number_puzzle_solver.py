
import copy
from typing import List, Tuple, Optional
from app.models import ValidationResult

class NumberPuzzleSolver:
    """通用填数谜题求解器（无宫格概念，任意边长 n）。

    使用 n 位的 int 作为每个格子的可能性掩码：最低位表示数字 1，
    次位表示数字 2，依此类推。已填的格子其掩码为单一位。
    """

    def __init__(self, board: List[List[int]]):
        self.board: List[List[int]] = copy.deepcopy(board)
        self.n = len(self.board)
        if any(len(row) != self.n for row in self.board):
            raise ValueError("棋盘必须为正方形")

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

    def _count_bits(self, mask: int) -> int:
        return mask.bit_count()

    # ---------- 约束传播基础操作 ----------
    def _get_peers(self, row: int, col: int) -> List[Tuple[int, int]]:
        """返回 (row,col) 在同一行和列的其他格子（不包含自身）。"""
        peers: List[Tuple[int, int]] = []
        for c in range(self.n):
            if c != col:
                peers.append((row, c))
        for r in range(self.n):
            if r != row:
                peers.append((r, col))
        return peers

    def _eliminate(self, row: int, col: int, val: int) -> bool:
        """从 (row,col) 的可能性中移除 val。若变为单一可能则递归传播。

        返回 True 表示成功（无矛盾），False 表示出现矛盾。
        """
        bit = 1 << (val - 1)
        if (self.pos[row][col] & bit) == 0:
            return True
        self.pos[row][col] &= ~bit
        if self.pos[row][col] == 0:
            return False
        if self._count_bits(self.pos[row][col]) == 1:
            # 裸单，确定值并传播
            d2 = next(self._mask_to_values(self.pos[row][col]))
            self.board[row][col] = d2
            for r, c in self._get_peers(row, col):
                if not self._eliminate(r, c, d2):
                    return False
        return True

    def _assign(self, row: int, col: int, val: int) -> bool:
        """将 val 赋给 (row,col)，并传播约束。"""
        # 先移除该格其他可能性
        other_mask = self.pos[row][col] & ~(1 << (val - 1))
        for d in list(self._mask_to_values(other_mask)):
            if not self._eliminate(row, col, d):
                return False
        self.board[row][col] = val
        # 然后从 peers 中移除该值
        for r, c in self._get_peers(row, col):
            if not self._eliminate(r, c, val):
                return False
        return True

    def _find_hidden_single(self, unit: List[Tuple[int, int]]) -> Optional[Tuple[int, int, int]]:
        """在给定范围 unit （行或列）中查找隐藏的唯一值。返回 (r,c,val) 或 None。"""
        for val in range(1, self.n + 1):
            cells = [(r, c) for r, c in unit if (self.pos[r][c] & (1 << (val - 1))) != 0]
            if len(cells) == 1:
                r, c = cells[0]
                if self._count_bits(self.pos[r][c]) > 1:
                    return (r, c, val)
        return None

    def _propagate(self) -> bool:
        """执行裸单 + hidden single 直到不再变化。返回是否成功。"""
        changed = True
        while changed:
            changed = False
            # 裸单处理
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

        return True

    def _find_min_cell(self) -> Optional[Tuple[int, int]]:
        best: Optional[Tuple[int, int]] = None
        min_size = self.n + 1
        for r in range(self.n):
            for c in range(self.n):
                s = self._count_bits(self.pos[r][c])
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
        # 备份当前状态
        for val in list(self._mask_to_values(self.pos[row][col])):
            board_cpy = copy.deepcopy(self.board)
            pos_cpy = copy.deepcopy(self.pos)
            solver = NumberPuzzleSolver(board_cpy)
            solver.pos = pos_cpy
            if solver._assign(row, col, val):
                if solver._solve_with_cp():
                    # 将解写回当前对象
                    self.board = solver.board
                    self.pos = solver.pos
                    return True
        return False

    def solve(self) -> Optional[List[List[int]]]:
        """尝试求解，失败返回 None，成功返回解盘（新的二维列表）。"""
        # 在开始前把已知格子的约束传播一次
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] != 0:
                    if not self._assign(r, c, self.board[r][c]):
                        return None

        if self._solve_with_cp():
            return self.board
        return None

    def validate_board(board: list[list[int]]) -> ValidationResult:
        """确保棋盘为正方形"""
        n = len(board)
        for row in board:
            if len(row) != n:
                return ValidationResult(valid=False, message="棋盘不是正方形")
            for cell in row:
                if not 0 <= cell <= n:
                    return ValidationResult(valid=False, message=f"格子值必须在0-{n}之间")
        for row in range(n):
            for col in range(n):
                if board[row][col] != 0:
                    for r in range(row+1,n):
                        if board[r][col] == board[row][col]:
                            return ValidationResult(valid=False, message="格子值重复")
                    for c in range(col+1,n):
                        if board[row][c] == board[row][col]:
                            return ValidationResult(valid=False, message="格子值重复")
        return ValidationResult(valid=True, message="棋盘合法")

