"""Clue definitions and references. Register a named class in this file."""
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import FrozenSet
import operator
from .models import PuzzleError


class Clue(ABC):
    """One definition owns semantics, encoding, reference fields and optional wording.

    Keep rule instances stateless: put puzzle parameters in the JSON spec.
    Declared fields are validated and highlighted automatically.
    """
    children = ()
    region_fields = ()
    person_fields = ()

    def validate(self, spec, board, clues):
        """Validate extra parameters; declared references are already checked."""

    @abstractmethod
    def evaluate(self, spec, assignment, board, clues):
        """Return truth directly, without calling the encoder/SAT solver."""

    @abstractmethod
    def expression(self, spec, encoder, clues):
        """Return a literal or bool, using the supplied shared encoder."""

    @abstractmethod
    def describe(self, spec, board, clues):
        """Plain fallback description."""

    def cells(self, spec, board, clues):
        cells = {spec[field] for field in self.person_fields}
        for field in self.region_fields:
            cells.update(clues.regions.resolve(spec[field], board))
        for field in self.children:
            cells.update(clues.cells(spec[field], board))
        return frozenset(cells)

    def named_regions(self, spec, board, clues):
        return False

    def wording(self, spec, text):
        """Optional linked wording; text.region/person/token work in plain and HTML."""
        return None


class ClueRegistry:
    def __init__(self, regions):
        self.regions = regions
        self.handlers = {}

    def register(self, name, rule=None):
        """Register an instance/class, or use @clues.register('NAME')."""
        def install(definition):
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Tên clue phải là chuỗi không rỗng.')
            if name in self.handlers:
                raise ValueError(f'Clue đã đăng ký: {name}')
            instance = definition() if isinstance(definition, type) else definition
            if not isinstance(instance, Clue):
                raise TypeError('Clue phải kế thừa lớp Clue.')
            self.handlers[name] = instance
            return definition
        return install if rule is None else install(rule)

    def handler(self, spec):
        if not isinstance(spec, Mapping):
            raise PuzzleError('Clue phải là một object.')
        kind = spec.get('type')
        if not isinstance(kind, str) or kind not in self.handlers:
            raise PuzzleError(f'Không hỗ trợ clue: {kind!r}')
        return self.handlers[kind]

    def validate(self, spec, board, depth=0):
        if depth > 12:
            raise PuzzleError('Clue lồng quá 12 cấp.')
        rule = self.handler(spec)
        for field in rule.children:
            self.validate(spec.get(field), board, depth + 1)
        for field in rule.region_fields:
            self.regions.resolve(spec.get(field), board)
        for field in rule.person_fields:
            board.position(spec.get(field))
        rule.validate(spec, board, self)

    def evaluate(self, spec, assignment, board):
        self.validate(spec, board)
        return self.handler(spec).evaluate(spec, assignment, board, self)

    def encode(self, spec, board):
        """Encode one standalone clue; use Encoder.add for a shared KB."""
        from .cnf import Encoder
        encoder = Encoder(board)
        encoder.add(spec, self)
        return list(encoder.finish().clauses)

    def describe(self, spec, board):
        self.validate(spec, board)
        return self.handler(spec).describe(spec, board, self)

    def cells(self, spec, board):
        self.validate(spec, board)
        return frozenset(self.handler(spec).cells(spec, board, self))

    def anchors(self, spec, board):
        rule = self.handler(spec)
        cells = set()
        for field in rule.region_fields:
            cells.update(self.regions.anchors(spec[field], board))
        for field in rule.children:
            cells.update(self.anchors(spec[field], board))
        return frozenset(cells)


# Only definitions are stored globally; each session gets its own catalog.
_DEFAULT_CLUES = ClueRegistry(None)
register_clue = _DEFAULT_CLUES.register


def clue_registry(regions):
    registry = ClueRegistry(regions)
    registry.handlers = dict(_DEFAULT_CLUES.handlers)
    return registry


@register_clue('FACT')
class Fact(Clue):
    person_fields = ('person',)

    def validate(self, spec, board, clues):
        if spec.get('status') not in ('CRIMINAL', 'INNOCENT'):
            raise PuzzleError('status phải là CRIMINAL hoặc INNOCENT.')

    def evaluate(self, spec, assignment, board, clues):
        # TODO(Thien): Kiểm tra trực tiếp xem `assignment[spec['person']]` có khớp với `spec['status']` không.
        # (`assignment` là dict {cell: bool} trong đó True ứng với 'CRIMINAL', False ứng với 'INNOCENT').
        raise NotImplementedError("TODO(Thien): Cài đặt Fact.evaluate() trong clues.py")

    def expression(self, spec, encoder, clues):
        # TODO(Phuc): Trả về literal biểu diễn Fact:
        # `encoder.variables[spec['person']]` nếu `spec['status'] == 'CRIMINAL'`, ngược lại trả về số âm của nó.
        raise NotImplementedError("TODO(Phuc): Cài đặt Fact.expression() trong clues.py")

    def describe(self, spec, board, clues):
        return f'{spec["person"]} là {spec["status"].title()}.'


