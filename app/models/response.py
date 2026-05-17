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
