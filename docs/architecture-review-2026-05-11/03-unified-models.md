# 统一请求/响应模型

## 现状问题

当前模型层存在不必要的重复：

- `SolveNumberPuzzleRequest` 和 `SolveSudokuRequest` 是两个独立的 Pydantic 类，功能几乎相同。唯一的区别是 `SolveSudokuRequest` 多了一个 `block_shape: tuple[int, int]` 字段。
- `SolveNumberPuzzleResponse` 和 `SolveSudokuResponse` **完全**相同——三个一样的字段：`success`、`solution`、`message`。
- 两个 Request 类各自实现了自己的 `validate_board`，且与 services 层中 solver 的 `validate_board` 静态方法逻辑重复。

这会导致以下问题：

1. 每增加一个谜题类型，如果它有额外的参数（比如对角线数独的"对角线数量"、杀手数独的 cage 定义），就必须新建一对 Request/Response 类
2. 如果某天需要给所有响应增加一个公共字段（比如 `solve_time_ms`），需要修改 N 个 Response 类
3. 校验逻辑散落在 Pydantic 模型和 solver 中，修改时需要两边同步

## 改进方案

用**一个通用请求模型** + **可选的扩展参数字段** 来替代每种谜题类型一个 Request 类。

### 通用请求模型

```python
# app/models/request.py
from pydantic import BaseModel, Field
from typing import Any

class SolvePuzzleRequest(BaseModel):
    """通用谜题求解请求"""
    puzzle_type: str = Field(..., description="谜题类型标识，如 'sudoku'")
    board: list[list[int]] = Field(..., description="待求解的棋盘")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="谜题类型的额外参数，如 sudoku 的 block_shape",
    )
```

### 通用响应模型

```python
# app/models/response.py
from pydantic import BaseModel, Field

class SolvePuzzleResponse(BaseModel):
    """通用谜题求解响应"""
    success: bool = Field(..., description="是否求解成功")
    solution: list[list[int]] | None = Field(
        default=None,
        description="解出的棋盘，无解时为 null",
    )
    message: str = Field(default="", description="附加信息（如错误原因）")
    solve_time_ms: float | None = Field(
        default=None,
        description="求解耗时（毫秒）",
    )
    steps: list[dict] | None = Field(
        default=None,
        description="求解步骤（可选，用于展示推理过程）",
    )

class ValidationResponse(BaseModel):
    """通用棋盘校验响应"""
    valid: bool = Field(..., description="棋盘是否合法")
    unique_solution: bool | None = Field(
        default=None,
        description="是否有唯一解（仅当 valid=true 时有意义）",
    )
    message: str = Field(default="", description="校验说明")
```

### 校验逻辑的归属

从 Pydantic 模型中**完全移除**棋盘内容校验（行/列/宫的重复检查、值范围等）。Pydantic 层只做最基础的类型校验（`board` 是 `list[list[int]]`）。棋盘的语义校验全部归属 solver 层：

```python
# 路由中的使用方式
@router.post("/{type_id}/solve")
async def solve_puzzle(type_id: str, request: SolvePuzzleRequest):
    puzzle_type = PuzzleRegistry.get(type_id)
    solver = puzzle_type.solver_class(request.board, **request.params)

    # 先校验
    validation = solver.validate()
    if not validation.valid:
        return SolvePuzzleResponse(success=False, message=validation.message)

    # 再求解
    import time
    start = time.perf_counter()
    solution = solver.solve()
    elapsed = (time.perf_counter() - start) * 1000

    return SolvePuzzleResponse(
        success=solution is not None,
        solution=solution,
        message="求解成功" if solution else "无解",
        solve_time_ms=elapsed,
    )
```

### 参数 schema 的声明

谜题类型的额外参数通过注册中心声明的 `param_schema` 来描述（参见「谜题注册中心」改进），前端可以据此渲染动态表单。路由层不需要静态地知道每个谜题类型的字段。

### 迁移路径

1. 新建 `app/models/request.py` 和 `app/models/response.py`，定义通用模型
2. 保留现有 `SolveSudokuRequest` / `SolveSudokuResponse` 但标记为 deprecated，内部转为通用模型
3. 新增的谜题类型统一使用通用模型
4. 所有旧类型迁移完成后，删除旧模型文件

## 预期收益

1. **N 种谜题类型，1 对 Request/Response**，不再线性膨胀
2. 给所有端点增加公共字段（耗时、步骤等）只需改一个地方
3. 校验逻辑由 solver 统一负责，不再出现 Pydantic 和 solver 各校验一遍的情况
4. 前端可以使用统一的请求格式，仅改变 `puzzle_type` 和 `params`

## 注意事项

- `params` 是自由 dict，失去了 Pydantic 的字段级校验。弥补方案：solver 初始化时校验 params 的合法性并抛出明确的错误信息；也可以在注册中心提供 params 的 JSON Schema，用 `jsonschema` 库在路由层做前置校验
- 如果需要强制某些参数的类型安全（例如 Python SDK 调用），可以保留特定谜题类型的 typed request model 作为 `params` 的 typed 替代，但这属于锦上添花而非必须
