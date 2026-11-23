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
        # TODO(Phuc): Cài đặt cổng logic Tseitin cho `kind` ("AND" hoặc "OR") trên tập `operands`.
        #
        # Input:
        #   - `kind`: chuỗi `"AND"` hoặc `"OR"`.
        #   - `operands`: iterable chứa các literal (int != 0) hoặc hằng `bool` (`True`/`False`).
        #
        # Các bước cần thực hiện:
        # 1. Rút gọn hằng số và literal trùng / đối ngẫu:
        #    - Đặt `identity = (kind == "AND")` (phần tử trung hòa: True với AND, False với OR).
        #    - Duyệt `value` trong `operands`:
        #        + Nếu `type(value) is bool`:
        #            * Nếu `value != identity` (gặp False trong AND, hoặc True trong OR) -> trả về ngay `value`.
        #            * Nếu `value == identity` -> bỏ qua.
        #        + Nếu `value` là literal (int):
        #            * Nếu `-value` đã nằm trong tập `values` (có cả x và ~x) -> trả về `not identity`
        #              (False cho AND, True cho OR).
        #            * Thêm `value` vào tập `values`.
        # 2. Trường hợp suy biến:
        #    - Nếu `values` rỗng -> trả về `identity`.
        #    - Nếu `len(values) == 1` -> trả về phần tử duy nhất trong `values` (không tạo biến phụ).
        # 3. Memoization & tạo biến phụ Tseitin:
        #    - Chuẩn hóa `inputs = tuple(sorted(values))`, `key = (kind, inputs)`.
        #    - Nếu `key` đã có trong `self.gates` -> trả về `self.gates[key]`.
        #    - Cấp phát biến phụ mới: `out = self.next_variable`, tăng `self.next_variable += 1`,
        #      lưu `self.gates[key] = out`.
        # 4. Sinh các mệnh đề tương đương Tseitin (out <-> AND(inputs) hoặc out <-> OR(inputs)):
        #    - Nếu `kind == "AND"`:
        #        + Với mỗi `v` trong `inputs`: thêm clause `(-out, v)`
        #        + Thêm clause `(out,) + tuple(-v for v in inputs)`
        #    - Nếu `kind == "OR"`:
        #        + Với mỗi `v` trong `inputs`: thêm clause `(out, -v)`
        #        + Thêm clause `(-out,) + inputs`
        #    - Trả về biến phụ `out`.
        raise NotImplementedError("TODO(Phuc): Cài đặt Encoder.gate() trong cnf.py")

    def thresholds(self, cells):
        # TODO(Phuc): Cài đặt bộ đếm ngưỡng quy hoạch động (unary threshold counter) cho tập ô `cells`.
        #
        # Mục tiêu:
        #   Trả về danh sách `counts` độ dài `len(cells) + 1`, trong đó `counts[k]` là literal (hoặc bool)
        #   biểu diễn mệnh đề: "Có ít nhất k ô trong `cells` là CRIMINAL (True)".
        #
        # Gợi ý quy hoạch động:
        #   - Lấy `values = tuple(self.variables[cell] for cell in self.board.ordered(cells))`.
        #   - Dùng `self.counts` để cache theo key `values`.
        #   - Khởi tạo `previous = [True]` (ít nhất 0 ô True luôn đúng).
        #   - Duyệt từng biến `value` trong `values`:
        #       Cập nhật danh sách ngưỡng mới có độ dài `len(previous) + 1`:
        #       + Phần tử 0 luôn là `True`.
        #       + Với mỗi `j` từ `1` đến `len(previous)`:
        #         "Ít nhất j ô đúng sau khi xét thêm `value`"
        #         = OR(đã có ít nhất j ô đúng trước đó, AND(`value` đúng, đã có ít nhất j-1 ô đúng trước đó))
        #         (Lưu ý: nếu `j == len(previous)` thì nhánh "đã có ít nhất j ô đúng trước đó" là `False`).
        #   - Lưu vào `self.counts[values]` và trả về.
        raise NotImplementedError("TODO(Phuc): Cài đặt Encoder.thresholds() trong cnf.py")

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
    # TODO(Phuc): Xây dựng KnowledgeBase (CNF) từ trạng thái công khai `state` (PublicState).
    #
    # Các bước cần thực hiện:
    # 1. Khởi tạo `encoder = Encoder(state.board)`.
    # 2. Duyệt từng `cell` theo thứ tự `state.board.cells`:
    #    - Nếu `cell` có trong `state.clues` (manh mối đã mở): gọi `encoder.add(state.clues[cell], registry)`.
    #    - Nếu `cell` có trong `state.statuses` (ô đã biết trạng thái):
    #        + Lấy `variable = encoder.variables[cell]`.
    #        + Thêm unit clause `(variable,)` nếu `state.statuses[cell] == "CRIMINAL"`,
    #          ngược lại thêm `(-variable,)`.
    # 3. Trả về `encoder.finish()`.
    raise NotImplementedError("TODO(Phuc): Cài đặt build_knowledge_base() trong cnf.py")
