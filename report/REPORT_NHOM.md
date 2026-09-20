# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhomtoi  
**Thành viên:** Nguyễn Đức Đông, Lê Thị Duyên, Nguyễn Thị Lê Na, Bùi Quốc Việt  
**Ngày:** 20/09/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, bảo hành và quy định người bán/người mua trên sàn Thương mại điện tử Lazada.

**Tại sao nhóm chọn chủ đề này?**
> Lazada là một trong những nền tảng thương mại điện tử lớn nhất tại Việt Nam với hệ thống chính sách quy định phân hóa rõ rệt giữa Người Mua (`buyer`) và Người Bán (`seller`). Lựa chọn chủ đề này giúp nhóm đánh giá thực tế khả năng của hệ thống RAG trong việc truy xuất các điều khoản pháp lý phức tạp và chứng minh tính hiệu quả của lọc metadata (`metadata_filter`).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `lazada-buyer-return.md` | https://www.lazada.vn/helpcenter/chinh-sach-tra-hang-hoan-tien-lazada.html | 20/09/2026 / v3.0 | 1,020 | `doc_id`, `audience: buyer`, `category: return_policy` |
| 2 | `lazada-seller-return-process.md` | https://university.lazada.vn/course/view.htm?id=1204 | 20/09/2026 / v2.1 | 980 | `doc_id`, `audience: seller`, `category: seller_policy` |
| 3 | `lazada-electronic-warranty.md` | https://www.lazada.vn/helpcenter/huong-dan-bao-hanh-san-pham.html | 20/09/2026 / v1.5 | 890 | `doc_id`, `audience: both`, `category: warranty` |
| 4 | `lazada-buyer-protection-claim.md` | https://www.lazada.vn/helpcenter/cam-ket-hang-chinh-hang-lazmall.html | 20/09/2026 / v2.0 | 950 | `doc_id`, `audience: buyer`, `category: buyer_protection` |
| 5 | `lazada-seller-fee-and-claim.md` | https://university.lazada.vn/course/view.htm?id=3055 | 20/09/2026 / v4.0 | 910 | `doc_id`, `audience: seller`, `category: seller_policy` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `lazada-buyer-return` | Định danh duy nhất tài liệu nguồn, bảo đảm tính truy vết nguồn gốc (Source Traceability). |
| `audience` | `str` | `buyer` / `seller` / `both` | Phân loại đối tượng áp dụng quy định để thực hiện pre-filtering chính xác. |
| `category` | `str` | `return_policy` / `warranty` | Phân loại danh mục chính sách để giới hạn phạm vi tìm kiếm vector. |
| `document_version` | `str` | `3.0` | Đảm bảo hệ thống sử dụng đúng phiên bản hiệu lực của chính sách. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên các tài liệu chính sách Lazada:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `lazada-buyer-return.md` | FixedSizeChunker (`fixed_size`) | 4 | 255 | Kém (dễ cắt đứt ngang ranh giới điều khoản). |
| `lazada-buyer-return.md` | SentenceChunker (`by_sentences`) | 3 | 340 | Trung bình (độ dài chunk không ổn định). |
| `lazada-buyer-return.md` | RecursiveChunker (`recursive`) | 3 | 310 | **Rất tốt** (giữ trọn khối ngữ nghĩa đoạn văn). |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Đức Đông (MSSV: 2A202602367)**
- **Loại chiến lược:** RecursiveChunker (`recursive`, `chunk_size=300`, `separators=["\n\n", "\n", ". ", " ", ""]`)
- **Mô tả & lý do chọn cho chủ đề này:** Cắt đệ quy theo thứ tự ưu tiên các dấu phân tách ngữ nghĩa. Ưu tiên cắt theo đoạn văn (`\n\n`) và dòng (`\n`) giúp giữ trọn vẹn từng Điều khoản chính sách Lazada mà không bị đứt gãy ý.

**Thành viên 2 — Lê Thị Duyên (MSSV: 02411)**
- **Loại chiến lược:** FixedSizeChunker (`fixed_size`, `chunk_size=300`, `overlap=30`)
- **Mô tả & lý do chọn cho chủ đề này:** Cắt cố định ký tự kèm độ chồng chéo. Chọn cách này làm mốc cơ sở (baseline) để so sánh nhược điểm cắt ngang câu/điều khoản đối với văn bản pháp lý.

**Thành viên 3 — Nguyễn Thị Lê Na (MSSV: 2A202602501)**
- **Loại chiến lược:** SentenceChunker (`by_sentences`, `max_sentences_per_chunk=2`)
- **Mô tả & lý do chọn cho chủ đề này:** Tách văn bản sau dấu kết thúc câu dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` và gom 2 câu mỗi chunk. Giúp nguyên vẹn từng câu nhưng độ dài chunk bị biến động do câu dài ngắn khác nhau.

**Thành viên 4 — Bùi Quốc Việt (MSSV: 2A202602884)**
- **Loại chiến lược:** HeadingChunker (`chunk_size=500`, cắt theo heading `## Điều...`) kết hợp Embedder Đa ngữ Cục bộ (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) và Groq LLM (`openai/gpt-oss-20b`).
- **Mô tả & lý do chọn cho chủ đề này:** Tách chính xác theo từng mục/điều khoản `## Điều 1`, `## Điều 2`. Mục quá dài được chia tiếp và lặp lại heading tiêu đề cha trên các chunk con để duy trì ngữ cảnh độc lập cho từng chunk.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lê Thị Duyên | FixedSizeChunker | 6.0 | Đơn giản, độ dài chunk rất đồng đều. | Rất dễ cắt đứt đôi điều khoản hay số ngày ở ranh giới. |
| Nguyễn Thị Lê Na | SentenceChunker | 7.5 | Đảm bảo nguyên vẹn cấu trúc từng câu. | Kích thước chunk không ổn định do độ dài câu chênh lệch. |
| **Nguyễn Đức Đông** | **RecursiveChunker** | **9.5 (Thắng)** | **Giữ trọn vẹn khối ngữ nghĩa từng Điều khoản Lazada.** | Cần cấu hình separators hợp lý. |
| Bùi Quốc Việt | HeadingChunker + Local Embedder | 9.0 | Bốc trọn vẹn 100% từng Điều khoản pháp lý kèm heading cha. | Tốn thêm ký tự do lặp lại heading tiêu đề. |


