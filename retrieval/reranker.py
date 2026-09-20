import os

if os.environ.get("HF_HUB_OFFLINE") == "1":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
else:
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from sentence_transformers import CrossEncoder

MODEL_NAME = "BAAI/bge-reranker-base"
_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        print(f"[Reranker] 加载模型 {MODEL_NAME}...")
        _reranker = CrossEncoder(MODEL_NAME, device="cpu")
    return _reranker


def rerank(query: str, candidates: list, top_k: int = 3, dedup_by_source: bool = True) -> list:
    if not candidates:
        return []
    reranker = _get_reranker()
    pairs = [(query, c["content"]) for c in candidates]
    scores = reranker.predict(pairs)
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: -x[1])

    results = []
    seen_sources = set()
    for idx, score in indexed:
        doc = candidates[idx]
        source = doc["source"]
        if dedup_by_source and source in seen_sources:
            continue
        seen_sources.add(source)
        results.append({
            "content": doc["content"],
            "source": source,
            "rerank_score": float(score)
        })
        if len(results) >= top_k:
            break
    return results