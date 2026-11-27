# Phân công công việc nhóm — Project 2: Griductive Solver

Tài liệu này ghi nhận phân công nhiệm vụ, tỷ lệ hoàn thành của từng thành viên lớp **24TN** (khớp với [docs/team.json](docs/team.json) và mục 1.1 của báo cáo kỹ thuật `Report.pdf`), chi tiết các mô-đun đã bàn giao và lệnh kiểm chứng tương ứng theo mục **4.6** của đề bài `AI - Project 2.pdf`.

---

## 1. Bảng phân công tổng quan và tỷ lệ hoàn thành

Công thức tính điểm cá nhân theo đề bài: $\text{Điểm cá nhân} = \text{Điểm nhóm} \times \text{Tỷ lệ hoàn thành}$. Với mức hoàn thành **100%** ở cả 5 thành viên, mỗi thành viên nhận trọn điểm nhóm.

| Thành viên | MSSV | Phần việc phụ trách chính | Tỷ lệ hoàn thành | Trạng thái & Commit tiêu biểu |
| --- | --- | --- | ---: | --- |
| **Phan Ngọc Thức** | `24120228` | Kiến trúc dự án, giao diện Desktop Cozy Harbor, thực nghiệm, báo cáo & video demo | 100% | Hoàn thành (`8a64909`, `65a0f41`) |
| **Nguyễn Lê Minh Quân** | `24120219` | Thực nghiệm hệ thống, phân tích so sánh 2 heuristic (`ordered` vs `frequency`), báo cáo kỹ thuật & video demo | 100% | Hoàn thành (`aada27b`) |
| **Tống Phúc Thiện** | `24120141` | Hệ thống vùng (`Regions` & phép toán tập hợp), đánh giá ngữ nghĩa trực tiếp (`evaluate`) & luồng `GameEngine` / `check_uniqueness` | 100% | Hoàn thành (`a56b700`) |
| **Bùi Phương Nam** | `24120502` | Bộ giải DPLL SAT Solver (`ordered` & `frequency`) & suy luận phản chứng `LogicAgent` | 100% | Hoàn thành (`edcd1c8`) |
| **Phan Gia Phúc** | `24120503` | Mã hóa CNF (cổng Tseitin, quy hoạch động đếm ngưỡng unary) & biểu diễn toàn bộ `Clue` sang CNF | 100% | Hoàn thành (`79718c2`) |

> **Video trình diễn trên Google Drive (mục 4.7):** [https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing](https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing) (`05:33`, thuyết minh và phụ đề tiếng Việt, quyền xem công khai *Anyone with the link*).

---

## 2. Chi tiết mô-đun bàn giao theo từng thành viên

### 2.1. Bùi Phương Nam (`24120502`) — Bộ giải DPLL & Suy luận Phản chứng
1. **Tệp [griductive/engine/sat.py](griductive/engine/sat.py):**
   - Cài đặt thủ tục đệ quy `search(current, assignment)` bên trong `solve()`:
     - Vòng lặp **Unit Propagation**: kiểm tra cờ hủy/timeout, phát hiện mệnh đề rỗng `()`, thu thập mệnh đề đơn, phát hiện xung đột hai đơn vị đối dấu ($x$ và $-x$), ghi nhận `stats.propagations` và rút gọn mệnh đề qua `simplify()`.
     - Chiến lược chọn biến phân nhánh tất định: `"ordered"` (chỉ số biến nhỏ nhất) và `"frequency"` (biến xuất hiện nhiều nhất trong các mệnh đề còn lại, hòa chọn chỉ số nhỏ hơn).
     - Phân nhánh đệ quy thử `True` rồi `False`, cập nhật `stats.decisions`, `stats.backtracks`, `stats.runtime` và điền mô hình đầy đủ cho dải biến $1 \dots m$.
2. **Tệp [griductive/engine/game.py](griductive/engine/game.py):**
   - `LogicAgent.verify(state, cell, verdict)`: kiểm tra $KB_t$ khả thỏa trước, sau đó kiểm chứng bằng phản chứng ($KB_t \land \neg\alpha$ vô nghiệm) để phân biệt `ACCEPTED`, `CONTRADICTED`, `NOT_PROVABLE` và `INCONSISTENT`.
   - `LogicAgent._verdicts(state)` và `LogicAgent.classify(state)`: phân loại toàn bộ ô chưa mở kèm bộ nhớ nhân chứng mô hình (`can_be_true`, `can_be_false`) giúp giảm số lần gọi SAT.

```powershell
# Kiểm tra riêng phần DPLL và LogicAgent
.\.venv\Scripts\python.exe -B -m unittest tests.test_solver -v
```

---

