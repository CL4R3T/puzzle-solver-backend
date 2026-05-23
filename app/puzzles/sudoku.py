from app.registry import PuzzleRegistry, PuzzleType
from app.services import SudokuSolver
from app.models import SolvePuzzleRequest, SolvePuzzleResponse

PuzzleRegistry.register(PuzzleType(
    type_id="sudoku",
    name="数独",
    description="标准数独，支持自定义宫格形状",
    solver_class=SudokuSolver,
    request_model=SolvePuzzleRequest,
    response_model=SolvePuzzleResponse,
    default_params={"box_shape": (3, 3)},
    param_schema={
        "box_shape": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
            "default": [3, 3],
            "description": "宫格的行数和列数",
        }
    },
))
