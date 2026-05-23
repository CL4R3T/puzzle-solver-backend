# 逐步求解与提示系统

## 现状问题

当前求解器的 `solve()` 方法是一个黑箱操作：传入棋盘，一次性返回完整结果。对 API 消费者（前端）来说，只能得到「最终答案」。但在实际的产品场景中，以下需求很常见：

- **提示系统**：「给我下一步」——不是要完整答案，而是要一个推理步骤
- **教学场景**：展示解题思路，说明每一步用了什么推理技术（裸单？隐藏单？回溯？）
- **调试/验证**：开发者想知道求解器在某一步为什么选择了这个数字

当前代码中，`_propagate()` 和 `_solve_with_cp()` 内部的推理过程完全不可见。

## 改进方案

给求解器增加一个可选的**记录模式**。在记录模式下，每次 `_assign`（确定一个格子）、`_eliminate`（排除候选值）时，将操作包装为「推理步骤」并追加到日志中。

### 步骤的数据结构

```python
from enum import Enum
from dataclasses import dataclass

class StepType(Enum):
    GIVEN = "given"                  # 初始提示数
    NAKED_SINGLE = "naked_single"    # 裸单：该格只剩一个候选值
    HIDDEN_SINGLE = "hidden_single"  # 隐藏单：该值在其单元内只出现一次
    BACKTRACK = "backtrack"          # 回溯尝试

@dataclass
class SolveStep:
    step_type: StepType
    row: int
    col: int
    value: int
    reason: str          # 人类可读的推理说明
    candidates_before: list[int] | None = None  # 推理前的候选值
```

### 求解器的记录模式

```python
class NumberPuzzleSolver:
    def __init__(self, ..., record_steps: bool = False):
        self._record_steps = record_steps
        self._steps: list[SolveStep] = []

    def _assign(self, row: int, col: int, val: int,
                reason: StepType = StepType.GIVEN, description: str = "") -> bool:
        if self._record_steps:
            self._steps.append(SolveStep(
                step_type=reason,
                row=row, col=col, value=val,
                reason=description or str(reason),
                candidates_before=list(self._mask_to_values(self.pos[row][col])),
            ))
        # ... 原有的 assign 逻辑

    def solve(self, ...) -> SolveResult:
        ...
        return SolveResult(
            solutions=self._solutions,
            solution_count=len(self._solutions),
            steps=self._steps if self._record_steps else None,
        )
```

### 推理说明示例

裸单：

```
{"step_type": "naked_single", "row": 0, "col": 2, "value": 4,
 "reason": "该格只剩下一个候选值 4（其他值均被同行/列/宫的已知数字排除）",
 "candidates_before": [1, 4]}
```

隐藏单：

```
{"step_type": "hidden_single", "row": 4, "col": 6, "value": 7,
 "reason": "在第 4 行中，数字 7 只能放在第 6 列（其他空格均已排除 7 的可能）",
 "candidates_before": [2, 5, 7]}
```

### 提示 API

前端可以通过两种方式使用：

**方式一：完整求解 + 步骤回放**

```
POST /api/puzzle/{type}/solve
{
  "board": [...],
  "params": {...},
  "include_steps": true
}
→ 返回 solution + steps 数组，前端可以逐步回放
```

**方式二：单步提示**

```
POST /api/puzzle/{type}/hint
{
  "board": [...],
  "params": {...}
}
→ 返回下一个最确定的推理步骤（如果有裸单/隐藏单就直接返回，否则 fallback 到回溯的最小候选格）
```

单步提示的实现：在求解器内部，先运行一轮不产生副作用的传播，找到第一个可以确定的格子，返回步骤信息但不修改棋盘状态。如果传播卡住，返回最早的回退格子和可能的候选值列表：

```python
class NumberPuzzleSolver:
    def get_hint(self) -> SolveStep | None:
        """在不修改棋盘的情况下，返回下一步的推理提示"""
        # 运行一轮传播，但不实际赋值
        for r in range(self.n):
            for c in range(self.n):
                if self.board[r][c] == 0 and self._count_bits(self.pos[r][c]) == 1:
                    val = next(self._mask_to_values(self.pos[r][c]))
                    return SolveStep(
                        step_type=StepType.NAKED_SINGLE,
                        row=r, col=c, value=val,
                        reason=f"该格只剩下一个候选值 {val}",
                        candidates_before=list(self._mask_to_values(self.pos[r][c])),
                    )

        # 类似的 hidden single 检测...

        # 如果没有直接可推理的，返回最简单的回溯建议
        cell = self._find_min_cell()
        if cell:
            r, c = cell
            return SolveStep(
                step_type=StepType.BACKTRACK,
                row=r, col=c, value=0,  # 无确定值
                reason="需要用试错法，建议尝试以下候选值之一",
                candidates_before=list(self._mask_to_values(self.pos[r][c])),
            )
        return None  # 已解决
```

## 预期收益

1. 前端可以实现「给个提示」按钮，逐步引导用户
2. 教学类应用可以直接展示每一步的推理逻辑
3. 方便开发者调试和验证求解器行为

## 注意事项

- `include_steps=True` 可能显著增加响应体大小（特别是大型棋盘或需要大量回溯的谜题）。建议设置步骤数量上限
- hint 功能需要求解器实例化但不应修改棋盘——可以用 `PuzzleSolver` 的只读查询模式，或 clone 一个临时实例
- 回溯步骤的「推理说明」比约束传播步骤的难写——回溯本质上就是试错，用人类可理解的方式解释试错过程需要额外的设计
