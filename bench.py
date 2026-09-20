import re
import sys
from pathlib import Path
from src.models import Document
from src.chunking import RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.store import EmbeddingStore

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



def parse_markdown_file(filepath: Path) -> tuple[dict, str]:
    raw = filepath.read_text(encoding="utf-8")
    parts = raw.split("---", 2)
    if len(parts) >= 3:
        yaml_text = parts[1]
        content = parts[2].strip()
        metadata = {}
        for line in yaml_text.strip().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip()
        return metadata, content
    return {}, raw.strip()


def run_benchmark():
    data_dir = Path("data/lazada")
    md_files = sorted(data_dir.glob("*.md"))
    
    chunker = RecursiveChunker(chunk_size=300)
    all_documents = []
    
    for md_file in md_files:
        meta, content = parse_markdown_file(md_file)
        doc_id = meta.get("doc_id", md_file.stem)
        chunks = chunker.chunk(content)
        
        for idx, chunk in enumerate(chunks):
            doc_chunk = Document(
                id=f"{doc_id}#{idx}",
                content=chunk,
                metadata={**meta, "doc_id": doc_id, "chunk_index": idx}
            )
            all_documents.append(doc_chunk)

    store = EmbeddingStore(collection_name="lazada_benchmark")
    store.add_documents(all_documents)

    benchmark_queries = [
        {
            "id": 1,
            "query": "Thời hạn trả hàng của sản phẩm LazMall là bao lâu?",
            "filter": None
        },
        {
            "id": 2,
            "query": "Thời gian và quy trình xử lý hoàn tiền cho người mua như thế nào?",
            "filter": {"audience": "buyer"}
        },
        {
            "id": 3,
            "query": "Nhà bán hàng có bao nhiêu ngày để mở khiếu nại khi nhận hàng hoàn bị hư hỏng?",
            "filter": {"audience": "seller"}
        },
        {
            "id": 4,
            "query": "Sản phẩm điện tử mua trên Lazada có các hình thức bảo hành nào?",
            "filter": None
        },
        {
            "id": 5,
            "query": "Chính sách đền bù của Lazada khi sản phẩm LazMall bị phát hiện là hàng giả?",
            "filter": {"audience": "buyer"}
        }
    ]

    output_lines = []
    output_lines.append(f"=== KẾT QUẢ BENCHMARK RAG - CHỦ ĐỀ LAZADA ===")
    output_lines.append(f"Tổng số tài liệu nạp vào: {len(md_files)}")
    output_lines.append(f"Tổng số chunks lưu trong store: {store.get_collection_size()}\n")

    for item in benchmark_queries:
        qid = item["id"]
        qtext = item["query"]
        qfilter = item["filter"]

        output_lines.append(f"--- Query {qid}: '{qtext}' ---")
        if qfilter:
            output_lines.append(f"-> Áp dụng Filter: {qfilter}")
            results = store.search_with_filter(qtext, top_k=3, metadata_filter=qfilter)
        else:
            output_lines.append("-> Không dùng Filter (Search tất cả)")
            results = store.search(qtext, top_k=3)

        for rank, res in enumerate(results, start=1):
            doc_id = res.get("metadata", {}).get("doc_id", res.get("id"))
            score = res.get("score", 0.0)
            snippet = res.get("content", "").replace("\n", " ")[:120]
            output_lines.append(f"  [Top {rank}] Doc: {doc_id} | Score: {score:.4f}")
            output_lines.append(f"        Snippet: {snippet}...")
        output_lines.append("")

    report_text = "\n".join(output_lines)
    print(report_text)
    
    Path("ket_qua_benchmark.txt").write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    run_benchmark()
