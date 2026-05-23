# 约束抽象化：以组合替代继承

## 现状问题

当前求解器采用单一继承链：`NumberPuzzleSolver` → `SudokuSolver`。

`NumberPuzzleSolver` 硬编码了行约束和列约束——`_get_peers()` 返回同行同列的格子，`_propagate()` 在行和列上执行 hidden single 检测。

`SudokuSolver` 继承后，为加入宫格约束，不得不**整体重写** `_propagate()` 和 `validate_board()`。虽然这两个方法与父类有 80% 的代码重叠，但无法通过 `super()` 调用复用——因为父类的循环结构不包含宫格维度，子类无法在中间"插入"一段宫格处理逻辑。最终结果是 ~50 行几乎完全相同的代码被复制粘贴。

当一个变体数独需要加入对角线约束时，这个模式会进一步恶化：

```
NumberPuzzleSolver
  └── SudokuSolver              ← 重写 _propagate()
        ├── DiagonalSudokuSolver ← 再次重写 _propagate()，添加对角线 hidden single
        ├── KillerSudokuSolver   ← 再次重写 _propagate()，添加 cage 约束
        └── ThermoSudokuSolver   ← 再次重写……
```

每一种新变体都要求你完整复制传播逻辑，然后附加新的约束处理。此外，多条继承线（比如同时支持对角线 + 宫格）会变得几乎不可能。

## 改进方案

将「约束」从求解器中解耦，变为一等公民。核心思想是：**求解器不关心具体的约束类型，它只在一个约束列表上执行通用算法**。

### 约束协议

每个约束实现以下接口：

```python
class Constraint(Protocol):
    n: int  # 棋盘边长

    def get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        """返回 (row, col) 在此约束下关联的所有格子"""
        ...

    def get_units(self) -> list[list[tuple[int, int]]]:
        """返回此约束下的所有'单元'，每个单元为一个格子列表，
           用于检测 hidden single"""
        ...

    def validate(self, board: list[list[int]]) -> ValidationResult:
        """在此约束下校验棋盘是否合法"""
        ...
```

### 内置约束实现

**行约束**：`get_peers` 返回同一行的所有格子。`get_units` 返回每行作为一个单元。

**列约束**：`get_peers` 返回同一列的所有格子。`get_units` 返回每列作为一个单元。

**宫格约束**：`get_peers` 返回同一 box 内的所有格子。`get_units` 返回每个 box 作为一个单元。接受 `block_shape` 参数。

**对角线约束**：`get_peers` 如果格子在主对角线上则返回主对角线所有格子，如果在副对角线上则返回副对角线。`get_units` 返回两条对角线作为两个单元。

### 统一的求解器

```python
class NumberPuzzleSolver:
    def __init__(self, board: list[list[int]], constraints: list[Constraint]):
        self.board = board
        self.n = len(board)
        self.constraints = constraints
        # 合并所有约束的 peer（去重）
        self._peer_map = self._build_peer_map()
        # 收集所有约束的 unit
        self._all_units = [u for c in constraints for u in c.get_units()]

    def _get_peers(self, row: int, col: int) -> list[tuple[int, int]]:
        return self._peer_map[(row, col)]

    def _propagate(self) -> bool:
        # 对所有 unit 执行裸单 + hidden single，与约束类型无关
        ...

    def _solve_with_cp(self) -> bool:
        # 回溯逻辑，与约束类型无关
        ...
```

### 使用示例

```python
# 标准数独
constraints = [
    RowConstraint(n=9),
    ColumnConstraint(n=9),
    BoxConstraint(n=9, block_shape=(3, 3)),
]

# 对角线数独
constraints = [
    RowConstraint(n=9),
    ColumnConstraint(n=9),
    BoxConstraint(n=9, block_shape=(3, 3)),
    DiagonalConstraint(n=9),
]

# 仅行列约束的拉丁方
constraints = [
    RowConstraint(n=6),
    ColumnConstraint(n=6),
]
```

### 扩展新约束

添加全新约束类型时，只需实现 `Constraint` 接口的三个方法，不修改求解器一行代码。比如杀手数独的 cage 约束：

```python
class KillerCageConstraint:
    def __init__(self, cages: list[Cage]):
        self.cages = cages

    def get_peers(self, row, col):
        # 返回同 cage 的格子
        ...

    def get_units(self):
        # 返回每个 cage 作为一个 unit
        ...

    def validate(self, board):
        # 校验每个 cage 的和是否等于目标值
        ...
```

## 预期收益

1. **新变体成本极低**：引入新数独变体 = 实现 1 个约束类，而非重写整个求解器
2. **约束可组合**：对角线+宫格同时存在只需要把两个约束都加入列表
3. **求解器可单独测试**：可以用 mock constraint 验证求解器本身的行为
4. **代码去重**：传播逻辑只有一份，维护点唯一

## 注意事项

- `get_peers` 的去重由求解器负责（不同约束可能返回同一个 peer）
- 约束的顺序不应该影响求解结果，但可能影响性能。求解器内部可以对 unit 做排序优化
- 部分高级约束（如 killer cage sum）需要自定义传播逻辑，`Constraint` 接口需要留一个可选的 `propagate(state) → bool` 钩子
