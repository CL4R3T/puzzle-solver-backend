"""
数独相关的数据模型 (Pydantic Schemas)

数独棋盘约定：
- 9x9 二维数组
- 每个格子取值范围 0-9，0 表示空格（待填）
- 行、列索引从 0 开始
"""

from pydantic import BaseModel, Field, field_validator

class SolveNumberPuzzleRequest(BaseModel):
    """求解填数谜题的请求体"""
    board: list[list[int]] = Field(
        ...,
        description="待求解的棋盘",
    )

    @field_validator("board")
    @classmethod
    def validate_board(cls, board: list[list[int]]) -> list[list[int]]:
        """确保棋盘为正方形"""
        n = len(board)
        for row in board:
            if len(row) != n:
                raise ValueError("棋盘不是正方形")
            for cell in row:
                if not 0 <= cell <= n:
                    raise ValueError(f"格子值必须在0-{n}之间")
        for row in range(n):
            for col in range(n):
                if board[row][col] != 0:
                    for r in range(row+1,n):
                        if board[r][col] == board[row][col]:
                            raise ValueError("格子值重复")
                    for c in range(col+1,n):
                        if board[row][c] == board[row][col]:
                            raise ValueError("格子值重复")
        return board


class SolveNumberPuzzleResponse(BaseModel):
    """求解填数谜题的响应"""
    success: bool = Field(..., description="是否求解成功")
    solution: list[list[int]] | None = Field(
        default=None,
        description="解出的棋盘，无解时为 null",
    )
    message: str = Field(default="", description="附加信息（如错误原因）")


