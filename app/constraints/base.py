"""约束协议：每个约束封装自己的消元逻辑。"""
from typing import Protocol
from app.models.validation import ValidationResult


class Constraint(Protocol):
    n: int

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        """根据本方约束逻辑，从 pos 中消除不可能的候选值。

        board: 当前确定的盘面（0 表示空格）
        pos:   每个格子的候选值位掩码（会被就地修改）

        返回:
            >0  — 本次消去的候选值个数
             0  — 没有新发现，无法进一步消除
            -1  — 发现矛盾
        """
        ...

    def validate(self, board: list[list[int]]) -> ValidationResult:
        """在此约束下校验棋盘是否合法"""
        ...


def _propagate_units(
    n: int,
    board: list[list[int]],
    pos: list[list[int]],
    units: list[list[tuple[int, int]]],
) -> int:
    """按单元传播：消除已确定值 + 隐式单值检测。

    供 RowConstraint / ColumnConstraint / BoxConstraint / DiagonalConstraint
    共用。不涉及特定约束逻辑，仅按单元拓扑执行标准消元。
    """
    eliminations = 0

    for unit in units:
        # 收集该单元内已确定的值
        determined = set()
        for r, c in unit:
            v = board[r][c]
            if v != 0:
                determined.add(v)

        # 从未确定格子中移除已确定值
        for r, c in unit:
            if board[r][c] == 0:
                for val in determined:
                    bit = 1 << (val - 1)
                    if pos[r][c] & bit:
                        pos[r][c] &= ~bit
                        eliminations += 1
                        if pos[r][c] == 0:
                            return -1

        # 隐式单值检测
        for val in range(1, n + 1):
            if val in determined:
                continue
            cells: list[tuple[int, int]] = []
            for r, c in unit:
                if board[r][c] == 0 and (pos[r][c] & (1 << (val - 1))):
                    cells.append((r, c))
            if len(cells) == 0:
                return -1  # val 无处可放
            if len(cells) == 1:
                r, c = cells[0]
                bit = 1 << (val - 1)
                if pos[r][c] != bit:
                    removed = pos[r][c] & ~bit
                    eliminations += removed.bit_count()
                    pos[r][c] = bit
                    board[r][c] = val

    return eliminations
