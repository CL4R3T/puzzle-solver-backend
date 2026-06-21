from app.models.validation import ValidationResult


class ThermoConstraint:
    """Thermometer constraint: values strictly increase along the path."""

    def __init__(self, n: int, cells: list[tuple[int, int]]):
        if len(cells) < 2:
            raise ValueError("thermometer path must contain at least two cells")
        if len(cells) > n:
            raise ValueError("thermometer path length cannot exceed board size")
        for r, c in cells:
            if not (0 <= r < n and 0 <= c < n):
                raise ValueError("thermometer cell is outside the board")
        if len(set(cells)) != len(cells):
            raise ValueError("thermometer path cannot contain duplicate cells")

        self.n = n
        self.cells = cells
        self.k = len(cells)
        self._abs_min = [i + 1 for i in range(self.k)]
        self._abs_max = [n - (self.k - 1 - i) for i in range(self.k)]

    def propagate(self, board: list[list[int]], pos: list[list[int]]) -> int:
        domains: list[int] = []

        for i, (r, c) in enumerate(self.cells):
            if board[r][c] != 0:
                value = board[r][c]
                if not (1 <= value <= self.n):
                    return -1
                domain = 1 << (value - 1)
            else:
                domain = pos[r][c]

            domain &= self._range_mask(self._abs_min[i], self._abs_max[i])
            if domain == 0:
                return -1
            domains.append(domain)

        forward = self._forward_support(domains)
        if forward is None:
            return -1

        backward = self._backward_support(domains)
        if backward is None:
            return -1

        eliminations = 0
        for i, (r, c) in enumerate(self.cells):
            supported = forward[i] & backward[i]
            if supported == 0:
                return -1

            if board[r][c] != 0:
                if supported & (1 << (board[r][c] - 1)) == 0:
                    return -1
                continue

            new_mask = pos[r][c] & supported
            if new_mask == 0:
                return -1
            if new_mask != pos[r][c]:
                removed = pos[r][c] & ~new_mask
                eliminations += removed.bit_count()
                pos[r][c] = new_mask

        return eliminations

    def _forward_support(self, domains: list[int]) -> list[int] | None:
        supported: list[int] = [0] * self.k
        supported[0] = domains[0]

        for i in range(1, self.k):
            mask = 0
            lower_values = 0
            for value in range(1, self.n + 1):
                if supported[i - 1] & (1 << (value - 1)):
                    lower_values |= self._range_mask(value + 1, self.n)
            mask = domains[i] & lower_values
            if mask == 0:
                return None
            supported[i] = mask

        return supported

    def _backward_support(self, domains: list[int]) -> list[int] | None:
        supported: list[int] = [0] * self.k
        supported[-1] = domains[-1]

        for i in range(self.k - 2, -1, -1):
            higher_values = 0
            for value in range(1, self.n + 1):
                if supported[i + 1] & (1 << (value - 1)):
                    higher_values |= self._range_mask(1, value - 1)
            mask = domains[i] & higher_values
            if mask == 0:
                return None
            supported[i] = mask

        return supported

    def _range_mask(self, min_val: int, max_val: int) -> int:
        min_val = max(1, min_val)
        max_val = min(self.n, max_val)
        if min_val > max_val:
            return 0
        width = max_val - min_val + 1
        return ((1 << width) - 1) << (min_val - 1)

    def validate(self, board: list[list[int]]) -> ValidationResult:
        vals = [board[r][c] for r, c in self.cells]
        if any(v == 0 for v in vals):
            return ValidationResult(valid=True, message="thermometer is not fully filled")
        for v in vals:
            if not (1 <= v <= self.n):
                return ValidationResult(valid=False, message=f"thermometer has invalid value {v}")
        for i in range(1, self.k):
            if vals[i] <= vals[i - 1]:
                return ValidationResult(
                    valid=False,
                    message=(
                        f"thermometer value at {self.cells[i]} ({vals[i]}) "
                        f"is not greater than previous value ({vals[i - 1]})"
                    ),
                )
        return ValidationResult(valid=True, message="thermometer constraint is valid")
