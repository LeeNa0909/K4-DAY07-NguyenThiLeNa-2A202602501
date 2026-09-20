# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Lê Na
**Nhóm:** Nhomtoi
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Độ tương tự cosine cao nghĩa là góc giữa hai vector nhỏ, nên chúng có hướng gần nhau. Nếu hai vector là embedding của văn bản từ một mô hình ngữ nghĩa, điểm cao thường cho thấy nội dung gần nhau theo mô hình đó.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua có thể yêu cầu đổi trả nếu sản phẩm còn nguyên tem/nhãn và chưa qua sử dụng.
- Câu B: Sản phẩm chưa sử dụng và còn nguyên tem/nhãn là điều kiện để người mua yêu cầu đổi trả.
- Tại sao tương đồng: Hai câu diễn đạt cùng một điều kiện đổi trả, chỉ khác cách sắp xếp từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người mua có thể yêu cầu đổi trả nếu sản phẩm còn nguyên tem/nhãn và chưa qua sử dụng.
- Câu B: Người bán có thể bị xử phạt nếu từ chối yêu cầu bảo hành hợp lệ hoặc phản hồi trễ hạn.
- Tại sao khác: Câu A nói về điều kiện đổi trả của người mua; câu B nói về trách nhiệm bảo hành của người bán.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* > Cosine similarity đo độ gần nhau về hướng của hai vector, nên không bị độ lớn vector chi phối như khoảng cách Euclid. Với text embeddings, hướng vector thường được dùng để so sánh ý nghĩa; nếu tất cả vector đã được chuẩn hóa về độ dài 1, hai cách đo cho cùng thứ tự xếp hạng.


### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> **Trình bày phép tính:** Bước dịch chuyển là `500 - 50 = 450` ký tự. Số chunk = `1 + ceil((10.000 - 500) / 450) = 23`.

> *Đáp án:* 23 chuncks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* > Khi overlap tăng lên 100, bước dịch chuyển còn `500 - 100 = 400` ký tự, nên số chunk là `1 + ceil((10.000 - 500) / 400) = 25`, tăng 2 chunk. Chồng chéo nhiều hơn giúp giữ thông tin ở ranh giới giữa các chunk, nhưng tăng nội dung lặp và chi phí xử lý.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết thúc câu khi tiếp theo là khoảng trắng hoặc xuống dòng. Sau khi bỏ phần rỗng và khoảng trắng thừa, tôi gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk; giá trị tối đa nhỏ hơn 1 được nâng lên 1, còn văn bản rỗng trả về danh sách rỗng.


**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

Tôi chia đệ quy theo thứ tự ưu tiên: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), rồi ký tự; phần nào vẫn quá `chunk_size` được xử lý tiếp bằng dấu tách kế tiếp. Trường hợp cơ sở là đoạn đã đủ ngắn; nếu hết dấu tách thì cắt trực tiếp theo độ dài ký tự. Tôi giữ lại dấu tách trong các phần để không làm mất nội dung gốc.


### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

`add_documents` tạo embedding cho mỗi tài liệu và lưu cùng `id`, nội dung, metadata trong danh sách bản ghi ở bộ nhớ; nếu có ChromaDB, bản ghi cũng được thêm vào collection. `search` tạo embedding cho câu hỏi, tính cosine similarity với từng bản ghi trong bộ nhớ, rồi trả tối đa `top_k` kết quả theo điểm giảm dần.


**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

`search_with_filter` lọc các bản ghi theo metadata trước khi tính điểm và xếp hạng. `delete_document` tìm mọi bản ghi có `metadata["doc_id"]` khớp mã cần xóa, xóa chúng khỏi bộ nhớ và ChromaDB nếu đang dùng, rồi trả về `True` khi có bản ghi được xóa.


### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

