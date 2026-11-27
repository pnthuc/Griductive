# Tài liệu Tham khảo và Nguồn Đối chiếu

Tài liệu này liệt kê toàn bộ các công trình học thuật, đặc tả học phần, tài liệu thư viện và các kho mã nguồn mở đã khảo sát trong quá trình thực hiện **Griductive Solver**, đồng bộ với 12 mục trích dẫn BibTeX trong báo cáo kỹ thuật HCMUS (`Report.pdf`).

---

## 1. Danh mục 12 tài liệu tham khảo chính thức

1. **Khoa Công nghệ Thông tin, Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM.** *CSC14003: Introduction to Artificial Intelligence — Project 2: Griductive Solver* (Đề đồ án học phần, mục 4.1–4.7 & 5).
2. **Knotwise Games.** *Griductive: How to Play*. https://knotwise.games/games/griductive/how-to-play
3. **Clues by Sam.** *Clues by Sam*. https://cluesbysam.com/
4. **The Qt Company.** *Qt for Python 6: QThread*. https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html
5. **G. S. Tseitin (1983).** *On the Complexity of Derivation in Propositional Calculus*. Trong *Automation of Reasoning*, tập 2, Springer, tr. 466–483. https://doi.org/10.1007/978-3-642-81955-1_28
6. **Martin Davis, George Logemann và Donald Loveland (1962).** *A Machine Program for Theorem-Proving*. *Communications of the ACM*, 5(7), tr. 394–397. https://doi.org/10.1145/368273.368557
7. **Plotly.** *Dash Documentation: Basic Callbacks*. https://dash.plotly.com/basic-callbacks
8. **Stable Diffusion v1.5.** *Stable Diffusion Inpainting: Model Card*. https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-inpainting
9. **gamedev-skills.** *Awesome Gamedev Agent Skills*. https://github.com/gamedev-skills/awesome-gamedev-agent-skills
10. **safina57.** *Clues by Sam Solver*. https://github.com/safina57/clues-by-sam-solver
11. **TranTai35.** *Griductive Solver*. https://github.com/TranTai35/griductive-solver
12. **WadeWartz.** *Griductive-Solver*. https://github.com/WadeWartz/Griductive-Solver

---

## 2. Phạm vi khảo sát và nguyên tắc áp dụng

Đề bài `AI - Project 2.pdf` là nguồn quy chuẩn duy nhất cho luật chơi, kiến trúc ranh giới công khai/ẩn và yêu cầu thuật toán. Nhóm **không sao chép mã nguồn hay tài sản đồ họa** từ các dự án bên ngoài; toàn bộ bộ biên dịch CNF ([cnf.py](../griductive/engine/cnf.py)) và bộ giải DPLL ([sat.py](../griductive/engine/sat.py)) được tự cài đặt từ đầu bằng Python.

### 2.1. Nền tảng lý thuyết CNF và DPLL
- Áp dụng phép biến đổi **Tseitin** [5] với ràng buộc tương đương hai chiều cho cổng `AND`/`OR` kết hợp quy hoạch động đếm ngưỡng unary để giữ kích thước CNF bậc đa thức $O(|R|^2)$ và an toàn khi lồng dưới phép phủ định của `CONDITIONAL`.
- Cài đặt thủ tục **DPLL** [6] với vòng lặp lan truyền mệnh đề đơn, phát hiện xung đột, phân nhánh đệ quy hai chiến lược (`ordered`, `frequency`) và kiểm chứng hệ quả logic bằng phản chứng.

### 2.2. Trò chơi gốc và hướng dẫn thiết kế giao diện
- **Griductive** [2] và **Clues by Sam** [3]: tham khảo quy ước đặt tên nhân vật theo thứ tự alphabet từng hàng (trái sang phải, trên xuống dưới), cơ chế lật thẻ mở lời khai mới và cách tô sáng các ô liên quan khi đọc manh mối; không đưa thêm các luật ngoài phạm vi đề bài.
- **Awesome Gamedev Agent Skills** [9] (`router/SKILL.md`, `skills/genres/puzzle/SKILL.md`, `skills/disciplines/game-ui-ux/SKILL.md`): áp dụng nguyên tắc tách mô hình bàn chơi khỏi tầng hiển thị, kiểm chứng hợp lệ trước khi ghi trạng thái, bố cục co giãn theo khung chứa và kiểm soát đầu vào khi đang chạy hoạt ảnh.
- **Qt for Python 6** [4] & **Plotly Dash** [7]: tham khảo mô hình xử lý tác vụ nền qua `QThread`/`Signal` cho Desktop PySide6 và kiến trúc callback kết hợp `dcc.Store` ở chế độ `session` cho bản Web.

### 2.3. Đối chiếu với các kho mã mở cùng chủ đề
- `safina57/clues-by-sam-solver` [10]: khảo sát cách tách lớp trạng thái và hành động trong `game_state.py`; khác với hướng dùng LLM dịch câu và thư viện Z3 hoặc `eval` chuỗi của repo này, dự án dùng đặc tả JSON có cấu trúc thông qua `RegionRegistry`/`ClueRegistry` và bộ giải DPLL tự viết.
- `TranTai35/griductive-solver` [11] và `WadeWartz/Griductive-Solver` [12]: chỉ khảo sát `README` và cấu trúc thư mục để đối chiếu cách trình bày bảng thực nghiệm và nhật ký suy luận; nhận thấy bảng mẫu của [12] còn chứa trường hợp `unique=False`, do đó nhóm xây dựng bộ 6 câu đố riêng và kiểm định `UNIQUE` + giải được từng bước bằng `tests/test_solver.py` và [puzzle-quality.json](../output/puzzle-quality.json).

---

## 3. Hồ sơ đồ họa và phụ lục AI tạo sinh

- Nhật ký chi tiết các prompt sinh minh họa nhân vật, quy trình sửa ảnh có mặt nạ (*inpainting* [8]) và kiểm định đăng ký khung hình được lưu tại [AI-PROMPTS.md](AI-PROMPTS.md).
- Lúc chạy, cả hai giao diện Desktop và Web chỉ đọc trực tiếp bộ manifest trong `assets/` cùng các tệp atlas/ảnh nền dùng chung trong `public/images/` và `public/pixel/`, không cần công cụ sinh ảnh hay thư viện xử lý ảnh ngoài.
