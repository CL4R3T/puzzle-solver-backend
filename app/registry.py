from dataclasses import dataclass, field
from typing import Any


@dataclass
class PuzzleType:
    type_id: str
    name: str
    description: str
    solver_class: type
    request_model: type
    response_model: type
    default_params: dict = field(default_factory=dict)
    param_schema: dict | None = None


class PuzzleRegistry:
    _types: dict[str, PuzzleType] = {}

    @classmethod
    def register(cls, puzzle_type: PuzzleType) -> None:
        if puzzle_type.type_id in cls._types:
            raise ValueError(f"Puzzle type '{puzzle_type.type_id}' is already registered")
        cls._types[puzzle_type.type_id] = puzzle_type

    @classmethod
    def get(cls, type_id: str) -> PuzzleType:
        if type_id not in cls._types:
            raise KeyError(f"Unknown puzzle type: {type_id}")
        return cls._types[type_id]

    @classmethod
    def list_types(cls) -> list[dict]:
        return [
            {
                "type_id": t.type_id,
                "name": t.name,
                "description": t.description,
                "params": t.param_schema,
            }
            for t in cls._types.values()
        ]
