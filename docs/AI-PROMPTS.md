# Nhật ký Sử dụng AI Tạo sinh và Các Prompt Tiêu biểu

Tài liệu này bổ sung chi tiết cho **Phụ lục A** của báo cáo kỹ thuật (`Report.pdf`), ghi lại phạm vi sử dụng các công cụ AI tạo sinh trong dự án **Griductive Solver**, các câu lệnh (prompt) thực tế đã dùng và cách nhóm kiểm chứng đầu ra theo mục **4.6** của đề bài.

---

## 1. Nguyên tắc sử dụng và phạm vi áp dụng

1. **Thuật toán cốt lõi do nhóm tự cài đặt:** Toàn bộ các mô-đun trong `griductive/engine/` (`models.py`, `regions.py`, `clues.py`, `cnf.py`, `sat.py`, `game.py`) do các thành viên trực tiếp thiết kế và cài đặt bằng Python thuần, không dùng thư viện giải SAT ngoài.
2. **Phạm vi hỗ trợ của AI:**
   - Tra cứu tài liệu PySide6 (`QMainWindow`, `QDockWidget`, `QPainter`, `QThread`/`Signal`) và gợi ý các trường hợp biên khi viết unit test.
   - Sinh tài sản đồ họa 2D pixel cho 25 nhân vật, 25 đạo cụ nghề nghiệp và ảnh nền bến cảng trong thư mục `assets/` (thay vì lấy ảnh từ trò chơi có sẵn).
   - Chuyển kịch bản tiếng Việt của nhóm sang giọng đọc thuyết minh cho video trình diễn (ElevenLabs TTS).

---

## 2. Các prompt tra cứu kỹ thuật và gợi ý kiểm thử

### 2.1. Gợi ý ca kiểm thử biên cho bộ phân giải vùng và CNF
```text
Đề xuất các trường hợp biên dễ sót khi kiểm thử bộ phân giải vùng tập hợp
(UNION, INTERSECTION, DIFFERENCE) và manh mối CONDITIONAL lồng nhau trên lưới
N x N (N thuộc {3, 4, 5}), sao cho có thể kiểm tra chéo giữa hàm evaluate()
trực tiếp trên phép gán đầy đủ và kết quả khả thỏa của công thức CNF.
```
- **Cách nhóm kiểm chứng:** Chọn lọc và tự viết các bài kiểm thử trong `tests/test_core.py`, `tests/test_solver.py` và `tests/test_rule_extensions.py` (kiểm tra vét cạn $2^9$ phép gán trên bàn $3\times3$, vùng hiệu rỗng `DIFFERENCE(R, R)` với `EXACTLY(0, ...)`, trùng biến trong `SAME(A1, A1)` / `DIFFERENT(A1, A1)`, và giới hạn lồng quá 12 cấp).

### 2.2. Tra cứu giao tiếp luồng nền an toàn trong PySide6
```text
Trong PySide6, khi QMainWindow gửi các yêu cầu giải SAT sang một QThread chạy
hàng đợi tuần tự, làm thế nào để hủy phép tìm kiếm đang chạy khi người chơi
bấm Restart hoặc đổi màn mới mà không xảy ra race condition ghi đè kết quả cũ
lên giao diện mới?
```
- **Cách nhóm kiểm chứng:** Cài đặt cơ chế bản sao `GameEngine.fork()` kết hợp `threading.Event` kiểm tra ngay trong vòng lặp DPLL (`SolverCancelled`) cùng cặp chỉ số `(generation, request)` tại `griductive/ui/game_controller.py` và kiểm thử trường hợp tranh chấp công bố kết quả trong `tests/test_background.py`.

---

## 3. Các prompt tạo tài sản đồ họa trong `assets/`

### 3.1. Sinh khung biểu cảm nhân vật đồng nhất tỉ lệ (`assets/characters/pixel/sprites.png`)
Prompt gốc định hình quy tắc khóa vị trí khuôn mặt và đường mắt cho nhân vật đầu tiên (Ada — Bác sĩ):
```text
Make a game animation sprite atlas of Ada, a female doctor. Exact grid of
square frames on a transparent RGBA background, no text, labels, borders, or
gutters. CRITICAL ANIMATION REGISTRATION: keep face center, eye line, head
scale, hair silhouette and shoulders in exactly same position across all
frames. Normal clothes for neutral/blink/startled/relieved/smile frames;
charcoal and ivory striped prison shirt without occupational props for the
criminal frames.
```

