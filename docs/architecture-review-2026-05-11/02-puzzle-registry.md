# 谜题类型注册中心

## 现状问题

当前添加一个新的谜题类型需要触及多个位置：

1. `app/services/` 下新建 solver 文件（如 `killer_sudoku_solver.py`）
2. `app/models/` 下新建请求/响应模型文件
3. `app/models/__init__.py` 中增加导出
4. `app/services/__init__.py` 中增加导出
5. `app/api/routes/` 下新建路由文件（如 `killer_sudoku.py`）
6. `app/main.py` 中 `include_router`

这些步骤中，第 3-6 步是纯粹的样板代码，每次重复且容易遗漏。随着 roadmap 上变体数独和其他填数谜题的增加（保守估计 10+ 种），这套流程会变得不可维护。

另外，前端无法通过 API 发现后端支持哪些谜题类型——必须通过文档或约定来知道端点路径 `/api/sudoku/solve` 是否存在。

## 改进方案

建立一个全局的谜题注册中心（registry），每个谜题类型在注册时声明其元信息、solver 类、请求模型。路由层变成通用的 thin layer，根据注册信息动态分发。

### 注册中心设计

```python
# app/registry.py

from dataclasses import dataclass, field
from typing import Type, Callable, Any

@dataclass
class PuzzleType:
    type_id: str                          # 唯一标识，如 "sudoku", "diagonal-sudoku"
    name: str                             # 显示名称，如 "数独"
    description: str                      # 简要说明
    solver_class: Type                    # 求解器类
    request_model: Type                   # Pydantic 请求模型
    response_model: Type                  # Pydantic 响应模型
    default_params: dict = field(default_factory=dict)  # 默认参数
    param_schema: dict | None = None      # JSON Schema 描述参数，供前端动态表单

class PuzzleRegistry:
    _types: dict[str, PuzzleType] = {}

    @classmethod
    def register(cls, puzzle_type: PuzzleType) -> None:
        if puzzle_type.type_id in cls._types:
            raise ValueError(f"谜题类型 {puzzle_type.type_id} 已注册")
        cls._types[puzzle_type.type_id] = puzzle_type

    @classmethod
    def get(cls, type_id: str) -> PuzzleType:
        if type_id not in cls._types:
            raise KeyError(f"未知的谜题类型: {type_id}")
        return cls._types[type_id]

    @classmethod
    def list_types(cls) -> list[dict]:
        return [
            {
                "type_id": t.type_id,
                "name": t.name,
                "description": t.description,
                "params": t.param_schema,
            }
            for t in cls._types.values()
        ]
```

### 注册示例

```python
# app/puzzles/sudoku.py
from app.registry import PuzzleRegistry, PuzzleType
from app.services import SudokuSolver
from app.models import SolveSudokuRequest, SolveSudokuResponse

PuzzleRegistry.register(PuzzleType(
    type_id="sudoku",
    name="数独",
    description="标准数独，支持自定义宫格形状",
    solver_class=SudokuSolver,
    request_model=SolveSudokuRequest,
    response_model=SolveSudokuResponse,
    default_params={"block_shape": (3, 3)},
    param_schema={
        "block_shape": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
            "default": [3, 3],
            "description": "宫格的行数和列数",
        }
    },
))
```

### 统一的路由层

```python
# app/api/routes/puzzle.py
from fastapi import APIRouter, HTTPException
from app.registry import PuzzleRegistry

router = APIRouter(prefix="/puzzle", tags=["谜题求解"])

@router.get("/types")
async def list_puzzle_types():
    """返回所有支持的谜题类型及参数说明"""
    return {"types": PuzzleRegistry.list_types()}

@router.post("/{type_id}/solve")
async def solve_puzzle(type_id: str, request: dict):
    puzzle_type = PuzzleRegistry.get(type_id)
    # 用注册的 request_model 校验
    req = puzzle_type.request_model(**request)
    solver = puzzle_type.solver_class(req.board, **req.model_dump(exclude={"board"}))
    solution = solver.solve()
    return puzzle_type.response_model(
        success=solution is not None,
        solution=solution,
        message="求解成功" if solution else "无解",
    )

@router.post("/{type_id}/validate")
async def validate_puzzle(type_id: str, request: dict):
    puzzle_type = PuzzleRegistry.get(type_id)
    req = puzzle_type.request_model(**request)
    return puzzle_type.solver_class.validate_board(req.board, **req.model_dump(exclude={"board"}))
```

### 前端发现流程

```
GET /api/puzzle/types
→
{
  "types": [
    {
      "type_id": "sudoku",
      "name": "数独",
      "description": "标准数独，支持自定义宫格形状",
      "params": {
        "block_shape": {
          "type": "array", "items": {"type": "integer"},
          "default": [3, 3]
        }
      }
    },
    {
      "type_id": "diagonal-sudoku",
      "name": "对角线数独",
      ...
    }
  ]
}
```

前端可以据此动态渲染谜题选择 UI 和参数表单，无需修改后端即可添加新谜题类型。

## 预期收益

1. **添加新谜题类型只需 2 步**：写 solver/constraint，写注册代码。不再需要动路由层、main.py、`__init__.py` 等
2. **API 自描述**：前端可以通过 `/api/puzzle/types` 发现能力，不需要硬编码端点路径
3. **注册中心即文档**：所有支持的类型及参数一目了然
4. **易于做 A/B 或灰度**：registry 可以扩展为支持 enable/disable 开关

## 注意事项

- 注册代码需要在应用启动时执行。可以在 `app/puzzles/__init__.py` 中集中 import 所有注册模块，然后在 `main.py` 中 import 该包
- 如果使用通用请求模型（参见「统一模型层」改进），路由的 request 校验会更简洁
- 考虑为 solver 类提供工厂函数而非直接存储类，以支持更复杂的构造逻辑
