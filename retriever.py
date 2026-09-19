import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ============ 配置 ============
PERSIST_DIR = "data/chroma_db"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
TOP_K = 3

# ============ 初始化 ============
_embeddings = None
_vectorstore = None


def _get_vectorstore():
    """延迟加载向量库，避免每次调用都重新加载"""
    global _embeddings, _vectorstore
    if _vectorstore is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        _vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=_embeddings
        )
    return _vectorstore


def retrieve(query: str, top_k: int = TOP_K) -> list:
    """
    检索知识库，返回 Top-K 相关片段。

    返回格式：
    [
        {
            "content": "片段内容",
            "source": "docs\\sop\\xxx.md",
            "score": 0.411
        },
        ...
    ]
    """
    vs = _get_vectorstore()
    results = vs.similarity_search_with_score(query, k=top_k)

    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "score": float(score)
        }
        for doc, score in results
    ]


def retrieve_with_filter(query: str, top_k: int = TOP_K, max_score: float = None) -> list:
    """
    带阈值过滤的检索。
    max_score：只返回 score <= max_score 的片段。
    """
    results = retrieve(query, top_k=top_k)
    if max_score is not None:
        results = [r for r in results if r["score"] <= max_score]
    return results


if __name__ == "__main__":
    # 测试
    test_queries = [
        "均衡电流异常怎么排查",
        "通讯中断怎么办",
        "绝缘告警处理",
        "今天天气怎么样",
    ]

    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"问题：{q}")
        results = retrieve(q, top_k=2)
        for r in results:
            print(f"  [score={r['score']:.3f}] {r['source']}")
            print(f"    {r['content'][:60]}...")