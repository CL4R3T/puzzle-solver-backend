import time

from fastapi import APIRouter, HTTPException

from app.models import SolvePuzzleRequest, SolvePuzzleResponse, ValidationResponse
from app.registry import PuzzleRegistry

router = APIRouter(prefix="/puzzle", tags=["谜题求解"])


@router.get("/types")
async def list_puzzle_types():
    return {"types": PuzzleRegistry.list_types()}


@router.post("/{type_id}/solve")
async def solve_puzzle(type_id: str, request: SolvePuzzleRequest):
    try:
        puzzle_type = PuzzleRegistry.get(type_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown puzzle type: {type_id}")

    try:
        params = dict(request.params)
        box_shape = tuple(params.pop("box_shape", [3, 3]))
        solver = puzzle_type.solver_class(request.board, box_shape=box_shape, extra_constraints=params)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    validation = solver.validate_board()
    if not validation.valid:
        return SolvePuzzleResponse(
            success=False,
            message=validation.message,
        )

    start = time.perf_counter()
    solution = solver.solve()
    elapsed = (time.perf_counter() - start) * 1000

    return SolvePuzzleResponse(
        success=solution is not None,
        solution=solution,
        message="求解成功" if solution else "无解",
        solve_time_ms=elapsed,
    )


@router.get("/{type_id}/constraints")
async def get_constraints_info(type_id: str):
    """获取谜题类型可用的所有约束信息，包括内置约束和额外约束"""
    try:
        puzzle_type = PuzzleRegistry.get(type_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown puzzle type: {type_id}")

    solver_cls = puzzle_type.solver_class
    builtin = []
    extra = []

    if hasattr(solver_cls, "get_builtin_constraints_info"):
        builtin = solver_cls.get_builtin_constraints_info()
    if hasattr(solver_cls, "get_extra_constraints_info"):
        extra = solver_cls.get_extra_constraints_info()

    return {
        "type_id": type_id,
        "builtin_constraints": builtin,
        "extra_constraints": extra,
    }


@router.post("/{type_id}/validate")
async def validate_puzzle(type_id: str, request: SolvePuzzleRequest):
    try:
        puzzle_type = PuzzleRegistry.get(type_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown puzzle type: {type_id}")

    try:
        params = dict(request.params)
        box_shape = tuple(params.pop("box_shape", [3, 3]))
        solver = puzzle_type.solver_class(request.board, box_shape=box_shape, extra_constraints=params)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = solver.validate_board()
    return ValidationResponse(
        valid=result.valid,
        message=result.message,
    )
