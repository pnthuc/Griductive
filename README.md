# Griductive Solver — Suy luận Không Đoán Mò với Mã hóa CNF và Bộ giải DPLL

Đồ án thực hành 2 môn **CSC14003 – Introduction to Artificial Intelligence** (Lớp **24TN**, Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên – ĐHQG-HCM).

Dự án cài đặt lại trò chơi suy luận lưới **Griductive** kết hợp tác tử suy diễn logic mệnh đề **không đoán mò (*no-guess*)** trên giao diện **Desktop PySide6 (Cozy Harbor)**. Toàn bộ bộ biên dịch công thức chuẩn hội (**CNF** — cổng Tseitin dùng chung không gian biến phụ và quy hoạch động đếm ngưỡng unary) cùng bộ giải **DPLL SAT Solver** (`ordered` và `frequency`) đều được tự cài đặt bằng Python thuần.

---

## 1. Thông tin nhóm và mức độ hoàn thành

Thông tin thành viên được đồng bộ với hồ sơ [docs/team.json](docs/team.json) và Bảng 1 của báo cáo kỹ thuật HCMUS (`Report.pdf`):

| Thành viên | MSSV | Phần việc phụ trách | Hoàn thành |
| --- | --- | --- | ---: |
| **Phan Ngọc Thức** | `24120228` | Kiến trúc chung, giao diện Desktop Cozy Harbor, thực nghiệm, báo cáo và video demo | 100% |
| **Nguyễn Lê Minh Quân** | `24120219` | Tổ chức thực nghiệm hệ thống, so sánh hai chiến lược chọn biến (`ordered` vs `frequency`), phân tích số liệu, báo cáo và video demo | 100% |
| **Tống Phúc Thiện** | `24120141` | Phân giải hệ thống vùng và phép toán tập hợp, đánh giá ngữ nghĩa trực tiếp (`evaluate`), điều phối `GameEngine` và `check_uniqueness` | 100% |
| **Bùi Phương Nam** | `24120502` | Bộ giải DPLL SAT Solver (`ordered` & `frequency`) và suy luận phản chứng của `LogicAgent` | 100% |
| **Phan Gia Phúc** | `24120503` | Mã hóa CNF (cổng Tseitin, quy hoạch động đếm ngưỡng unary) và chuyển đổi toàn bộ mẫu manh mối sang CNF | 100% |

- **Video trình diễn trên Google Drive (mục 4.7):** [https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing](https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing) (`05:33`, thuyết minh và phụ đề tiếng Việt, quyền xem *Anyone with the link* — đã lưu trong [docs/team.json](docs/team.json) và `Report.pdf`).

---

## 2. Cài đặt và khởi chạy nhanh

Các lệnh dưới đây chạy trực tiếp tại thư mục chứa [main.py](main.py) — áp dụng giống nhau dù bạn đứng ở thư mục gốc của kho mã hay bên trong thư mục `Source/` sau khi giải nén gói nộp bài `24120228_24120219_24120141_24120502_24120503.zip`.

- **Yêu cầu môi trường:** Python `3.11+` (đã kiểm thử và đo thực nghiệm trên Python `3.12` và `3.14`).
- **Thư viện cài đặt ([requirements.txt](requirements.txt)):** Chỉ cần duy nhất `PySide6==6.12.0` cho giao diện đồ họa Desktop; toàn bộ lõi suy luận trong `griductive/engine/` và bộ thực nghiệm `griductive/experiments.py` chỉ dùng thư viện chuẩn của Python.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Chạy giao diện Desktop Cozy Harbor (mặc định mở màn 3x3 đầu tiên)
.\.venv\Scripts\python.exe -B main.py

# Hoặc mở trực tiếp một màn cụ thể từ dòng lệnh:
.\.venv\Scripts\python.exe -B main.py puzzles/case-5x5-01.json
```

### macOS / Linux (Bash)

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt

# Chạy giao diện Desktop Cozy Harbor
./.venv/bin/python -B main.py
```

