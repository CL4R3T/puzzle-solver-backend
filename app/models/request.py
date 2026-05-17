from typing import Any

from pydantic import BaseModel, Field


class SolvePuzzleRequest(BaseModel):
    """通用谜题求解请求"""
    puzzle_type: str = Field(..., description="谜题类型标识，如 'sudoku'")
    board: list[list[int]] = Field(..., description="待求解的棋盘")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="谜题类型的额外参数，如 sudoku 的 block_shape",
    )
