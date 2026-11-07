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
        kb = build_knowledge_base(state, self.registry)
        if self.query(kb).status == 'UNSAT':
            return 'INCONSISTENT', kb
        variable = kb.primary[cell]
        proposed = variable if verdict == 'CRIMINAL' else -variable
        if self.query(kb, (-proposed,)).status == 'UNSAT':
            return 'ACCEPTED', kb
        if self.query(kb, (proposed,)).status == 'UNSAT':
            return 'CONTRADICTED', kb
        return 'NOT_PROVABLE', kb

    def classify(self, state):
        kb = build_knowledge_base(state, self.registry)
        if self.query(kb).status == "UNSAT":
            return {cell: "INCONSISTENT" for cell in state.board.cells if cell not in state.statuses}
        verdicts = {}
        for cell in state.board.cells:
            if cell in state.statuses:
                continue
            variable = kb.primary[cell]
            negative = self.query(kb, (-variable,))
            positive = self.query(kb, (variable,))
            verdicts[cell] = "CRIMINAL" if negative.status == "UNSAT" else (
                "INNOCENT" if positive.status == "UNSAT" else "UNKNOWN")
        return verdicts

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
        agent = LogicAgent(self.registry, heuristic=heuristic, cancelled=cancelled)
        return agent.next_verdict(self.public_state())

    def step(self, heuristic='ordered', cancelled=lambda: False):
        cell, verdict = self.hint(heuristic, cancelled)
        if cell is None:
            return {'result': verdict}
        return self.submit(cell, verdict, heuristic, cancelled)

    @property
    def solved(self):
        return len(self._statuses) == len(self._puzzle.board.cells)


def check_uniqueness(puzzle, registry, heuristic="ordered", timeout=10.):
    """Offline validation only. Block primary variables, regardless of auxiliaries."""
    encoder = Encoder(puzzle.board)
    for cell in puzzle.board.cells:
        encoder.add(puzzle.clues[cell], registry)
    kb = encoder.finish()
    first = solve(kb.clauses, kb.variable_count, heuristic=heuristic, timeout=timeout)
    if first.status == "UNSAT":
        return "INCONSISTENT"
    block = tuple(-v if first.model[v] else v for v in kb.primary.values())
    second = solve(kb.clauses + (block,), kb.variable_count, heuristic=heuristic, timeout=timeout)
    return "UNIQUE" if second.status == "UNSAT" else "MULTIPLE"
