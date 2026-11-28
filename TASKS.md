# Phân công công việc nhóm — Project 2: Griductive Solver

Tài liệu này ghi nhận phân công nhiệm vụ, tỷ lệ hoàn thành của từng thành viên lớp **24TN** (khớp với [docs/team.json](docs/team.json) và Mục 1.1 của `Report.pdf`), chi tiết mô-đun phụ trách và lệnh kiểm tra tương ứng.

---

## 1. Bảng phân công tổng quan

| Thành viên | MSSV | Phần việc phụ trách chính | Hoàn thành |
| --- | --- | --- | ---: |
| Phan Ngọc Thức | `24120228` | Kiến trúc dự án, giao diện Desktop Cozy Harbor, thực nghiệm, báo cáo và video | 100% |
| Nguyễn Lê Minh Quân | `24120219` | Chạy thực nghiệm, so sánh hai chiến lược chọn biến (`ordered` vs `frequency`), phân tích số liệu, báo cáo và video | 100% |
| Tống Phúc Thiện | `24120141` | Hệ thống vùng (`Regions` và phép tập hợp), đánh giá ngữ nghĩa trực tiếp (`evaluate`), luồng `GameEngine` và `check_uniqueness` | 100% |
| Bùi Phương Nam | `24120502` | Bộ giải DPLL (`ordered`, `frequency`) và suy luận phản chứng của `LogicAgent` | 100% |
| Phan Gia Phúc | `24120503` | Mã hóa CNF (cổng Tseitin, quy hoạch động đếm ngưỡng unary) và biên dịch toàn bộ mẫu manh mối sang CNF | 100% |

- **Video trình diễn trên Google Drive:** [Xem video demo](https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing) (`05:33`, thuyết minh và phụ đề tiếng Việt, quyền xem công khai *Anyone with the link*).

---

## 2. Chi tiết mô-đun phụ trách theo từng thành viên

### 2.1. Bùi Phương Nam (`24120502`) — Bộ giải DPLL & Suy luận phản chứng
1. **[griductive/engine/sat.py](griductive/engine/sat.py):**
   - Cài đặt thủ tục đệ quy `search(current, assignment)` trong `solve()`:
     - Vòng lặp lan truyền mệnh đề đơn (*Unit Propagation*): kiểm tra cờ hủy/timeout, phát hiện mệnh đề rỗng `()`, thu thập mệnh đề đơn, phát hiện xung đột hai đơn vị đối dấu ($x$ và $-x$), cập nhật `stats.propagations` và rút gọn qua `simplify()`.
     - Chọn biến phân nhánh tất định theo 2 chiến lược: `"ordered"` (chỉ số nhỏ nhất) và `"frequency"` (tần suất cao nhất, hòa chọn chỉ số nhỏ hơn).
     - Phân nhánh đệ quy thử `True` rồi `False`, ghi nhận `stats.decisions`, `stats.backtracks`, `stats.runtime` và hoàn thiện mô hình cho dải biến $1 \dots m$.