**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **`RecursiveChunker`** (và `HeadingChunker`) là tốt nhất cho văn bản chính sách Lazada. Do các văn bản quy định luôn tổ chức theo từng Điều/Mục (`## Điều 1...`), việc cắt đệ quy theo ranh giới đoạn văn (`\n\n`) giúp trọn vẹn một điều khoản nằm trong 1 chunk, tránh làm rách rưới thông tin về mốc thời hạn (30 ngày, 3 ngày) hay điều kiện bồi thường (200%).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn trả hàng của sản phẩm LazMall là bao lâu? | Người mua trên LazMall được đổi trả trong vòng 30 ngày kể từ ngày giao hàng thành công. | `lazada-buyer-return#0` |
| 2 | Thời gian và quy trình xử lý hoàn tiền cho người mua như thế nào? | Hoàn tiền vào Ví LazadaPay trong 03 - 05 ngày làm việc, thẻ tín dụng từ 07 - 14 ngày. | `lazada-buyer-return#1` |
| 3 | Nhà bán hàng có bao nhiêu ngày để mở khiếu nại khi nhận hàng hoàn bị hư hỏng? | Nhà bán hàng có 03 ngày làm việc kể từ khi nhận lại hàng để mở khiếu nại trên PSC. | `lazada-seller-return-process#1` |
| 4 | Sản phẩm điện tử mua trên Lazada có các hình thức bảo hành nào? | Bảo hành qua SĐT/IMEI, Phiếu bảo hành kèm theo hoặc Bảo hành điện tử. | `lazada-electronic-warranty#0` |
| 5 | Chính sách đền bù của Lazada khi sản phẩm LazMall bị phát hiện là hàng giả? | Lazada cam kết đền tiền gấp 2 lần (200% giá trị sản phẩm) nếu là hàng giả. | `lazada-buyer-protection-claim#0` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn trả hàng LazMall | RecursiveChunker / HeadingChunker | Có (Top 1) | Đạt 2/2 điểm |
| 2 | Quy trình hoàn tiền cho người mua | RecursiveChunker + Metadata Filter | Có (Top 1) | Cần filter `audience: buyer` (2/2 điểm) |
| 3 | Thời hạn khiếu nại của nhà bán hàng | RecursiveChunker + Metadata Filter | Có (Top 1) | Cần filter `audience: seller` (2/2 điểm) |
| 4 | Hình thức bảo hành điện tử | RecursiveChunker / SentenceChunker | Có (Top 1) | Đạt 2/2 điểm |
| 5 | Chính sách đền bù hàng giả | RecursiveChunker / HeadingChunker | Có (Top 1) | Đạt 2/2 điểm |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất giúp ích**, đặc biệt tại **Câu 2 và Câu 3**. Do quy trình hoàn tiền cho Người Mua và quy trình xử lý hàng hoàn của Người Bán chứa nhiều từ vựng giống nhau (`hoàn tiền`, `trả hàng`, `thời hạn`), việc áp dụng `metadata_filter={"audience": "buyer"}` giúp hệ thống loại bỏ hoàn toàn các tài liệu dành cho Người Bán, ngăn ngừa việc AI truy xuất nhầm đối tượng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Ranh giới chia nhỏ (`Recursive` vs `FixedSize`) trực tiếp quyết định việc giữ nguyên vẹn ngữ cảnh của điều khoản pháp lý.
> 2. Pre-filtering theo metadata (`audience: buyer/seller`) giúp nâng cao vượt trội độ chính xác truy xuất (Precision) khi corpus chứa dữ liệu đa đối tượng.

**Bài học rút ra khi so sánh trong nhóm:**
> So sánh giữa 4 chiến lược của các thành viên cho thấy: `FixedSizeChunker` của Duyên dễ gây vỡ câu/điều khoản ở ranh giới; `SentenceChunker` của Na giữ được câu nhưng kích thước chunk thiếu ổn định; trong khi `RecursiveChunker` của Đồng và `HeadingChunker` của Việt là hai chiến lược tối ưu nhất cho bài toán RAG văn bản điều khoản TMĐT.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm các thuộc tính metadata chi tiết như `sub_category` (điện tử, thời trang) và áp dụng kỹ thuật Context Injection (gắn tiêu đề Điều khoản cha vào từng chunk con) để khi truy xuất độc lập, chunk vẫn mang đầy đủ ngữ cảnh của toàn bộ điều khoản.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
