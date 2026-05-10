# 资源保护：尺寸限制、超时与深度控制

## 现状问题

当前服务对恶意或意外的资源滥用没有任何防护。后端是一个无状态纯计算服务，每个请求直接消耗 CPU 和内存。

具体的攻击面：

1. **无棋盘尺寸上限**：用户可以发送 500×500 的空棋盘请求。`__init__` 会创建一个 500×500 的 `pos` 掩码数组（250,000 个 int），然后尝试求解——内存和计算量巨大
2. **无超时机制**：一个困难的（或故意构造为需要大量回溯的）15×15 数独可能导致求解器运行数分钟甚至数小时。FastAPI 的同步端点会阻塞事件循环
3. **无递归/回溯深度限制**：虽然 Python 有默认递归深度限制（~1000），但 `_solve_with_cp` 的递归深度等于需要回溯的次数，设计糟糕的谜题可能触发 RecursionError
4. **无请求频率限制**：恶意调用者可以并发发送大量求解请求，耗尽服务器资源

## 改进方案

分三层防护：请求准入 → 运行时监控 → 资源隔离。

### 第一层：请求准入（FastAPI 中间件 / Pydantic 校验器）

在请求进入业务逻辑之前，拒绝明显不合理的请求：

```python
# app/validators/board_limits.py
MAX_BOARD_SIZE = 25       # 最大边长
MAX_EMPTY_CELLS = 200     # 最大空格数
MAX_BOARD_SIZE_BYTES = 1024 * 1024  # 请求体最大 1MB（FastAPI 层面控制）

def validate_request_size(board: list[list[int]]) -> None:
    n = len(board)
    if n > MAX_BOARD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"棋盘边长不能超过 {MAX_BOARD_SIZE}，当前: {n}",
        )
    # 可选：更精细的复杂度估算（空格数量）
    empty_count = sum(1 for row in board for cell in row if cell == 0)
    if empty_count > MAX_EMPTY_CELLS:
        raise HTTPException(
            status_code=400,
            detail=f"空格数不能超过 {MAX_EMPTY_CELLS}，当前: {empty_count}",
        )
```

这些限制应当在 FastAPI 依赖注入中统一应用，或在通用的请求模型中作为 validator：

```python
class SolvePuzzleRequest(BaseModel):
    board: list[list[int]]
    ...

    @field_validator("board")
    @classmethod
    def check_board_size(cls, board):
        n = len(board)
        if n > MAX_BOARD_SIZE:
            raise ValueError(f"棋盘边长不能超过 {MAX_BOARD_SIZE}")
        return board
```

### 第二层：求解超时

对求解器设置硬超时。由于求解器是同步 CPU 密集型代码，需要使用线程 + 超时，或将求解器改造为支持协作式中断：

**方案 A：线程 + 超时（最简单）**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

SOLVER_TIMEOUT_SECONDS = 30

@router.post("/{type_id}/solve")
async def solve_puzzle(type_id: str, request: SolvePuzzleRequest):
    puzzle_type = PuzzleRegistry.get(type_id)
    solver = puzzle_type.solver_class(request.board, **request.params)

    loop = asyncio.get_event_loop()
    try:
        solution = await asyncio.wait_for(
            loop.run_in_executor(_solver_executor, solver.solve),
            timeout=SOLVER_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail=f"求解超时（>{SOLVER_TIMEOUT_SECONDS}秒），请简化谜题或尝试更小的棋盘",
        )

    return SolvePuzzleResponse(...)

# 线程池执行器（全局复用）
_solver_executor = ThreadPoolExecutor(max_workers=4)
```

**方案 B：协作式中断（更精细）**

在求解器内部，每次 `_propagate()` 或每 N 次循环后检查是否超时：

```python
import time

class PuzzleSolver:
    def __init__(self, ...):
        self._start_time = time.perf_counter()
        self._timeout = 30.0

    def _check_timeout(self):
        if time.perf_counter() - self._start_time > self._timeout:
            raise TimeoutError("求解超时")

    def _solve_with_cp(self) -> bool:
        self._check_timeout()  # 每次递归入口检查
        ...
```

方案 B 更干净但需要改动求解器内部循环。建议先用方案 A，后续迭代到方案 B。

### 第三层：请求频率限制

在 FastAPI 层或反向代理层（如 nginx）设置速率限制：

```python
# 使用 slowapi 或自定义中间件
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{type_id}/solve")
@limiter.limit("10/minute")  # 每个 IP 每分钟最多 10 次求解请求
async def solve_puzzle(...):
    ...
```

## 推荐的默认限制值

| 参数 | 建议值 | 理由 |
|------|--------|------|
| 最大棋盘边长 | 25 | 25×25 数独在标准参数下已在回溯求解的极限 |
| 最大空格数 | 200 | 防止高度未填充的棋盘消耗过多搜索 |
| 求解超时 | 30s | 对于 web API 合理的等待上限 |
| 速率限制 | 10 req/min/IP | 防止并发攻击，但允许正常使用 |
| 线程池大小 | 4 | 限制并发 CPU 密集型任务数 |

## 预期收益

1. 消除 DoS 攻击面
2. 为服务上线生产提供基本的安全保障
3. 限制值为可配置的，可以根据实际硬件和需求调整

## 注意事项

- 这些限制值应当通过配置文件或环境变量控制，而非硬编码，以方便不同部署环境调整
- 超时后的线程实际上不会被杀死（Python 限制），需要在超时时记录日志并考虑线程泄漏问题。更好的长期方案是方案 B（协作式中断）
- 速率限制在开发阶段可能妨碍调试，可以在本地环境默认关闭