2. **[griductive/engine/game.py](griductive/engine/game.py):**
   - `LogicAgent.verify(state, cell, verdict)`: kiểm tra $KB_t$ khả thỏa trước, sau đó kiểm chứng bằng phản chứng ($KB_t \land \neg\alpha$ vô nghiệm) để phân biệt `ACCEPTED`, `CONTRADICTED`, `NOT_PROVABLE` và `INCONSISTENT`.
   - `LogicAgent._verdicts(state)` và `LogicAgent.classify(state)`: phân loại toàn bộ ô chưa mở kèm lưu nhân chứng mô hình (`can_be_true`, `can_be_false`) để giảm số lần gọi SAT.

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.test_solver -v
```

---

### 2.2. Phan Gia Phúc (`24120503`) — Mã hóa CNF & Biên dịch manh mối
1. **[griductive/engine/cnf.py](griductive/engine/cnf.py):**
   - `Encoder.gate(kind, operands)`: rút gọn hằng `bool`, khử literal trùng, phát hiện cặp đối dấu, tra bảng `self.gates` để dùng chung biến phụ Tseitin và sinh các mệnh đề tương đương hai chiều cho cổng `"AND"` / `"OR"`.
   - `Encoder.thresholds(cells)`: quy hoạch động bậc đa thức $O(|R|^2)$ tính dãy ngưỡng `counts[k]` (*ít nhất $k$ tội phạm trong vùng*) trong cùng không gian biến phụ của `Encoder`.
   - `build_knowledge_base(state, registry)`: dựng $KB_t$ chỉ từ `state.clues` đã mở và mệnh đề đơn của `state.statuses` đã chứng minh.
2. **[griductive/engine/clues.py](griductive/engine/clues.py):**
   - Cài đặt `expression()` cho 6 mẫu cơ sở (`Fact`, `Same`/`Different`, `Count` + `Exactly`/`AtLeast`/`AtMost`) và 2 mẫu mở rộng (`Comparison` qua `greater_equal`, `Conditional` qua $\neg P \lor Q$).

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_rule_extensions tests.test_rule_registration -v
```

---

### 2.3. Tống Phúc Thiện (`24120141`) — Hệ thống vùng, Đánh giá ngữ nghĩa & `GameEngine`
1. **[griductive/engine/regions.py](griductive/engine/regions.py):**
   - Cài đặt `resolve()` cho 4 vùng cơ sở (`Row`, `Column`, `Neighbors` theo khoảng cách Chebyshev $\le 1$ loại trừ ô mốc, `Explicit`) và 4 vùng mở rộng (`Corners`, cùng `SetOperation.combine` cho `Union`, `Intersection`, `Difference`).
2. **[griductive/engine/clues.py](griductive/engine/clues.py):**
   - Cài đặt hàm đánh giá trực tiếp `evaluate()` / `compare()` độc lập hoàn toàn với CNF/SAT cho cả 8 kiểu manh mối.
3. **[griductive/engine/game.py](griductive/engine/game.py):**
   - Cài đặt `GameEngine.hint()` (chỉ dùng `PublicState`, không đọc nghiệm ẩn), `GameEngine.step()` và `check_uniqueness()` (kiểm tra nghiệm duy nhất ngoại tuyến bằng mệnh đề chặn chỉ trên tập biến chính).

```powershell
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_puzzle_5x5 -v
```

---

### 2.4. Phan Ngọc Thức (`24120228`) & Nguyễn Lê Minh Quân (`24120219`) — Kiến trúc, Giao diện Desktop, Thực nghiệm, Báo cáo & Video
1. **Kiến trúc, dữ liệu câu đố và giao diện Desktop ([griductive/ui/](griductive/ui/), [griductive/presentation/](griductive/presentation/), [puzzles/](puzzles/)):**
   - Thiết kế ranh giới bất biến `PublicState` / `PrivatePuzzle`, luồng nền `EngineWorker` có `fork()` và cờ hủy an toàn, bộ diễn đạt lời khai tiếng Việt [wording_vi.py](griductive/presentation/wording_vi.py), 6 màn chơi chuẩn (`3×3`, `4×4`, `5×5`) và bộ 87 bài kiểm thử tự động.
2. **Thực nghiệm, báo cáo và video ([griductive/experiments.py](griductive/experiments.py), [output/experiments/](output/experiments/)):**
   - Chạy 12 lượt thực nghiệm đối sánh `ordered` và `frequency` trên cùng 6 màn chơi (môi trường Windows 11, Python 3.14.6, CPU Intel Core i5-12450HX), xuất CSV/JSON/12 tệp trace, vẽ biểu đồ, biên soạn báo cáo LaTeX 21 trang chuẩn mẫu HCMUS (`Report.pdf`) và dựng video thuyết minh tiếng Việt.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m griductive.experiments
```
