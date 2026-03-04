from .number_puzzle import SolveNumberPuzzleRequest, SolveNumberPuzzleResponse
from pydantic import Field, model_validator, BaseModel


class SolveSudokuRequest(BaseModel):
    """求解数独的请求体"""
    board: list[list[int]] = Field(
        ...,
        description="待求解的棋盘",
    )
    block_shape: tuple[int, int] = Field(default=(3, 3), description="宫格形状，默认为3x3")
    
    @model_validator(mode="after")
    def validate_block_shape(self) -> dict:
        board = self.board
        block_shape = self.block_shape
        # 验证宫的面积与边长相等
        n = len(board)
        br, bc = block_shape
        if br * bc != n:
            return ValueError("block_shape 的面积必须等于棋盘边长")
        # 验证宫内无重复
        for r in range(0, n, br):
            for c in range(0, n, bc):
                box_values = set()
                for r1 in range(r, r + br):
                    for c1 in range(c, c + bc):
                        if board[r1][c1] != 0:
                            if board[r1][c1] in box_values:
                                return ValueError("宫内有重复值")
                            box_values.add(board[r1][c1])
        return self


class SolveSudokuResponse(BaseModel):
    """求解填数谜题的响应"""
    success: bool = Field(..., description="是否求解成功")
    solution: list[list[int]] | None = Field(
        default=None,
        description="解出的棋盘，无解时为 null",
    )
    message: str = Field(default="", description="附加信息（如错误原因）")