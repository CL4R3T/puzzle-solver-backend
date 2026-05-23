from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_types():
    r = client.get("/api/puzzle/types")
    assert r.status_code == 200
    types = r.json()["types"]
    type_ids = [t["type_id"] for t in types]
    assert "sudoku" in type_ids
    assert "killer-sudoku" in type_ids


def test_solve_standard_sudoku():
    r = client.post("/api/puzzle/sudoku/solve", json={
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
        ],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["solution"] is not None


def test_solve_killer_sudoku():
    r = client.post("/api/puzzle/killer-sudoku/solve", json={
        "board": [
            [1, 0, 0, 4],
            [0, 4, 0, 0],
            [2, 0, 0, 0],
            [0, 0, 0, 1],
        ],
        "params": {
            "box_shape": [2, 2],
            "cages": [
                {"cells": [[0, 1], [0, 2]], "sum": 5},
            ],
        },
    })
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    sol = body["solution"]
    # 笼子和校验
    assert sol[0][1] + sol[0][2] == 5


def test_validate_sudoku_invalid():
    r = client.post("/api/puzzle/sudoku/validate", json={
        "board": [[1, 1], [0, 0]],
        "params": {"box_shape": [1, 2]},
    })
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_validate_sudoku_valid():
    r = client.post("/api/puzzle/sudoku/validate", json={
        "board": [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 9],
        ],
    })
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_validate_killer_sudoku_valid():
    r = client.post("/api/puzzle/killer-sudoku/validate", json={
        "board": [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 1],
        ],
        "params": {
            "box_shape": [2, 2],
            "cages": [
                {"cells": [[0, 0], [0, 1]], "sum": 3},
            ],
        },
    })
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_unknown_puzzle_type_404():
    r = client.post("/api/puzzle/unknown/solve", json={"board": [[0]]})
    assert r.status_code == 404


def test_sudoku_no_solution():
    # 第一行两个 1 矛盾
    r = client.post("/api/puzzle/sudoku/solve", json={
        "board": [
            [1, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        "params": {"box_shape": [2, 2]},
    })
    assert r.status_code == 200
    assert r.json()["success"] is False
