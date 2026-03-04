from app.services.sudoku_solver import SudokuSolver

board = [
    [0, 0, 7, 0, 0, 3, 5, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [6, 0, 0, 0, 0, 0, 3, 8, 0],    
    [3, 0, 0, 0, 1, 0, 9, 6, 0],
    [0, 2, 0, 9, 0, 8, 0, 0, 0],
    [4, 0, 5, 0, 6, 0, 0, 0, 0],
    [0, 0, 0, 8, 0, 0, 0, 0, 7],
    [0, 0, 0, 1, 0, 0, 0, 9, 0],
    [9, 6, 0, 7, 0, 5, 0, 2, 0],
]

solver = SudokuSolver(board, block_shape=(3, 3))
solution = solver.solve()
if solution:
    for row in solution:
        print(row)
else:
    print("无解")