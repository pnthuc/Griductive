# Kiến trúc Hệ thống và Thiết kế Thuật toán

Tài liệu này mô tả chi tiết ranh giới dữ liệu, quy tắc suy luận không đoán mò (*no-guess*), ngôn ngữ manh mối và vùng (kể cả phần mở rộng), bộ biên dịch CNF tự động, bộ giải DPLL tự cài đặt, cấu trúc nhật ký `trace`, phép kiểm tra nghiệm duy nhất và cách đọc số liệu thực nghiệm của **Griductive Solver**. Mọi ký hiệu và số liệu đều đồng bộ với báo cáo kỹ thuật HCMUS (`Report.pdf`).

---

## 1. Kiến trúc phân tầng và ranh giới `GameEngine` / `LogicAgent`

Theo mục 4.1 và 4.4 của đề bài, kiến trúc tách rời nghiêm ngặt quyền sở hữu dữ liệu ẩn với tác tử suy luận công khai qua 6 mô-đun lõi trong `griductive/engine/`:

| Mô-đun | Trách nhiệm chính | Dữ liệu được phép truy cập |
| --- | --- | --- |
| [models.py](../griductive/engine/models.py) | Định nghĩa `Board`, `Character`, `PrivatePuzzle`, `PublicState`, hàm đóng băng đệ quy `freeze()` và bộ nạp `load_puzzle()`. | Kiểm tra cấu trúc JSON, tọa độ, thứ tự tên alphabet và tính đúng của toàn bộ lời khai dưới `solution` khi nạp tệp. |
| [regions.py](../griductive/engine/regions.py) | Định nghĩa lớp trừu tượng `Region`, `RegionRegistry` và 8 kiểu vùng (4 cơ sở + 4 mở rộng). | Chỉ nhận `Board` và đặc tả JSON của vùng. |
| [clues.py](../griductive/engine/clues.py) | Định nghĩa `Clue`, `ClueRegistry`, 8 kiểu manh mối (6 cơ sở + 2 mở rộng), bộ đánh giá trực tiếp `evaluate()`, biểu thức `expression()` và cây tham chiếu `clue_parts()`. | Chỉ nhận đặc tả manh mối, `Board` và phép gán khi đánh giá ngữ nghĩa. |
| [cnf.py](../griductive/engine/cnf.py) | Cấp phát biến chính/biến phụ, cổng Tseitin có khử trùng (`Encoder.gate`), quy hoạch động đếm ngưỡng unary (`Encoder.thresholds`) và `build_knowledge_base()`. | Chỉ đọc `PublicState` (`state.clues` đã mở và `state.statuses` đã chứng minh). |
| [sat.py](../griductive/engine/sat.py) | Thủ tục DPLL tự cài đặt (`solve`) với hai chiến lược `ordered` và `frequency`, hỗ trợ `assumptions`, hạn thời gian và cờ hủy. | Chỉ nhận danh sách mệnh đề số nguyên, tổng số biến và giả định tạm thời. |
| [game.py](../griductive/engine/game.py) | Điều phối phiên chơi `GameEngine`, tác tử suy diễn `LogicAgent` và hàm kiểm định ngoại tuyến `check_uniqueness()`. | `GameEngine` giữ `PrivatePuzzle`; `LogicAgent` **chỉ** nhận `PublicState` bất biến. |

### Cơ chế cô lập trạng thái công khai (`PublicState`)
- `PrivatePuzzle` giữ `solution` (nghiệm đầy đủ) và toàn bộ `clues` (kể cả các thẻ đang úp) bên trong thuộc tính riêng `GameEngine._puzzle`.
- Mỗi lần gọi `GameEngine.public_state()`, engine tạo một đối tượng `@dataclass(frozen=True) PublicState` chỉ chứa `board`, `characters`, `statuses` (các ô đã mở) và `clues` (các lời khai đã lật). Mọi `dict` và `list` lồng bên trong đều được gói bằng `MappingProxyType` và `tuple` qua `freeze()`, ngăn mọi hành vi sửa đổi hoặc rò rỉ dữ liệu ẩn (kiểm chứng tại `tests/test_core.py`: `test_public_state_does_not_publish_hidden_data` và `test_hidden_changes_do_not_change_public_state`).