---

## 3. Hướng dẫn chơi thủ công, Hint, Auto Solve và Sổ giải

Giao diện Desktop Cozy Harbor ([griductive/ui/](griductive/ui/)) hiển thị lưới $N \times N$ với tọa độ cột chữ (`A`–`E`) và hàng số (`1`–`5`), tên nhân vật theo thứ tự bảng chữ cái từng hàng, nghề nghiệp, trạng thái đã chứng minh và lời khai trên các thẻ đã lật.

### 3.1. Chọn màn chơi và nạp tệp JSON (`Load` / `Restart`)
- **Đổi màn có sẵn:** Bấm vào tên vụ án trên thanh tiêu đề để mở menu 6 hồ sơ được nhóm theo kích thước bàn (`3×3`, `4×4`, `5×5`):
  - `3×3`: [puzzles/case-3x3-01.json](puzzles/case-3x3-01.json) (*Bức thư bên cửa sổ*), [puzzles/case-3x3-02.json](puzzles/case-3x3-02.json) (*Lời khai trên bến vắng*).
  - `4×4`: [puzzles/case-4x4-01.json](puzzles/case-4x4-01.json) (*Chuyến tàu lúc hoàng hôn*), [puzzles/case-4x4-02.json](puzzles/case-4x4-02.json) (*Dấu vết trong phố nhỏ*).
  - `5×5`: [puzzles/case-5x5-01.json](puzzles/case-5x5-01.json) (*Đêm hội bên hải đăng*), [puzzles/case-5x5-02.json](puzzles/case-5x5-02.json) (*Bí mật sau phiên chợ*).
- **Nạp câu đố ngoài (`Load`):** Chọn **Mở màn chơi JSON…** ở cuối menu hồ sơ hoặc trong menu bánh răng. Bộ nạp [load_puzzle](griductive/engine/models.py) kiểm tra đầy đủ cấu trúc, vùng tham chiếu và tính đúng đắn của mọi lời khai dưới nghiệm ẩn.
- **Làm lại màn (`Restart`):** Bấm nút **Làm lại** trên thanh công cụ (hoặc **Làm lại màn này** trong menu bánh răng) để hủy yêu cầu suy luận đang chạy, khôi phục các thẻ mở ban đầu và xóa lịch sử bước giải.

### 3.2. Đọc lời khai và tô sáng vùng tham chiếu
- Bấm vào một thẻ **đã mở** để tô sáng toàn bộ các ô thuộc vùng tham chiếu của lời khai đó trên bàn cờ; các ô ngoài vùng được làm mờ nhẹ để dễ đối chiếu.
- Với lời khai nhiều vùng (`COMPARISON`, `CONDITIONAL` hoặc phép toán tập hợp), di chuột lên từng cụm chữ màu trong lời khai để xem trước vùng toán hạng tương ứng (`left`, `right`, ô mốc `anchor`), hoặc bấm vào cụm chữ để ghim cố định vùng đó.
- Nhấn phím `Escape` hoặc bấm vùng trống để bỏ chọn thẻ/vùng đang ghim.

### 3.3. Phán quyết thủ công không đoán mò (`CRIMINAL` / `INNOCENT`)
- Bấm vào một thẻ **đang úp** để hiện hai nút phán quyết **Vô tội** (`INNOCENT`) và **Tội phạm** (`CRIMINAL`).
- `GameEngine.submit` chuyển bản chụp công khai bất biến (`PublicState`) cho `LogicAgent.verify` kiểm tra bằng phản chứng trên DPLL và xử lý đúng ba trường hợp:
  1. **`ACCEPTED` (Hợp lệ & đã chứng minh):** Giả thiết ngược lại làm `KB` vô nghiệm (`UNSAT`). Thẻ được đánh dấu trạng thái, lật mở lời khai mới và ghi thêm một mục vào nhật ký.
  2. **`NOT_PROVABLE` (Chưa đủ cơ sở kết luận):** Cả hai giả thiết `CRIMINAL` và `INNOCENT` đều khả thỏa (`SAT`) với tri thức công khai hiện tại. Giao diện báo chưa đủ thông tin và **giữ nguyên thẻ úp**, không làm lộ lời khai ẩn.
  3. **`CONTRADICTED` (Mâu thuẫn với tri thức hiện có):** Giả thiết người chơi chọn dẫn tới `UNSAT` (tức trạng thái ngược lại mới là hệ quả bắt buộc). Giao diện báo mâu thuẫn với dữ kiện đã mở và **giữ nguyên trạng thái bàn**.

