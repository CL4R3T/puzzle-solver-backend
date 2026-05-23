# 回溯机制：以撤销栈替代深拷贝

## 现状问题

当前 `_solve_with_cp()` 在每次尝试候选值时，执行完整的状态拷贝：

```python
# app/services/number_puzzle_solver.py，约 152-159 行
for val in list(self._mask_to_values(self.pos[row][col])):
    board_cpy = copy.deepcopy(self.board)
    pos_cpy = copy.deepcopy(self.pos)
    solver = type(self)(board_cpy)
    solver.pos = pos_cpy
    if solver._assign(row, col, val):
        if solver._solve_with_cp():
            self.board = solver.board
            self.pos = solver.pos
            return True
```

这段代码每个回溯分支产生以下开销：

1. `copy.deepcopy(self.board)` — 复制整个 N×N 的 `list[list[int]]`
2. `copy.deepcopy(self.pos)` — 复制整个 N×N 的 `list[list[int]]`
3. `type(self)(board_cpy)` — 重新调用构造器，重新初始化所有格子

对于一个 9×9 标准数独（81 格），假设初始有 30 个已填格子，剩余 51 个空格子，最坏情况下回溯树可能有数千个节点。每次深拷贝 81 个 int 的嵌套列表虽然不是不可接受的，但：

- 随着棋盘尺寸增大（16×16、25×25），开销会以 O(N²) 增长
- 每个节点还创建了一个新求解器对象（构造器再次遍历所有格子）
- 更复杂的变体数独（如杀手数独）可能携带额外的状态（cage 和、区域约束等），拷贝成本会更高

## 改进方案

使用**撤销栈**模式。核心思想：每次修改状态时，将旧值压入栈中；回溯时从栈中弹出旧值恢复。不再拷贝整个棋盘。

### 撤销记录

```python
from dataclasses import dataclass

@dataclass
class StateChange:
    row: int
    col: int
    old_mask: int      # pos 的旧掩码
    old_value: int     # board 的旧值

class NumberPuzzleSolver:
    def __init__(self, board, constraints):
        self.board = board
        self.pos = ...
        self._undo_stack: list[list[StateChange]] = []  # 每个分支一层

    def _push_state(self):
        """开始一个新的回溯分支——推入一个新的空层"""
        self._undo_stack.append([])

    def _record_change(self, row: int, col: int, old_mask: int, old_value: int):
        """记录一个格子的旧状态"""
        self._undo_stack[-1].append(StateChange(row, col, old_mask, old_value))

    def _pop_state(self):
        """回溯——恢复该分支所有修改过的格子"""
        for change in reversed(self._undo_stack[-1]):
            self.pos[change.row][change.col] = change.old_mask
            self.board[change.row][change.col] = change.old_value
        self._undo_stack.pop()
```

### 修改 `_assign` 和 `_eliminate`

这两个方法在修改 `pos[r][c]` 或 `board[r][c]` 之前，先记录旧值：

```python
def _eliminate(self, row: int, col: int, val: int) -> bool:
    bit = 1 << (val - 1)
    if (self.pos[row][col] & bit) == 0:
        return True

    # 记录修改前的状态
    self._record_change(row, col, self.pos[row][col], self.board[row][col])

    self.pos[row][col] &= ~bit
    if self.pos[row][col] == 0:
        return False
    if self._count_bits(self.pos[row][col]) == 1:
        d2 = next(self._mask_to_values(self.pos[row][col]))
        self.board[row][col] = d2
        for r, c in self._get_peers(row, col):
            if not self._eliminate(r, c, d2):
                return False
    return True
```

关键点：修改前的状态记录一次即可。`_record_change` 对同一个 `(row, col)` 在同一分支内多次调用时，应当只保留**第一次**的记录（因为我们需要的是分支开始时的原始值）：

```python
def _record_change(self, row: int, col: int, old_mask: int, old_value: int):
    current_layer = self._undo_stack[-1]
    # 同一个格子在当前分支只记录一次（保留最早的状态）
    for c in current_layer:
        if c.row == row and c.col == col:
            return
    current_layer.append(StateChange(row, col, old_mask, old_value))
```

### 改造后的回溯主循环

```python
def _solve_with_cp(self) -> bool:
    if not self._propagate():
        return False

    cell = self._find_min_cell()
    if cell is None:
        return True  # 所有格子已填充

    row, col = cell
    for val in list(self._mask_to_values(self.pos[row][col])):
        self._push_state()  # 标记新分支

        if self._assign(row, col, val):
            if self._solve_with_cp():
                # 注意：解已写入 self.board/self.pos，不需要额外拷贝
                return True

        self._pop_state()  # 回溯：恢复该分支所有修改

    return False
```

注意改进后的代码不再需要 `copy.deepcopy`，不再创建新的 solver 对象，不再重新初始化。回溯只是简单地恢复被修改过的格子的旧值。

## 性能对比

| 方案 | 每次分支成本 | 9×9 空棋盘最快情况 | 16×16 空棋盘最快情况 |
|------|-------------|--------------------|-------------------------------|
| 深拷贝 | copy 81 个 int × 2 + 构造器 | copy 81 × 2 × 分支数 | copy 256 × 2 × 分支数 |
| 撤销栈 | 记录修改过的格子（通常 < 20） | 记录 ~10 个格子 × 分支数 | 记录 ~20 个格子 × 分支数 |

对于大的棋盘和深回溯树，撤销栈可节省数倍到数十倍的内存分配。

## 预期收益

1. 回溯分支的创建和销毁接近零成本（只分配几个 `StateChange` 对象）
2. 内存使用显著降低，特别是大棋盘场景
3. 求解速度提升（减少了大量内存分配和 GC 压力）
4. 容易扩展：新约束增加新的状态字段时，只需扩展 `StateChange`

## 注意事项

- `_propagate()` 中的修改也需要被记录（通过 `_assign` 和 `_eliminate` 间接记录），因此 `_propagate` 不需要特殊处理
- `_push_state()` 必须在 `_assign` 之前调用，确保后续的 `_record_change` 有对应的层
- 如果在同一分支内多次 `_push_state()`（嵌套），每次回溯 `_pop_state()` 只恢复该层独有的修改。实际上回溯是线性的（每次只尝试一个分支），所以只需要一层栈
- 需要小心 `_record_change` 的幂等性（同一格子在同一分支只记录一次原始值），否则恢复时可能覆盖为中间值
