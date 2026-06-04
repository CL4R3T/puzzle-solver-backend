from app.models.validation import ValidationResult


class ThermoConstraint:
    """温度计约束：沿折线路径，数字严格单调递增。"""

    def __init__(self, n: int, cells: list[tuple[int, int]]):
        self.n = n
        self.cells = cells
        self.k = len(cells)

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        eliminations = 0

        # 检查已确定值是否违反递增顺序
        for i in range(self.k):
            vi = board[self.cells[i][0]][self.cells[i][1]]
            if vi == 0:
                continue
            for j in range(i + 1, self.k):
                vj = board[self.cells[j][0]][self.cells[j][1]]
                if vj == 0:
                    continue
                if vi >= vj:
                    return -1

        # 对每个未填格子，根据位置限制和相邻确定值收紧候选范围
        for i, (r, c) in enumerate(self.cells):
            if board[r][c] != 0:
                continue

            # 绝对下界：位置 0 最小为 1，位置 i 最小为 i+1
            min_val = i + 1
            # 绝对上界：位置 i 最大为 n - (k-1-i)
            max_val = self.n - (self.k - 1 - i)

            # 收紧下界：找前面最近的确定值
            for j in range(i - 1, -1, -1):
                vj = board[self.cells[j][0]][self.cells[j][1]]
                if vj != 0:
                    min_val = max(min_val, vj + (i - j))
                    break

            # 收紧上界：找后面最近的确定值
            for j in range(i + 1, self.k):
                vj = board[self.cells[j][0]][self.cells[j][1]]
                if vj != 0:
                    max_val = min(max_val, vj - (j - i))
                    break

            if min_val > max_val:
                return -1

            # 从候选掩码中移除范围外的值
            new_mask = 0
            for v in range(min_val, max_val + 1):
                new_mask |= 1 << (v - 1)
            new_mask &= pos[r][c]
            if new_mask == 0:
                return -1
            if new_mask != pos[r][c]:
                removed = pos[r][c] & ~new_mask
                eliminations += removed.bit_count()
                pos[r][c] = new_mask

        return eliminations

    def validate(self, board: list[list[int]]) -> ValidationResult:
        vals = [board[r][c] for r, c in self.cells]
        if any(v == 0 for v in vals):
            return ValidationResult(valid=True, message="温度计未填满，跳过校验")
        for v in vals:
            if not (1 <= v <= self.n):
                return ValidationResult(valid=False, message=f"温度计上有非法值 {v}")
        for i in range(1, self.k):
            if vals[i] <= vals[i - 1]:
                return ValidationResult(
                    valid=False,
                    message=f"温度计上位置 {self.cells[i]} 的值 {vals[i]} 不严格大于前一位置的值 {vals[i-1]}",
                )
        return ValidationResult(valid=True, message="温度计约束合法")
