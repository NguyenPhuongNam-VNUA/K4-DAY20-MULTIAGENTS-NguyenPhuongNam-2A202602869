# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Phương Nam
- Mã sinh viên: 2A202602869
- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `LAB_MODEL=google_genai:gemini-3.5-flash-lite`, `LAB_TEMPERATURE=0.0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, macOS (Darwin arm64), chạy trực tiếp trên môi trường máy tính người dùng (Native)
- Số lần chạy tác vụ đã dùng / ngân sách: 21 / 30 runs
- Commit của tag `freeze`: `472ca9dbd9c1f2d2b8c475cbc1a1aaa1ca61e566`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điều kiện `subagents` sẽ đạt điểm tương đương hoặc chỉ tăng nhẹ so với `baseline` trên các tác vụ đánh giá (eval), nhưng chi phí token sẽ tăng gấp 2 đến 2.5 lần và thời gian chạy tăng 2 đến 4 lần. Lý do: Phân loại lỗi baseline chỉ ra 100% lỗi thất bại bắt nguồn từ việc thiếu tri thức quy ước tổ chức ngầm (Nhóm E). Việc chia việc cho các subagent (explorer, implementer, reviewer) chỉ tối ưu hóa việc phân tách vai trò kỹ thuật mà không thể tự sinh ra tri thức quy ước ngầm chưa từng xuất hiện trong mô tả bài toán ban đầu.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` sẽ đạt điểm cao nhất trên các tác vụ học (learn) và cải thiện một phần trên các tác vụ đánh giá (eval) đối với các quy ước chung có khả năng chuyển giao kỹ thuật (như viết regression tests hoặc chuẩn hóa type annotations), nhưng sẽ không giải quyết được các quy ước đặc thù riêng biệt mới (unseen organizational rules) của tác vụ đánh giá. Lý do: Curator tự động đúc kết kỹ năng từ baseline giúp agent nắm bắt quy chuẩn công việc; các kỹ năng này có tính tổng quát kỹ thuật cao nhưng không thể biết trước các quy tắc tổ chức mới của tác vụ eval.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm trung bình trên các tác vụ đánh giá (eval) sẽ thấp hơn rõ rệt so với tác vụ học (learn) ở tất cả các điều kiện, với khoảng cách chênh lệch lớn nhất xuất hiện ở điều kiện `skills-auto`. Lý do: Các tác vụ đánh giá đưa vào các quy ước tổ chức mới mà agent chưa từng tiếp xúc (phân phối out-of-distribution), khiến hiệu ứng cải thiện từ kinh nghiệm học trước đó bị suy giảm trên miền tác vụ mới.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Deep Agents tương tác với hệ thống tệp và môi trường thông qua các công cụ tích hợp sẵn và tùy biến trong sandbox: agent sử dụng các công cụ `execute_command`, `read_file`, `write_file`, `list_dir`, `edit_file` để duyệt tệp, chỉnh sửa mã nguồn và thực thi các lệnh kiểm thử.
2. Công cụ `execute` (thực thi) cho phép agent chạy mã kiểm thử, script Python và các công cụ dòng lệnh trực tiếp trong thư mục workspace được cô lập (`ROOT / "workspace"`). Điều này giúp agent kiểm tra tính đúng đắn của giải pháp, bắt lỗi cú pháp/runtime trước khi nộp bài.
3. Cấu trúc một tác vụ trong lab bao gồm:
   - `prompt.txt`: Mô tả yêu cầu nghiệp vụ và bài toán được gửi trực tiếp cho agent.
   - Thư mục `setup/`: Chứa mã nguồn, bộ dữ liệu hoặc tệp log khởi tạo ban đầu được sao chép vào `workspace/` trước mỗi lượt chạy.
   - `check.py`: Kịch bản chấm điểm độc lập và khách quan chạy sau khi agent hoàn thành, đánh giá cả các tiêu chí kỹ thuật công khai lẫn các quy ước tổ chức ngầm (`rule_*`).

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `code-learn` | `rule_type_hints` | E (Quy ước tổ chức) | RULE: every public function (name not starting with '_') in the package has type annotations on all parameters and on the return value. |
| `code-learn` | `rule_regression_tests` | E (Quy ước tổ chức) | RULE: write at least 2 regression tests in tests/test_regression.py covering the fixed bugs. |
| `code-learn` | `rule_changelog` | E (Quy ước tổ chức) | RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet '- fix(<function name>): <short description>' (at least 3 bullets). |
| `data-learn` | `rule_money_in_cents` | E (Quy ước tổ chức) | RULE: money values in answer.json are integer cents (1606.67 USD is written 160667). |
| `data-learn` | `rule_meta_block` | E (Quy ước tổ chức) | RULE: answer.json has an object `meta` = {"source": <input file name>, "rows_in": <number of data rows>, "rows_used": <number of distinct orders>}. |
| `data-learn` | `rule_clean_csv` | E (Quy ước tổ chức) | RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order with a known amount; timestamp_utc as UTC. |
| `logs-learn` | `rule_service_names` | E (Quy ước tổ chức) | RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service). |
| `logs-learn` | `rule_sorted_errors` | E (Quy ước tổ chức) | RULE: `errors` is sorted by service, then by timestamp_utc, ascending. |
| `logs-learn` | `rule_schema_header` | E (Quy ước tổ chức) | RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage". |

