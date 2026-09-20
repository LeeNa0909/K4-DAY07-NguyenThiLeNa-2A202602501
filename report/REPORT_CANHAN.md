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

Tôi chạy 5 câu hỏi Lazada trong `bench.py` trên mã nguồn cá nhân ở gói `src`. Benchmark nạp 5 tài liệu, tạo 18 chunk và ghi chi tiết top-3 cùng câu trả lời trích dẫn vào `ket_qua_benchmark.txt`. Các câu hỏi này cần được đối chiếu với bộ câu hỏi chung của nhóm khi hoàn thiện `REPORT_NHOM.md`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm xếp hạng | Có liên quan không? (Relevant) | Câu trả lời của Agent cục bộ (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn trả hàng của sản phẩm LazMall là bao lâu? | `lazada-buyer-return`: LazMall cho yêu cầu trả hàng trong 30 ngày kể từ khi giao thành công | 11,1013 | Có | Đoạn trích top-1 nêu 30 ngày |
| 2 | Thời gian và quy trình xử lý hoàn tiền cho người mua như thế nào? | `lazada-buyer-return`: sau khi duyệt trả hàng và thu hồi hàng, hoàn tiền trong 03–05 ngày làm việc | 6,1008 | Có | Top-1 nêu quy trình và 03–05 ngày; top-2 bổ sung 07–14 ngày làm việc** nếu thanh toán bằng thẻ tín dụng |
| 3 | Nhà bán hàng có bao nhiêu ngày để mở khiếu nại khi nhận hàng hoàn bị hư hỏng? | `lazada-seller-return-process`: mở khiếu nại trong 03 ngày làm việc kể từ khi nhận hàng hoàn | 16,4876 | Có | Đoạn trích top-1 nêu 03 ngày làm việc |
| 4 | Sản phẩm điện tử mua trên Lazada có các hình thức bảo hành nào? | `lazada-electronic-warranty`: bảo hành qua số điện thoại/IMEI, phiếu bảo hành hoặc ứng dụng nhà sản xuất | 11,4191 | Có | Đoạn trích top-1 nêu đủ 3 hình thức bảo hành |
| 5 | Chính sách đền bù của Lazada khi sản phẩm LazMall bị phát hiện là hàng giả? | `lazada-buyer-protection-claim`: người mua chứng minh hàng LazMall giả/nhái được đền tiền gấp 2 lần | 15,1989 | Có | Đoạn trích top-1 nêu 200% giá trị sản phẩm |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*  Nhóm tôi đã thử nghiệm so sánh giữa `FixedSizeChunker` (của tôi) với `SentenceChunker` và `RecursiveChunker`. Chiến lược `FixedSizeChunker` có thể vô tình cắt đứt ngang câu văn làm giảm tính mạch lạc của chunk, trong khi `RecursiveChunker` giữ trọn vẹn được cấu trúc đoạn và điều khoản chính sách tốt hơn, giúp độ tương đồng khi truy xuất chính xác hơn. 
---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | Chờ đánh giá / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Tự đánh giá tạm 10 / 10 (top-3 liên quan 5/5; Agent cục bộ trích đủ dữ kiện 5/5) |
| **Tổng phần cá nhân** | **55 + điểm dự đoán độ tương tự (chờ đánh giá) / 60** |
