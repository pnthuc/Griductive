# Thêm region và clue

Engine có sáu file: `models.py`, `regions.py`, `clues.py`, `cnf.py`, `sat.py`,
`game.py`. Thêm luật ở `regions.py` hoặc `clues.py`; giữ các hàm liên quan trong
cùng một lớp. Compiler, solver, game và GUI không cần biết tên loại mới.

## 1. Thêm region

Ví dụ vùng biên: thêm lớp dưới đây vào `griductive/engine/regions.py`.
Hai hàm cần viết là `resolve()` và `describe()`.

```python
@register_region('BOUNDARY')
class Boundary(Region):
    def resolve(self, spec, board, regions, depth):
        last = board.size - 1
        return {
            cell for cell in board.cells
            if any(index in (0, last) for index in board.position(cell))
        }

    def describe(self, spec, board, regions):
        return 'những người ở biên bàn'
```

Dùng ngay trong clue đếm có sẵn:

```json
{
  "type": "EXACTLY",
  "k": 2,
  "region": {"type": "BOUNDARY"}
}
```

Registry kiểm tra các ô mà `resolve()` trả về. Nếu vùng có ô mốc, khai báo
`anchor_fields = ('cell',)`: ô đó được kiểm tra và ghi vào metadata highlight,
nhưng chỉ được đếm nếu chính `resolve()` trả về nó.

Vùng ghép khai báo `children = ('left', 'right')`. Trong `resolve()`, gọi
`regions.resolve(spec['left'], board, depth + 1)` và tương tự cho vế phải.
Truyền `depth + 1` để giữ giới hạn lồng 12 cấp. `named_cells = True` dành cho
vùng liệt kê trực tiếp người, như EXPLICIT.

## 2. Thêm clue

Ví dụ mọi người trong vùng đều vô tội: thêm vào `griductive/engine/clues.py`.
Ba hàm bắt buộc là `evaluate()`, `expression()` và `describe()`.

```python
@register_clue('ALL_INNOCENT')
class AllInnocent(Clue):
    region_fields = ('region',)

    def evaluate(self, spec, assignment, board, clues):
        cells = clues.regions.resolve(spec['region'], board)
        return all(not assignment[cell] for cell in cells)

    def expression(self, spec, encoder, clues):
        cells = clues.regions.resolve(spec['region'], encoder.board)
        return encoder.gate(
            'AND', (-encoder.variables[cell] for cell in cells)
        )

    def describe(self, spec, board, clues):
        region = clues.regions.describe(spec['region'], board)
        return region + ' đều vô tội.'

    def wording(self, spec, text):
        return text.region(spec['region']) + ' đều vô tội.'
```

`wording()` tùy chọn. Nếu bỏ, giao diện dùng `describe()` làm mô tả, và vẫn
highlight các ô dựa trên metadata. Nếu thêm như ví dụ, đoạn chữ chỉ vùng còn
có liên kết hover/click đúng với highlight. Cùng một hàm dùng được cho câu
thường và HTML, kể cả khi clue nằm trong CONDITIONAL.

Clue mới có thể dùng vùng mới và lồng trong clue có sẵn:

```json
{
  "type": "CONDITIONAL",
  "if": {"type": "FACT", "person": "A1", "status": "CRIMINAL"},
  "then": {
    "type": "ALL_INNOCENT",
    "region": {"type": "BOUNDARY"}
  }
}
```

Evaluator nhận assignment đầy đủ dạng `{'A1': True, 'B1': False, ...}`.
Không gọi encoder/SAT từ evaluator: hai đường độc lập để kiểm tra chéo.
`expression()` trả về literal số nguyên hoặc hằng bool, và chỉ dùng encoder
được truyền vào. Không tạo Encoder riêng cho từng phần của cùng một KB.

## 3. Metadata thay cho các callback lặp lại

