# 数独求解后端

基于 FastAPI 的数独求解 API 服务。

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── api/
│   │   └── routes/
│   │       └── sudoku.py    # 数独相关 API
│   ├── models/
│   │   └── sudoku.py        # 请求/响应数据模型
│   └── services/
│       └── sudoku_solver.py # 求解逻辑（待实现）
├── requirements.txt
└── README.md
```

## 数据类型约定

### 数独棋盘 `board`

- 9x9 二维数组 `list[list[int]]`
- 每个格子取值 0–9，**0 表示空格**（待填）
- 行、列索引从 0 开始

## API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sudoku/solve` | 求解数独 |
| POST | `/api/sudoku/validate` | 校验数独合法性 |

### POST /api/sudoku/solve

**请求体：**
```json
{
  "board": [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    ...
  ]
}
```

**成功响应：**
```json
{
  "success": true,
  "solution": [[...], ...],
  "message": "求解成功"
}
```

**无解响应：**
```json
{
  "success": false,
  "solution": null,
  "message": "无解"
}
```

### POST /api/sudoku/validate

**请求体：** 同上（`board`）

**响应：**
```json
{
  "valid": true,
  "message": "校验通过"
}
```

## 运行

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问 http://127.0.0.1:8000/docs 查看 Swagger 文档。
