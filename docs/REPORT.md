# Griductive Solver - Báo cáo kỹ thuật

GRIDUCTIVE

Project Lab 2 · Griductive Solver

CSC14003 - Introduction to Artificial Intelligence

Ngày lập báo cáo 05/11/2026

Thành viên | MSSV

Phan Ngọc Thức | 24120228

Nguyễn Lê Minh Quân | 24120219

Tống Phúc Thiện | 24120141

Bùi Phương Nam | 24120502

Phan Gia Phúc | 24120503

Lớp học phần chờ nhóm cung cấp

Bản kỹ thuật chờ xác nhận thông tin nộp bài

Phần mềm, bộ màn, kiểm thử và thực nghiệm đã được triển khai. Phân công thực tế, phần trăm hoàn thành và liên kết Google Drive của video cần được nhóm xác nhận trước khi nộp.

Video Google Drive chờ tải video và kiểm tra quyền xem ẩn danh


---

1. Kế hoạch và kiến trúc

Sản phẩm có một engine Python dùng chung và hai cách hiển thị Realistic, Pixel 2D. GameEngine sở hữu nghiệm, clue chưa mở và lịch sử đã chấp nhận. LogicAgent chỉ nhận PublicState, gồm tên, nghề, tọa độ, trạng thái đã chứng minh và clue đã mở.

PublicState bất biến giúp lời khai ẩn không bị đưa vào KB. Giao diện gửi một đề nghị phán quyết cho engine. Engine kiểm tra bằng SAT trên bản công khai trước khi cập nhật trạng thái và mở clue của nhân vật.

Phân công cá nhân

Thành viên | Phần việc thực tế | Hoàn thành

Phan Ngọc Thức | Chờ xác nhận | Chờ xác nhận

Nguyễn Lê Minh Quân | Chờ xác nhận | Chờ xác nhận

Tống Phúc Thiện | Chờ xác nhận | Chờ xác nhận

Bùi Phương Nam | Chờ xác nhận | Chờ xác nhận

Phan Gia Phúc | Chờ xác nhận | Chờ xác nhận

Các tỷ lệ cá nhân chưa được người dùng cung cấp. Báo cáo không suy đoán đóng góp hoặc gán đồng đều. Theo đề, điểm cá nhân được nhân với tỷ lệ hoàn thành của chính thành viên đó.

Các giai đoạn đã thực hiện

Đối chiếu đề và hỏi rõ extension. Xây dựng registry, CNF và DPLL. Nối phán quyết, hint, auto solve và trace vào GUI. Kiểm nghiệm 6 màn cùng hai cấu hình. Tạo lại đồ họa và kiểm tra việc đổi style giữa phiên chơi.


---

2. Mô hình bài toán

Với N thuộc {3, 4, 5}, mỗi người ở một ô có một biến Boolean C_i. Giá trị True nghĩa là Tội phạm, False nghĩa là Vô tội. Biến chính được đánh số từ 1 đến N² theo hàng, từ trái sang phải và từ trên xuống dưới. Tên hiển thị tuân thứ tự alphabet.

Mọi clue công khai đều đúng, kể cả clue của người phạm tội. Nghề và tên chỉ là thông tin hiển thị. KB tại bước t chỉ gồm CNF của clue đã mở và các unit clause cho trạng thái đã biết.

Clue | Ngữ nghĩa

FACT | Một người có trạng thái đã nêu.

SAME | Hai người có cùng trạng thái.

DIFFERENT | Hai người có trạng thái khác nhau.

EXACTLY(k,R) | Đúng k người thuộc R là Tội phạm.

AT_LEAST(k,R) | Ít nhất k người thuộc R là Tội phạm.

AT_MOST(k,R) | Nhiều nhất k người thuộc R là Tội phạm.

Clue đếm bắt buộc k là số nguyên và 0 ≤ k ≤ |R|. NO có thể biểu diễn bằng EXACTLY(0,R). ROW là hàng, COLUMN là cột. NEIGHBORS gồm 8 hướng kề và loại chính ô mốc. EXPLICIT là danh sách ô phân biệt, có thể rỗng.

Mở rộng vùng

CORNERS chọn bốn ô góc. UNION, INTERSECTION, DIFFERENCE kết hợp các vùng đã hỗ trợ và loại phần tử trùng. Lồng vùng có giới hạn 12 cấp để từ chối dữ liệu không hợp lệ một cách kiểm soát.


---

3. Comparison và Conditional

COMPARISON so sánh số Tội phạm trong hai vùng với =, !=, <, <=, >, >=. Một ô chung được tính một lần trong mỗi vùng. Hai vùng có thể chồng nhau hoặc rỗng.

CONDITIONAL biểu diễn A kéo theo B. Nó sai đúng khi A đúng và B sai. A và B có thể là bất kỳ clue hỗ trợ nào, bao gồm Comparison, counting clue và Conditional lồng nhau. Giá trị chân lý độc lập với việc người chơi đã mở các ô được nhắc tới.

