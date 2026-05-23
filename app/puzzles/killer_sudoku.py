from app.registry import PuzzleRegistry, PuzzleType
from app.services import KillerSudokuSolver
from app.models import SolvePuzzleRequest, SolvePuzzleResponse

PuzzleRegistry.register(PuzzleType(
    type_id="killer-sudoku",
    name="杀手数独",
    description="标准数独规则 + 虚线框内数字不重复且和等于目标值",
    solver_class=KillerSudokuSolver,
    request_model=SolvePuzzleRequest,
    response_model=SolvePuzzleResponse,
    default_params={"cages": [], "box_shape": [3, 3]},
    param_schema={
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
            "description": "笼子列表，每个笼子包含格子和目标总和",
        },
        "box_shape": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
            "default": [3, 3],
            "description": "宫格的行数和列数，默认 3x3",
        },
    },
))
