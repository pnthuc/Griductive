"""Region definitions. Add a class with @register_region; no compiler changes."""
from abc import ABC, abstractmethod
from collections.abc import Mapping
from .models import Board, PuzzleError


class Region(ABC):
    """Resolve cells and describe them. Metadata supplies reference traversal."""
    children = ()
    anchor_fields = ()
    named_cells = False

    @abstractmethod
    def resolve(self, spec, board, regions, depth):
        """Return cell IDs; recurse with regions.resolve(..., depth + 1)."""

    @abstractmethod
    def describe(self, spec, board, regions):
        """Return a plain description, also used by the default text renderer."""

    def wording(self, spec, text, key, role):
        """Optionally return text/HTML using text.token/person/region helpers."""
        return None


class RegionRegistry:
    def __init__(self):
        self.handlers = {}

    def register(self, name, rule=None):
        """Register an instance/class, or use @regions.register('NAME')."""
        def install(definition):
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Tên region phải là chuỗi không rỗng.')
            if name in self.handlers:
                raise ValueError(f'Region đã đăng ký: {name}')
            instance = definition() if isinstance(definition, type) else definition
            if not isinstance(instance, Region):
                raise TypeError('Region phải kế thừa lớp Region.')
            self.handlers[name] = instance
            return definition
        return install if rule is None else install(rule)

    def handler(self, spec):
        if not isinstance(spec, Mapping):
            raise PuzzleError('Region phải là một object.')
        kind = spec.get('type')
        if not isinstance(kind, str) or kind not in self.handlers:
            raise PuzzleError(f'Không hỗ trợ region: {kind!r}')
        return self.handlers[kind]

    def resolve(self, spec, board, depth=0):
        if depth > 12:
            raise PuzzleError('Region lồng quá 12 cấp.')
        rule = self.handler(spec)
        for field in rule.anchor_fields:
            board.position(spec.get(field))
        result = frozenset(rule.resolve(spec, board, self, depth))
        for cell in result:
            board.position(cell)
        return result

    def describe(self, spec, board):
        self.resolve(spec, board)
        return self.handler(spec).describe(spec, board, self)

    def anchors(self, spec, board):
        self.resolve(spec, board)
        rule = self.handler(spec)
        cells = {spec[field] for field in rule.anchor_fields}
        for field in rule.children:
            cells.update(self.anchors(spec[field], board))
        return frozenset(cells)


_DEFAULT_REGIONS = RegionRegistry()
register_region = _DEFAULT_REGIONS.register


def region_registry():
    """Return an independent catalog of the definitions registered at import."""
    registry = RegionRegistry()
    registry.handlers = dict(_DEFAULT_REGIONS.handlers)
    return registry


@register_region('ROW')
class Row(Region):
    def resolve(self, spec, board, regions, depth):
        number = spec.get('row')
        if type(number) is not int or not 1 <= number <= board.size:
            raise PuzzleError('row phải là số nguyên trong phạm vi bàn.')

        rows = []
        for i in range(board.size):
            rows.append(f'{chr(i + 65)}{number}')

        return rows

    def describe(self, spec, board, regions):
        return f'hàng {spec["row"]}'


@register_region('COLUMN')
class Column(Region):
    def resolve(self, spec, board, regions, depth):
        letter = spec.get('column')
        columns = tuple(chr(65 + index) for index in range(board.size))
        if not isinstance(letter, str) or letter not in columns:
            raise PuzzleError('column phải là chữ cột hợp lệ, ví dụ A.')

        cols = []
        for i in range(board.size):
            cols.append(f'{letter}{i + 1}')

        return cols

    def describe(self, spec, board, regions):
        return f'cột {spec["column"]}'


@register_region('NEIGHBORS')
class Neighbors(Region):
    anchor_fields = ('cell',)

    def resolve(self, spec, board, regions, depth):
        row, column = board.position(spec['cell'])
        neighbors = []
        for i in range(row - 1, row + 2):
            for j in range(column - 1, column + 2):
                if 0 <= i < board.size and 0 <= j < board.size and (i, j) != (row, column):
                    neighbors.append(f'{chr(65 + j)}{i + 1}')

        return neighbors

    def describe(self, spec, board, regions):
        return f'hàng xóm của {spec["cell"]}'


@register_region('EXPLICIT')
class Explicit(Region):
    named_cells = True

    def resolve(self, spec, board, regions, depth):
        cells = spec.get('cells')
        if not isinstance(cells, (list, tuple)):
            raise PuzzleError('cells phải là danh sách ô.')
        for cell in cells:
            board.position(cell)
        if len(set(cells)) != len(cells):
            raise PuzzleError('EXPLICIT không được chứa ô trùng.')
        
        return cells

    def describe(self, spec, board, regions):
        return 'nhóm [' + ', '.join(spec['cells']) + ']'


@register_region('CORNERS')
class Corners(Region):
    def resolve(self, spec, board, regions, depth):
        last_col = chr(65 + board.size - 1)
        last_row = board.size
        
        return [
            'A1',
            f'{last_col}1',
            f'A{last_row}',
            f'{last_col}{last_row}',
        ]

    def describe(self, spec, board, regions):
        return 'bốn ô góc'


class SetOperation(Region):
    children = ('left', 'right')

    def resolve(self, spec, board, regions, depth):
        left = regions.resolve(spec.get('left'), board, depth + 1)
        right = regions.resolve(spec.get('right'), board, depth + 1)
        return self.combine(left, right)

    def describe(self, spec, board, regions):
        left = regions.describe(spec['left'], board)
        right = regions.describe(spec['right'], board)
        return f'{self.word} của ({left}) và ({right})'

    @abstractmethod
    def combine(self, left, right):
        pass


@register_region('UNION')
class Union(SetOperation):
    word = 'hợp'

    def combine(self, left, right):
        return left | right


@register_region('INTERSECTION')
class Intersection(SetOperation):
    word = 'giao'

    def combine(self, left, right):
        return left & right


@register_region('DIFFERENCE')
class Difference(SetOperation):
    word = 'hiệu'

    def combine(self, left, right):
        return left - right