@register_clue('SAME')
class Same(Clue):
    person_fields = ('a', 'b')
    same = True

    def evaluate(self, spec, assignment, board, clues):
        # TODO(Thien): Kiểm tra 2 ô `spec['a']` và `spec['b']` có cùng trạng thái (`self.same == True`)
        # hoặc khác trạng thái (`self.same == False`, dùng chung cho lớp `Different`) trong `assignment` không.
        raise NotImplementedError("TODO(Thien): Cài đặt Same.evaluate() trong clues.py")

    def expression(self, spec, encoder, clues):
        # TODO(Phuc): Mã hóa mệnh đề tương đương (a <-> b) hoặc (a xor b) qua cổng Tseitin `encoder.gate`:
        # - Lấy `a, b = encoder.variables[spec['a']], encoder.variables[spec['b']]`.
        # - `equal = AND(OR(-a, b), OR(a, -b))`
        # - Nếu `self.same` là True trả về `equal`, ngược lại trả về `encoder.negate(equal)`.
        raise NotImplementedError("TODO(Phuc): Cài đặt Same.expression() trong clues.py")

    def describe(self, spec, board, clues):
        relation = 'cùng' if self.same else 'khác'
        return f'{spec["a"]} và {spec["b"]} {relation} trạng thái.'


@register_clue('DIFFERENT')
class Different(Same):
    same = False


class Count(Clue):
    region_fields = ('region',)

    def validate(self, spec, board, clues):
        size = len(clues.regions.resolve(spec['region'], board))
        if type(spec.get('k')) is not int or not 0 <= spec['k'] <= size:
            raise PuzzleError(f'k phải là số nguyên từ 0 đến {size}.')

    def evaluate(self, spec, assignment, board, clues):
        # TODO(Thien): Đếm số ô có `assignment[cell] == True` trong vùng `clues.regions.resolve(spec['region'], board)`,
        # sau đó gọi `self.compare(count, spec['k'])`.
        raise NotImplementedError("TODO(Thien): Cài đặt Count.evaluate() trong clues.py")

    def expression(self, spec, encoder, clues):
        # TODO(Phuc): Mã hóa ràng buộc đếm số lượng Criminal trong vùng `spec['region']`:
        # - Gọi `counts = encoder.thresholds(clues.regions.resolve(spec['region'], encoder.board))`.
        # - `lower = encoder.at_least(counts, spec['k'])` (ít nhất k Criminal).
        # - `upper = encoder.negate(encoder.at_least(counts, spec['k'] + 1))` (nhiều nhất k Criminal, tức không có >= k+1).
        # - Trả về `self.bound(encoder, lower, upper)`.
        raise NotImplementedError("TODO(Phuc): Cài đặt Count.expression() trong clues.py")

    def describe(self, spec, board, clues):
        region = clues.regions.describe(spec['region'], board)
        return f'{self.word} {spec["k"]} Criminal trong {region}.'

    @abstractmethod
    def compare(self, count, k):
        pass

    @abstractmethod
    def bound(self, encoder, lower, upper):
        pass


@register_clue('EXACTLY')
class Exactly(Count):
    word = 'Có đúng'

    def compare(self, count, k):
        # TODO(Thien): Trả về True nếu `count == k`.
        raise NotImplementedError("TODO(Thien): Cài đặt Exactly.compare() trong clues.py")

    def bound(self, encoder, lower, upper):
        # TODO(Phuc): Có đúng k <=> vừa >= k (`lower`) vừa <= k (`upper`). Dùng `encoder.gate('AND', ...)`.
        raise NotImplementedError("TODO(Phuc): Cài đặt Exactly.bound() trong clues.py")


@register_clue('AT_LEAST')
class AtLeast(Count):
    word = 'Có ít nhất'

    def compare(self, count, k):
        # TODO(Thien): Trả về True nếu `count >= k`.
        raise NotImplementedError("TODO(Thien): Cài đặt AtLeast.compare() trong clues.py")

    def bound(self, encoder, lower, upper):
        # TODO(Phuc): Có ít nhất k <=> trả về `lower`.
        raise NotImplementedError("TODO(Phuc): Cài đặt AtLeast.bound() trong clues.py")


@register_clue('AT_MOST')
class AtMost(Count):
    word = 'Có nhiều nhất'

    def compare(self, count, k):
        # TODO(Thien): Trả về True nếu `count <= k`.
        raise NotImplementedError("TODO(Thien): Cài đặt AtMost.compare() trong clues.py")

    def bound(self, encoder, lower, upper):
        # TODO(Phuc): Có nhiều nhất k <=> trả về `upper`.
        raise NotImplementedError("TODO(Phuc): Cài đặt AtMost.bound() trong clues.py")