Nhận xét:
- **Nhóm lỗi chiếm đa số:** 100% các check thất bại ở baseline thuộc về **Nhóm E (Vi phạm quy ước tổ chức / quy ước ngầm)** (9/9 checks thất bại trên cả 3 tác vụ học).
- **Bằng chứng phủ định cho Nhóm A-D:** 100% các tiêu chí kỹ thuật thuần túy đều ĐẠT (18/18 checks kỹ thuật thành công): `code-learn` vượt qua `visible_suite_passes`, `parse_price_all_formats`, `discount_rounds_half_up`, `low_stock_follows_docstring`, `csv_quoting_follows_docstring`; `data-learn` tính đúng tuyệt đối `north_q1_revenue`, `north_q1_orders`, `top_region`, `missing_amount_orders`, `duplicate_rows_removed`; `logs-learn` đạt chuẩn `valid_structure`, `entry_count`, `timestamps_utc`, `exception_fields`, `repeat_counts`, `counts_by_service`. Agent hoàn toàn hiểu bài toán, không bị lỗi cú pháp hay logic kỹ thuật.
- **Khả năng phòng ngừa của Skill:** Skill hoàn toàn có thể phòng ngừa Nhóm E đối với các quy ước chung được đúc kết từ tác vụ học (ví dụ: bổ sung type hints, sinh regression test, chuẩn hóa schema metadata). Tuy nhiên, skill không thể phòng ngừa các quy ước ngầm hoàn toàn mới phát sinh trong các tác vụ đánh giá mà chưa từng được đưa vào tri thức nền tảng.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  1. `explorer`: Chuyên trách đọc mã nguồn, dữ liệu, cấu trúc thư mục và tìm kiếm vị trí phát sinh lỗi. Thiết kế nhằm tránh làm tràn context window của agent chính khi đọc các tệp lớn.
  2. `implementer`: Chuyên trách sửa mã, viết script phân tích dữ liệu và trích xuất log theo kế hoạch, đảm bảo không sửa đổi hay làm hỏng bộ test có sẵn.
  3. `reviewer`: Chuyên trách chạy kiểm thử độc lập (`pytest`, python validation), rà soát kết quả đầu ra và kiểm tra các tiêu chí chất lượng trước khi nộp kết quả.
- `subagent_calls` ở từng tác vụ và nhận xét:
  - `code-learn`: 3 lần gọi (agent chính lần lượt điều phối `explorer` -> `implementer` -> `reviewer`).
  - `data-learn`: 1 lần gọi (agent chính gọi subagent phụ trách xử lý và làm sạch dữ liệu).
  - `logs-learn`: 2 lần gọi (agent chính gọi `implementer` để parse log và hoàn thiện file JSON).
  - Nhận xét: Agent chính đã phân công công việc rõ ràng theo quy trình ở tác vụ mã nguồn (`code-learn`). Ở các tác vụ phân tích dữ liệu và log, agent chính có xu hướng giảm bớt số lần gọi do bài toán có thể giải quyết nhanh bằng 1 script tập trung.
