"""Deterministic DPLL, with complete models, assumptions and per-call statistics."""
from dataclasses import dataclass
from time import perf_counter


@dataclass
class Statistics:
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0
    runtime: float = 0.


@dataclass(frozen=True)
class SATResult:
    status: str
    model: dict | None
    stats: Statistics


class SolverTimeout(TimeoutError):
    pass


class SolverCancelled(Exception):
    pass


def solve(clauses, variable_count=None, assumptions=(), heuristic="ordered", timeout=10., cancelled=lambda: False):
    if heuristic not in ("ordered", "frequency"):
        raise ValueError("Unknown branching heuristic")
    formula = [tuple(dict.fromkeys(c)) for c in clauses]
    formula += [(literal,) for literal in assumptions]
    maximum = max((abs(v) for c in formula for v in c), default=0)
    count = maximum if variable_count is None else variable_count
    if count < maximum or any(type(v) is not int or v == 0 for c in formula for v in c):
        raise ValueError("Invalid CNF literals or variable count")
    formula = [c for c in formula if not any(-v in c for v in c)]
    stats = Statistics()
    start = perf_counter()

    def check_control():
        if cancelled():
            raise SolverCancelled("SAT query cancelled")
        if perf_counter() - start > timeout:
            raise SolverTimeout("SAT query exceeded its time limit")

    def search(current, assignment):
        check_control()
        # TODO(Nam): Cài đặt thuật toán DPLL đệ quy tìm phép gán thỏa mãn tập mệnh đề `current`.
        #
        # Input:
        #   - `current`: list các clause, mỗi clause là 1 tuple các số nguyên (literal).
        #     Ví dụ: [(1, -2), (2,)] tương ứng với (x1 v ~x2) ^ (x2).
        #   - `assignment`: dict {variable_id (int > 0): bool} lưu các biến đã gán giá trị.
        #
        # Các bước cần thực hiện:
        # 1. Vòng lặp Unit Propagation:
        #    - Gọi `check_control()` mỗi đầu vòng lặp để kiểm tra timeout / cancel.
        #    - Nếu trong `current` có mệnh đề rỗng `()` -> mâu thuẫn, trả về `None`.
        #    - Tìm tất cả unit clauses (các mệnh đề có `len(clause) == 1`).
        #    - Nếu không còn unit clause nào -> thoát vòng lặp Unit Propagation.
        #    - Duyệt từng `unit` (literal duy nhất trong unit clause):
        #        + `variable, value = abs(unit), unit > 0`
        #        + Nếu `variable` đã có trong `assignment`:
        #            * Nếu `assignment[variable] != value` -> mâu thuẫn, trả về `None`.
        #        + Nếu chưa có: gán `assignment[variable] = value` và tăng `stats.propagations += 1`.
        #    - Rút gọn `current` thành danh sách mệnh đề mới `simplified`:
        #        + Bỏ qua (xóa) các clause đã thỏa mãn (có chứa literal `v` mà `assignment[abs(v)] == (v > 0)`).
        #        + Với các clause còn lại, loại bỏ những literal mà biến `abs(v)` đã có trong `assignment`.
        #
        # 2. Kiểm tra điều kiện dừng sau Unit Propagation:
        #    - Nếu `current` rỗng (tất cả mệnh đề đã thỏa mãn) -> trả về `assignment`.
        #
        # 3. Chọn biến phân nhánh (Branching Heuristic):
        #    - Đếm tần suất xuất hiện `frequencies[abs(literal)]` của từng biến trong `current`.
        #    - Nếu `heuristic == "ordered"`: chọn biến có chỉ số nhỏ nhất (`min(frequencies)`).
        #    - Nếu `heuristic == "frequency"`: chọn biến xuất hiện nhiều nhất, nếu bằng nhau ưu tiên chỉ số nhỏ hơn
        #      (`min(frequencies, key=lambda v: (-frequencies[v], v))`).
        #    - Tăng `stats.decisions += 1`.
        #
        # 4. Đệ quy thử gán True rồi False (Backtracking):
        #    - Thử lần lượt `literal` trong `(variable, -variable)`:
        #        + Gọi đệ quy `search(current + [(literal,)], assignment.copy())`.
        #        + Nếu kết quả khác `None` -> trả về kết quả đó.
        #        + Nếu thất bại (`None`) -> tăng `stats.backtracks += 1` rồi thử nhánh tiếp theo.
        #    - Nếu cả 2 nhánh đều thất bại -> trả về `None`.
        raise NotImplementedError("TODO(Nam): Cài đặt hàm search() của thuật toán DPLL trong sat.py")

    try:
        result = search(formula, {})
        if result is not None:
            result = {v: result.get(v, False) for v in range(1, count + 1)}
        return SATResult("SAT" if result is not None else "UNSAT", result, stats)
    finally:
        stats.runtime = perf_counter() - start
