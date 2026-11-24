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
        if kind not in ("AND", "OR"):
            raise ValueError(f"Unknown gate: {kind}")
        identity = kind == "AND"
        literals = set()
        for value in operands:
            if type(value) is bool:
                if value != identity:
                    return value
            elif -value in literals:
                return not identity
            else:
                literals.add(value)

        if not literals:
            return identity
        if len(literals) == 1:
            return next(iter(literals))

        inputs = tuple(sorted(literals))
        key = (kind, inputs)
        if key in self.gates:
            return self.gates[key]

        output = self.next_variable
        self.next_variable += 1
        self.gates[key] = output
        if kind == "AND":
            self.clauses.extend((-output, literal) for literal in inputs)
            self.clauses.append((output,) + tuple(-literal for literal in inputs))
        else:
            self.clauses.extend((output, -literal) for literal in inputs)
            self.clauses.append((-output,) + inputs)
        return output

    def thresholds(self, cells):
        """Return one literal or constant for each possible lower bound."""
        values = tuple(self.variables[cell] for cell in self.board.ordered(cells))
        if values in self.counts:
            return self.counts[values]

        previous = [True]
        for value in values:
            current = [True]
            for k in range(1, len(previous) + 1):
                # Reach k with this cell, or keep a threshold already reached.
                with_cell = self.gate("AND", (value, previous[k - 1]))
                current.append(self.gate("OR", (self.at_least(previous, k), with_cell)))
            previous = current
        self.counts[values] = previous
        return previous

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
            literal = variable if state.statuses[cell] == "CRIMINAL" else -variable
            encoder.clauses.append((literal,))
    return encoder.finish()