### 3.4. Gợi ý (`Hint`) và Sổ giải / Tự động giải (`Auto Solve`)
- **Gợi ý (`Gợi ý`):** Gọi `GameEngine.hint()` trên `PublicState` hiện tại để chỉ ra nhân vật đầu tiên (theo thứ tự hàng) có trạng thái bắt buộc suy ra được mà **không đọc đáp án ẩn** và chưa tự ý lật thẻ.
- **Sổ giải & Tự động giải:** Bấm nút **Sổ giải** trên thanh tiêu đề (hoặc **Tự động giải** trong menu bánh răng) để mở bảng Sổ tay suy luận bên phải:
  - **Bước tiếp:** Thực hiện đúng một bước suy luận đã chứng minh (`GameEngine.step()`).
  - **Chạy tự động / Tạm dừng:** Tự động giải lần lượt từng bước đến khi mở hết bàn (`SOLVED`) hoặc dừng ở trạng thái không còn bước ép buộc (`UNKNOWN` / `INCONSISTENT`). Đóng bảng Sổ giải sẽ tự động tạm dừng phát tự động.
  - **Chi tiết & Thông số KB:** Mỗi bước giải có nút **Chi tiết** hiển thị lời khai vừa mở, danh sách ID lời khai đang hoạt động trước bước đó và danh sách từng truy vấn SAT (giả định, kết quả `SAT`/`UNSAT`, số quyết định, lan truyền, quay lui). Nút **Thông số KB** hiển thị số biến chính, biến phụ Tseitin và số mệnh đề CNF hiện thời.
  - **Xuất JSON:** Tải toàn bộ danh sách `trace` của phiên chơi ra tệp JSON.

---

## 4. Kiểm thử tự động và tái lập thực nghiệm

### 4.1. Chạy bộ kiểm thử tự động (87 kiểm thử / 13 mô-đun)

```powershell
# Chạy toàn bộ 87 unit test
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v

# Chạy riêng kiểm thử lõi CNF, vùng, luật mở rộng, DPLL và bộ thực nghiệm
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_solver tests.test_rule_extensions tests.test_rule_registration tests.test_puzzle_5x5 tests.test_experiments -v

# Chạy riêng kiểm thử giao diện Desktop, luồng nền và bản địa hóa
.\.venv\Scripts\python.exe -B -m unittest tests.test_ui tests.test_journal tests.test_background tests.test_presentation tests.test_localization -v
```

*(Trên macOS/Linux thay `.\.venv\Scripts\python.exe` bằng `./.venv/bin/python`.)*

### 4.2. Chạy lại bộ thực nghiệm so sánh hai chiến lược DPLL

Module [griductive/experiments.py](griductive/experiments.py) chạy tự động cả hai chiến lược chọn biến của DPLL (`ordered` và `frequency`) trên cùng 6 màn chơi chuẩn (`3×3`, `4×4`, `5×5` — tổng cộng 12 lượt chạy):

```powershell
# Ghi kết quả vào output/experiments/ (--timeout mặc định 30 giây, kiểm tra giữa các bước)
.\.venv\Scripts\python.exe -B -m griductive.experiments

# Hoặc xuất ra thư mục tạm để đối chiếu mà không ghi đè số liệu gốc trong kho:
.\.venv\Scripts\python.exe -B -m griductive.experiments --output output/experiments_recheck --timeout 30
```

