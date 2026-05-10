# 谜题生成能力

## 现状问题

当前整个代码库只实现了「求解」和「校验」两个能力。Roadmap 提到目标是支持各类变体数独和填数谜题大类，但如果只提供求解，一个谜题应用的使用场景是极度受限的：

- **求解**：用户从别处找到谜题，来这里求解。这是被动场景。
- **生成**：服务自己产出谜题，用户直接来玩。这是主动场景。

几乎所有的在线数独/谜题产品，生成功能都是核心。此外，生成功能还服务于内部的测试流水线（自动生成测试用例）。

## 改进方案

### 核心生成算法：挖空法

最主流的谜题生成方法。思路很简单：

1. **生成完整终盘**：用求解器从空棋盘开始求解，得到一个完全填充的棋盘
2. **随机移除格子**：对已填格子随机打乱顺序，依次尝试移除
3. **唯一性校验**：每移除一个格子后，用求解器的 `solve(max_solutions=2)` 检查是否仍保持唯一解
4. 如果仍唯一 → 保留移除。如果不唯一 → 恢复该格子
5. 重复步骤 3-4 直到满足目标难度或最小提示数

```python
import random

class PuzzleGenerator:
    def __init__(self, solver_class, constraints):
        self.solver_class = solver_class
        self.constraints = constraints

    def generate(self, target_clues: int | None = None) -> list[list[int]]:
        # 步骤 1：生成完整终盘
        empty_board = [[0] * n for _ in range(n)]
        solver = self.solver_class(empty_board, **self.constraints)
        full_board = solver.solve()
        if full_board is None:
            raise GenerationError("无法生成完整终盘")

        # 步骤 2-4：挖空
        puzzle = copy.deepcopy(full_board)
        cells = [(r, c) for r in range(n) for c in range(n)]
        random.shuffle(cells)

        removed = 0
        total_cells = n * n
        for r, c in cells:
            # 尝试移除
            backup = puzzle[r][c]
            puzzle[r][c] = 0

            # 唯一性检查
            solver = self.solver_class(puzzle, **self.constraints)
            result = solver.solve(max_solutions=2)

            if result.solution_count == 1:
                removed += 1
            else:
                puzzle[r][c] = backup  # 恢复

            if target_clues and (total_cells - removed) <= target_clues:
                break

        return puzzle
```

### 难度控制

难度可以通过以下维度调控：

1. **提示数（clue count）**：移除的格子越多（提示数越少），通常越难。但不是绝对的——有时 30 个提示比 25 个提示更难
2. **所需推理技术**：在挖空过程中，调用求解器时记录是否需要回溯（vs 纯传播）。如果某步需要回溯，说明该题的难度超过「初级」
3. **回溯深度**：对于更难的分析，记录求解器回溯的深度和频率

一个简单的难度分级可以这样：

```python
class Difficulty(Enum):
    EASY = "easy"         # 纯传播可解（裸单 + 隐藏单），无回溯
    MEDIUM = "medium"     # 需要少量回溯（<10 次）
    HARD = "hard"         # 需要中等回溯（10-50 次）
    EXPERT = "expert"     # 需要大量回溯（>50 次）
```

### API 端点

```python
@router.post("/{type_id}/generate")
async def generate_puzzle(type_id: str, request: GeneratePuzzleRequest):
    puzzle_type = PuzzleRegistry.get(type_id)
    generator = PuzzleGenerator(puzzle_type.solver_class, request.params)
    puzzle = generator.generate(
        target_clues=request.target_clues,
        difficulty=request.difficulty,
    )
    return GeneratePuzzleResponse(puzzle=puzzle, ...)
```

### 生成中的随机化

为了产出多样化的谜题，有两个随机化点：

1. **终盘生成**：求解器在 `_find_min_cell` 时可以选择随机格子而非候选最少的格子（trade off 性能换多样性）；或者在回溯时对候选值 shuffle
2. **挖空顺序**：`random.shuffle(cells)` 提供了基础多样性

如果需要更可控的多样性，可以让求解器在回溯时接受一个 `random` 实例，通过 seed 实现可复现的生成。

## 预期收益

1. 服务从「被动的求解工具」变为「主动的内容提供商」
2. 为测试提供自动化生成用例的能力
3. 生成 + 求解 + 校验 形成完整的谜题生命周期

## 注意事项

- 挖空法对大棋盘（16×16+）可能非常慢——每次移除都要跑一次求解器的唯一性检测。优化方向：增量校验（只检测移除此格后是否引入多解，而非从零求解）
- 难度分级是一个主观问题，不同来源的难度定义差异很大。建议初期只分 3 档（易/中/难），后续根据用户反馈迭代
- 生成功能需要良好的随机数管理（seed 控制、可复现性），否则调试生成逻辑会非常困难
