"""
数独相关的数据模型 (Pydantic Schemas)

数独棋盘约定：
- 9x9 二维数组
- 每个格子取值范围 0-9，0 表示空格（待填）
- 行、列索引从 0 开始
"""

from pydantic import BaseModel, Field, field_validator


def _validate_board(v: list[list[int]]) -> list[list[int]]:
    """确保棋盘为 9x9，且每个格子为 0-9"""
    if len(v) != 9:
        raise ValueError("棋盘必须有 9 行")
    for i, row in enumerate(v):
        if len(row) != 9:
            raise ValueError(f"第 {i+1} 行必须有 9 列")
        for j, cell in enumerate(row):
            if not 0 <= cell <= 9:
                raise ValueError(f"格子 ({i+1}, {j+1}) 的值必须在 0-9 之间")
    return v


class SudokuBoard(BaseModel):
    """数独棋盘模型"""
    board: list[list[int]] = Field(
        ...,
        description="9x9 二维数组，0 表示空格",
        min_length=9,
        max_length=9,
    )

    @field_validator("board")
    @classmethod
    def validate_board(cls, v: list[list[int]]) -> list[list[int]]:
        return _validate_board(v)

    model_config = {"json_schema_extra": {"example": {
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
        ]
    }}}


class SolveRequest(BaseModel):
    """求解数独的请求体"""
    board: list[list[int]] = Field(
        ...,
        description="待求解的数独棋盘",
    )

    @field_validator("board")
    @classmethod
    def validate_board(cls, v: list[list[int]]) -> list[list[int]]:
        return _validate_board(v)


class SolveResponse(BaseModel):
    """求解数独的响应"""
    success: bool = Field(..., description="是否求解成功")
    solution: list[list[int]] | None = Field(
        default=None,
        description="解出的棋盘，无解时为 null",
    )
    message: str = Field(default="", description="附加信息（如错误原因）")


class ValidationResult(BaseModel):
    """数独合法性校验结果"""
    valid: bool = Field(..., description="当前棋盘是否符合数独规则")
    message: str = Field(default="", description="校验说明")