Đầu ra gồm [output/experiments/results.json](output/experiments/results.json), [output/experiments/results.csv](output/experiments/results.csv) và 12 tệp nhật ký chi tiết `output/experiments/<puzzle>-<heuristic>-trace.json`. Tham số `--timeout T` (mặc định `30` giây) được kiểm tra **giữa các bước mở thẻ**; bên trong mỗi bước, `LogicAgent` dùng hạn `min(10, T)` giây cho từng truy vấn SAT, còn `GameEngine.submit` xác minh độc lập với hạn riêng `10` giây/truy vấn (hàm ngoại tuyến `check_uniqueness` dùng `min(10, T)` giây), nên thời gian đo thực tế khi xảy ra `TIMEOUT` có thể vượt quá `T` cho tới khi truy vấn/bước đang chạy hoàn tất.

### 4.3. Tóm tắt số liệu thực nghiệm gốc

Số liệu lưu tại [output/experiments/results.json](output/experiments/results.json) (đồng bộ với Bảng 5 và Bảng 6 trong báo cáo HCMUS, đo trên môi trường **Windows 11, Python 3.14.6, CPU 12th Gen Intel Core i5-12450HX**):

| Màn | Chiến lược | N | Kết quả | Nghiệm | Biến chính | Biến phụ | Mệnh đề | Bước | Gọi SAT | Quyết định | Lan truyền | Quay lui | Thời gian (s) |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `case-3x3-01` | `ordered` | 3 | `SOLVED` | `UNIQUE` | 9 | 156 | 491 | 7 | 34 | 48 | 2944 | 4 | 0.046907 |
| `case-3x3-01` | `frequency` | 3 | `SOLVED` | `UNIQUE` | 9 | 156 | 491 | 7 | 33 | 40 | 2942 | 4 | 0.059760 |
| `case-3x3-02` | `ordered` | 3 | `SOLVED` | `UNIQUE` | 9 | 144 | 455 | 7 | 30 | 34 | 2802 | 15 | 0.070753 |
| `case-3x3-02` | `frequency` | 3 | `SOLVED` | `UNIQUE` | 9 | 144 | 455 | 7 | 30 | 27 | 2693 | 9 | 0.051107 |
| `case-4x4-01` | `ordered` | 4 | `SOLVED` | `UNIQUE` | 16 | 364 | 1138 | 13 | 84 | 518 | 29666 | 444 | 1.014534 |
| `case-4x4-01` | `frequency` | 4 | `SOLVED` | `UNIQUE` | 16 | 364 | 1138 | 13 | 85 | 287 | 18887 | 8 | 0.504275 |
| `case-4x4-02` | `ordered` | 4 | `SOLVED` | `UNIQUE` | 16 | 273 | 862 | 13 | 93 | 168 | 12568 | 7 | 1.150945 |
| `case-4x4-02` | `frequency` | 4 | `SOLVED` | `UNIQUE` | 16 | 273 | 862 | 13 | 91 | 158 | 12567 | 16 | 1.089805 |
| `case-5x5-01` | `ordered` | 5 | `SOLVED` | `UNIQUE` | 25 | 668 | 2068 | 22 | 162 | 193 | 43608 | 18 | 3.482976 |
| `case-5x5-01` | `frequency` | 5 | `SOLVED` | `UNIQUE` | 25 | 668 | 2068 | 22 | 164 | 247 | 44288 | 45 | 3.591465 |
| `case-5x5-02` | `ordered` | 5 | `SOLVED` | `UNIQUE` | 25 | 654 | 2045 | 22 | 182 | 752 | 55976 | 113 | 6.432318 |
| `case-5x5-02` | `frequency` | 5 | `SOLVED` | `UNIQUE` | 25 | 654 | 2045 | 22 | 182 | 647 | 53655 | 37 | 5.540037 |