~~~
{"type":"COMPARISON","op":">=",
 "left":{"type":"ROW","row":1},
 "right":{"type":"COLUMN","column":"A"}}
~~~

~~~
{"type":"CONDITIONAL",
 "if":{"type":"FACT","person":"A1","status":"CRIMINAL"},
 "then":{"type":"EXACTLY","k":1,
         "region":{"type":"CORNERS"}}}
~~~

Cùng một cây clue tạo câu chữ và metadata highlight. Từng nhánh vùng có khóa liên kết riêng. Conditional giữ khóa theo nhánh if/then, nên hover một vế sẽ chỉ vùng của vế đó.

Khả năng mở rộng

RegionHandler đăng ký resolve, describe và anchor. ClueHandler đăng ký validation, evaluator, encoding, description và tập ô liên quan. Encoder dùng một bộ cấp biến phụ cho toàn KB, tránh va chạm ID giữa các clue.


---

4. Chuyển tự động sang CNF

Ví dụ binary clue

SAME(A,B) tương đương (¬C_A ∨ C_B) ∧ (C_A ∨ ¬C_B). DIFFERENT(A,B) tương đương (C_A ∨ C_B) ∧ (¬C_A ∨ ¬C_B). FACT là một unit literal.

Ví dụ counting clue

Với R={A,B,C} và đúng 2 Tội phạm, ràng buộc ít nhất 2 cho các clause (A ∨ B), (A ∨ C), (B ∨ C). Ràng buộc nhiều nhất 2 cho clause (¬A ∨ ¬B ∨ ¬C). Giao của hai nhóm là EXACTLY(2,R).

Mã đếm trực tiếp vẫn có trong registry để minh họa và kiểm thử. KB chạy game dùng bộ đếm unary tái hiện bằng cổng Tseitin nhằm tránh số clause tổ hợp lớn ở vùng 25 ô.

~~~
T(i,j) = T(i-1,j) OR (C_i AND T(i-1,j-1))
T(i,0) = True; T(i,j) = False when j > i
AT_LEAST(k) = T(n,k)
AT_MOST(k)  = NOT T(n,k+1)
EXACTLY(k)  = T(n,k) AND NOT T(n,k+1)
~~~

Cổng z=a∧b sinh (¬z∨a), (¬z∨b), (z∨¬a∨¬b). Cổng OR dùng dạng đối ngẫu. Hằng số, cổng trùng và phủ định đối nhau được rút gọn. Một bộ đếm có số cổng O(n²).

Comparison x≥y là hội của các mệnh đề T_y(j) kéo theo T_x(j). Equality dùng hai chiều, inequality phủ định equality. Conditional dùng ¬A∨B trên literal tái hiện của hai vế. Do đó cả hai vế đều có thể là biểu thức lồng.

Các biến phụ bắt đầu sau N². Thống kê phân biệt biến chính, biến phụ và số clause. Không có CNF viết sẵn riêng cho từng puzzle.


---

5. DPLL và suy luận

Solver tự cài unit propagation, phát hiện clause rỗng, chọn biến xác định, phân nhánh đệ quy và quay lui. Mỗi vòng lan truyền xử lý đồng thời các unit clause rồi rút gọn công thức. SAT trả model đầy đủ cho cả các biến không còn bị ràng buộc.

~~~
DPLL(F, assignment)
  propagate unit clauses until fixed point
  if an empty clause exists: return UNSAT
  if F is empty: complete the assignment and return SAT
  choose variable deterministically
  recurse with variable=True
  if unsuccessful, recurse with variable=False
  if both branches fail: return UNSAT
~~~

Hai cấu hình khác nhau ở chọn biến. Ordered chọn ID nhỏ nhất. Frequency chọn biến xuất hiện nhiều nhất trong các clause còn lại, hòa thì chọn ID nhỏ nhất. Cả hai thử True trước False và ghi quyết định, lan truyền, quay lui, thời gian.

Kiểm tra hệ quả logic

Trước hết kiểm tra KB có SAT. Nếu UNSAT, trả INCONSISTENT. Với ô i chưa mở, KB∧¬C_i UNSAT chứng minh Tội phạm. KB∧C_i UNSAT chứng minh Vô tội. Nếu cả hai SAT, trả UNKNOWN.

Agent phân loại mọi người chưa xác định rồi chọn người bị ép trạng thái đầu tiên theo thứ tự hàng. Engine kiểm tra lại yêu cầu bằng KB công khai. Phán quyết ngược kết luận trả CONTRADICTED. Chưa có kết luận trả NOT_PROVABLE. Các phản hồi từ chối không đổi trạng thái và không mở clue.

