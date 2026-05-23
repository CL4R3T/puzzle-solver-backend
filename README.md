# 谜题求解后端

基于 FastAPI 的通用谜题求解 API，支持数独、杀手数独等多种谜题类型。

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看 Swagger 交互式文档。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/puzzle/types` | 列出所有支持的谜题类型 |
| POST | `/api/puzzle/{type_id}/solve` | 求解谜题 |
| POST | `/api/puzzle/{type_id}/validate` | 校验棋盘合法性 |

## 棋盘数据约定

- `board` 为二维数组 `list[list[int]]`，必须正方形
- 每个格子取值 0~N（N = 边长），**0 表示空格**
- 行、列索引从 0 开始

---

## GET /api/puzzle/types

列出所有已注册的谜题类型及参数说明。

**响应示例：**

```json
{
  "types": [
    {
      "type_id": "sudoku",
      "name": "数独",
      "description": "标准数独，支持自定义宫格形状",
      "params": {
        "box_shape": {
          "type": "array",
          "items": {"type": "integer"},
          "minItems": 2, "maxItems": 2,
          "default": [3, 3],
          "description": "宫格的行数和列数"
        }
      }
    },
    {
      "type_id": "killer-sudoku",
      "name": "杀手数独",
      "description": "标准数独规则 + 虚线框内数字不重复且和等于目标值",
      "params": {
        "cages": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "cells": {
                "type": "array",
                "items": {
                  "type": "array",
                  "items": {"type": "integer"},
                  "minItems": 2, "maxItems": 2
                }
              },
              "sum": {"type": "integer"}
            },
            "required": ["cells", "sum"]
          },
          "description": "笼子列表，每个笼子包含格子和目标总和"
        },
        "box_shape": {
          "type": "array",
          "items": {"type": "integer"},
          "minItems": 2, "maxItems": 2,
          "default": [3, 3],
          "description": "宫格的行数和列数，默认 3x3"
        }
      }
    }
  ]
}
```

---

## POST /api/puzzle/{type_id}/solve

求解指定类型的谜题。`type_id` 在 URL 中指定（如 `sudoku`、`killer-sudoku`）。

### 标准数独

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/sudoku/solve \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [5, 3, 0, 0, 7, 0, 0, 0, 0],
      [6, 0, 0, 1, 9, 5, 0, 0, 0],
      [0, 9, 8, 0, 0, 0, 0, 6, 0],
      [8, 0, 0, 0, 6, 0, 0, 0, 3],
      [4, 0, 0, 8, 0, 3, 0, 0, 1],
      [7, 0, 0, 0, 2, 0, 0, 0, 6],
      [0, 6, 0, 0, 0, 0, 2, 8, 0],
      [0, 0, 0, 4, 1, 9, 0, 0, 5],
      [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
  }'
```

**成功响应：**

```json
{
  "success": true,
  "solution": [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9]
  ],
  "message": "求解成功",
  "solve_time_ms": 1.23
}
```

**无解 / 棋盘不合法：**

```json
{
  "success": false,
  "solution": null,
  "message": "第0行有重复值5",
  "solve_time_ms": null
}
```

### 自定义宫格大小

请求体中传入 `box_shape` 参数，例如 6x6 数独（宫格 2x3）：

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/sudoku/solve \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [1, 0, 3, 0, 5, 6],
      [0, 0, 6, 1, 0, 3],
      [2, 3, 0, 5, 0, 0],
      [5, 0, 1, 0, 3, 0],
      [3, 4, 0, 0, 1, 2],
      [0, 0, 2, 0, 0, 5]
    ],
    "params": {
      "box_shape": [2, 3]
    }
  }'
