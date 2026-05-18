from app.services.sudoku_solver import SudokuSolver
from app.services.number_puzzle_solver import PuzzleSolver
from app.constraints import RowConstraint, ColumnConstraint, BoxConstraint, DiagonalConstraint


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
    assert SudokuSolver(solution).validate_board().valid
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
    assert SudokuSolver(sol, block_shape=(2, 3)).validate_board().valid


def test_validate_rejects_bad():
    bad = [[1, 1], [0, 0]]
    res = SudokuSolver(bad, block_shape=(1, 2)).validate_board()
    assert not res.valid


def test_solver_inheritance():
    # 确保 SudokuSolver 继承了 PuzzleSolver
    solver = SudokuSolver([[0, 0], [0, 0]], block_shape=(1, 2))
    assert solver.solve() == [[1, 2], [2, 1]] or solver.solve() == [[2, 1], [1, 2]]
    assert hasattr(solver, "_mask_to_values")
    from app.services.number_puzzle_solver import PuzzleSolver as PS
    assert isinstance(solver, PS)


def test_latin_square():
    """纯行列约束（拉丁方），无宫格"""
    board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    solver = PuzzleSolver(board, [RowConstraint(3), ColumnConstraint(3)])
    sol = solver.solve()
    assert sol is not None
    for r in range(3):
        assert len(set(sol[r])) == 3, f"第{r}行有重复"
    for c in range(3):
        assert len(set(sol[r][c] for r in range(3))) == 3, f"第{c}列有重复"


def test_diagonal_sudoku():
    """对角线数独：行+列+宫+对角线"""
    board = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    solver = PuzzleSolver(board, [
        RowConstraint(9), ColumnConstraint(9),
        BoxConstraint(9, (3, 3)), DiagonalConstraint(9),
    ])
    sol = solver.solve()
    assert sol is not None
    main_diag = [sol[i][i] for i in range(9)]
    anti_diag = [sol[i][8 - i] for i in range(9)]
    assert len(set(main_diag)) == 9, "主对角线有重复"
    assert len(set(anti_diag)) == 9, "副对角线有重复"


def test_constraint_validation():
    """各约束独立校验"""
    # RowConstraint
    rc = RowConstraint(3)
    assert rc.validate([[1, 2, 3], [0, 0, 0], [0, 0, 0]]).valid
    assert not rc.validate([[1, 1, 0], [0, 0, 0], [0, 0, 0]]).valid

    # ColumnConstraint
    cc = ColumnConstraint(3)
    assert cc.validate([[1, 0, 0], [2, 0, 0], [3, 0, 0]]).valid
    assert not cc.validate([[1, 0, 0], [1, 0, 0], [0, 0, 0]]).valid

    # BoxConstraint
    bc = BoxConstraint(4, (2, 2))
    assert bc.validate([[1, 2, 0, 0], [3, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid
    assert not bc.validate([[1, 2, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid

    # DiagonalConstraint
    dc = DiagonalConstraint(3)
    assert dc.validate([[1, 0, 0], [0, 2, 0], [0, 0, 3]]).valid
    assert not dc.validate([[1, 0, 0], [0, 1, 0], [0, 0, 2]]).valid