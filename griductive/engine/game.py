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
        """Kiểm chứng một phán quyết bằng phản chứng: KB ∧ ¬α UNSAT  ⟺  KB ⊨ α."""
        if verdict not in ('CRIMINAL', 'INNOCENT'):
            raise PuzzleError('Verdict phải là CRIMINAL hoặc INNOCENT.')
        kb = build_knowledge_base(state, self.registry)
        # KB mâu thuẫn thì suy ra được mọi thứ, nên phải loại trường hợp này trước.
        if self.query(kb).status == 'UNSAT':
            return 'INCONSISTENT', kb
        variable = kb.primary[cell]
        proposed = variable if verdict == 'CRIMINAL' else -variable
        if self.query(kb, (-proposed,)).status == 'UNSAT':
            return 'ACCEPTED', kb       # không thể sai  -> bắt buộc đúng
        if self.query(kb, (proposed,)).status == 'UNSAT':
            return 'CONTRADICTED', kb   # không thể đúng -> phán quyết ngược lại mới đúng
        return 'NOT_PROVABLE', kb       # cả hai khả năng đều còn mở

    def _verdicts(self, state):
        """Sinh (ô, kết luận) cho từng ô chưa mở, theo thứ tự trên bàn cờ.

        Mỗi kết quả SAT trả về một mô hình (nhân chứng). Nếu một mô hình nào đó
        đã cho biến v = False thì KB ∧ ¬v chắc chắn SAT, không cần hỏi lại; tương
        tự cho v = True. Nhờ vậy mỗi ô cần tối đa 1 truy vấn thay vì 2.
        """
        kb = build_knowledge_base(state, self.registry)
        pending = [cell for cell in state.board.cells if cell not in state.statuses]
        base = self.query(kb)
        if base.status == "UNSAT":
            for cell in pending:
                yield cell, "INCONSISTENT"
            return
        can_be_true, can_be_false = set(), set()

        def record(model):
            for v in kb.primary.values():
                (can_be_true if model[v] else can_be_false).add(v)

        record(base.model)
        for cell in pending:
            variable = kb.primary[cell]
            if variable not in can_be_false:
                result = self.query(kb, (-variable,))
                if result.status == "UNSAT":
                    yield cell, "CRIMINAL"
                    continue
                record(result.model)
            if variable not in can_be_true:
                result = self.query(kb, (variable,))
                if result.status == "UNSAT":
                    yield cell, "INNOCENT"
                    continue
                record(result.model)
            yield cell, "UNKNOWN"

    def classify(self, state):
        """Phân loại mọi ô chưa mở: CRIMINAL / INNOCENT / UNKNOWN / INCONSISTENT."""
        return dict(self._verdicts(state))

    def next_verdict(self, state):
        """Ô đầu tiên (theo thứ tự bàn cờ) suy ra được; dừng ngay khi tìm thấy."""
        for cell, verdict in self._verdicts(state):
            if verdict in ("CRIMINAL", "INNOCENT"):
                return cell, verdict
            if verdict == "INCONSISTENT":
                return None, "INCONSISTENT"
        return None, "UNKNOWN"


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
