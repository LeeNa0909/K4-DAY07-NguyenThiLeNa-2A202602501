from collections import Counter
import math
import re
import unicodedata


STOPWORDS = {
    "a", "bao", "bi", "cac", "cho", "co", "cua", "duoc", "khi", "la",
    "mua", "nao", "nhu", "o", "san", "pham", "the", "thi", "toi", "trong",
    "tren", "va", "ve", "voi",
}


def terms(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower().replace("đ", "d"))
    plain = "".join(char for char in normalized if not unicodedata.combining(char))
    return [word for word in re.findall(r"[a-z0-9]+", plain) if word not in STOPWORDS]


def rerank(query: str, results: list[dict], top_k: int = 3) -> list[dict]:
    """Rank existing store results by BM25, using hash cosine only as a tie-breaker."""
    if top_k <= 0 or not results:
        return []
    query_terms = terms(query)
    if not query_terms:
        return results[:top_k]

    texts = [result["content"] for result in results]
    token_lists = [terms(text) for text in texts]
    counts = [Counter(tokens) for tokens in token_lists]
    doc_count = len(results)
    avg_length = sum(len(tokens) for tokens in token_lists) / doc_count or 1
    document_frequency = Counter(term for tokens in token_lists for term in set(tokens))

    ranked = []
    for result, tokens, frequencies in zip(results, token_lists, counts):
        length = len(tokens)
        lexical_score = 0.0
        for term in set(query_terms):
            frequency = frequencies[term]
            if not frequency:
                continue
            idf = math.log(1 + (doc_count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            lexical_score += idf * frequency * 2.2 / (frequency + 1.2 * (0.25 + 0.75 * length / avg_length))

        # Adjacent words help distinguish "thời hạn trả hàng" from "thời gian hoàn tiền".
        bigrams = set(zip(tokens, tokens[1:]))
        lexical_score += 0.7 * sum(pair in bigrams for pair in zip(query_terms, query_terms[1:]))
        ranked.append({**result, "score": lexical_score + 0.01 * result["score"], "hash_score": result["score"]})

    return sorted(ranked, key=lambda result: result["score"], reverse=True)[:top_k]
