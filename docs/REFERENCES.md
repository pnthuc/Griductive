# Research references

## 2. Nguồn đã đọc và cách sử dụng

Nguồn quyết định yêu cầu: AI - Project 2.pdf trong project và bảng hỏi đáp do người dùng gửi.
Các repo khác chỉ là tham khảo, không chứng minh chương trình đúng hoặc đáp ứng rubric.

### Bộ skill người dùng chỉ định

- https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/main/router/SKILL.md
- https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/main/skills/genres/puzzle/SKILL.md
- https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/main/skills/disciplines/game-ui-ux/SKILL.md

Đã đọc router và toàn bộ hai skill puzzle, game-ui-ux; không cài toàn bộ bộ skill.
Áp dụng: model bàn độc lập với hình ảnh; xử lý lượt xác định; kiểm tra lượt trước khi đổi trạng thái;
layout bằng container; cập nhật GUI qua sự kiện; điều hướng bàn phím; kiểm soát input khi animation.
Không tự đưa các yêu cầu của game khác (điểm số, giới hạn thời gian, undo, cascade, gamepad)
thành yêu cầu của bài lab. Không dùng mặc định Godot của router vì bài yêu cầu Python.

### Giao diện và luật game gốc

- https://knotwise.games/games/griductive
- https://knotwise.games/games/griductive/how-to-play
- https://cluesbysam.com/

Đã mở hai giao diện trong trình duyệt, xem màn chào/tutorial và các thẻ hiện trên trang;
chưa kiểm thử hoàn chỉnh các tương tác verdict/hint của hai game.
Trang hướng dẫn Griductive xác định tên theo trái sang phải rồi trên xuống dưới,
phù hợp ví dụ người dùng đã cung cấp.
Tham khảo: thẻ nhân vật, reveal clue, spotlight vùng, hint tăng dần.
Không nhập thêm luật trên website vào bài lab nếu PDF không yêu cầu.

### Mã nguồn tham khảo

- https://github.com/safina57/clues-by-sam-solver
  - Đã đọc src/models/game_state.py và src/solver/engine.py.
  - README dùng Observe → Parse → Deduce → Act, LLM dịch clue và Z3 giải.
  - Học cách tách dữ liệu nhân vật, KB, hành động; không dùng LLM/Z3 thay encoder/DPLL tự cài.
  - engine.py có eval chuỗi constraint; thiết kế của mình dùng JSON dữ liệu và registry,
    không thực thi chuỗi trong puzzle.
- https://github.com/TranTai35/griductive-solver
  - Chỉ xem README và cấu trúc thư mục; mô tả GUI Pygame, public state và bộ benchmark.
- https://github.com/WadeWartz/Griductive-Solver
  - Chỉ xem README và cấu trúc; mô tả Tkinter, clue inspector và deduction log.
  - Bảng benchmark của chính README có trường hợp unique=False, nên không lấy các màn
    hay tuyên bố của repo làm bằng chứng đáp ứng yêu cầu nghiệm duy nhất.

Chưa sao chép mã hoặc tài sản từ các repo. Khi sử dụng về sau phải ghi nguồn cụ thể,
xem license của đúng nội dung và lưu vào tài liệu tham khảo/phụ lục AI.

### Mẫu Python GUI chính thức

- https://doc.qt.io/qtforpython-6/examples/example_widgets_animation_animatedtiles.html
- https://doc.qt.io/qtforpython-6.11/examples/example_widgets_thread_signals.html
- https://doc.qt.io/qtforpython-6/examples/

Tham khảo animation theo thuộc tính, layout và worker báo kết quả qua signal.


### Nhật ký sử dụng AI cho đồ họa

Các prompt tạo hình được giữ trong `docs/AI-PROMPTS.md` để làm phụ lục AI.
Các script tạo dữ liệu và ảnh xem thử đã hoàn tất nhiệm vụ được dọn khỏi bản
source hiện tại; game chỉ đọc các atlas đã có trong `assets/`.
