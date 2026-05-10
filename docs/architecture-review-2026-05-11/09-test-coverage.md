# 测试体系完善

## 现状问题

当前测试仅包含 4 个测试函数，全部放在一个文件 `tests/test_sudoku_solver.py` 中，且全部是 solver 层的单元测试：

| 测试 | 覆盖内容 | 缺失 |
|------|---------|------|
| `test_solve_standard` | 1 个标准 9×9 数独的 happy path | 无解、多解 |
| `test_solve_custom_block` | 1 个 6×6 矩形 block 的 happy path | 其他 block shape 组合 |
| `test_validate_rejects_bad` | 1 个 2×2 故意重复的拒绝 case | 其他类型的非法输入 |
| `test_solver_inheritance` | 验证 SudokuSolver 是子类 | 并非功能测试 |

缺失的测试维度：

- **API 层**：完全没有 FastAPI TestClient 测试，路由逻辑未经验证
- **无解场景**：没有测试求解器正确处理不可解棋盘
- **多解场景**：没有测试棋盘有多个解的情况
- **边界值**：空棋盘、满棋盘、1×1 棋盘、最大合法尺寸
- **非法输入**：非方阵、越界值、非整数类型、超大棋盘
- **约束传播正确性**：没有对 `_eliminate`、`_propagate`、`_find_hidden_single` 的精细单元测试
- **性能回归**：没有性能基准
- **`NumberPuzzleSolver` 基类**：4 个测试全部用 `SudokuSolver`，基类本身没有独立测试

## 改进方案

### 测试分层

```
tests/
├── conftest.py                    # 共享 fixture（标准棋盘、求解器等）
├── unit/
│   ├── test_number_puzzle_solver.py   # 基类求解器单元测试
│   ├── test_sudoku_solver.py          # 数独求解器单元测试（细化现有测试）
│   ├── test_constraints.py            # 各约束类的测试（行/列/宫/对角线...）
│   └── test_models.py                 # Pydantic 模型校验测试
├── integration/
│   ├── test_api_solve.py              # POST /solve 端点的集成测试
│   ├── test_api_validate.py           # POST /validate 端点的集成测试
│   └── test_api_puzzle_types.py       # 谜题类型注册/发现端点测试
└── performance/
    └── test_solver_benchmark.py       # 性能基准测试
```

### 单元测试补充

**对 `NumberPuzzleSolver` 的测试**（当前为 0）：

```python
class TestNumberPuzzleSolver:
    def test_solve_2x2_latin_square(self):
        """2×2 拉丁方应正确求解"""
        board = [[1, 0], [0, 1]]
        solver = NumberPuzzleSolver(board)
        assert solver.solve() == [[1, 2], [2, 1]]

    def test_unsolvable_board(self):
        """检测无解棋盘（存在逻辑矛盾）"""
        board = [[1, 1], [0, 0]]  # 同一行两个 1
        solver = NumberPuzzleSolver(board)
        assert solver.solve() is None

    def test_empty_board_has_solution(self):
        """空棋盘应当有解（拉丁方）"""
        solver = NumberPuzzleSolver([[0, 0], [0, 0]])
        assert solver.solve() is not None

    def test_full_valid_board(self):
        """已完整且合法的棋盘应直接返回"""
        board = [[1, 2], [2, 1]]
        solver = NumberPuzzleSolver(board)
        assert solver.solve() == board

    def test_non_square_board_raises(self):
        """非方阵应在构造时抛出"""
        with pytest.raises(ValueError, match="正方形"):
            NumberPuzzleSolver([[1, 2, 3], [4, 5, 6]])

    def test_out_of_range_value_raises(self):
        """越界值应在构造时抛出"""
        with pytest.raises(ValueError, match="格子值"):
            NumberPuzzleSolver([[0, 5], [0, 0]])  # n=2，不能有 5

    @pytest.mark.parametrize("n", [4, 9, 16])
    def test_various_sizes(self, n):
        """各种尺寸的空棋盘均应有解"""
        board = [[0] * n for _ in range(n)]
        solver = NumberPuzzleSolver(board)
        assert solver.solve() is not None
```

**对约束传播的精细测试**：

```python
class TestConstraintPropagation:
    def test_naked_single_triggers_assign(self):
        """当一格只剩一个候选值时，应自动赋值并传播"""
        board = [
            [0, 0, 0],
            [2, 3, 0],  # 已知
            [0, 0, 0],
        ]
        # 2×2 拉丁方，(0,0) 所在行列有 2,3，所以只剩 1
        solver = NumberPuzzleSolver(board)
        assert solver._count_bits(solver.pos[0][0]) == 1

    def test_hidden_single_detected(self):
        """检测行中的隐藏单"""
        # 构造场景：某行中数字 3 只能出现在一格
        ...
```

### 集成测试

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestSolveAPI:
    def test_solve_valid_sudoku(self):
        response = client.post("/api/puzzle/sudoku/solve", json={
            "board": [
                [5, 3, 0, 0, 7, 0, 0, 0, 0],
                [6, 0, 0, 1, 9, 5, 0, 0, 0],
                [0, 9, 8, 0, 0, 0, 0, 6, 0],
                [8, 0, 0, 0, 6, 0, 0, 0, 3],
                [4, 0, 0, 8, 0, 3, 0, 0, 1],
                [7, 0, 0, 0, 2, 0, 0, 0, 6],
                [0, 6, 0, 0, 0, 0, 2, 8, 0],
                [0, 0, 0, 4, 1, 9, 0, 0, 5],
                [0, 0, 0, 0, 8, 0, 0, 7, 9],
            ],
            "block_shape": [3, 3],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["solution"] is not None

    def test_solve_invalid_board_returns_400(self):
        response = client.post("/api/puzzle/sudoku/solve", json={
            "board": [[1, 1], [0, 0]],
            "block_shape": [1, 2],
        })
        assert response.status_code == 400

    def test_solve_nonexistent_type_returns_404(self):
        response = client.post("/api/puzzle/nonexistent/solve", json={
            "board": [[0]],
            "params": {},
        })
        assert response.status_code == 404
```

### 性能基准测试

```python
@pytest.mark.slow
class TestSolverPerformance:
    @pytest.mark.parametrize("n,block", [(9, (3,3)), (16, (4,4))])
    def test_solve_empty_board(self, n, block):
        """空棋盘求解的性能基准"""
        board = [[0] * n for _ in range(n)]
        solver = SudokuSolver(board, block_shape=block)
        start = time.perf_counter()
        solution = solver.solve()
        elapsed = time.perf_counter() - start
        assert solution is not None
        assert elapsed < 5.0  # 期望在 5 秒内完成

    def test_known_hard_sudoku(self):
        """一个已知的困难数独应在合理时间内解出"""
        # 选择一个公认的「世界最难数独」
        ...
```

### 测试配置

```python
# conftest.py
import pytest

# 标准测试用的数独棋盘 fixture
@pytest.fixture
def standard_board():
    return [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]

@pytest.fixture
def standard_solution():
    return [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]
```

## 预期收益

1. 重构安全网：有了足够覆盖的测试，前述各项架构改进可以放心进行
2. 回归防护：新增变体数独时不会意外破坏标准数独的求解
3. 性能可量化：基准测试让任何性能退化可被 CI 捕获

## 注意事项

- 性能测试用 `pytest.mark.slow` 标记，日常开发时跳过，CI 中运行
- API 集成测试需要将求解超时设置得足够长（或 mock solver）
- 约束传播的单元测试需要精心构造棋盘来触发特定的推理场景，这部分测试编写成本较高但价值也最高
