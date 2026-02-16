from app.services.sudoku_solver import solve_sudoku, validate_board

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

if validate_board(board).valid:
    print("Board is valid")
    result = solve_sudoku(board)
    if result:
        print("Solved successfully")
        print(result)
    else:
        print("Failed to solve")
else:
    print("Board is invalid")
    print(validate_board(board).message)
