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

    def simplify(clauses, assignment):
        """Bỏ mệnh đề đã đúng; xóa literal của biến đã gán khỏi mệnh đề còn lại."""
        remaining = []
        for clause in clauses:
            if any(assignment.get(abs(v)) == (v > 0) for v in clause):
                continue
            remaining.append(tuple(v for v in clause if abs(v) not in assignment))
        return remaining

    def search(current, assignment):
        """DPLL đệ quy. Trả về phép gán thỏa mãn `current`, hoặc None nếu UNSAT."""
        # 1. Unit propagation: mệnh đề chỉ còn 1 literal thì literal đó bắt buộc đúng.
        while True:
            check_control()
            if any(not clause for clause in current):
                return None                     # mệnh đề rỗng: mọi literal đều sai
            units = [clause[0] for clause in current if len(clause) == 1]
            if not units:
                break
            for unit in units:
                variable, value = abs(unit), unit > 0
                if variable in assignment:
                    if assignment[variable] != value:
                        return None             # hai unit đối nhau: x và -x
                else:
                    assignment[variable] = value
                    stats.propagations += 1
            current = simplify(current, assignment)

        # 2. Không còn mệnh đề nào: mọi mệnh đề đã được thỏa mãn.
        if not current:
            return assignment

        # 3. Chọn biến phân nhánh trong các mệnh đề còn lại.
        frequencies = {}
        for clause in current:
            for literal in clause:
                frequencies[abs(literal)] = frequencies.get(abs(literal), 0) + 1
        if heuristic == "ordered":
            variable = min(frequencies)
        else:  # "frequency": xuất hiện nhiều nhất, hòa thì lấy chỉ số nhỏ hơn
            variable = min(frequencies, key=lambda v: (-frequencies[v], v))
        stats.decisions += 1

        # 4. Thử True rồi False. Gán quyết định trực tiếp (không đi qua unit
        #    propagation) để `propagations` chỉ đếm phép gán bị ép buộc.
        for value in (True, False):
            branch = dict(assignment)
            branch[variable] = value
            result = search(simplify(current, branch), branch)
            if result is not None:
                return result
            stats.backtracks += 1
        return None

    try:
        result = search(formula, {})
        if result is not None:
            result = {v: result.get(v, False) for v in range(1, count + 1)}
        return SATResult("SAT" if result is not None else "UNSAT", result, stats)
    finally:
        stats.runtime = perf_counter() - start
