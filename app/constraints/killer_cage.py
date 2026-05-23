from app.models.validation import ValidationResult


class KillerCageConstraint:
    """杀手数独笼子约束：笼内数字不重复且求和等于目标值。"""

    def __init__(self, n: int, cells: list[tuple[int, int]], target_sum: int):
        self.n = n
        self.cells = cells
        self.target = target_sum

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        eliminations = 0

        determined_sum = 0
        unfilled: list[tuple[int, int]] = []
        for r, c in self.cells:
            if board[r][c] != 0:
                determined_sum += board[r][c]
            else:
                unfilled.append((r, c))

        # 已确定部分超过目标
        if determined_sum > self.target:
            return -1

        if not unfilled:
            return 0 if determined_sum == self.target else -1

        remaining = self.target - determined_sum

        # 仅剩一个空格 — 直接填入差值
        if len(unfilled) == 1:
            r, c = unfilled[0]
            val = remaining
            if not (1 <= val <= self.n):
                return -1
            bit = 1 << (val - 1)
            if (pos[r][c] & bit) == 0:
                return -1
            if pos[r][c].bit_count() > 1:
                removed = pos[r][c] & ~bit
                eliminations += removed.bit_count()
                pos[r][c] = bit
                board[r][c] = val
            return eliminations

        # 提取各未填格子的候选值列表
        cell_candidates: list[list[int]] = []
        for r, c in unfilled:
            candidates = [v for v in self._values_of(pos[r][c])]
            cell_candidates.append(candidates)

        # 回溯枚举所有满足总和且不重复的组合
        valid_combos: list[list[int]] = []
        self._find_combos(cell_candidates, 0, 0, [], valid_combos, remaining)

        if not valid_combos:
            return -1

        # 从每格移除未出现在任何有效组合中的候选值
        for i, (r, c) in enumerate(unfilled):
            valid_vals = {combo[i] for combo in valid_combos}
            new_mask = 0
            for val in valid_vals:
                new_mask |= 1 << (val - 1)
            old_mask = pos[r][c]
            if new_mask != old_mask:
                removed = old_mask & ~new_mask
                eliminations += removed.bit_count()
                pos[r][c] = new_mask
                if pos[r][c] == 0:
                    return -1

        return eliminations

    def _values_of(self, mask: int):
        m = mask
        while m:
            lsb = m & -m
            yield lsb.bit_length()
            m ^= lsb

    def _find_combos(
        self,
        candidates: list[list[int]],
        idx: int,
        current_sum: int,
        current_combo: list[int],
        result: list[list[int]],
        target: int,
    ) -> None:
        """回溯搜索所有和为 target 且无重复值的组合。"""
        if idx == len(candidates):
            if current_sum == target:
                result.append(current_combo[:])
            return

        used = set(current_combo)
        # 剪枝：计算剩余格子能贡献的最小/最大和
        min_possible = current_sum
        max_possible = current_sum
        for j in range(idx, len(candidates)):
            avail = [v for v in candidates[j] if v not in used]
            if not avail:
                return  # 某格无可行值
            # 对于剪枝我们只需估算，使用全局范围即可
            cmin = min(candidates[j])
            cmax = max(candidates[j])
            min_possible += cmin
            max_possible += cmax

        if min_possible > target or max_possible < target:
            return

        for val in candidates[idx]:
            if val in current_combo:
                continue
            if current_sum + val > target:
                continue
            current_combo.append(val)
            self._find_combos(candidates, idx + 1, current_sum + val, current_combo, result, target)
            current_combo.pop()

    def validate(self, board: list[list[int]]) -> ValidationResult:
        vals = [board[r][c] for r, c in self.cells]
        if any(v == 0 for v in vals):
            return ValidationResult(valid=True, message="笼子未填满，跳过校验")
        if sum(vals) != self.target:
            return ValidationResult(
                valid=False, message=f"笼子求和为{sum(vals)}，目标为{self.target}"
            )
        if len(set(vals)) != len(vals):
            return ValidationResult(valid=False, message="笼子内有重复值")
        return ValidationResult(valid=True, message="笼子约束合法")
