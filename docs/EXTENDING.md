# Hướng dẫn Mở rộng Vùng (`Region`) và Manh mối (`Clue`)

Lõi suy luận trong `griductive/engine/` gồm 6 tệp: [models.py](../griductive/engine/models.py), [regions.py](../griductive/engine/regions.py), [clues.py](../griductive/engine/clues.py), [cnf.py](../griductive/engine/cnf.py), [sat.py](../griductive/engine/sat.py) và [game.py](../griductive/engine/game.py). Nhờ cơ chế đăng ký qua decorator, khi cần bổ sung một loại vùng hoặc mẫu manh mối mới, bạn chỉ cần định nghĩa lớp xử lý tại `regions.py` hoặc `clues.py` (hoặc đăng ký cục bộ cho riêng một phiên chơi) mà **không cần sửa đổi** bộ biên dịch CNF, bộ giải DPLL, `GameEngine` hay giao diện Desktop.

---

## 1. Danh mục các loại vùng và manh mối có sẵn

Trước khi viết luật mới, đối chiếu danh mục mặc định đang được đăng ký sẵn khi nạp gói `griductive.engine`:

- **8 kiểu vùng (`@register_region` trong [regions.py](../griductive/engine/regions.py)):**
  - *4 vùng cơ sở (mục 2.1 & 3.2 đề bài):* `ROW`, `COLUMN`, `NEIGHBORS`, `EXPLICIT`.
  - *4 vùng mở rộng:* `CORNERS` (4 ô góc), `UNION` ($R_1 \cup R_2$), `INTERSECTION` ($R_1 \cap R_2$), `DIFFERENCE` ($R_1 \setminus R_2$).
- **8 kiểu manh mối (`@register_clue` trong [clues.py](../griductive/engine/clues.py)):**
  - *6 mẫu cơ sở (Bảng 1 mục 3.2 đề bài):* `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`.
  - *2 mẫu mở rộng:* `COMPARISON` (so sánh số `CRIMINAL` giữa hai vùng với `=`, `!=`, `<`, `<=`, `>`, `>=`) và `CONDITIONAL` (kéo theo đệ quy `if` $\to$ `then`).

---

## 2. Thêm một loại vùng mới (`@register_region`)

Ví dụ thêm vùng biên bàn cờ `BOUNDARY` vào [regions.py](../griductive/engine/regions.py). Hai phương thức bắt buộc là `resolve()` và `describe()`:

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

Ngay sau khi đăng ký, vùng mới dùng được trực tiếp trong mọi manh mối đếm, phép so sánh hoặc phép toán tập hợp có sẵn:

```json
{
  "type": "EXACTLY",
  "k": 2,
  "region": {"type": "BOUNDARY"}
}
```

### Quy ước cho lớp kế thừa `Region`
- `RegionRegistry.resolve()` tự động kiểm tra mọi mã ô do `resolve()` trả về có nằm trên `board` hay không và chuyển kết quả thành `frozenset`.
- Nếu vùng có ô mốc tham chiếu (như `NEIGHBORS`), khai báo `anchor_fields = ('cell',)`: ô mốc sẽ được kiểm tra hợp lệ và đánh dấu vai trò `anchor` khi giao diện tô sáng, nhưng chỉ được đếm vào tổng tội phạm nếu chính `resolve()` trả về ô đó.
- Nếu là vùng tổ hợp đệ quy, khai báo `children = ('left', 'right')` và gọi `regions.resolve(spec['left'], board, depth + 1)` để duy trì giới hạn lồng tối đa **12 cấp**.
- Đặt `named_cells = True` nếu vùng liệt kê trực tiếp danh sách nghi phạm cụ thể (như `EXPLICIT`).

---

## 3. Thêm một mẫu manh mối mới (`@register_clue`)

Ví dụ thêm mẫu `ALL_INNOCENT` (*mọi người trong vùng đều vô tội*) vào [clues.py](../griductive/engine/clues.py). Ba phương thức bắt buộc là `evaluate()`, `expression()` và `describe()`:

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

Manh mối mới tự động kết hợp được với vùng mới và lồng bên trong `CONDITIONAL`:

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

### Hai nguyên tắc bất biến khi cài đặt `Clue`
1. **Tách rời ngữ nghĩa và mã hóa CNF (mục 4.2 đề bài):** `evaluate()` nhận phép gán đầy đủ `{'A1': True, 'B1': False, ...}` và phải tính chân trị trực tiếp bằng logic Python thuần — **tuyệt đối không gọi `Encoder` hay bộ giải SAT** từ bên trong `evaluate()`.
2. **Dùng chung không gian biến phụ Tseitin:** `expression()` trả về một literal số nguyên (hoặc hằng `bool`) thông qua đối tượng `encoder` được truyền vào (`encoder.gate('AND' | 'OR', ...)`, `encoder.negate(...)`, `encoder.thresholds(cells)`). Không khởi tạo `Encoder` riêng lẻ cho từng biểu thức con của cùng một $KB_t$.

