# 多解检测与唯一性校验

## 现状问题

当前求解器的 `solve()` 方法在找到第一个有效解后立即返回：

```python
# app/services/number_puzzle_solver.py
def _solve_with_cp(self) -> bool:
    ...
    for val in list(self._mask_to_values(self.pos[row][col])):
        ...
        if solver._assign(row, col, val):
            if solver._solve_with_cp():
                self.board = solver.board
                self.pos = solver.pos
                return True       # ← 找到第一个解就返回
    return False
```

而当前的 `/api/sudoku/validate` 端点只做了**静态棋盘合法性校验**（检查行/列/宫有无重复值），完全没有检查解的存在性或唯一性：

```python
# 当前的 validate 只做了这些：
# 1. 棋盘是正方形
# 2. 值在 [0, n] 范围内
# 3. 无行/列/宫重复
# 没有检查 → 是否有解？是否有唯一解？
```

这导致一个严重问题：一道在行/列/宫上没有明显冲突的谜题可能通过 validate 校验，但实际上它有 0 个解（不可解）或 2+ 个解（不合格的谜题）。对于前端 puzzle 应用，这是一个关键缺陷——非唯一解的谜题会导致用户体验极差（玩家填了一个合法答案却被判错）。

## 改进方案

### solver 层：支持限数搜索

给求解器增加一个参数，控制找到的解的数量上限：

```python
class PuzzleSolver:
    def solve(self, max_solutions: int = 1) -> SolveResult:
        """
        max_solutions:
            0 → 找出所有解
            1 → 只找第一个解（当前行为）
            2 → 找最多 2 个解（用于唯一性检测）
        """
        self._max_solutions = max_solutions
        self._solutions: list[list[list[int]]] = []
        self._solve_with_cp()
        return SolveResult(
            solutions=self._solutions,
            solution_count=len(self._solutions),
        )
```

回溯时，找到解后不立即返回，而是保存解并继续搜索（除非已满足上限）：

```python
def _solve_with_cp(self) -> bool:
    if not self._propagate():
        return False

    cell = self._find_min_cell()
    if cell is None:
        # 找到一个解
        self._solutions.append(copy.deepcopy(self.board))
        return len(self._solutions) >= self._max_solutions  # True=继续搜

    row, col = cell
    for val in list(self._mask_to_values(self.pos[row][col])):
        self._push_state()
        if self._assign(row, col, val):
            if self._solve_with_cp():
                return True  # 已达到上限，停止
        self._pop_state()
    return False
```

关键优化：`max_solutions=2` 时，一旦找到第二个解就立即停止，不会继续遍历剩余的搜索空间。这使得唯一性检测的开销仅比找第一个解略高（通常只多探索一小部分分支）。

### API 层：升级 validate 端点

将 validate 从纯静态校验升级为语义校验：

```python
@router.post("/{type_id}/validate")
async def validate_puzzle(type_id: str, request: SolvePuzzleRequest):
    puzzle_type = PuzzleRegistry.get(type_id)

    # 第一步：静态校验
    static_result = puzzle_type.solver_class.validate_board(
        request.board, **request.params
    )
    if not static_result.valid:
        return ValidationResponse(
            valid=False,
            unique_solution=None,
            message=static_result.message,
        )

    # 第二步：解存在性和唯一性校验
    solver = puzzle_type.solver_class(request.board, **request.params)
    result = solver.solve(max_solutions=2)

    if result.solution_count == 0:
        return ValidationResponse(
            valid=False,
            unique_solution=False,
            message="棋盘无解",
        )
    elif result.solution_count > 1:
        return ValidationResponse(
            valid=True,
            unique_solution=False,
            message="棋盘合法但存在多个解",
        )
    else:
        return ValidationResponse(
            valid=True,
            unique_solution=True,
            message="棋盘合法且存在唯一解",
        )
```

### 响应模型升级

```python
class ValidationResponse(BaseModel):
    valid: bool
    unique_solution: bool | None  # None=未检测（静态校验未通过）
    message: str
```

## 额外用途

`solve(max_solutions=0)` 或 `solve(max_solutions=N)` 还可用于：

- **谜题生成**：挖空法需要验证是否仍保持唯一解
- **谜题分析**：统计一个给定 pattern 有多少种解法
- **前端提示**：如果用户点「显示所有可能性」，可以枚举前 K 个解

## 预期收益

1. validate 端点真正能回答「这道题合格吗」
2. 为谜题生成功能提供必要的基础能力
3. 对现有行为零影响（`max_solutions=1` 时与当前完全一致）

## 注意事项

- 枚举所有解（`max_solutions=0`）可能在极端情况下（如几乎空白的棋盘）产生天文数字的解，需要考虑额外的安全限制（最大解数量、超时）
- unique_solution 检测应该是最常用的模式，`max_solutions=2` 是为此优化的甜点
- 在 API 响应中，一般不需要返回多个解的内容（会很大），只需返回计数和第一个解足矣
