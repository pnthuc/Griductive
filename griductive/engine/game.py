"""Public-only reasoning, private sessions and offline uniqueness checking."""
import json
from dataclasses import dataclass, field
from .cnf import Encoder, build_knowledge_base
from .models import PublicState, PuzzleError, freeze
from .sat import solve


@dataclass
class LogicAgent:
    registry: object
    heuristic: str = "ordered"
    timeout: float = 10.
    queries: list = field(default_factory=list)
    cancelled: object = lambda: False

    def query(self, kb, assumptions=()):
        result = solve(kb.clauses, kb.variable_count, assumptions, self.heuristic, self.timeout, cancelled=self.cancelled)
        self.queries.append({
            "assumptions": list(assumptions), "result": result.status,
            "decisions": result.stats.decisions, "propagations": result.stats.propagations,
            "backtracks": result.stats.backtracks, "runtime": result.stats.runtime})
        return result

    def verify(self, state, cell, verdict):
        # TODO(Nam): Kiểm tra phán đoán `verdict` ('CRIMINAL' hoặc 'INNOCENT') cho ô `cell` bằng suy luận phản chứng.
        #
        # Các bước cần thực hiện:
        # 1. Tạo `kb = build_knowledge_base(state, self.registry)`.
        # 2. Nếu bản thân `self.query(kb).status == 'UNSAT'` -> trả về `'INCONSISTENT', kb`.
        # 3. Lấy biến chính `variable = kb.primary[cell]`.
        #    Đặt `proposed = variable if verdict == 'CRIMINAL' else -variable`.
        # 4. Kiểm tra phản chứng:
        #    - Nếu thêm giả định ngược `(-proposed,)` mà `self.query(kb, (-proposed,)).status == 'UNSAT'`,
        #      nghĩa là `proposed` bắt buộc đúng -> trả về `'ACCEPTED', kb`.
        #    - Ngược lại, nếu thêm giả định `(proposed,)` mà `self.query(kb, (proposed,)).status == 'UNSAT'`,
        #      nghĩa là `proposed` mâu thuẫn với KB -> trả về `'CONTRADICTED', kb`.
        #    - Nếu cả 2 đều SAT (chưa đủ thông tin kết luận) -> trả về `'NOT_PROVABLE', kb`.
        raise NotImplementedError("TODO(Nam): Cài đặt LogicAgent.verify() trong game.py")

    def classify(self, state):
        # TODO(Nam): Phân loại toàn bộ các ô chưa mở trên bàn cờ (`cell not in state.statuses`).
        #
        # Các bước cần thực hiện:
        # 1. Tạo `kb = build_knowledge_base(state, self.registry)`.
        # 2. Nếu `self.query(kb).status == "UNSAT"`:
        #    Trả về dict `{cell: "INCONSISTENT"}` cho mọi `cell` trong `state.board.cells` chưa có trong `state.statuses`.
        # 3. Với mỗi `cell` chưa mở:
        #    - Lấy `variable = kb.primary[cell]`.
        #    - Gọi `negative = self.query(kb, (-variable,))` và `positive = self.query(kb, (variable,))`.
        #    - Nếu `negative.status == "UNSAT"` -> `"CRIMINAL"`
        #      Ngược lại nếu `positive.status == "UNSAT"` -> `"INNOCENT"`
        #      Ngược lại -> `"UNKNOWN"`.
        # 4. Trả về dict `verdicts`.
        raise NotImplementedError("TODO(Nam): Cài đặt LogicAgent.classify() trong game.py")

    def next_verdict(self, state):
        results = self.classify(state)
        for cell, verdict in results.items():
            if verdict in ("CRIMINAL", "INNOCENT"):
                return cell, verdict
        return None, "INCONSISTENT" if "INCONSISTENT" in results.values() else "UNKNOWN"