---

## 4. Khai báo metadata tham chiếu và kiểm tra tham số

| Thuộc tính lớp `Clue` | Tác dụng tự động từ `ClueRegistry` |
| --- | --- |
| `region_fields = ('region',)` | Kiểm tra tính hợp lệ của vùng và tự động đưa các ô vào danh sách tô sáng (`cells()`, `clue_parts()`). |
| `person_fields = ('a', 'b')` | Kiểm tra tọa độ ô trên bàn cờ và sinh tham chiếu tô sáng cho từng người. |
| `children = ('if', 'then')` | Kiểm tra đệ quy các manh mối con (tối đa 12 cấp) và ghép tiền tố khóa tham chiếu tự động. |

Nhờ các thuộc tính trên, lớp mới không cần viết lại hàm duyệt ô. Nếu manh mối có tham số riêng (ví dụ số nguyên `k` hoặc toán tử `op`), ghi đè `validate(self, spec, board, clues)` và ném `PuzzleError` khi tham số không hợp lệ (các trường trong metadata luôn được kiểm tra trước khi gọi `validate`).

---

## 5. Sinh câu tiếng Việt có liên kết tô sáng (`wording`)

Phương thức `wording(self, spec, text)` là tùy chọn: nếu lược bỏ, giao diện dùng chuỗi từ `describe()` và vẫn tô sáng đầy đủ các ô dựa trên metadata. Khi cài đặt `wording()`, đối tượng `RuleText` trong [wording_vi.py](../griductive/presentation/wording_vi.py) cung cấp các helper dùng chung cho cả văn bản thuần và HTML (tự động escape ký tự đặc biệt và nối tiền tố khi lồng trong `CONDITIONAL`):

| Helper | Công dụng |
| --- | --- |
| `text.region(region_spec, key='region', role='result')` | Sinh cụm từ mô tả vùng có liên kết hover/ghim trên thẻ. |
| `text.person(cell, key, role)` | Sinh tên nhân vật có liên kết tới ô tương ứng. |
| `text.token(key, value)` | Sinh đoạn chữ thường (tự động escape HTML). |
| `text.token(key, value, role, True)` | Sinh đoạn chữ màu có liên kết tới khóa `key`. |
| `text.child(clue_spec, field)` | Dựng câu cho manh mối con với tiền tố `if.` hoặc `then.` chính xác. |

Trong đó `key` khớp với tên trường metadata (`region`, `left`, `right`, `person`, `a`, `b`), còn `role` chọn bảng màu ngữ nghĩa (`result`, `a`, `b`, `anchor`). Một lớp `Region` cũng có thể định nghĩa `wording(self, spec, text, key, role)` kèm `anchor_fields = ('cell',)` — xem ví dụ hoàn chỉnh `Cross` và `AllInnocent` trong [test_rule_registration.py](../tests/test_rule_registration.py).

---

## 6. Đăng ký cục bộ cho riêng một phiên chơi hoặc bài kiểm thử

`@register_region` và `@register_clue` đăng ký vào catalog mặc định lúc nạp module. Nếu chỉ muốn thử nghiệm luật mới trong một phiên chơi hoặc một unit test mà không làm thay đổi catalog toàn cục, hãy đăng ký trực tiếp trên thực thể registry:

```python
from griductive.engine import (
    Region, Clue, region_registry, clue_registry, load_puzzle, GameEngine,
)

regions = region_registry()
clues = clue_registry(regions)

# Dùng @regions.register('NAME') và @clues.register('NAME') trên catalog cục bộ
puzzle = load_puzzle('puzzles/case-3x3-01.json', clues)
engine = GameEngine(puzzle, clues)
```

- Tên trùng lặp hoặc đối tượng không kế thừa `Region`/`Clue` sẽ bị từ chối ngay lúc đăng ký.
- Giữ các thực thể luật hoàn toàn **không trạng thái (*stateless*)**: đọc mọi tham số từ `spec`, không lưu dữ liệu của từng màn vào `self`.

---

## 7. Kiểm tra sau khi thêm luật mới

Chạy kiểm thử tự động và thực nghiệm từ thư mục gốc (hoặc thư mục `Source/`):

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m griductive.experiments
```

```bash
# macOS / Linux
./.venv/bin/python -B -m unittest discover -s tests -v
./.venv/bin/python -B -m griductive.experiments
```

Khi viết unit test cho luật mới (xem mẫu tại [test_rule_extensions.py](../tests/test_rule_extensions.py) và [test_rule_registration.py](../tests/test_rule_registration.py)), hãy kiểm tra đủ 5 khía cạnh: (1) từ chối tham số sai bằng `PuzzleError`, (2) trường hợp vùng biên/rỗng, (3) tính tương đương vét cạn giữa `evaluate()` và khả thỏa CNF khi cố định biến chính, (4) lồng bên trong `CONDITIONAL`, và (5) sự ăn khớp của các khóa `clue_parts()` với liên kết HTML.
