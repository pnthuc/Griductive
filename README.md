# Griductive Solver

Đồ án thực hành 2 môn **CSC14003 – Nhập môn Trí tuệ Nhân tạo** (Lớp **24TN**, Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM).

Dự án cài đặt lại trò chơi suy luận lưới **Griductive** kèm bộ suy luận logic mệnh đề không đoán mò (*no-guess*) trên giao diện Desktop **PySide6**. Toàn bộ phần mã hóa **CNF** (cổng Tseitin và bộ đếm ngưỡng unary bằng quy hoạch động) cùng bộ giải **DPLL** (`ordered` và `frequency`) đều do nhóm tự viết bằng Python thuần, không dùng thư viện SAT ngoài.

---

## 1. Thành viên nhóm và phân công

Thông tin khớp với [docs/team.json](docs/team.json) và Bảng 1 trong `Report.pdf`:

| Thành viên | MSSV | Phần việc phụ trách | Hoàn thành |
| --- | --- | --- | ---: |
| Phan Ngọc Thức | `24120228` | Kiến trúc dự án, giao diện Desktop Cozy Harbor, thực nghiệm, báo cáo và video | 100% |
| Nguyễn Lê Minh Quân | `24120219` | Chạy thực nghiệm, so sánh hai chiến lược chọn biến, phân tích số liệu, báo cáo và video | 100% |
| Tống Phúc Thiện | `24120141` | Hệ thống vùng và phép tập hợp, hàm đánh giá ngữ nghĩa (`evaluate`), `GameEngine` và `check_uniqueness` | 100% |
| Bùi Phương Nam | `24120502` | Bộ giải DPLL (`ordered`, `frequency`) và suy luận phản chứng của `LogicAgent` | 100% |
| Phan Gia Phúc | `24120503` | Cổng Tseitin, bộ đếm ngưỡng quy hoạch động và biên dịch các mẫu manh mối sang CNF | 100% |