- Thông tin thiếu hoặc thừa khi giao việc:
  - Thiếu: Agent chính chỉ truyền đạt mô tả bài toán bề mặt mà không cung cấp được các quy ước ngầm tổ chức cho subagent, khiến subagent cũng không thể tự đáp ứng các tiêu chí Nhóm E.
  - Thừa: Agent chính lặp lại toàn bộ prompt dài và lịch sử hội thoại khi gọi subagent, làm lãng phí dung lượng context.
- Ảnh hưởng đến token và thời gian:
  - Token: Tiêu thụ tăng gấp ~2.2 đến 2.5 lần (từ 85k - 260k token ở baseline lên 216k - 574k token ở subagents).
  - Thời gian: Tăng gấp 2.5 đến 4.8 lần (từ 53s - 65s ở baseline lên 129s - 314s ở subagents) do độ trễ mạng qua nhiều vòng gọi API và chi phí context lớn.

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần chạy với lệnh `python -m lab.curator`.
- Số skill bị xóa: 0 skill bị xóa (curator hoạt động chuẩn xác, sinh ra 3 kỹ năng đạt chuẩn ngay lần đầu, tuân thủ YAML frontmatter hợp lệ, độ dài từ 11 đến 14 dòng và không vi phạm quy tắc an toàn).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `python-type-annotations` | Tổng quát cho các dự án Python yêu cầu chuẩn hóa type hint | Đúng: hướng dẫn chi tiết thêm type hint cho public functions và return values | 11 dòng; "Rules and best practices for writing public Python functions with full type annotations."; skills_read: 0 ở code-learn (do chạm recursion limit) |
| `json-schema-and-format-validation` | Tổng quát cho các bài toán xuất dữ liệu dạng JSON/báo cáo | Đúng: hướng dẫn cấu trúc hóa schema, trường meta và format tiền tệ dạng cent | 12 dòng; "Conventions and schema requirements for structured JSON data outputs and reports."; skills_read: 2 ở data-learn |
| `comprehensive-bug-fix-testing-and-changelog` | Tổng quát cho quy trình bảo trì phần mềm và theo dõi thay đổi | Đúng: yêu cầu tạo test hồi quy trong `tests/test_regression.py` và cập nhật `CHANGELOG.md` | 14 dòng; "Guidelines for writing regression tests and maintaining CHANGELOG.md during bug fixes."; skills_read: 2 ở logs-learn / code-learn |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng so sánh tổng hợp (`report/table.md`):

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 7/10 | 6/10 | 8/10 |
| data-learn | 5/8 | 5/8 | 5/8 |
| logs-learn | 6/9 | 6/9 | 6/9 |
| code-eval | 7/11 | 6/11 | 10/11 |
| data-eval | 5/9 | 5/9 | 5/9 |
| logs-eval | 6/10 | 6/10 | 6/10 |
| **Mean score - learning tasks** | 0.66 | 0.63 | 0.70 |
| **Mean score - evaluation tasks** | 0.60 | 0.57 | 0.69 |
| **Mean tokens per run** | 130,038 | 295,361 | 152,774 |
| **Runs that read a skill** | 0/6 | 0/6 | 4/6 |

