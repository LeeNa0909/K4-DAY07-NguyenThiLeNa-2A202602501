import re
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from src.agent import KnowledgeBaseAgent
from src.embeddings import MockEmbedder
from src.models import Document
from src.chunking import RecursiveChunker
from src.store import EmbeddingStore
from src.retrieval import rerank

mock_embedder = MockEmbedder()

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


def local_extract_fn(prompt: str) -> str:
    """Quote the two best chunks so multi-part answers keep their evidence."""
    context = prompt.split("Context:\n", 1)[1].split("\n\nQuestion:", 1)[0]
    chunks = [re.sub(r"^\[\d+\] ", "", part).strip() for part in re.split(r"\n\n(?=\[\d+\] )", context)]
    if not chunks or chunks == ["(no relevant documents)"]:
        return "Không có đoạn trích để trả lời."
    excerpts = "\n".join(f"[{index}] {chunk}" for index, chunk in enumerate(chunks[:2], start=1))
    return f"Các đoạn trích sau xếp hạng từ khóa (cần tự đối chiếu):\n{excerpts}"


def make_llm_fn():
    """Use a real API when configured, otherwise a labeled local extractive function."""
    load_dotenv()
    provider = os.getenv("BENCH_LLM_PROVIDER", "").strip().lower()
    model = os.getenv("BENCH_LLM_MODEL", "").strip()
    if provider in ("", "local"):
        return local_extract_fn

    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            return local_extract_fn
        if not model:
            raise ValueError("Set BENCH_LLM_MODEL in .env before running the Agent benchmark.")
        from openai import OpenAI
        client = OpenAI()
        return lambda prompt: client.responses.create(model=model, input=prompt).output_text

    if provider == "gemini":
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            return local_extract_fn
        if not model:
            raise ValueError("Set BENCH_LLM_MODEL in .env before running the Agent benchmark.")
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        return lambda prompt: client.models.generate_content(model=model, contents=prompt).text or ""

    raise ValueError("BENCH_LLM_PROVIDER must be 'local', 'openai', or 'gemini'.")


def run_benchmark():
    llm_fn = make_llm_fn()
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

    store = EmbeddingStore(collection_name="lazada_benchmark", embedding_fn=mock_embedder)
    store.add_documents(all_documents)
    agent = KnowledgeBaseAgent(store, llm_fn)

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
    output_lines.append("Xếp hạng: BM25 từ/cụm từ; MockEmbedder dùng khi điểm gần bằng nhau")
    output_lines.append("Chế độ Agent: trích dẫn top-2, không dùng LLM/API" if llm_fn is local_extract_fn else "Chế độ Agent: LLM qua API")
    output_lines.append("")

    for item in benchmark_queries:
        qid = item["id"]
        qtext = item["query"]
        qfilter = item["filter"]

        output_lines.append(f"--- Query {qid}: '{qtext}' ---")
        if qfilter:
            output_lines.append(f"-> Áp dụng Filter: {qfilter}")
            candidates = store.search_with_filter(qtext, top_k=store.get_collection_size(), metadata_filter=qfilter)
        else:
            output_lines.append("-> Không dùng Filter (Search tất cả)")
            candidates = store.search(qtext, top_k=store.get_collection_size())
        results = rerank(qtext, candidates, top_k=3)

        for rank, res in enumerate(results, start=1):
            doc_id = res.get("metadata", {}).get("doc_id", res.get("id"))
            score = res.get("score", 0.0)
            snippet = " ".join(res.get("content", "").split())
            output_lines.append(f"  [Top {rank}] Doc: {doc_id} | Score BM25: {score:.4f} | Score băm: {res['hash_score']:.4f}")
            output_lines.append(f"        Chunk: {snippet}")
        answer = agent.answer_from_results(qtext, results)
        output_lines.append(f"  Agent answer: {answer}")
        output_lines.append("")

    report_text = "\n".join(output_lines)
    print(report_text)
    
    Path("ket_qua_benchmark.txt").write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    run_benchmark()