- **Video trình diễn (Google Drive):** [Xem video demo](https://drive.google.com/file/d/1Y-84FGh__BUx-dtXgX3oKmJwhWga77Ou/view?usp=sharing) (`05:33`, có thuyết minh và phụ đề tiếng Việt, mở quyền xem công khai *Anyone with the link*).

---

## 2. Cài đặt và chạy chương trình

Chạy các lệnh dưới đây ngay tại thư mục chứa [main.py](main.py) (thư mục `Source/` sau khi giải nén gói nộp bài).

- **Python:** phiên bản `3.11+` (đã thử nghiệm trên Python `3.11`, `3.12` và `3.14`).
- **Thư viện ([requirements.txt](requirements.txt)):** chỉ cần `PySide6==6.12.0` cho giao diện Desktop; lõi suy luận trong `griductive/engine/` và module thực nghiệm `griductive/experiments.py` chỉ dùng thư viện chuẩn của Python.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Mở giao diện Desktop (mặc định mở màn 3x3 đầu tiên)
.\.venv\Scripts\python.exe -B main.py

# Hoặc mở sẵn một tệp màn chơi cụ thể
.\.venv\Scripts\python.exe -B main.py puzzles/case-5x5-01.json
```

### macOS / Linux (Bash)

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt

./.venv/bin/python -B main.py
```

---

## 3. Chức năng chính trên giao diện Desktop

- **Chọn màn chơi (`Load`) và chơi lại (`Restart`):** Bấm vào tên vụ án trên thanh tiêu đề để chuyển giữa 6 màn chuẩn (`3×3`, `4×4`, `5×5`) trong thư mục [puzzles/](puzzles/) hoặc chọn **Mở màn chơi JSON…** để nạp màn chơi ngoài (`load_puzzle` tự kiểm tra cấu trúc, vùng tham chiếu và tính đúng của toàn bộ lời khai). Nút **Làm lại** hủy mọi truy vấn đang chạy và đưa bàn về trạng thái mở đầu.
- **Đọc lời khai và tô sáng vùng:** Bấm vào thẻ đã mở để tô sáng các ô thuộc vùng lời khai (các ô ngoài vùng được làm mờ nhẹ). Với lời khai nhiều vùng (`COMPARISON`, `CONDITIONAL`, phép toán tập hợp), có thể di chuột lên cụm chữ màu để xem trước hoặc bấm vào để ghim vùng tương ứng; nhấn `Escape` để bỏ chọn.
- **Phán quyết thủ công không đoán mò:** Bấm vào một thẻ đang úp rồi chọn **Vô tội** (`INNOCENT`) hoặc **Tội phạm** (`CRIMINAL`). `GameEngine.submit` chỉ đưa trạng thái công khai bất biến (`PublicState`) cho `LogicAgent.verify` kiểm chứng bằng phản chứng trên DPLL:
  - `ACCEPTED`: giả thiết phủ định dẫn tới `UNSAT`, thẻ được lật mở lời khai mới và ghi vào nhật ký.
  - `NOT_PROVABLE`: cả hai khả năng đều `SAT`, giao diện báo chưa đủ cơ sở và giữ nguyên thẻ úp.
  - `CONTRADICTED`: giả thiết đề nghị dẫn tới `UNSAT`, giao diện báo mâu thuẫn và giữ nguyên bàn.
- **Gợi ý (`Hint`) và Sổ giải (`Auto Solve`):**
  - **Gợi ý:** gọi `GameEngine.hint()` trên `PublicState` để chỉ ra nhân vật đầu tiên suy ra được theo thứ tự hàng mà không đọc đáp án ẩn và không tự lật thẻ.
  - **Sổ giải / Tự động giải:** mở bảng Sổ tay suy luận ở cạnh phải để chạy từng bước (**Bước tiếp**) hoặc giải tự động (**Chạy tự động** / **Tạm dừng**). Mỗi mục có nút **Chi tiết** xem danh sách lời khai hiệu lực và các truy vấn SAT, nút **Thông số KB** xem số biến chính/biến phụ/mệnh đề, và nút **Xuất JSON** để lưu `engine.trace`.

---

## 4. Kiểm thử tự động và chạy lại thực nghiệm

### 4.1. Bộ kiểm thử tự động (87 bài test / 13 mô-đun)

```powershell
# Chạy toàn bộ 87 bài kiểm thử
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v

# Chạy riêng kiểm thử lõi CNF, vùng, luật mở rộng, DPLL và thực nghiệm (không cần PySide6)
.\.venv\Scripts\python.exe -B -m unittest tests.test_core tests.test_solver tests.test_rule_extensions tests.test_rule_registration tests.test_puzzle_5x5 tests.test_experiments -v
```

### 4.2. Chạy lại thực nghiệm `ordered` vs `frequency`

```powershell
# Chạy 2 chiến lược chọn biến trên cùng 6 màn và ghi vào output/experiments/
.\.venv\Scripts\python.exe -B -m griductive.experiments

# Hoặc xuất sang thư mục khác để đối chiếu
.\.venv\Scripts\python.exe -B -m griductive.experiments --output output/experiments_recheck --timeout 30
```

Kết quả gồm [output/experiments/results.json](output/experiments/results.json), [output/experiments/results.csv](output/experiments/results.csv) và 12 tệp trace theo từng màn/cấu hình. Tham số `--timeout` (mặc định `30` giây) được kiểm tra giữa các bước mở thẻ, kèm hạn riêng trên từng truy vấn SAT (tối đa `10` giây). Các ca dừng sớm (`UNKNOWN`, `INCONSISTENT`, `TIMEOUT`) được giữ nguyên trong bảng thay vì loại bỏ.

### 4.3. Tóm tắt số liệu thực nghiệm

Đo trên Windows 11, Python 3.14.6, CPU Intel Core i5-12450HX (khớp Bảng 5 và Bảng 6 trong `Report.pdf`; thời gian làm tròn 3 chữ số thập phân từ `results.json`):

| Màn | Chiến lược | N | Kết quả | Nghiệm | Biến chính | Biến phụ | Mệnh đề | Bước | Gọi SAT | Quyết định | Lan truyền | Quay lui | Thời gian (s) |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `case-3x3-01` | `ordered` | 3 | `SOLVED` | `UNIQUE` | 9 | 156 | 491 | 7 | 34 | 48 | 2944 | 4 | 0,047 |
| `case-3x3-01` | `frequency` | 3 | `SOLVED` | `UNIQUE` | 9 | 156 | 491 | 7 | 33 | 40 | 2942 | 4 | 0,060 |
| `case-3x3-02` | `ordered` | 3 | `SOLVED` | `UNIQUE` | 9 | 144 | 455 | 7 | 30 | 34 | 2802 | 15 | 0,071 |
| `case-3x3-02` | `frequency` | 3 | `SOLVED` | `UNIQUE` | 9 | 144 | 455 | 7 | 30 | 27 | 2693 | 9 | 0,051 |
| `case-4x4-01` | `ordered` | 4 | `SOLVED` | `UNIQUE` | 16 | 364 | 1138 | 13 | 84 | 518 | 29666 | 444 | 1,015 |
| `case-4x4-01` | `frequency` | 4 | `SOLVED` | `UNIQUE` | 16 | 364 | 1138 | 13 | 85 | 287 | 18887 | 8 | 0,504 |
| `case-4x4-02` | `ordered` | 4 | `SOLVED` | `UNIQUE` | 16 | 273 | 862 | 13 | 93 | 168 | 12568 | 7 | 1,151 |
| `case-4x4-02` | `frequency` | 4 | `SOLVED` | `UNIQUE` | 16 | 273 | 862 | 13 | 91 | 158 | 12567 | 16 | 1,090 |
| `case-5x5-01` | `ordered` | 5 | `SOLVED` | `UNIQUE` | 25 | 668 | 2068 | 22 | 162 | 193 | 43608 | 18 | 3,483 |
| `case-5x5-01` | `frequency` | 5 | `SOLVED` | `UNIQUE` | 25 | 668 | 2068 | 22 | 164 | 247 | 44288 | 45 | 3,591 |
| `case-5x5-02` | `ordered` | 5 | `SOLVED` | `UNIQUE` | 25 | 654 | 2045 | 22 | 182 | 752 | 55976 | 113 | 6,432 |
| `case-5x5-02` | `frequency` | 5 | `SOLVED` | `UNIQUE` | 25 | 654 | 2045 | 22 | 182 | 647 | 53655 | 37 | 5,540 |

---

## 5. Cấu trúc thư mục

```text
.
├── main.py                      # Điểm khởi chạy ứng dụng Desktop PySide6
├── requirements.txt             # Thư viện cài đặt (PySide6==6.12.0)
├── griductive/
│   ├── engine/                  # Lõi suy luận độc lập với giao diện
│   │   ├── models.py            # Board, Character, PublicState, PrivatePuzzle, load_puzzle
│   │   ├── regions.py           # 4 vùng cơ sở + 4 vùng mở rộng (CORNERS, UNION, INTERSECTION, DIFFERENCE)
│   │   ├── clues.py             # 6 mẫu cơ sở + 2 mở rộng (COMPARISON, CONDITIONAL), evaluate(), expression()
│   │   ├── cnf.py               # Encoder cổng Tseitin, đếm ngưỡng unary, KnowledgeBase
│   │   ├── sat.py               # Bộ giải DPLL tự cài đặt (ordered & frequency)
│   │   └── game.py              # LogicAgent, GameEngine, fork(), check_uniqueness()
│   ├── presentation/            # Diễn đạt câu tiếng Việt và ánh xạ vùng tô sáng (không phụ thuộc Qt)
│   ├── ui/                      # Giao diện Desktop Cozy Harbor, Sổ giải và EngineWorker
│   └── experiments.py           # Chương trình chạy thực nghiệm 2 chiến lược trên 6 màn
├── puzzles/                     # 6 màn chơi chuẩn (2 màn 3x3, 2 màn 4x4, 2 màn 5x5)
├── assets/                      # Atlas nhân vật pixel, đạo cụ nghề nghiệp, ảnh nền và biểu tượng
├── tests/                       # 13 mô-đun kiểm thử (87 test cases)
├── output/                      # Kết quả thực nghiệm (CSV, JSON, 12 tệp trace) và kiểm định độ khó
├── TASKS.md                     # Chi tiết phân công và mô-đun phụ trách của từng thành viên
└── docs/                        # Tài liệu thiết kế, mở rộng luật, nguồn tham khảo và nhật ký AI
```

### Tài liệu kèm theo
- [docs/DESIGN.md](docs/DESIGN.md): kiến trúc `GameEngine`/`LogicAgent`, mã hóa CNF, DPLL, cấu trúc `trace` và kiểm tra nghiệm duy nhất.
- [docs/EXTENDING.md](docs/EXTENDING.md): cách đăng ký thêm loại vùng (`@register_region`) và manh mối (`@register_clue`).
- [TASKS.md](TASKS.md): phân công công việc và lệnh kiểm tra từng phần.
- [docs/REFERENCES.md](docs/REFERENCES.md): danh sách 12 tài liệu tham khảo và phạm vi đối chiếu.
- [docs/AI-PROMPTS.md](docs/AI-PROMPTS.md): nhật ký sử dụng AI tạo sinh và prompt tiêu biểu (bổ sung cho Phụ lục A của `Report.pdf`).
