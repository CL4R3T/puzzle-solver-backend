from app.registry import PuzzleRegistry, PuzzleType
from app.services import SudokuSolver
from app.models import SolvePuzzleRequest, SolvePuzzleResponse
from app.constraints import DiagonalConstraint, KillerCageConstraint

# ---- 额外约束工厂注册 ----

def _build_diagonals(n: int, enabled: bool):
    return [DiagonalConstraint(n)] if enabled else []

def _build_cages(n: int, cages: list[dict]):
    if not cages:
        return []
    return [
        KillerCageConstraint(n, [tuple(c) for c in cage["cells"]], cage["sum"])
        for cage in cages
    ]

SudokuSolver.register_extra_constraint("diagonals", _build_diagonals)
SudokuSolver.register_extra_constraint("cages", _build_cages)

# ---- 谜题类型注册 ----

PuzzleRegistry.register(PuzzleType(
    type_id="sudoku",
    name="数独",
    description="标准数独，支持自定义宫格形状、杀手笼子、对角线等额外约束",
    solver_class=SudokuSolver,
    request_model=SolvePuzzleRequest,
    response_model=SolvePuzzleResponse,
    default_params={"box_shape": [3, 3], "cages": [], "diagonals": False},
    param_schema={
        "box_shape": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
            "default": [3, 3],
            "description": "宫格的行数和列数",
        },
        "diagonals": {
            "type": "boolean",
            "default": False,
            "description": "是否启用对角线约束（主对角线+副对角线数字不重复）",
        },
        "cages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cells": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 2,
                            "maxItems": 2,
                        },
                    },
                    "sum": {"type": "integer"},
                },
                "required": ["cells", "sum"],
            },
            "default": [],
            "description": "杀手数独笼子列表，每个笼子包含格子和目标总和",
        },
    },
))