`answer` truy xuất tối đa `top_k` chunk, đánh số và ghép nội dung của chúng vào phần `Context` của prompt; phần `Question` chứa câu hỏi của người dùng. Prompt yêu cầu LLM chỉ dựa vào ngữ cảnh và nói rõ nếu ngữ cảnh không chứa câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
pytest tests/ -v
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- F:\AI THỰC CHIẾN\LABS\K4-DAY07-NguyenThiLeNa-2A202602501\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: F:\AI THỰC CHIẾN\LABS\K4-DAY07-NguyenThiLeNa-2A202602501
collected 42 items                                                                                                                                   

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                 [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                     [100%]
============================= 42 passed ==============================
```
 
**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Các điểm dưới đây được tính bằng `MockEmbedder` mặc định; mô hình này dùng hàm băm nên điểm không đại diện đáng tin cậy cho sự gần nhau về ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể đổi trả sản phẩm chưa sử dụng. | Sản phẩm chưa qua sử dụng có thể được người mua yêu cầu đổi trả. | Cao | 0,0979 | Không khớp |
| 2 | Người bán phải xử lý yêu cầu bảo hành đúng hạn. | Yêu cầu bảo hành cần được người bán phản hồi trong thời hạn quy định. | Cao | 0,0878 | Không khớp |
| 3 | Sản phẩm phải còn nguyên tem/nhãn để yêu cầu đổi trả. | Điều kiện đổi trả là hàng vẫn còn tem và nhãn. | Cao | -0,2127 | Không khớp |
| 4 | Người mua yêu cầu đổi trả sản phẩm. | Người bán bị xử phạt vì phản hồi bảo hành trễ hạn. | Thấp | 0,0206 | Phù hợp |
| 5 | Sản phẩm chưa qua sử dụng là điều kiện đổi trả. | Người bán cần bổ sung quy trình khiếu nại bảo hành. | Thấp | -0,0079 | Phù hợp |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 bất ngờ nhất: hai câu cùng nói về điều kiện còn tem/nhãn khi đổi trả, nhưng điểm cosine lại âm (-0,2127). Kết quả cho thấy `MockEmbedder` không mã hóa ý nghĩa câu, nên tôi cần dùng mô hình embedding ngữ nghĩa để đánh giá chất lượng tương đồng thực sự.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn trả hàng của sản phẩm LazMall là bao lâu? | `lazada-buyer-return`: thời gian hoàn tiền qua thẻ tín dụng 07–14 ngày làm việc | 0,1818 | Không — nói về hoàn tiền, không phải thời hạn trả hàng | Chưa chạy Agent |
| 2 | Thời gian và quy trình xử lý hoàn tiền cho người mua như thế nào? | `lazada-buyer-protection-claim`: cam kết hàng chính hãng LazMall | 0,1062 | Không ở top-1; chunk liên quan ở top-2 và top-3 (`lazada-buyer-return`) | Chưa chạy Agent |
| 3 | Nhà bán hàng có bao nhiêu ngày để mở khiếu nại khi nhận hàng hoàn bị hư hỏng? | `lazada-seller-return-process`: thời hạn khiếu nại hàng hoàn hư hỏng là 03 ngày làm việc | 0,1690 | Có | Chưa chạy Agent |
| 4 | Sản phẩm điện tử mua trên Lazada có các hình thức bảo hành nào? | `lazada-seller-fee-and-claim`: biểu phí cố định và phí thanh toán của nhà bán hàng | 0,1345 | Không; top-3 không có chunk về hình thức bảo hành | Chưa chạy Agent |
| 5 | Chính sách đền bù của Lazada khi sản phẩm LazMall bị phát hiện là hàng giả? | `lazada-buyer-return`: các trường hợp sản phẩm lỗi kỹ thuật hoặc hư hỏng | 0,2458 | Không; top-3 không có chunk về đền bù hàng giả | Chưa chạy Agent |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 (câu 2 và 3, dựa trên các đoạn trích trong `ket_qua_benchmark.txt`).

Lần chạy benchmark dùng 5 tài liệu Lazada, tạo 18 chunk bằng `RecursiveChunker(chunk_size=300)`. Câu 2 và 3 có lọc metadata theo `audience`; câu 5 cũng lọc `buyer`. Điểm Score là cosine similarity do `MockEmbedder` tạo ra, nên điểm cao không bảo đảm chunk đúng nghĩa. Benchmark mới kiểm tra truy xuất, chưa gọi Agent để tạo câu trả lời; vì vậy chưa thể chấm điểm đầy đủ theo tiêu chí vừa truy xuất đúng vừa trả lời đúng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | Chờ đánh giá / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Đã ghi nhận truy xuất 2/5; chưa chấm điểm Agent / 10 |
| **Tổng phần cá nhân** | **Chưa xác định / 60** |