Sau khi chấp nhận, engine thêm trạng thái và clue của đúng người đó. Trace lưu bước, clue đang hoạt động, assumption và kết quả SAT, verdict, ID cùng nội dung clue mới. Agent dừng khi giải xong, UNKNOWN, INCONSISTENT hoặc hết thời gian.


---

6. Uniqueness và kiểm thử

Kiểm tra nghiệm duy nhất tách riêng khỏi agent. Nó mã hóa toàn bộ clue trong chế độ kiểm định puzzle. Sau model đầu tiên, thêm clause chặn chỉ các biến chính. Nếu SAT lần hai thì có nhiều nghiệm. Nếu UNSAT lần hai thì nghiệm chính là duy nhất. Các cách gán biến phụ không được đếm thành nghiệm khác.

Nghiệm duy nhất không bảo đảm luôn mở được toàn bộ thẻ từ thông tin ban đầu. Vì vậy bộ kiểm thử xác nhận đồng thời uniqueness và một đường mở clue tuần tự cho cả 6 màn.

Bộ kiểm thử hiện gồm 46 test và đã chạy thành công. Chúng kiểm tra evaluator trực tiếp đối chiếu khả thỏa CNF với assumption cố định, vùng trùng và rỗng, k biên, Conditional lồng và implication có tiền đề sai, tính nguyên tử khi từ chối và việc retry.

Các kiểm tra GUI thực hiện click phán quyết thật, mở clue, giải hết 3×3, chuyển style giữa phiên, giữ highlight, khung thẻ đều, cuộn clue và bố cục đủ 25 ô.

Trường hợp cần phân biệt

KB=(A∨B) cho phép ít nhất một người là Tội phạm nhưng chưa buộc riêng A hay B. Dùng một model để mở A sẽ sai. Hai assumption của mỗi người đều SAT nên agent trả UNKNOWN.

KB chứa FACT(A,Criminal) cùng trạng thái đã biết A=Innocent là INCONSISTENT. Việc kiểm tra KB trước kiểm tra hệ quả tránh suy ra tùy ý từ công thức mâu thuẫn.

Một test UNSAT không có unit đầu vào dùng cả bốn clause trên hai biến để bắt buộc đi qua phân nhánh và quay lui. Một test khác xác nhận hai counting clue mâu thuẫn dùng chung namespace biến phụ.

Tái chạy

~~~
python -m unittest discover -s tests -v
python -m griductive.experiments
~~~


---

7. Thiết lập thực nghiệm

Cùng 6 puzzle được chạy bằng Ordered và Frequency, mỗi kích thước có 2 puzzle. Màn 5×5 thứ nhất có nhiều clue đếm liên kết, còn các màn còn lại chủ yếu là chuỗi suy luận có kiểm soát. Đây là bộ test chức năng có độ khó không đồng đều.

Môi trường đo Windows, Python 3.14.4, PySide6 6.12.0, CPU Intel Core i5-12450HX. Solver dùng CPU. Mỗi cấu hình chạy một lượt trên bộ màn cố định. Thời gian nhỏ chịu nhiễu của hệ điều hành và quá trình tạo ảnh khác đang chạy.

Màn | Biến chính | Biến phụ | Clause cuối | Bước mở

3x3-01 | 9 | 23 | 87 | 8

3x3-02 | 9 | 23 | 87 | 8

4x4-01 | 16 | 32 | 128 | 15

4x4-02 | 16 | 30 | 122 | 15

5x5-01 | 25 | 601 | 1853 | 22

5x5-02 | 25 | 43 | 179 | 24

Số clause và biến phụ trong bảng là KB cuối phiên. Thời gian thực nghiệm bao gồm dựng KB, agent phân loại và engine kiểm tra lại verdict. SAT calls cộng cả truy vấn của agent và engine. Kiểm tra uniqueness được chạy riêng và không cộng vào các chỉ số giải tuần tự.

Mọi màn đều SOLVED và UNIQUE. Không có timeout hay thất bại trong 12 lượt này. Chương trình vẫn giữ dòng kết quả cho TIMEOUT, UNKNOWN và lỗi trạng thái khi xảy ra. Giới hạn mặc định 30 giây được kiểm tra giữa các bước và mỗi SAT query có giới hạn riêng.

Dữ liệu gốc cùng trace được lưu trong output/experiments. Mỗi lần chạy sẽ ghi lại kết quả trên cùng danh sách màn, thuận tiện đối chiếu thay đổi thuật toán.


---

8. Kết quả và nhận xét

Màn | Cấu hình | SAT | QĐ | LT | QL | Giây

3x3-01 | O | 96 | 0 | 1084 | 0 | 0.009

3x3-01 | F | 96 | 0 | 1084 | 0 | 0.009

3x3-02 | O | 96 | 0 | 938 | 0 | 0.009

3x3-02 | F | 96 | 0 | 938 | 0 | 0.010