```

### 杀手数独

杀手数独在标准规则（行、列、宫不重复）基础上，增加了"笼子"约束。每个笼子内数字不重复且求和等于目标值。

**4x4 杀手数独示例：**

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/killer-sudoku/solve \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [1, 0, 0, 4],
      [0, 4, 0, 0],
      [2, 0, 0, 0],
      [0, 0, 0, 1]
    ],
    "params": {
      "box_shape": [2, 2],
      "cages": [
        {"cells": [[0, 1], [0, 2]], "sum": 5}
      ]
    }
  }'
```

**响应：**

```json
{
  "success": true,
  "solution": [
    [1, 2, 3, 4],
    [3, 4, 1, 2],
    [2, 1, 4, 3],
    [4, 3, 2, 1]
  ],
  "message": "求解成功",
  "solve_time_ms": 0.45
}
```

**9x9 杀手数独示例（多个笼子）：**

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/killer-sudoku/solve \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0, 0, 0]
    ],
    "params": {
      "cages": [
        {"cells": [[0, 0], [0, 1], [1, 0]], "sum": 15},
        {"cells": [[0, 2], [0, 3], [1, 2]], "sum": 13},
        {"cells": [[0, 4], [0, 5]], "sum": 11},
        {"cells": [[0, 6], [0, 7], [1, 7]], "sum": 20},
        {"cells": [[0, 8], [1, 8]], "sum": 10},
        {"cells": [[1, 1], [2, 0], [2, 1]], "sum": 18}
      ]
    }
  }'
```

> 9x9 默认 `box_shape` 为 `[3, 3]`，可省略。

---

## POST /api/puzzle/{type_id}/validate

校验棋盘在当前谜题类型的规则下是否合法。请求体格式与 solve 相同。

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/sudoku/validate \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [5, 3, 0, 0, 7, 0, 0, 0, 0],
      [6, 0, 0, 1, 9, 5, 0, 0, 0]
    ]
  }'
```

**响应：**

```json
{
  "valid": true,
  "unique_solution": null,
  "message": "棋盘合法"
}
```

### 杀手数独校验

```bash
curl -X POST http://127.0.0.1:8000/api/puzzle/killer-sudoku/validate \
  -H "Content-Type: application/json" \
  -d '{
    "board": [
      [1, 2, 3, 4],
      [3, 4, 1, 2],
      [2, 1, 4, 3],
      [4, 3, 2, 1]
    ],
    "params": {
      "box_shape": [2, 2],
      "cages": [
        {"cells": [[0, 0], [0, 1]], "sum": 3}
      ]
    }
  }'
```

---

## 架构

```
请求 → FastAPI 路由 → PuzzleRegistry.get(type_id)
                    → solver = PuzzleType.solver_class(board, **params)
                    → solver.validate_board()  → 校验
                    → solver.solve()           → 约束传播 + 回溯
                    → SolvePuzzleResponse
```

- **约束层** (`app/constraints/`) — 每个约束实现自己的 `propagate(board, pos)` 消元逻辑
- **求解引擎** (`app/services/number_puzzle_solver.py`) — 固定点迭代调度所有约束，配合回溯搜索
- **注册中心** (`app/registry.py`) — 新谜题类型注册后自动出现在 API 和文档中

## 扩展

在 `app/puzzles/` 下新建注册文件，在 `app/constraints/` 下添加新约束类，在 `app/services/` 下组合求解器即可。无需修改路由或引擎。

示例：添加对角线数独

```python
# app/services/diagonal_sudoku_solver.py
class DiagonalSudokuSolver(NumberPuzzleSolver):
    def __init__(self, board, box_shape=(3, 3)):
        n = len(board)
        constraints = [
            RowConstraint(n),
            ColumnConstraint(n),
            BoxConstraint(n, box_shape),
            DiagonalConstraint(n),
        ]
        super().__init__(board, constraints)
```

```python
# app/puzzles/diagonal_sudoku.py
PuzzleRegistry.register(PuzzleType(
    type_id="diagonal-sudoku",
    name="对角线数独",
    description="标准数独 + 两条对角线不重复",
    solver_class=DiagonalSudokuSolver,
    ...
))
```
