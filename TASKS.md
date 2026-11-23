# Phân Công Công Việc Nhóm — Project 2: Griductive (Clues by Sam)

Tài liệu này hướng dẫn chi tiết phần việc của từng thành viên trong nhóm. Toàn bộ phần khung dự án (UI Desktop/Web, dữ liệu Puzzle, bộ Unit Test) đã được chuẩn bị sẵn. Các thành viên phụ trách phần thuật toán lõi trong `griductive/engine/` tìm đúng tag `TODO` theo tên mình, cài đặt code vào chỗ `raise NotImplementedError(...)` và chạy lệnh test tương ứng để kiểm tra.

---

## 1. Bảng Phân Công Tổng Quan

| Thành viên | MSSV | Phụ trách chính | Tag tìm kiếm trong code |
| --- | --- | --- | --- |
| **Bùi Phương Nam** | `24120502` | SAT Solver (DPLL) & Suy luận phản chứng (`LogicAgent`) | `TODO(Nam)` |
| **Phan Gia Phúc** | `24120503` | Mã hóa CNF (Tseitin, Unary Threshold Counter) & Biểu diễn Clue sang CNF | `TODO(Phuc)` |
| **Tống Phúc Thiện** | `24120141` | Vùng bàn cờ (`Regions`), Ngữ nghĩa/Đánh giá Clue (`evaluate`) & Luồng `GameEngine` | `TODO(Thien)` |
| **Phan Ngọc Thức** | `24120228` | Thực nghiệm (`experiments.py`), Báo cáo (`REPORT.md` / `Report.pdf`), Video Demo | — |
| **Nguyễn Lê Minh Quân** | `24120219` | Thực nghiệm, Phân tích kết quả 2 heuristic, Báo cáo & Video Demo | — |

---

## 2. Chi Tiết Nhiệm Vụ Từng Thành Viên

### 🔹 Phần 1: Bùi Phương Nam (`TODO(Nam)`) — SAT Solver & Suy Luận Phản Chứng

Nam phụ trách bộ giải DPLL và cơ chế chứng minh một ô là `CRIMINAL` / `INNOCENT` bằng phản chứng ($\text{KB} \land \neg \alpha \models \perp$).

1. **File `griductive/engine/sat.py`**:
   - **`search(current, assignment)`** (bên trong hàm `solve`):
     - Thực hiện vòng lặp **Unit Propagation**: phát hiện mệnh đề rỗng `()`, tìm unit clauses (`len(clause) == 1`), gán giá trị biến, cộng `stats.propagations += 1`, và rút gọn danh sách mệnh đề `current`.
     - Chọn biến phân nhánh theo 2 heuristic:
       - `"ordered"`: chọn biến chưa gán có chỉ số nhỏ nhất.
       - `"frequency"`: chọn biến xuất hiện nhiều nhất trong các mệnh đề hiện tại (nếu bằng nhau chọn chỉ số nhỏ hơn).
     - Tăng `stats.decisions += 1`, thử gán `True` rồi `False` (đệ quy), nếu nhánh thất bại thì tăng `stats.backtracks += 1`.
2. **File `griductive/engine/game.py`**:
   - **`LogicAgent.verify(self, state, cell, verdict)`**:
     - Tạo Knowledge Base từ `state`. Nếu bản thân KB đã `UNSAT` thì trả về `'INCONSISTENT', kb`.
     - Kiểm tra phản chứng bằng cách truyền `assumptions=(-proposed,)` rồi `(proposed,)` vào `self.query(...)` để trả về `'ACCEPTED'`, `'CONTRADICTED'`, hoặc `'NOT_PROVABLE'`.
   - **`LogicAgent.classify(self, state)`**:
     - Phân loại mọi ô chưa mở trên bàn cờ thành `"CRIMINAL"`, `"INNOCENT"`, `"UNKNOWN"`, hoặc `"INCONSISTENT"`.

**Lệnh chạy test kiểm tra riêng phần của Nam:**
```bash
python -m unittest tests.test_solver
```

---

### 🔹 Phần 2: Phan Gia Phúc (`TODO(Phuc)`) — Mã Hóa CNF & Chuyển Đổi Clue Sang CNF

Phúc phụ trách chuyển đổi các biểu thức logic và phép đếm số lượng sang dạng chuẩn hội (CNF) sử dụng biến phụ Tseitin và quy hoạch động đếm ngưỡng.