4x4-01 | O | 285 | 0 | 4807 | 0 | 0.046

4x4-01 | F | 285 | 0 | 4807 | 0 | 0.043

4x4-02 | O | 285 | 0 | 4323 | 0 | 0.044

4x4-02 | F | 285 | 0 | 4323 | 0 | 0.044

5x5-01 | O | 572 | 38 | 100398 | 0 | 0.988

5x5-01 | F | 572 | 38 | 100398 | 0 | 0.946

5x5-02 | O | 672 | 0 | 14826 | 0 | 0.171

5x5-02 | F | 672 | 0 | 14826 | 0 | 0.171

O là Ordered, F là Frequency. QĐ là quyết định, LT là lan truyền và QL là quay lui. Các chuỗi clue đơn giản được giải chỉ bằng unit propagation, nên hai cấu hình có cùng bộ đếm logic.

Màn 5×5-01 dùng nhiều biến phụ và nhiều lan truyền hơn, tạo chênh lệch thời gian rõ giữa hai loại màn. Hai heuristic vẫn có cùng số quyết định trong bộ này. Một lượt đo trên sáu màn chưa đủ để kết luận cấu hình nào luôn nhanh hơn.

Các giới hạn còn lại gồm DPLL chưa có clause learning hay watched literals, độ sâu Python hạn chế puzzle lớn hơn phạm vi đề, và auto solve thực hiện truy vấn trên luồng GUI. Những truy vấn khó hơn bộ test có thể làm giao diện chờ trong thời gian giới hạn của solver.


---

9. Hai bộ giao diện

Realistic và Pixel 2D dùng cùng engine và giữ nguyên tiến độ khi chuyển. Cả hai hiển thị đủ 25 ô, cùng chú thích màu, vùng highlight và các điều khiển chơi.

Realistic · chân dung và background theo nghề

Pixel 2D · nhân vật chibi và cảnh nền pixel

Menu Công cụ cung cấp 6 màn và Load JSON. Solver dock chỉ xuất hiện khi được yêu cầu. Hint dùng PublicState. Nút đồ họa thay hình ảnh và cách vẽ, không đặt lại phiên chơi.


---

10. Tham khảo và phụ lục AI

AI - Project 2.pdf, CSC14003, bản đề do người dùng cung cấp, 9 trang.

Martin Davis, George Logemann, Donald Loveland. A Machine Program for Theorem-Proving. Communications of the ACM, 5(7), 394-397, 1962. DOI 10.1145/368273.368557.

Qt for Python, QPixmap và QPainter. https://doc.qt.io/qtforpython-6/

Griductive. https://knotwise.games/games/griductive và hướng dẫn chơi chính thức.

Clues by Sam. https://cluesbysam.com/ - tham khảo tương tác thẻ và highlight.

Gamedev agent skills. https://github.com/gamedev-skills/awesome-gamedev-agent-skills

Stable Diffusion 1.5 Inpainting và Diffusers. https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-inpainting

Các repo tham khảo trước đây và phạm vi đã đọc được ghi riêng trong docs/REFERENCES.md. Không dùng SAT library, Z3 hay LLM làm solver khi chạy game. Đồ họa sinh mới bằng ImageGen và masked inpainting, không sao chép asset của game tham khảo.

Cách sử dụng AI

Codex hỗ trợ phân tích đề, đề xuất cấu trúc, viết và sửa mã, tạo kiểm thử, chạy thực nghiệm, xây dựng báo cáo và sản xuất đồ họa. Các kiểm tra tự động nêu trong báo cáo đã được chạy trong workspace. Đóng góp thực tế của từng sinh viên vẫn cần nhóm tự xác nhận.

Các nhóm prompt chính gồm xây engine tách private/public, tự cài DPLL và kiểm tra entailment, thêm Comparison với ≥/≤/≠ và Conditional nhận hai clue bất kỳ, tạo 25 sprite đồng bộ và tạo bản pixel chibi dùng chung engine. Prompt đồ họa và lịch sử chỉnh sửa được lưu trong docs/AI-PROMPTS.md.

Video và đóng gói

Video cục bộ output/Demo.mp4 trình bày giao diện, từ chối đoán, phán quyết hợp lệ, Hint, Auto Solve, Load, Restart và chuyển style. Đây là demo tự động thao tác trên GUI thật, có phụ đề tiếng Việt.

Theo đề, nhóm cần tải video lên Google Drive, đặt Anyone with the link, kiểm tra trong cửa sổ ẩn danh rồi điền URL vào docs/team.json và báo cáo. Liên kết hiện chưa được cung cấp.

Gói nộp phải mang tên các MSSV, chứa Source và Report.pdf. Nếu trên 20 MB thì nộp qua Google Drive theo hướng dẫn đề. Không sửa bài sau hạn nộp.