*(Giá trị `runtime` đầy đủ độ chính xác dấu phẩy động nằm trong [output/experiments/results.json](output/experiments/results.json). Với các lượt chạy hoàn tất không gặp `TIMEOUT`, tất cả các cột đếm logic từ `Biến chính` đến `Quay lui` đều tất định trên mọi máy; riêng `Thời gian (s)` — cũng như bước dừng và bộ đếm nếu đặt `--timeout` nhỏ gây `TIMEOUT` giữa chừng — phụ thuộc tốc độ phần cứng.)*

---

## 5. Bảng đối chiếu yêu cầu đề bài (`AI - Project 2.pdf`)

| Mục đề bài | Nội dung yêu cầu cốt lõi | Tệp cài đặt chính | Kiểm thử & kết quả minh chứng |
| --- | --- | --- | --- |
| **4.1 Reimplement the Game (10 đ)** | GUI hiển thị lưới $N \times N$, tọa độ, tên, nghề, thẻ mở/úp; chọn `CRIMINAL`/`INNOCENT`; lật thẻ khi chứng minh đúng; từ chối không lộ lời khai ẩn (`NOT_PROVABLE` vs `CONTRADICTED`); tô sáng vùng lời khai; có `Load`, `Restart`, `Hint`, `Auto Solve`; tách biệt `GameEngine` và `LogicAgent` (`PublicState` bất biến). | [main.py](main.py), [griductive/engine/models.py](griductive/engine/models.py), [griductive/engine/game.py](griductive/engine/game.py), [griductive/ui/window.py](griductive/ui/window.py), [griductive/ui/cards.py](griductive/ui/cards.py), [griductive/ui/engine_worker.py](griductive/ui/engine_worker.py) | [tests/test_core.py](tests/test_core.py) (`test_public_state_does_not_publish_hidden_data`), [tests/test_solver.py](tests/test_solver.py) (`test_rejection_is_atomic_and_acceptance_is_repeatable`), [tests/test_ui.py](tests/test_ui.py), [tests/test_background.py](tests/test_background.py) |
| **4.2 Automatic Logical Representation & CNF Encoding (10 đ)** | Ánh xạ biến mệnh đề tất định; kiểm tra tham số và vùng; biên dịch tự động 6 mẫu cơ sở (`FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`) + **phần mở rộng** (`COMPARISON`, `CONDITIONAL` cùng 4 vùng mở rộng `CORNERS`, `UNION`, `INTERSECTION`, `DIFFERENCE`); dựng $KB_t$ chỉ từ lời khai đã mở và mệnh đề đơn đã chứng minh; báo cáo số biến chính/phụ và số mệnh đề; bộ đánh giá ngữ nghĩa trực tiếp (`evaluate`) độc lập với CNF. | [griductive/engine/regions.py](griductive/engine/regions.py), [griductive/engine/clues.py](griductive/engine/clues.py), [griductive/engine/cnf.py](griductive/engine/cnf.py) | [tests/test_core.py](tests/test_core.py) (`test_semantics_and_cnf_agree_exhaustively`), [tests/test_solver.py](tests/test_solver.py) (`test_reified_semantics_and_overlapping_comparisons`, `test_shared_auxiliary_namespace_and_polynomial_size`), [tests/test_rule_extensions.py](tests/test_rule_extensions.py), [tests/test_rule_registration.py](tests/test_rule_registration.py) |
| **4.3 DPLL SAT Solver (10 đ)** | Tự cài đặt thủ tục DPLL: lan truyền mệnh đề đơn (*unit propagation*), phát hiện xung đột, chọn biến tất định (`ordered` & `frequency`), phân nhánh đệ quy và quay lui, trả về `SAT` kèm mô hình đầy đủ hoặc `UNSAT`, ghi nhận `decisions`, `propagations`, `backtracks`, `runtime` và hỗ trợ `assumptions`. | [griductive/engine/sat.py](griductive/engine/sat.py) | [tests/test_solver.py](tests/test_solver.py) (`test_dpll_complete_model_and_unsat`), [tests/test_rule_extensions.py](tests/test_rule_extensions.py) (`test_cancel_is_not_unknown_or_a_partial_model`) |
| **4.4 Deductive Logic Agent (20 đ)** | Phân loại ô chưa mở (`CRIMINAL`, `INNOCENT`, `UNKNOWN`, `INCONSISTENT`); chỉ chọn phán quyết bắt buộc (*no-guess*); nhận lời khai mới từ `GameEngine` sau khi phán quyết được chấp nhận; sinh nhật ký `trace` đầy đủ (số bước, ID lời khai hiệu lực, truy vấn SAT, phán quyết, lời khai mới); hàm `check_uniqueness` kiểm tra nghiệm duy nhất bằng mệnh đề chặn trên biến chính; `Hint` không đọc đáp án ẩn. | [griductive/engine/game.py](griductive/engine/game.py), [griductive/ui/journal.py](griductive/ui/journal.py) | [tests/test_solver.py](tests/test_solver.py) (`test_model_is_not_entailment_and_inconsistency`, `test_six_cases_unique_and_progressively_solvable`), [tests/test_puzzle_5x5.py](tests/test_puzzle_5x5.py), [tests/test_journal.py](tests/test_journal.py) |
| **4.5 Experiments (10 đ)** | Đánh giá trên cùng tập câu đố gồm các màn $3 \times 3$, $4 \times 4$ và ca kiểm tra tải $5 \times 5$; ghi nhận biến chính/phụ, mệnh đề CNF, số lần gọi SAT, quyết định, lan truyền, quay lui, số bước suy luận và thời gian chạy; bảo toàn trạng thái dừng/`TIMEOUT` thay vì xóa khỏi kết quả. | [griductive/experiments.py](griductive/experiments.py), [puzzles/](puzzles/) | [tests/test_experiments.py](tests/test_experiments.py), [output/experiments/results.json](output/experiments/results.json), [output/experiments/results.csv](output/experiments/results.csv), 12 tệp `output/experiments/*-trace.json`, [output/puzzle-quality.json](output/puzzle-quality.json) |
| **4.6 Report (30 đ)** | Báo cáo PDF trình bày kế hoạch & phân công kèm tỷ lệ hoàn thành, mô hình hóa bài toán, dẫn xuất mã hóa CNF cho manh mối nhị phân & manh mối đếm, thuật toán DPLL/phản chứng/nghiệm duy nhất, bảng biểu & phân tích thực nghiệm (kể cả giới hạn), tài liệu tham khảo và phụ lục AI tạo sinh. | `Report.pdf` (biên dịch từ nguồn LaTeX HCMUS `docs/latex/`), [docs/team.json](docs/team.json), [TASKS.md](TASKS.md) | [docs/REFERENCES.md](docs/REFERENCES.md), [docs/AI-PROMPTS.md](docs/AI-PROMPTS.md), `Report.pdf` (22 trang chuẩn mẫu HCMUS) |
| **4.7 Demonstration Video (10 đ)** | Video 5–10 phút trình diễn GUI, chơi thủ công, chạy bộ giải, có thuyết minh/phụ đề tiếng Việt hoặc tiếng Anh, tải lên Google Drive ở chế độ *Anyone with the link* (không dùng YouTube). | [docs/team.json](docs/team.json) (`demo_url`) | `output/Demo.mp4` (`05:33`, thuyết minh & phụ đề tiếng Việt; đã tải lên [Google Drive](https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing), kiểm tra xem ẩn danh và nhúng vào `docs/team.json` + `Report.pdf`) |
| **5. Submission** | Đóng gói `.zip` theo định dạng `StudentID1_StudentID2_...` gồm thư mục `Source/` (`main.py`, `README.md`, `requirements.txt`, ...) và tệp `Report.pdf` ở cấp ngoài cùng; nếu gói nén `> 20 MB` mới cần nộp qua link Drive. | Cấu trúc kho mã sạch, tương thích giải nén độc lập trong `Source/` | `output/24120228_24120219_24120141_24120502_24120503.zip` (`< 20 MB`, vượt qua toàn bộ 87/87 kiểm thử khi chạy trực tiếp từ `Source/`) |