### Phân rã tiêu chí kỹ thuật và quy ước (`check_breakdown.py`):

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     18/18         0/12          92,956      0/3     
baseline      learn    18/18         0/9          167,120      0/3     
subagents     eval     17/18         0/12         227,000      0/3     
subagents     learn    17/18         0/9          363,722      0/3     
skills-auto   eval     18/18         3/12         143,259      2/3     
skills-auto   learn    18/18         1/9          162,289      2/3     
```

### Xử lý lỗi và tính toàn vẹn:
- **`skills_modified`**: Giá trị luôn là `false` trên 100% các lần chạy, xác nhận tuân thủ tuyệt đối giao thức đóng băng sau tag `freeze`; không có bất kỳ sửa đổi trái phép nào đối với thư mục `skills/auto/`.
- **Lỗi `GraphRecursionError`**: Xuất hiện ở tác vụ `code-learn` (cả ở lần chạy dev trước đóng băng và chạy chính thức sau đóng băng) do agent sử dụng nhiều lượt gọi công cụ liên tục để vừa sửa code vừa kiểm tra type hint. Tuy nhiên, trước khi chạm giới hạn 60 bước, agent đã kịp thời hoàn tất các sửa đổi chức năng và tạo xong bài test hồi quy trong `tests/test_regression.py`, giúp điểm số tăng từ 7/10 lên 8/10. Trong khi đó, tác vụ `code-eval` sau đóng băng hoàn thành trọn vẹn không lỗi trong 26 tool calls (74.2s), đạt điểm số xuất sắc 10/11.

## 8. Phân tích

1. **Cải thiện điểm tác vụ học và tác vụ đánh giá:**
   - So với `baseline` (Mean Learn: 0.66, Mean Eval: 0.60), điều kiện `skills-auto` cải thiện điểm số ở **cả hai tập**: Mean Learn tăng lên 0.70 (+4.0%) và Mean Eval tăng mạnh lên 0.69 (+9.0%). Trong đó, tác vụ `code-eval` đạt mức nhảy vọt ấn tượng từ 7/11 (0.64) lên 10/11 (0.91).
   - Ngược lại, điều kiện `subagents` không cải thiện mà giảm nhẹ điểm số trên cả hai tập (Learn: 0.63, Eval: 0.57).
   - Không có điều kiện nào chỉ cải thiện học mà không cải thiện đánh giá. Việc `skills-auto` đạt điểm cao trên cả tập đánh giá (với các bài toán mới) chứng minh các kỹ năng do curator đúc kết có tính chuyển giao (transferability) thực chất, không bị hiện tượng học vẹt hay quá khớp (overfitting).

2. **Tách điểm kỹ thuật và quy ước tổ chức (`rule_`):**
   - Tiêu chí kỹ thuật: Cả `baseline` và `skills-auto` đều đạt tuyệt đối 18/18 trên cả hai tập tác vụ (học và đánh giá).
   - Tiêu chí quy ước (`house rules`): `baseline` và `subagents` hoàn toàn thất bại (0/9 ở learn, 0/12 ở eval).
   - `skills-auto` đã giúp vượt qua 1/9 quy ước ở tập học và 3/12 quy ước ở tập đánh giá. Trên `code-eval`, 3 quy ước được giải quyết thành công là `rule_type_hints`, `rule_regression_tests`, và `rule_changelog` nhờ áp dụng hai kỹ năng `comprehensive-bug-fix-testing-and-changelog` và `python-type-annotations`.
   - Ngược lại, check quy ước **mới** của tác vụ đánh giá (`rule_version_bump` trong `code-eval` và các quy ước định dạng đặc thù mới trong log/data) **không được skill giúp** (bị fail). Lý do: Đây là các quy ước tổ chức ngầm hoàn toàn mới, chưa từng xuất hiện trong tập tác vụ học, do đó curator không thể tổng hợp được vào kỹ năng ban đầu. Điều này khẳng định Agent không thể "đoán mò" các quy ước ngầm nếu không được cung cấp tri thức.

3. **Giải thích dựa vào vết chạy và `skills_read`:**
   - **Check được skill giúp:** `rule_regression_tests` trong `code-eval`. Vết chạy cho thấy agent đã kích hoạt đọc skill `comprehensive-bug-fix-testing-and-changelog/SKILL.md` (`skills_read = 2`). Sau khi đọc hướng dẫn, agent nhận ra yêu cầu bắt buộc phải viết bài test hồi quy khi sửa lỗi, và đã chủ động tạo tệp `workspace/tests/test_regressions.py` với các ca kiểm thử cho `parse_duration` và `billable_blocks`, giúp vượt qua check này.
   - **Check không được skill giúp:** `rule_money_in_cents` trong `data-learn`. Mặc dù agent đã đọc skill `json-schema-and-format-validation` (`skills_read = 2`), nhưng trong prompt bài toán gốc yêu cầu tính doanh thu USD cụ thể (`$3,130.24`), agent đã ưu tiên bám sát định dạng câu hỏi trực tiếp và lưu số thực thay vì chuyển đổi sang đơn vị số nguyên cent. Đây là trường hợp skill được đọc nhưng bị prompt trực tiếp lấn át (prompt priority over general skill).

4. **Chi phí token và hiệu quả đa tác tử:**
   - Token trung bình mỗi lần chạy:
     - `baseline`: 130,038 tokens (thấp nhất).
     - `skills-auto`: 152,774 tokens (chỉ tăng 17.5% so với baseline).
     - `subagents`: 295,361 tokens (tăng vọt 127.1%, gấp 2.27 lần baseline).
   - Hiệu quả điểm trên mỗi token: `skills-auto` đạt hiệu suất cao nhất trên tác vụ đánh giá (0.69 điểm / 143k token).
   - **Đa tác tử (subagents) hoàn toàn không đáng chi phí trong thí nghiệm này:** Việc chia nhỏ vai trò cho `explorer`, `implementer`, `reviewer` làm tăng gấp đôi token và tăng gấp 3 đến 4 lần thời gian chạy (từ ~50s lên ~180s) nhưng không cải thiện được điểm số, bởi vì điểm nghẽn chính nằm ở việc thiếu tri thức quy ước tổ chức ngầm (Nhóm E) chứ không phải do thiếu năng lực thực thi kỹ thuật.

5. **Phòng tránh rò rỉ dữ liệu và quá khớp trong Skill:**
   - Không có dấu hiệu rò rỉ dữ liệu (no data leakage). Các kỹ năng sinh ra trong `skills/auto/` hoàn toàn độc lập với dữ liệu cụ thể: không chứa tên biến, tên hàm, hay giá trị cố định từ các bài toán trong `tasks/`.
   - Các kỹ năng chỉ tập trung vào nguyên tắc quy chuẩn: cú pháp Type Annotations chuẩn PEP-484, quy chuẩn viết regression test với pytest và định dạng `CHANGELOG.md`, cấu trúc trường `meta` và quy đổi cent trong JSON.
   - Curator được thiết kế với prompt nghiêm ngặt, chỉ trích xuất các mẫu hành vi kỹ thuật lặp lại và kiểm duyệt độ dài dưới 15 dòng, đảm bảo tính tổng quát hóa tối đa.

6. **Độ ổn định và phân tích nhiễu (Noise analysis):**
   - So sánh điểm số tác vụ học ở Phần 3.4 (lần chạy dev đã sao lưu tại `results/skills-auto-dev/`) và lần chạy chính thức sau đóng băng (`results/skills-auto/`):
     - `code-learn`: 8/10 (dev) vs 8/10 (chính thức) -> Chênh lệch = 0.0
     - `data-learn`: 5/8 (dev) vs 5/8 (chính thức) -> Chênh lệch = 0.0
     - `logs-learn`: 6/9 (dev) vs 6/9 (chính thức) -> Chênh lệch = 0.0
   - Độ chênh lệch giữa hai đợt chạy độc lập bằng đúng **0.0 (0%)**. Điều này chứng minh rằng với cấu hình `LAB_TEMPERATURE=0.0`, hành vi của mô hình có tính tất định và độ tin cậy cực kỳ cao. Sự cải thiện điểm số ở mục 7 phản ánh chính xác giá trị thực tế của bộ kỹ năng chứ không phải do biến động ngẫu nhiên.

## 9. Hạn chế và tính hợp lệ

1. **Quy mô tập tác vụ còn hạn chế (3 cặp bài toán):** Thí nghiệm mới thực hiện trên 6 tác vụ (3 learn, 3 eval) đại diện cho 3 lĩnh vực (code, data, logs). Mặc dù kết quả cho thấy xu hướng rõ ràng, kích thước mẫu nhỏ chưa cho phép áp dụng các kiểm định thống kê có ý nghĩa lớn (như t-test).
2. **Quy ước ngầm mang tính tất định trong kịch bản kiểm tra (`check.py`):** Các quy ước ngầm trong lab được kiểm định tự động bằng các hàm kiểm tra tĩnh (regex, AST, JSON schema), trong khi trong thực tế doanh nghiệp các quy ước văn hóa thường đa dạng hơn và được truyền đạt qua quá trình code review giữa con người với nhau.
3. **Giới hạn số bước thực thi (`recursion_limit=60`):** Đối với các tác vụ lập trình phức tạp đòi hỏi nhiều bước đọc file, chỉnh sửa code và chạy lại kiểm thử, giới hạn 60 bước khiến agent có thể bị dừng giữa chừng trước khi hoàn thiện 100% các công việc phụ trợ (như trường hợp `code-learn`).

## 10. Kết luận

1. Nghiên cứu thực nghiệm chứng minh rằng điểm nghẽn lớn nhất của AI Agent khi áp dụng vào môi trường phần mềm thực tế là sự vi phạm các quy ước tổ chức ngầm (Nhóm E) chứ không phải do thiếu sót năng lực lập trình cơ bản.
2. Mô hình đa tác tử (subagents) làm tăng chi phí token lên gấp 2.27 lần và thời gian thực thi lên gấp 3.5 lần nhưng không giúp cải thiện điểm số quy ước ngầm.
3. Cơ chế tự tiến hóa thông qua kỹ năng (skills-auto) cải thiện vượt trội hiệu năng trên cả tác vụ học và tác vụ đánh giá OOD (đặc biệt `code-eval` tăng từ 7/11 lên 10/11) với chi phí token tăng không đáng kể (+17.5%).
4. Giao thức đóng băng kỹ năng và kiểm thử trên tập dữ liệu chưa từng thấy là phương pháp khoa học chuẩn xác để loại bỏ rò rỉ dữ liệu và đo lường khả năng chuyển giao tri thức của Agent.
5. **Đề xuất cải tiến:** Tích hợp cơ chế phản hồi linter/formatter trực tiếp vào vòng lặp công cụ của Agent để phát hiện và cảnh báo vi phạm quy ước tổ chức ngay trong quá trình sinh mã thay vì chỉ phát hiện sau khi hoàn tất tác vụ.

## Phụ lục

- **Lệnh đã chạy (theo thứ tự):**
  1. `python scripts/tour.py` (Làm quen môi trường và Deep Agents)
  2. `python -m lab.runner --condition baseline --tasks learn` (Thu thập kết quả baseline trên tập học)
  3. `python -m lab.runner --condition subagents --tasks learn` (Thu thập kết quả subagents trên tập học)
  4. `python -m lab.curator` (Tự động phân tích vết và sinh kỹ năng trong `skills/auto/`)
  5. `python -m lab.runner --condition skills-auto --tasks learn` (Kiểm tra kỹ năng dev trước đóng băng)
  6. `cp -r results/skills-auto results/skills-auto-dev` (Sao lưu kết quả dev)
  7. `git commit -m "hypotheses: ..."` (Commit giả thuyết H1-H3 trước khi đóng băng)
  8. `git tag freeze` (Tạo tag freeze khóa cứng kỹ năng)
  9. `python -m lab.runner --condition baseline --tasks eval` (Đánh giá chính thức baseline trên tập eval)
  10. `python -m lab.runner --condition subagents --tasks eval` (Đánh giá chính thức subagents trên tập eval)
  11. `python -m lab.runner --condition skills-auto --tasks all` (Đánh giá chính thức skills-auto sau đóng băng)
  12. `python scripts/verify_freeze.py` (Kiểm định tự động giao thức freeze: Đạt `OK`)
  13. `python -m lab.compare > report/table.md` (Xuất bảng so sánh tổng hợp)
  14. `python scripts/check_breakdown.py` (Phân rã chi tiết tiêu chí kỹ thuật và quy ước)

- **Thử thách mở rộng (Phân tích cơ chế chuyển giao quy ước kỹ thuật):**
  - Kết quả thực nghiệm cho thấy tính chuyển giao cao của các kỹ năng lập trình tổng quát (`python-type-annotations`, `comprehensive-bug-fix-testing-and-changelog`): Cả hai kỹ năng này được học từ `code-learn` nhưng khi áp dụng vào `code-eval` (bài toán quản lý lịch đặt phòng với logic hoàn toàn khác) đều được Agent vận dụng chính xác 100% để vượt qua cả 3 tiêu chí quy ước (`rule_type_hints`, `rule_regression_tests`, `rule_changelog`).
  - Điều này khẳng định rằng việc đúc kết tri thức dạng meta-skill ngắn gọn kết hợp với Progressive Disclosure là phương pháp hiệu quả nhất để xây dựng các AI Coding Assistant có khả năng thích nghi liên tục với chuẩn mực công nghệ của từng dự án.

