"""
数独相关 API 路由
"""

from fastapi import APIRouter, HTTPException

from app.models import SolveSudokuRequest, SolveSudokuResponse, ValidationResult
from app.services import SudokuSolver

router = APIRouter(prefix="/sudoku", tags=["数独"])


@router.post("/solve", response_model=SolveSudokuResponse)
async def sudoku_solve(request: SolveSudokuRequest) -> SolveSudokuResponse:
    """
    求解数独

    - 接收 9x9 棋盘（0 表示空格）
    - 返回求解结果或错误信息
    """
    try:
        solution = SudokuSolver(request.board, request.block_shape).solve()
        return SolveSudokuResponse(
            success=solution is not None,
            solution=solution,
            message="求解成功" if solution else "无解",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
async def sudoku_validate(request: SolveSudokuRequest) -> ValidationResult:
    """
    校验数独棋盘是否合法

    - 检查行、列、九宫格内是否有重复
    - 空格（0）不参与重复检查
    """
    return SudokuSolver.validate_board(request.board, request.block_shape)