---

## 6. Cấu trúc thư mục và tài liệu kỹ thuật

```text
.
├── main.py                      # Điểm vào ứng dụng Desktop PySide6 (Cozy Harbor)
├── requirements.txt             # Thư viện cài đặt (PySide6==6.12.0)
├── griductive/
│   ├── engine/                  # Lõi logic mệnh đề độc lập giao diện
│   │   ├── models.py            # Board, Character, PublicState, PrivatePuzzle, load_puzzle
│   │   ├── regions.py           # 4 vùng cơ sở + 4 vùng mở rộng & RegionRegistry
│   │   ├── clues.py             # 6 manh mối cơ sở + 2 mở rộng, evaluate(), expression(), CluePart
│   │   ├── cnf.py               # Encoder cổng Tseitin, quy hoạch động ngưỡng unary, KnowledgeBase
│   │   ├── sat.py               # DPLL tự cài đặt (ordered & frequency), giả định, thống kê
│   │   └── game.py              # LogicAgent, GameEngine, fork(), check_uniqueness()
│   ├── presentation/            # Sinh câu tiếng Việt và ánh xạ tham chiếu tô sáng (không phụ thuộc Qt)
│   ├── ui/                      # Cửa sổ Desktop Cozy Harbor, thẻ nghi phạm, Sổ giải, EngineWorker
│   └── experiments.py           # Chạy thực nghiệm đối sánh ordered vs frequency trên 6 màn
├── puzzles/                     # 6 hồ sơ vụ án chuẩn (2 màn 3x3, 2 màn 4x4, 2 màn 5x5)
├── assets/                      # Atlas nhân vật pixel, đạo cụ nghề nghiệp, nền bến cảng và biểu tượng HUD
├── tests/                       # 13 mô-đun kiểm thử đơn vị và tích hợp (87 test cases)
├── output/                      # Kết quả thực nghiệm (CSV, JSON, 12 trace) và kiểm định độ khó câu đố
├── TASKS.md                     # Phân công công việc nhóm, mô-đun bàn giao và lệnh kiểm tra
└── docs/                        # Tài liệu thiết kế, hướng dẫn mở rộng, nguồn tham khảo và phụ lục AI
```

