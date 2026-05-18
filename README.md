# 谜题求解后端

基于 FastAPI 的通用谜题求解 API，支持数独、杀手数独等多种谜题类型。

## 运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看 Swagger 文档。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/puzzle/types` | 列出所有支持的谜题类型 |
| POST | `/api/puzzle/{type_id}/solve` | 求解谜题 |
| POST | `/api/puzzle/{type_id}/validate` | 校验棋盘合法性 |

### GET /api/puzzle/types

**响应：**
```json
{
  "types": [
    {
      "type_id": "sudoku",
      "name": "数独",
      "description": "标准数独，支持自定义宫格形状",
      "params": {
        "block_shape": {
          "type": "array",
          "items": {"type": "integer"},
          "minItems": 2,
          "maxItems": 2,
          "default": [3, 3],
          "description": "宫格的行数和列数"
        }
      }
    }
  ]
}
```

### POST /api/puzzle/{type_id}/solve

**请求体：** `SolvePuzzleRequest`

```json
{
  "puzzle_type": "sudoku",
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
  ],
  "params": {
    "block_shape": [3, 3]
  }
}
```

**成功响应：** `SolvePuzzleResponse`

```json
{
  "success": true,
  "solution": [[5, 3, 4, ...], ...],
  "message": "求解成功",
  "solve_time_ms": 1.23
}
```

**无解响应：**

```json
{
  "success": false,
  "solution": null,
  "message": "无解",
  "solve_time_ms": 15.8
}
```

### POST /api/puzzle/{type_id}/validate

**请求体：** 同 solve（`puzzle_type` + `board` + `params`）

**响应：** `ValidationResponse`

```json
{
  "valid": true,
  "message": "棋盘合法"
}
```

## 棋盘数据约定

- `board` 为二维数组 `list[list[int]]`，必须正方形
- 每个格子取值 0~N（N = 边长），**0 表示空格**
- 行、列索引从 0 开始

## 扩展谜题类型

在 `app/puzzles/` 下新建注册文件，在 `app/constraints/` 下添加新约束，在 `app/services/` 下组合求解器即可。新类型会自动出现在 `/api/puzzle/types` 列表中，无需修改路由或模型。
