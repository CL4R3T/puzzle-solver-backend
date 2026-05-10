# 可观测性：日志、指标与追踪

## 现状问题

当前服务没有任何可观测性基础设施：

- **没有日志记录**：整个代码库中找不到一行 `logging` 或 `print` 调用。求解成功/失败、耗时、异常全部无声发生
- **没有指标暴露**：无法知道每天有多少求解请求、平均耗时多少、失败率多高
- **没有请求追踪**：如果一次求解超时或报错，没有足够信息可以复现问题（比如：用户传了什么棋盘？求解器在哪个阶段卡住了？）
- **异常信息不充分**：路由层的 `except Exception as e: raise HTTPException(500, f"服务器错误: {str(e)}")` 丢失了异常的 traceback 信息

## 改进方案

### 结构化日志

引入 `structlog` 做结构化日志，替代裸的 `print` 或不存在的日志。

```python
# app/logging_config.py
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),  # 开发环境友好输出
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger():
    return structlog.get_logger()
```

### 关键日志点

```python
# 路由层
logger = get_logger()

@router.post("/{type_id}/solve")
async def solve_puzzle(type_id: str, request: SolvePuzzleRequest):
    logger.info("求解请求", puzzle_type=type_id, board_size=len(request.board))

    try:
        solution = solver.solve()
        elapsed = ...
        if solution:
            logger.info("求解成功", puzzle_type=type_id,
                        board_size=len(request.board), solve_time_ms=elapsed)
        else:
            logger.warning("求解失败（无解）", puzzle_type=type_id,
                           board_size=len(request.board), solve_time_ms=elapsed)
    except TimeoutError:
        logger.error("求解超时", puzzle_type=type_id,
                     board_size=len(request.board))
        raise HTTPException(408, ...)
    except Exception:
        logger.exception("求解异常")  # 自动附带 traceback
        raise HTTPException(500, ...)
```

```python
# 求解器内部
class PuzzleSolver:
    def __init__(self, ...):
        self._logger = get_logger().bind(
            board_size=self.n,
            puzzle_type=type(self).__name__,
        )

    def _solve_with_cp(self) -> bool:
        self._backtrack_count += 1
        if self._backtrack_count % 1000 == 0:
            self._logger.debug("回溯进度", backtrack_count=self._backtrack_count,
                               remaining_empty=sum(1 for r in self.board for c in r if c == 0))
        ...
```

### 请求/响应日志中间件

```python
# app/middleware/logging.py
import time
import uuid
from fastapi import Request

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    logger = get_logger().bind(request_id=request_id)

    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000

    logger.info("请求完成",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                elapsed_ms=round(elapsed, 2))

    response.headers["X-Request-ID"] = request_id
    return response
```

### 关键指标

暴露 Prometheus 指标（通过 `prometheus-fastapi-instrumentator` 或手动埋点）：

```python
from prometheus_client import Counter, Histogram

solve_requests = Counter(
    "puzzle_solve_requests_total",
    "求解请求总数",
    ["puzzle_type", "status"],  # status: success / no_solution / timeout / error
)

solve_duration = Histogram(
    "puzzle_solve_duration_seconds",
    "求解耗时分布",
    ["puzzle_type", "board_size"],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
)

backtrack_count = Histogram(
    "puzzle_solve_backtrack_count",
    "回溯次数分布",
    ["puzzle_type", "board_size"],
)
```

在求解完成后上报：

```python
solve_requests.labels(puzzle_type=type_id, status="success").inc()
solve_duration.labels(puzzle_type=type_id, board_size=str(n)).observe(elapsed_sec)
```

### 棋盘日志的安全考量

棋盘数据可能很大（81+ 个数字）。全量记录到日志中会造成日志爆炸。建议：

- 记录棋盘的 hash（如 `hash(str(board))`）作为去重标识，而非完整棋盘
- 仅在 DEBUG 级别记录完整棋盘
- 对于异常/超时场景，可以将完整棋盘写入单独的异常日志文件（采样记录）

```python
import hashlib

def board_fingerprint(board: list[list[int]]) -> str:
    """生成棋盘的短指纹，用于去重和关联"""
    data = str(board).encode()
    return hashlib.md5(data).hexdigest()[:8]
```

### 健康检查端点

```python
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}
```

可扩展为包括依赖项检查（如果将来有数据库/缓存）。

## 预期收益

1. 线上问题排查有据可依——看到错误时能知道用户传了什么棋、求解器在哪个阶段失败
2. 性能瓶颈可量化——通过 `solve_duration` histogram 可以直观看到多少比例的请求超过预期耗时
3. 业务洞察——知道哪些谜题类型使用最多、哪个尺寸的棋盘最常见
4. 告警能力——可以基于指标设置告警（如 5xx 错误率 > 5%、P99 求解耗时 > 10s）

## 注意事项

- 在开发环境，日志输出到控制台（人类可读）；在生产环境，输出为 JSON 格式供日志聚合系统（ELK / Loki）消费
- 指标暴露端口（如 `/metrics`）需要与 API 端口区分，或至少做 IP 白名单限制
- 棋盘指纹化只能去重，无法复现——如果需要在开发环境复现问题，可以在 DEBUG 级别记录完整棋盘并以采样方式写入
- 引入 `structlog` 和 `prometheus_client` 需要更新 `requirements.txt`