class GameEngine:
    """Owns hidden data. Verdict checks use only a public snapshot."""
    def __init__(self, puzzle, registry=None):
        self._puzzle = puzzle
        if registry is None:
            from .clues import clue_registry
            from .regions import region_registry
            registry = clue_registry(region_registry())
        self.registry = registry
        self._statuses = {c: puzzle.solution[c] for c in puzzle.initially_revealed}
        self._clues = {c: puzzle.clues[c] for c in puzzle.initially_revealed}
        self.trace = []

    def fork(self):
        """Isolated tentative session; private immutable puzzle is shared."""
        import copy
        candidate = copy.copy(self)
        candidate._statuses = dict(self._statuses)
        candidate._clues = dict(self._clues)
        candidate.trace = list(self.trace)
        return candidate

    def public_state(self):
        p = self._puzzle
        return PublicState(p.puzzle_id, p.title, p.board, p.characters,
            freeze(self._statuses), freeze(self._clues))

    def submit(self, cell, verdict, heuristic="ordered", cancelled=lambda: False):
        self._puzzle.board.position(cell)
        if verdict not in ('CRIMINAL', 'INNOCENT'):
            raise PuzzleError('Verdict phải là CRIMINAL hoặc INNOCENT.')
        if cell in self._statuses:
            return {'result': 'ALREADY_REVEALED', 'cell': cell}
        agent = LogicAgent(self.registry, heuristic=heuristic, cancelled=cancelled)
        before = self.public_state()
        outcome, kb = agent.verify(before, cell, verdict)
        if outcome != 'ACCEPTED':
            return {'result': outcome, 'cell': cell, 'queries': agent.queries}
        if self._puzzle.solution[cell] != verdict:
            return {'result': 'INCONSISTENT', 'cell': cell, 'queries': agent.queries}
        entry = {
            'step': len(self.trace) + 1, 'cell': cell, 'verdict': verdict,
            'active_clues': [before.clues[c]['id'] for c in before.board.cells if c in before.clues],
            'queries': agent.queries, 'new_clue': self._puzzle.clues[cell]['id'],
            'new_clue_content': json.loads(json.dumps(self._puzzle.clues[cell], default=dict)),
            'primary_variables': len(kb.primary), 'auxiliary_variables': kb.auxiliary_count,
            'clauses': len(kb.clauses)}
        if cancelled():
            from .sat import SolverCancelled
            raise SolverCancelled('Cancelled before committing verdict')
        self._statuses[cell] = verdict
        self._clues[cell] = self._puzzle.clues[cell]
        self.trace.append(entry)
        return {'result': 'ACCEPTED', **entry}

    def hint(self, heuristic='ordered', cancelled=lambda: False):
        # TODO(Thien): Tạo `LogicAgent(self.registry, heuristic=heuristic, cancelled=cancelled)`
        # và trả về `agent.next_verdict(self.public_state())`.
        raise NotImplementedError("TODO(Thien): Cài đặt GameEngine.hint() trong game.py")

    def step(self, heuristic='ordered', cancelled=lambda: False):
        # TODO(Thien): Thực hiện tự động 1 bước suy luận:
        # - Gọi `cell, verdict = self.hint(heuristic, cancelled)`.
        # - Nếu `cell is None`: trả về `{'result': verdict}`.
        # - Ngược lại: gọi và trả về `self.submit(cell, verdict, heuristic, cancelled)`.
        raise NotImplementedError("TODO(Thien): Cài đặt GameEngine.step() trong game.py")

    @property
    def solved(self):
        return len(self._statuses) == len(self._puzzle.board.cells)


def check_uniqueness(puzzle, registry, heuristic="ordered", timeout=10.):
    """Offline validation only. Block primary variables, regardless of auxiliaries."""
    # TODO(Thien): Kiểm tra xem `puzzle` (khi mở toàn bộ clues) có nghiệm duy nhất trên các biến chính hay không.
    #
    # Các bước cần thực hiện:
    # 1. Tạo `encoder = Encoder(puzzle.board)`, duyệt mọi `cell` trong `puzzle.board.cells` và gọi
    #    `encoder.add(puzzle.clues[cell], registry)`, sau đó `kb = encoder.finish()`.
    # 2. Giải lần 1: `first = solve(kb.clauses, kb.variable_count, heuristic=heuristic, timeout=timeout)`.
    #    Nếu `first.status == "UNSAT"` -> trả về `"INCONSISTENT"`.
    # 3. Tạo mệnh đề chặn (blocking clause) trên các biến chính (`kb.primary.values()`):
    #    `block = tuple(-v if first.model[v] else v for v in kb.primary.values())`
    # 4. Giải lần 2 với `kb.clauses + (block,)`:
    #    Nếu kết quả là `"UNSAT"` -> trả về `"UNIQUE"`, ngược lại trả về `"MULTIPLE"`.
    raise NotImplementedError("TODO(Thien): Cài đặt check_uniqueness() trong game.py")
