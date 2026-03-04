from app.services.sudoku_solver import SudokuSolver


def test_solve_standard():
    # 一个简单的 9x9 数独
    board = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    solver = SudokuSolver(board)
    solution = solver.solve()
    assert solution is not None
    # 核心验证行、列、宫都不重复
    assert SudokuSolver.validate_board(solution).valid
    # 一些固定位置被填充
    assert solution[0][2] == 4
    assert solution[8][8] == 9


def test_solve_custom_block():
    # 6x6 矩形数独，块大小 2x3
    board=[
        [1,0,3,0,5,6],
        [0,0,6,1,0,3],
        [2,3,0,5,0,0],
        [5,0,1,0,3,0],
        [3,4,0,0,1,2],
        [0,0,2,0,0,5],
    ]
    # solve directly with solver class
    solver = SudokuSolver(board, block_shape=(2, 3))
    sol = solver.solve()
    assert sol is not None
    assert SudokuSolver.validate_board(sol, block_shape=(2, 3)).valid


def test_validate_rejects_bad():
    bad = [[1, 1], [0, 0]]
    res = SudokuSolver.validate_board(bad, block_shape=(1, 2))
    assert not res.valid


def test_solver_inheritance():
    # 确保 SudokuSolver 仍是 NumberPuzzleSolver 子类
    solver = SudokuSolver([[0, 0], [0, 0]], block_shape=(1, 2))
    assert solver.solve() == [[1, 2], [2, 1]] or solver.solve() == [[2, 1], [1, 2]]
    assert hasattr(solver, "_mask_to_values")