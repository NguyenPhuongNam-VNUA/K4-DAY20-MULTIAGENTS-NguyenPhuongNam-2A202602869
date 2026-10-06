# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin sinh viên và cấu hình

- Họ tên: Nguyễn Phương Nam
- Mã sinh viên: 2A202602869
- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: `LAB_MODEL=google_genai:gemini-3.5-flash-lite`, `LAB_TEMPERATURE=0.0`, `recursion_limit=60`
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, macOS (Darwin arm64), chạy trực tiếp trên môi trường máy tính người dùng (Native)
- Số lần chạy tác vụ đã dùng / ngân sách: 15 / 30 runs
- Commit của tag `freeze`: Sẽ được cập nhật sau khi tạo tag `freeze`

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

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Bạn đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