### 2.2. Phan Gia Phúc (`24120503`) — Mã hóa CNF & Biên dịch Manh mối
1. **Tệp [griductive/engine/cnf.py](griductive/engine/cnf.py):**
   - `Encoder.gate(kind, operands)`: rút gọn hằng `bool`, khử literal trùng, phát hiện cặp đối ngẫu, tra bảng băm `self.gates` để dùng chung biến phụ Tseitin và sinh các mệnh đề tương đương hai chiều cho cổng `"AND"` / `"OR"`.
   - `Encoder.thresholds(cells)`: quy hoạch động bậc đa thức $O(|R|^2)$ tính dãy literal ngưỡng `counts[k]` (*có ít nhất $k$ tội phạm trong vùng*), dùng chung không gian biến phụ của `Encoder`.
   - `build_knowledge_base(state, registry)`: tạo $KB_t$ chỉ từ `state.clues` đã mở và mệnh đề đơn của `state.statuses` đã chứng minh.
2. **Tệp [griductive/engine/clues.py](griductive/engine/clues.py):**
   - Cài đặt phương thức biên dịch `expression()` cho cả 6 mẫu cơ sở (`Fact`, `Same`/`Different`, `Count` + `Exactly`/`AtLeast`/`AtMost`) và 2 mẫu mở rộng (`Comparison` qua quan hệ `greater_equal`, `Conditional` qua $\neg P \lor Q$).

```powershell
# Kiểm tra riêng phần mã hóa CNF và luật mở rộng
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_rule_extensions tests.test_rule_registration -v
```

---

### 2.3. Tống Phúc Thiện (`24120141`) — Hệ thống Vùng, Đánh giá Ngữ nghĩa & Luồng GameEngine
1. **Tệp [griductive/engine/regions.py](griductive/engine/regions.py):**
   - Cài đặt `resolve()` cho 4 vùng cơ sở (`Row`, `Column`, `Neighbors` theo khoảng cách Chebyshev $\le 1$ loại trừ ô mốc, `Explicit`) và 4 vùng mở rộng (`Corners`, cùng `SetOperation.combine` cho `Union`, `Intersection`, `Difference`).
2. **Tệp [griductive/engine/clues.py](griductive/engine/clues.py):**
   - Cài đặt bộ đánh giá ngữ nghĩa trực tiếp `evaluate()` / `compare()` hoàn toàn độc lập với CNF/SAT cho toàn bộ 8 kiểu manh mối.
3. **Tệp [griductive/engine/game.py](griductive/engine/game.py):**
   - Cài đặt `GameEngine.hint()` (chỉ dùng `PublicState`, không đọc nghiệm ẩn), `GameEngine.step()` và `check_uniqueness()` (kiểm tra nghiệm duy nhất ngoại tuyến bằng mệnh đề chặn trên tập biến chính).

```powershell
# Kiểm tra riêng phần vùng, đánh giá ngữ nghĩa và các màn 5x5
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_puzzle_5x5 -v
```

---

### 2.4. Phan Ngọc Thức (`24120228`) & Nguyễn Lê Minh Quân (`24120219`) — Kiến trúc, Giao diện Desktop, Thực nghiệm, Báo cáo & Video
1. **Kiến trúc, Dữ liệu câu đố & Giao diện Desktop ([griductive/ui/](griductive/ui/), [griductive/presentation/](griductive/presentation/), [puzzles/](puzzles/)):**
   - Thiết kế mô hình dữ liệu bất biến `PublicState` / `PrivatePuzzle`, luồng nền `EngineWorker` có cơ chế `fork()` và hủy an toàn trên Desktop Cozy Harbor, bộ dựng câu tiếng Việt [wording_vi.py](griductive/presentation/wording_vi.py), 6 hồ sơ câu đố chuẩn (`3×3`, `4×4`, `5×5`) và bộ 87 bài kiểm thử tự động.
2. **Thực nghiệm hệ thống, Báo cáo HCMUS & Video trình diễn ([griductive/experiments.py](griductive/experiments.py), [output/experiments/](output/experiments/)):**
   - Đo kiểm 12 lượt chạy đối sánh `ordered` và `frequency` trên cùng 6 màn chơi (môi trường đo chính thức trên máy Quân: `Windows 11, Python 3.14.6, CPU Intel Core i5-12450HX`), xuất đầy đủ CSV/JSON/12 tệp trace, phân tích số liệu & biểu đồ 300 DPI, biên soạn báo cáo LaTeX 22 trang chuẩn mẫu HCMUS (`Report.pdf`) và dựng video thuyết minh tiếng Việt `Demo.mp4`.

```powershell
# Chạy toàn bộ 87 kiểm thử và tái lập thực nghiệm
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m griductive.experiments
```
