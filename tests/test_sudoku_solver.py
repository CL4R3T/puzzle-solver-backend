from app.services.sudoku_solver import SudokuSolver
from app.services.number_puzzle_solver import NumberPuzzleSolver
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
    solver = SudokuSolver(board, box_shape=(2, 3))
    sol = solver.solve()
    assert sol is not None
    assert SudokuSolver(sol, box_shape=(2, 3)).validate_board().valid


def test_validate_rejects_bad():
    bad = [[1, 1], [0, 0]]
    res = SudokuSolver(bad, box_shape=(1, 2)).validate_board()
    assert not res.valid


def test_solver_inheritance():
    # 确保 SudokuSolver 继承了 NumberPuzzleSolver
    solver = SudokuSolver([[0, 0], [0, 0]], box_shape=(1, 2))
    assert solver.solve() == [[1, 2], [2, 1]] or solver.solve() == [[2, 1], [1, 2]]
    assert hasattr(solver, "_mask_to_values")
    from app.services.number_puzzle_solver import NumberPuzzleSolver as PS
    assert isinstance(solver, PS)


def test_latin_square():
    """纯行列约束（拉丁方），无宫格"""
    board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    solver = NumberPuzzleSolver(board, [RowConstraint(3), ColumnConstraint(3)])
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
    solver = NumberPuzzleSolver(board, [
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


# ---------- Killer Sudoku ----------

def test_killer_cage_validation():
    from app.constraints import KillerCageConstraint
    cage = KillerCageConstraint(4, [(0, 0), (0, 1)], 5)

    # 正确：1+4=5，无不重复冲突
    assert cage.validate([[1, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid

    # 和错误：2+4=6 != 5
    assert not cage.validate([[2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid

    # 重复值
    assert not cage.validate([[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid

    # 未填满时跳过校验
    assert cage.validate([[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]).valid


def test_killer_cage_propagate_single_remaining():
    """只剩一个空格时直接填差值"""
    from app.constraints import KillerCageConstraint
    n = 4
    cage = KillerCageConstraint(n, [(0, 0), (0, 1)], 5)
    board = [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    pos = [[(1 << n) - 1] * n for _ in range(n)]
    pos[0][0] = 1  # val=1

    result = cage.propagate(board, pos)
    assert result > 0
    assert board[0][1] == 4
    assert pos[0][1] == 1 << 3  # val=4


def test_killer_cage_propagate_elimination():
    """三格笼子和=6 应消去 4，因为仅有 {1,2,3} 可行"""
    from app.constraints import KillerCageConstraint
    n = 4
    cage = KillerCageConstraint(n, [(0, 0), (0, 1), (0, 2)], 6)
    board = [[0] * n for _ in range(n)]
    pos = [[(1 << n) - 1] * n for _ in range(n)]

    result = cage.propagate(board, pos)
    assert result > 0
    # 值 4 应该从所有三格中被消除
    bit4 = 1 << 3
    for c in range(3):
        assert (pos[0][c] & bit4) == 0, f"cell (0,{c}) 不应包含 4"
        assert pos[0][c] != 0

    # 值 1,2,3 应该保留
    for c in range(3):
        for val in [1, 2, 3]:
            assert (pos[0][c] & (1 << (val - 1))) != 0


def test_killer_cage_contradiction():
    """笼子和不可能达成时应返回 -1"""
    from app.constraints import KillerCageConstraint
    n = 4
    cage = KillerCageConstraint(n, [(0, 0), (0, 1)], 3)  # 最小和 1+2=3，可以
    # 填入 4 后剩余格子无法达成 target
    board = [[4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    pos = [[(1 << n) - 1] * n for _ in range(n)]
    pos[0][0] = 1 << 3

    result = cage.propagate(board, pos)
    assert result == -1


def test_killer_sudoku_solve():
    """用 SudokuSolver + cages 求解含笼子约束的 4x4 数独"""
    from app.services import SudokuSolver

    board = [
        [1, 0, 0, 4],
        [0, 4, 0, 0],
        [2, 0, 0, 0],
        [0, 0, 0, 1],
    ]
    cages = [
        {"cells": [[0, 1], [0, 2]], "sum": 5},
    ]

    solver = SudokuSolver(board, box_shape=(2, 2), extra_constraints={"cages": cages})
    sol = solver.solve()
    assert sol is not None, "应该有解"
    assert SudokuSolver(sol, box_shape=(2, 2), extra_constraints={"cages": cages}).validate_board().valid

    assert sol[0][1] + sol[0][2] == 5


def test_killer_sudoku_full_cage():
    """全部格子被笼子覆盖且笼子和匹配标准数独解的 4x4 杀手数独"""
    from app.services import SudokuSolver

    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    # 基于已知解 [[1,2,3,4],[3,4,1,2],[2,1,4,3],[4,3,2,1]] 构造笼子
    cages = [
        {"cells": [[0, 0], [0, 1]], "sum": 3},   # 1+2
        {"cells": [[0, 2], [1, 2]], "sum": 4},   # 3+1
        {"cells": [[0, 3], [1, 3]], "sum": 6},   # 4+2
        {"cells": [[1, 0], [1, 1]], "sum": 7},   # 3+4
        {"cells": [[2, 0], [3, 0]], "sum": 6},   # 2+4
        {"cells": [[2, 1], [2, 2]], "sum": 5},   # 1+4
        {"cells": [[2, 3], [3, 3]], "sum": 4},   # 3+1
        {"cells": [[3, 1], [3, 2]], "sum": 5},   # 3+2
    ]

    solver = SudokuSolver(board, box_shape=(2, 2), extra_constraints={"cages": cages})
    sol = solver.solve()
    assert sol is not None, "应该有解"
    assert SudokuSolver(sol, box_shape=(2, 2), extra_constraints={"cages": cages}).validate_board().valid
    for cage in cages:
        cage_sum = sum(sol[r][c] for r, c in (tuple(c) for c in cage["cells"]))
        assert cage_sum == cage["sum"], f"笼子 {cage} 和不对"