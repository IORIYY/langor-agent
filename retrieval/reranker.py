import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

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
    """
    对候选文档重新打分排序。

    参数：
    - query: 用户问题
    - candidates: [{"content": "...", "source": "...", ...}, ...]
    - top_k: 返回条数
    - dedup_by_source: 是否按 source 去重（同一文件只保留最高分片段）
    """
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

        # 去重
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


if __name__ == "__main__":
    from retrieval.fusion import hybrid_search

    for q in ["均衡电流异常", "通讯中断", "终端电阻", "绝缘告警"]:
        print(f"\n{'='*60}")
        print(f"问题：{q}")

        candidates = hybrid_search(q, top_k=10)
        print("--- RRF 融合 Top3 ---")
        for r in candidates[:3]:
            print(f"  [rrf={r['rrf_score']:.4f}] {r['source']}")

        reranked = rerank(q, candidates, top_k=3)
        print("--- Rerank 精排 Top3（去重后） ---")
        for r in reranked:
            print(f"  [rerank={r['rerank_score']:.4f}] {r['source']}")