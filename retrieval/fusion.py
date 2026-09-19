import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from retrieval.bm25 import bm25_search
from retrieval.vector import vector_search
from retrieval.reranker import rerank


def rrf_fusion(bm25_results: list, vector_results: list, k: int = 60, top_k: int = 10) -> list:
    """RRF 融合两路检索结果"""
    def _key(doc):
        return (doc["source"], doc["content"][:50])

    scores = {}
    doc_map = {}

    for rank, doc in enumerate(bm25_results, start=1):
        key = _key(doc)
        scores[key] = scores.get(key, 0) + 1 / (k + rank)
        doc_map[key] = doc

    for rank, doc in enumerate(vector_results, start=1):
        key = _key(doc)
        scores[key] = scores.get(key, 0) + 1 / (k + rank)
        doc_map[key] = doc

    sorted_items = sorted(scores.items(), key=lambda x: -x[1])

    results = []
    for key, rrf_score in sorted_items[:top_k]:
        doc = doc_map[key]
        results.append({
            "content": doc["content"],
            "source": doc["source"],
            "rrf_score": rrf_score
        })

    return results


def hybrid_search(query: str, top_k: int = 5, use_rerank: bool = True) -> list:
    """
    混合检索：BM25 + 向量 + RRF + Rerank。

    参数：
    - top_k: 最终返回条数
    - use_rerank: 是否启用 Rerank 精排
    """
    bm25_results = bm25_search(query, top_k=10)
    vector_results = vector_search(query, top_k=10)

    fused = rrf_fusion(bm25_results, vector_results, top_k=10)

    if use_rerank:
        return rerank(query, fused, top_k=top_k)

    return fused[:top_k]


if __name__ == "__main__":
    for q in ["均衡电流异常", "通讯中断", "终端电阻", "绝缘告警"]:
        print(f"\n{'='*60}")
        print(f"问题：{q}")
        print("--- 最终结果（含Rerank） ---")
        for r in hybrid_search(q, top_k=3):
            score = r.get("rerank_score", r.get("rrf_score", 0))
            print(f"  [score={score:.4f}] {r['source']}")