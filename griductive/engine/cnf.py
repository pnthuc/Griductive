"""Tseitin gates and polynomial unary counting, sharing one auxiliary namespace."""
from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeBase:
    clauses: tuple
    primary: dict
    auxiliary_count: int

    @property
    def variable_count(self):
        return len(self.primary) + self.auxiliary_count


class Encoder:
    def __init__(self, board):
        self.board = board
        self.variables = {cell: i + 1 for i, cell in enumerate(board.cells)}
        self.next_variable = len(self.variables) + 1
        self.clauses = []
        self.gates = {}
        self.counts = {}

    @staticmethod
    def negate(value):
        return not value if type(value) is bool else -value

    def gate(self, kind, operands):
        identity = kind == "AND"
        values = set()
        for value in operands:
            if type(value) is bool:
                if value != identity:
                    return value
            else:
                if -value in values:
                    return not identity
                values.add(value)
        if not values:
            return identity
        if len(values) == 1:
            return next(iter(values))
        inputs = tuple(sorted(values))
        key = kind, inputs
        if key in self.gates:
            return self.gates[key]
        out = self.next_variable
        self.next_variable += 1
        self.gates[key] = out
        if kind == "AND":
            self.clauses.extend((-out, v) for v in inputs)
            self.clauses.append((out,) + tuple(-v for v in inputs))
        else:
            self.clauses.extend((out, -v) for v in inputs)
            self.clauses.append((-out,) + inputs)
        return out

    def thresholds(self, cells):
        values = tuple(self.variables[cell] for cell in self.board.ordered(cells))
        if values not in self.counts:
            previous = [True]
            for value in values:
                previous = [True] + [
                    self.gate("OR", (previous[j] if j < len(previous) else False,
                        self.gate("AND", (value, previous[j-1]))))
                    for j in range(1, len(previous) + 1)]
            self.counts[values] = previous
        return self.counts[values]

    @staticmethod
    def at_least(thresholds, k):
        return thresholds[k] if k < len(thresholds) else False

    def expression(self, spec, registry):
        return registry.handler(spec).expression(spec, self, registry)

    def add(self, spec, registry):
        registry.validate(spec, self.board)
        expression = self.expression(spec, registry)
        if expression is False:
            self.clauses.append(())
        elif expression is not True:
            self.clauses.append((expression,))

    def finish(self):
        return KnowledgeBase(tuple(self.clauses), dict(self.variables),
            self.next_variable - len(self.variables) - 1)


def build_knowledge_base(state, registry):
    encoder = Encoder(state.board)
    for cell in state.board.cells:
        if cell in state.clues:
            encoder.add(state.clues[cell], registry)
        if cell in state.statuses:
            variable = encoder.variables[cell]
            encoder.clauses.append((variable if state.statuses[cell] == "CRIMINAL" else -variable,))
    return encoder.finish()