### Điều phối phiên chơi trên Desktop và Web
- **Desktop Cozy Harbor ([griductive/ui/](../griductive/ui/)):** Giao diện PySide6 dùng bảng màu phố biển sáng, thẻ nghi phạm kích thước đồng nhất gắn bộ 25 nhân vật × 7 khung biểu cảm pixel từ `public/images/` và `public/pixel/`. Thanh tiêu đề cung cấp menu chọn 6 vụ án theo cỡ bàn (`CaseMenu`), tiến độ mở thẻ, các nút **Gợi ý**, **Làm lại**, **Sổ giải**, và menu công cụ (**Tự động giải**, **Mở màn chơi JSON…**, **Làm lại màn này**, bật/tắt **Hiệu ứng chuyển động**). Mọi tác vụ SAT chạy tuần tự trên luồng nền [engine_worker.py](../griductive/ui/engine_worker.py) thông qua bản sao tạm `GameEngine.fork()`. Nếu người chơi đổi màn, làm lại hoặc tạm dừng giữa chừng, cờ `cancel` ném `SolverCancelled` ngay trong DPLL và hủy bản sao `fork()` mà không làm hỏng trạng thái trên màn hình.
- **Web Plotly Dash ([griductive/web.py](../griductive/web.py), [griductive/web_game.py](../griductive/web_game.py)):** Giao diện trình duyệt dựng cây thành phần và callback bằng Python kết hợp bảng kiểu và tương tác khách tại `public/board.css` và `public/board.js`; toàn bộ luật chơi và suy luận chạy trên máy chủ Python. `dcc.Store(storage_type="session")` chỉ lưu mã màn và lịch sử nước đi công khai (`history`). Ở mỗi yêu cầu, `web_game.restore()` tạo `GameEngine` mới và phát lại từng nước qua `engine.submit()`: mọi lịch sử bị chỉnh sửa hoặc chứa nước đoán mò đều bị từ chối ngay lập tức, bảo đảm đáp án và lời khai chưa mở của các màn tích hợp sẵn không bao giờ đi xuống trình duyệt.

---

## 2. Suy luận không đoán mò (*No-Guess*) và lưu nhân chứng mô hình

### Nguyên lý hệ quả logic và chứng minh phản chứng
Một mô hình thỏa mãn ($\text{SAT}$) chỉ cho biết một cách gán khả dĩ, không đủ để kết luận trạng thái của nhân vật. Ở bước suy luận $t$, gọi $L_t$ là tập lời khai đã mở và $S_t$ là tập ô đã biết trạng thái ($\ell_i = C_i$ nếu ô $i$ là `CRIMINAL`, $\ell_i = \neg C_i$ nếu `INNOCENT`). Cơ sở tri thức công khai là:

$$
KB_t = \bigwedge_{q \in L_t} \operatorname{CNF}(q) \;\land\; \bigwedge_{i \in S_t} (\ell_i).
$$

Với ô chưa mở $i$, một phán quyết chỉ hợp lệ khi đúng trong **mọi** mô hình của $KB_t$:
- $KB_t \models C_i \iff KB_t \land \neg C_i$ là `UNSAT` $\implies$ bắt buộc là **`CRIMINAL`**.
- $KB_t \models \neg C_i \iff KB_t \land C_i$ là `UNSAT` $\implies$ bắt buộc là **`INNOCENT`**.
- Nếu cả $KB_t \land \neg C_i$ và $KB_t \land C_i$ đều `SAT`, ô $i$ mang trạng thái **`UNKNOWN`** (tác tử tuyệt đối không đoán và không lật thẻ).
- Nếu bản thân $KB_t$ đã `UNSAT`, trạng thái là **`INCONSISTENT`** (phải kiểm tra trước tiên vì từ một KB mâu thuẫn có thể suy ra mọi mệnh đề).

### Phân biệt các kết quả kiểm chứng trong `GameEngine.submit`
Khi người chơi hoặc chế độ tự giải gửi đề nghị `(cell, verdict)` (với literal đề nghị $p \in \{C_i, \neg C_i\}$):
1. `ALREADY_REVEALED`: Ô đã mở từ trước; giữ nguyên bàn.
2. `INCONSISTENT`: Bản thân $KB_t$ vô nghiệm, hoặc phán quyết đã chứng minh mâu thuẫn với nghiệm ẩn của tệp dữ liệu lỗi.
3. `ACCEPTED`: $KB_t$ khả thỏa và $KB_t \land \neg p$ trả `UNSAT`. Engine ghi nhận trạng thái, lật mở lời khai của `cell` để tạo $KB_{t+1}$ và ghi một mục vào `trace`.
4. `CONTRADICTED`: $KB_t \land \neg p$ khả thỏa nhưng $KB_t \land p$ trả `UNSAT` (tri thức hiện có chứng minh trạng thái ngược lại mới đúng). Giữ nguyên bàn, không lộ lời khai ẩn.
5. `NOT_PROVABLE`: Cả $KB_t \land \neg p$ và $KB_t \land p$ đều khả thỏa. Giữ nguyên bàn, không lộ lời khai ẩn.

