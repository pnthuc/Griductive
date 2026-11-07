# Griductive - Lab 2

Game Python, dùng CNF và DPLL tự cài đặt, đồ họa pixel phố biển.
Hai giao diện dùng chung engine: desktop PySide6 và web Dash. Bản web khai báo
giao diện, style và callback bằng Python, không có file HTML/CSS/JavaScript tự viết.

## Chạy bản web

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B app.py
```

Mở http://127.0.0.1:8050. Có chọn màn, mở JSON, phán quyết thủ công, gợi ý,
giải từng bước/tự động, chọn vùng highlight và tải nhật ký JSON. Tiến độ được
giữ riêng cho mỗi tab bằng session storage. Mỗi yêu cầu dựng lại phiên và kiểm
chứng lịch sử bằng engine; không tin trạng thái do trình duyệt tự khai báo,
không đưa solution hoặc clue chưa mở của các màn có sẵn xuống trình duyệt.

`griductive/web.py` chứa các component và callback Dash;
`griductive/web_game.py` điều phối phiên độc lập với UI. Thư viện Dash tự sinh
mã để trình duyệt hiển thị; mọi luật chơi và suy luận chạy bằng Python trên server.

## Deploy Vercel

Chọn framework Flask, dùng `app.py` làm entrypoint. `vercel.json` và
`.python-version` đã cấu hình Python 3.12 và giới hạn request 60 giây.
Atlas/background dùng chung cho web và desktop nằm trong `public/images`,
Vercel phục vụ trực tiếp qua CDN. Không cần Node/React build hay cơ sở dữ liệu.
Dependencies web ở `requirements.txt`; PySide6 không được cài vào bản deploy.

```powershell
npx vercel login
npx vercel deploy --prod
```

Đăng nhập Vercel để sở hữu project và giữ deployment lâu dài. Có thể import
repo GitHub `pnthuc/Griductive` trên Vercel để tự deploy khi push.

## Chạy game

Nếu đã có `.venv`:

```powershell
.\.venv\Scripts\python.exe -B main.py
```

Cài mới:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe -B main.py
```

Mở màn cụ thể bằng cách thêm `puzzles/case-5x5-01.json` sau `main.py`.
Trong **Công cụ** có chọn màn, mở JSON, tự động giải và bật/tắt chuyển động.
Chọn người rồi bấm **Vô tội** hoặc **Tội phạm**. Game chỉ mở thẻ khi chứng minh
được phán quyết từ dữ kiện công khai. Gợi ý chỉ ra một người suy ra được tiếp.
Chọn clue để xem highlight; bấm đoạn chữ màu để tập trung vào vùng/người đó.
Escape bỏ chọn. Tạm dừng, Restart và đổi màn hủy yêu cầu suy luận cũ.

## Đọc mã theo thứ tự này

| File trong `griductive/engine/` | Nội dung |
|---|---|
| `models.py` | Dữ liệu Board/Character, trạng thái public/private, đọc và kiểm tra JSON |
| `regions.py` | Các lớp Region, registry và decorator đăng ký vùng |
| `clues.py` | Các lớp Clue, registry, decorator và tham chiếu highlight |
| `cnf.py` | Dựng KB và tạo CNF, quản lý biến chính/biến phụ |
| `sat.py` | DPLL: lan truyền đơn, phân nhánh và quay lui |
| `game.py` | GameEngine, LogicAgent, kiểm chứng phán quyết và nghiệm duy nhất |

Điểm bắt đầu là `main.py`. Luồng chính: UI gửi yêu cầu, engine tạo PublicState,
agent kiểm chứng bằng CNF/DPLL, engine chấp nhận hoặc từ chối, UI nhận kết quả.
Mỗi clue là một lớp có các hàm rõ tên, giữ evaluator độc lập với encoder.
Khai báo `region_fields`, `person_fields`, `children` để tự kiểm tra tham chiếu
và tạo highlight. Đăng ký bằng `@register_clue('NAME')` hoặc
`@register_region('NAME')`, không sửa CNF/DPLL. Phương thức `wording()` tùy chọn
tạo câu thường và HTML có liên kết ngay trong định nghĩa luật.

Ví dụ đầy đủ và cách đăng ký riêng cho một phiên nằm trong
[docs/EXTENDING.md](docs/EXTENDING.md).

## Các thư mục khác

- `griductive/presentation/`: câu tiếng Việt và lựa chọn tham chiếu, không Qt.
- `griductive/ui/`: cửa sổ, thẻ, animation, nhật ký, controller và worker.
- `assets/`: dữ liệu nhân vật và manifest ảnh.
- `public/images/`: atlas và ảnh nền dùng chung; 25 người, 7 frame/người.
- `puzzles/`: sáu màn, hai màn cho mỗi size 3x3, 4x4, 5x5; ID clue là mã ô.
- `tests/`: kiểm tra thuật toán, UI, sprite và xử lý nền; cần giữ để chống lỗi.
- `output/`: kết quả thực nghiệm chính và bản kiểm định độ khó đã lưu.
- `docs/`: báo cáo nháp, thành viên, nguồn tham khảo và prompt AI.

Thiết kế và ranh giới giữa các module được mô tả trong `docs/DESIGN.md`.
Extension gồm `COMPARISON`, `CONDITIONAL` và các vùng `CORNERS`, `UNION`,
`INTERSECTION`, `DIFFERENCE`.

Worker chạy các phép SAT ngoài luồng UI. Engine chỉ đưa clue đã mở và trạng thái
đã biết vào KB. Agent không nhận đáp án hoặc clue ẩn. Không dùng SAT library.
Runtime đọc ảnh có sẵn, không sinh asset khi khởi động. Các script tạo map,
xem thử sprite, ảnh concept và kế hoạch đã dùng xong được dọn khỏi project.
Đầu ra cần dùng được giữ dưới dạng sáu puzzle JSON, atlas ảnh và manifest;
không cần NumPy hay công cụ sinh ảnh để chạy game.

## Kiểm tra và chạy lại thực nghiệm

Để chạy cả test web và desktop, cài cả hai file requirements trước.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests
.\.venv\Scripts\python.exe -B -m griductive.experiments
```

Thực nghiệm dùng cùng sáu màn cho hai heuristic `ordered` và `frequency`.
Kết quả ở `output/experiments/`: CSV, JSON và trace theo màn/cấu hình.
`output/puzzle-quality.json` là bản kiểm định độ khó đã lưu. Các test vẫn kiểm
tra nghiệm duy nhất, public deduction loop và điều kiện của conditional.
Mỗi mục kiểm định có SHA256 của puzzle nguồn và chứng nhận bước mở đầu đã
đối chiếu với puzzle hiện tại. `output/verification.txt` lưu kết quả chạy test
sau lần dọn project. Giữ bộ test và module thực nghiệm để kiểm tra lại khi sửa
source; đây là các công cụ cần chạy nhiều lần.

## Tài liệu bài nộp

`AI - Project 2.pdf` là đề bài. `Report.pdf` và `docs/REPORT.md` là bản cũ, chưa
cập nhật đầy đủ theo source hiện tại. Báo cáo và video đang được để sau theo
yêu cầu của nhóm. Cần cập nhật lớp, phân công thực tế, tỷ lệ hoàn thành, số
liệu và link video trước khi nộp.
Nguồn tham khảo ở `docs/REFERENCES.md`; prompt AI ở `docs/AI-PROMPTS.md`.