### Đọc tiếp tài liệu chi tiết

- [docs/DESIGN.md](docs/DESIGN.md) — Ranh giới bất biến `GameEngine`/`LogicAgent`, suy luận không đoán mò, chi tiết các mẫu manh mối/vùng và phần mở rộng, dẫn xuất mã hóa CNF, thuật toán DPLL, cấu trúc `trace`, kiểm tra nghiệm duy nhất và cách đọc bảng số liệu thực nghiệm.
- [docs/EXTENDING.md](docs/EXTENDING.md) — Hướng dẫn đăng ký thêm loại vùng (`@register_region`) và manh mối mới (`@register_clue`) mà không cần sửa bộ biên dịch CNF, bộ giải DPLL hay giao diện.
- [TASKS.md](TASKS.md) — Bảng phân công chi tiết từng thành viên, tỷ lệ hoàn thành và hướng dẫn kiểm tra theo từng phần việc.
- [docs/REFERENCES.md](docs/REFERENCES.md) — Danh mục tài liệu học thuật, tài liệu kỹ thuật và các dự án đối chiếu (đồng bộ với mục Tài liệu tham khảo của báo cáo HCMUS).
- [docs/AI-PROMPTS.md](docs/AI-PROMPTS.md) — Nhật ký prompt AI tạo sinh và quy trình kiểm chứng đồ họa nhân vật.
