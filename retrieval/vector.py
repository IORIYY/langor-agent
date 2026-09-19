import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


PERSIST_DIR = "data/chroma_db"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

_embeddings = None
_vectorstore = None


def _get_vectorstore():
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


def vector_search(query: str, top_k: int = 3) -> list:
    """
    向量检索。

    返回格式：
    [
        {"content": "...", "source": "...", "score": 0.411},
        ...
    ]
    注意：score 是距离，越小越相关。
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


if __name__ == "__main__":
    for q in ["均衡电流异常", "通讯中断", "终端电阻", "绝缘告警"]:
        print(f"\n问题：{q}")
        for r in vector_search(q, top_k=2):
            print(f"  [dist={r['score']:.3f}] {r['source']}")