@register_clue('COMPARISON')
class Comparison(Clue):
    region_fields = ('left', 'right')
    operators = {'=': operator.eq, '!=': operator.ne, '<': operator.lt,
                 '<=': operator.le, '>': operator.gt, '>=': operator.ge}

    def validate(self, spec, board, clues):
        if not isinstance(spec.get('op'), str) or spec['op'] not in self.operators:
            raise PuzzleError('op phải là =, !=, <, <=, > hoặc >=.')

    def evaluate(self, spec, assignment, board, clues):
        # TODO(Thien): Đếm số Criminal ở vùng `left` và vùng `right`, rồi so sánh bằng `self.operators[spec['op']]`.
        raise NotImplementedError("TODO(Thien): Cài đặt Comparison.evaluate() trong clues.py")

    def expression(self, spec, encoder, clues):
        # TODO(Phuc): Mã hóa phép so sánh số lượng Criminal giữa 2 vùng `left` và `right`:
        # - Lấy `a = encoder.thresholds(...)` cho `left` và `b = encoder.thresholds(...)` cho `right`.
        # - Viết hàm phụ `greater_equal(x, y)` biểu diễn count(x) >= count(y):
        #   count(x) >= count(y) <=> với mọi j từ 1..len(y)-1: (count(y) >= j) -> (count(x) >= j)
        #   tức là `AND` trên mọi j của `OR(negate(y[j]), at_least(x, j))`.
        # - Tính `ab = greater_equal(a, b)` (a >= b) và `ba = greater_equal(b, a)` (b >= a).
        # - Từ `ab` và `ba`, trả về biểu thức tương ứng với `op` trong ('>=', '<=', '>', '<', '=', '!=').
        raise NotImplementedError("TODO(Phuc): Cài đặt Comparison.expression() trong clues.py")

    def describe(self, spec, board, clues):
        left = clues.regions.describe(spec['left'], board)
        right = clues.regions.describe(spec['right'], board)
        return f'Số Tội phạm trong {left} {spec["op"]} số trong {right}.'

    def named_regions(self, spec, board, clues):
        return (spec['op'] in ('=', '!=')
                and len(clues.regions.resolve(spec['left'], board))
                == len(clues.regions.resolve(spec['right'], board)) == 1)


@register_clue('CONDITIONAL')
class Conditional(Clue):
    children = ('if', 'then')

    def evaluate(self, spec, assignment, board, clues):
        # TODO(Thien): Đánh giá mệnh đề kéo theo (P -> Q) <=> (not P or Q) bằng `clues.evaluate(...)`.
        raise NotImplementedError("TODO(Thien): Cài đặt Conditional.evaluate() trong clues.py")

    def expression(self, spec, encoder, clues):
        # TODO(Phuc): Mã hóa mệnh đề kéo theo (if -> then) <=> OR(negate(first), second).
        raise NotImplementedError("TODO(Phuc): Cài đặt Conditional.expression() trong clues.py")

    def describe(self, spec, board, clues):
        return f"Nếu {clues.describe(spec['if'], board)} thì {clues.describe(spec['then'], board)}"


# Semantic references shared by wording and visual inspection.

@dataclass(frozen=True)
class CluePart:
    key: str
    title: str
    cells: FrozenSet[str]
    anchors: FrozenSet[str]
    role: str
    is_region: bool = False
    named_cells: FrozenSet[str] = frozenset()


def clue_parts(spec, board, clues):
    """Semantic link keys mirror the recursive wording tree."""
    parts = []

    def region_visit(region, key, role, named_singleton=False):
        cells=clues.regions.resolve(region,board)
        parts.append(CluePart(key,clues.regions.describe(region,board),
            cells,clues.regions.anchors(region,board),role,True,
            cells if named_singleton or clues.regions.handler(region).named_cells else frozenset()))
        if named_singleton:return
        for cell in board.ordered(clues.regions.anchors(region,board)):
            parts.append(CluePart(key+'.anchor.'+cell,cell,frozenset({cell}),frozenset({cell}),'anchor',named_cells=frozenset({cell})))
        for side in clues.regions.handler(region).children:
            if side in region:
                region_visit(region[side],key+'.'+side,'a' if side=='left' else 'b')

    def visit(clue, prefix=''):
        parts.append(CluePart(prefix+'result','Kết quả',clues.cells(clue,board),clues.anchors(clue,board),'result'))
        handler=clues.handler(clue)
        for field in handler.children:
            visit(clue[field],prefix+field+'.')
        named=handler.named_regions(clue,board,clues)
        for field in handler.region_fields:
            role={'left':'a','right':'b'}.get(field,'result')
            region_visit(clue[field],prefix+field,role,named)
        for field in handler.person_fields:
            cell=clue[field]
            parts.append(CluePart(prefix+field,cell,frozenset({cell}),frozenset(),
                'b' if field=='b' else 'a',named_cells=frozenset({cell})))
    visit(spec)
    return tuple(parts)