| Khai báo trong lớp Clue | Registry tự làm |
|---|---|
| `region_fields = ('region',)` | Kiểm tra vùng và đưa các ô vào tham chiếu highlight |
| `person_fields = ('a', 'b')` | Kiểm tra tọa độ người và tạo tham chiếu từng người |
| `children = ('if', 'then')` | Kiểm tra clue con và duyệt tham chiếu đệ quy |

Không cần tự viết `cells()` cho các trường hợp trên. Nếu có tham số bổ sung,
viết `validate(self, spec, board, clues)` để kiểm tra chúng; các trường đã khai
báo ở metadata được kiểm tra trước. Ném `PuzzleError` khi tham số không hợp lệ.
Xem `Fact`, `Count`, `Comparison`, `Conditional` để tham khảo các luật có sẵn.

## 4. Câu chữ có liên kết

Các helper của `text` xử lý tên, escape HTML và tiền tố của clue lồng:

| Helper | Cách dùng |
|---|---|
| `text.region(region_spec, key='region', role='result')` | Mô tả một vùng có liên kết |
| `text.person(cell, key, role)` | Tên người có liên kết |
| `text.token(key, value)` | Chữ thường, tự escape trong HTML |
| `text.token(key, value, role, True)` | Chữ có liên kết |
| `text.child(clue_spec, field)` | Render clue con với prefix đúng |

`key` trùng tên trường metadata: `region`, `left`, `right`, `person`, `a`, `b`.
Role màu là `result`, `a`, `b`, `anchor`. Không tự thêm prefix `if.` hay
`then.`: các helper đã làm việc đó.

Region có thể thêm `wording(self, spec, text, key, role)` trong chính lớp của
nó. Ví dụ, vùng quanh một người có thể dùng:

```python
def wording(self, spec, text, key, role):
    return (
        text.token(key, 'những người quanh ', role, True)
        + text.person(spec['cell'], key + '.anchor.' + spec['cell'], 'anchor')
    )
```

Khai báo `anchor_fields = ('cell',)` cho ví dụ này để liên kết ô mốc có metadata
tương ứng. Xem `tests/test_rule_registration.py` cho một ví dụ chạy hoàn chỉnh.

## 5. Catalog mặc định và đăng ký riêng

`@register_region` và `@register_clue` đăng ký vào catalog mặc định lúc module
được import. Không cần thêm tên lớp vào danh sách hoặc hàm factory.
Nếu định nghĩa ở module riêng, import module đó trước khi tạo registry.

Để đăng ký chỉ cho một phiên hoặc một test, dùng cùng cú pháp trên registry:

```python
from griductive.engine import (
    Region, Clue, region_registry, clue_registry, load_puzzle, GameEngine,
)

regions = region_registry()
clues = clue_registry(regions)

# Dùng @regions.register('NAME') trên lớp Region riêng.
# Dùng @clues.register('NAME') trên lớp Clue riêng.

puzzle = load_puzzle('puzzles/case-3x3-01.json', clues)
engine = GameEngine(puzzle, clues)
```

Cũng hỗ trợ `regions.register('NAME', MyRegion)` hoặc một instance. Tên trùng
bị từ chối. Catalog mới không nhận các đăng ký local của catalog khác.
Mỗi registry là một bản chụp catalog tại lúc tạo; đăng ký global sau đó chỉ
xuất hiện trong những registry tạo sau. Các instance luật phải không giữ
trạng thái phiên: lấy tham số từ `spec`, không gán dữ liệu puzzle vào `self`.

## 6. Kiểm tra sau khi thêm luật

Chạy từ thư mục project trên Windows:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
.\.venv\Scripts\python.exe -B -m griductive.experiments
```

Với luật mới, kiểm tra tham số sai, trường hợp biên, evaluator so với khả thỏa
CNF khi cố định biến chính, lồng CONDITIONAL và các key của text/highlight.
Giữ nguyên điều kiện agent chỉ nhận thông tin công khai và không đoán.