1. **File `griductive/engine/cnf.py`**:
   - **`Encoder.gate(self, kind, operands)`**:
     - Rút gọn các hằng `bool` (`True`/`False`), loại bỏ literal trùng, phát hiện cặp đối ngẫu (`v` và `-v`).
     - Dùng `self.gates` để tránh tạo trùng biến phụ cho cùng một cổng `(kind, inputs)`.
     - Cấp phát biến phụ `out` và sinh các mệnh đề tương đương Tseitin cho cổng `"AND"` hoặc `"OR"`.
   - **`Encoder.thresholds(self, cells)`**:
     - Quy hoạch động tính danh sách ngưỡng `counts` cho tập ô `cells`, trong đó `counts[k]` biểu diễn mệnh đề *"có ít nhất $k$ ô trong `cells` là Criminal"*.
   - **`build_knowledge_base(state, registry)`**:
     - Khởi tạo `Encoder`, nạp toàn bộ `state.clues` (các manh mối đã mở) và `state.statuses` (các ô đã biết trạng thái dưới dạng unit clause) rồi trả về `encoder.finish()`.
2. **File `griductive/engine/clues.py`**:
   - Cài đặt các phương thức mã hóa CNF cho từng loại manh mối:
     - `Fact.expression`
     - `Same.expression` (dùng chung cho cả `SAME` và `DIFFERENT`)
     - `Count.expression`, `Exactly.bound`, `AtLeast.bound`, `AtMost.bound`
     - `Comparison.expression` (so sánh số lượng Criminal giữa 2 vùng bằng `greater_equal`)
     - `Conditional.expression` (mệnh đề kéo theo $P \rightarrow Q \equiv \neg P \lor Q$)

**Lệnh chạy test kiểm tra phần của Phúc (sau khi Thiện xong `regions.py` hoặc kết hợp cùng Thiện):**
```bash
python -m unittest tests.test_core tests.test_rule_extensions
```

---

### 🔹 Phần 3: Tống Phúc Thiện (`TODO(Thien)`) — Regions, Clue Evaluation & Game Engine

Thiện phụ trách hệ thống xác định vùng trên bàn cờ, đánh giá trực tiếp tính đúng/sai của manh mối trên một nghiệm, và điều phối luồng chơi.

1. **File `griductive/engine/regions.py`**:
   - Cài đặt phương thức `resolve()` cho các loại vùng cơ bản:
     - `Row.resolve` (hàng $1 \dots N$)
     - `Column.resolve` (cột $A, B, \dots$)
     - `Neighbors.resolve` (8 ô lân cận Chebyshev distance $\le 1$)
     - `Explicit.resolve` (danh sách ô liệt kê tường minh)
     - `Corners.resolve` (4 ô góc bàn cờ)
   - Cài đặt `combine(self, left, right)` cho 3 phép toán tập hợp:
     - `Union.combine` (`|`), `Intersection.combine` (`&`), `Difference.combine` (`-`)
2. **File `griductive/engine/clues.py`**:
   - Cài đặt phương thức đánh giá trực tiếp `evaluate()` / `compare()` (không qua SAT):
     - `Fact.evaluate`, `Same.evaluate`
     - `Count.evaluate`, `Exactly.compare`, `AtLeast.compare`, `AtMost.compare`
     - `Comparison.evaluate`
     - `Conditional.evaluate`
3. **File `griductive/engine/game.py`**:
   - `GameEngine.hint()` và `GameEngine.step()`
   - `check_uniqueness(puzzle, registry, heuristic, timeout)`: kiểm tra một puzzle có nghiệm duy nhất trên tập biến chính bằng kỹ thuật thêm mệnh đề chặn (*blocking clause*).

**Lệnh chạy test kiểm tra phần của Thiện:**
```bash
python -m unittest tests.test_core tests.test_puzzle_5x5
```

---

### 🔹 Phần 4: Phan Ngọc Thức & Nguyễn Lê Minh Quân — Thực Nghiệm, Báo Cáo & Video

1. Sau khi Nam, Phúc, Thiện hoàn tất và pass toàn bộ unit test:
   ```bash
   python -m unittest discover -s tests
   ```
2. Chạy script thực nghiệm so sánh 2 heuristic (`ordered` vs `frequency`) trên toàn bộ 6 puzzle ($3\times 3$, $4\times 4$, $5\times 5$):
   ```bash
   python -m griductive.experiments
   ```
3. Tổng hợp bảng số liệu (`decisions`, `propagations`, `backtracks`, `runtime`), hoàn thiện báo cáo và quay video demo.

---

## 3. Quy Trình Làm Việc Với Git

1. Pull code mới nhất từ nhánh `main`:
   ```bash
   git pull origin main
   ```
2. Tìm tất cả các vị trí `TODO` của mình (ví dụ trong VS Code nhấn `Ctrl+Shift+F` và gõ `TODO(Nam)`, `TODO(Phuc)`, hoặc `TODO(Thien)`).
3. Sau khi điền code và chạy pass các bài test liên quan, commit và push phần việc của mình:
   ```bash
   git add griductive/engine/
   git commit -m "Implement <tên phần việc của bạn>"
   git push origin main
   ```