### Tối ưu lưu nhân chứng trong `LogicAgent._verdicts`
Khi duyệt các ô chưa mở theo thứ tự hàng (`A1, B1, ..., A2, ...`), lời gọi cơ sở `solve(KB_t)` trả về một mô hình hoàn chỉnh $M_0$. Nếu $M_0(C_i) = \mathrm{True}$ thì $KB_t \land C_i$ chắc chắn `SAT` (đã có nhân chứng dương), nên tác tử chỉ cần kiểm tra thêm $KB_t \land \neg C_i$. Hơn nữa, mỗi lần một truy vấn giả định trả về mô hình mới $M'$, hàm `record(M')` cập nhật tập `can_be_true` và `can_be_false` cho toàn bộ biến chính còn lại. Nhờ vậy, sau 1 truy vấn cơ sở, mỗi ô chưa mở tốn **tối đa 1 truy vấn SAT bổ sung** (và tốn **0 truy vấn** nếu các mô hình trước đó đã chứng kiến cả hai dấu `True` và `False` cho ô đó).

---

## 3. Ngôn ngữ manh mối, hệ thống vùng và các phần mở rộng

Trên bàn $N \times N$ ($N \in \{3, 4, 5\}$), cột đánh chữ từ `A` ($c=1$) sang phải và hàng đánh số từ `1` ($r=1$) xuống dưới. Mỗi nhân vật ở $(r, c)$ ứng với biến chính $C_i$ có chỉ số tất định $i = (r - 1)N + c \in \{1, \dots, N^2\}$ (`True` = `CRIMINAL`, `False` = `INNOCENT`). Mọi lời khai đã mở đều luôn đúng bất kể chủ thẻ là tội phạm hay vô tội.

### 3.1. Sáu mẫu manh mối cơ sở và hai mẫu mở rộng ([clues.py](../griductive/engine/clues.py))

| Nhóm | Kiểu JSON | Tham số chính | Ngữ nghĩa logic |
| --- | --- | --- | --- |
| Cơ sở | `FACT` | `person`, `status` | Trạng thái trực tiếp của một người: $C_i$ hoặc $\neg C_i$. |
| Cơ sở | `SAME` | `a`, `b` | Hai người cùng trạng thái: $C_a \leftrightarrow C_b$. |
| Cơ sở | `DIFFERENT` | `a`, `b` | Hai người khác trạng thái: $C_a \oplus C_b$. |
| Cơ sở | `EXACTLY` | `region`, `k` | Đúng $k$ tội phạm trong vùng $R$: $\sum_{i \in R} C_i = k$ ($0 \le k \le |R|$; `NO` tương ứng $k=0$). |
| Cơ sở | `AT_LEAST` | `region`, `k` | Ít nhất $k$ tội phạm trong vùng $R$: $\sum_{i \in R} C_i \ge k$. |
| Cơ sở | `AT_MOST` | `region`, `k` | Nhiều nhất $k$ tội phạm trong vùng $R$: $\sum_{i \in R} C_i \le k$. |
| **Mở rộng 1** | `COMPARISON` | `left`, `right`, `op` | So sánh số tội phạm giữa hai vùng $R_1, R_2$ với 6 toán tử `=`, `!=`, `<`, `<=`, `>`, `>=` (ô giao nhau vẫn đóng góp bình thường vào từng tổng). |
| **Mở rộng 2** | `CONDITIONAL` | `if`, `then` | Mệnh đề kéo theo $P \to Q \equiv \neg P \lor Q$, cho phép lồng đệ quy hai cây manh mối bất kỳ (giới hạn độ sâu kiểm tra tối đa 12 cấp). |

### 3.2. Bốn vùng cơ sở và bốn biểu thức vùng mở rộng ([regions.py](../griductive/engine/regions.py))

| Nhóm | Kiểu vùng | Tham số | Tập ô phân giải |
| --- | --- | --- | --- |
| Cơ sở | `ROW` | `row` ($1 \dots N$) | Tất cả các ô trên cùng hàng `row`. |
| Cơ sở | `COLUMN` | `column` (`A`…) | Tất cả các ô trên cùng cột `column`. |
| Cơ sở | `NEIGHBORS` | `cell` | Các ô chạm ngang, dọc hoặc chéo với `cell` (khoảng cách Chebyshev bằng 1, loại trừ chính `cell`; góc có 3, cạnh có 5, ô trong có 8 láng giềng). `cell` được đánh dấu là `anchor`. |
| Cơ sở | `EXPLICIT` | `cells` | Danh sách tường minh các mã ô phân biệt (có thể rỗng). |
| **Mở rộng** | `CORNERS` | *(không)* | Bốn ô góc của bàn cờ: `A1`, `<cột cuối>1`, `A<hàng cuối>`, `<cột cuối><hàng cuối>`. |
| **Mở rộng** | `UNION` | `left`, `right` | Hợp tập hợp hai vùng con: $R_1 \cup R_2$ (mỗi ô chỉ đếm một lần). |
| **Mở rộng** | `INTERSECTION` | `left`, `right` | Giao tập hợp hai vùng con: $R_1 \cap R_2$. |
| **Mở rộng** | `DIFFERENCE` | `left`, `right` | Hiệu tập hợp có thứ tự: $R_1 \setminus R_2$ (ví dụ lời khai B1 ở `case-3x3-01`: láng giềng của `A2` trừ hàng `2`). |

### Đánh giá ngữ nghĩa độc lập và ánh xạ tô sáng
- Mỗi lớp `Clue` bắt buộc cài đặt hai đường độc lập:
  1. `evaluate(spec, assignment, board, clues)`: tính trực tiếp giá trị đúng/sai trên một phép gán đầy đủ `{'A1': True, ...}` bằng phép toán Python thuần, **không gọi `Encoder` hay `solve`**.
  2. `expression(spec, encoder, clues)`: biên dịch ràng buộc sang biến/mệnh đề CNF trên bộ mã hóa dùng chung.
- Các kiểm thử vét cạn (`test_semantics_and_cnf_agree_exhaustively`, `test_reified_semantics_and_overlapping_comparisons`) đối chiếu hai đường này trên mọi tổ hợp chân trị.
- Hàm `clue_parts()` sinh cây `CluePart` mang khóa ngữ nghĩa (`result`, `left`, `right`, `if.person`, `then.region.anchor.B2`, ...) dùng chung cho bộ dựng câu tiếng Việt [wording_vi.py](../griductive/presentation/wording_vi.py) và bộ tô sáng viền màu trên thẻ. Cách thêm vùng/manh mối mới bằng `@register_region` và `@register_clue` xem tại [EXTENDING.md](EXTENDING.md).

---

## 4. Biểu diễn logic tự động và mã hóa CNF ([cnf.py](../griductive/engine/cnf.py))

Chương trình không chứa bất kỳ công thức CNF viết tay nào cho từng màn. `build_knowledge_base(state, registry)` khởi tạo một `Encoder(state.board)` duy nhất cho toàn bộ $KB_t$: biến chính chiếm dải $1 \dots N^2$, còn biến phụ Tseitin cấp phát liên tiếp từ $N^2 + 1$.

### 4.1. Cổng Tseitin dùng chung và rút gọn sớm (`Encoder.gate`)
Trước khi cấp biến phụ cho cổng `AND` hoặc `OR`:
- Rút gọn phần tử đơn vị (`True` với `AND`, `False` với `OR`), phần tử nuốt (`False` với `AND`, `True` với `OR`), loại literal trùng và phát hiện cặp đối ngẫu ($x$ và $\neg x$).
- Nếu sau rút gọn chỉ còn 0 hoặc 1 literal, trả trực tiếp hằng Boolean hoặc literal đó mà không tốn biến phụ.
- Tra bảng nhớ `self.gates[(kind, sorted_inputs)]` để tái sử dụng biến phụ nếu biểu thức con đã xuất hiện.
- Khi tạo biến phụ mới $z$ cho $z \leftrightarrow (a \land b)$ hoặc $w \leftrightarrow (a \lor b)$, bộ mã hóa sinh mệnh đề tương đương hai chiều (để cổng có thể nằm an toàn bên dưới phép phủ định hoặc vế `if` của `CONDITIONAL`):

$$
z \leftrightarrow (a \land b) \equiv (\neg z \lor a) \land (\neg z \lor b) \land (z \lor \neg a \lor \neg b),
$$

$$
w \leftrightarrow (a \lor b) \equiv (w \lor \neg a) \land (w \lor \neg b) \land (\neg w \lor a \lor b).
$$

### 4.2. Dẫn xuất manh mối nhị phân (`SAME` và `DIFFERENT`)
Với hai biến chính $C_A, C_B$:
- **Cùng trạng thái (`SAME`):**

$$
C_A \leftrightarrow C_B \equiv (C_A \to C_B) \land (C_B \to C_A) \equiv (\neg C_A \lor C_B) \land (C_A \lor \neg C_B).
$$

Trong `Same.expression`, chương trình tạo $u_1 \leftrightarrow (\neg C_A \lor C_B)$, $u_2 \leftrightarrow (C_A \lor \neg C_B)$ và đầu ra $e \leftrightarrow (u_1 \land u_2)$. Khi manh mối đứng độc lập ở mức đỉnh, `Encoder.add` ép mệnh đề đơn $(e)$; với `DIFFERENT`, đầu ra chỉ cần đảo dấu thành $(-e)$ trên cùng cấu trúc cổng.

### 4.3. Dẫn xuất manh mối đếm và bộ đếm ngưỡng unary đa thức (`Encoder.thresholds`)
Nếu mã hóa tổ hợp trực tiếp cho $\operatorname{EXACTLY}(k, R)$ trên vùng $n = |R|$ ô (chẳng hạn với $R = \{A, B, C\}, k = 2$ ta có $(A \lor B) \land (A \lor C) \land (B \lor C) \land (\neg A \lor \neg B \lor \neg C)$), số mệnh đề là $\binom{n}{k-1} + \binom{n}{k+1}$, lên tới $9\,657\,700$ mệnh đề khi $n = 25, k = 12$.

Để giữ kích thước CNF bậc đa thức $O(n^2)$ ngay cả trên bàn $5 \times 5$ và tái sử dụng cho phép so sánh vùng, `Encoder.thresholds(cells)` quy hoạch động bảng ngưỡng unary $T(i, k)$ — mệnh đề *“có ít nhất $k$ tội phạm trong $i$ ô đầu của vùng”*:
- Điều kiện biên: $T(i, 0) = \mathrm{True}$, và $T(i, k) = \mathrm{False}$ với mọi $k > i$.
- Công thức chuyển trạng thái với biến chính thứ $i$ là $x_i$:

$$
T(i, k) \leftrightarrow T(i - 1, k) \lor \bigl(x_i \land T(i - 1, k - 1)\bigr), \quad 1 \le k \le i.
$$

Đặt $T_R(k) = T(|R|, k)$ (được lưu cache trong `self.counts` theo bộ ô đã chuẩn hóa thứ tự):
- `AT_LEAST(k, R)`: đầu ra là $T_R(k)$.
- `AT_MOST(k, R)`: đầu ra là $\neg T_R(k + 1)$.
- `EXACTLY(k, R)`: đầu ra là cổng `AND` của $T_R(k)$ và $\neg T_R(k + 1)$.
- `COMPARISON(R_1, R_2, op)`: quan hệ $\sum_{R_1} \ge \sum_{R_2}$ tương đương việc mọi ngưỡng $k \ge 1$ đạt được ở $R_2$ đều phải đạt ở $R_1$:

$$
\operatorname{GE}(R_1, R_2) \equiv \bigwedge_{k=1}^{|R_2|} \bigl(\neg T_{R_2}(k) \lor T_{R_1}(k)\bigr).
$$

Từ $\operatorname{GE}(R_1, R_2)$ và $\operatorname{GE}(R_2, R_1)$, lớp `Comparison` suy ra đủ 6 toán tử: `>=`, `<=` (đảo đối số), `<` ($\neg\operatorname{GE}(R_1, R_2)$), `>` ($\neg\operatorname{GE}(R_2, R_1)$), `=` ($\operatorname{GE}(R_1, R_2) \land \operatorname{GE}(R_2, R_1)$) và `!=` (phủ định của `=`).

---

## 5. Bộ giải DPLL tự cài đặt ([sat.py](../griductive/engine/sat.py))

Hàm `solve(clauses, variable_count=None, assumptions=(), heuristic="ordered", timeout=10., cancelled=...)` thực thi đầy đủ thủ tục Davis–Putnam–Logemann–Loveland thuần Python:

1. **Tiền xử lý và giả định:** Khử literal trùng trong từng mệnh đề, nối các literal trong `assumptions` thành mệnh đề đơn `(literal,)`, kiểm tra tính hợp lệ của chỉ số biến $1 \dots m$, và loại bỏ các mệnh đề hằng đúng (chứa đồng thời $v$ và $-v$).
2. **Lan truyền mệnh đề đơn (*Unit Propagation*) & phát hiện xung đột:**
   - Trong vòng lặp `while True`, kiểm tra cờ hủy (`SolverCancelled`) và hạn thời gian (`SolverTimeout`).
   - Nếu xuất hiện mệnh đề rỗng `()`, nhánh hiện tại mâu thuẫn $\implies$ trả `None` (`UNSAT`).
   - Thu thập mọi mệnh đề đơn `(unit,)`. Nếu không còn mệnh đề đơn nào thì thoát vòng lặp lan truyền.
   - Với từng `unit`: nếu biến đã mang giá trị ngược dấu trong `assignment` (xung đột hai mệnh đề đơn $x$ và $-x$) thì trả `None`; nếu biến chưa gán thì ghi vào `assignment` và cộng `stats.propagations += 1`.
   - Rút gọn công thức bằng `simplify(current, assignment)`: xóa mệnh đề đã có ít nhất một literal đúng và loại bỏ các literal sai khỏi những mệnh đề còn lại.
3. **Kiểm tra thỏa mãn hoàn toàn:** Nếu danh sách mệnh đề còn lại rỗng, điền mặc định `False` cho mọi biến tự do chưa gán trong dải $1 \dots m$ để trả về `SATResult("SAT", model, stats)` với mô hình đầy đủ.
4. **Chọn biến phân nhánh tất định:** Đếm số lần xuất hiện (gộp cả hai dấu dương/âm) của từng biến trong công thức rút gọn hiện tại `current`:
   - Chiến lược **`ordered`**: chọn biến chưa gán có chỉ số nhỏ nhất (`min(frequencies)`).
   - Chiến lược **`frequency`**: chọn biến có tần suất xuất hiện lớn nhất, nếu hòa thì chọn chỉ số nhỏ nhất (`min(frequencies, key=lambda v: (-frequencies[v], v))`).
5. **Phân nhánh đệ quy và quay lui:** Cộng `stats.decisions += 1`, thử gán trực tiếp `True` trước rồi `False` sau trên bản sao `branch` của phép gán (không đi vòng qua mệnh đề đơn giả để `propagations` chỉ đếm đúng các phép gán bị ép buộc). Mỗi khi một nhánh con trả về `None`, cộng `stats.backtracks += 1`. Nếu cả hai nhánh đều thất bại, trả `UNSAT`.

---

## 6. Nhật ký suy luận (`trace`), kiểm tra nghiệm duy nhất và cách đọc số liệu

### 6.1. Cấu trúc một mục trong nhật ký suy luận (`GameEngine.trace`)
Mỗi phán quyết được `GameEngine.submit` chấp nhận sẽ ghi một từ điển JSON gồm các trường:
- `step`: Số thứ tự bước mở thẻ ($1, 2, \dots$).
- `cell`, `verdict`: Mã ô vừa chứng minh (ví dụ `"A3"`) và kết luận (`"CRIMINAL"` hoặc `"INNOCENT"`).
- `active_clues`: Danh sách ID các lời khai công khai đang có hiệu lực **ngay trước khi** lật thẻ ở bước này.
- `queries`: Danh sách các truy vấn DPLL mà `LogicAgent.verify` vừa thực hiện để kiểm chứng bước đó (mỗi phần tử ghi `assumptions`, `result`, `decisions`, `propagations`, `backtracks`, `runtime`). Truy vấn cuối cùng của một bước `ACCEPTED` luôn có `result == "UNSAT"` cho giả thiết phủ định.
- `new_clue`, `new_clue_content`: Định danh và cấu trúc JSON của lời khai mới vừa được lật mở tại `cell`.
- `primary_variables`, `auxiliary_variables`, `clauses`: Quy mô của $KB_t$ tại thời điểm chứng minh bước đó.

### 6.2. Kiểm tra nghiệm duy nhất ngoại tuyến (`check_uniqueness`)
Hàm `check_uniqueness(puzzle, registry, heuristic="ordered", timeout=10.)` trong [game.py](../griductive/engine/game.py) kiểm định chất lượng bộ câu đố bằng toàn bộ lời khai của màn:
1. Mã hóa tất cả $N^2$ lời khai vào công thức $F$ và gọi DPLL lần thứ nhất. Nếu `UNSAT`, trả `"INCONSISTENT"`.
2. Nếu tìm được mô hình $M$, tạo **mệnh đề chặn (*blocking clause*) chỉ trên tập biến chính** $P = \text{kb.primary.values()}$:

$$
B_M = \bigvee_{v \in P} \begin{cases} \neg v, & \text{nếu } M(v) = \mathrm{True}, \\ v, & \text{nếu } M(v) = \mathrm{False}. \end{cases}
$$

3. Giải $F \land B_M$: nếu `UNSAT` thì trả `"UNIQUE"` (duy nhất một nghiệm nhân vật); nếu `SAT` thì trả `"MULTIPLE"`. Việc chỉ đưa biến chính vào $B_M$ bảo đảm sự khác biệt ở các biến phụ Tseitin không bị đếm nhầm thành nghiệm thứ hai. Lưu ý: `UNIQUE` trên toàn bộ lời khai chỉ là điều kiện cần; khả năng giải từng bước không đoán mò từ tập mở đầu còn được kiểm chứng riêng qua vòng suy luận công khai trong `test_six_cases_unique_and_progressively_solvable`.

### 6.3. Cách đọc bảng số liệu trong `output/experiments/`
Khi đọc [results.json](../output/experiments/results.json) và `results.csv` do [experiments.py](../griductive/experiments.py) sinh ra, cần lưu ý 4 quy tắc đo lường sau:
1. **Quy mô KB cuối phiên (`primary_variables`, `auxiliary_variables`, `clauses`):** Đo trên `engine.public_state()` sau khi vòng lặp mở thẻ kết thúc. Khi cả `ordered` và `frequency` đều giải trọn vẹn màn chơi (`SOLVED`), hai cấu hình mở cùng tập thẻ cuối nên sinh ra cùng số biến và số mệnh đề cuối.
2. **Tổng số truy vấn (`sat_calls`) và các bộ đếm DPLL (`decisions`, `propagations`, `backtracks`):** Cộng gộp **cả** các truy vấn dò tìm bước đi của `LogicAgent.next_verdict` **lẫn** các truy vấn kiểm chứng độc lập bên trong `GameEngine.submit` (chạy cùng `heuristic` để đối sánh công bằng). Do mô hình `SAT` trả về ở hai chiến lược có thể khác nhau, bộ nhớ nhân chứng `can_be_true` / `can_be_false` có thể bỏ qua số truy vấn hơi khác nhau (ví dụ `case-4x4-01`: `84` so với `85` lần gọi SAT) dù số bước mở thẻ (`steps = 13`) như nhau.
3. **Tách biệt phép kiểm tra ngoại tuyến khỏi `runtime`:** `check_uniqueness` được gọi **sau khi** đồng hồ `runtime` đã dừng và không cộng vào `sat_calls`, `decisions`, `propagations`, `backtracks` của phiên chơi.
4. **Đánh đổi giữa hai chiến lược chọn biến:** Các biến phụ Tseitin cũng tham gia đếm tần suất trong `frequency`. Trên các màn có ràng buộc đếm giao thoa mạnh như `case-4x4-01` (quay lui giảm `444 → 8`, thời gian `1.015s → 0.504s`) và `case-5x5-02` (quay lui giảm `113 → 37`, thời gian `6.432s → 5.540s`), ưu tiên biến xuất hiện nhiều giúp kích hoạt lan truyền ngưỡng và cắt nhánh mâu thuẫn sớm. Ngược lại, ở `case-5x5-01`, vì cả hai chiến lược đều thử nhánh `True` trước, việc chọn biến có tần suất cao nhất có thể rẽ vào nhánh sai đầu tiên khiến số lần quay lui tăng nhẹ (`18 → 45`). Ngoài ra, nếu một màn dừng sớm hoặc quá hạn (mặc định `30s`/màn, `10s`/truy vấn), bộ thực nghiệm giữ nguyên trạng thái `UNKNOWN`, `INCONSISTENT` hoặc `TIMEOUT` trong bảng kết quả theo đúng mục 4.5 của đề bài.