Prompt chuẩn hóa phong cách pixel viền mảnh áp dụng đồng bộ cho cả 25 nhân vật trong bảng tên `assets/characters/characters.json`:
```text
Use image1 as the character identity and costume reference, and image2 as the
pixel-art style reference (thin dark contour, controlled warm palette, stepped
pixel edges). Produce a 4-column by 2-row sprite atlas of the same character in
eight equal square cells with consistent standing height and head/body ratio:
1 neutral eyes open, 2 neutral blinking closed eyes, 3 surprised, 4 relieved
closed-eye smile, 5 friendly open-eye smile, 6 worried in striped prison
clothes, 7 remorseful closed eyes in prison clothes, 8 neutral repeated.
Clean RGBA alpha transparency with empty margin around every tile, no floor
shadow, no text or grid lines.
```

### 3.2. Chỉnh sửa chớp mắt bằng mặt nạ (Stable Diffusion 1.5 Inpainting)
Với những nhân vật cần đồng bộ mí mắt nhắm/mở mà không làm lệch chi tiết mũ, kính hoặc trang phục, nhóm chỉ khoanh mặt nạ quanh vùng mắt và giữ nguyên kênh alpha gốc ngoài mặt nạ:
```text
eyes naturally open with dark brown irises, subtle small pupils, matching
eyelids, same expression and eyebrows, crisp video game portrait
```
- **Cách nhóm kiểm chứng:** Mô-đun `tests/test_sprite_registration.py` quét toàn bộ $25 \times 7 = 175$ ô kích thước `256×256`, xác nhận dải viền trong suốt 8 pixel ở cả bốn cạnh mỗi ô và kiểm tra chiều cao hiển thị giữa các khung của cùng một nhân vật không lệch quá ngưỡng pixel cho phép; khi cập nhật lại 7 khung của nhân vật Finn, nhóm đối chiếu từng byte trên 24 hàng nhân vật còn lại để bảo đảm không làm thay đổi các ô khác.

### 3.3. Đạo cụ 25 nghề nghiệp (`assets/scenery/pixel-profession-props.png`)
```text
Create a 5-column by 5-row pixel-art prop atlas (25 equal rectangular tiles,
no borders, no text, transparent RGBA background). Place small profession
objects in the right half and lower area so the left half remains open.
Row-major order matching the 25 professions: medical, painting, journalism,
law, academic, cooking, library, mechanics, gardening, photography,
architecture, watchmaking, musician, firefighting, floristry, tailoring,
aviation, baking, detective, engineering, bookselling, nursing, sailing,
music teaching, botany.
```

### 3.4. Ảnh nền phố biển (`assets/ui/harbor.png`)
```text
Wide 16:9 pixel-art background for a desktop detective board game. Bright
coastal town atmosphere with soft sky and sea tones in the center 85 percent
of the canvas so a 5x5 card grid remains clearly readable; subtle shutters,
flowers, distant lighthouse, and harbor dock kept strictly along the outer
margins. No UI frames, no characters, no text.
```

---

## 4. Thuyết minh tiếng Việt cho Video trình diễn (`Demo.mp4`)

- Kịch bản 16 phân đoạn tiếng Việt do nhóm biên soạn bám sát sáu phần nội dung (giới thiệu kiến trúc, khám phá giao diện, phán quyết thủ công `NOT_PROVABLE` so với `CONTRADICTED`, Sổ giải DPLL, giải tự động bàn $4\times4$ / $5\times5$ và tổng kết thực nghiệm).
- Dịch vụ ElevenLabs TTS chuyển văn bản từng đoạn thành tệp thoại tiếng Việt, chuẩn hóa độ lớn âm thanh theo chuẩn phát thanh (`-16.4 LUFS`) và ghép khớp với hình quay trực tiếp từ cửa sổ ứng dụng kèm phụ đề tiếng Việt và 6 mốc chương MP4.
