import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

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


def vector_search(query: str, top_k: int = 3, device_model: str = None) -> list:
    """
    向量检索，支持按设备型号过滤。
    """
    vs = _get_vectorstore()

    if device_model:
        results = vs.similarity_search_with_score(
            query, k=top_k,
            filter={"source": {"$contains": device_model}}
        )
    else:
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
    for q in ["均衡电流异常", "通讯中断"]:
        print(f"\n问题：{q}")
        for r in vector_search(q, top_k=2):
            print(f"  [dist={r['score']:.3f}] {r['source']}")